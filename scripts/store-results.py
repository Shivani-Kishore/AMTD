#!/usr/bin/env python3
"""
Store Scan Results in Database
Stores scan results from JSON file into PostgreSQL database
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


def store_scan_results(results_file: str, application_name: str) -> bool:
    """
    Store scan results in database

    Args:
        results_file: Path to scan results JSON file
        application_name: Application name

    Returns:
        True if successful
    """
    try:
        # Load results
        with open(results_file, 'r') as f:
            results = json.load(f)

        scan_info = results.get('scan_info', {})
        statistics = results.get('statistics', {})
        vulnerabilities = results.get('vulnerabilities', [])

        logger.info(f"Storing results for application: {application_name}")

        # Get or create application
        application = db.execute_one(
            "SELECT * FROM applications WHERE name = %s",
            (application_name,)
        )

        if not application:
            logger.info(f"Creating new application: {application_name}")
            application = db.insert('applications', {
                'name': application_name,
                'target_url': scan_info.get('target_url', 'Unknown'),
                'status': 'active'
            })

        application_id = application['id']

        # Create scan record
        scan = db.insert('scans', {
            'application_id': application_id,
            'scan_type': scan_info.get('scan_type', 'full'),
            'target_url': scan_info.get('target_url'),
            'status': scan_info.get('status', 'completed'),
            'started_at': scan_info.get('started_at'),
            'completed_at': scan_info.get('completed_at'),
            'duration': scan_info.get('duration'),
            'critical_count': statistics.get('critical', 0),
            'high_count': statistics.get('high', 0),
            'medium_count': statistics.get('medium', 0),
            'low_count': statistics.get('low', 0),
            'info_count': statistics.get('info', 0),
            'total_count': statistics.get('total', 0)
        })

        scan_id = scan['id']
        logger.info(f"Created scan record: {scan_id}")

        # Store vulnerabilities
        vuln_count = 0
        for vuln in vulnerabilities:
            try:
                db.insert('vulnerabilities', {
                    'scan_id': scan_id,
                    'name': vuln.get('name'),
                    'severity': vuln.get('severity', 'info'),
                    'confidence': vuln.get('confidence'),
                    'description': vuln.get('description'),
                    'url': vuln.get('url'),
                    'method': vuln.get('method'),
                    'parameter': vuln.get('parameter'),
                    'evidence': vuln.get('evidence'),
                    'solution': vuln.get('solution'),
                    'reference': vuln.get('reference'),
                    'cwe_id': vuln.get('cwe_id'),
                    'category': vuln.get('category'),
                    'status': 'open'
                })
                vuln_count += 1
            except Exception as e:
                logger.warning(f"Failed to store vulnerability: {e}")

        logger.info(f"Stored {vuln_count} vulnerabilities")

        # Update statistics
        logger.info(f"Scan stored successfully:")
        logger.info(f"  - Application: {application_name}")
        logger.info(f"  - Scan ID: {scan_id}")
        logger.info(f"  - Total vulnerabilities: {vuln_count}")
        logger.info(f"  - Critical: {statistics.get('critical', 0)}")
        logger.info(f"  - High: {statistics.get('high', 0)}")

        return True

    except Exception as e:
        logger.error(f"Failed to store scan results: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Store scan results in database')
    parser.add_argument('results_file', help='Path to scan results JSON file')
    parser.add_argument('--application', '-a', required=True, help='Application name')
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

    # Store results
    success = store_scan_results(args.results_file, args.application)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
