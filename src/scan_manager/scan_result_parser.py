"""
Scan Result Parser
Parses ZAP scan results into structured format
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ScanResultParser:
    """
    Parses ZAP scan alerts into structured vulnerability data
    """

    SEVERITY_MAP = {
        "0": "info",
        "1": "low",
        "2": "medium",
        "3": "high",
        "4": "critical"
    }

    CONFIDENCE_MAP = {
        "0": "false_positive",
        "1": "low",
        "2": "medium",
        "3": "high",
        "4": "confirmed"
    }

    def __init__(self):
        """Initialize parser"""
        pass

    def parse_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse ZAP alerts into structured format

        Args:
            alerts: List of ZAP alerts

        Returns:
            Dictionary with parsed vulnerabilities and statistics
        """
        logger.info(f"Parsing {len(alerts)} alerts...")

        vulnerabilities = []
        statistics = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'total': 0
        }

        for alert in alerts:
            try:
                vuln = self._parse_alert(alert)
                vulnerabilities.append(vuln)

                # Update statistics
                severity = vuln.get('severity', 'info')
                statistics[severity] = statistics.get(severity, 0) + 1
                statistics['total'] += 1

            except Exception as e:
                logger.error(f"Error parsing alert: {e}", exc_info=True)
                continue

        logger.info(f"Parsed {len(vulnerabilities)} vulnerabilities")
        logger.info(f"Statistics: {statistics}")

        return {
            'vulnerabilities': vulnerabilities,
            'statistics': statistics
        }

    def _parse_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse single ZAP alert

        Args:
            alert: ZAP alert dictionary

        Returns:
            Parsed vulnerability dictionary
        """
        # Map severity
        risk = alert.get('risk', '0')
        severity = self.SEVERITY_MAP.get(str(risk), 'info')

        # Map confidence
        confidence_level = alert.get('confidence', '0')
        confidence = self.CONFIDENCE_MAP.get(str(confidence_level), 'low')

        # Extract vulnerability details
        vuln = {
            # Basic information
            'name': alert.get('name', 'Unknown Vulnerability'),
            'type': alert.get('alert', alert.get('name', 'Unknown')),
            'severity': severity,
            'confidence': confidence,

            # Scoring
            'risk_code': int(risk),
            'confidence_code': int(confidence_level),

            # CWE/OWASP mapping
            'cwe_id': self._extract_cwe(alert),
            'owasp_category': self._map_owasp_category(alert),

            # Location
            'url': alert.get('url', ''),
            'method': alert.get('method', ''),
            'parameter': alert.get('param', ''),
            'attack': alert.get('attack', ''),

            # Evidence
            'evidence': alert.get('evidence', ''),
            'other_info': alert.get('other', ''),

            # Details
            'description': alert.get('description', ''),
            'solution': alert.get('solution', ''),
            'reference': alert.get('reference', ''),

            # Source
            'plugin_id': alert.get('pluginId', ''),
            'alert_ref': alert.get('alertRef', ''),
            'message_id': alert.get('messageId', ''),

            # Input/Output
            'input_vector': alert.get('inputVector', ''),

            # Status
            'status': 'new'
        }

        return vuln

    def _extract_cwe(self, alert: Dict[str, Any]) -> str:
        """
        Extract CWE ID from alert

        Args:
            alert: ZAP alert

        Returns:
            CWE ID (e.g., 'CWE-79')
        """
        cwe_id = alert.get('cweid', '')

        if cwe_id:
            if not cwe_id.startswith('CWE-'):
                cwe_id = f"CWE-{cwe_id}"
            return cwe_id

        return ''

    def _map_owasp_category(self, alert: Dict[str, Any]) -> str:
        """
        Map vulnerability to OWASP Top 10 category

        Args:
            alert: ZAP alert

        Returns:
            OWASP category
        """
        # Common mappings based on vulnerability type
        name = alert.get('name', '').lower()

        owasp_mappings = {
            'injection': 'A03:2021 - Injection',
            'sql injection': 'A03:2021 - Injection',
            'xss': 'A03:2021 - Injection',
            'cross site scripting': 'A03:2021 - Injection',
            'authentication': 'A07:2021 - Identification and Authentication Failures',
            'session': 'A07:2021 - Identification and Authentication Failures',
            'authorization': 'A01:2021 - Broken Access Control',
            'access control': 'A01:2021 - Broken Access Control',
            'sensitive data': 'A02:2021 - Cryptographic Failures',
            'encryption': 'A02:2021 - Cryptographic Failures',
            'xxe': 'A05:2021 - Security Misconfiguration',
            'misconfiguration': 'A05:2021 - Security Misconfiguration',
            'vulnerable component': 'A06:2021 - Vulnerable and Outdated Components',
            'outdated': 'A06:2021 - Vulnerable and Outdated Components',
            'logging': 'A09:2021 - Security Logging and Monitoring Failures',
            'monitoring': 'A09:2021 - Security Logging and Monitoring Failures',
            'ssrf': 'A10:2021 - Server-Side Request Forgery',
            'csrf': 'A01:2021 - Broken Access Control',
        }

        for keyword, category in owasp_mappings.items():
            if keyword in name:
                return category

        return 'Unknown'

    def calculate_cvss_score(self, alert: Dict[str, Any]) -> float:
        """
        Calculate approximate CVSS score

        Args:
            alert: ZAP alert

        Returns:
            CVSS score (0.0 - 10.0)
        """
        # Simple CVSS estimation based on risk
        risk = alert.get('risk', '0')

        cvss_scores = {
            '4': 9.0,  # Critical
            '3': 7.5,  # High
            '2': 5.0,  # Medium
            '1': 3.0,  # Low
            '0': 0.0   # Info
        }

        return cvss_scores.get(str(risk), 0.0)

    def group_by_severity(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group vulnerabilities by severity

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            Dictionary grouped by severity
        """
        grouped = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'info')
            if severity in grouped:
                grouped[severity].append(vuln)

        return grouped

    def filter_by_confidence(
        self,
        vulnerabilities: List[Dict[str, Any]],
        min_confidence: str = 'medium'
    ) -> List[Dict[str, Any]]:
        """
        Filter vulnerabilities by minimum confidence level

        Args:
            vulnerabilities: List of vulnerabilities
            min_confidence: Minimum confidence level (low, medium, high, confirmed)

        Returns:
            Filtered list of vulnerabilities
        """
        confidence_order = ['low', 'medium', 'high', 'confirmed']

        if min_confidence not in confidence_order:
            return vulnerabilities

        min_index = confidence_order.index(min_confidence)

        filtered = [
            vuln for vuln in vulnerabilities
            if vuln.get('confidence', 'low') in confidence_order[min_index:]
        ]

        logger.info(f"Filtered {len(vulnerabilities) - len(filtered)} low-confidence findings")
        return filtered

    def deduplicate(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate vulnerabilities

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for vuln in vulnerabilities:
            # Create unique key based on type, url, and parameter
            key = (
                vuln.get('type', ''),
                vuln.get('url', ''),
                vuln.get('parameter', '')
            )

            if key not in seen:
                seen.add(key)
                unique.append(vuln)

        if len(unique) < len(vulnerabilities):
            logger.info(f"Removed {len(vulnerabilities) - len(unique)} duplicate findings")

        return unique
