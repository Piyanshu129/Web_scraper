"""
State management for resuming interrupted scrapes.
Tracks progress per project and allows seamless resumption.
"""

import json
import os
from typing import Dict, Optional, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """Manages scraping state to enable resume functionality."""
    
    def __init__(self, state_dir: str = "state"):
        """
        Initialize state manager.
        
        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "scrape_state.json"
        self.state: Dict = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from disk if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state: {len(state.get('processed_issues', {}))} projects tracked")
                    return state
            except Exception as e:
                logger.warning(f"Failed to load state: {e}. Starting fresh.")
                return self._default_state()
        return self._default_state()
    
    def _default_state(self) -> Dict:
        """Return default empty state structure."""
        return {
            'projects': {},
            'processed_issues': {},
            'last_updated': None
        }
    
    def save_state(self):
        """Save current state to disk."""
        from datetime import datetime
        self.state['last_updated'] = datetime.utcnow().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug("State saved successfully")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_processed_issues(self, project: str) -> Set[str]:
        """
        Get set of already processed issue keys for a project.
        
        Args:
            project: Project key
            
        Returns:
            Set of processed issue keys
        """
        return set(self.state.get('processed_issues', {}).get(project, []))
    
    def mark_issue_processed(self, project: str, issue_key: str):
        """
        Mark an issue as processed.
        
        Args:
            project: Project key
            issue_key: Issue key
        """
        if 'processed_issues' not in self.state:
            self.state['processed_issues'] = {}
        if project not in self.state['processed_issues']:
            self.state['processed_issues'][project] = []
        
        if issue_key not in self.state['processed_issues'][project]:
            self.state['processed_issues'][project].append(issue_key)
    
    def get_project_progress(self, project: str) -> Dict:
        """
        Get progress information for a project.
        
        Args:
            project: Project key
            
        Returns:
            Dictionary with progress info (start_at, last_issue_key, etc.)
        """
        return self.state.get('projects', {}).get(project, {})
    
    def update_project_progress(
        self,
        project: str,
        start_at: int,
        last_issue_key: Optional[str] = None
    ):
        """
        Update progress for a project.
        
        Args:
            project: Project key
            start_at: Current pagination offset
            last_issue_key: Last processed issue key
        """
        if 'projects' not in self.state:
            self.state['projects'] = {}
        self.state['projects'][project] = {
            'start_at': start_at,
            'last_issue_key': last_issue_key
        }
    
    def reset_project(self, project: str):
        """Reset state for a specific project."""
        if 'projects' in self.state and project in self.state['projects']:
            del self.state['projects'][project]
        if 'processed_issues' in self.state and project in self.state['processed_issues']:
            del self.state['processed_issues'][project]
        logger.info(f"Reset state for project {project}")
    
    def get_total_processed(self) -> int:
        """Get total number of processed issues across all projects."""
        total = 0
        for issues in self.state.get('processed_issues', {}).values():
            total += len(issues)
        return total

