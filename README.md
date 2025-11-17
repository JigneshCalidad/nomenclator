# nomenclator

> A gentle naming‑convention intelligence bot. It scans a full codebase, detects naming patterns, highlights inconsistencies, and proposes clean, human‑friendly names. Think of it as a reverse‑engineering guide that helps newcomers understand the project without confusion.

## Purpose

Naming is meaning. When names follow no pattern, a codebase feels like a maze. `nomenclator` reads the repo, infers its naming logic, and offers a consistent scheme across files, functions, classes, configs, endpoints, and docs.

This helps:

- **new developers** onboard faster,
- **existing developers** clean up inconsistencies,
- **teams** converge on shared naming intuition.

## Learning Path: Concept → Pattern → Details → Practice → Reflect

### Concept

Clear naming is the quiet backbone of maintainable software. Reduce cognitive load, raise clarity.

### Pattern

Scan → Analyze → Detect → Suggest → Export.

The bot doesn't enforce rules by force. It reads, understands, and teaches.

### Details

- Uses Python `ast` for accurate parsing.
- Uses heuristics for JS, Markdown, YAML.
- Extracts classes, functions, variables, modules, filenames.
- Computes naming patterns and violations.
- Suggests new names using configurable rules.
- Generates reports (HTML, JSON, CSV).
- Provides optional dry‑run rename planning.

### Practice

Labs guide you through scanning, reviewing suggestions, and adjusting naming rules.

### Reflect

Observe what patterns your mind prefers and how naming clarity affects your confidence.

## Features

- ✅ Multi-language naming scanner (Python, JavaScript, Markdown, YAML)
- ✅ Naming rules via YAML configuration
- ✅ HTML and JSON reports
- ✅ CLI for scanning and generating suggestions
- ✅ Dry‑run renaming plan
- ✅ Example repo with intentional inconsistencies
- ✅ CI pipeline (pytest + flake8)

## Project Structure

```
nomenclator/
├─ nomenclator/
│  ├─ __init__.py
│  ├─ core.py                 # Core scanning logic
│  ├─ rules.py                # Rules engine
│  ├─ report.py               # Report generation
│  ├─ apply.py                # Apply suggestions
│  └─ cli.py                  # CLI interface
├─ examples/sample_repo/
│  ├─ README.md
│  ├─ bad_naming.py           # Intentional violations
│  └─ sample.js               # Intentional violations
├─ tests/
│  ├─ test_rules.py
│  └─ test_scanner.py
├─ rules.yaml                 # Naming rules configuration
├─ pyproject.toml
├─ README.md
├─ LICENSE
└─ .github/workflows/ci.yml
```

## Quickstart

### Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Basic Usage

**Scan a repo:**

```bash
nomenclator scan examples/sample_repo --out scan.json
```

**Generate an HTML report:**

```bash
nomenclator report --format html --in scan.json --out report.html
```

**Dry-run rename suggestions:**

```bash
nomenclator apply-suggestions --dry-run
```

## Hands-on Labs

### Lab A: First Scan

**Goal:** Run a scan on the sample repo, inspect violations and suggestions.

**Steps:**

1. **Navigate to the project root:**

   ```bash
   cd /path/to/nomenclator
   ```

2. **Activate your virtual environment:**

   ```bash
   source .venv/bin/activate
   ```

3. **Run a scan on the example repo:**

   ```bash
   nomenclator scan examples/sample_repo --out scan.json
   ```

4. **Inspect the JSON output:**

   ```bash
   cat scan.json | jq '.'  # If you have jq installed
   # Or open scan.json in your editor
   ```

   **Observe:**
   - How many items were scanned?
   - What types of items were found (classes, functions, variables)?
   - How many violations were detected?

5. **Generate an HTML report:**

   ```bash
   nomenclator report --format html --in scan.json --out report.html
   ```

6. **Open the HTML report:**

   ```bash
   open report.html  # macOS
   # or
   xdg-open report.html  # Linux
   # or
   start report.html  # Windows
   ```

   **Notice:**
   - How different languages reveal different naming patterns
   - The severity levels (error, warning, info)
   - The suggestions provided for each violation

**Reflection Questions:**

