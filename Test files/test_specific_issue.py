#!/usr/bin/env python3
"""
Test script to fetch a specific issue and show the output.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.jira_client import JiraClient
from src.data_transformer import DataTransformer

def fetch_and_display_issue(issue_key: str):
    """Fetch a specific issue and display both raw and transformed output."""
    
    print(f"Fetching issue: {issue_key}")
    print("=" * 80)
    
    with JiraClient() as client:
        # Fetch issue details
        print("\n1. Fetching issue details...")
        issue = client.get_issue(issue_key, expand='changelog,renderedFields')
        
        if not issue:
            print(f"❌ Failed to fetch issue {issue_key}")
            return
        
        print(f"✓ Successfully fetched issue")
        
        # Fetch comments
        print("\n2. Fetching comments...")
        comments_data = client.get_issue_comments(issue_key)
        
        if comments_data:
            comment_count = len(comments_data.get('comments', []))
            print(f"✓ Found {comment_count} comments")
        else:
            print("⚠ No comments found or failed to fetch")
            comments_data = None
        
        # Display raw API response (pretty printed)
        print("\n" + "=" * 80)
        print("RAW API RESPONSE (first 2000 chars):")
        print("=" * 80)
        raw_json = json.dumps(issue, indent=2, ensure_ascii=False)
        print(raw_json[:2000])
        if len(raw_json) > 2000:
            print(f"\n... (truncated, total length: {len(raw_json)} chars)")
        
        # Transform the issue
        print("\n" + "=" * 80)
        print("TRANSFORMED OUTPUT (JSONL format):")
        print("=" * 80)
        transformer = DataTransformer()
        transformed = transformer.transform_issue(issue, comments_data)
        
        if transformed:
            transformed_json = json.dumps(transformed, indent=2, ensure_ascii=False)
            print(transformed_json)
        else:
            print("❌ Failed to transform issue")
            return
        
        # Display key fields
        print("\n" + "=" * 80)
        print("KEY INFORMATION:")
        print("=" * 80)
        print(f"Issue Key: {transformed.get('issue_key')}")
        print(f"Project: {transformed.get('project')}")
        print(f"Title: {transformed.get('title')}")
        print(f"Status: {transformed.get('status')}")
        print(f"Issue Type: {transformed.get('issue_type')}")
        print(f"Priority: {transformed.get('priority')}")
        print(f"Reporter: {transformed.get('reporter')}")
        print(f"Assignee: {transformed.get('assignee')}")
        print(f"Created: {transformed.get('created')}")
        print(f"Updated: {transformed.get('updated')}")
        print(f"Labels: {', '.join(transformed.get('labels', []))}")
        print(f"Components: {', '.join(transformed.get('components', []))}")
        print(f"Comment Count: {transformed.get('comment_count', 0)}")
        
        # Show description preview
        description = transformed.get('description', '')
        if description:
            print(f"\nDescription Preview (first 300 chars):")
            print("-" * 80)
            print(description[:300])
            if len(description) > 300:
                print("... (truncated)")
        
        # Show comments preview
        comments = transformed.get('comments', [])
        if comments:
            print(f"\nComments ({len(comments)}):")
            print("-" * 80)
            for i, comment in enumerate(comments[:3], 1):  # Show first 3
                print(f"\nComment {i} by {comment.get('author')} on {comment.get('created')}:")
                body = comment.get('body', '')
                print(body[:200])
                if len(body) > 200:
                    print("... (truncated)")
            if len(comments) > 3:
                print(f"\n... and {len(comments) - 3} more comments")
        
        # Show derived tasks
        print("\n" + "=" * 80)
        print("DERIVED TASKS:")
        print("=" * 80)
        tasks = transformed.get('derived_tasks', {})
        
        if 'summarization' in tasks:
            print("\n1. Summarization Task:")
            print(f"   Instruction: {tasks['summarization']['instruction']}")
            print(f"   Input: {tasks['summarization']['input'][:200]}...")
            print(f"   Output: {tasks['summarization']['output']}")
        
        if 'classification' in tasks:
            print("\n2. Classification Task:")
            print(f"   Instruction: {tasks['classification']['instruction']}")
            print(f"   Input: {tasks['classification']['input'][:200]}...")
            print(f"   Output: {tasks['classification']['output']}")
        
        if 'qa_generation' in tasks:
            print("\n3. Q&A Generation Task:")
            print(f"   Question: {tasks['qa_generation']['question']}")
            print(f"   Context: {tasks['qa_generation']['context'][:200]}...")
            print(f"   Answer: {tasks['qa_generation']['answer']}")

if __name__ == '__main__':
    # Extract issue key from URL or use directly
    issue_key = "NIFI-15171"
    
    print("Apache Jira Scraper - Issue Fetch Test")
    print("=" * 80)
    print(f"Testing with issue: {issue_key}")
    print(f"URL: https://issues.apache.org/jira/browse/{issue_key}")
    print()
    
    try:
        fetch_and_display_issue(issue_key)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

