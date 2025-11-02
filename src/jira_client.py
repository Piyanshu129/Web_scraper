"""
Jira API Client with rate limiting, retry logic, and error handling.
Handles HTTP 429, 5xx errors, timeouts, and network failures gracefully.
"""

import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Apache Jira REST API with robust error handling."""
    
    BASE_URL = "https://issues.apache.org/jira/rest/api/2"
    
    def __init__(
        self,
        max_retries: int = 5,
        retry_delay: float = 1.0,
        timeout: int = 30,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize Jira client.
        
        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Base delay between retries (seconds)
            timeout: Request timeout (seconds)
            rate_limit_delay: Delay after rate limit (seconds)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Apache-Jira-Scraper/1.0'
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        Make HTTP request with retry logic and error handling.
        
        Handles:
        - HTTP 429 (Rate Limiting)
        - HTTP 5xx (Server Errors)
        - Network timeouts
        - Connection errors
        - Empty/malformed responses
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout,
                    **kwargs
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = float(response.headers.get('Retry-After', self.rate_limit_delay))
                    logger.warning(f"Rate limited. Waiting {retry_after}s before retry...")
                    time.sleep(retry_after)
                    continue
                
                # Handle server errors (5xx)
                if response.status_code >= 500:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Server error {response.status_code}. "
                        f"Attempt {attempt + 1}/{self.max_retries}. Waiting {wait_time}s..."
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for {url}")
                        return None
                
                # Handle client errors (4xx except 429)
                if 400 <= response.status_code < 500:
                    logger.error(f"Client error {response.status_code} for {url}: {response.text[:200]}")
                    return None
                
                # Handle successful response
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Check for empty or malformed data
                        if data is None:
                            logger.warning(f"Empty response from {url}")
                            return None
                        return data
                    except ValueError as e:
                        logger.error(f"Failed to parse JSON response from {url}: {e}")
                        return None
                
                # Unexpected status code
                logger.warning(f"Unexpected status code {response.status_code} for {url}")
                return None
                
            except requests.exceptions.Timeout:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Request timeout. Attempt {attempt + 1}/{self.max_retries}. "
                    f"Waiting {wait_time}s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries exceeded due to timeout for {url}")
                    return None
                    
            except requests.exceptions.ConnectionError as e:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(
                    f"Connection error: {e}. Attempt {attempt + 1}/{self.max_retries}. "
                    f"Waiting {wait_time}s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries exceeded due to connection error for {url}")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error during request to {url}: {e}")
                return None
        
        return None
    
    def search_issues(
        self,
        project: str,
        start_at: int = 0,
        max_results: int = 50,
        jql: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Search for issues in a project.
        
        Args:
            project: Jira project key
            start_at: Starting index for pagination
            max_results: Maximum number of results per page
            jql: Optional JQL query string
            
        Returns:
            Search results dictionary or None if failed
        """
        if jql is None:
            jql = f"project = {project} ORDER BY created DESC"
        
        params = {
            'jql': jql,
            'startAt': start_at,
            'maxResults': max_results,
            'expand': 'changelog,renderedFields'
        }
        
        return self._make_request('GET', 'search', params=params)
    
    def get_issue(self, issue_key: str, expand: str = 'changelog,renderedFields') -> Optional[Dict]:
        """
        Get detailed information about a specific issue.
        
        Args:
            issue_key: Issue key (e.g., 'SPARK-12345')
            expand: Fields to expand in response
            
        Returns:
            Issue dictionary or None if failed
        """
        params = {'expand': expand} if expand else {}
        return self._make_request('GET', f'issue/{issue_key}', params=params)
    
    def get_issue_comments(self, issue_key: str) -> Optional[Dict]:
        """
        Get comments for a specific issue.
        
        Args:
            issue_key: Issue key
            
        Returns:
            Comments dictionary or None if failed
        """
        return self._make_request('GET', f'issue/{issue_key}/comment')
    
    def get_project_info(self, project_key: str) -> Optional[Dict]:
        """
        Get project information.
        
        Args:
            project_key: Project key
            
        Returns:
            Project dictionary or None if failed
        """
        return self._make_request('GET', f'project/{project_key}')
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

