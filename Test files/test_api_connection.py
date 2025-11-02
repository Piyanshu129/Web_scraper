#!/usr/bin/env python3
"""
Quick test to verify API connection to Apache Jira.
This can be run after installation to verify everything works.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.jira_client import JiraClient
    
    print("Testing Apache Jira API connection...")
    print("=" * 60)
    
    with JiraClient() as client:
        # Test getting project info for SPARK
        print("Testing project info retrieval...")
        project_info = client.get_project_info('SPARK')
        
        if project_info:
            print(f"✓ Successfully connected to Apache Jira")
            print(f"  Project: {project_info.get('name', 'Unknown')}")
            print(f"  Key: {project_info.get('key', 'Unknown')}")
        else:
            print("❌ Failed to retrieve project info")
            sys.exit(1)
        
        # Test searching for issues
        print("\nTesting issue search...")
        search_results = client.search_issues('SPARK', start_at=0, max_results=1)
        
        if search_results:
            total = search_results.get('total', 0)
            print(f"✓ Successfully searched issues")
            print(f"  Total issues in SPARK: {total}")
            if total > 0:
                issues = search_results.get('issues', [])
                if issues:
                    issue_key = issues[0].get('key', 'Unknown')
                    print(f"  Sample issue: {issue_key}")
        else:
            print("❌ Failed to search issues")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✓ All API tests passed!")
        print("=" * 60)
        print("\nYou can now run the scraper with:")
        print("  python main.py")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure dependencies are installed:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

