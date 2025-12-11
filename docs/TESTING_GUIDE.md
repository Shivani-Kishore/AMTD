# AMTD Testing Guide

**Version:** 1.0  
**Last Updated:** November 26, 2025

---

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [Test Data Management](#test-data-management)
- [CI/CD Integration](#cicd-integration)

---

## Testing Strategy

### Testing Pyramid

```
                    /\
                   /  \
                  / E2E \           10% - End-to-End
                 /______\
                /        \
               /Integration\        30% - Integration
              /____________\
             /              \
            /   Unit Tests   \     60% - Unit Tests
           /__________________\
```

### Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| **Core Logic** | 90%+ | P0 |
| **API Endpoints** | 85%+ | P0 |
| **Configuration** | 80%+ | P1 |
| **UI Components** | 75%+ | P2 |
| **Scripts** | 70%+ | P2 |

---

## Unit Testing

### Overview

Unit tests verify individual functions and classes in isolation.

### Setup

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock

# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### Writing Unit Tests

**File Structure:**
```
tests/
├── unit/
│   ├── test_scan_manager.py
│   ├── test_report_generator.py
│   ├── test_config_loader.py
│   └── test_notification_service.py
```

**Example: test_scan_manager.py**

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.scan_manager import ScanManager

class TestScanManager:
    """Test suite for ScanManager class."""
    
    @pytest.fixture
    def scan_manager(self):
        """Create ScanManager instance for testing."""
        return ScanManager(config={"timeout": 3600})
    
    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client."""
        with patch('docker.from_env') as mock:
            yield mock.return_value
    
    def test_start_scan_success(self, scan_manager, mock_docker_client):
        """Test successful scan initiation."""
        # Arrange
        target_url = "http://example.com"
        scan_config = {"type": "full", "timeout": 7200}
        
        mock_container = Mock()
        mock_container.id = "container123"
        mock_docker_client.containers.run.return_value = mock_container
        
        # Act
        result = scan_manager.start_scan(target_url, scan_config)
        
        # Assert
        assert result["status"] == "started"
        assert result["container_id"] == "container123"
        mock_docker_client.containers.run.assert_called_once()
    
    def test_start_scan_with_authentication(self, scan_manager):
        """Test scan with authentication credentials."""
        # Arrange
        target_url = "http://example.com"
        scan_config = {
            "type": "full",
            "authentication": {
                "type": "form",
                "username": "testuser",
                "password": "testpass"
            }
        }
        
        # Act
        with patch.object(scan_manager, '_configure_authentication') as mock_auth:
            scan_manager.start_scan(target_url, scan_config)
            
            # Assert
            mock_auth.assert_called_once_with(scan_config["authentication"])
    
    def test_start_scan_timeout_handling(self, scan_manager):
        """Test scan timeout error handling."""
        # Arrange
        target_url = "http://example.com"
        scan_config = {"type": "full", "timeout": 10}  # Very short timeout
        
        # Act & Assert
        with pytest.raises(TimeoutError):
            scan_manager.start_scan(target_url, scan_config)
    
    @pytest.mark.parametrize("scan_type,expected_depth", [
        ("quick", 3),
        ("full", 5),
        ("aggressive", 10),
    ])
    def test_scan_depth_configuration(self, scan_manager, scan_type, expected_depth):
        """Test scan depth varies by scan type."""
        # Act
        config = scan_manager._get_scan_config(scan_type)
        
        # Assert
        assert config["spider_depth"] == expected_depth
    
    def test_scan_status_monitoring(self, scan_manager, mock_docker_client):
        """Test scan status monitoring."""
        # Arrange
        container_id = "container123"
        mock_container = Mock()
        mock_container.status = "running"
        mock_container.logs.return_value = b"Scan progress: 50%"
        mock_docker_client.containers.get.return_value = mock_container
        
        # Act
        status = scan_manager.get_scan_status(container_id)
        
        # Assert
        assert status["status"] == "running"
        assert status["progress"] == 50
```

### Best Practices

1. **Arrange-Act-Assert Pattern:**
   ```python
   def test_example():
       # Arrange - Set up test data
       data = {"key": "value"}
       
       # Act - Execute the function
       result = process_data(data)
       
       # Assert - Verify the result
       assert result == expected_value
   ```

2. **Use Fixtures:**
   ```python
   @pytest.fixture
   def sample_config():
       return {
           "url": "http://example.com",
           "timeout": 3600
       }
   
   def test_with_fixture(sample_config):
       assert sample_config["url"] == "http://example.com"
   ```

3. **Mock External Dependencies:**
   ```python
   @patch('requests.get')
   def test_api_call(mock_get):
       mock_get.return_value.status_code = 200
       mock_get.return_value.json.return_value = {"status": "ok"}
       
       result = fetch_data()
       assert result["status"] == "ok"
   ```

4. **Test Edge Cases:**
   ```python
   @pytest.mark.parametrize("input,expected", [
       (None, ValueError),
       ("", ValueError),
       ("invalid-url", ValueError),
       ("http://valid.com", None),
   ])
   def test_url_validation(input, expected):
       if expected:
           with pytest.raises(expected):
               validate_url(input)
       else:
           validate_url(input)  # Should not raise
   ```

---

## Integration Testing

### Overview

Integration tests verify interactions between components.

### Setup

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Stop test environment
docker-compose -f docker-compose.test.yml down
```

### Writing Integration Tests

**Example: test_scan_pipeline.py**

```python
import pytest
import time
from src.pipeline_orchestrator import PipelineOrchestrator
from src.scan_manager import ScanManager
from src.report_generator import ReportGenerator

@pytest.mark.integration
class TestScanPipeline:
    """Integration tests for scan pipeline."""
    
    @pytest.fixture(scope="class")
    def test_target(self):
        """Start test application (Juice Shop)."""
        # Start container
        import docker
        client = docker.from_env()
        container = client.containers.run(
            "bkimminich/juice-shop",
            detach=True,
            ports={'3000/tcp': 3000}
        )
        
        # Wait for container to be ready
        time.sleep(10)
        
        yield "http://localhost:3000"
        
        # Cleanup
        container.stop()
        container.remove()
    
    def test_full_scan_pipeline(self, test_target):
        """Test complete scan pipeline end-to-end."""
        # Arrange
        orchestrator = PipelineOrchestrator()
        scan_config = {
            "target_url": test_target,
            "scan_type": "quick",
            "timeout": 300
        }
        
        # Act
        result = orchestrator.execute_scan(scan_config)
        
        # Assert
        assert result["status"] == "completed"
        assert "scan_id" in result
        assert result["vulnerabilities"]["total"] > 0
        assert len(result["reports"]) > 0
    
    def test_scan_with_database_persistence(self, test_target):
        """Test scan results are stored in database."""
        # Arrange
        from src.database import Database
        db = Database()
        scan_manager = ScanManager()
        
        # Act
        scan_result = scan_manager.start_scan(test_target, {"type": "quick"})
        scan_id = scan_result["scan_id"]
        
        # Wait for scan to complete
        while True:
            status = scan_manager.get_scan_status(scan_id)
            if status["status"] in ["completed", "failed"]:
                break
            time.sleep(5)
        
        # Assert
        stored_scan = db.get_scan(scan_id)
        assert stored_scan is not None
        assert stored_scan["target_url"] == test_target
        
        vulnerabilities = db.get_vulnerabilities(scan_id)
        assert len(vulnerabilities) > 0
    
    def test_report_generation_integration(self, test_target):
        """Test report generation from scan results."""
        # Arrange
        scan_manager = ScanManager()
        report_generator = ReportGenerator()
        
        # Act
        scan_result = scan_manager.start_scan(test_target, {"type": "quick"})
        
        # Wait for completion
        time.sleep(60)
        
        reports = report_generator.generate_all_reports(scan_result["scan_id"])
        
        # Assert
        assert "html" in reports
        assert "json" in reports
        assert "pdf" in reports
        
        # Verify HTML report exists and contains data
        import os
        assert os.path.exists(reports["html"])
        with open(reports["html"], 'r') as f:
            content = f.read()
            assert "Vulnerability Report" in content
            assert test_target in content
```

---

## End-to-End Testing

### Overview

E2E tests verify complete user workflows.

### Setup

```bash
# Run E2E tests
pytest tests/e2e/ --browser chrome
```

### Example E2E Test

```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.e2e
class TestJenkinsUI:
    """E2E tests for Jenkins UI workflows."""
    
    @pytest.fixture
    def driver(self):
        """Setup Selenium WebDriver."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_trigger_scan_via_ui(self, driver):
        """Test triggering a scan through Jenkins UI."""
        # Navigate to Jenkins
        driver.get("http://localhost:8080")
        
        # Login
        driver.find_element(By.ID, "username").send_keys("admin")
        driver.find_element(By.ID, "password").send_keys("admin")
        driver.find_element(By.ID, "login-button").click()
        
        # Navigate to AMTD job
        driver.find_element(By.LINK_TEXT, "AMTD Scan").click()
        
        # Build with parameters
        driver.find_element(By.LINK_TEXT, "Build with Parameters").click()
        
        # Fill parameters
        driver.find_element(By.NAME, "TARGET_URL").send_keys("http://juice-shop:3000")
        driver.find_element(By.NAME, "SCAN_TYPE").send_keys("quick")
        
        # Submit
        driver.find_element(By.NAME, "Submit").click()
        
        # Wait for build to start
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "build-row"))
        )
        
        # Verify build started
        assert "Build #" in driver.page_source
