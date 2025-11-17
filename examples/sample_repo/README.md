# Sample Repo

This is an example repository with intentional naming inconsistencies to demonstrate nomenclator's capabilities.

## Purpose

This repo contains deliberately inconsistent naming patterns across different files to showcase how nomenclator detects violations and suggests improvements.

## Structure

- `bad_naming.py` - Python file with naming violations
- `sample.js` - JavaScript file with naming violations

## Running Nomenclator

```bash
# From project root
nomenclator scan examples/sample_repo --out scan.json
nomenclator report --format html --in scan.json --out report.html
```

