"""Doctor command - check prerequisites and environment."""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from kiku_dist.config import Config, find_config_file
from kiku_dist.targets.base import Issue, IssueLevel


@dataclass
class DoctorResult:
    """Result of doctor checks."""
    
    issues: list[Issue] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0


def check_tool(name: str, command: str | None = None) -> Issue | None:
    """Check if a CLI tool is available."""
    cmd = command or name
    if shutil.which(cmd) is None:
        return Issue(
            level=IssueLevel.ERROR,
            message=f"Tool '{name}' not found in PATH",
            fix_hint=f"Install {name} and ensure it's in your PATH",
        )
    return None


def check_secret(name: str, env_name: str | None = None) -> Issue | None:
    """Check if an environment variable / secret is set."""
    var_name = env_name or name
    if not os.environ.get(var_name):
        return Issue(
            level=IssueLevel.ERROR,
            message=f"Secret '{var_name}' not found",
            fix_hint=f"Set {var_name} environment variable",
            ci_hints={
                "gha": f"Settings > Secrets > Actions > New: {var_name}",
                "gitlab": f"Settings > CI/CD > Variables > Add: {var_name}",
                "drone": f"drone secret add --name {var_name} --data <value>",
                "jenkins": f"Credentials > Add > Secret text: {var_name}",
            },
        )
    return None


def verify_github_token() -> Issue | None:
    """Verify GitHub token has required scopes via API."""
    import subprocess
    
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        return None  # Already checked by check_secret
    
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return Issue(
                level=IssueLevel.ERROR,
                message="GitHub token invalid or expired",
                fix_hint="Run: gh auth login",
            )
        
        # Check scopes via API
        import httpx
        resp = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code == 401:
            return Issue(
                level=IssueLevel.ERROR,
                message="GitHub token unauthorized",
                fix_hint="Token is invalid or expired. Generate a new one.",
            )
        
        scopes = resp.headers.get("x-oauth-scopes", "")
        required = {"repo", "write:packages"}
        missing = required - set(s.strip() for s in scopes.split(","))
        if missing:
            return Issue(
                level=IssueLevel.WARNING,
                message=f"GitHub token missing scopes: {', '.join(missing)}",
                fix_hint="Create token with repo and write:packages scopes",
            )
    except Exception as e:
        return Issue(
            level=IssueLevel.WARNING,
            message=f"Could not verify GitHub token: {e}",
            fix_hint="Manual check: gh auth status",
        )
    
    return None