```

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_concurrent_scans.py
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.scan_manager import ScanManager

@pytest.mark.performance
class TestConcurrentScans:
    """Performance tests for concurrent scanning."""
    
    def test_10_concurrent_scans(self):
        """Test system handles 10 concurrent scans."""
        scan_manager = ScanManager()
        targets = [f"http://target{i}.example.com" for i in range(10)]
        
        def run_scan(target):
            return scan_manager.start_scan(target, {"type": "quick"})
        
        # Execute concurrent scans
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_scan, target) for target in targets]
            results = [f.result() for f in as_completed(futures)]
        
        # Verify all scans completed
        assert len(results) == 10
        assert all(r["status"] == "started" for r in results)
    
    def test_scan_performance_metrics(self):
        """Test scan completion time is within acceptable range."""
        import time
        scan_manager = ScanManager()
        
        start_time = time.time()
        result = scan_manager.start_scan(
            "http://localhost:3000",
            {"type": "quick"}
        )
        
        # Wait for completion
        while scan_manager.get_scan_status(result["scan_id"])["status"] == "running":
            time.sleep(5)
        
        duration = time.time() - start_time
        
        # Assert scan completes within 5 minutes for quick scan
        assert duration < 300, f"Scan took too long: {duration}s"
```

### Stress Testing

