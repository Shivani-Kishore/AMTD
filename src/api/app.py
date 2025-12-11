"""
Flask Application Factory
Creates and configures the Flask application
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def create_app(config=None):
    """
    Create and configure Flask application

    Args:
        config: Configuration dictionary (optional)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        DATABASE_URL=os.getenv('DATABASE_URL', 'postgresql://amtd:amtd@localhost:5432/amtd'),
        MINIO_ENDPOINT=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
        MINIO_ACCESS_KEY=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        MINIO_SECRET_KEY=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max request size
        JSON_SORT_KEYS=False,
        CORS_ORIGINS=os.getenv('CORS_ORIGINS', '*').split(',')
    )

    # Override with custom config
    if config:
        app.config.update(config)

    # Setup CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Setup logging
    setup_logging(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'service': 'AMTD API'
        })

    # Root endpoint
    @app.route('/')
    def index():
        """API root endpoint"""
        return jsonify({
            'name': 'AMTD REST API',
            'version': '1.0.0',
            'documentation': '/api/v1/docs',
            'endpoints': {
                'applications': '/api/v1/applications',
                'scans': '/api/v1/scans',
                'vulnerabilities': '/api/v1/vulnerabilities',
                'reports': '/api/v1/reports',
                'health': '/health'
            }
        })

    logger.info("Flask application created successfully")
    return app


def setup_logging(app):
    """Setup application logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Flask logger
    app.logger.setLevel(getattr(logging, log_level))


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        response = {
            'error': e.name,
            'message': e.description,
            'status': e.code
        }
        return jsonify(response), e.code

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        response = {
            'error': 'Internal Server Error',
            'message': str(e),
            'status': 500
        }
        return jsonify(response), 500

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status': 404
        }), 404

    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 errors"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(e),
            'status': 400
        }), 400


def register_blueprints(app):
    """Register API blueprints"""
    from .routes.applications import applications_bp
    from .routes.scans import scans_bp
    from .routes.vulnerabilities import vulnerabilities_bp
    from .routes.reports import reports_bp

    # Register blueprints with /api/v1 prefix
    app.register_blueprint(applications_bp, url_prefix='/api/v1/applications')
    app.register_blueprint(scans_bp, url_prefix='/api/v1/scans')
    app.register_blueprint(vulnerabilities_bp, url_prefix='/api/v1/vulnerabilities')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')

    logger.info("Blueprints registered successfully")


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=os.getenv('API_HOST', '0.0.0.0'),
        port=int(os.getenv('API_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