def verify_docker_login() -> Issue | None:
    """Verify Docker registries are accessible."""
    import subprocess
    
    # Check Docker daemon
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return Issue(
                level=IssueLevel.ERROR,
                message="Docker daemon not running",
                fix_hint="Start Docker Desktop or docker service",
            )
    except Exception:
        return Issue(
            level=IssueLevel.ERROR,
            message="Docker not available",
            fix_hint="Install Docker: https://docs.docker.com/get-docker/",
        )
    
    # Check buildx
    try:
        result = subprocess.run(
            ["docker", "buildx", "version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return Issue(
                level=IssueLevel.WARNING,
                message="Docker buildx not available",
                fix_hint="Install buildx: docker buildx install",
            )
    except Exception:
        pass
    
    return None


def check_openapi(config: Config) -> Issue | None:
    """Check if OpenAPI spec exists and is valid."""
    openapi_path = Path(config.docs.openapi_path)
    if not openapi_path.exists():
        return Issue(
            level=IssueLevel.WARNING,
            message=f"OpenAPI spec not found: {openapi_path}",
            fix_hint="Create openapi.yaml or update docs.openapi_path in config",
        )
    
    # Basic validation - check it's valid YAML/JSON
    try:
        import yaml
        with open(openapi_path) as f:
            spec = yaml.safe_load(f)
        if not isinstance(spec, dict) or "openapi" not in spec:
            return Issue(
                level=IssueLevel.ERROR,
                message=f"Invalid OpenAPI spec: missing 'openapi' field",
                fix_hint="Ensure the file is a valid OpenAPI 3.x specification",
            )
    except Exception as e:
        return Issue(
            level=IssueLevel.ERROR,
            message=f"Failed to parse OpenAPI spec: {e}",
            fix_hint="Fix YAML/JSON syntax errors in the file",
        )
    
    return None


def run_doctor(config: Config | None = None, targets: list[str] | None = None) -> DoctorResult:
    """Run all doctor checks.
    
    Args:
        config: Parsed config, or None to also check for config file
        targets: Specific targets to check, or None for all
        
    Returns:
        DoctorResult with all issues found
    """
    result = DoctorResult()
    
    # Check config file exists
    if config is None:
        config_path = find_config_file()
        if config_path is None:
            result.issues.append(Issue(
                level=IssueLevel.ERROR,
                message="kiku-dist.toml not found",
                fix_hint="Run 'kiku-dist init' to create configuration",
            ))
            result.failed += 1
            return result
    
    # Core tools
    core_tools = [
        ("git", None),
        ("docker", None),
        ("node", None),
        ("npx", None),
    ]
    
    for tool_name, cmd in core_tools:
        issue = check_tool(tool_name, cmd)
        if issue:
            result.issues.append(issue)
            result.failed += 1
        else:
            result.passed += 1
    
    # Secrets based on targets
    all_targets = targets or ["gh", "ghcr", "dockerhub", "docs"]
    
    secret_map = {
        "gh": [("GH_TOKEN", "GITHUB_TOKEN")],
        "ghcr": [("GHCR_TOKEN", "GITHUB_TOKEN")],
        "dockerhub": [("DOCKERHUB_USERNAME", None), ("DOCKERHUB_TOKEN", None)],
        "docs": [],  # Usually uses GH_TOKEN
    }
    
    checked_secrets: set[str] = set()
    for target in all_targets:
        for secret_name, alt_name in secret_map.get(target, []):
            if secret_name in checked_secrets:
                continue
            checked_secrets.add(secret_name)
            
            # Check primary or alternative
            if os.environ.get(secret_name) or (alt_name and os.environ.get(alt_name)):
                result.passed += 1
            else:
                issue = check_secret(secret_name)
                if issue:
                    result.issues.append(issue)
                    result.failed += 1
    
    # OpenAPI spec
    if config:
        issue = check_openapi(config)
        if issue:
            result.issues.append(issue)
            if issue.level == IssueLevel.ERROR:
                result.failed += 1
            else:
                result.warnings += 1
        else:
            result.passed += 1
    
    return result


def print_doctor_report(result: DoctorResult, console: Console) -> None:
    """Print formatted doctor report."""
    console.print()
    console.print("[bold]KikuAI Distributor - Doctor Report[/bold]")
    console.print()
    
    # Summary
    if result.failed == 0 and result.warnings == 0:
        console.print("[green]✓ All checks passed![/green]")
    else:
        console.print(
            f"[green]✓ {result.passed} passed[/green]  "
            f"[yellow]⚠ {result.warnings} warnings[/yellow]  "
            f"[red]✗ {result.failed} failed[/red]"
        )
    
    if not result.issues:
        return
    
    console.print()
    
    # Issues table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Level", width=8)
    table.add_column("Issue")
    table.add_column("Fix")
    
    for issue in result.issues:
        level_style = {
            IssueLevel.ERROR: "[red]ERROR[/red]",
            IssueLevel.WARNING: "[yellow]WARN[/yellow]",
            IssueLevel.INFO: "[blue]INFO[/blue]",
        }[issue.level]
        
        fix = issue.fix_hint or ""
        if issue.ci_hints:
            fix += "\n" + "\n".join(
                f"  {ci}: {hint}" for ci, hint in issue.ci_hints.items()
            )
        
        table.add_row(level_style, issue.message, fix)
    
    console.print(table)
