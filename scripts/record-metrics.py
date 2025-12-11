#!/usr/bin/env python3
"""
Record Metrics to Database
Records scan metrics to the metrics table for historical tracking
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from api.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_scan_metrics(
    results_file: str,
    application_name: str,
    scan_id: str = None
) -> bool:
    """
    Record scan metrics to database

    Args:
        results_file: Path to scan results JSON file
        application_name: Application name
        scan_id: Scan ID (optional)

    Returns:
        True if successful
    """
    try:
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)

        scan_info = results.get('scan_info', {})
        statistics = results.get('statistics', {})

        logger.info(f"Recording metrics for application: {application_name}")

        # Get application
        application = db.execute_one(
            "SELECT * FROM applications WHERE name = %s",
            (application_name,)
        )

        if not application:
            logger.error(f"Application not found: {application_name}")
            return False

        application_id = application['id']

        # Get scan ID if provided
        if not scan_id:
            # Get latest scan for this application
            latest_scan = db.execute_one(
                """
                SELECT id FROM scans
                WHERE application_id = %s
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (application_id,)
            )
            if latest_scan:
                scan_id = latest_scan['id']

        # Record metrics
        metrics = [
            ('vulnerability_count', 'critical', statistics.get('critical', 0)),
            ('vulnerability_count', 'high', statistics.get('high', 0)),
            ('vulnerability_count', 'medium', statistics.get('medium', 0)),
            ('vulnerability_count', 'low', statistics.get('low', 0)),
            ('vulnerability_count', 'info', statistics.get('info', 0)),
            ('vulnerability_count', 'total', statistics.get('total', 0)),
            ('scan_duration', 'seconds', scan_info.get('duration', 0))
        ]

        for metric_name, metric_type, value in metrics:
            try:
                db.insert('metrics', {
                    'scan_id': scan_id,
                    'application_id': application_id,
                    'metric_name': metric_name,
                    'metric_type': metric_type,
                    'value': float(value),
                    'recorded_at': datetime.utcnow()
                })
            except Exception as e:
                logger.warning(f"Failed to record metric {metric_name}: {e}")

        logger.info(f"Recorded {len(metrics)} metrics")
        return True

    except Exception as e:
        logger.error(f"Failed to record metrics: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Record scan metrics to database')
    parser.add_argument('results_file', help='Path to scan results JSON file')
    parser.add_argument('--application', '-a', required=True, help='Application name')
    parser.add_argument('--scan-id', '-s', help='Scan ID (optional)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Verify file exists
    if not Path(args.results_file).exists():
        logger.error(f"Results file not found: {args.results_file}")
        sys.exit(1)

    # Test database connection
    if not db.test_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)

    # Record metrics
    success = record_scan_metrics(
        args.results_file,
        args.application_name,
        args.scan_id
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