- Which naming violations were easiest to spot?
- What patterns did you notice across Python vs JavaScript files?
- How do the suggestions help clarify the intended naming convention?

---

### Lab B: Staged Cleanup

**Goal:** Create a new branch, pick three safe rename suggestions, apply them manually, and commit changes.

**Steps:**

1. **Create a new branch:**

   ```bash
   git checkout -b naming-cleanup
   ```

2. **Generate a dry-run plan:**

   ```bash
   nomenclator apply-suggestions --dry-run --in scan.json --out rename-plan.txt
   ```

3. **Review the rename plan:**

   ```bash
   cat rename-plan.txt
   ```

   **Observe:**
   - Which files will be modified
   - The old names and new names
   - The suggested commands to apply changes

4. **Pick three safe suggestions:**

   Choose three violations that:
   - Are clearly wrong (e.g., PascalCase function in Python)
   - Won't break your code if renamed
   - Are in files you understand

5. **Apply changes manually:**

   For each suggestion:
   - Open the file in your editor
   - Find the line mentioned in the plan
   - Replace the old name with the new name
   - Make sure you update all references (not just the definition)

   **Example:**
   
   If the suggestion is to rename `ProcessData` → `process_data` in `examples/sample_repo/bad_naming.py`:
   
   ```python
   # Before:
   def ProcessData():
       pass
   
   # After:
   def process_data():
       pass
   ```

6. **Test your changes:**

   ```bash
   # Run the scanner again to verify
   nomenclator scan examples/sample_repo --out scan-after.json
   
   # Compare violation counts
   nomenclator report --format html --in scan-after.json --out report-after.html
   ```

7. **Commit your changes:**

   ```bash
   git add .
   git commit -m "Fix naming violations: process_data, user_count, etc."
   ```

8. **Compare before and after:**

   ```bash
   git diff main...naming-cleanup
   ```

**Reflection Questions:**

- Which renames felt most impactful?
- Did renaming improve code readability?
- What challenges did you encounter when applying renames?

---

### Lab C: Adjust Naming Rules

**Goal:** Open `rules.yaml`, change conventions (e.g., modules → kebab-case), re-run scan, and compare violation counts.

**Steps:**

1. **Examine the current rules:**

   ```bash
   cat rules.yaml
   ```

   **Observe:**
   - Python conventions (snake_case for modules, functions, variables)
   - JavaScript conventions (camelCase for functions, variables)
   - Markdown conventions (UPPER_SNAKE_CASE for files)

2. **Make a deliberate change:**

   Let's experiment with Python module naming. Change the convention for Python modules from `snake_case` to `kebab-case`:

   ```yaml
   # In rules.yaml, change:
   modules:
     case: snake_case
   
   # To:
   modules:
     case: kebab-case
   ```

   **Note:** This is intentionally different from Python's PEP 8 to demonstrate how rules affect violation detection.

3. **Save the rules file**

4. **Re-run the scan with the new rules:**

   ```bash
   nomenclator scan examples/sample_repo --out scan-new-rules.json --rules rules.yaml
   ```

5. **Generate a report with new rules:**

   ```bash
   nomenclator report --format html --in scan-new-rules.json --out report-new-rules.html
   ```

6. **Compare violation counts:**

   ```bash
   # Count violations in original scan
   cat scan.json | jq '.violation_statistics.total'
   
   # Count violations with new rules
   cat scan-new-rules.json | jq '.violation_statistics.total'
   ```

7. **Examine the differences:**

   - Which violations disappeared?
   - Which new violations appeared?
   - How do the suggestions differ?

8. **Restore original rules (optional):**

   If you want to revert:

   ```bash
   git checkout rules.yaml
   ```

**Reflection Questions:**

- How did changing the rules affect your perception of code quality?
- Which naming conventions feel most natural to you?
- How might team preferences influence rule configuration?

---

### Lab D: Custom Report Format

**Goal:** Generate reports in different formats (JSON, CSV, HTML) and explore their use cases.

**Steps:**

1. **Generate a CSV report:**

   ```bash
   nomenclator report --format csv --in scan.json --out report.csv
   ```

