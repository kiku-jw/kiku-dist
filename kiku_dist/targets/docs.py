"""Documentation target for MkDocs and ReDoc."""

from typing import Any

from kiku_dist.targets.base import Issue, IssueLevel, Step, Target, TargetResult


class DocsTarget(Target):
    """Build and deploy documentation with MkDocs and ReDoc."""

    name = "docs"
    aliases = ["mkdocs", "redoc"]
    description = "Build and deploy documentation to GitHub Pages"
    required_secrets = ["GH_TOKEN"]
    required_tools = ["mkdocs"]
    supports_dry_run = True

    def doctor(self, config: dict[str, Any]) -> list[Issue]:
        """Check MkDocs installation and config."""
        issues = []

        import shutil
        from pathlib import Path

        docs_config = config.get("docs", {})
        provider = docs_config.get("provider", "mkdocs")

        if provider == "mkdocs":
            # Check mkdocs CLI
            if not shutil.which("mkdocs"):
                issues.append(Issue(
                    level=IssueLevel.ERROR,
                    message="MkDocs not found",
                    fix_hint="Install: pip install mkdocs-material",
                ))

            # Check mkdocs.yml
            if not Path("mkdocs.yml").exists():
                issues.append(Issue(
                    level=IssueLevel.WARNING,
                    message="mkdocs.yml not found",
                    fix_hint="Create mkdocs.yml or run: mkdocs new .",
                ))

        # Check OpenAPI spec for ReDoc
        openapi_path = docs_config.get("openapi_path", "openapi.yaml")
        if not Path(openapi_path).exists():
            issues.append(Issue(
                level=IssueLevel.WARNING,
                message=f"OpenAPI spec not found: {openapi_path}",
                fix_hint="Create OpenAPI spec or update docs.openapi_path",
            ))

        return issues

    def plan(self, config: dict[str, Any]) -> list[Step]:
        """Generate docs build and deploy steps."""
        docs_config = config.get("docs", {})
        provider = docs_config.get("provider", "mkdocs")
        deploy_to = docs_config.get("deploy_to", "gh-pages")

        steps = []

        if provider == "mkdocs":
            steps.append(Step(
                name="Build MkDocs site",
                description="Generate static documentation",
                command="mkdocs build",
            ))

            if deploy_to == "gh-pages":
                steps.append(Step(
                    name="Deploy to GitHub Pages",
                    description="Push to gh-pages branch",
                    command="mkdocs gh-deploy --force",
                    dry_run_safe=False,
                ))

        # ReDoc for API reference
        openapi_path = docs_config.get("openapi_path", "openapi.yaml")
        steps.append(Step(
            name="Generate ReDoc API reference",
            description="Create standalone API docs HTML",
            command=f"npx @redocly/cli build-docs {openapi_path} -o docs/api-reference.html",
        ))

        return steps

    def execute(self, config: dict[str, Any], dry_run: bool = False) -> TargetResult:
        """Build and deploy documentation."""
        import subprocess
        from pathlib import Path

        docs_config = config.get("docs", {})
        provider = docs_config.get("provider", "mkdocs")
        deploy_to = docs_config.get("deploy_to", "gh-pages")
        openapi_path = docs_config.get("openapi_path", "openapi.yaml")

        artifacts = []

        if dry_run:
            steps = []
            if provider == "mkdocs":
                steps.append("mkdocs build")
                if deploy_to == "gh-pages":
                    steps.append("mkdocs gh-deploy")
            steps.append(f"redocly build-docs {openapi_path}")

            return TargetResult(
                success=True,
                message=f"Would run: {', '.join(steps)}",
                artifacts=["site/", "docs/api-reference.html"],
            )

        # Build MkDocs
        if provider == "mkdocs" and Path("mkdocs.yml").exists():
            result = subprocess.run(
                ["mkdocs", "build"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return TargetResult(
                    success=False,
                    message=f"MkDocs build failed: {result.stderr}",
                )
            artifacts.append("site/")

            # Deploy to gh-pages
            if deploy_to == "gh-pages":
                result = subprocess.run(
                    ["mkdocs", "gh-deploy", "--force"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return TargetResult(
                        success=False,
                        message=f"Deploy failed: {result.stderr}",
                    )

        # Build ReDoc
        if Path(openapi_path).exists():
            Path("docs").mkdir(exist_ok=True)
            result = subprocess.run(
                [
                    "npx", "@redocly/cli", "build-docs",
                    openapi_path, "-o", "docs/api-reference.html"
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                artifacts.append("docs/api-reference.html")

        return TargetResult(
            success=True,
            message="Documentation built and deployed",
            artifacts=artifacts,
        )
