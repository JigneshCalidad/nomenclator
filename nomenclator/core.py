"""Core scanning functionality for nomenclator."""

import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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

    def _scan_directory(self, directory: Path, ignore_patterns: Optional[Set[str]] = None) -> None:
        """Recursively scan directory for code files.
        
        Args:
            directory: Path to directory to scan
            ignore_patterns: Set of directory names to ignore during scanning
        """
        if ignore_patterns is None:
            ignore_patterns = {
                "__pycache__", ".git", ".venv", "venv", "node_modules",
                ".pytest_cache", ".mypy_cache", "dist", "build", ".eggs"
            }
        
        # Use pathlib for consistent path handling
        try:
            for file_path in directory.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip if any parent directory is in ignore list
                if any(part in ignore_patterns for part in file_path.parts):
                    continue
                
                if self._should_scan(file_path):
                    self._scan_file(file_path)
        except (OSError, PermissionError) as e:
            logger.warning(f"Error accessing directory {directory}: {e}")

    def _should_scan(self, file_path: Path) -> bool:
        """Check if file should be scanned based on extension.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file extension is supported, False otherwise
        """
        extensions = {".py", ".js", ".md", ".yaml", ".yml"}
        return file_path.suffix in extensions

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for naming patterns.
        
        Args:
            file_path: Path to file to scan
        """
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

    def _scan_python(self, file_path: Path) -> None:
        """Scan Python file using AST.
        
        Args:
            file_path: Path to Python file to scan
        """
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
            
            # Track context to determine module-level variables
            is_constant_name = self._is_constant_name  # Capture method reference
            
            class ASTContextVisitor(ast.NodeVisitor):
                def __init__(self, file_path, is_constant_name_func):
                    self.context_stack = []
                    self.items = []
                    self.file_path = file_path
                    self.is_constant_name = is_constant_name_func
                
                def visit_ClassDef(self, node):
                    self.context_stack.append("class")
                    self.generic_visit(node)
                    self.context_stack.pop()
                
                def visit_FunctionDef(self, node):
                    is_private = node.name.startswith("_")
                    self.items.append({
                        "type": "function",
                        "name": node.name,
                        "file": str(self.file_path),
                        "line": node.lineno,
                        "language": "python",
                        "private": is_private,
                    })
                    self.context_stack.append("function")
                    self.generic_visit(node)
                    self.context_stack.pop()
                
                def visit_Assign(self, node):
                    # Check if this is a module-level assignment
                    is_module_level = len(self.context_stack) == 0
                    
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if self.is_constant_name(target.id):
                                self.items.append({
                                    "type": "constant",
                                    "name": target.id,
                                    "file": str(self.file_path),
                                    "line": node.lineno,
                                    "language": "python",
                                })
                            elif is_module_level:
                                # Module-level variable (not a constant)
                                self.items.append({
                                    "type": "variable",
                                    "name": target.id,
                                    "file": str(self.file_path),
                                    "line": node.lineno,
                                    "language": "python",
                                })
                    self.generic_visit(node)
            
            visitor = ASTContextVisitor(file_path, is_constant_name)
            
            # Extract classes first
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self.items.append({
                        "type": "class",
                        "name": node.name,
                        "file": str(file_path),
                        "line": node.lineno,
                        "language": "python",
                    })
            
            # Visit tree to extract functions, variables, and constants
            visitor.visit(tree)
            self.items.extend(visitor.items)
        
        except SyntaxError as e:
            # Skip files with syntax errors
            logger.debug(f"Skipping {file_path} due to syntax error: {e}")
        except (OSError, IOError, UnicodeDecodeError) as e:
            # Log error but continue
            logger.warning(f"Error scanning {file_path}: {e}")
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error scanning {file_path}: {e}", exc_info=True)

    def _scan_javascript(self, file_path: Path) -> None:
        """Scan JavaScript file using heuristics.
        
        Args:
            file_path: Path to JavaScript file to scan
        """
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
            # Pattern matches: const followed by uppercase letters and underscores
            const_pattern = r'const\s+([A-Z][A-Z0-9_]*(?:_[A-Z0-9_]+)*)\s*='
            for match in re.finditer(const_pattern, content):
                const_name = match.group(1)
                # Verify it's actually UPPER_SNAKE_CASE (all uppercase)
                if const_name.isupper() and ("_" in const_name or const_name.isalpha()):
                    self.items.append({
                        "type": "constant",
                        "name": const_name,
                        "file": str(file_path),
                        "line": content[:match.start()].count("\n") + 1,
                        "language": "javascript",
                    })
        
        except (OSError, IOError, UnicodeDecodeError) as e:
            logger.warning(f"Error scanning {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scanning {file_path}: {e}", exc_info=True)

    def _scan_yaml(self, file_path: Path) -> None:
        """Scan YAML file.
        
        Args:
            file_path: Path to YAML file to scan
        """
        self.items.append({
            "type": "file",
            "name": file_path.name,
            "file": str(file_path),
            "line": 1,
            "language": "yaml",
        })

    def _scan_markdown(self, file_path: Path) -> None:
        """Scan Markdown file.
        
        Args:
            file_path: Path to Markdown file to scan
        """
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

