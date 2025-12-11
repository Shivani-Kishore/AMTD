"""
HTML Report Generator
Generates interactive HTML security reports using Jinja2 templates
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate interactive HTML reports for security scans"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize HTML report generator

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            # Default to templates/reports directory
            base_dir = Path(__file__).parent.parent.parent
            template_dir = base_dir / "templates" / "reports"

        self.template_dir = Path(template_dir)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register custom filters
        self.env.filters['severity_color'] = self._severity_color
        self.env.filters['severity_badge'] = self._severity_badge
        self.env.filters['format_timestamp'] = self._format_timestamp
        self.env.filters['format_duration'] = self._format_duration

        logger.info(f"HTML Report Generator initialized with template dir: {template_dir}")

    def generate(
        self,
        scan_results: Dict[str, Any],
        output_path: str,
        include_charts: bool = True
    ) -> str:
        """
        Generate HTML report from scan results

        Args:
            scan_results: Scan results dictionary
            output_path: Path to save HTML report
            include_charts: Include JavaScript charts

        Returns:
            Path to generated report
        """
        try:
            logger.info(f"Generating HTML report: {output_path}")

            # Prepare report data
            report_data = self._prepare_report_data(scan_results)

            # Load template
            template = self.env.get_template('report.html')

            # Render template
            html_content = template.render(
                report=report_data,
                include_charts=include_charts,
                generated_at=datetime.utcnow().isoformat()
            )

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_content, encoding='utf-8')

            logger.info(f"HTML report generated successfully: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise

    def _prepare_report_data(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and enrich scan results for report

        Args:
            scan_results: Raw scan results

        Returns:
            Enhanced report data
        """
        # Extract main sections
        scan_info = scan_results.get('scan_info', {})
        vulnerabilities = scan_results.get('vulnerabilities', [])
        statistics = scan_results.get('statistics', {})

        # Calculate additional metrics
        total_vulns = statistics.get('total', 0)

        # Group vulnerabilities by severity
        vuln_by_severity = self._group_by_severity(vulnerabilities)

        # Group vulnerabilities by category
        vuln_by_category = self._group_by_category(vulnerabilities)

        # Get top vulnerabilities
        top_vulns = self._get_top_vulnerabilities(vulnerabilities, limit=10)

        # Calculate risk score
        risk_score = self._calculate_risk_score(statistics)

        # Prepare chart data
        chart_data = self._prepare_chart_data(
            vuln_by_severity,
            vuln_by_category,
            vulnerabilities
        )

        return {
            'scan_info': scan_info,
            'statistics': statistics,
            'vulnerabilities': vulnerabilities,
            'vuln_by_severity': vuln_by_severity,
            'vuln_by_category': vuln_by_category,
            'top_vulnerabilities': top_vulns,
            'risk_score': risk_score,
            'chart_data': chart_data,
            'total_vulnerabilities': total_vulns
        }

    def _group_by_severity(self, vulnerabilities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group vulnerabilities by severity level"""
        grouped = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'info').lower()
            if severity in grouped:
                grouped[severity].append(vuln)

        return grouped

    def _group_by_category(self, vulnerabilities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group vulnerabilities by category"""
        grouped = {}

        for vuln in vulnerabilities:
            category = vuln.get('category', 'Other')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(vuln)

        # Sort by count
        return dict(sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True))

    def _get_top_vulnerabilities(
        self,
        vulnerabilities: List[Dict],
        limit: int = 10
    ) -> List[Dict]:
        """Get top vulnerabilities by severity and risk"""
        # Define severity weights
        severity_weight = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'info': 1
        }

        # Calculate risk score for each vulnerability
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'info').lower()
            confidence = vuln.get('confidence', 'low').lower()

            # Base score from severity
            score = severity_weight.get(severity, 1)

            # Adjust by confidence
            if confidence == 'high':
                score *= 1.5
            elif confidence == 'medium':
                score *= 1.2

            vuln['risk_score'] = score

        # Sort by risk score and return top N
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda x: x.get('risk_score', 0),
            reverse=True
        )

        return sorted_vulns[:limit]

    def _calculate_risk_score(self, statistics: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate overall risk score (0-100)

        Args:
            statistics: Vulnerability statistics

        Returns:
            Risk score with rating
        """
        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)
        medium = statistics.get('medium', 0)
        low = statistics.get('low', 0)

        # Weighted score
        score = (critical * 10) + (high * 5) + (medium * 2) + (low * 1)

        # Normalize to 0-100 scale (cap at 100)
        normalized_score = min(score, 100)

        # Determine rating
        if normalized_score >= 80:
            rating = 'Critical'
            color = '#dc3545'
        elif normalized_score >= 60:
            rating = 'High'
            color = '#fd7e14'
        elif normalized_score >= 40:
            rating = 'Medium'
            color = '#ffc107'
        elif normalized_score >= 20:
            rating = 'Low'
            color = '#17a2b8'
        else:
            rating = 'Minimal'
            color = '#28a745'

        return {
            'score': normalized_score,
            'rating': rating,
            'color': color
        }

    def _prepare_chart_data(
        self,
        vuln_by_severity: Dict[str, List],
        vuln_by_category: Dict[str, List],
        vulnerabilities: List[Dict]
    ) -> Dict[str, Any]:
        """Prepare data for JavaScript charts"""

        # Severity chart data
        severity_data = {
            'labels': ['Critical', 'High', 'Medium', 'Low', 'Info'],
            'values': [
                len(vuln_by_severity.get('critical', [])),
                len(vuln_by_severity.get('high', [])),
                len(vuln_by_severity.get('medium', [])),
                len(vuln_by_severity.get('low', [])),
                len(vuln_by_severity.get('info', []))
            ],
            'colors': ['#dc3545', '#fd7e14', '#ffc107', '#17a2b8', '#6c757d']
        }

        # Category chart data (top 10)
        category_items = list(vuln_by_category.items())[:10]
        category_data = {
            'labels': [cat for cat, _ in category_items],
            'values': [len(vulns) for _, vulns in category_items]
        }

        return {
            'severity': severity_data,
            'category': category_data
        }

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Get Bootstrap color class for severity"""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary',
            'info': 'light'
        }
        return colors.get(severity.lower(), 'secondary')

    @staticmethod
    def _severity_badge(severity: str) -> str:
        """Get Bootstrap badge HTML for severity"""
        color = HTMLReportGenerator._severity_color(severity)
        return f'<span class="badge badge-{color}">{severity.upper()}</span>'

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format ISO timestamp to readable format"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            return timestamp

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    sample_results = {
        'scan_info': {
            'application': 'test-app',
            'scan_type': 'full',
            'target_url': 'http://example.com',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration': 3600
        },
        'statistics': {
            'critical': 2,
            'high': 5,
            'medium': 10,
            'low': 15,
            'info': 20,
            'total': 52
        },
        'vulnerabilities': []
    }

    generator = HTMLReportGenerator()
    report_path = generator.generate(sample_results, 'test_report.html')
    print(f"Report generated: {report_path}")