2. **Open the CSV in a spreadsheet:**

   ```bash
   open report.csv  # or use Excel, Google Sheets, etc.
   ```

   **Use cases:**
   - Sorting by severity
   - Filtering by file or language
   - Sharing with non-technical stakeholders
   - Creating charts and visualizations

3. **Generate a JSON report (detailed):**

   ```bash
   nomenclator report --format json --in scan.json --out report-detailed.json
   ```

4. **Parse JSON with jq (if available):**

   ```bash
   # List all files with violations
   cat report-detailed.json | jq '.items[] | select(.has_violations == true) | .file' | sort -u
   
   # Count violations by severity
   cat report-detailed.json | jq '.violation_statistics.by_severity'
   
   # Find all error-level violations
   cat report-detailed.json | jq '.items[] | select(.violations[]?.severity == "error")'
   ```

   **Use cases:**
   - Programmatic analysis
   - Integration with CI/CD pipelines
   - Custom reporting scripts

5. **Compare formats:**

   Create a summary document listing:
   - What information each format provides
   - When to use each format
   - Limitations of each format

**Reflection Questions:**

- Which format was most useful for your workflow?
- How could you integrate nomenclator into your development process?
- What additional information would be valuable in reports?

---

### Lab E: Real-World Project Scan

**Goal:** Scan your own project (or a small open-source project) and identify naming inconsistencies.

**Steps:**

1. **Choose a target project:**

   - A small personal project
   - A specific directory in a larger project
   - A cloned open-source repository

2. **Run an initial scan:**

   ```bash
   nomenclator scan /path/to/your/project --out my-project-scan.json
   ```

3. **Review the results:**

   - How many violations were found?
   - What are the most common violations?
   - Are there patterns specific to your codebase?

4. **Adjust rules to match your team's preferences:**

   Edit `rules.yaml` to match your project's conventions.

5. **Re-scan with custom rules:**

   ```bash
   nomenclator scan /path/to/your/project --out my-project-custom.json --rules rules.yaml
   ```

6. **Create a plan for improvements:**

   - Prioritize violations by severity
   - Identify low-risk renames to start with
   - Plan larger refactoring efforts

7. **Generate a presentation-ready report:**

   ```bash
   nomenclator report --format html --in my-project-custom.json --out my-project-report.html
   ```

**Reflection Questions:**

- What naming patterns emerged in your project?
- Which inconsistencies caused the most confusion when reading code?
- How do naming conventions shape your sense of project order and flow?
- What would you change about your project's naming conventions?

## Reflection Prompts

After completing the labs, consider these questions:

### On Naming Patterns

- Which naming patterns felt natural to you?
- Which felt forced or unnatural?
- How do different programming languages influence your naming preferences?

### On Code Clarity

- Which inconsistencies caused the most confusion when reading code?
- How did consistent naming improve code readability?
- What makes a name "good" vs "bad" in your mind?

### On Project Organization

- How do naming conventions shape your sense of project order and flow?
- What role does naming play in onboarding new developers?
- How might naming conventions reflect a team's values and priorities?

### On the Process

- What challenges did you encounter when applying renames?
- How might you integrate nomenclator into your workflow?
- What additional features would be valuable?

## Configuration

### Rules File (`rules.yaml`)

The rules file defines naming conventions for different languages and code elements. Key sections:

- **`conventions`**: Language-specific rules (Python, JavaScript, Markdown, YAML)
- **`violations`**: Severity level definitions
- **`reporting`**: Report generation options

Example:

```yaml
conventions:
  python:
    modules:
      case: snake_case
    classes:
      case: PascalCase
    functions:
      case: snake_case
```

## API Usage

You can also use nomenclator programmatically:

```python
from nomenclator import Scanner, RuleEngine, ReportGenerator

# Scan a directory
scanner = Scanner()
scan_result = scanner.scan("path/to/code")

# Apply rules
rule_engine = RuleEngine()
scan_result = rule_engine.analyze_scan(scan_result)

# Generate report
generator = ReportGenerator(scan_result)
generator.generate("html", "report.html")
```

## Contributing

Contributions are welcome! Areas for improvement:

- Additional language support
- More sophisticated naming pattern detection
- Integration with IDEs
- Team-specific rule presets

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Remember:** Naming is meaning. Consistent naming is a gift you give to your future self and your teammates. ✨

