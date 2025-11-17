"""Report generation for nomenclator."""

import json
from typing import Dict


class ReportGenerator:
    """Generates reports in various formats."""

    def __init__(self, scan_result: Dict):
        """Initialize with scan results."""
        if not scan_result:
            raise ValueError("Scan result cannot be empty")
        if not isinstance(scan_result, dict):
            raise TypeError("Scan result must be a dictionary")
        self.scan_result = scan_result

    def generate_json(self, output_path: str):
        """Generate JSON report."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.scan_result, f, indent=2)

    def generate_csv(self, output_path: str):
        """Generate CSV report."""
        import csv

        items = self.scan_result.get("items", [])
        violations = [item for item in items if item.get("has_violations")]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "File", "Line", "Type", "Language", "Name",
                "Violation Type", "Severity", "Expected", "Actual", "Suggestion"
            ])

            for item in violations:
                file_path = item.get("file", "")
                line = item.get("line", 0)
                item_type = item.get("type", "")
                language = item.get("language", "")
                name = item.get("name", "")

                violations_list = item.get("violations", [])
                suggestions = item.get("suggestions", [])
                suggestion = suggestions[0] if suggestions else ""

                if violations_list:
                    for violation in violations_list:
                        violation_type = violation.get("type", "")
                        severity = violation.get("severity", "")
                        expected = violation.get("expected", "")
                        actual = violation.get("actual", "")

                        writer.writerow([
                            file_path, line, item_type, language, name,
                            violation_type, severity, expected, actual, suggestion
                        ])
                else:
                    writer.writerow([
                        file_path, line, item_type, language, name,
                        "", "", "", "", suggestion
                    ])

    def generate_html(self, output_path: str):
        """Generate HTML report."""
        items = self.scan_result.get("items", [])
        violations = [item for item in items if item.get("has_violations")]

        stats = self.scan_result.get("violation_statistics", {})
        scan_stats = self.scan_result.get("statistics", {})

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nomenclator Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            flex: 1;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .severity-error {{ color: #e74c3c; }}
        .severity-warning {{ color: #f39c12; }}
        .severity-info {{ color: #3498db; }}
        .violations {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .violation-item {{
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin-bottom: 15px;
            background: #fff;
            border-radius: 4px;
        }}
        .violation-item.warning {{
            border-left-color: #f39c12;
        }}
        .violation-item.info {{
            border-left-color: #3498db;
        }}
        .violation-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .violation-name {{
            font-weight: bold;
            font-size: 1.1em;
            color: #2c3e50;
        }}
        .violation-type {{
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        .violation-details {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ecf0f1;
        }}
        .violation-detail {{
            margin: 5px 0;
        }}
        .suggestion {{
            background: #e8f5e9;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .suggestion-label {{
            font-weight: bold;
            color: #2e7d32;
        }}
        .file-path {{
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        .no-violations {{
            text-align: center;
            padding: 40px;
            color: #27ae60;
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Nomenclator Report</h1>
        <p class="file-path">Scanned: {self.scan_result.get('path', 'N/A')}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{stats.get('total', 0)}</div>
                <div class="stat-label">Total Violations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value severity-error">
                    {stats.get('by_severity', {}).get('error', 0)}
                </div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value severity-warning">
                    {stats.get('by_severity', {}).get('warning', 0)}
                </div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{scan_stats.get('total_items', 0)}</div>
                <div class="stat-label">Items Scanned</div>
            </div>
        </div>
    </div>

    <div class="violations">
        <h2>Violations</h2>
"""

        if not violations:
            html += (
                '<div class="no-violations">'
                '✨ No violations found! Your codebase follows naming conventions.'
                '</div>'
            )
        else:
            for item in violations:
                name = item.get("name", "")
                file_path = item.get("file", "")
                line = item.get("line", 0)
                item_type = item.get("type", "")
                language = item.get("language", "")
                violations_list = item.get("violations", [])
                suggestions = item.get("suggestions", [])

                # Determine highest severity
                severities = [v.get("severity", "info") for v in violations_list]
                if "error" in severities:
                    highest_severity = "error"
                elif "warning" in severities:
                    highest_severity = "warning"
                else:
                    highest_severity = "info"

                html += f'<div class="violation-item {highest_severity}">'
                html += '<div class="violation-header">'
                html += '<div>'
                html += f'<div class="violation-name">{name}</div>'
                html += f'<div class="violation-type">{item_type} in {language}</div>'
                html += '</div>'
                html += f'<div class="file-path">{file_path}:{line}</div>'
                html += '</div>'

                html += '<div class="violation-details">'
                for violation in violations_list:
                    violation_type = violation.get("type", "")
                    severity = violation.get("severity", "")
                    expected = violation.get("expected", "")
                    actual = violation.get("actual", "")

                    html += '<div class="violation-detail">'
                    severity_span = (
                        f'<span class="severity-{severity}">'
                        f'<strong>{severity.upper()}</strong></span>: '
                    )
                    html += severity_span
                    html += (
                        f'{violation_type} - Expected {expected}, '
                        f'found {actual}'
                    )
                    html += '</div>'

                if suggestions:
                    suggestion = suggestions[0]
                    html += '<div class="suggestion">'
                    html += (
                        '<span class="suggestion-label">💡 Suggestion:</span> '
                        f'<code>{suggestion}</code>'
                    )
                    html += '</div>'

                html += '</div>'
                html += '</div>'

        html += """
    </div>
</body>
</html>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def generate(self, format_type: str, output_path: str):
        """Generate report in specified format."""
        if format_type == "json":
            self.generate_json(output_path)
        elif format_type == "html":
            self.generate_html(output_path)
        elif format_type == "csv":
            self.generate_csv(output_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
