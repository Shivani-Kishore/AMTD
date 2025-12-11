# AMTD Report Generator Module

Professional multi-format report generation for security scans.

## Overview

The Report Generator module creates comprehensive security scan reports in multiple formats:
- HTML (Interactive web reports)
- JSON (Structured data for APIs)
- PDF (Professional printable reports)
- SARIF (GitHub security integration)

## Module Structure

```
src/report_generator/
├── __init__.py              # Module initialization
├── html_generator.py        # HTML report generation
├── json_generator.py        # JSON and SARIF generation
├── pdf_generator.py         # PDF report generation
├── report_manager.py        # Coordinates all generators
└── README.md               # This file

templates/reports/
├── report.html             # Main HTML template
├── report_pdf.html         # PDF template (full report)
├── executive_summary_pdf.html  # Executive summary template
└── assets/
    └── css/
        ├── report.css      # HTML styling
        └── pdf.css         # PDF styling
```

## Components

### 1. HTMLReportGenerator

Generates interactive HTML reports with:
- Real-time vulnerability statistics
- Interactive charts (Chart.js)
- Severity-based color coding
- Responsive design
- Detailed vulnerability listings

**Usage:**
```python
from report_generator import HTMLReportGenerator

generator = HTMLReportGenerator()
report_path = generator.generate(scan_results, 'report.html')
```

**Features:**
- Risk score calculation
- Vulnerability grouping by severity and category
- Top vulnerabilities identification
- Chart data preparation
- Custom Jinja2 filters

### 2. JSONReportGenerator

Generates structured JSON reports with:
- Complete scan results
- Risk assessment
- Summary reports
- SARIF format for GitHub

**Usage:**
```python
from report_generator import JSONReportGenerator

generator = JSONReportGenerator(pretty_print=True)

# Full report
generator.generate(scan_results, 'report.json')

# Summary only
generator.generate_summary(scan_results, 'summary.json')

# SARIF format
generator.generate_sarif(scan_results, 'report.sarif')
```

**Features:**
- Configurable indentation
- Metadata generation
- Risk assessment calculations
- Threshold validation
- GitHub SARIF format

### 3. PDFReportGenerator

Generates professional PDF reports using WeasyPrint:
- Full detailed reports
- Executive summaries
- Professional styling
- Page breaks and pagination

**Usage:**
```python
from report_generator import PDFReportGenerator

generator = PDFReportGenerator()

# Full report
generator.generate(scan_results, 'report.pdf')

# Executive summary
generator.generate_executive_summary(scan_results, 'summary.pdf')
```

**Features:**
- Executive summary generation
- Prioritized recommendations
- Professional typography
- Page break management
- Custom CSS styling

### 4. ReportManager

Coordinates all report generation:
- Multi-format generation
- Report organization
- Metadata tracking
- Report listing and cleanup

**Usage:**
```python
from report_generator import ReportManager

manager = ReportManager(output_dir='./reports')

# Generate all formats
reports = manager.generate_all(scan_results)

# Generate specific format
html_report = manager.generate_html(scan_results)
pdf_report = manager.generate_pdf(scan_results)

# List reports
all_reports = manager.list_reports(application='my-app')

# Cleanup old reports
manager.cleanup_old_reports(application='my-app', keep_count=10)
```

**Features:**
- Automatic directory organization
- Metadata file creation
- Report listing and searching
- Automatic cleanup
- Multiple format support

## Report Formats

### HTML Report

**Features:**
- Interactive and responsive
- Real-time charts
- Collapsible sections
- Print-friendly
- Bootstrap styling

**Sections:**
- Risk score overview
- Vulnerability statistics
- Severity distribution chart
- Category distribution chart
- Top vulnerabilities
- Detailed findings by severity

### JSON Report

**Structure:**
```json
{
  "version": "1.0",
  "format": "AMTD-JSON-REPORT",
  "metadata": { ... },
  "scan_info": { ... },
  "statistics": { ... },
  "vulnerabilities": [ ... ],
  "risk_assessment": { ... }
}
```

**Summary Format:**
```json
{
  "application": "my-app",
  "scan_id": "scan-123",
  "statistics": { ... },
  "risk_score": { ... },
  "passed_thresholds": true
}
```

### PDF Report

**Full Report Sections:**
1. Cover page
2. Executive summary
3. Risk assessment
4. Key findings
5. Vulnerability statistics
6. Recommendations
7. Detailed findings by severity
8. Scan information

**Executive Summary Sections:**
1. Header with application info
2. Risk score assessment
3. Executive summary text
4. Vulnerability overview
5. Key findings
6. Top priority issues
7. Recommendations
8. Scan details

### SARIF Report

**GitHub Integration Format:**
- SARIF 2.1.0 schema
- Tool driver information
- Security rules
- Results with locations
- Severity mappings

## Configuration

### Template Directory

Default: `templates/reports/`

Override:
```python
generator = HTMLReportGenerator(template_dir='/custom/templates')
```

### Output Directory

Organize reports by application and scan:
```
reports/
  ├── application-1/
  │   ├── scan-id-1/
  │   │   ├── report.html
  │   │   ├── report.json
  │   │   ├── report.pdf
  │   │   └── metadata.json
  │   └── scan-id-2/
  │       └── ...
  └── application-2/
      └── ...
```

