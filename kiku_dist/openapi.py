"""OpenAPI validation utilities - Python-based, no Node dependency."""

from pathlib import Path
from typing import Any

import yaml


def load_openapi(path: Path) -> dict[str, Any] | None:
    """Load OpenAPI spec from file."""
    if not path.exists():
        return None

    try:
        with open(path) as f:
            if path.suffix in (".yaml", ".yml"):
                return yaml.safe_load(f)
            else:
                import json
                return json.load(f)
    except Exception:
        return None


def validate_openapi(spec: dict[str, Any]) -> list[str]:
    """Validate OpenAPI spec structure. Returns list of errors."""
    errors = []

    # Check required fields
    if "openapi" not in spec:
        errors.append("Missing 'openapi' version field")
    elif not spec["openapi"].startswith("3."):
        errors.append(f"Unsupported OpenAPI version: {spec['openapi']}. Use 3.x")

    if "info" not in spec:
        errors.append("Missing 'info' section")
    else:
        info = spec["info"]
        if "title" not in info:
            errors.append("Missing info.title")
        if "version" not in info:
            errors.append("Missing info.version")

    if "paths" not in spec:
        errors.append("Missing 'paths' section")
    elif not spec["paths"]:
        errors.append("'paths' section is empty")

    return errors


def extract_api_info(spec: dict[str, Any]) -> dict[str, Any]:
    """Extract key information from OpenAPI spec."""
    info = spec.get("info", {})
    paths = spec.get("paths", {})

    # Count endpoints
    endpoint_count = 0
    methods = set()
    for path, operations in paths.items():
        for method in operations:
            if method in ("get", "post", "put", "patch", "delete", "options", "head"):
                endpoint_count += 1
                methods.add(method.upper())

    # Extract tags
    tags = set()
    for path, operations in paths.items():
        for method, details in operations.items():
            if isinstance(details, dict):
                for tag in details.get("tags", []):
                    tags.add(tag)

    return {
        "title": info.get("title", "Unknown API"),
        "version": info.get("version", "0.0.0"),
        "description": info.get("description", ""),
        "endpoint_count": endpoint_count,
        "methods": sorted(methods),
        "tags": sorted(tags),
        "servers": [s.get("url", "") for s in spec.get("servers", [])],
    }


def generate_rapidapi_metadata(spec: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Generate RapidAPI-compatible metadata from OpenAPI spec."""
    api_info = extract_api_info(spec)
    prepare_config = config.get("prepare", {}).get("rapidapi", {})

    return {
        "name": api_info["title"],
        "description": api_info["description"],
        "version": api_info["version"],
        "category": prepare_config.get("category", "Other"),
        "tags": prepare_config.get("tags", api_info["tags"][:5]),
        "pricing": prepare_config.get("pricing_model", "freemium"),
        "endpoints": api_info["endpoint_count"],
    }
