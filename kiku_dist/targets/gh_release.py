"""GitHub Release target."""

from typing import Any

from kiku_dist.targets.base import Issue, IssueLevel, Step, Target, TargetResult


class GitHubReleaseTarget(Target):
    """Publish to GitHub Releases."""
    
    name = "gh"
    aliases = ["gh-release", "github"]
    description = "Create GitHub Release with changelog and assets"
    required_secrets = ["GH_TOKEN"]
    required_tools = ["gh"]
    supports_dry_run = True
    
    def doctor(self, config: dict[str, Any]) -> list[Issue]:
        """Check GitHub CLI and token."""
        issues = []
        
        import os
        import shutil
        
        # Check gh CLI
        if not shutil.which("gh"):
            issues.append(Issue(
                level=IssueLevel.ERROR,
                message="GitHub CLI (gh) not found",
                fix_hint="Install: brew install gh (macOS) or see https://cli.github.com",
            ))
        
        # Check token
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            issues.append(Issue(
                level=IssueLevel.ERROR,
                message="GH_TOKEN or GITHUB_TOKEN not set",
                fix_hint="Set GH_TOKEN environment variable",
                ci_hints=self.get_secret_hints("GH_TOKEN"),
            ))
        
        return issues
    
    def plan(self, config: dict[str, Any]) -> list[Step]:
        """Generate release steps."""
        version = config.get("version", "0.0.0")
        name = config.get("name", "unknown")
        gh_config = config.get("gh_release", {})
        
        steps = [
            Step(
                name="Generate changelog",
                description="Create release notes from commits",
                command="git log --oneline $(git describe --tags --abbrev=0)..HEAD",
            ),
            Step(
                name="Create GitHub Release",
                description=f"Create release v{version}",
                command=f"gh release create v{version} --title '{name} v{version}' --generate-notes",
            ),
        ]
        
        if gh_config.get("draft", False):
            steps[-1].command += " --draft"
        
        if gh_config.get("prerelease", False):
            steps[-1].command += " --prerelease"
        
        return steps
    
    def execute(self, config: dict[str, Any], dry_run: bool = False) -> TargetResult:
        """Create GitHub Release."""
        import subprocess
        
        version = config.get("version", "0.0.0")
        name = config.get("name", "unknown")
        gh_config = config.get("gh_release", {})
        
        tag = f"v{version}"
        
        cmd = [
            "gh", "release", "create", tag,
            "--title", f"{name} {tag}",
        ]
        
        if gh_config.get("generate_notes", True):
            cmd.append("--generate-notes")
        
        if gh_config.get("draft", False):
            cmd.append("--draft")
        
        if gh_config.get("prerelease", False):
            cmd.append("--prerelease")
        
        if dry_run:
            return TargetResult(
                success=True,
                message=f"Would create release {tag}",
                metadata={"command": " ".join(cmd)},
            )
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return TargetResult(
                    success=False,
                    message=f"Failed to create release: {result.stderr}",
                )
            
            return TargetResult(
                success=True,
                message=f"Created release {tag}",
                artifacts=[result.stdout.strip()],  # URL to release
            )
        except Exception as e:
            return TargetResult(
                success=False,
                message=f"Error: {e}",
            )
