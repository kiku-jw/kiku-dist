"""Tests for doctor module."""

from unittest.mock import patch

from kiku_dist.doctor import DoctorResult, check_secret, check_tool


def test_check_tool_found():
    """Test check_tool when tool exists."""
    with patch("shutil.which", return_value="/usr/bin/git"):
        issue = check_tool("git")
        assert issue is None


def test_check_tool_not_found():
    """Test check_tool when tool is missing."""
    with patch("shutil.which", return_value=None):
        issue = check_tool("nonexistent-tool")
        assert issue is not None
        assert "not found" in issue.message


def test_check_secret_found():
    """Test check_secret when env var exists."""
    with patch.dict("os.environ", {"TEST_SECRET": "value"}):
        issue = check_secret("TEST_SECRET")
        assert issue is None


def test_check_secret_not_found():
    """Test check_secret when env var is missing."""
    with patch.dict("os.environ", {}, clear=True):
        issue = check_secret("MISSING_SECRET")
        assert issue is not None
        assert "not found" in issue.message


def test_doctor_result_defaults():
    """Test DoctorResult default values."""
    result = DoctorResult()
    assert result.issues == []
    assert result.passed == 0
    assert result.failed == 0
    assert result.warnings == 0
