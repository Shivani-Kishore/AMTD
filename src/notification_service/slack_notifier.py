"""
Slack Notification Service
Sends Slack notifications for scan results via webhooks
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send Slack notifications for security scan results"""

    def __init__(self, webhook_url: Optional[str] = None, channel: Optional[str] = None):
        """
        Initialize Slack Notifier

        Args:
            webhook_url: Slack webhook URL
            channel: Default channel to post to (optional)
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL', '')
        self.channel = channel or os.getenv('SLACK_CHANNEL', '')

        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")

        logger.info("Slack Notifier initialized")

    def send_scan_notification(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        report_url: Optional[str] = None,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send scan completion notification to Slack

        Args:
            scan_info: Scan information dictionary
            statistics: Vulnerability statistics
            report_url: URL to full report
            channel: Channel to post to (overrides default)

        Returns:
            True if sent successfully
        """
        try:
            if not self.webhook_url:
                logger.error("Slack webhook URL not configured")
                return False

            logger.info("Sending scan notification to Slack")

            # Determine severity and color
            severity = self._determine_severity(statistics)
            color = self._severity_color(severity)

            # Build message
            message = self._build_scan_message(
                scan_info,
                statistics,
                severity,
                color,
                report_url
            )

            # Set channel if provided
            if channel or self.channel:
                message['channel'] = channel or self.channel

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def send_failure_notification(
        self,
        scan_info: Dict[str, Any],
        error_message: str,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send scan failure notification to Slack

        Args:
            scan_info: Scan information
            error_message: Error message
            channel: Channel to post to

        Returns:
            True if sent successfully
        """
        try:
            if not self.webhook_url:
                logger.error("Slack webhook URL not configured")
                return False

            logger.info("Sending failure notification to Slack")

            message = self._build_failure_message(scan_info, error_message)

            if channel or self.channel:
                message['channel'] = channel or self.channel

            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send Slack failure notification: {e}")
            return False

    def send_threshold_alert(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        exceeded_thresholds: Dict[str, Dict[str, int]],
        channel: Optional[str] = None
    ) -> bool:
        """
        Send threshold exceeded alert to Slack

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            exceeded_thresholds: Dictionary of exceeded thresholds
            channel: Channel to post to

        Returns:
            True if sent successfully
        """
        try:
            if not self.webhook_url:
                logger.error("Slack webhook URL not configured")
                return False

            logger.info("Sending threshold alert to Slack")

            message = self._build_threshold_alert(
                scan_info,
                statistics,
                exceeded_thresholds
            )

            if channel or self.channel:
                message['channel'] = channel or self.channel

            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send Slack threshold alert: {e}")
            return False

    def send_custom_message(
        self,
        text: str,
        attachments: Optional[List[Dict]] = None,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send custom Slack message

        Args:
            text: Message text
            attachments: Slack attachments (optional)
            channel: Channel to post to

        Returns:
            True if sent successfully
        """
        try:
            if not self.webhook_url:
                logger.error("Slack webhook URL not configured")
                return False

            message = {'text': text}

            if attachments:
                message['attachments'] = attachments

            if channel or self.channel:
                message['channel'] = channel or self.channel

            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send custom Slack message: {e}")
            return False

    def _build_scan_message(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        severity: str,
        color: str,
        report_url: Optional[str]
    ) -> Dict[str, Any]:
        """
        Build Slack message for scan completion

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            severity: Overall severity
            color: Color code for attachment
            report_url: URL to report

        Returns:
            Slack message payload
        """
        app = scan_info.get('application', 'Unknown')
        scan_type = scan_info.get('scan_type', 'unknown').upper()
        target = scan_info.get('target_url', 'Unknown')

        # Build summary text
        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)
        total = statistics.get('total', 0)

        if critical > 0:
            icon = ':rotating_light:'
            summary = f"{icon} *Critical Issues Found* - {critical} critical vulnerabilities detected!"
        elif high > 0:
            icon = ':warning:'
            summary = f"{icon} *High Severity Issues* - {high} high severity vulnerabilities found."
        elif total > 0:
            icon = ':mag:'
            summary = f"{icon} Scan complete - {total} issues identified."
        else:
            icon = ':white_check_mark:'
            summary = f"{icon} *Clean Scan* - No vulnerabilities detected!"

        # Build fields
        fields = [
            {
                'title': 'Application',
                'value': app,
                'short': True
            },
            {
                'title': 'Scan Type',
                'value': scan_type,
                'short': True
            },
            {
                'title': 'Critical',
                'value': str(statistics.get('critical', 0)),
                'short': True
            },
            {
                'title': 'High',
                'value': str(statistics.get('high', 0)),
                'short': True
            },
            {
                'title': 'Medium',
                'value': str(statistics.get('medium', 0)),
                'short': True
            },
            {
                'title': 'Low',
                'value': str(statistics.get('low', 0)),
                'short': True
            },
            {
                'title': 'Total Vulnerabilities',
                'value': str(total),
                'short': True
            },
            {
                'title': 'Target',
                'value': target,
                'short': False
            }
        ]

        # Build actions
        actions = []
        if report_url:
            actions.append({
                'type': 'button',
                'text': 'View Full Report',
                'url': report_url,
                'style': 'primary' if severity in ['critical', 'high'] else 'default'
            })

        attachment = {
            'fallback': f"Scan complete for {app}: {total} vulnerabilities",
            'color': color,
            'pretext': summary,
            'title': f'Security Scan Report - {app}',
            'fields': fields,
            'footer': 'AMTD Security Scanner',
            'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png',
            'ts': int(datetime.utcnow().timestamp())
        }

        if actions:
            attachment['actions'] = actions

        return {
            'text': f'Security scan completed for *{app}*',
            'attachments': [attachment]
        }

    def _build_failure_message(
        self,
        scan_info: Dict[str, Any],
        error_message: str
    ) -> Dict[str, Any]:
        """
        Build Slack message for scan failure

        Args:
            scan_info: Scan information
            error_message: Error message

        Returns:
            Slack message payload
        """
        app = scan_info.get('application', 'Unknown')
        scan_id = scan_info.get('scan_id', 'Unknown')

        attachment = {
            'fallback': f"Scan failed for {app}",
            'color': 'danger',
            'pretext': ':x: *Scan Failed*',
            'title': f'Scan Failure - {app}',
            'text': f"```{error_message}```",
            'fields': [
                {
                    'title': 'Application',
                    'value': app,
                    'short': True
                },
                {
                    'title': 'Scan ID',
                    'value': scan_id,
                    'short': True
                }
            ],
            'footer': 'AMTD Security Scanner',
            'ts': int(datetime.utcnow().timestamp())
        }

        return {
            'text': f'Scan failed for *{app}*',
            'attachments': [attachment]
        }

    def _build_threshold_alert(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        exceeded_thresholds: Dict[str, Dict[str, int]]
    ) -> Dict[str, Any]:
        """
        Build Slack message for threshold alert

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            exceeded_thresholds: Exceeded thresholds

        Returns:
            Slack message payload
        """
        app = scan_info.get('application', 'Unknown')

        # Build threshold text
        threshold_text = []
        for severity, data in exceeded_thresholds.items():
            count = data.get('count', 0)
            threshold = data.get('threshold', 0)
            threshold_text.append(f"*{severity.upper()}*: {count} (threshold: {threshold})")

        attachment = {
            'fallback': f"Thresholds exceeded for {app}",
            'color': 'danger',
            'pretext': ':rotating_light: *ALERT: Vulnerability Thresholds Exceeded*',
            'title': f'Threshold Alert - {app}',
            'text': 'The following vulnerability thresholds have been exceeded:\n' + '\n'.join(threshold_text),
            'fields': [
                {
                    'title': 'Application',
                    'value': app,
                    'short': True
                },
                {
                    'title': 'Total Issues',
                    'value': str(statistics.get('total', 0)),
                    'short': True
                }
            ],
            'footer': 'AMTD Security Scanner',
            'ts': int(datetime.utcnow().timestamp())
        }

        return {
            'text': f'Vulnerability thresholds exceeded for *{app}*',
            'attachments': [attachment]
        }

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

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Get Slack color for severity"""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': '#ffc107',
            'low': '#17a2b8',
            'info': 'good'
        }
        return colors.get(severity.lower(), 'good')

    def test_connection(self) -> bool:
        """
        Test Slack webhook connection

        Returns:
            True if connection successful
        """
        try:
            if not self.webhook_url:
                logger.error("Webhook URL not configured")
                return False

            message = {
                'text': 'AMTD Slack integration test - connection successful!'
            }

            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Slack connection test successful")
                return True
            else:
                logger.error(f"Slack connection test failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    notifier = SlackNotifier()

    # Test connection
    if notifier.test_connection():
        print("Slack connection successful")

        # Send test notification
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

        notifier.send_scan_notification(
            scan_info=scan_info,
            statistics=statistics,
            report_url='http://jenkins/reports/scan-123'
        )
