"""
Scans API Routes
Endpoints for managing security scans
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from ..database import db
from ..auth import auth

logger = logging.getLogger(__name__)

scans_bp = Blueprint('scans', __name__)


@scans_bp.route('', methods=['GET'])
@auth.require_api_key
def list_scans():
    """
    List scans with optional filters

    Query Parameters:
        - application_id: Filter by application ID
        - status: Filter by status (pending, running, completed, failed)
        - scan_type: Filter by scan type (full, quick, incremental)
        - limit: Maximum number of results (default: 50)
        - offset: Offset for pagination (default: 0)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        application_id = request.args.get('application_id')
        status = request.args.get('status')
        scan_type = request.args.get('scan_type')

        query = """
            SELECT s.*, a.name as application_name
            FROM scans s
            LEFT JOIN applications a ON s.application_id = a.id
            WHERE 1=1
        """
        params = []

        if application_id:
            query += " AND s.application_id = %s"
            params.append(application_id)

        if status:
            query += " AND s.status = %s"
            params.append(status)

        if scan_type:
            query += " AND s.scan_type = %s"
            params.append(scan_type)

        query += " ORDER BY s.started_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        scans = db.execute_query(query, tuple(params))

        # Get total count
        count_query = "SELECT COUNT(*) as total FROM scans WHERE 1=1"
        count_params = []

        if application_id:
            count_query += " AND application_id = %s"
            count_params.append(application_id)
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        if scan_type:
            count_query += " AND scan_type = %s"
            count_params.append(scan_type)

        total = db.execute_one(count_query, tuple(count_params) if count_params else None)

        return jsonify({
            'scans': scans or [],
            'total': total['total'] if total else 0,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        logger.error(f"Failed to list scans: {e}")
        return jsonify({'error': str(e)}), 500


@scans_bp.route('/<scan_id>', methods=['GET'])
@auth.require_api_key
def get_scan(scan_id):
    """Get scan by ID with vulnerability details"""
    try:
        scan = db.execute_one(
            """
            SELECT s.*, a.name as application_name
            FROM scans s
            LEFT JOIN applications a ON s.application_id = a.id
            WHERE s.id = %s
            """,
            (scan_id,)
        )

        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        # Get vulnerability summary
        vulnerabilities = db.execute_query(
            """
            SELECT severity, COUNT(*) as count
            FROM vulnerabilities
            WHERE scan_id = %s
            GROUP BY severity
            """,
            (scan_id,)
        )

        scan['vulnerability_summary'] = {
            v['severity']: v['count'] for v in vulnerabilities
        } if vulnerabilities else {}

        return jsonify(scan)

    except Exception as e:
        logger.error(f"Failed to get scan: {e}")
        return jsonify({'error': str(e)}), 500


@scans_bp.route('', methods=['POST'])
@auth.require_api_key
def create_scan():
    """
    Create new scan

    Request Body:
        - application_id: Application UUID (required)
        - scan_type: Scan type (full, quick, incremental)
        - target_url: Target URL override (optional)
    """
    try:
        data = request.get_json()

        if 'application_id' not in data:
            return jsonify({'error': 'Missing required field: application_id'}), 400

        # Verify application exists
        application = db.execute_one(
            "SELECT * FROM applications WHERE id = %s",
            (data['application_id'],)
        )

        if not application:
            return jsonify({'error': 'Application not found'}), 404

        scan = db.insert('scans', {
            'application_id': data['application_id'],
            'scan_type': data.get('scan_type', 'full'),
            'target_url': data.get('target_url', application['target_url']),
            'status': 'pending',
            'started_at': datetime.utcnow()
        })

        return jsonify(scan), 201

    except Exception as e:
        logger.error(f"Failed to create scan: {e}")
        return jsonify({'error': str(e)}), 500


@scans_bp.route('/<scan_id>', methods=['PUT'])
@auth.require_api_key
def update_scan(scan_id):
    """Update scan status and results"""
    try:
        data = request.get_json()

        # Remove fields that shouldn't be updated
        data.pop('id', None)
        data.pop('application_id', None)
        data.pop('started_at', None)

        if not data:
            return jsonify({'error': 'No fields to update'}), 400

        # Set completed_at if status is completed or failed
        if data.get('status') in ['completed', 'failed'] and 'completed_at' not in data:
            data['completed_at'] = datetime.utcnow()

        scan = db.update(
            'scans',
            data,
            'id = %s',
            (scan_id,)
        )

        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        return jsonify(scan)

    except Exception as e:
        logger.error(f"Failed to update scan: {e}")
        return jsonify({'error': str(e)}), 500


@scans_bp.route('/<scan_id>', methods=['DELETE'])
@auth.require_api_key
def delete_scan(scan_id):
    """Delete scan and associated data"""
    try:
        deleted_count = db.delete('scans', 'id = %s', (scan_id,))

        if deleted_count > 0:
            return jsonify({'message': 'Scan deleted successfully'})
        else:
            return jsonify({'error': 'Scan not found'}), 404

    except Exception as e:
        logger.error(f"Failed to delete scan: {e}")
        return jsonify({'error': str(e)}), 500


@scans_bp.route('/recent', methods=['GET'])
@auth.require_api_key
def get_recent_scans():
    """Get recent scans across all applications"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)

        scans = db.execute_query(
            """
            SELECT *
            FROM vw_recent_scans
            LIMIT %s
            """,
            (limit,)
        )

        return jsonify({
            'scans': scans or [],
            'count': len(scans) if scans else 0
        })

    except Exception as e:
        logger.error(f"Failed to get recent scans: {e}")
        return jsonify({'error': str(e)}), 500


@scans_bp.route('/statistics', methods=['GET'])
@auth.require_api_key
def get_scan_statistics():
    """Get overall scan statistics"""
    try:
        # Get various statistics
        stats = {}

        # Total scans
        total = db.execute_one("SELECT COUNT(*) as total FROM scans")
        stats['total_scans'] = total['total'] if total else 0

        # Scans by status
        by_status = db.execute_query(
            "SELECT status, COUNT(*) as count FROM scans GROUP BY status"
        )
        stats['by_status'] = {
            s['status']: s['count'] for s in by_status
        } if by_status else {}

        # Scans by type
        by_type = db.execute_query(
            "SELECT scan_type, COUNT(*) as count FROM scans GROUP BY scan_type"
        )
        stats['by_type'] = {
            s['scan_type']: s['count'] for s in by_type
        } if by_type else {}

        # Recent scans (last 7 days)
        recent = db.execute_one(
            """
            SELECT COUNT(*) as count
            FROM scans
            WHERE started_at >= NOW() - INTERVAL '7 days'
            """
        )
        stats['last_7_days'] = recent['count'] if recent else 0

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Failed to get scan statistics: {e}")
        return jsonify({'error': str(e)}), 500
