"""Target registry - all available publish targets."""


from kiku_dist.targets.base import Target
from kiku_dist.targets.container import ContainerTarget
from kiku_dist.targets.docs import DocsTarget
from kiku_dist.targets.gh_release import GitHubReleaseTarget
from kiku_dist.targets.pr_dirs import PRDirsTarget
from kiku_dist.targets.rapidapi import RapidAPITarget

# Registry of all available targets
_registry: dict[str, Target] = {}


def register(target: Target) -> None:
    """Register a target in the global registry."""
    _registry[target.name] = target
    # Also register aliases
    for alias in getattr(target, "aliases", []):
        _registry[alias] = target


def get(name: str) -> Target | None:
    """Get a target by name or alias."""
    return _registry.get(name)


def all_targets() -> list[Target]:
    """Get all registered targets (no duplicates)."""
    seen = set()
    result = []
    for target in _registry.values():
        if id(target) not in seen:
            seen.add(id(target))
            result.append(target)
    return result


# Register built-in targets
register(GitHubReleaseTarget())
register(ContainerTarget())
register(DocsTarget())
register(PRDirsTarget())
register(RapidAPITarget())

