"""
Scan Executor
Orchestrates the complete scan process from start to finish
"""

import os
import time
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .zap_scanner import ZAPScanner
from .scan_result_parser import ScanResultParser

logger = logging.getLogger(__name__)


class ScanExecutor:
    """
    Executes complete security scan workflow
    """

    def __init__(
        self,
        config: Dict[str, Any],
        output_dir: str = "reports"
    ):
        """
        Initialize Scan Executor

        Args:
            config: Application and scan configuration
            output_dir: Directory for scan outputs
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scan_id = str(uuid.uuid4())
        self.scanner = None
        self.scan_results = {}

    def execute_scan(self) -> Dict[str, Any]:
        """
        Execute complete scan workflow

        Returns:
            Scan results dictionary

        Raises:
            Exception: If scan fails
        """
        logger.info(f"Starting scan execution for scan ID: {self.scan_id}")

        try:
            # Initialize scanner
            self._initialize_scanner()

            # Get scan configuration
            scan_config = self.config.get('application', {}).get('scan', {})
            app_config = self.config.get('application', {})
            target_url = app_config.get('url')

            if not target_url:
                raise ValueError("Target URL not specified in configuration")

            logger.info(f"Target URL: {target_url}")

            # Record start time
            start_time = datetime.utcnow()
            self.scan_results['started_at'] = start_time.isoformat()
            self.scan_results['target_url'] = target_url
            self.scan_results['scan_type'] = scan_config.get('type', 'full')

            # Get scan policy configuration
            policy_config = scan_config.get('policy_config', {})

            # Step 1: Spider scan
            if policy_config.get('spider', {}).get('enabled', True):
                logger.info("Step 1: Running spider scan...")
                self._run_spider_scan(target_url, policy_config.get('spider', {}))
            else:
                logger.info("Spider scan disabled, skipping...")

            # Step 2: AJAX spider (if enabled)
            if policy_config.get('ajax_spider', {}).get('enabled', False):
                logger.info("Step 2: Running AJAX spider scan...")
                self._run_ajax_spider_scan(target_url, policy_config.get('ajax_spider', {}))
            else:
                logger.info("AJAX spider disabled, skipping...")

            # Step 3: Passive scan (wait for completion)
            logger.info("Step 3: Waiting for passive scan...")
            self._wait_for_passive_scan()

            # Step 4: Active scan
            if policy_config.get('active_scan', {}).get('enabled', True):
                logger.info("Step 4: Running active scan...")
                self._run_active_scan(target_url, policy_config.get('active_scan', {}))
            else:
                logger.info("Active scan disabled, skipping...")

            # Step 5: Collect results
            logger.info("Step 5: Collecting scan results...")
            alerts = self.scanner.get_alerts(target_url)

            # Parse results
            parser = ScanResultParser()
            parsed_results = parser.parse_alerts(alerts)

            # Record end time and duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.scan_results.update({
                'completed_at': end_time.isoformat(),
                'duration': int(duration),
                'status': 'completed',
                'vulnerabilities': parsed_results['vulnerabilities'],
                'statistics': parsed_results['statistics']
            })

            logger.info(f"Scan completed successfully in {duration:.0f} seconds")
            logger.info(f"Found {parsed_results['statistics']['total']} vulnerabilities")

            return self.scan_results

        except Exception as e:
            logger.error(f"Scan execution failed: {e}", exc_info=True)
            self.scan_results['status'] = 'failed'
            self.scan_results['error'] = str(e)
            raise

        finally:
            # Cleanup
            self._cleanup()

    def _initialize_scanner(self):
        """Initialize ZAP scanner"""
        logger.info("Initializing ZAP scanner...")

        zap_image = os.getenv('ZAP_IMAGE', 'ghcr.io/zaproxy/zaproxy:stable')
        self.scanner = ZAPScanner(zap_image=zap_image)

        # Start container
        self.scanner.start_container(
            scan_id=self.scan_id,
            memory_limit="2g",
            cpu_limit="2"
        )

        logger.info("ZAP scanner initialized")

    def _run_spider_scan(self, target_url: str, spider_config: Dict[str, Any]):
        """
        Run spider scan

        Args:
            target_url: Target URL
            spider_config: Spider configuration
        """
        max_depth = spider_config.get('max_depth', 5)
        max_children = spider_config.get('max_children', 10)

        scan_id = self.scanner.spider_scan(
            target_url=target_url,
            max_depth=max_depth,
            max_children=max_children
        )

        # Wait for completion
        success = self.scanner.wait_for_spider(scan_id, timeout=1800)

        if not success:
            logger.warning("Spider scan did not complete within timeout")

        self.scan_results['spider_scan_id'] = scan_id

    def _run_ajax_spider_scan(self, target_url: str, ajax_config: Dict[str, Any]):
        """
        Run AJAX spider scan

        Args:
            target_url: Target URL
            ajax_config: AJAX spider configuration
        """
        max_duration = ajax_config.get('max_duration', 10)

        result = self.scanner.ajax_spider_scan(
            target_url=target_url,
            max_duration=max_duration
        )

        logger.info(f"AJAX spider result: {result}")

    def _wait_for_passive_scan(self, timeout: int = 300):
        """
        Wait for passive scan to complete

        Args:
            timeout: Maximum time to wait
        """
        logger.info("Waiting for passive scan to complete...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            progress = self.scanner.get_scan_progress()

            if progress.get('passive_scan_complete', False):
                logger.info("Passive scan completed")
                return

            records_to_scan = progress.get('records_to_scan', 0)
            logger.debug(f"Passive scan in progress: {records_to_scan} records remaining")
            time.sleep(5)

        logger.warning("Passive scan timeout reached")

    def _run_active_scan(self, target_url: str, active_config: Dict[str, Any]):
        """
        Run active scan

        Args:
            target_url: Target URL
            active_config: Active scan configuration
        """
        scan_id = self.scanner.active_scan(target_url=target_url)

        # Get timeout from config
        scan_config = self.config.get('application', {}).get('scan', {})
        timeout = scan_config.get('timeout', 7200)

        # Wait for completion
        success = self.scanner.wait_for_active_scan(scan_id, timeout=timeout)

        if not success:
            logger.warning("Active scan did not complete within timeout")

        self.scan_results['active_scan_id'] = scan_id

    def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up scan resources...")

        if self.scanner:
            try:
                # Get logs before stopping
                logs = self.scanner.get_container_logs()
                log_file = self.output_dir / f"{self.scan_id}_zap.log"
                with open(log_file, 'w') as f:
                    f.write(logs)
                logger.info(f"ZAP logs saved to {log_file}")
            except Exception as e:
                logger.error(f"Error saving logs: {e}")

            # Stop container
            try:
                self.scanner.shutdown()
                self.scanner.stop_container()
            except Exception as e:
                logger.error(f"Error stopping scanner: {e}")

        logger.info("Cleanup completed")

    def get_scan_id(self) -> str:
        """
        Get scan ID

        Returns:
            Scan ID
        """
        return self.scan_id

    def get_scan_results(self) -> Dict[str, Any]:
        """
        Get scan results

        Returns:
            Scan results dictionary
        """
        return self.scan_results
