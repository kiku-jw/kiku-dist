"""Tests for OpenAPI validation module."""

from pathlib import Path
import tempfile

import pytest

from kiku_dist.openapi import load_openapi, validate_openapi, extract_api_info


def test_validate_openapi_valid():
    """Test validation of valid OpenAPI spec."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {"/test": {"get": {"summary": "Test endpoint"}}},
    }
    errors = validate_openapi(spec)
    assert errors == []


def test_validate_openapi_missing_fields():
    """Test validation catches missing fields."""
    spec = {"paths": {}}
    errors = validate_openapi(spec)
    assert "Missing 'openapi' version field" in errors
    assert "Missing 'info' section" in errors


def test_validate_openapi_empty_paths():
    """Test validation catches empty paths."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0"},
        "paths": {},
    }
    errors = validate_openapi(spec)
    assert "'paths' section is empty" in errors


def test_extract_api_info():
    """Test extraction of API info."""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "My API",
            "version": "2.0.0",
            "description": "A test API",
        },
        "paths": {
            "/users": {
                "get": {"tags": ["users"], "summary": "List users"},
                "post": {"tags": ["users"], "summary": "Create user"},
            },
            "/health": {
                "get": {"summary": "Health check"},
            },
        },
        "servers": [{"url": "https://api.example.com"}],
    }
    
    info = extract_api_info(spec)
    assert info["title"] == "My API"
    assert info["version"] == "2.0.0"
    assert info["endpoint_count"] == 3
    assert "GET" in info["methods"]
    assert "POST" in info["methods"]
    assert "users" in info["tags"]


def test_load_openapi_yaml():
    """Test loading YAML OpenAPI spec."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "openapi.yaml"
        spec_path.write_text("""
openapi: "3.0.0"
info:
  title: Test
  version: "1.0"
paths:
  /test:
    get:
      summary: Test
""")
        spec = load_openapi(spec_path)
        assert spec is not None
        assert spec["openapi"] == "3.0.0"


def test_load_openapi_not_found():
    """Test loading non-existent file."""
    spec = load_openapi(Path("/nonexistent/file.yaml"))
    assert spec is None
