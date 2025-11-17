"""Core scanning functionality for nomenclator."""

import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


class Scanner:
    """Scans codebase for naming patterns and violations."""

    def __init__(self, rules_path: Optional[str] = None):
        """Initialize scanner with rules."""
        self.rules_path = rules_path or "rules.yaml"
        self.items: List[Dict] = []
        self.languages: Set[str] = set()

    def scan(self, path: str) -> Dict:
        """
        Scan a directory or file for naming patterns.
        
        Returns:
            Dictionary with scan results including items and statistics
        """
        self.items = []
        self.languages = set()
        
        path_obj = Path(path)
        
        if path_obj.is_file():
            self._scan_file(path_obj)
        elif path_obj.is_dir():
            self._scan_directory(path_obj)
        else:
            raise ValueError(f"Path does not exist: {path}")
        
        return {
            "path": str(path),
            "items": self.items,
            "statistics": self._compute_statistics(),
        }

    def _scan_directory(self, directory: Path, ignore_patterns: Optional[Set[str]] = None):
        """Recursively scan directory for code files."""
        if ignore_patterns is None:
            ignore_patterns = {
                "__pycache__", ".git", ".venv", "venv", "node_modules",
                ".pytest_cache", ".mypy_cache", "dist", "build", ".eggs"
            }
        
        try:
            for file_path in directory.rglob("*"):
                # Skip ignored directories
                if any(ignore_pattern in file_path.parts for ignore_pattern in ignore_patterns):
                    continue
                
                if file_path.is_file() and self._should_scan(file_path):
                    self._scan_file(file_path)
        except (PermissionError, OSError) as e:
            logger.warning(f"Error accessing directory {directory}: {e}")

    def _should_scan(self, file_path: Path) -> bool:
        """Check if file should be scanned based on extension."""
        extensions = {".py", ".js", ".md", ".yaml", ".yml"}
        return file_path.suffix in extensions

    def _scan_file(self, file_path: Path):
        """Scan a single file for naming patterns."""
        extension = file_path.suffix
        
        if extension == ".py":
            self._scan_python(file_path)
            self.languages.add("python")
        elif extension == ".js":
            self._scan_javascript(file_path)
            self.languages.add("javascript")
        elif extension in {".yaml", ".yml"}:
            self._scan_yaml(file_path)
            self.languages.add("yaml")
        elif extension == ".md":
            self._scan_markdown(file_path)
            self.languages.add("markdown")

    def _scan_python(self, file_path: Path):
        """Scan Python file using AST."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # Extract filename itself
            self.items.append({
                "type": "module",
                "name": file_path.stem,
                "file": str(file_path),
                "line": 1,
                "language": "python",
            })
            
            # Walk AST to find classes, functions, variables
            # Use a visitor to track parent nodes for proper variable detection
            class VariableVisitor(ast.NodeVisitor):
                def __init__(self, scanner_instance, file_path):
                    self.scanner = scanner_instance
                    self.file_path = file_path
                    self.current_parent = None
                
                def visit_ClassDef(self, node):
                    self.scanner.items.append({
                        "type": "class",
                        "name": node.name,
                        "file": str(self.file_path),
                        "line": node.lineno,
                        "language": "python",
                    })
                    old_parent = self.current_parent
                    self.current_parent = node
                    self.generic_visit(node)
                    self.current_parent = old_parent
                
                def visit_FunctionDef(self, node):
                    is_private = node.name.startswith("_")
                    self.scanner.items.append({
                        "type": "function",
                        "name": node.name,
                        "file": str(self.file_path),
                        "line": node.lineno,
                        "language": "python",
                        "private": is_private,
                    })
                    old_parent = self.current_parent
                    self.current_parent = node
                    self.generic_visit(node)
                    self.current_parent = old_parent
                
                def visit_Assign(self, node):
                    # Check if this is a module-level assignment (not inside function/class)
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if self.current_parent is None:
                                # Module-level variable
                                if self._is_constant_name(target.id):
                                    self.scanner.items.append({
                                        "type": "constant",
                                        "name": target.id,
                                        "file": str(self.file_path),
                                        "line": node.lineno,
                                        "language": "python",
                                    })
                                else:
                                    self.scanner.items.append({
                                        "type": "variable",
                                        "name": target.id,
                                        "file": str(self.file_path),
                                        "line": node.lineno,
                                        "language": "python",
                                    })
                    self.generic_visit(node)
                
                def _is_constant_name(self, name: str) -> bool:
                    """Check if name looks like a constant (UPPER_SNAKE_CASE)."""
                    return name.isupper() and ("_" in name or name.isalpha())
            
            visitor = VariableVisitor(self, file_path)
            visitor.visit(tree)
        
        except SyntaxError as e:
            # Skip files with syntax errors
            logger.debug(f"Syntax error in {file_path}: {e}")
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            # Log error but continue
            logger.warning(f"Error scanning {file_path}: {e}")
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error scanning {file_path}: {e}", exc_info=True)

    def _scan_javascript(self, file_path: Path):
        """Scan JavaScript file using heuristics."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract filename
            self.items.append({
                "type": "file",
                "name": file_path.stem,
                "file": str(file_path),
                "line": 1,
                "language": "javascript",
            })
            
            # Extract class declarations
            class_pattern = r'class\s+(\w+)\s*'
            for match in re.finditer(class_pattern, content):
                self.items.append({
                    "type": "class",
                    "name": match.group(1),
                    "file": str(file_path),
                    "line": content[:match.start()].count("\n") + 1,
                    "language": "javascript",
                })
            
            # Extract function declarations (both function and arrow functions)
            func_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=|let\s+(\w+)\s*=|var\s+(\w+)\s*=)\s*[=(]'
            for match in re.finditer(func_pattern, content):
                name = match.group(1) or match.group(2) or match.group(3) or match.group(4)
                if name:
                    self.items.append({
                        "type": "function",
                        "name": name,
                        "file": str(file_path),
                        "line": content[:match.start()].count("\n") + 1,
                        "language": "javascript",
                    })
            
            # Extract constants (UPPER_SNAKE_CASE)
            const_pattern = r'const\s+([A-Z][A-Z_]+)\s*='
            for match in re.finditer(const_pattern, content):
                self.items.append({
                    "type": "constant",
                    "name": match.group(1),
                    "file": str(file_path),
                    "line": content[:match.start()].count("\n") + 1,
                    "language": "javascript",
                })
        
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logger.warning(f"Error scanning {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scanning {file_path}: {e}", exc_info=True)

    def _scan_yaml(self, file_path: Path):
        """Scan YAML file."""
        self.items.append({
            "type": "file",
            "name": file_path.name,
            "file": str(file_path),
            "line": 1,
            "language": "yaml",
        })

    def _scan_markdown(self, file_path: Path):
        """Scan Markdown file."""
        self.items.append({
            "type": "file",
            "name": file_path.name,
            "file": str(file_path),
            "line": 1,
            "language": "markdown",
        })

    def _is_constant_name(self, name: str) -> bool:
        """Check if name looks like a constant (UPPER_SNAKE_CASE)."""
        return name.isupper() and ("_" in name or name.isalpha())

    def _compute_statistics(self) -> Dict:
        """Compute scan statistics."""
        by_type = {}
        by_language = {}
        
        for item in self.items:
            item_type = item["type"]
            language = item["language"]
            
            by_type[item_type] = by_type.get(item_type, 0) + 1
            by_language[language] = by_language.get(language, 0) + 1
        
        return {
            "total_items": len(self.items),
            "by_type": by_type,
            "by_language": by_language,
            "languages": list(self.languages),
        }

