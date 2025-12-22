"""Container target for Docker builds and pushes."""

from typing import Any

from kiku_dist.targets.base import Issue, IssueLevel, Step, Target, TargetResult


class ContainerTarget(Target):
    """Build and push Docker containers to GHCR and Docker Hub."""

    name = "container"
    aliases = ["docker", "ghcr", "dockerhub"]
    description = "Build and push Docker images to registries"
    required_secrets = ["GHCR_TOKEN", "DOCKERHUB_TOKEN"]
    required_tools = ["docker"]
    supports_dry_run = True

    def doctor(self, config: dict[str, Any]) -> list[Issue]:
        """Check Docker and registry credentials."""
        issues = []

        import os
        import shutil
        from pathlib import Path

        # Check Docker
        if not shutil.which("docker"):
            issues.append(Issue(
                level=IssueLevel.ERROR,
                message="Docker not found",
                fix_hint="Install Docker: https://docs.docker.com/get-docker/",
            ))

        # Check Dockerfile
        container_config = config.get("container", {})
        dockerfile = container_config.get("dockerfile", "Dockerfile")
        if not Path(dockerfile).exists():
            issues.append(Issue(
                level=IssueLevel.WARNING,
                message=f"Dockerfile not found: {dockerfile}",
                fix_hint="Create Dockerfile or update container.dockerfile in config",
            ))

        # Check registry tokens based on enabled registries
        registries = container_config.get("registry", ["ghcr", "dockerhub"])

        if "ghcr" in registries:
            token = os.environ.get("GHCR_TOKEN") or os.environ.get("GITHUB_TOKEN")
            if not token:
                issues.append(Issue(
                    level=IssueLevel.ERROR,
                    message="GHCR_TOKEN not set (for GitHub Container Registry)",
                    fix_hint="Set GHCR_TOKEN or GITHUB_TOKEN with packages:write scope",
                    ci_hints=self.get_secret_hints("GHCR_TOKEN"),
                ))

        if "dockerhub" in registries:
            if not os.environ.get("DOCKERHUB_USERNAME"):
                issues.append(Issue(
                    level=IssueLevel.ERROR,
                    message="DOCKERHUB_USERNAME not set",
                    fix_hint="Set DOCKERHUB_USERNAME environment variable",
                    ci_hints=self.get_secret_hints("DOCKERHUB_USERNAME"),
                ))
            if not os.environ.get("DOCKERHUB_TOKEN"):
                issues.append(Issue(
                    level=IssueLevel.ERROR,
                    message="DOCKERHUB_TOKEN not set",
                    fix_hint="Set DOCKERHUB_TOKEN environment variable",
                    ci_hints=self.get_secret_hints("DOCKERHUB_TOKEN"),
                ))

        return issues

    def plan(self, config: dict[str, Any]) -> list[Step]:
        """Generate build and push steps."""
        name = config.get("name", "unknown")
        version = config.get("version", "0.0.0")
        container_config = config.get("container", {})

        registries = container_config.get("registry", ["ghcr", "dockerhub"])
        platforms = container_config.get("platforms", ["linux/amd64"])
        dockerfile = container_config.get("dockerfile", "Dockerfile")

        steps = []

        # Build step
        platform_arg = ",".join(platforms)
        steps.append(Step(
            name="Build multi-platform image",
            description=f"Build for {platform_arg}",
            command=f"docker buildx build --platform {platform_arg} -f {dockerfile} .",
        ))

        # Push steps per registry
        ci_repo = config.get("ci", {}).get("repo", "")

        if "ghcr" in registries and ci_repo:
            image = f"ghcr.io/{ci_repo}:{version}"
            steps.append(Step(
                name="Push to GHCR",
                description=f"Push {image}",
                command=f"docker push {image}",
                dry_run_safe=False,
            ))

        if "dockerhub" in registries:
            image = f"{name}:{version}"
            steps.append(Step(
                name="Push to Docker Hub",
                description=f"Push {image}",
                command=f"docker push {image}",
                dry_run_safe=False,
            ))

        return steps

    def execute(self, config: dict[str, Any], dry_run: bool = False) -> TargetResult:
        """Build and push Docker images."""
        import os
        import subprocess

        name = config.get("name", "unknown")
        version = config.get("version", "0.0.0")
        container_config = config.get("container", {})

        registries = container_config.get("registry", ["ghcr", "dockerhub"])
        platforms = container_config.get("platforms", ["linux/amd64"])
        dockerfile = container_config.get("dockerfile", "Dockerfile")
        ci_repo = config.get("ci", {}).get("repo", "")

        # Determine tags
        tags = []
        if "ghcr" in registries and ci_repo:
            tags.append(f"ghcr.io/{ci_repo}:{version}")
            tags.append(f"ghcr.io/{ci_repo}:latest")
        if "dockerhub" in registries:
            username = os.environ.get("DOCKERHUB_USERNAME", name)
            tags.append(f"{username}/{name}:{version}")
            tags.append(f"{username}/{name}:latest")

        if dry_run:
            return TargetResult(
                success=True,
                message=f"Would build and push {len(tags)} tags",
                artifacts=tags,
                metadata={"platforms": platforms},
            )

        # Build command with buildx
        platform_arg = ",".join(platforms)
        tag_args = []
        for tag in tags:
            tag_args.extend(["-t", tag])

        cmd = [
            "docker", "buildx", "build",
            "--platform", platform_arg,
            "-f", dockerfile,
            "--push",
            *tag_args,
            ".",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return TargetResult(
                    success=False,
                    message=f"Build failed: {result.stderr}",
                )

            return TargetResult(
                success=True,
                message=f"Built and pushed {len(tags)} images",
                artifacts=tags,
            )
        except Exception as e:
            return TargetResult(
                success=False,
                message=f"Error: {e}",
            )
