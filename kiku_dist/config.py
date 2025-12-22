"""Configuration loader for kiku-dist.toml."""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ContainerConfig(BaseModel):
    """Container target configuration."""

    registry: list[str] = Field(default=["ghcr", "dockerhub"])
    dockerfile: str = "Dockerfile"
    platforms: list[str] = Field(default=["linux/amd64", "linux/arm64"])
    build_args: dict[str, str] = Field(default_factory=dict)


class DocsConfig(BaseModel):
    """Documentation target configuration."""

    provider: str = "mkdocs"
    openapi_path: str = "openapi.yaml"
    deploy_to: str = "gh-pages"


class GHReleaseConfig(BaseModel):
    """GitHub Release target configuration."""

    draft: bool = False
    prerelease: bool = False
    generate_notes: bool = True


class PRDirsConfig(BaseModel):
    """PR to directories target configuration."""

    targets: list[dict[str, str]] = Field(default_factory=list)


class PrepareConfig(BaseModel):
    """Prepare-only targets configuration."""

    rapidapi: dict[str, Any] = Field(default_factory=dict)
    producthunt: dict[str, Any] = Field(default_factory=dict)


class CIConfig(BaseModel):
    """CI backend configuration."""

    primary: str = "gha"
    repo: str = ""
    branch: str = "main"


class Config(BaseModel):
    """Main kiku-dist configuration."""

    name: str
    version: str = "0.0.0"
    description: str = ""

    # Targets
    gh_release: GHReleaseConfig = Field(default_factory=GHReleaseConfig)
    container: ContainerConfig = Field(default_factory=ContainerConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)
    pr_dirs: PRDirsConfig = Field(default_factory=PRDirsConfig)
    prepare: PrepareConfig = Field(default_factory=PrepareConfig)

    # CI
    ci: CIConfig = Field(default_factory=CIConfig)


def find_config_file(start_path: Path | None = None) -> Path | None:
    """Find kiku-dist.toml in current or parent directories."""
    path = start_path or Path.cwd()

    for parent in [path, *path.parents]:
        config_file = parent / "kiku-dist.toml"
        if config_file.exists():
            return config_file

    return None


def load_config(config_path: Path | None = None) -> Config:
    """Load and parse kiku-dist.toml configuration.

    Args:
        config_path: Explicit path to config file, or None to search

    Returns:
        Parsed Config object

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not config_path.exists():
        raise FileNotFoundError(
            "kiku-dist.toml not found. Run 'kiku-dist init' to create one."
        )

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return Config(**data)


def get_config_template() -> str:
    """Return the default kiku-dist.toml template."""
    return '''# KikuAI Distributor Configuration
# https://kikuai.dev/docs/distributor

name = "my-api"
version = "0.1.0"
description = "My awesome API"

[ci]
primary = "gha"  # gha | gitlab | drone | jenkins
repo = "kikuai/my-api"
branch = "main"

[gh_release]
draft = false
prerelease = false
generate_notes = true

[container]
registry = ["ghcr", "dockerhub"]
dockerfile = "Dockerfile"
platforms = ["linux/amd64", "linux/arm64"]

[container.build_args]
# EXAMPLE = "value"

[docs]
provider = "mkdocs"  # mkdocs | redoc
openapi_path = "openapi.yaml"
deploy_to = "gh-pages"

[pr_dirs]
# List of directories/awesome-lists to submit PRs
# [[pr_dirs.targets]]
# repo = "public-apis/public-apis"
# category = "Machine Learning"
# template = "templates/public-apis.md.j2"

[prepare.rapidapi]
# hub_id = "your-hub-id"
# pricing_model = "freemium"
# tags = ["ai", "api", "machine-learning"]

[prepare.producthunt]
# tagline = "Your product tagline"
# topics = ["Developer Tools", "Artificial Intelligence"]
'''
