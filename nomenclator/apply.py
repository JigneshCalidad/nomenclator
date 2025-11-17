"""Apply naming suggestions to codebase."""

import json
import logging
import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SuggestionApplier:
    """Applies naming suggestions to files."""

    def __init__(self, scan_result_path: str):
        """Initialize with scan result file."""
        scan_path = Path(scan_result_path)
        if not scan_path.exists():
            raise FileNotFoundError(f"Scan result file not found: {scan_result_path}")
        
        try:
            with open(scan_path, "r", encoding="utf-8") as f:
                self.scan_result = json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            raise ValueError(f"Error reading scan result file: {e}") from e
        
        self.rename_plan: List[Dict] = []

    def generate_plan(self) -> List[Dict]:
        """Generate a rename plan from suggestions."""
        items = self.scan_result.get("items", [])
        violations = [item for item in items if item.get("has_violations")]
        
        plan = []
        
        for item in violations:
            name = item.get("name", "")
            file_path = item.get("file", "")
            line = item.get("line", 0)
            item_type = item.get("type", "")
            suggestions = item.get("suggestions", [])
            
            if suggestions:
                new_name = suggestions[0]
                if new_name != name:
                    plan.append({
                        "file": file_path,
                        "line": line,
                        "type": item_type,
                        "old_name": name,
                        "new_name": new_name,
                        "action": "rename",
                    })
        
        self.rename_plan = plan
        return plan

    def apply_dry_run(self, output_path: Optional[str] = None) -> str:
        """Generate dry-run output showing what would be changed."""
        plan = self.generate_plan()
        
        output = "=" * 80 + "\n"
        output += "DRY-RUN: Rename Plan\n"
        output += "=" * 80 + "\n\n"
        
        if not plan:
            output += "No rename suggestions found.\n"
            return output
        
        # Group by file
        by_file: Dict[str, List[Dict]] = {}
        for item in plan:
            file_path = item["file"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(item)
        
        for file_path, items in by_file.items():
            output += f"\nFile: {file_path}\n"
            output += "-" * 80 + "\n"
            
            for item in items:
                output += f"  Line {item['line']:4d} | {item['type']:10s} | "
                output += f"{item['old_name']:30s} → {item['new_name']}\n"
            
            # Generate commands for this file
            output += "\n  Commands to apply:\n"
            
            # Read file content
            try:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    output += f"    (File not found: {file_path})\n"
                    continue
                
                with open(file_path_obj, "r", encoding="utf-8") as f:
                    content = f.read()
            except (OSError, IOError, UnicodeDecodeError) as e:
                output += f"    (Could not read file: {e})\n"
                continue
            
            lines = content.split("\n")
            for item in items:
                line_num = item["line"] - 1
                if 0 <= line_num < len(lines):
                    old_line = lines[line_num]
                    new_line = self._replace_name_in_line(
                        old_line, item["old_name"], item["new_name"]
                    )
                    if old_line != new_line:
                        # Use platform-agnostic approach - show manual edit instructions
                        # Escape for shell safety
                        escaped_file = shlex.quote(str(file_path))
                        escaped_old = shlex.quote(item['old_name'])
                        escaped_new = shlex.quote(item['new_name'])
                        
                        output += f"    # Manual edit for line {item['line']}:\n"
                        output += f"    # Old: {old_line.strip()}\n"
                        output += f"    # New: {new_line.strip()}\n"
                        output += f"    # Python: Replace '{escaped_old}' with '{escaped_new}' in {escaped_file}\n"
        
        output += "\n" + "=" * 80 + "\n"
        output += f"Total: {len(plan)} rename operations across {len(by_file)} files\n"
        output += "=" * 80 + "\n"
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output)
        
        return output

    def _replace_name_in_line(self, line: str, old_name: str, new_name: str) -> str:
        """Replace name in a line of code (simple heuristic)."""
        # Simple word boundary replacement
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, line)

    def apply(self, dry_run: bool = True) -> Optional[str]:
        """Apply rename suggestions.
        
        Args:
            dry_run: If True, only show what would be changed. If False, apply changes.
            
        Returns:
            Dry-run output string if dry_run is True, None otherwise
        """
        if dry_run:
            return self.apply_dry_run()
        
        plan = self.generate_plan()
        
        # Group by file
        by_file: Dict[str, List[Dict]] = {}
        for item in plan:
            file_path = item["file"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(item)
        
        # Apply changes to each file
        for file_path, items in by_file.items():
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.warning(f"File not found, skipping: {file_path}")
                continue
            
            try:
                with open(file_path_obj, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original_content = content
                
                # Apply replacements
                for item in items:
                    pattern = r'\b' + re.escape(item["old_name"]) + r'\b'
                    content = re.sub(pattern, item["new_name"], content)
                
                # Only write if content changed
                if content != original_content:
                    with open(file_path_obj, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"Applied {len(items)} renames to {file_path}")
                else:
                    logger.warning(f"No changes made to {file_path} (names may not match)")
            
            except (OSError, IOError, UnicodeDecodeError) as e:
                logger.error(f"Error reading file {file_path}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error applying changes to {file_path}: {e}", exc_info=True)

