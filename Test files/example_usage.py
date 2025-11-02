#!/usr/bin/env python3
"""
Example usage script demonstrating how to use the scraper programmatically.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import JiraScraper

def example_basic_usage():
    """Basic usage example."""
    print("Example: Basic scraping")
    print("=" * 60)
    
    # Initialize scraper with 3 Apache projects
    with JiraScraper(
        projects=['SPARK', 'HADOOP', 'FLINK'],
        output_file='example_output.jsonl',
        delay_between_requests=1.5  # Be respectful with rate limits
    ) as scraper:
        stats = scraper.scrape_all()
        print(f"\nScraped {stats['total_issues']} issues total")
        print(f"Output saved to: {stats['output_file']}")


def example_single_project():
    """Example of scraping a single project."""
    print("Example: Single project scraping")
    print("=" * 60)
    
    with JiraScraper(
        projects=['SPARK'],
        output_file='spark_only.jsonl'
    ) as scraper:
        count = scraper.scrape_project('SPARK')
        print(f"\nScraped {count} issues from SPARK project")


if __name__ == '__main__':
    print("Apache Jira Scraper - Example Usage\n")
    
    # Uncomment to run examples:
    # example_basic_usage()
    # example_single_project()
    
    print("Examples are commented out. Uncomment to run.")
    print("See README.md for detailed usage instructions.")

