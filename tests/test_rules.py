"""Tests for rule engine."""

import pytest

from nomenclator.rules import RuleEngine


@pytest.fixture
def rule_engine():
    """Create a rule engine instance."""
    return RuleEngine(rules_path="rules.yaml")


def test_detect_case_snake_case(rule_engine):
    """Test detection of snake_case."""
    assert rule_engine._detect_case("user_name") == "snake_case"
    assert rule_engine._detect_case("process_data") == "snake_case"


def test_detect_case_pascal_case(rule_engine):
    """Test detection of PascalCase."""
    assert rule_engine._detect_case("UserManager") == "PascalCase"
    assert rule_engine._detect_case("DataProcessor") == "PascalCase"


def test_detect_case_camel_case(rule_engine):
    """Test detection of camelCase."""
    assert rule_engine._detect_case("userName") == "camelCase"
    assert rule_engine._detect_case("processData") == "camelCase"


def test_detect_case_upper_snake_case(rule_engine):
    """Test detection of UPPER_SNAKE_CASE."""
    assert rule_engine._detect_case("MAX_USERS") == "UPPER_SNAKE_CASE"
    assert rule_engine._detect_case("MIN_TEMP") == "UPPER_SNAKE_CASE"


def test_to_snake_case(rule_engine):
    """Test conversion to snake_case."""
    assert rule_engine._to_snake_case("UserName") == "user_name"
    assert rule_engine._to_snake_case("processData") == "process_data"
    assert rule_engine._to_snake_case("user-name") == "user_name"


def test_to_pascal_case(rule_engine):
    """Test conversion to PascalCase."""
    assert rule_engine._to_pascal_case("user_name") == "UserName"
    assert rule_engine._to_pascal_case("user-name") == "UserName"
    assert rule_engine._to_pascal_case("userName") == "Username"


def test_to_camel_case(rule_engine):
    """Test conversion to camelCase."""
    assert rule_engine._to_camel_case("user_name") == "userName"
    assert rule_engine._to_camel_case("User_Name") == "userName"


def test_check_python_function(rule_engine):
    """Test checking Python function naming."""
    item = {
        "type": "function",
        "name": "ProcessData",  # Violation: should be snake_case
        "language": "python",
        "file": "test.py",
        "line": 1,
    }
    
    result = rule_engine.check_item(item)
    assert not result["compliant"]
    assert len(result["violations"]) > 0
    assert "snake_case" in result["suggestions"][0] or "process_data" in result["suggestions"][0]


def test_check_python_class(rule_engine):
    """Test checking Python class naming."""
    item = {
        "type": "class",
        "name": "user_manager",  # Violation: should be PascalCase
        "language": "python",
        "file": "test.py",
        "line": 1,
    }
    
    result = rule_engine.check_item(item)
    assert not result["compliant"]
    assert len(result["violations"]) > 0


def test_check_python_compliant(rule_engine):
    """Test checking compliant Python names."""
    item = {
        "type": "function",
        "name": "process_data",  # Correct
        "language": "python",
        "file": "test.py",
        "line": 1,
    }
    
    result = rule_engine.check_item(item)
    assert result["compliant"]


def test_private_function_requires_prefix(rule_engine):
    """Private functions should enforce the configured prefix."""
    item = {
        "type": "function",
        "name": "internal_helper",
        "language": "python",
        "file": "test.py",
        "line": 1,
        "private": True,
    }
    
    result = rule_engine.check_item(item)
    assert not result["compliant"]
    assert any(v["type"] == "missing_prefix" for v in result["violations"])
    assert result["suggestions"][0].startswith("_")


def test_private_function_with_prefix_is_compliant(rule_engine):
    """Private functions that already use the prefix should pass."""
    item = {
        "type": "function",
        "name": "_internal_helper",
        "language": "python",
        "file": "test.py",
        "line": 1,
        "private": True,
    }
    
    result = rule_engine.check_item(item)
    assert result["compliant"]

