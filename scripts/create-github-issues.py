#!/usr/bin/env python3
"""
Create GitHub Issues for Vulnerabilities
Creates GitHub issues for scan results
"""

import sys
import json
import logging
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from notification_service import GitHubNotifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_issues_from_results(
    results_file: str,
    severity_filter: list,
    dry_run: bool,
    labels: list
) -> bool:
    """
    Create GitHub issues from scan results

    Args:
        results_file: Path to scan results JSON file
        severity_filter: List of severities to create issues for
        dry_run: If True, don't actually create issues
        labels: Additional labels to add

    Returns:
        True if successful
    """
    try:
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)

        scan_info = results.get('scan_info', {})
        vulnerabilities = results.get('vulnerabilities', [])

        logger.info(f"Creating GitHub issues from {results_file}")
        logger.info(f"Total vulnerabilities: {len(vulnerabilities)}")
        logger.info(f"Severity filter: {severity_filter}")

        # Initialize GitHub notifier
        notifier = GitHubNotifier()

        # Test connection
        if not notifier.test_connection():
            logger.error("Failed to connect to GitHub API")
            return False

        # Create issues
        result = notifier.create_issues_for_vulnerabilities(
            vulnerabilities=vulnerabilities,
            scan_info=scan_info,
            severity_filter=severity_filter,
            labels=labels,
            dry_run=dry_run
        )

        logger.info("GitHub issue creation complete:")
        logger.info(f"  - Created: {result['created']}")
        logger.info(f"  - Skipped: {result['skipped']}")
        logger.info(f"  - Total processed: {result['total']}")

        if result.get('errors'):
            logger.warning(f"  - Errors: {len(result['errors'])}")
            for error in result['errors'][:5]:  # Show first 5 errors
                logger.warning(f"    {error}")

        return True

    except Exception as e:
        logger.error(f"Failed to create GitHub issues: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Create GitHub issues for vulnerabilities')
    parser.add_argument('results_file', help='Path to scan results JSON file')
    parser.add_argument(
        '--severity',
        '-s',
        nargs='+',
        default=['critical', 'high'],
        choices=['critical', 'high', 'medium', 'low', 'info'],
        help='Severity levels to create issues for (default: critical high)'
    )
    parser.add_argument(
        '--labels',
        '-l',
        nargs='+',
        default=['security', 'automated'],
        help='Additional labels to add to issues'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run - don\'t actually create issues'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Verify file exists
    if not Path(args.results_file).exists():
        logger.error(f"Results file not found: {args.results_file}")
        sys.exit(1)

    if args.dry_run:
        logger.info("DRY RUN MODE - No issues will be created")

    # Create issues
    success = create_issues_from_results(
        args.results_file,
        args.severity,
        args.dry_run,
        args.labels
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
