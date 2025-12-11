"""
Email Notification Service
Sends email notifications for scan results
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Send email notifications for security scan results"""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_use_tls: bool = True,
        from_address: Optional[str] = None,
        template_dir: Optional[str] = None
    ):
        """
        Initialize Email Notifier

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            smtp_use_tls: Use TLS encryption
            from_address: Sender email address
            template_dir: Directory containing email templates
        """
        # Load from environment if not provided
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER', '')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD', '')
        self.smtp_use_tls = smtp_use_tls
        self.from_address = from_address or os.getenv('SMTP_FROM', 'amtd@example.com')

        # Setup template environment
        if template_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            template_dir = base_dir / "templates" / "notifications"

        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register custom filters
        self.env.filters['severity_color'] = self._severity_color

        logger.info(f"Email Notifier initialized with SMTP host: {self.smtp_host}:{self.smtp_port}")

    def send_scan_notification(
        self,
        recipients: List[str],
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        report_url: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send scan completion notification

        Args:
            recipients: List of email addresses
            scan_info: Scan information dictionary
            statistics: Vulnerability statistics
            report_url: URL to full report
            attachments: List of file paths to attach

        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"Sending scan notification to {len(recipients)} recipients")

            # Determine severity
            severity = self._determine_severity(statistics)

            # Prepare template data
            template_data = {
                'scan_info': scan_info,
                'statistics': statistics,
                'severity': severity,
                'report_url': report_url,
                'severity_color': self._severity_color(severity)
            }

            # Render email body
            html_body = self._render_template('scan_notification.html', template_data)
            text_body = self._render_template('scan_notification.txt', template_data)

            # Create subject
            subject = self._create_subject(scan_info, statistics, severity)

            # Send email
            return self._send_email(
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                attachments=attachments
            )

        except Exception as e:
            logger.error(f"Failed to send scan notification: {e}")
            return False

    def send_failure_notification(
        self,
        recipients: List[str],
        scan_info: Dict[str, Any],
        error_message: str
    ) -> bool:
        """
        Send scan failure notification

        Args:
            recipients: List of email addresses
            scan_info: Scan information
            error_message: Error message

        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"Sending failure notification to {len(recipients)} recipients")

            template_data = {
                'scan_info': scan_info,
                'error_message': error_message
            }

            html_body = self._render_template('scan_failure.html', template_data)
            text_body = self._render_template('scan_failure.txt', template_data)

            subject = f"[AMTD] Scan Failed - {scan_info.get('application', 'Unknown')}"

            return self._send_email(
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")
            return False

    def send_threshold_alert(
        self,
        recipients: List[str],
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        exceeded_thresholds: Dict[str, Dict[str, int]]
    ) -> bool:
        """
        Send threshold exceeded alert

        Args:
            recipients: List of email addresses
            scan_info: Scan information
            statistics: Vulnerability statistics
            exceeded_thresholds: Dictionary of exceeded thresholds

        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"Sending threshold alert to {len(recipients)} recipients")

            template_data = {
                'scan_info': scan_info,
                'statistics': statistics,
                'exceeded_thresholds': exceeded_thresholds
            }

            html_body = self._render_template('threshold_alert.html', template_data)
            text_body = self._render_template('threshold_alert.txt', template_data)

            subject = f"[AMTD] ALERT: Thresholds Exceeded - {scan_info.get('application', 'Unknown')}"

            return self._send_email(
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

        except Exception as e:
            logger.error(f"Failed to send threshold alert: {e}")
            return False

    def _send_email(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email via SMTP

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            attachments: List of file paths to attach

        Returns:
            True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_address
            msg['To'] = ', '.join(recipients)

            # Attach text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Attach files
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)

            # Connect to SMTP server
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            # Login if credentials provided
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # Send email
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """
        Attach file to email message

        Args:
            msg: Email message
            file_path: Path to file to attach
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Attachment not found: {file_path}")
                return

            with open(path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={path.name}'
            )

            msg.attach(part)
            logger.debug(f"Attached file: {path.name}")

        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        Render email template

        Args:
            template_name: Template file name
            data: Template data

        Returns:
            Rendered template content
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            # Return basic fallback content
            if template_name.endswith('.html'):
                return f"<html><body><h1>AMTD Notification</h1><p>Error rendering template: {e}</p></body></html>"
            else:
                return f"AMTD Notification\n\nError rendering template: {e}"

    def _create_subject(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        severity: str
    ) -> str:
        """
        Create email subject line

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            severity: Overall severity

        Returns:
            Email subject
        """
        app = scan_info.get('application', 'Unknown')
        total = statistics.get('total', 0)

        severity_prefix = {
            'critical': '[CRITICAL]',
            'high': '[HIGH]',
            'medium': '[MEDIUM]',
            'low': '[LOW]',
            'info': '[INFO]'
        }.get(severity, '')

        return f"[AMTD] {severity_prefix} Scan Complete - {app} ({total} issues)"

    def _determine_severity(self, statistics: Dict[str, int]) -> str:
        """
        Determine overall severity from statistics

        Args:
            statistics: Vulnerability statistics

        Returns:
            Severity level
        """
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
        """
        Get color code for severity

        Args:
            severity: Severity level

        Returns:
            Hex color code
        """
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#17a2b8',
            'info': '#6c757d'
        }
        return colors.get(severity.lower(), '#6c757d')

    def test_connection(self) -> bool:
        """
        Test SMTP connection

        Returns:
            True if connection successful
        """
        try:
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)

            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            server.quit()
            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    notifier = EmailNotifier()

    # Test connection
    if notifier.test_connection():
        print("SMTP connection successful")

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
            recipients=['test@example.com'],
            scan_info=scan_info,
            statistics=statistics,
            report_url='http://jenkins/reports/scan-123'
        )
