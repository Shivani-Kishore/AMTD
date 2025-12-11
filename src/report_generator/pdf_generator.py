"""
PDF Report Generator
Generates professional PDF reports from HTML using WeasyPrint
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate professional PDF reports for security scans"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize PDF report generator

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
        self.env.filters['format_timestamp'] = self._format_timestamp
        self.env.filters['format_duration'] = self._format_duration

        logger.info(f"PDF Report Generator initialized with template dir: {template_dir}")

    def generate(
        self,
        scan_results: Dict[str, Any],
        output_path: str,
        include_executive_summary: bool = True,
        include_detailed_findings: bool = True
    ) -> str:
        """
        Generate PDF report from scan results

        Args:
            scan_results: Scan results dictionary
            output_path: Path to save PDF report
            include_executive_summary: Include executive summary section
            include_detailed_findings: Include detailed vulnerability findings

        Returns:
            Path to generated report
        """
        try:
            logger.info(f"Generating PDF report: {output_path}")

            # Prepare report data
            report_data = self._prepare_report_data(
                scan_results,
                include_executive_summary,
                include_detailed_findings
            )

            # Load template
            template = self.env.get_template('report_pdf.html')

            # Render HTML
            html_content = template.render(
                report=report_data,
                generated_at=datetime.utcnow().isoformat()
            )

            # Load custom CSS for PDF
            css_path = self.template_dir / 'assets' / 'css' / 'pdf.css'
            css = None
            if css_path.exists():
                css = CSS(filename=str(css_path))

            # Generate PDF
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            html_doc = HTML(string=html_content, base_url=str(self.template_dir))
            html_doc.write_pdf(
                str(output_file),
                stylesheets=[css] if css else None
            )

            logger.info(f"PDF report generated successfully: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise

    def generate_executive_summary(
        self,
        scan_results: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate executive summary PDF (high-level overview only)

        Args:
            scan_results: Scan results dictionary
            output_path: Path to save PDF report

        Returns:
            Path to generated report
        """
        try:
            logger.info(f"Generating executive summary PDF: {output_path}")

            # Prepare executive summary data
            report_data = self._prepare_executive_summary(scan_results)

            # Load template
            template = self.env.get_template('executive_summary_pdf.html')

            # Render HTML
            html_content = template.render(
                report=report_data,
                generated_at=datetime.utcnow().isoformat()
            )

            # Load CSS
            css_path = self.template_dir / 'assets' / 'css' / 'pdf.css'
            css = None
            if css_path.exists():
                css = CSS(filename=str(css_path))

            # Generate PDF
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            html_doc = HTML(string=html_content, base_url=str(self.template_dir))
            html_doc.write_pdf(
                str(output_file),
                stylesheets=[css] if css else None
            )

            logger.info(f"Executive summary PDF generated: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            raise

    def _prepare_report_data(
        self,
        scan_results: Dict[str, Any],
        include_executive_summary: bool,
        include_detailed_findings: bool
    ) -> Dict[str, Any]:
        """
        Prepare comprehensive report data for PDF

        Args:
            scan_results: Raw scan results
            include_executive_summary: Include executive summary
            include_detailed_findings: Include detailed findings

        Returns:
            Enhanced report data
        """
        scan_info = scan_results.get('scan_info', {})
        vulnerabilities = scan_results.get('vulnerabilities', [])
        statistics = scan_results.get('statistics', {})

        report = {
            'scan_info': scan_info,
            'statistics': statistics,
            'include_executive_summary': include_executive_summary,
            'include_detailed_findings': include_detailed_findings
        }

        # Add executive summary if requested
        if include_executive_summary:
            report['executive_summary'] = self._build_executive_summary(
                scan_info,
                statistics,
                vulnerabilities
            )

        # Add vulnerability sections
        if include_detailed_findings:
            report['vulnerabilities'] = self._organize_vulnerabilities(vulnerabilities)
        else:
            # Include only summary statistics
            report['top_vulnerabilities'] = self._get_top_vulnerabilities(
                vulnerabilities,
                limit=5
            )

        # Add risk assessment
        report['risk_assessment'] = self._calculate_risk_assessment(statistics)

        # Add recommendations
        report['recommendations'] = self._generate_recommendations(
            statistics,
            vulnerabilities
        )

        return report

    def _prepare_executive_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare executive summary data only

        Args:
            scan_results: Raw scan results

        Returns:
            Executive summary data
        """
        scan_info = scan_results.get('scan_info', {})
        statistics = scan_results.get('statistics', {})
        vulnerabilities = scan_results.get('vulnerabilities', [])

        return {
            'scan_info': scan_info,
            'statistics': statistics,
            'executive_summary': self._build_executive_summary(
                scan_info,
                statistics,
                vulnerabilities
            ),
            'risk_assessment': self._calculate_risk_assessment(statistics),
            'top_vulnerabilities': self._get_top_vulnerabilities(vulnerabilities, 5),
            'recommendations': self._generate_recommendations(statistics, vulnerabilities)
        }

    def _build_executive_summary(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        vulnerabilities: List[Dict]
    ) -> Dict[str, Any]:
        """Build executive summary section"""

        total = statistics.get('total', 0)
        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)

        # Generate summary text
        if total == 0:
            summary_text = "No security vulnerabilities were identified during this assessment."
            severity = "success"
        elif critical > 0:
            summary_text = f"This security assessment identified {total} vulnerabilities, " \
                         f"including {critical} critical issues requiring immediate attention."
            severity = "critical"
        elif high > 0:
            summary_text = f"This security assessment identified {total} vulnerabilities, " \
                         f"including {high} high severity issues that should be addressed promptly."
            severity = "high"
        else:
            summary_text = f"This security assessment identified {total} vulnerabilities " \
                         f"of medium or lower severity."
            severity = "medium"

        # Key findings
        key_findings = []
        if critical > 0:
            key_findings.append(f"{critical} critical vulnerabilities requiring immediate remediation")
        if high > 5:
            key_findings.append(f"{high} high severity issues identified")

        # Get unique vulnerability categories
        categories = set(v.get('category', 'Other') for v in vulnerabilities)
        if len(categories) > 3:
            key_findings.append(f"Vulnerabilities span {len(categories)} different categories")

        return {
            'summary_text': summary_text,
            'severity': severity,
            'key_findings': key_findings,
            'scan_duration': self._format_duration(scan_info.get('duration', 0)),
            'total_checks': len(vulnerabilities)
        }

    def _organize_vulnerabilities(self, vulnerabilities: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize vulnerabilities by severity for detailed sections"""
        organized = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'info').lower()
            if severity in organized:
                organized[severity].append(vuln)

        return organized

    def _get_top_vulnerabilities(
        self,
        vulnerabilities: List[Dict],
        limit: int = 5
    ) -> List[Dict]:
        """Get top vulnerabilities by risk score"""
        severity_weight = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'info': 1
        }

        # Calculate risk score
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'info').lower()
            confidence = vuln.get('confidence', 'low').lower()

            score = severity_weight.get(severity, 1)
            if confidence == 'high':
                score *= 1.5
            elif confidence == 'medium':
                score *= 1.2

            vuln['risk_score'] = score

        # Sort and return top N
        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda x: x.get('risk_score', 0),
            reverse=True
        )

        return sorted_vulns[:limit]

    def _calculate_risk_assessment(self, statistics: Dict[str, int]) -> Dict[str, Any]:
        """Calculate overall risk assessment"""
        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)
        medium = statistics.get('medium', 0)
        low = statistics.get('low', 0)

        # Weighted risk score
        score = (critical * 10) + (high * 5) + (medium * 2) + (low * 1)
        normalized_score = min(score, 100)

        # Determine rating and color
        if normalized_score >= 80:
            rating = 'Critical'
            color = '#dc3545'
            description = 'Immediate action required'
        elif normalized_score >= 60:
            rating = 'High'
            color = '#fd7e14'
            description = 'Prompt remediation recommended'
        elif normalized_score >= 40:
            rating = 'Medium'
            color = '#ffc107'
            description = 'Schedule remediation'
        elif normalized_score >= 20:
            rating = 'Low'
            color = '#17a2b8'
            description = 'Monitor and address as resources permit'
        else:
            rating = 'Minimal'
            color = '#28a745'
            description = 'Acceptable risk level'

        return {
            'score': normalized_score,
            'rating': rating,
            'color': color,
            'description': description
        }

    def _generate_recommendations(
        self,
        statistics: Dict[str, int],
        vulnerabilities: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []

        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)
        medium = statistics.get('medium', 0)

        # Critical vulnerabilities
        if critical > 0:
            recommendations.append({
                'priority': 'Immediate',
                'title': 'Address Critical Vulnerabilities',
                'description': f'Remediate {critical} critical vulnerabilities immediately. '
                             f'These pose severe security risks.',
                'timeline': 'Within 24-48 hours'
            })

        # High severity issues
        if high > 0:
            recommendations.append({
                'priority': 'High',
                'title': 'Remediate High Severity Issues',
                'description': f'Address {high} high severity vulnerabilities. '
                             f'These represent significant security concerns.',
                'timeline': 'Within 1-2 weeks'
            })

        # Medium severity issues
        if medium > 10:
            recommendations.append({
                'priority': 'Medium',
                'title': 'Plan Medium Severity Remediation',
                'description': f'Develop a plan to address {medium} medium severity issues. '
                             f'Prioritize based on business impact.',
                'timeline': 'Within 1-3 months'
            })

        # Security best practices
        recommendations.append({
            'priority': 'Ongoing',
            'title': 'Implement Security Best Practices',
            'description': 'Establish regular security scanning, code reviews, and security training.',
            'timeline': 'Continuous'
        })

        # Regular scanning
        recommendations.append({
            'priority': 'Ongoing',
            'title': 'Schedule Regular Scans',
            'description': 'Conduct automated security scans with each deployment and weekly full scans.',
            'timeline': 'Continuous'
        })

        return recommendations

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Get color code for severity"""
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#17a2b8',
            'info': '#6c757d'
        }
        return colors.get(severity.lower(), '#6c757d')

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format ISO timestamp"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            return timestamp

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"


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

    generator = PDFReportGenerator()
    report_path = generator.generate(sample_results, 'test_report.pdf')
    print(f"Report generated: {report_path}")

    summary_path = generator.generate_executive_summary(sample_results, 'test_summary.pdf')
    print(f"Executive summary generated: {summary_path}")
