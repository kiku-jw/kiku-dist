"""Tests for CLI module."""

from typer.testing import CliRunner

from kiku_dist import __version__
from kiku_dist.cli import app

runner = CliRunner()


def test_version():
    """Test --version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help():
    """Test --help flag."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "kiku-dist" in result.stdout


def test_init_already_exists(tmp_path, monkeypatch):
    """Test init when config already exists."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / "kiku-dist.toml"
    config_file.write_text("name = 'test'")

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 1
    assert "already exists" in result.stdout


def test_init_with_force(tmp_path, monkeypatch):
    """Test init with --force flag."""
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / "kiku-dist.toml"
    config_file.write_text("name = 'old'")

    result = runner.invoke(app, ["init", "--force"])
    assert result.exit_code == 0
    assert "Created" in result.stdout


def test_doctor_no_config(tmp_path, monkeypatch):
    """Test doctor without config file."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0  # Doctor runs even without config
