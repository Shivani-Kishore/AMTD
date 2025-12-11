"""
Notification Manager
Coordinates all notification services (Email, Slack, GitHub, Webhooks)
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .email_notifier import EmailNotifier
from .slack_notifier import SlackNotifier
from .github_notifier import GitHubNotifier
from .webhook_notifier import WebhookNotifier

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages and coordinates all notification services"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Notification Manager

        Args:
            config: Notification configuration dictionary
        """
        self.config = config or {}

        # Initialize notifiers
        self.email_notifier = None
        self.slack_notifier = None
        self.github_notifier = None
        self.webhook_notifier = None

        # Setup notifiers based on configuration
        self._setup_notifiers()

        logger.info("Notification Manager initialized")

    def _setup_notifiers(self):
        """Setup all notification services based on configuration"""
        # Email notifier
        if self.config.get('email', {}).get('enabled', True):
            try:
                email_config = self.config.get('email', {})
                self.email_notifier = EmailNotifier(
                    smtp_host=email_config.get('smtp_host'),
                    smtp_port=email_config.get('smtp_port'),
                    smtp_user=email_config.get('smtp_user'),
                    smtp_password=email_config.get('smtp_password'),
                    smtp_use_tls=email_config.get('smtp_use_tls', True),
                    from_address=email_config.get('from_address'),
                    template_dir=email_config.get('template_dir')
                )
                logger.info("Email notifier enabled")
            except Exception as e:
                logger.error(f"Failed to initialize email notifier: {e}")

        # Slack notifier
        if self.config.get('slack', {}).get('enabled', True):
            try:
                slack_config = self.config.get('slack', {})
                self.slack_notifier = SlackNotifier(
                    webhook_url=slack_config.get('webhook_url'),
                    channel=slack_config.get('channel')
                )
                logger.info("Slack notifier enabled")
            except Exception as e:
                logger.error(f"Failed to initialize Slack notifier: {e}")

        # GitHub notifier
        if self.config.get('github', {}).get('enabled', True):
            try:
                github_config = self.config.get('github', {})
                self.github_notifier = GitHubNotifier(
                    token=github_config.get('token'),
                    repo_owner=github_config.get('repo_owner'),
                    repo_name=github_config.get('repo_name')
                )
                logger.info("GitHub notifier enabled")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub notifier: {e}")

        # Webhook notifier
        if self.config.get('webhook', {}).get('enabled', True):
            try:
                webhook_config = self.config.get('webhook', {})
                self.webhook_notifier = WebhookNotifier(
                    webhook_urls=webhook_config.get('urls', []),
                    timeout=webhook_config.get('timeout', 30),
                    retry_count=webhook_config.get('retry_count', 3)
                )
                logger.info("Webhook notifier enabled")
            except Exception as e:
                logger.error(f"Failed to initialize webhook notifier: {e}")

    def send_scan_notification(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        vulnerabilities: Optional[List[Dict]] = None,
        report_url: Optional[str] = None,
        report_files: Optional[Dict[str, str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send scan completion notifications across all enabled channels

        Args:
            scan_info: Scan information dictionary
            statistics: Vulnerability statistics
            vulnerabilities: List of vulnerabilities (optional)
            report_url: URL to full report
            report_files: Dictionary of report format to file path
            channels: Specific channels to use (email, slack, github, webhook)

        Returns:
            Dictionary with results from each channel
        """
        results = {}

        # Determine which channels to use
        active_channels = channels or ['email', 'slack', 'github', 'webhook']

        logger.info(f"Sending scan notifications via: {', '.join(active_channels)}")

        # Email notification
        if 'email' in active_channels and self.email_notifier:
            try:
                email_config = self.config.get('email', {})
                recipients = email_config.get('recipients', [])

                if recipients:
                    # Attach reports if available
                    attachments = []
                    if report_files:
                        if email_config.get('attach_pdf', False) and 'pdf' in report_files:
                            attachments.append(report_files['pdf'])
                        if email_config.get('attach_json', False) and 'json' in report_files:
                            attachments.append(report_files['json'])

                    success = self.email_notifier.send_scan_notification(
                        recipients=recipients,
                        scan_info=scan_info,
                        statistics=statistics,
                        report_url=report_url,
                        attachments=attachments if attachments else None
                    )
                    results['email'] = {'sent': success}
                else:
                    logger.warning("No email recipients configured")
                    results['email'] = {'sent': False, 'reason': 'no_recipients'}

            except Exception as e:
                logger.error(f"Email notification failed: {e}")
                results['email'] = {'sent': False, 'error': str(e)}

        # Slack notification
        if 'slack' in active_channels and self.slack_notifier:
            try:
                slack_config = self.config.get('slack', {})
                channel = slack_config.get('channel')

                success = self.slack_notifier.send_scan_notification(
                    scan_info=scan_info,
                    statistics=statistics,
                    report_url=report_url,
                    channel=channel
                )
                results['slack'] = {'sent': success}

            except Exception as e:
                logger.error(f"Slack notification failed: {e}")
                results['slack'] = {'sent': False, 'error': str(e)}

        # GitHub notification
        if 'github' in active_channels and self.github_notifier:
            try:
                github_config = self.config.get('github', {})

                # Create issues for vulnerabilities
                if github_config.get('create_issues', False) and vulnerabilities:
                    severity_filter = github_config.get('issue_severity_filter', ['critical', 'high'])
                    labels = github_config.get('issue_labels', [])

                    issue_results = self.github_notifier.create_issues_for_vulnerabilities(
                        vulnerabilities=vulnerabilities,
                        scan_info=scan_info,
                        severity_filter=severity_filter,
                        labels=labels
                    )
                    results['github_issues'] = issue_results

                # Upload SARIF report
                if github_config.get('upload_sarif', False) and report_files and 'sarif' in report_files:
                    sarif_uploaded = self.github_notifier.upload_sarif_report(
                        sarif_file_path=report_files['sarif'],
                        ref=github_config.get('ref')
                    )
                    results['github_sarif'] = {'uploaded': sarif_uploaded}

                # Create check run
                if github_config.get('create_check_run', False):
                    conclusion = 'success' if statistics.get('critical', 0) == 0 else 'failure'
                    check_run = self.github_notifier.create_check_run(
                        scan_info=scan_info,
                        statistics=statistics,
                        conclusion=conclusion,
                        report_url=report_url
                    )
                    results['github_check'] = {'created': check_run is not None}

            except Exception as e:
                logger.error(f"GitHub notification failed: {e}")
                results['github'] = {'error': str(e)}

        # Webhook notification
        if 'webhook' in active_channels and self.webhook_notifier:
            try:
                webhook_results = self.webhook_notifier.send_scan_notification(
                    scan_info=scan_info,
                    statistics=statistics,
                    vulnerabilities=vulnerabilities,
                    report_url=report_url
                )
                results['webhook'] = webhook_results

            except Exception as e:
                logger.error(f"Webhook notification failed: {e}")
                results['webhook'] = {'sent': 0, 'failed': 0, 'error': str(e)}

        logger.info(f"Notification results: {results}")
        return results

    def send_failure_notification(
        self,
        scan_info: Dict[str, Any],
        error_message: str,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send scan failure notifications

        Args:
            scan_info: Scan information
            error_message: Error message
            channels: Specific channels to use

        Returns:
            Dictionary with results from each channel
        """
        results = {}
        active_channels = channels or ['email', 'slack', 'webhook']

        logger.info(f"Sending failure notifications via: {', '.join(active_channels)}")

        # Email
        if 'email' in active_channels and self.email_notifier:
            try:
                recipients = self.config.get('email', {}).get('recipients', [])
                if recipients:
                    success = self.email_notifier.send_failure_notification(
                        recipients=recipients,
                        scan_info=scan_info,
                        error_message=error_message
                    )
                    results['email'] = {'sent': success}
            except Exception as e:
                logger.error(f"Email failure notification failed: {e}")
                results['email'] = {'sent': False, 'error': str(e)}

        # Slack
        if 'slack' in active_channels and self.slack_notifier:
            try:
                channel = self.config.get('slack', {}).get('channel')
                success = self.slack_notifier.send_failure_notification(
                    scan_info=scan_info,
                    error_message=error_message,
                    channel=channel
                )
                results['slack'] = {'sent': success}
            except Exception as e:
                logger.error(f"Slack failure notification failed: {e}")
                results['slack'] = {'sent': False, 'error': str(e)}

        # Webhook
        if 'webhook' in active_channels and self.webhook_notifier:
            try:
                webhook_results = self.webhook_notifier.send_failure_notification(
                    scan_info=scan_info,
                    error_message=error_message
                )
                results['webhook'] = webhook_results
            except Exception as e:
                logger.error(f"Webhook failure notification failed: {e}")
                results['webhook'] = {'error': str(e)}

        return results

    def send_threshold_alert(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        exceeded_thresholds: Dict[str, Dict[str, int]],
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send threshold exceeded alerts

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            exceeded_thresholds: Dictionary of exceeded thresholds
            channels: Specific channels to use

        Returns:
            Dictionary with results from each channel
        """
        results = {}
        active_channels = channels or ['email', 'slack', 'webhook']

        logger.info(f"Sending threshold alerts via: {', '.join(active_channels)}")

        # Email
        if 'email' in active_channels and self.email_notifier:
            try:
                recipients = self.config.get('email', {}).get('recipients', [])
                if recipients:
                    success = self.email_notifier.send_threshold_alert(
                        recipients=recipients,
                        scan_info=scan_info,
                        statistics=statistics,
                        exceeded_thresholds=exceeded_thresholds
                    )
                    results['email'] = {'sent': success}
            except Exception as e:
                logger.error(f"Email threshold alert failed: {e}")
                results['email'] = {'sent': False, 'error': str(e)}

        # Slack
        if 'slack' in active_channels and self.slack_notifier:
            try:
                channel = self.config.get('slack', {}).get('channel')
                success = self.slack_notifier.send_threshold_alert(
                    scan_info=scan_info,
                    statistics=statistics,
                    exceeded_thresholds=exceeded_thresholds,
                    channel=channel
                )
                results['slack'] = {'sent': success}
            except Exception as e:
                logger.error(f"Slack threshold alert failed: {e}")
                results['slack'] = {'sent': False, 'error': str(e)}

        # Webhook
        if 'webhook' in active_channels and self.webhook_notifier:
            try:
                webhook_results = self.webhook_notifier.send_threshold_alert(
                    scan_info=scan_info,
                    statistics=statistics,
                    exceeded_thresholds=exceeded_thresholds
                )
                results['webhook'] = webhook_results
            except Exception as e:
                logger.error(f"Webhook threshold alert failed: {e}")
                results['webhook'] = {'error': str(e)}

        return results

    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections to all notification services

        Returns:
            Dictionary with connection status for each service
        """
        results = {}

        if self.email_notifier:
            results['email'] = self.email_notifier.test_connection()

        if self.slack_notifier:
            results['slack'] = self.slack_notifier.test_connection()

        if self.github_notifier:
            results['github'] = self.github_notifier.test_connection()

        if self.webhook_notifier:
            webhook_tests = self.webhook_notifier.test_all_webhooks()
            results['webhook'] = webhook_tests.get('passed', 0) > 0

        logger.info(f"Connection test results: {results}")
        return results

    def get_active_channels(self) -> List[str]:
        """
        Get list of active notification channels

        Returns:
            List of active channel names
        """
        channels = []

        if self.email_notifier:
            channels.append('email')
        if self.slack_notifier:
            channels.append('slack')
        if self.github_notifier:
            channels.append('github')
        if self.webhook_notifier:
            channels.append('webhook')

        return channels


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Sample configuration
    config = {
        'email': {
            'enabled': True,
            'recipients': ['security@example.com'],
            'attach_pdf': True
        },
        'slack': {
            'enabled': True,
            'channel': '#security-alerts'
        },
        'github': {
            'enabled': True,
            'create_issues': True,
            'upload_sarif': True,
            'issue_severity_filter': ['critical', 'high']
        },
        'webhook': {
            'enabled': True,
            'urls': ['https://webhook.site/your-unique-url']
        }
    }

    manager = NotificationManager(config)

    # Test connections
    test_results = manager.test_all_connections()
    print(f"Connection tests: {test_results}")

    # Send notification
    scan_info = {
        'application': 'test-app',
        'scan_id': 'scan-123',
        'scan_type': 'full',
        'target_url': 'http://example.com'
    }

    statistics = {
        'critical': 2,
        'high': 5,
        'medium': 10,
        'low': 15,
        'info': 20,
        'total': 52
    }

    results = manager.send_scan_notification(
        scan_info=scan_info,
        statistics=statistics,
        report_url='http://jenkins/reports/scan-123'
    )
    print(f"Notification results: {results}")
