"""Apply naming suggestions to codebase."""

import json
import logging
import platform
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SuggestionApplier:
    """Applies naming suggestions to files."""

    def __init__(self, scan_result_path: str):
        """Initialize with scan result file."""
        try:
            with open(scan_result_path, "r", encoding="utf-8") as f:
                self.scan_result = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Scan result file not found: {scan_result_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in scan result file: {e}")
        except (PermissionError, OSError) as e:
            raise IOError(f"Error reading scan result file: {e}")
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
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError) as e:
                logger.warning(f"Could not read file {file_path}: {e}")
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
                        # Generate platform-agnostic sed command
                        # macOS uses 'sed -i ''', Linux uses 'sed -i'
                        sed_suffix = "''" if platform.system() == "Darwin" else ""
                        escaped_old = re.escape(item['old_name'])
                        escaped_new = re.escape(item['new_name'])
                        output += f"    sed -i {sed_suffix} '{line_num + 1}s/{escaped_old}/{escaped_new}/' {file_path}\n"
                        output += f"    # Or manually edit line {item['line']}:\n"
                        output += f"    # Old: {old_line.strip()}\n"
                        output += f"    # New: {new_line.strip()}\n"
        
        output += "\n" + "=" * 80 + "\n"
        output += f"Total: {len(plan)} rename operations across {len(by_file)} files\n"
        output += "=" * 80 + "\n"
        
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(output)
            except (PermissionError, OSError) as e:
                logger.error(f"Error writing dry-run output to {output_path}: {e}")
                raise
        
        return output

    def _replace_name_in_line(self, line: str, old_name: str, new_name: str) -> str:
        """Replace name in a line of code (simple heuristic)."""
        # Simple word boundary replacement
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, line)

    def apply(self, dry_run: bool = True):
        """Apply rename suggestions."""
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
            try:
                # Read file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError) as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    continue
                
                # Apply replacements
                for item in items:
                    pattern = r'\b' + re.escape(item["old_name"]) + r'\b'
                    content = re.sub(pattern, item["new_name"], content)
                
                # Write file
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"Applied {len(items)} renames to {file_path}")
                except (PermissionError, OSError) as e:
                    logger.error(f"Error writing file {file_path}: {e}")
                    continue
            
            except Exception as e:
                logger.error(f"Unexpected error applying changes to {file_path}: {e}", exc_info=True)

