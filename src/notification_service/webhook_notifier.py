"""
Webhook Notification Service
Sends HTTP webhook notifications for scan results
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Send webhook notifications for security scan results"""

    def __init__(
        self,
        webhook_urls: Optional[List[str]] = None,
        timeout: int = 30,
        retry_count: int = 3
    ):
        """
        Initialize Webhook Notifier

        Args:
            webhook_urls: List of webhook URLs to send to
            timeout: Request timeout in seconds
            retry_count: Number of retries on failure
        """
        self.webhook_urls = webhook_urls or []
        self.timeout = timeout
        self.retry_count = retry_count

        # Load from environment if not provided
        if not self.webhook_urls:
            env_webhooks = os.getenv('WEBHOOK_URLS', '')
            if env_webhooks:
                self.webhook_urls = [url.strip() for url in env_webhooks.split(',')]

        logger.info(f"Webhook Notifier initialized with {len(self.webhook_urls)} webhooks")

    def send_scan_notification(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        vulnerabilities: Optional[List[Dict]] = None,
        report_url: Optional[str] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send scan completion notification via webhooks

        Args:
            scan_info: Scan information dictionary
            statistics: Vulnerability statistics
            vulnerabilities: List of vulnerabilities (optional)
            report_url: URL to full report
            custom_data: Additional custom data to include

        Returns:
            Dictionary with success/failure counts per webhook
        """
        try:
            if not self.webhook_urls:
                logger.warning("No webhook URLs configured")
                return {'sent': 0, 'failed': 0}

            logger.info(f"Sending scan notification to {len(self.webhook_urls)} webhooks")

            # Build payload
            payload = self._build_scan_payload(
                scan_info,
                statistics,
                vulnerabilities,
                report_url,
                custom_data
            )

            # Send to all webhooks
            results = self._send_to_webhooks(payload)

            logger.info(f"Webhooks sent: {results['sent']}, failed: {results['failed']}")
            return results

        except Exception as e:
            logger.error(f"Failed to send webhook notifications: {e}")
            return {'sent': 0, 'failed': len(self.webhook_urls), 'error': str(e)}

    def send_failure_notification(
        self,
        scan_info: Dict[str, Any],
        error_message: str,
        custom_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send scan failure notification via webhooks

        Args:
            scan_info: Scan information
            error_message: Error message
            custom_data: Additional custom data

        Returns:
            Dictionary with success/failure counts
        """
        try:
            if not self.webhook_urls:
                logger.warning("No webhook URLs configured")
                return {'sent': 0, 'failed': 0}

            logger.info("Sending failure notification to webhooks")

            payload = self._build_failure_payload(scan_info, error_message, custom_data)
            results = self._send_to_webhooks(payload)

            return results

        except Exception as e:
            logger.error(f"Failed to send failure webhook: {e}")
            return {'sent': 0, 'failed': len(self.webhook_urls), 'error': str(e)}

    def send_threshold_alert(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        exceeded_thresholds: Dict[str, Dict[str, int]],
        custom_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send threshold exceeded alert via webhooks

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            exceeded_thresholds: Dictionary of exceeded thresholds
            custom_data: Additional custom data

        Returns:
            Dictionary with success/failure counts
        """
        try:
            if not self.webhook_urls:
                logger.warning("No webhook URLs configured")
                return {'sent': 0, 'failed': 0}

            logger.info("Sending threshold alert to webhooks")

            payload = self._build_threshold_payload(
                scan_info,
                statistics,
                exceeded_thresholds,
                custom_data
            )

            results = self._send_to_webhooks(payload)
            return results

        except Exception as e:
            logger.error(f"Failed to send threshold webhook: {e}")
            return {'sent': 0, 'failed': len(self.webhook_urls), 'error': str(e)}

    def send_custom_webhook(
        self,
        event_type: str,
        data: Dict[str, Any],
        urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send custom webhook payload

        Args:
            event_type: Type of event
            data: Custom data to send
            urls: Specific URLs to send to (overrides default)

        Returns:
            Dictionary with success/failure counts
        """
        try:
            target_urls = urls or self.webhook_urls

            if not target_urls:
                logger.warning("No webhook URLs configured")
                return {'sent': 0, 'failed': 0}

            payload = {
                'event': event_type,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'data': data,
                'source': 'AMTD'
            }

            results = self._send_to_webhooks(payload, urls=target_urls)
            return results

        except Exception as e:
            logger.error(f"Failed to send custom webhook: {e}")
            return {'sent': 0, 'failed': len(target_urls), 'error': str(e)}

    def _send_to_webhooks(
        self,
        payload: Dict[str, Any],
        urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send payload to all webhook URLs

        Args:
            payload: Data to send
            urls: Specific URLs to send to (overrides default)

        Returns:
            Dictionary with success/failure counts and details
        """
        target_urls = urls or self.webhook_urls
        sent_count = 0
        failed_count = 0
        results = []

        for url in target_urls:
            success = self._send_webhook(url, payload)
            if success:
                sent_count += 1
                results.append({'url': url, 'status': 'success'})
            else:
                failed_count += 1
                results.append({'url': url, 'status': 'failed'})

        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(target_urls),
            'results': results
        }

    def _send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        """
        Send webhook to single URL with retry logic

        Args:
            url: Webhook URL
            payload: Data to send

        Returns:
            True if successful
        """
        for attempt in range(self.retry_count):
            try:
                logger.debug(f"Sending webhook to {url} (attempt {attempt + 1}/{self.retry_count})")

                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'AMTD-Webhook-Notifier/1.0'
                    },
                    timeout=self.timeout
                )

                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook sent successfully to {url}")
                    return True
                else:
                    logger.warning(f"Webhook failed: {url} - {response.status_code}")

                    # Don't retry for client errors
                    if 400 <= response.status_code < 500:
                        return False

            except requests.exceptions.Timeout:
                logger.warning(f"Webhook timeout: {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Webhook error: {url} - {e}")

            # Wait before retry (exponential backoff)
            if attempt < self.retry_count - 1:
                import time
                time.sleep(2 ** attempt)

        logger.error(f"Webhook failed after {self.retry_count} attempts: {url}")
        return False

    def _build_scan_payload(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        vulnerabilities: Optional[List[Dict]],
        report_url: Optional[str],
        custom_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build payload for scan completion webhook"""
        payload = {
            'event': 'scan.completed',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'scan_info': scan_info,
            'statistics': statistics,
            'severity': self._determine_severity(statistics),
            'source': 'AMTD'
        }

        if report_url:
            payload['report_url'] = report_url

        if vulnerabilities:
            # Include vulnerabilities (limit to prevent huge payloads)
            payload['vulnerabilities'] = vulnerabilities[:100]
            if len(vulnerabilities) > 100:
                payload['vulnerabilities_truncated'] = True
                payload['total_vulnerabilities'] = len(vulnerabilities)

        if custom_data:
            payload['custom'] = custom_data

        return payload

    def _build_failure_payload(
        self,
        scan_info: Dict[str, Any],
        error_message: str,
        custom_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build payload for scan failure webhook"""
        payload = {
            'event': 'scan.failed',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'scan_info': scan_info,
            'error': error_message,
            'source': 'AMTD'
        }

        if custom_data:
            payload['custom'] = custom_data

        return payload

    def _build_threshold_payload(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        exceeded_thresholds: Dict[str, Dict[str, int]],
        custom_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build payload for threshold alert webhook"""
        payload = {
            'event': 'threshold.exceeded',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'scan_info': scan_info,
            'statistics': statistics,
            'exceeded_thresholds': exceeded_thresholds,
            'source': 'AMTD'
        }

        if custom_data:
            payload['custom'] = custom_data

        return payload

    def _determine_severity(self, statistics: Dict[str, int]) -> str:
        """Determine overall severity from statistics"""
        if statistics.get('critical', 0) > 0:
            return 'critical'
        elif statistics.get('high', 0) > 0:
            return 'high'
        elif statistics.get('medium', 0) > 0:
            return 'medium'
        elif statistics.get('low', 0) > 0:
            return 'low'
        else:
            return 'info'

    def add_webhook_url(self, url: str):
        """
        Add a webhook URL to the list

        Args:
            url: Webhook URL to add
        """
        if url not in self.webhook_urls:
            self.webhook_urls.append(url)
            logger.info(f"Added webhook URL: {url}")

    def remove_webhook_url(self, url: str):
        """
        Remove a webhook URL from the list

        Args:
            url: Webhook URL to remove
        """
        if url in self.webhook_urls:
            self.webhook_urls.remove(url)
            logger.info(f"Removed webhook URL: {url}")

    def test_webhook(self, url: str) -> bool:
        """
        Test a webhook URL with a test payload

        Args:
            url: Webhook URL to test

        Returns:
            True if successful
        """
        try:
            test_payload = {
                'event': 'test',
                'message': 'AMTD webhook test',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'AMTD'
            }

            return self._send_webhook(url, test_payload)

        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False

    def test_all_webhooks(self) -> Dict[str, Any]:
        """
        Test all configured webhooks

        Returns:
            Dictionary with test results
        """
        if not self.webhook_urls:
            logger.warning("No webhook URLs configured")
            return {'tested': 0, 'passed': 0, 'failed': 0}

        logger.info(f"Testing {len(self.webhook_urls)} webhooks")

        passed = 0
        failed = 0
        results = []

        for url in self.webhook_urls:
            success = self.test_webhook(url)
            if success:
                passed += 1
                results.append({'url': url, 'status': 'passed'})
            else:
                failed += 1
                results.append({'url': url, 'status': 'failed'})

        return {
            'tested': len(self.webhook_urls),
            'passed': passed,
            'failed': failed,
            'results': results
        }


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Example webhook URL (replace with actual endpoint)
    notifier = WebhookNotifier(webhook_urls=['https://webhook.site/your-unique-url'])

    # Test webhooks
    test_results = notifier.test_all_webhooks()
    print(f"Test results: {test_results}")

    # Send scan notification
    scan_info = {
        'application': 'test-app',
        'scan_id': 'scan-123',
        'scan_type': 'full',
        'target_url': 'http://example.com',
        'started_at': '2025-01-01T00:00:00Z',
        'completed_at': '2025-01-01T01:00:00Z'
    }

    statistics = {
        'critical': 2,
        'high': 5,
        'medium': 10,
        'low': 15,
        'info': 20,
        'total': 52
    }

    results = notifier.send_scan_notification(
        scan_info=scan_info,
        statistics=statistics,
        report_url='http://jenkins/reports/scan-123'
    )
    print(f"Webhook results: {results}")
