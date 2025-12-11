"""
JSON Report Generator
Generates structured JSON reports for programmatic consumption
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class JSONReportGenerator:
    """Generate structured JSON reports for security scans"""

    def __init__(self, pretty_print: bool = True, indent: int = 2):
        """
        Initialize JSON report generator

        Args:
            pretty_print: Enable pretty printing with indentation
            indent: Number of spaces for indentation
        """
        self.pretty_print = pretty_print
        self.indent = indent if pretty_print else None

        logger.info("JSON Report Generator initialized")

    def generate(
        self,
        scan_results: Dict[str, Any],
        output_path: str,
        include_metadata: bool = True
    ) -> str:
        """
        Generate JSON report from scan results

        Args:
            scan_results: Scan results dictionary
            output_path: Path to save JSON report
            include_metadata: Include generation metadata

        Returns:
            Path to generated report
        """
        try:
            logger.info(f"Generating JSON report: {output_path}")

            # Prepare report data
            report_data = self._prepare_report_data(scan_results, include_metadata)

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open('w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=self.indent, ensure_ascii=False)

            logger.info(f"JSON report generated successfully: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise

    def generate_summary(
        self,
        scan_results: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate summary JSON report with key metrics only

        Args:
            scan_results: Scan results dictionary
            output_path: Path to save summary report

        Returns:
            Path to generated report
        """
        try:
            logger.info(f"Generating JSON summary report: {output_path}")

            # Extract summary data
            summary_data = self._extract_summary(scan_results)

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open('w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=self.indent, ensure_ascii=False)

            logger.info(f"JSON summary generated successfully: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate JSON summary: {e}")
            raise

    def _prepare_report_data(
        self,
        scan_results: Dict[str, Any],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """
        Prepare complete report data

        Args:
            scan_results: Raw scan results
            include_metadata: Include metadata section

        Returns:
            Complete report data
        """
        report = {
            'version': '1.0',
            'format': 'AMTD-JSON-REPORT'
        }

        if include_metadata:
            report['metadata'] = {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'generator': 'AMTD JSON Report Generator',
                'generator_version': '1.0.0'
            }

        # Copy scan results
        report['scan_info'] = scan_results.get('scan_info', {})
        report['statistics'] = scan_results.get('statistics', {})
        report['vulnerabilities'] = scan_results.get('vulnerabilities', [])

        # Add risk assessment
        report['risk_assessment'] = self._calculate_risk_assessment(
            report['statistics']
        )

        # Add compliance information if available
        if 'compliance' in scan_results:
            report['compliance'] = scan_results['compliance']

        return report

    def _extract_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract summary information

        Args:
            scan_results: Full scan results

        Returns:
            Summary data
        """
        scan_info = scan_results.get('scan_info', {})
        statistics = scan_results.get('statistics', {})

        summary = {
            'application': scan_info.get('application'),
            'scan_id': scan_info.get('scan_id'),
            'scan_type': scan_info.get('scan_type'),
            'target_url': scan_info.get('target_url'),
            'started_at': scan_info.get('started_at'),
            'completed_at': scan_info.get('completed_at'),
            'duration': scan_info.get('duration'),
            'status': scan_info.get('status'),
            'statistics': statistics,
            'risk_score': self._calculate_risk_score(statistics),
            'passed_thresholds': self._check_thresholds(scan_results)
        }

        return summary

    def _calculate_risk_assessment(self, statistics: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate detailed risk assessment

        Args:
            statistics: Vulnerability statistics

        Returns:
            Risk assessment data
        """
        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)
        medium = statistics.get('medium', 0)
        low = statistics.get('low', 0)
        info = statistics.get('info', 0)
        total = statistics.get('total', 0)

        # Calculate risk score
        risk_score = self._calculate_risk_score(statistics)

        # Calculate severity distribution
        severity_distribution = {}
        if total > 0:
            severity_distribution = {
                'critical': round((critical / total) * 100, 2),
                'high': round((high / total) * 100, 2),
                'medium': round((medium / total) * 100, 2),
                'low': round((low / total) * 100, 2),
                'info': round((info / total) * 100, 2)
            }

        # Determine priority actions
        priority_actions = []
        if critical > 0:
            priority_actions.append(f"Address {critical} critical vulnerabilities immediately")
        if high > 5:
            priority_actions.append(f"Plan remediation for {high} high severity issues")
        if medium > 20:
            priority_actions.append(f"Review and prioritize {medium} medium severity findings")

        return {
            'risk_score': risk_score['score'],
            'risk_rating': risk_score['rating'],
            'severity_distribution': severity_distribution,
            'priority_actions': priority_actions,
            'requires_immediate_attention': critical > 0 or high > 10
        }

    def _calculate_risk_score(self, statistics: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate overall risk score

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

        # Normalize to 0-100
        normalized_score = min(score, 100)

        # Determine rating
        if normalized_score >= 80:
            rating = 'CRITICAL'
        elif normalized_score >= 60:
            rating = 'HIGH'
        elif normalized_score >= 40:
            rating = 'MEDIUM'
        elif normalized_score >= 20:
            rating = 'LOW'
        else:
            rating = 'MINIMAL'

        return {
            'score': normalized_score,
            'rating': rating
        }

    def _check_thresholds(self, scan_results: Dict[str, Any]) -> bool:
        """
        Check if scan passed configured thresholds

        Args:
            scan_results: Full scan results

        Returns:
            True if all thresholds passed
        """
        statistics = scan_results.get('statistics', {})
        thresholds = scan_results.get('scan_info', {}).get('thresholds', {})

        if not thresholds:
            return True

        # Check each threshold
        for severity, threshold in thresholds.items():
            count = statistics.get(severity, 0)
            if count > threshold:
                return False

        return True

    def generate_sarif(
        self,
        scan_results: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate SARIF format report for GitHub integration

        Args:
            scan_results: Scan results dictionary
            output_path: Path to save SARIF report

        Returns:
            Path to generated report
        """
        try:
            logger.info(f"Generating SARIF report: {output_path}")

            # Build SARIF structure
            sarif_report = {
                "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {
                            "driver": {
                                "name": "AMTD",
                                "version": "1.0.0",
                                "informationUri": "https://github.com/your-org/amtd",
                                "rules": []
                            }
                        },
                        "results": []
                    }
                ]
            }

            # Convert vulnerabilities to SARIF results
            vulnerabilities = scan_results.get('vulnerabilities', [])
            rules_map = {}

            for vuln in vulnerabilities:
                # Create rule if not exists
                rule_id = vuln.get('alert_id', vuln.get('name', 'unknown'))
                if rule_id not in rules_map:
                    rule = {
                        "id": str(rule_id),
                        "name": vuln.get('name', 'Unknown Vulnerability'),
                        "shortDescription": {
                            "text": vuln.get('name', 'Unknown Vulnerability')
                        },
                        "fullDescription": {
                            "text": vuln.get('description', '')
                        },
                        "help": {
                            "text": vuln.get('solution', '')
                        },
                        "properties": {
                            "category": vuln.get('category', 'Other'),
                            "cwe": vuln.get('cwe_id', '')
                        }
                    }
                    sarif_report["runs"][0]["tool"]["driver"]["rules"].append(rule)
                    rules_map[rule_id] = True

                # Create result
                result = {
                    "ruleId": str(rule_id),
                    "level": self._sarif_severity(vuln.get('severity', 'info')),
                    "message": {
                        "text": vuln.get('description', '')
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": vuln.get('url', '')
                                }
                            }
                        }
                    ]
                }

                sarif_report["runs"][0]["results"].append(result)

            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with output_file.open('w', encoding='utf-8') as f:
                json.dump(sarif_report, f, indent=self.indent, ensure_ascii=False)

            logger.info(f"SARIF report generated successfully: {output_path}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Failed to generate SARIF report: {e}")
            raise

    @staticmethod
    def _sarif_severity(severity: str) -> str:
        """Convert AMTD severity to SARIF level"""
        mapping = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'note',
            'info': 'note'
        }
        return mapping.get(severity.lower(), 'note')


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

    generator = JSONReportGenerator()
    report_path = generator.generate(sample_results, 'test_report.json')
    print(f"Report generated: {report_path}")

    summary_path = generator.generate_summary(sample_results, 'test_summary.json')
    print(f"Summary generated: {summary_path}")

    sarif_path = generator.generate_sarif(sample_results, 'test_report.sarif')
    print(f"SARIF report generated: {sarif_path}")