```bash
# Using Apache Bench
ab -n 1000 -c 50 http://localhost:8080/api/v1/scans

# Using Locust
locust -f tests/performance/locustfile.py --host=http://localhost:8080
```

---

## Security Testing

### Authentication Tests

```python
@pytest.mark.security
class TestAuthentication:
    """Security tests for authentication."""
    
    def test_api_requires_authentication(self):
        """Test API endpoints require authentication."""
        import requests
        
        # Without auth token
        response = requests.get("http://localhost:8080/api/v1/scans")
        assert response.status_code == 401
        
        # With invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get("http://localhost:8080/api/v1/scans", headers=headers)
        assert response.status_code == 401
    
    def test_sql_injection_prevention(self):
        """Test API is protected against SQL injection."""
        import requests
        
        # Attempt SQL injection
        malicious_payload = "'; DROP TABLE scans; --"
        response = requests.get(
            f"http://localhost:8080/api/v1/applications/{malicious_payload}"
        )
        
        # Should return 404, not execute SQL
        assert response.status_code in [400, 404]
```

---

## Test Data Management

### Test Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def test_database():
    """Create test database."""
    from src.database import Database
    db = Database("postgresql://localhost/amtd_test")
    db.init_schema()
    yield db
    db.drop_all()

@pytest.fixture
def sample_application(test_database):
    """Create sample application for testing."""
    app_data = {
        "name": "Test App",
        "url": "http://test.example.com",
        "owner": "test@example.com"
    }
    app_id = test_database.create_application(app_data)
    yield app_id
    test_database.delete_application(app_id)

@pytest.fixture
def sample_scan_results():
    """Load sample scan results."""
    import json
    with open('tests/fixtures/sample_scan.json') as f:
        return json.load(f)
```

### Test Data Files

```
tests/
├── fixtures/
│   ├── sample_scan.json
│   ├── sample_vulnerabilities.json
│   ├── sample_config.yaml
│   └── test_app_config.yaml
```

---

## CI/CD Integration

### GitHub Actions

**.github/workflows/test.yml:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run linters
        run: |
          flake8 src/
          pylint src/
      
      - name: Run unit tests
        run: pytest tests/unit/ --cov=src --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Test Execution

### Running All Tests

```bash
# All tests
pytest

# Specific test category
pytest -m unit
pytest -m integration
pytest -m e2e
pytest -m performance
pytest -m security

# Exclude slow tests
pytest -m "not slow"

# Run tests in parallel
pytest -n auto

# With verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Continuous Testing

```bash
# Watch mode (re-run on file changes)
pytest-watch

# Or using make
make test-watch
```

---

**Document Version:** 1.0  
**Last Updated:** November 26, 2025
