"""
Data transformation module.
Converts raw Jira API responses into structured JSONL format suitable for LLM training.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms Jira issue data into JSONL format with derived tasks."""
    
    @staticmethod
    def extract_text_content(field: Any) -> str:
        """
        Extract plain text from Jira fields which may contain HTML or structured data.
        
        Args:
            field: Field value (can be string, dict, or None)
            
        Returns:
            Plain text content
        """
        if field is None:
            return ""
        
        if isinstance(field, str):
            # Simple text field
            return field.strip()
        
        if isinstance(field, dict):
            # Structured field (e.g., rendered content, user objects)
            if 'rendered' in field:
                # Extract text from rendered HTML (basic cleanup)
                import re
                text = field['rendered']
                # Remove HTML tags (basic)
                text = re.sub(r'<[^>]+>', '', text)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
            
            if 'name' in field:
                return str(field['name'])
            
            if 'displayName' in field:
                return str(field['displayName'])
            
            if 'value' in field:
                return str(field['value'])
            
            # Fallback: try to extract any string values
            text_parts = []
            for key, value in field.items():
                if isinstance(value, str):
                    text_parts.append(value)
            return " ".join(text_parts).strip()
        
        return str(field).strip()
    
    @staticmethod
    def format_timestamp(timestamp: Optional[str]) -> Optional[str]:
        """Format ISO timestamp to readable format."""
        if not timestamp:
            return None
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            return timestamp
    
    @staticmethod
    def extract_labels(issue: Dict) -> List[str]:
        """Extract labels from issue."""
        labels = issue.get('fields', {}).get('labels', [])
        return labels if isinstance(labels, list) else []
    
    @staticmethod
    def extract_components(issue: Dict) -> List[str]:
        """Extract component names from issue."""
        components = issue.get('fields', {}).get('components', [])
        return [comp.get('name', '') for comp in components if isinstance(comp, dict)]
    
    @staticmethod
    def extract_comments(issue: Dict, comments_data: Optional[Dict] = None) -> List[Dict]:
        """
        Extract comments from issue.
        
        Args:
            issue: Issue dictionary
            comments_data: Optional separate comments API response
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        # Try to get from separate comments endpoint
        if comments_data:
            comment_list = comments_data.get('comments', [])
            for comment in comment_list:
                comments.append({
                    'author': DataTransformer.extract_text_content(comment.get('author')),
                    'body': DataTransformer.extract_text_content(comment.get('body')),
                    'created': DataTransformer.format_timestamp(comment.get('created')),
                    'updated': DataTransformer.format_timestamp(comment.get('updated'))
                })
        
        # Also check comment field in issue (if present)
        comment_field = issue.get('fields', {}).get('comment', {})
        if comment_field and 'comments' in comment_field:
            for comment in comment_field['comments']:
                # Avoid duplicates
                existing = any(
                    c.get('body') == DataTransformer.extract_text_content(comment.get('body'))
                    for c in comments
                )
                if not existing:
                    comments.append({
                        'author': DataTransformer.extract_text_content(comment.get('author')),
                        'body': DataTransformer.extract_text_content(comment.get('body')),
                        'created': DataTransformer.format_timestamp(comment.get('created')),
                        'updated': DataTransformer.format_timestamp(comment.get('updated'))
                    })
        
        return comments
    
    @staticmethod
    def create_derived_tasks(issue_data: Dict) -> Dict:
        """
        Create derived tasks for LLM training.
        
        Includes:
        - Summarization task
        - Classification task
        - Q&A generation
        """
        issue_key = issue_data.get('key', '')
        title = issue_data.get('title', '')
        description = issue_data.get('description', '')
        status = issue_data.get('status', 'Unknown')
        issue_type = issue_data.get('issue_type', 'Unknown')
        
        # Combine issue text
        full_text = f"{title}\n\n{description}"
        if issue_data.get('comments'):
            full_text += "\n\nComments:\n"
            for comment in issue_data['comments']:
                full_text += f"- {comment.get('author', 'Unknown')}: {comment.get('body', '')}\n"
        
        tasks = {
            'summarization': {
                'instruction': 'Summarize the following Jira issue:',
                'input': full_text,
                'output': f"Issue {issue_key}: {title} (Status: {status}, Type: {issue_type})"
            },
            'classification': {
                'instruction': 'Classify the following Jira issue by type and status:',
                'input': f"{title}\n\n{description[:500]}",  # Truncate for classification
                'output': f"Type: {issue_type}, Status: {status}"
            },
            'qa_generation': {
                'question': f"What is the issue {issue_key} about?",
                'context': full_text[:1000] if len(full_text) > 1000 else full_text,  # Truncate context if needed
                'answer': f"{title} - {description[:200]}" if description else title
            }
        }
        
        return tasks
    
    @classmethod
    def transform_issue(cls, issue: Dict, comments_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Transform a single issue from Jira API format to JSONL format.
        
        Args:
            issue: Raw issue dictionary from Jira API
            comments_data: Optional separate comments API response
            
        Returns:
            Transformed issue dictionary or None if invalid
        """
        try:
            fields = issue.get('fields', {})
            if not fields:
                logger.warning(f"No fields found in issue {issue.get('key', 'unknown')}")
                return None
            
            # Extract basic metadata
            issue_key = issue.get('key', '')
            
            # Extract text fields
            title = cls.extract_text_content(fields.get('summary', ''))
            description = cls.extract_text_content(
                fields.get('description') or fields.get('renderedFields', {}).get('description', '')
            )
            
            # Extract structured fields
            status = cls.extract_text_content(fields.get('status', {}))
            issue_type = cls.extract_text_content(fields.get('issuetype', {}))
            priority = cls.extract_text_content(fields.get('priority', {}))
            project = cls.extract_text_content(fields.get('project', {}))
            
            # Extract user fields
            reporter = cls.extract_text_content(fields.get('reporter', {}))
            assignee = cls.extract_text_content(fields.get('assignee', {}))
            
            # Extract timestamps
            created = cls.format_timestamp(fields.get('created'))
            updated = cls.format_timestamp(fields.get('updated'))
            resolved = cls.format_timestamp(fields.get('resolutiondate'))
            
            # Extract additional metadata
            labels = cls.extract_labels(issue)
            components = cls.extract_components(issue)
            
            # Extract comments
            comments = cls.extract_comments(issue, comments_data)
            
            # Build transformed issue
            transformed = {
                'issue_key': issue_key,
                'project': project,
                'title': title,
                'description': description,
                'status': status,
                'issue_type': issue_type,
                'priority': priority,
                'reporter': reporter,
                'assignee': assignee,
                'created': created,
                'updated': updated,
                'resolved': resolved,
                'labels': labels,
                'components': components,
                'comments': comments,
                'comment_count': len(comments),
                'metadata': {
                    'raw_issue_key': issue_key,
                    'scraped_at': datetime.utcnow().isoformat(),
                    'source': 'apache-jira'
                }
            }
            
            # Add derived tasks
            transformed['derived_tasks'] = cls.create_derived_tasks(transformed)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming issue {issue.get('key', 'unknown')}: {e}")
            return None
    
    @staticmethod
    def write_jsonl(data: List[Dict], output_file: str):
        """
        Write list of dictionaries to JSONL file.
        
        Args:
            data: List of dictionaries to write
            output_file: Output file path
        """
        with open(output_file, 'a', encoding='utf-8') as f:
            for item in data:
                if item:  # Skip None values
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

