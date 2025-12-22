"""Base target interface for all publish destinations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueLevel(str, Enum):
    """Severity level for doctor issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Issue:
    """An issue found during doctor check."""

    level: IssueLevel
    message: str
    fix_hint: str | None = None
    ci_hints: dict[str, str] = field(default_factory=dict)


@dataclass
class Step:
    """A planned execution step."""

    name: str
    description: str
    command: str | None = None
    dry_run_safe: bool = True


@dataclass
class TargetResult:
    """Result of target execution."""

    success: bool
    message: str
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Target(ABC):
    """Base class for all publish targets."""

    name: str
    description: str
    required_secrets: list[str] = []
    required_tools: list[str] = []
    supports_dry_run: bool = True

    @abstractmethod
    def doctor(self, config: dict[str, Any]) -> list[Issue]:
        """Check prerequisites for this target.

        Returns list of issues found (empty = all good).
        """
        ...

    @abstractmethod
    def plan(self, config: dict[str, Any]) -> list[Step]:
        """Generate execution plan for this target.

        Returns list of steps that will be executed.
        """
        ...

    @abstractmethod
    def execute(self, config: dict[str, Any], dry_run: bool = False) -> TargetResult:
        """Execute the target publish.

        Args:
            config: Parsed kiku-dist.toml configuration
            dry_run: If True, simulate without actual publish

        Returns:
            TargetResult with success status and details
        """
        ...

    def get_secret_hints(self, secret_name: str) -> dict[str, str]:
        """Get CI-specific hints for setting up a secret."""
        return {
            "gha": f"Settings > Secrets > Actions > New: {secret_name}",
            "gitlab": f"Settings > CI/CD > Variables > Add: {secret_name}",
            "drone": f"drone secret add --name {secret_name} --data <value>",
            "jenkins": f"Credentials > Add > Secret text: {secret_name}",
        }
