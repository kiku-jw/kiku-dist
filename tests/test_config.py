"""Tests for config module."""

import tempfile
from pathlib import Path

import pytest

from kiku_dist.config import get_config_template, load_config


def test_get_config_template():
    """Test that config template is valid TOML."""
    template = get_config_template()
    assert "name = " in template
    assert "[ci]" in template
    assert "[container]" in template


def test_load_config_file_not_found():
    """Test error when config file not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            load_config(Path(tmpdir) / "nonexistent.toml")


def test_load_config_valid():
    """Test loading valid config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "kiku-dist.toml"
        config_path.write_text('''
name = "test-api"
version = "1.0.0"

[ci]
primary = "gha"
repo = "test/repo"
''')

        config = load_config(config_path)
        assert config.name == "test-api"
        assert config.version == "1.0.0"
        assert config.ci.primary == "gha"
        assert config.ci.repo == "test/repo"


def test_config_defaults():
    """Test config has sensible defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "kiku-dist.toml"
        config_path.write_text('name = "minimal"')

        config = load_config(config_path)
        assert config.name == "minimal"
        assert config.version == "0.0.0"
        assert config.container.registry == ["ghcr", "dockerhub"]
        assert config.docs.provider == "mkdocs"
