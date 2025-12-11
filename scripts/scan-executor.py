#!/usr/bin/env python3
"""
Scan Executor Script
Main script to execute security scans on configured applications
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager
from src.scan_manager import ScanExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/scan-executor.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='AMTD Scan Executor - Execute security scans on web applications'
    )

    parser.add_argument(
        '--application', '-a',
        required=True,
        help='Application name (config file name without .yaml)'
    )

    parser.add_argument(
        '--scan-type', '-t',
        choices=['full', 'quick', 'incremental'],
        default='full',
        help='Type of scan to perform'
    )

    parser.add_argument(
        '--environment', '-e',
        default=None,
        help='Environment (development, staging, production)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        default='reports',
        help='Output directory for reports'
    )

    parser.add_argument(
        '--config-dir', '-c',
        default='config',
        help='Configuration directory'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration without running scan'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 80)
    logger.info("AMTD Scan Executor")
    logger.info("=" * 80)
    logger.info(f"Application: {args.application}")
    logger.info(f"Scan Type: {args.scan_type}")
    logger.info(f"Environment: {args.environment or 'default'}")

    try:
        # Initialize configuration manager
        logger.info("Loading configuration...")
        config_mgr = ConfigManager(config_dir=args.config_dir)

        # Load application configuration
        config = config_mgr.get_application_config(
            app_name=args.application,
            environment=args.environment
        )

        logger.info(f"Configuration loaded successfully for '{args.application}'")

        # Override scan type if specified
        if 'application' not in config:
            config['application'] = {}
        if 'scan' not in config['application']:
            config['application']['scan'] = {}

        config['application']['scan']['type'] = args.scan_type

        # Display configuration summary
        app_config = config.get('application', {})
        logger.info("-" * 80)
        logger.info("Configuration Summary:")
        logger.info(f"  Name: {app_config.get('name', 'N/A')}")
        logger.info(f"  URL: {app_config.get('url', 'N/A')}")
        logger.info(f"  Owner: {app_config.get('owner', 'N/A')}")
        logger.info(f"  Criticality: {app_config.get('criticality', 'N/A')}")

        scan_config = app_config.get('scan', {})
        logger.info(f"  Scan Type: {scan_config.get('type', 'N/A')}")
        logger.info(f"  Scan Policy: {scan_config.get('policy', 'N/A')}")
        logger.info(f"  Timeout: {scan_config.get('timeout', 'N/A')}s")

        thresholds = scan_config.get('thresholds', {})
        logger.info(f"  Thresholds: Critical={thresholds.get('critical')}, "
                   f"High={thresholds.get('high')}, "
                   f"Medium={thresholds.get('medium')}")
        logger.info("-" * 80)

        # Validate-only mode
        if args.validate_only:
            logger.info("Validation successful! (--validate-only mode)")
            logger.info("Configuration is valid and ready for scanning")
            return 0

        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Execute scan
        logger.info("Initializing scan executor...")
        executor = ScanExecutor(config=config, output_dir=str(output_dir))

        logger.info("Starting scan execution...")
        logger.info("=" * 80)

        results = executor.execute_scan()

        logger.info("=" * 80)
        logger.info("Scan completed successfully!")
        logger.info("-" * 80)

        # Display results summary
        statistics = results.get('statistics', {})
        logger.info("Vulnerability Summary:")
        logger.info(f"  Critical: {statistics.get('critical', 0)}")
        logger.info(f"  High: {statistics.get('high', 0)}")
        logger.info(f"  Medium: {statistics.get('medium', 0)}")
        logger.info(f"  Low: {statistics.get('low', 0)}")
        logger.info(f"  Info: {statistics.get('info', 0)}")
        logger.info(f"  Total: {statistics.get('total', 0)}")
        logger.info("-" * 80)

        # Save results to JSON file
        scan_id = executor.get_scan_id()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        results_file = output_dir / f"{args.application}_{timestamp}_{scan_id}.json"

        logger.info(f"Saving results to: {results_file}")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Check thresholds
        logger.info("-" * 80)
        logger.info("Checking vulnerability thresholds...")

        threshold_exceeded = False

        if thresholds.get('critical') is not None:
            if statistics.get('critical', 0) > thresholds['critical']:
                logger.error(f"❌ Critical vulnerabilities ({statistics['critical']}) "
                           f"exceed threshold ({thresholds['critical']})")
                threshold_exceeded = True

        if thresholds.get('high') is not None:
            if statistics.get('high', 0) > thresholds['high']:
                logger.error(f"❌ High vulnerabilities ({statistics['high']}) "
                           f"exceed threshold ({thresholds['high']})")
                threshold_exceeded = True

        if thresholds.get('medium') is not None:
            if statistics.get('medium', 0) > thresholds['medium']:
                logger.error(f"❌ Medium vulnerabilities ({statistics['medium']}) "
                           f"exceed threshold ({thresholds['medium']})")
                threshold_exceeded = True

        if not threshold_exceeded:
            logger.info("✅ All vulnerability thresholds passed")

        logger.info("-" * 80)
        logger.info(f"Scan ID: {scan_id}")
        logger.info(f"Duration: {results.get('duration', 0)}s")
        logger.info(f"Results: {results_file}")
        logger.info("=" * 80)

        # Exit with appropriate code
        return 1 if threshold_exceeded else 0

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error(f"Make sure the configuration file exists at: config/applications/{args.application}.yaml")
        return 2

    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        return 3

    except Exception as e:
        logger.error(f"Scan execution failed: {e}", exc_info=True)
        return 4


if __name__ == "__main__":
    sys.exit(main())
