"""
Reports API Routes
Endpoints for managing scan reports
"""

import logging
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
from ..database import db
from ..auth import auth

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('', methods=['GET'])
@auth.require_api_key
def list_reports():
    """
    List reports

    Query Parameters:
        - scan_id: Filter by scan ID
        - application_id: Filter by application ID
        - format: Filter by format (html, json, pdf, sarif)
        - limit: Maximum number of results (default: 50)
        - offset: Offset for pagination (default: 0)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        scan_id = request.args.get('scan_id')
        application_id = request.args.get('application_id')
        format_type = request.args.get('format')

        query = """
            SELECT r.*, s.scan_type, a.name as application_name
            FROM reports r
            LEFT JOIN scans s ON r.scan_id = s.id
            LEFT JOIN applications a ON s.application_id = a.id
            WHERE 1=1
        """
        params = []

        if scan_id:
            query += " AND r.scan_id = %s"
            params.append(scan_id)

        if application_id:
            query += " AND s.application_id = %s"
            params.append(application_id)

        if format_type:
            query += " AND r.format = %s"
            params.append(format_type)

        query += " ORDER BY r.generated_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        reports = db.execute_query(query, tuple(params))

        # Get total count
        count_query = "SELECT COUNT(*) as total FROM reports r LEFT JOIN scans s ON r.scan_id = s.id WHERE 1=1"
        count_params = []

        if scan_id:
            count_query += " AND r.scan_id = %s"
            count_params.append(scan_id)
        if application_id:
            count_query += " AND s.application_id = %s"
            count_params.append(application_id)
        if format_type:
            count_query += " AND r.format = %s"
            count_params.append(format_type)

        total = db.execute_one(count_query, tuple(count_params) if count_params else None)

        return jsonify({
            'reports': reports or [],
            'total': total['total'] if total else 0,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<report_id>', methods=['GET'])
@auth.require_api_key
def get_report(report_id):
    """Get report metadata by ID"""
    try:
        report = db.execute_one(
            """
            SELECT r.*, s.scan_type, a.name as application_name, a.id as application_id
            FROM reports r
            LEFT JOIN scans s ON r.scan_id = s.id
            LEFT JOIN applications a ON s.application_id = a.id
            WHERE r.id = %s
            """,
            (report_id,)
        )

        if not report:
            return jsonify({'error': 'Report not found'}), 404

        return jsonify(report)

    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<report_id>/download', methods=['GET'])
@auth.require_api_key
def download_report(report_id):
    """Download report file"""
    try:
        report = db.execute_one(
            "SELECT * FROM reports WHERE id = %s",
            (report_id,)
        )

        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Check if file exists
        file_path = Path(report['file_path'])
        if not file_path.exists():
            return jsonify({'error': 'Report file not found on disk'}), 404

        # Determine MIME type
        mime_types = {
            'html': 'text/html',
            'json': 'application/json',
            'pdf': 'application/pdf',
            'sarif': 'application/json'
        }

        mime_type = mime_types.get(report['format'], 'application/octet-stream')

        return send_file(
            str(file_path),
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"report_{report_id}.{report['format']}"
        )

    except Exception as e:
        logger.error(f"Failed to download report: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('', methods=['POST'])
@auth.require_api_key
def create_report():
    """Create new report record"""
    try:
        data = request.get_json()

        required_fields = ['scan_id', 'format', 'file_path']
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

        report = db.insert('reports', {
            'scan_id': data['scan_id'],
            'format': data['format'],
            'file_path': data['file_path'],
            'file_size': data.get('file_size'),
            's3_bucket': data.get('s3_bucket'),
            's3_key': data.get('s3_key')
        })

        return jsonify(report), 201

    except Exception as e:
        logger.error(f"Failed to create report: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<report_id>', methods=['DELETE'])
@auth.require_api_key
def delete_report(report_id):
    """Delete report (metadata only, file remains)"""
    try:
        deleted_count = db.delete('reports', 'id = %s', (report_id,))

        if deleted_count > 0:
            return jsonify({'message': 'Report deleted successfully'})
        else:
            return jsonify({'error': 'Report not found'}), 404

    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/latest', methods=['GET'])
@auth.require_api_key
def get_latest_reports():
    """Get latest reports for each application"""
    try:
        application_id = request.args.get('application_id')
        format_type = request.args.get('format', 'html')

        if application_id:
            # Latest report for specific application
            report = db.execute_one(
                """
                SELECT r.*, s.scan_type, a.name as application_name
                FROM reports r
                LEFT JOIN scans s ON r.scan_id = s.id
                LEFT JOIN applications a ON s.application_id = a.id
                WHERE s.application_id = %s AND r.format = %s
                ORDER BY r.generated_at DESC
                LIMIT 1
                """,
                (application_id, format_type)
            )

            if not report:
                return jsonify({'error': 'No reports found for this application'}), 404

            return jsonify(report)

        else:
            # Latest report for each application
            reports = db.execute_query(
                """
                WITH ranked_reports AS (
                    SELECT r.*, s.scan_type, a.name as application_name, a.id as application_id,
                           ROW_NUMBER() OVER (PARTITION BY s.application_id ORDER BY r.generated_at DESC) as rn
                    FROM reports r
                    LEFT JOIN scans s ON r.scan_id = s.id
                    LEFT JOIN applications a ON s.application_id = a.id
                    WHERE r.format = %s
                )
                SELECT * FROM ranked_reports WHERE rn = 1
                ORDER BY generated_at DESC
                """,
                (format_type,)
            )

            return jsonify({
                'reports': reports or [],
                'count': len(reports) if reports else 0
            })

    except Exception as e:
        logger.error(f"Failed to get latest reports: {e}")
        return jsonify({'error': str(e)}), 500
