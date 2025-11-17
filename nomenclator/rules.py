"""Rule engine for checking naming conventions."""

import re
from typing import Dict, List, Optional

import yaml


class RuleEngine:
    """Evaluates naming patterns against rules."""

    def __init__(self, rules_path: str = "rules.yaml"):
        """Initialize rule engine with rules file."""
        self.rules_path = rules_path
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load rules from YAML file."""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def check_item(self, item: Dict) -> Dict:
        """
        Check a single item against naming rules.
        
        Returns:
            Dictionary with violation information or None if compliant
        """
        language = item.get("language")
        item_type = item.get("type")
        name = item.get("name")
        is_private = item.get("private", False)
        
        if not all([language, item_type, name]):
            return {"compliant": True}
        
        # Get rules for this language and type
        convention = self._get_convention(language, item_type, is_private=is_private)
        if not convention:
            return {"compliant": True}
        
        case_rule = convention.get("case")
        prefix_rule = convention.get("prefix")
        
        violations = []
        suggestions = []
        
        # Check case convention
        if case_rule:
            expected_case = case_rule
            actual_case = self._detect_case(name)
            
            if actual_case != expected_case:
                severity = self._determine_severity(item_type, expected_case, actual_case)
                violations.append({
                    "type": "case_mismatch",
                    "expected": expected_case,
                    "actual": actual_case,
                    "severity": severity,
                })
                
                # Generate suggestion
                suggested_name = self._suggest_name(name, expected_case)
                if suggested_name != name:
                    suggestions.append(suggested_name)
        
        # Check prefix convention
        if prefix_rule:
            if item.get("private", False) and not name.startswith(prefix_rule):
                violations.append({
                    "type": "missing_prefix",
                    "expected_prefix": prefix_rule,
                    "severity": "warning",
                })
                suggestions.append(prefix_rule + name)
        
        if violations:
            return {
                "compliant": False,
                "violations": violations,
                "suggestions": suggestions[:1] if suggestions else [],  # Top suggestion
            }
        
        return {"compliant": True}

    def _get_convention(self, language: str, item_type: str, is_private: bool = False) -> Optional[Dict]:
        """Get convention rules for language and type."""
        conventions = self.rules.get("conventions", {})
        lang_rules = conventions.get(language, {})
        
        # Map item types to rule keys
        type_map = {
            "module": "modules",
            "file": "files",
            "class": "classes",
            "function": "functions",
            "variable": "variables",
            "constant": "constants",
        }
        
        rule_key = type_map.get(item_type)
        base_rules = lang_rules.get(rule_key, {}) if rule_key else {}
        merged_rules = dict(base_rules) if base_rules else {}
        
        if is_private:
            private_rules = lang_rules.get("private", {})
            for key, value in private_rules.items():
                merged_rules.setdefault(key, value)
        
        return merged_rules or None

    def _detect_case(self, name: str) -> str:
        """Detect the naming case of a string."""
        if name.isupper() and ("_" in name or name.isalpha()):
            return "UPPER_SNAKE_CASE"
        elif name.islower() and "_" in name:
            return "snake_case"
        elif name.islower() and "-" in name:
            return "kebab-case"
        elif name[0].isupper() and "_" not in name and "-" not in name:
            return "PascalCase"
        elif name[0].islower() and "_" not in name and "-" not in name:
            # Check for camelCase (has uppercase letters inside)
            if any(c.isupper() for c in name[1:]):
                return "camelCase"
            return "lowercase"
        else:
            return "mixed"

    def _determine_severity(self, item_type: str, expected: str, actual: str) -> str:
        """Determine violation severity."""
        # Some mismatches are worse than others
        if item_type == "function" and actual == "PascalCase":
            return "error"  # Functions should never be PascalCase
        elif item_type == "class" and actual == "snake_case":
            return "error"  # Classes should be PascalCase
        elif actual == "mixed":
            return "error"
        else:
            return "warning"

    def _suggest_name(self, name: str, target_case: str) -> str:
        """Suggest a name in target case format."""
        if target_case == "snake_case":
            return self._to_snake_case(name)
        elif target_case == "PascalCase":
            return self._to_pascal_case(name)
        elif target_case == "camelCase":
            return self._to_camel_case(name)
        elif target_case == "kebab-case":
            return self._to_kebab_case(name)
        elif target_case == "UPPER_SNAKE_CASE":
            return self._to_upper_snake_case(name)
        else:
            return name

    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case."""
        # Handle already mixed formats
        if "_" in name:
            return name.lower()
        # Insert underscores before capitals
        name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        return name.lower().replace("-", "_")

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        # Remove underscores and hyphens, capitalize words
        words = re.split(r"[_\-]+", name)
        return "".join(word.capitalize() for word in words if word)

    def _to_camel_case(self, name: str) -> str:
        """Convert to camelCase."""
        pascal = self._to_pascal_case(name)
        return pascal[0].lower() + pascal[1:] if pascal else ""

    def _to_kebab_case(self, name: str) -> str:
        """Convert to kebab-case."""
        snake = self._to_snake_case(name)
        return snake.replace("_", "-")

    def _to_upper_snake_case(self, name: str) -> str:
        """Convert to UPPER_SNAKE_CASE."""
        snake = self._to_snake_case(name)
        return snake.upper()

    def analyze_scan(self, scan_result: Dict) -> Dict:
        """
        Analyze full scan results and add violations.
        
        Returns:
            Scan result with violations and suggestions added
        """
        items_with_violations = []
        
        for item in scan_result.get("items", []):
            check_result = self.check_item(item)
            if not check_result.get("compliant", True):
                item["violations"] = check_result["violations"]
                item["suggestions"] = check_result.get("suggestions", [])
                item["has_violations"] = True
            else:
                item["has_violations"] = False
            
            items_with_violations.append(item)
        
        scan_result["items"] = items_with_violations
        
        # Compute violation statistics
        violations = [item for item in items_with_violations if item.get("has_violations")]
        by_severity = {"error": 0, "warning": 0, "info": 0}
        
        for item in violations:
            for violation in item.get("violations", []):
                severity = violation.get("severity", "info")
                by_severity[severity] = by_severity.get(severity, 0) + 1
        
        scan_result["violation_statistics"] = {
            "total": len(violations),
            "by_severity": by_severity,
        }
        
        return scan_result

