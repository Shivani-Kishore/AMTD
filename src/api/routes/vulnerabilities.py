"""
Vulnerabilities API Routes
Endpoints for managing vulnerabilities
"""

import logging
from flask import Blueprint, request, jsonify
from ..database import db
from ..auth import auth

logger = logging.getLogger(__name__)

vulnerabilities_bp = Blueprint('vulnerabilities', __name__)


@vulnerabilities_bp.route('', methods=['GET'])
@auth.require_api_key
def list_vulnerabilities():
    """
    List vulnerabilities with optional filters

    Query Parameters:
        - scan_id: Filter by scan ID
        - application_id: Filter by application ID
        - severity: Filter by severity (critical, high, medium, low, info)
        - status: Filter by status (open, fixed, false_positive, accepted)
        - limit: Maximum number of results (default: 50)
        - offset: Offset for pagination (default: 0)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        scan_id = request.args.get('scan_id')
        application_id = request.args.get('application_id')
        severity = request.args.get('severity')
        status = request.args.get('status')

        query = """
            SELECT v.*, s.scan_type, a.name as application_name
            FROM vulnerabilities v
            LEFT JOIN scans s ON v.scan_id = s.id
            LEFT JOIN applications a ON s.application_id = a.id
            WHERE 1=1
        """
        params = []

        if scan_id:
            query += " AND v.scan_id = %s"
            params.append(scan_id)

        if application_id:
            query += " AND s.application_id = %s"
            params.append(application_id)

        if severity:
            query += " AND v.severity = %s"
            params.append(severity)

        if status:
            query += " AND v.status = %s"
            params.append(status)

        query += " ORDER BY v.discovered_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        vulnerabilities = db.execute_query(query, tuple(params))

        # Get total count
        count_query = "SELECT COUNT(*) as total FROM vulnerabilities v LEFT JOIN scans s ON v.scan_id = s.id WHERE 1=1"
        count_params = []

        if scan_id:
            count_query += " AND v.scan_id = %s"
            count_params.append(scan_id)
        if application_id:
            count_query += " AND s.application_id = %s"
            count_params.append(application_id)
        if severity:
            count_query += " AND v.severity = %s"
            count_params.append(severity)
        if status:
            count_query += " AND v.status = %s"
            count_params.append(status)

        total = db.execute_one(count_query, tuple(count_params) if count_params else None)

        return jsonify({
            'vulnerabilities': vulnerabilities or [],
            'total': total['total'] if total else 0,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        logger.error(f"Failed to list vulnerabilities: {e}")
        return jsonify({'error': str(e)}), 500


@vulnerabilities_bp.route('/<vulnerability_id>', methods=['GET'])
@auth.require_api_key
def get_vulnerability(vulnerability_id):
    """Get vulnerability by ID"""
    try:
        vulnerability = db.execute_one(
            """
            SELECT v.*, s.scan_type, a.name as application_name, a.id as application_id
            FROM vulnerabilities v
            LEFT JOIN scans s ON v.scan_id = s.id
            LEFT JOIN applications a ON s.application_id = a.id
            WHERE v.id = %s
            """,
            (vulnerability_id,)
        )

        if not vulnerability:
            return jsonify({'error': 'Vulnerability not found'}), 404

        return jsonify(vulnerability)

    except Exception as e:
        logger.error(f"Failed to get vulnerability: {e}")
        return jsonify({'error': str(e)}), 500


@vulnerabilities_bp.route('', methods=['POST'])
@auth.require_api_key
def create_vulnerability():
    """Create new vulnerability"""
    try:
        data = request.get_json()

        required_fields = ['scan_id', 'name', 'severity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Verify scan exists
        scan = db.execute_one(
            "SELECT * FROM scans WHERE id = %s",
            (data['scan_id'],)
        )

        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        vulnerability = db.insert('vulnerabilities', {
            'scan_id': data['scan_id'],
            'name': data['name'],
            'severity': data['severity'],
            'confidence': data.get('confidence'),
            'description': data.get('description'),
            'url': data.get('url'),
            'method': data.get('method'),
            'parameter': data.get('parameter'),
            'evidence': data.get('evidence'),
            'solution': data.get('solution'),
            'reference': data.get('reference'),
            'cwe_id': data.get('cwe_id'),
            'category': data.get('category'),
            'status': data.get('status', 'open')
        })

        return jsonify(vulnerability), 201

    except Exception as e:
        logger.error(f"Failed to create vulnerability: {e}")
        return jsonify({'error': str(e)}), 500


@vulnerabilities_bp.route('/<vulnerability_id>', methods=['PUT'])
@auth.require_api_key
def update_vulnerability(vulnerability_id):
    """Update vulnerability (typically status)"""
    try:
        data = request.get_json()

        # Remove fields that shouldn't be updated
        data.pop('id', None)
        data.pop('scan_id', None)
        data.pop('discovered_at', None)

        if not data:
            return jsonify({'error': 'No fields to update'}), 400

        vulnerability = db.update(
            'vulnerabilities',
            data,
            'id = %s',
            (vulnerability_id,)
        )

        if not vulnerability:
            return jsonify({'error': 'Vulnerability not found'}), 404

        return jsonify(vulnerability)

    except Exception as e:
        logger.error(f"Failed to update vulnerability: {e}")
        return jsonify({'error': str(e)}), 500


@vulnerabilities_bp.route('/<vulnerability_id>', methods=['DELETE'])
@auth.require_api_key
def delete_vulnerability(vulnerability_id):
    """Delete vulnerability"""
    try:
        deleted_count = db.delete('vulnerabilities', 'id = %s', (vulnerability_id,))

        if deleted_count > 0:
            return jsonify({'message': 'Vulnerability deleted successfully'})
        else:
            return jsonify({'error': 'Vulnerability not found'}), 404

    except Exception as e:
        logger.error(f"Failed to delete vulnerability: {e}")
        return jsonify({'error': str(e)}), 500


@vulnerabilities_bp.route('/summary', methods=['GET'])
@auth.require_api_key
def get_vulnerability_summary():
    """Get vulnerability summary statistics"""
    try:
        application_id = request.args.get('application_id')

        if application_id:
            # Summary for specific application
            summary = db.execute_one(
                """
                SELECT *
                FROM vw_vulnerability_summary
                WHERE application_id = %s
                """,
                (application_id,)
            )
        else:
            # Overall summary
            summary = db.execute_one(
                """
                SELECT
                    COUNT(*) as total_vulnerabilities,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low,
                    SUM(CASE WHEN severity = 'info' THEN 1 ELSE 0 END) as info,
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                    SUM(CASE WHEN status = 'fixed' THEN 1 ELSE 0 END) as fixed_count
                FROM vulnerabilities
                """
            )

        if not summary:
            return jsonify({
                'total_vulnerabilities': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0,
                'open_count': 0,
                'fixed_count': 0
            })

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Failed to get vulnerability summary: {e}")
        return jsonify({'error': str(e)}), 500
