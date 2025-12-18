"""Tests for targets registry."""

from kiku_dist.targets import registry


def test_get_gh_target():
    """Test getting GitHub release target."""
    target = registry.get("gh")
    assert target is not None
    assert target.name == "gh"


def test_get_by_alias():
    """Test getting target by alias."""
    target = registry.get("github")
    assert target is not None
    assert target.name == "gh"


def test_get_container_target():
    """Test getting container target."""
    target = registry.get("container")
    assert target is not None
    assert "docker" in target.aliases


def test_get_docs_target():
    """Test getting docs target."""
    target = registry.get("docs")
    assert target is not None


def test_get_pr_dirs_target():
    """Test getting pr-dirs target."""
    target = registry.get("pr-dirs")
    assert target is not None


def test_get_unknown_returns_none():
    """Test getting unknown target returns None."""
    target = registry.get("nonexistent-target")
    assert target is None


def test_all_targets():
    """Test getting all registered targets."""
    targets = registry.all_targets()
    assert len(targets) >= 4  # gh, container, docs, pr-dirs
    names = [t.name for t in targets]
    assert "gh" in names
    assert "container" in names
    assert "docs" in names
    assert "pr-dirs" in names
