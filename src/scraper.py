"""
Main scraping orchestration module.
Coordinates API calls, state management, and data transformation.
"""

import time
import sys
from typing import List, Optional
from pathlib import Path
import logging
from tqdm import tqdm

# Handle both package and direct imports
try:
    from .jira_client import JiraClient
    from .state_manager import StateManager
    from .data_transformer import DataTransformer
except ImportError:
    # For direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.jira_client import JiraClient
    from src.state_manager import StateManager
    from src.data_transformer import DataTransformer

logger = logging.getLogger(__name__)


class JiraScraper:
    """Main scraper class that orchestrates the entire scraping process."""
    
    def __init__(
        self,
        projects: List[str],
        output_file: str = "jira_dataset.jsonl",
        state_dir: str = "state",
        max_results_per_page: int = 50,
        batch_size: int = 10,
        delay_between_requests: float = 1.0
    ):
        """
        Initialize scraper.
        
        Args:
            projects: List of Jira project keys to scrape
            output_file: Output JSONL file path
            state_dir: Directory for state files
            max_results_per_page: Results per API page
            batch_size: Number of issues to process before saving state
            delay_between_requests: Delay between API requests (seconds)
        """
        self.projects = projects
        self.output_file = Path(output_file)
        self.max_results_per_page = max_results_per_page
        self.batch_size = batch_size
        self.delay_between_requests = delay_between_requests
        
        # Initialize components
        self.client = JiraClient()
        self.state_manager = StateManager(state_dir)
        self.transformer = DataTransformer()
        
        # Ensure output file exists (will append if exists)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized scraper for projects: {', '.join(projects)}")
    
    def scrape_project(self, project: str) -> int:
        """
        Scrape all issues from a single project.
        
        Args:
            project: Project key
            
        Returns:
            Number of issues scraped
        """
        logger.info(f"Starting scrape for project: {project}")
        
        # Check if project exists
        project_info = self.client.get_project_info(project)
        if not project_info:
            logger.error(f"Failed to retrieve project info for {project}. Skipping.")
            return 0
        
        project_name = project_info.get('name', project)
        logger.info(f"Scraping project: {project_name} ({project})")
        
        # Get processed issues to avoid duplicates
        processed_issues = self.state_manager.get_processed_issues(project)
        logger.info(f"Found {len(processed_issues)} already processed issues")
        
        # Get progress state
        progress = self.state_manager.get_project_progress(project)
        start_at = progress.get('start_at', 0)
        
        total_scraped = 0
        batch = []
        
        # Initial search to get total count
        search_results = self.client.search_issues(
            project=project,
            start_at=0,
            max_results=1
        )
        
        if not search_results:
            logger.error(f"Failed to get issue count for {project}")
            return 0
        
        total_issues = search_results.get('total', 0)
        logger.info(f"Total issues in {project}: {total_issues}")
        
        # Progress bar
        pbar = tqdm(
            total=total_issues,
            desc=f"Scraping {project}",
            initial=len(processed_issues),
            unit="issues"
        )
        
        # Scrape with pagination
        current_start = start_at
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while current_start < total_issues:
            # Rate limiting
            time.sleep(self.delay_between_requests)
            
            # Search for issues
            search_results = self.client.search_issues(
                project=project,
                start_at=current_start,
                max_results=self.max_results_per_page
            )
            
            if not search_results:
                consecutive_failures += 1
                logger.warning(
                    f"Failed to get search results for {project} at start_at={current_start}. "
                    f"Consecutive failures: {consecutive_failures}"
                )
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures for {project}. Stopping.")
                    break
                
                # Exponential backoff
                time.sleep(2 ** consecutive_failures)
                continue
            
            consecutive_failures = 0
            
            issues = search_results.get('issues', [])
            if not issues:
                logger.info(f"No more issues found for {project}")
                break
            
            # Process each issue
            for issue in issues:
                issue_key = issue.get('key', '')
                
                # Skip if already processed
                if issue_key in processed_issues:
                    pbar.update(1)
                    continue
                
                # Get detailed issue data (may already be in search results)
                issue_data = issue
                
                # Fetch comments separately for completeness
                comments_data = None
                if self.delay_between_requests > 0:
                    time.sleep(self.delay_between_requests * 0.5)  # Shorter delay for comments
                
                comments_data = self.client.get_issue_comments(issue_key)
                
                # Transform issue
                transformed = self.transformer.transform_issue(issue_data, comments_data)
                
                if transformed:
                    batch.append(transformed)
                    self.state_manager.mark_issue_processed(project, issue_key)
                    total_scraped += 1
                
                # Save batch periodically
                if len(batch) >= self.batch_size:
                    self.transformer.write_jsonl(batch, str(self.output_file))
                    self.state_manager.update_project_progress(
                        project,
                        current_start,
                        issue_key
                    )
                    self.state_manager.save_state()
                    batch = []
                    logger.debug(f"Saved batch of {self.batch_size} issues")
                
                pbar.update(1)
            
            # Update progress
            current_start += len(issues)
            self.state_manager.update_project_progress(project, current_start)
            
            # Check if we've reached the end
            if len(issues) < self.max_results_per_page:
                break
        
        # Save remaining batch
        if batch:
            self.transformer.write_jsonl(batch, str(self.output_file))
            self.state_manager.save_state()
        
        pbar.close()
        logger.info(f"Completed scraping {project}. Total scraped: {total_scraped}")
        return total_scraped
    
    def scrape_all(self) -> dict:
        """
        Scrape all configured projects.
        
        Returns:
            Dictionary with scraping statistics
        """
        stats = {
            'projects': {},
            'total_issues': 0,
            'output_file': str(self.output_file)
        }
        
        logger.info(f"Starting scrape for {len(self.projects)} projects")
        
        for project in self.projects:
            try:
                count = self.scrape_project(project)
                stats['projects'][project] = {
                    'issues_scraped': count,
                    'success': True
                }
                stats['total_issues'] += count
            except Exception as e:
                logger.error(f"Error scraping project {project}: {e}", exc_info=True)
                stats['projects'][project] = {
                    'issues_scraped': 0,
                    'success': False,
                    'error': str(e)
                }
            
            # Delay between projects
            if project != self.projects[-1]:
                logger.info("Waiting before next project...")
                time.sleep(self.delay_between_requests * 2)
        
        logger.info(f"Scraping complete. Total issues: {stats['total_issues']}")
        return stats
    
    def reset_project(self, project: str):
        """Reset state for a project to re-scrape it."""
        self.state_manager.reset_project(project)
        logger.info(f"Reset state for project {project}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.__exit__(exc_type, exc_val, exc_tb)

