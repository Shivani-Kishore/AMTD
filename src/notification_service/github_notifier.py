"""
GitHub Integration Service
Creates GitHub issues for vulnerabilities and uploads SARIF reports
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubNotifier:
    """Create GitHub issues and upload SARIF reports for vulnerabilities"""

    def __init__(
        self,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None
    ):
        """
        Initialize GitHub Notifier

        Args:
            token: GitHub personal access token
            repo_owner: Repository owner/organization
            repo_name: Repository name
        """
        self.token = token or os.getenv('GITHUB_TOKEN', '')
        self.repo_owner = repo_owner or os.getenv('GITHUB_REPO_OWNER', '')
        self.repo_name = repo_name or os.getenv('GITHUB_REPO_NAME', '')

        self.api_base = 'https://api.github.com'
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        if not self.token:
            logger.warning("GitHub token not configured")

        logger.info(f"GitHub Notifier initialized for {self.repo_owner}/{self.repo_name}")

    def create_issues_for_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]],
        scan_info: Dict[str, Any],
        severity_filter: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Create GitHub issues for vulnerabilities

        Args:
            vulnerabilities: List of vulnerability dictionaries
            scan_info: Scan information
            severity_filter: Only create issues for these severities (e.g., ['critical', 'high'])
            labels: Additional labels to add to issues
            dry_run: If True, don't actually create issues

        Returns:
            Dictionary with created/skipped issue counts
        """
        try:
            if not self.token or not self.repo_owner or not self.repo_name:
                logger.error("GitHub configuration incomplete")
                return {'error': 'Configuration incomplete', 'created': 0, 'skipped': 0}

            logger.info(f"Creating GitHub issues for {len(vulnerabilities)} vulnerabilities")

            # Filter vulnerabilities by severity
            filtered_vulns = self._filter_vulnerabilities(vulnerabilities, severity_filter)

            created_count = 0
            skipped_count = 0
            errors = []

            for vuln in filtered_vulns:
                try:
                    # Check if issue already exists
                    if self._issue_exists(vuln):
                        logger.info(f"Issue already exists for: {vuln.get('name')}")
                        skipped_count += 1
                        continue

                    if dry_run:
                        logger.info(f"[DRY RUN] Would create issue for: {vuln.get('name')}")
                        created_count += 1
                        continue

                    # Create issue
                    issue = self._create_issue(vuln, scan_info, labels)
                    if issue:
                        logger.info(f"Created issue #{issue['number']}: {vuln.get('name')}")
                        created_count += 1
                    else:
                        skipped_count += 1

                except Exception as e:
                    logger.error(f"Failed to create issue for {vuln.get('name')}: {e}")
                    errors.append(str(e))
                    skipped_count += 1

            result = {
                'created': created_count,
                'skipped': skipped_count,
                'total': len(filtered_vulns),
                'errors': errors
            }

            logger.info(f"GitHub issue creation complete: {created_count} created, {skipped_count} skipped")
            return result

        except Exception as e:
            logger.error(f"Failed to create GitHub issues: {e}")
            return {'error': str(e), 'created': 0, 'skipped': 0}

    def upload_sarif_report(
        self,
        sarif_file_path: str,
        commit_sha: Optional[str] = None,
        ref: Optional[str] = None
    ) -> bool:
        """
        Upload SARIF report to GitHub Code Scanning

        Args:
            sarif_file_path: Path to SARIF report file
            commit_sha: Commit SHA (default: latest)
            ref: Git ref (default: main/master)

        Returns:
            True if uploaded successfully
        """
        try:
            if not self.token or not self.repo_owner or not self.repo_name:
                logger.error("GitHub configuration incomplete")
                return False

            logger.info(f"Uploading SARIF report to GitHub: {sarif_file_path}")

            # Read SARIF file
            import json
            with open(sarif_file_path, 'r') as f:
                sarif_data = json.load(f)

            # Encode SARIF as base64
            import base64
            sarif_base64 = base64.b64encode(
                json.dumps(sarif_data).encode()
            ).decode()

            # Get commit SHA if not provided
            if not commit_sha:
                commit_sha = self._get_latest_commit_sha(ref)

            if not commit_sha:
                logger.error("Could not determine commit SHA")
                return False

            # Upload to GitHub Code Scanning API
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/code-scanning/sarifs"

            payload = {
                'commit_sha': commit_sha,
                'ref': ref or 'refs/heads/main',
                'sarif': sarif_base64,
                'tool_name': 'AMTD'
            }

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 202]:
                logger.info("SARIF report uploaded successfully")
                return True
            else:
                logger.error(f"Failed to upload SARIF: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to upload SARIF report: {e}")
            return False

    def create_check_run(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int],
        conclusion: str = 'neutral',
        report_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create GitHub Check Run for scan results

        Args:
            scan_info: Scan information
            statistics: Vulnerability statistics
            conclusion: Check conclusion (success, failure, neutral, etc.)
            report_url: URL to full report

        Returns:
            Check run data or None
        """
        try:
            if not self.token or not self.repo_owner or not self.repo_name:
                logger.error("GitHub configuration incomplete")
                return None

            logger.info("Creating GitHub Check Run")

            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/check-runs"

            # Build check run data
            check_data = {
                'name': 'AMTD Security Scan',
                'head_sha': scan_info.get('commit_sha', self._get_latest_commit_sha()),
                'status': 'completed',
                'conclusion': conclusion,
                'completed_at': datetime.utcnow().isoformat() + 'Z',
                'output': {
                    'title': f"Security Scan - {scan_info.get('application')}",
                    'summary': self._build_check_summary(statistics),
                    'text': self._build_check_details(scan_info, statistics)
                }
            }

            if report_url:
                check_data['details_url'] = report_url

            # Add annotations for vulnerabilities
            annotations = self._build_annotations(statistics)
            if annotations:
                check_data['output']['annotations'] = annotations[:50]  # Max 50 annotations

            response = requests.post(
                url,
                headers={**self.headers, 'Accept': 'application/vnd.github.antiope-preview+json'},
                json=check_data,
                timeout=30
            )

            if response.status_code == 201:
                logger.info("Check run created successfully")
                return response.json()
            else:
                logger.error(f"Failed to create check run: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to create check run: {e}")
            return None

    def _create_issue(
        self,
        vuln: Dict[str, Any],
        scan_info: Dict[str, Any],
        additional_labels: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Create a GitHub issue for a vulnerability

        Args:
            vuln: Vulnerability data
            scan_info: Scan information
            additional_labels: Additional labels to add

        Returns:
            Created issue data or None
        """
        try:
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"

            # Build issue title
            severity = vuln.get('severity', 'unknown').upper()
            title = f"[{severity}] {vuln.get('name', 'Unknown Vulnerability')}"

            # Build issue body
            body = self._build_issue_body(vuln, scan_info)

            # Build labels
            labels = ['security', f'severity:{vuln.get("severity", "unknown")}']
            if additional_labels:
                labels.extend(additional_labels)

            # Add CWE label if available
            if vuln.get('cwe_id'):
                labels.append(f"cwe:{vuln.get('cwe_id')}")

            issue_data = {
                'title': title,
                'body': body,
                'labels': labels
            }

            response = requests.post(
                url,
                headers=self.headers,
                json=issue_data,
                timeout=30
            )

            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Failed to create issue: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None

    def _build_issue_body(
        self,
        vuln: Dict[str, Any],
        scan_info: Dict[str, Any]
    ) -> str:
        """Build issue body from vulnerability data"""
        severity = vuln.get('severity', 'unknown').upper()
        confidence = vuln.get('confidence', 'unknown').upper()

        body = f"""## Vulnerability Details

**Severity:** {severity}
**Confidence:** {confidence}

### Description

{vuln.get('description', 'No description available')}

### Affected URL

```
{vuln.get('url', 'Unknown')}
```

"""

        if vuln.get('method'):
            body += f"**HTTP Method:** {vuln.get('method')}\n\n"

        if vuln.get('parameter'):
            body += f"**Parameter:** `{vuln.get('parameter')}`\n\n"

        if vuln.get('evidence'):
            body += f"""### Evidence

```
{vuln.get('evidence')}
```

"""

        if vuln.get('solution'):
            body += f"""### Recommended Solution

{vuln.get('solution')}

"""

        if vuln.get('reference'):
            body += f"""### References

{vuln.get('reference')}

"""

        # Add metadata
        body += f"""---

**Scan Information:**
- Application: {scan_info.get('application', 'Unknown')}
- Scan ID: {scan_info.get('scan_id', 'Unknown')}
- Scan Type: {scan_info.get('scan_type', 'unknown').upper()}
- Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

"""

        if vuln.get('cwe_id'):
            body += f"\n**CWE:** {vuln.get('cwe_id')}"

        if vuln.get('category'):
            body += f"\n**Category:** {vuln.get('category')}"

        body += "\n\n*This issue was automatically created by AMTD Security Scanner*"

        return body

    def _issue_exists(self, vuln: Dict[str, Any]) -> bool:
        """
        Check if issue already exists for this vulnerability

        Args:
            vuln: Vulnerability data

        Returns:
            True if issue exists
        """
        try:
            # Search for existing issues with same title
            vuln_name = vuln.get('name', '')
            severity = vuln.get('severity', 'unknown').upper()
            title = f"[{severity}] {vuln_name}"

            url = f"{self.api_base}/search/issues"
            params = {
                'q': f'repo:{self.repo_owner}/{self.repo_name} is:issue "{title}" in:title'
            }

            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('total_count', 0) > 0

            return False

        except Exception as e:
            logger.error(f"Failed to check for existing issue: {e}")
            return False

    def _filter_vulnerabilities(
        self,
        vulnerabilities: List[Dict],
        severity_filter: Optional[List[str]]
    ) -> List[Dict]:
        """Filter vulnerabilities by severity"""
        if not severity_filter:
            return vulnerabilities

        return [
            v for v in vulnerabilities
            if v.get('severity', '').lower() in [s.lower() for s in severity_filter]
        ]

    def _get_latest_commit_sha(self, ref: Optional[str] = None) -> Optional[str]:
        """Get latest commit SHA for repository"""
        try:
            branch = ref or 'main'
            url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{branch}"

            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()['sha']

            # Try master if main fails
            if branch == 'main':
                return self._get_latest_commit_sha('master')

            return None

        except Exception as e:
            logger.error(f"Failed to get latest commit SHA: {e}")
            return None

    def _build_check_summary(self, statistics: Dict[str, int]) -> str:
        """Build check run summary"""
        total = statistics.get('total', 0)
        critical = statistics.get('critical', 0)
        high = statistics.get('high', 0)

        if total == 0:
            return "No vulnerabilities detected"
        elif critical > 0:
            return f"Found {critical} critical vulnerabilities (Total: {total})"
        elif high > 0:
            return f"Found {high} high severity vulnerabilities (Total: {total})"
        else:
            return f"Found {total} vulnerabilities"

    def _build_check_details(
        self,
        scan_info: Dict[str, Any],
        statistics: Dict[str, int]
    ) -> str:
        """Build detailed check run output"""
        details = f"""## Vulnerability Summary

| Severity | Count |
|----------|-------|
| Critical | {statistics.get('critical', 0)} |
| High | {statistics.get('high', 0)} |
| Medium | {statistics.get('medium', 0)} |
| Low | {statistics.get('low', 0)} |
| Info | {statistics.get('info', 0)} |
| **Total** | **{statistics.get('total', 0)}** |

**Scan Details:**
- Application: {scan_info.get('application', 'Unknown')}
- Scan Type: {scan_info.get('scan_type', 'unknown').upper()}
- Target: {scan_info.get('target_url', 'Unknown')}
"""
        return details

    def _build_annotations(self, statistics: Dict[str, int]) -> List[Dict]:
        """Build annotations for check run"""
        # Placeholder - would need actual vulnerability data with file locations
        # For now, return empty list
        return []

    def test_connection(self) -> bool:
        """
        Test GitHub API connection

        Returns:
            True if connection successful
        """
        try:
            if not self.token:
                logger.error("GitHub token not configured")
                return False

            url = f"{self.api_base}/user"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                user = response.json()
                logger.info(f"GitHub connection successful. Authenticated as: {user.get('login')}")
                return True
            else:
                logger.error(f"GitHub connection failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    notifier = GitHubNotifier()

    # Test connection
    if notifier.test_connection():
        print("GitHub connection successful")

        # Example vulnerability
        vulnerabilities = [{
            'name': 'SQL Injection',
            'severity': 'critical',
            'confidence': 'high',
            'description': 'SQL injection vulnerability detected',
            'url': 'http://example.com/login',
            'method': 'POST',
            'parameter': 'username',
            'solution': 'Use parameterized queries',
            'cwe_id': 'CWE-89'
        }]

        scan_info = {
            'application': 'test-app',
            'scan_id': 'scan-123',
            'scan_type': 'full',
            'target_url': 'http://example.com'
        }

        # Create issues (dry run)
        result = notifier.create_issues_for_vulnerabilities(
            vulnerabilities,
            scan_info,
            severity_filter=['critical', 'high'],
            dry_run=True
        )
        print(f"Result: {result}")
