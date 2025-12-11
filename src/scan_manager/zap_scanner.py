"""
ZAP Scanner
Manages OWASP ZAP Docker container lifecycle and scanning operations
"""

import os
import time
import logging
import docker
import requests
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ZAPScanner:
    """
    Manages OWASP ZAP scanner in Docker container
    """

    def __init__(
        self,
        zap_image: str = "ghcr.io/zaproxy/zaproxy:stable",
        network: str = "amtd-network"
    ):
        """
        Initialize ZAP Scanner

        Args:
            zap_image: Docker image for ZAP
            network: Docker network name
        """
        self.zap_image = zap_image
        self.network = network
        self.docker_client = docker.from_env()
        self.container = None
        self.zap_api_key = "amtd-api-key"
        self.zap_port = 8080
        self.zap_url = None

    def start_container(
        self,
        scan_id: str,
        memory_limit: str = "2g",
        cpu_limit: str = "2"
    ) -> str:
        """
        Start ZAP container

        Args:
            scan_id: Unique scan identifier
            memory_limit: Memory limit for container
            cpu_limit: CPU limit for container

        Returns:
            Container ID

        Raises:
            Exception: If container fails to start
        """
        container_name = f"amtd-zap-{scan_id}"

        logger.info(f"Starting ZAP container: {container_name}")

        try:
            # Remove existing container if it exists
            try:
                old_container = self.docker_client.containers.get(container_name)
                old_container.remove(force=True)
                logger.info(f"Removed existing container: {container_name}")
            except docker.errors.NotFound:
                pass

            # Start ZAP container
            self.container = self.docker_client.containers.run(
                self.zap_image,
                name=container_name,
                command=f"zap.sh -daemon -host 0.0.0.0 -port {self.zap_port} -config api.key={self.zap_api_key} -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true",
                detach=True,
                network=self.network,
                mem_limit=memory_limit,
                cpu_count=int(cpu_limit),
                remove=False,
                environment={
                    "ZAP_PORT": str(self.zap_port)
                }
            )

            # Wait for ZAP to be ready
            self.zap_url = f"http://{container_name}:{self.zap_port}"
            self._wait_for_zap()

            logger.info(f"ZAP container started successfully: {self.container.id}")
            return self.container.id

        except Exception as e:
            logger.error(f"Failed to start ZAP container: {e}")
            raise

    def _wait_for_zap(self, timeout: int = 120):
        """
        Wait for ZAP to be ready

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            TimeoutError: If ZAP doesn't start within timeout
        """
        logger.info("Waiting for ZAP to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.zap_url}/JSON/core/view/version/",
                    params={"apikey": self.zap_api_key},
                    timeout=5
                )
                if response.status_code == 200:
                    version = response.json().get("version", "unknown")
                    logger.info(f"ZAP is ready (version: {version})")
                    return
            except requests.exceptions.RequestException:
                pass

            time.sleep(2)

        raise TimeoutError(f"ZAP failed to start within {timeout} seconds")

    def spider_scan(
        self,
        target_url: str,
        max_depth: int = 5,
        max_children: int = 10
    ) -> str:
        """
        Start spider scan

        Args:
            target_url: Target URL to spider
            max_depth: Maximum spider depth
            max_children: Maximum child nodes per page

        Returns:
            Spider scan ID
        """
        logger.info(f"Starting spider scan on: {target_url}")

        # Configure spider
        self._api_call("spider/action/setOptionMaxDepth/", {"Integer": max_depth})
        self._api_call("spider/action/setOptionMaxChildren/", {"Integer": max_children})

        # Start spider
        response = self._api_call("spider/action/scan/", {"url": target_url})
        scan_id = response.get("scan", "")

        logger.info(f"Spider scan started with ID: {scan_id}")
        return scan_id

    def ajax_spider_scan(
        self,
        target_url: str,
        max_duration: int = 10
    ) -> str:
        """
        Start AJAX spider scan

        Args:
            target_url: Target URL to spider
            max_duration: Maximum scan duration in minutes

        Returns:
            AJAX spider scan status
        """
        logger.info(f"Starting AJAX spider scan on: {target_url}")

        # Configure AJAX spider
        self._api_call("ajaxSpider/action/setOptionMaxDuration/", {"Integer": max_duration})

        # Start AJAX spider
        response = self._api_call("ajaxSpider/action/scan/", {"url": target_url})

        logger.info("AJAX spider scan started")
        return response.get("Result", "")

    def active_scan(
        self,
        target_url: str,
        policy: Optional[str] = None
    ) -> str:
        """
        Start active scan

        Args:
            target_url: Target URL to scan
            policy: Scan policy name

        Returns:
            Active scan ID
        """
        logger.info(f"Starting active scan on: {target_url}")

        params = {"url": target_url, "recurse": "true"}
        if policy:
            params["scanPolicyName"] = policy

        response = self._api_call("ascan/action/scan/", params)
        scan_id = response.get("scan", "")

        logger.info(f"Active scan started with ID: {scan_id}")
        return scan_id

    def wait_for_spider(self, scan_id: str, timeout: int = 3600) -> bool:
        """
        Wait for spider scan to complete

        Args:
            scan_id: Spider scan ID
            timeout: Maximum time to wait

        Returns:
            True if completed successfully
        """
        logger.info(f"Waiting for spider scan {scan_id} to complete...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self._api_call("spider/view/status/", {"scanId": scan_id})
            status = int(response.get("status", 0))

            if status >= 100:
                logger.info(f"Spider scan {scan_id} completed")
                return True

            logger.debug(f"Spider progress: {status}%")
            time.sleep(5)

        logger.error(f"Spider scan {scan_id} timed out")
        return False

    def wait_for_active_scan(self, scan_id: str, timeout: int = 7200) -> bool:
        """
        Wait for active scan to complete

        Args:
            scan_id: Active scan ID
            timeout: Maximum time to wait

        Returns:
            True if completed successfully
        """
        logger.info(f"Waiting for active scan {scan_id} to complete...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self._api_call("ascan/view/status/", {"scanId": scan_id})
            status = int(response.get("status", 0))

            if status >= 100:
                logger.info(f"Active scan {scan_id} completed")
                return True

            logger.debug(f"Active scan progress: {status}%")
            time.sleep(10)

        logger.error(f"Active scan {scan_id} timed out")
        return False

    def get_alerts(self, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get scan alerts (vulnerabilities)

        Args:
            base_url: Filter alerts by base URL

        Returns:
            List of alerts
        """
        logger.info("Retrieving scan alerts...")

        params = {}
        if base_url:
            params["baseurl"] = base_url

        response = self._api_call("core/view/alerts/", params)
        alerts = response.get("alerts", [])

        logger.info(f"Retrieved {len(alerts)} alerts")
        return alerts

    def generate_html_report(self) -> str:
        """
        Generate HTML report

        Returns:
            HTML report content
        """
        logger.info("Generating HTML report...")

        response = self._api_call("core/other/htmlreport/")
        return response

    def generate_json_report(self) -> Dict[str, Any]:
        """
        Generate JSON report

        Returns:
            JSON report data
        """
        logger.info("Generating JSON report...")

        response = self._api_call("core/view/alerts/")
        return response

    def shutdown(self):
        """
        Shutdown ZAP gracefully
        """
        logger.info("Shutting down ZAP...")

        try:
            self._api_call("core/action/shutdown/")
            time.sleep(5)
        except Exception as e:
            logger.warning(f"Error during ZAP shutdown: {e}")

    def stop_container(self):
        """
        Stop and remove ZAP container
        """
        if self.container:
            logger.info(f"Stopping container: {self.container.name}")
            try:
                self.container.stop(timeout=10)
                self.container.remove()
                logger.info("Container stopped and removed")
            except Exception as e:
                logger.error(f"Error stopping container: {e}")
                try:
                    self.container.remove(force=True)
                except:
                    pass

        self.container = None
        self.zap_url = None

    def get_scan_progress(self) -> Dict[str, int]:
        """
        Get overall scan progress

        Returns:
            Dictionary with progress percentages
        """
        try:
            # Get number of records to scan
            response = self._api_call("pscan/view/recordsToScan/")
            records_to_scan = int(response.get("recordsToScan", 0))

            return {
                "records_to_scan": records_to_scan,
                "passive_scan_complete": records_to_scan == 0
            }
        except Exception as e:
            logger.error(f"Error getting scan progress: {e}")
            return {"records_to_scan": 0, "passive_scan_complete": False}

    def _api_call(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API call to ZAP

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response

        Raises:
            Exception: If API call fails
        """
        if not self.zap_url:
            raise Exception("ZAP container not started")

        if params is None:
            params = {}

        params["apikey"] = self.zap_api_key

        # Determine if JSON or OTHER endpoint
        if "/other/" in endpoint:
            url = f"{self.zap_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            return response.text
        else:
            url = f"{self.zap_url}/JSON/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

    def get_container_logs(self) -> str:
        """
        Get container logs

        Returns:
            Container logs as string
        """
        if self.container:
            try:
                logs = self.container.logs().decode('utf-8')
                return logs
            except Exception as e:
                logger.error(f"Error getting container logs: {e}")
                return ""
        return ""
