"""
Report Manager
Coordinates report generation across multiple formats
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .html_generator import HTMLReportGenerator
from .json_generator import JSONReportGenerator
from .pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class ReportManager:
    """Manages report generation across multiple formats"""

    def __init__(self, output_dir: str, template_dir: Optional[str] = None):
        """
        Initialize Report Manager

        Args:
            output_dir: Base directory for report output
            template_dir: Directory containing report templates
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize generators
        self.html_generator = HTMLReportGenerator(template_dir)
        self.json_generator = JSONReportGenerator(pretty_print=True)
        self.pdf_generator = PDFReportGenerator(template_dir)

        logger.info(f"Report Manager initialized with output dir: {output_dir}")

    def generate_all(
        self,
        scan_results: Dict[str, Any],
        formats: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate reports in all specified formats

        Args:
            scan_results: Scan results dictionary
            formats: List of formats to generate (html, json, pdf, sarif)
                    If None, generates all formats

        Returns:
            Dictionary mapping format to file path
        """
        if formats is None:
            formats = ['html', 'json', 'pdf', 'sarif']

        logger.info(f"Generating reports in formats: {', '.join(formats)}")

        # Create timestamped report directory
        report_dir = self._create_report_directory(scan_results)
        generated_reports = {}

        # Generate each format
        if 'html' in formats:
            try:
                html_path = report_dir / 'report.html'
                self.html_generator.generate(scan_results, str(html_path))
                generated_reports['html'] = str(html_path)
                logger.info(f"HTML report: {html_path}")
            except Exception as e:
                logger.error(f"Failed to generate HTML report: {e}")

        if 'json' in formats:
            try:
                json_path = report_dir / 'report.json'
                self.json_generator.generate(scan_results, str(json_path))
                generated_reports['json'] = str(json_path)
                logger.info(f"JSON report: {json_path}")
            except Exception as e:
                logger.error(f"Failed to generate JSON report: {e}")

        if 'pdf' in formats:
            try:
                pdf_path = report_dir / 'report.pdf'
                self.pdf_generator.generate(scan_results, str(pdf_path))
                generated_reports['pdf'] = str(pdf_path)
                logger.info(f"PDF report: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to generate PDF report: {e}")

        if 'sarif' in formats:
            try:
                sarif_path = report_dir / 'report.sarif'
                self.json_generator.generate_sarif(scan_results, str(sarif_path))
                generated_reports['sarif'] = str(sarif_path)
                logger.info(f"SARIF report: {sarif_path}")
            except Exception as e:
                logger.error(f"Failed to generate SARIF report: {e}")

        # Generate summary reports
        try:
            summary_json = report_dir / 'summary.json'
            self.json_generator.generate_summary(scan_results, str(summary_json))
            generated_reports['summary_json'] = str(summary_json)
        except Exception as e:
            logger.error(f"Failed to generate summary JSON: {e}")

        try:
            exec_summary_pdf = report_dir / 'executive_summary.pdf'
            self.pdf_generator.generate_executive_summary(
                scan_results,
                str(exec_summary_pdf)
            )
            generated_reports['executive_summary'] = str(exec_summary_pdf)
        except Exception as e:
            logger.error(f"Failed to generate executive summary PDF: {e}")

        # Create metadata file
        self._create_metadata_file(report_dir, scan_results, generated_reports)

        logger.info(f"Report generation complete. {len(generated_reports)} reports generated.")
        return generated_reports

    def generate_html(self, scan_results: Dict[str, Any]) -> str:
        """Generate HTML report only"""
        report_dir = self._create_report_directory(scan_results)
        html_path = report_dir / 'report.html'
        return self.html_generator.generate(scan_results, str(html_path))

    def generate_json(self, scan_results: Dict[str, Any]) -> str:
        """Generate JSON report only"""
        report_dir = self._create_report_directory(scan_results)
        json_path = report_dir / 'report.json'
        return self.json_generator.generate(scan_results, str(json_path))

    def generate_pdf(self, scan_results: Dict[str, Any]) -> str:
        """Generate PDF report only"""
        report_dir = self._create_report_directory(scan_results)
        pdf_path = report_dir / 'report.pdf'
        return self.pdf_generator.generate(scan_results, str(pdf_path))

    def generate_sarif(self, scan_results: Dict[str, Any]) -> str:
        """Generate SARIF report only"""
        report_dir = self._create_report_directory(scan_results)
        sarif_path = report_dir / 'report.sarif'
        return self.json_generator.generate_sarif(scan_results, str(sarif_path))

    def _create_report_directory(self, scan_results: Dict[str, Any]) -> Path:
        """
        Create timestamped directory for reports

        Args:
            scan_results: Scan results (to extract scan ID and application)

        Returns:
            Path to report directory
        """
        scan_info = scan_results.get('scan_info', {})
        application = scan_info.get('application', 'unknown')
        scan_id = scan_info.get('scan_id', datetime.utcnow().strftime('%Y%m%d_%H%M%S'))

        # Create directory structure: output_dir/application/scan_id/
        report_dir = self.output_dir / application / scan_id
        report_dir.mkdir(parents=True, exist_ok=True)

        return report_dir

    def _create_metadata_file(
        self,
        report_dir: Path,
        scan_results: Dict[str, Any],
        generated_reports: Dict[str, str]
    ):
        """
        Create metadata file with report information

        Args:
            report_dir: Report directory
            scan_results: Scan results
            generated_reports: Generated report paths
        """
        try:
            metadata = {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'scan_info': scan_results.get('scan_info', {}),
                'statistics': scan_results.get('statistics', {}),
                'reports': generated_reports,
                'generator_version': '1.0.0'
            }

            metadata_file = report_dir / 'metadata.json'
            import json
            with metadata_file.open('w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Metadata file created: {metadata_file}")

        except Exception as e:
            logger.error(f"Failed to create metadata file: {e}")

    def get_latest_report(self, application: str, format: str = 'html') -> Optional[str]:
        """
        Get path to latest report for an application

        Args:
            application: Application name
            format: Report format (html, json, pdf, sarif)

        Returns:
            Path to latest report or None
        """
        app_dir = self.output_dir / application
        if not app_dir.exists():
            return None

        # Get all scan directories (sorted by name, which includes timestamp)
        scan_dirs = sorted([d for d in app_dir.iterdir() if d.is_dir()], reverse=True)

        if not scan_dirs:
            return None

        # Look for report file in latest scan directory
        latest_dir = scan_dirs[0]
        report_file = latest_dir / f'report.{format}'

        if report_file.exists():
            return str(report_file)

        return None

    def list_reports(self, application: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available reports

        Args:
            application: Filter by application name (optional)

        Returns:
            List of report metadata
        """
        reports = []

        if application:
            app_dirs = [self.output_dir / application]
        else:
            app_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]

        for app_dir in app_dirs:
            if not app_dir.exists():
                continue

            app_name = app_dir.name

            # Get all scan directories
            scan_dirs = sorted([d for d in app_dir.iterdir() if d.is_dir()], reverse=True)

            for scan_dir in scan_dirs:
                metadata_file = scan_dir / 'metadata.json'

                if metadata_file.exists():
                    try:
                        import json
                        with metadata_file.open() as f:
                            metadata = json.load(f)

                        reports.append({
                            'application': app_name,
                            'scan_id': scan_dir.name,
                            'directory': str(scan_dir),
                            'metadata': metadata
                        })
                    except Exception as e:
                        logger.error(f"Failed to read metadata from {metadata_file}: {e}")

        return reports

    def cleanup_old_reports(self, application: str, keep_count: int = 10):
        """
        Clean up old reports, keeping only the most recent ones

        Args:
            application: Application name
            keep_count: Number of recent reports to keep
        """
        app_dir = self.output_dir / application
        if not app_dir.exists():
            return

        # Get all scan directories sorted by name (timestamp)
        scan_dirs = sorted([d for d in app_dir.iterdir() if d.is_dir()], reverse=True)

        # Delete older reports
        for old_dir in scan_dirs[keep_count:]:
            try:
                import shutil
                shutil.rmtree(old_dir)
                logger.info(f"Deleted old report directory: {old_dir}")
            except Exception as e:
                logger.error(f"Failed to delete {old_dir}: {e}")


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    sample_results = {
        'scan_info': {
            'application': 'test-app',
            'scan_id': 'scan-123',
            'scan_type': 'full',
            'target_url': 'http://example.com',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat(),
            'duration': 3600,
            'status': 'completed'
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

    manager = ReportManager(output_dir='./test_reports')
    reports = manager.generate_all(sample_results)

    print("Generated reports:")
    for format, path in reports.items():
        print(f"  {format}: {path}")

    # List all reports
    all_reports = manager.list_reports()
    print(f"\nTotal reports: {len(all_reports)}")
