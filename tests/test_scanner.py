"""Tests for scanner."""

import tempfile
from pathlib import Path

import pytest

from nomenclator.core import Scanner


@pytest.fixture
def scanner():
    """Create a scanner instance."""
    return Scanner()


def test_scan_python_file(scanner):
    """Test scanning a Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
class UserManager:
    def process_data(self):
        MAX_USERS = 100
        return MAX_USERS
""")
        temp_path = f.name

    try:
        result = scanner.scan(temp_path)

        assert "items" in result
        assert len(result["items"]) > 0

        # Check that we found the class
        class_items = [item for item in result["items"] if item["type"] == "class"]
        assert len(class_items) > 0
        assert any(item["name"] == "UserManager" for item in class_items)

        # Check that we found functions
        func_items = [item for item in result["items"] if item["type"] == "function"]
        assert len(func_items) > 0

    finally:
        Path(temp_path).unlink()


def test_scan_javascript_file(scanner):
    """Test scanning a JavaScript file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write("""
class UserService {
    processData() {
        const MAX_ITEMS = 100;
        return MAX_ITEMS;
    }
}
""")
        temp_path = f.name

    try:
        result = scanner.scan(temp_path)

        assert "items" in result
        assert len(result["items"]) > 0

        # Check that we found the class
        class_items = [item for item in result["items"] if item["type"] == "class"]
        assert len(class_items) > 0

    finally:
        Path(temp_path).unlink()


def test_scan_directory(scanner):
    """Test scanning a directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a Python file
        py_file = temp_path / "test.py"
        py_file.write_text("class TestClass:\n    pass\n")

        # Create a JS file
        js_file = temp_path / "test.js"
        js_file.write_text("class TestService {\n}\n")

        result = scanner.scan(str(temp_path))

        assert "items" in result
        assert len(result["items"]) > 0

        # Should have found items from both files
        assert "python" in result["statistics"]["by_language"]
        assert "javascript" in result["statistics"]["by_language"]


def test_scan_nonexistent_path(scanner):
    """Test scanning a nonexistent path."""
    with pytest.raises(ValueError):
        scanner.scan("/nonexistent/path/12345")
