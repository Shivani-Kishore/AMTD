"""
API Authentication Module
Simple API key authentication for REST endpoints
"""

import os
import logging
from functools import wraps
from flask import request, jsonify
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class APIKeyAuth:
    """API Key authentication manager"""

    def __init__(self, api_keys: Optional[list] = None):
        """
        Initialize API key authentication

        Args:
            api_keys: List of valid API keys
        """
        # Load API keys from environment or use provided list
        if api_keys is None:
            env_keys = os.getenv('API_KEYS', '')
            self.api_keys = set([k.strip() for k in env_keys.split(',') if k.strip()])
        else:
            self.api_keys = set(api_keys)

        # Add default key for development
        if not self.api_keys and os.getenv('FLASK_ENV') == 'development':
            self.api_keys.add('dev-key-change-in-production')
            logger.warning("Using default development API key")

        self.enabled = len(self.api_keys) > 0
        logger.info(f"API Key authentication {'enabled' if self.enabled else 'disabled'}")

    def require_api_key(self, f: Callable) -> Callable:
        """
        Decorator to require API key authentication

        Args:
            f: Function to wrap

        Returns:
            Wrapped function
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.enabled:
                # Authentication disabled
                return f(*args, **kwargs)

            # Check for API key in header
            api_key = request.headers.get('X-API-Key')

            if not api_key:
                # Check for API key in query parameter
                api_key = request.args.get('api_key')

            if not api_key:
                logger.warning("API request without API key")
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'API key required. Provide key in X-API-Key header or api_key parameter',
                    'status': 401
                }), 401

            if not self.validate_api_key(api_key):
                logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Invalid API key',
                    'status': 403
                }), 403

            # API key valid, proceed with request
            return f(*args, **kwargs)

        return decorated_function

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key

        Args:
            api_key: API key to validate

        Returns:
            True if valid
        """
        return api_key in self.api_keys

    def add_api_key(self, api_key: str):
        """
        Add a new API key

        Args:
            api_key: API key to add
        """
        self.api_keys.add(api_key)
        self.enabled = True
        logger.info("API key added")

    def remove_api_key(self, api_key: str):
        """
        Remove an API key

        Args:
            api_key: API key to remove
        """
        self.api_keys.discard(api_key)
        logger.info("API key removed")

    def generate_api_key(self) -> str:
        """
        Generate a new random API key

        Returns:
            Generated API key
        """
        import secrets
        api_key = secrets.token_urlsafe(32)
        return api_key


# Global auth instance
auth = APIKeyAuth()


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication
    Allows request with or without API key

    Args:
        f: Function to wrap

    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if API key provided
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if api_key and auth.enabled:
            # Validate if provided
            if not auth.validate_api_key(api_key):
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Invalid API key',
                    'status': 403
                }), 403

        # Proceed regardless of authentication
        return f(*args, **kwargs)

    return decorated_function


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create auth with test key
    test_auth = APIKeyAuth(['test-key-123'])

    # Test validation
    print(f"Valid key: {test_auth.validate_api_key('test-key-123')}")
    print(f"Invalid key: {test_auth.validate_api_key('wrong-key')}")

    # Generate new key
    new_key = test_auth.generate_api_key()
    print(f"Generated key: {new_key}")
