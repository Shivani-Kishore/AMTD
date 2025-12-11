"""
Applications API Routes
Endpoints for managing applications
"""

import logging
from flask import Blueprint, request, jsonify
from ..database import db
from ..auth import auth

logger = logging.getLogger(__name__)

applications_bp = Blueprint('applications', __name__)


@applications_bp.route('', methods=['GET'])
@auth.require_api_key
def list_applications():
    """
    List all applications

    Query Parameters:
        - limit: Maximum number of results (default: 50)
        - offset: Offset for pagination (default: 0)
        - status: Filter by status (active, inactive)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')

        query = "SELECT * FROM applications WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        applications = db.execute_query(query, tuple(params))

        # Get total count
        count_query = "SELECT COUNT(*) as total FROM applications WHERE 1=1"
        count_params = []
        if status:
            count_query += " AND status = %s"
            count_params.append(status)

        total = db.execute_one(count_query, tuple(count_params) if count_params else None)

        return jsonify({
            'applications': applications or [],
            'total': total['total'] if total else 0,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        logger.error(f"Failed to list applications: {e}")
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<application_id>', methods=['GET'])
@auth.require_api_key
def get_application(application_id):
    """Get application by ID"""
    try:
        application = db.execute_one(
            "SELECT * FROM applications WHERE id = %s",
            (application_id,)
        )

        if not application:
            return jsonify({'error': 'Application not found'}), 404

        # Get recent scans for this application
        scans = db.execute_query(
            """
            SELECT id, scan_type, status, started_at, completed_at,
                   critical_count, high_count, medium_count, low_count, info_count
            FROM scans
            WHERE application_id = %s
            ORDER BY started_at DESC
            LIMIT 10
            """,
            (application_id,)
        )

        application['recent_scans'] = scans or []

        return jsonify(application)

    except Exception as e:
        logger.error(f"Failed to get application: {e}")
        return jsonify({'error': str(e)}), 500


@applications_bp.route('', methods=['POST'])
@auth.require_api_key
def create_application():
    """Create new application"""
    try:
        data = request.get_json()

        required_fields = ['name', 'target_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        application = db.insert('applications', {
            'name': data['name'],
            'target_url': data['target_url'],
            'description': data.get('description'),
            'status': data.get('status', 'active'),
            'environment': data.get('environment', 'development'),
            'owner': data.get('owner'),
            'repository': data.get('repository')
        })

        return jsonify(application), 201

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<application_id>', methods=['PUT'])
@auth.require_api_key
def update_application(application_id):
    """Update application"""
    try:
        data = request.get_json()

        # Remove fields that shouldn't be updated
        data.pop('id', None)
        data.pop('created_at', None)

        if not data:
            return jsonify({'error': 'No fields to update'}), 400

        application = db.update(
            'applications',
            data,
            'id = %s',
            (application_id,)
        )

        if not application:
            return jsonify({'error': 'Application not found'}), 404

        return jsonify(application)

    except Exception as e:
        logger.error(f"Failed to update application: {e}")
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<application_id>', methods=['DELETE'])
@auth.require_api_key
def delete_application(application_id):
    """Delete application"""
    try:
        # Check if application exists
        application = db.execute_one(
            "SELECT * FROM applications WHERE id = %s",
            (application_id,)
        )

        if not application:
            return jsonify({'error': 'Application not found'}), 404

        # Delete application (cascades to scans due to FK constraint)
        deleted_count = db.delete('applications', 'id = %s', (application_id,))

        if deleted_count > 0:
            return jsonify({'message': 'Application deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete application'}), 500

    except Exception as e:
        logger.error(f"Failed to delete application: {e}")
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<application_id>/statistics', methods=['GET'])
@auth.require_api_key
def get_application_statistics(application_id):
    """Get vulnerability statistics for application"""
    try:
        # Check if application exists
        application = db.execute_one(
            "SELECT name FROM applications WHERE id = %s",
            (application_id,)
        )

        if not application:
            return jsonify({'error': 'Application not found'}), 404

        # Get statistics from view
        stats = db.execute_one(
            """
            SELECT *
            FROM vw_application_portfolio
            WHERE application_id = %s
            """,
            (application_id,)
        )

        if not stats:
            return jsonify({
                'application_id': application_id,
                'application_name': application['name'],
                'total_scans': 0,
                'last_scan_date': None,
                'avg_critical': 0,
                'avg_high': 0,
                'avg_medium': 0,
                'avg_low': 0
            })

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Failed to get application statistics: {e}")
        return jsonify({'error': str(e)}), 500