## Customization

### Custom Jinja2 Filters

Available filters:
- `severity_color`: Get Bootstrap color class
- `severity_badge`: Generate badge HTML
- `format_timestamp`: Format ISO timestamps
- `format_duration`: Format seconds to readable format

Add custom filters:
```python
generator = HTMLReportGenerator()
generator.env.filters['my_filter'] = my_filter_function
```

### Custom CSS Styling

Modify templates/reports/assets/css/:
- `report.css`: HTML report styling
- `pdf.css`: PDF report styling

### Custom Templates

Create custom templates in template directory:
```python
template = generator.env.get_template('custom_report.html')
html_content = template.render(report=report_data)
```

## Risk Score Calculation

Risk score formula:
```
score = (critical * 10) + (high * 5) + (medium * 2) + (low * 1)
normalized = min(score, 100)
```

Risk ratings:
- 80-100: CRITICAL
- 60-79: HIGH
- 40-59: MEDIUM
- 20-39: LOW
- 0-19: MINIMAL

## Dependencies

Required Python packages:
- `jinja2`: Template engine
- `weasyprint`: PDF generation
- `pillow`: Image processing for PDF

Install:
```bash
pip install jinja2 weasyprint pillow
```

## Examples

### Generate All Formats

```python
from report_generator import ReportManager

scan_results = {
    'scan_info': {
        'application': 'my-app',
        'scan_id': 'scan-123',
        'scan_type': 'full',
        'target_url': 'http://example.com',
        'started_at': '2025-01-01T00:00:00Z',
        'completed_at': '2025-01-01T01:00:00Z',
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
    'vulnerabilities': [...]
}

manager = ReportManager(output_dir='./reports')
reports = manager.generate_all(scan_results, formats=['html', 'json', 'pdf'])

print(f"HTML: {reports['html']}")
print(f"JSON: {reports['json']}")
print(f"PDF: {reports['pdf']}")
```

### Custom Report Generation

```python
from report_generator import HTMLReportGenerator

generator = HTMLReportGenerator()

# Generate with custom options
report_path = generator.generate(
    scan_results,
    output_path='custom_report.html',
    include_charts=True
)
```

### List and Manage Reports

```python
from report_generator import ReportManager

manager = ReportManager(output_dir='./reports')

# List all reports
all_reports = manager.list_reports()
for report in all_reports:
    print(f"{report['application']}: {report['scan_id']}")

# Get latest report
latest_html = manager.get_latest_report('my-app', format='html')

# Cleanup old reports (keep last 10)
manager.cleanup_old_reports('my-app', keep_count=10)
```

## Integration

### With Scan Manager

```python
from scan_manager import ScanExecutor
from report_generator import ReportManager

# Execute scan
executor = ScanExecutor()
scan_results = executor.execute_scan('my-app')

# Generate reports
report_manager = ReportManager(output_dir='./reports')
reports = report_manager.generate_all(scan_results)
```

### With Jenkins

```groovy
stage('Generate Reports') {
    steps {
        script {
            sh """
                python3 -c "
                from report_generator import ReportManager
                import json

                with open('scan_results.json') as f:
                    results = json.load(f)

                manager = ReportManager('reports')
                reports = manager.generate_all(results)
                print(json.dumps(reports))
                "
            """
        }
    }
}
```

## Best Practices

1. **Directory Organization**: Use ReportManager for consistent organization
2. **Format Selection**: Generate only needed formats to save time
3. **Template Caching**: Jinja2 templates are cached automatically
4. **Error Handling**: Wrap generation in try-catch blocks
5. **Cleanup**: Regularly cleanup old reports
6. **Metadata**: Always generate metadata for tracking
7. **SARIF**: Use SARIF format for GitHub integration

## Troubleshooting

### WeasyPrint Issues

**Error**: Cannot find system fonts

**Solution**:
```bash
# Ubuntu/Debian
apt-get install fonts-liberation

# macOS
brew install cairo pango gdk-pixbuf libffi
```

### Template Not Found

**Error**: `TemplateNotFound: report.html`

**Solution**:
```python
# Specify correct template directory
generator = HTMLReportGenerator(template_dir='/path/to/templates')
```

### PDF Generation Fails

**Error**: `OSError: cannot load library 'gobject-2.0'`

**Solution**:
```bash
# Ubuntu/Debian
apt-get install libgobject-2.0-0

# macOS
brew install gobject-introspection
```

### Chart.js Not Loading

**Issue**: Charts not displaying in HTML reports

**Solution**: Ensure internet connection for CDN or use local Chart.js

## Performance

Report generation benchmarks (approximate):
- HTML: < 1 second
- JSON: < 0.5 seconds
- PDF: 2-5 seconds (depends on report size)
- SARIF: < 1 second

Optimization tips:
- Use `include_charts=False` for faster HTML generation
- Generate executive summaries instead of full PDFs
- Use JSON for programmatic access
- Cleanup old reports to save disk space

## Support

For issues or questions:
- Check main AMTD documentation
- Review Jinja2 template syntax
- Test with example scan results
- Check WeasyPrint documentation for PDF issues
