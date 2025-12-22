"""PR to directories target - automated PRs to awesome-lists."""

from pathlib import Path
from typing import Any

from kiku_dist.targets.base import Issue, IssueLevel, Step, Target, TargetResult


class PRDirsTarget(Target):
    """Create PRs to awesome-lists and public API directories."""

    name = "pr-dirs"
    aliases = ["pr", "awesome"]
    description = "Create PRs to directories and awesome-lists"
    required_secrets = ["GH_TOKEN"]
    required_tools = ["gh", "git"]
    supports_dry_run = True

    def doctor(self, config: dict[str, Any]) -> list[Issue]:
        """Check prerequisites for PR creation."""
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

        # Check git
        if not shutil.which("git"):
            issues.append(Issue(
                level=IssueLevel.ERROR,
                message="git not found",
                fix_hint="Install git",
            ))

        # Check token
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            issues.append(Issue(
                level=IssueLevel.ERROR,
                message="GH_TOKEN not set",
                fix_hint="Set GH_TOKEN with repo scope",
                ci_hints=self.get_secret_hints("GH_TOKEN"),
            ))

        # Check pr_dirs config
        pr_config = config.get("pr_dirs", {})
        targets = pr_config.get("targets", [])
        if not targets:
            issues.append(Issue(
                level=IssueLevel.WARNING,
                message="No PR targets configured",
                fix_hint="Add [[pr_dirs.targets]] sections to kiku-dist.toml",
            ))

        return issues

    def plan(self, config: dict[str, Any]) -> list[Step]:
        """Generate PR creation steps."""
        pr_config = config.get("pr_dirs", {})
        targets = pr_config.get("targets", [])
        name = config.get("name", "unknown")
        version = config.get("version", "0.0.0")

        steps = []

        for target in targets:
            repo = target.get("repo", "unknown/repo")
            steps.append(Step(
                name=f"Fork and clone {repo}",
                description="Create fork and clone locally",
                command=f"gh repo fork {repo} --clone",
            ))
            steps.append(Step(
                name=f"Add {name} to {repo}",
                description="Add entry based on template",
                command=None,  # Template rendering
            ))
            steps.append(Step(
                name=f"Create PR to {repo}",
                description=f"Submit PR adding {name} v{version}",
                command=f"gh pr create --repo {repo} --title 'Add {name}'",
                dry_run_safe=False,
            ))

        if not targets:
            steps.append(Step(
                name="No targets configured",
                description="Add [[pr_dirs.targets]] to kiku-dist.toml",
                command=None,
            ))

        return steps

    def execute(self, config: dict[str, Any], dry_run: bool = False) -> TargetResult:
        """Create PRs to configured directories."""
        import subprocess
        import tempfile

        pr_config = config.get("pr_dirs", {})
        targets = pr_config.get("targets", [])
        name = config.get("name", "unknown")
        version = config.get("version", "0.0.0")
        description = config.get("description", "")
        ci_repo = config.get("ci", {}).get("repo", "")

        if not targets:
            return TargetResult(
                success=True,
                message="No PR targets configured",
            )

        created_prs = []
        failed = []

        for target in targets:
            repo = target.get("repo", "")
            category = target.get("category", "")
            template_path = target.get("template", "")

            if not repo:
                continue

            if dry_run:
                created_prs.append(f"Would create PR to {repo}")
                continue

            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    work_dir = Path(tmpdir)

                    # Fork and clone
                    result = subprocess.run(
                        ["gh", "repo", "fork", repo, "--clone", "--remote"],
                        cwd=work_dir,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        failed.append(f"{repo}: fork failed")
                        continue

                    repo_dir = work_dir / repo.split("/")[-1]
                    branch = f"add-{name.lower().replace(' ', '-')}"

                    # Create branch
                    subprocess.run(
                        ["git", "checkout", "-b", branch],
                        cwd=repo_dir,
                        capture_output=True,
                    )

                    # Generate entry content
                    if template_path and Path(template_path).exists():
                        from jinja2 import Template
                        template = Template(Path(template_path).read_text())
                        entry = template.render(
                            name=name,
                            version=version,
                            description=description,
                            repo=ci_repo,
                            category=category,
                        )
                    else:
                        # Default markdown entry
                        url = f"https://github.com/{ci_repo}" if ci_repo else ""
                        entry = f"| [{name}]({url}) | {description} |"

                    # Append to README (simplified - real impl would parse structure)
                    readme = repo_dir / "README.md"
                    if readme.exists():
                        content = readme.read_text()
                        # Find category or append at end
                        if category and f"## {category}" in content:
                            idx = content.find(f"## {category}")
                            next_section = content.find("\n## ", idx + 1)
                            if next_section == -1:
                                next_section = len(content)
                            # Insert before next section
                            insert = f"\n{entry}\n"
                            content = content[:next_section] + insert + content[next_section:]
                        else:
                            content += f"\n{entry}\n"
                        readme.write_text(content)

                    # Commit
                    subprocess.run(
                        ["git", "add", "."],
                        cwd=repo_dir,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-m", f"Add {name}"],
                        cwd=repo_dir,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "push", "-u", "origin", branch],
                        cwd=repo_dir,
                        capture_output=True,
                    )

                    # Create PR
                    pr_body = (
                        f"Adding {name} to the list.\n\n"
                        f"{description}\n\n---\nAutomated by kiku-dist"
                    )
                    result = subprocess.run(
                        [
                            "gh", "pr", "create",
                            "--repo", repo,
                            "--title", f"Add {name}",
                            "--body", pr_body,
                        ],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        created_prs.append(result.stdout.strip())
                    else:
                        failed.append(f"{repo}: {result.stderr}")

            except Exception as e:
                failed.append(f"{repo}: {e}")

        if failed:
            return TargetResult(
                success=False,
                message=f"Created {len(created_prs)} PRs, {len(failed)} failed",
                artifacts=created_prs,
                metadata={"failed": failed},
            )

        return TargetResult(
            success=True,
            message=f"Created {len(created_prs)} PRs",
            artifacts=created_prs,
        )
