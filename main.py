#!/usr/bin/env python3
"""
Main entry point for Apache Jira scraper.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import JiraScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scrape Apache Jira issues and convert to JSONL format'
    )
    
    parser.add_argument(
        '--projects',
        nargs='+',
        default=['SPARK', 'HADOOP', 'FLINK'],
        help='Jira project keys to scrape (default: SPARK HADOOP FLINK)'
    )
    
    parser.add_argument(
        '--output',
        default='jira_dataset.jsonl',
        help='Output JSONL file path (default: jira_dataset.jsonl)'
    )
    
    parser.add_argument(
        '--state-dir',
        default='state',
        help='Directory for state files (default: state)'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum results per page (default: 50)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Batch size for saving (default: 10)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset state and start fresh'
    )
    
    parser.add_argument(
        '--reset-project',
        help='Reset state for a specific project'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Apache Jira Scraper")
    logger.info("=" * 60)
    logger.info(f"Projects: {', '.join(args.projects)}")
    logger.info(f"Output: {args.output}")
    logger.info(f"State directory: {args.state_dir}")
    logger.info("=" * 60)
    
    try:
        with JiraScraper(
            projects=args.projects,
            output_file=args.output,
            state_dir=args.state_dir,
            max_results_per_page=args.max_results,
            batch_size=args.batch_size,
            delay_between_requests=args.delay
        ) as scraper:
            
            # Handle reset options
            if args.reset:
                logger.info("Resetting all project states...")
                for project in args.projects:
                    scraper.reset_project(project)
            
            if args.reset_project:
                logger.info(f"Resetting state for project: {args.reset_project}")
                scraper.reset_project(args.reset_project)
                return
            
            # Start scraping
            stats = scraper.scrape_all()
            
            # Print summary
            print("\n" + "=" * 60)
            print("SCRAPING SUMMARY")
            print("=" * 60)
            print(f"Output file: {stats['output_file']}")
            print(f"Total issues scraped: {stats['total_issues']}")
            print("\nPer-project breakdown:")
            for project, project_stats in stats['projects'].items():
                status = "✓" if project_stats['success'] else "✗"
                print(f"  {status} {project}: {project_stats['issues_scraped']} issues")
                if not project_stats['success']:
                    print(f"    Error: {project_stats.get('error', 'Unknown')}")
            print("=" * 60)
            
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user. State saved. Run again to resume.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

