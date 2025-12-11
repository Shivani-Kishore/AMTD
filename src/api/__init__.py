"""
AMTD REST API Module
Flask-based REST API for managing security scans
"""

from .app import create_app

__all__ = ['create_app']
__version__ = '1.0.0'
