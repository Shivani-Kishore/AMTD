"""
AMTD Notification Service Module
Handles notifications via Email, Slack, GitHub, and Webhooks
"""

from .email_notifier import EmailNotifier
from .slack_notifier import SlackNotifier
from .github_notifier import GitHubNotifier
from .webhook_notifier import WebhookNotifier
from .notification_manager import NotificationManager

__all__ = [
    'EmailNotifier',
    'SlackNotifier',
    'GitHubNotifier',
    'WebhookNotifier',
    'NotificationManager'
]

__version__ = '1.0.0'
