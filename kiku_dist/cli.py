"""Main CLI entry point for kiku-dist."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from kiku_dist import __version__
from kiku_dist.config import get_config_template, load_config
from kiku_dist.doctor import print_doctor_report, run_doctor

app = typer.Typer(
    name="kiku-dist",
    help="CLI-first, CI-agnostic release automation for KikuAI API products.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"kiku-dist version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """KikuAI Distributor - Release automation from terminal."""
    pass


@app.command()
def init(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing config"),
    ] = False,
) -> None:
    """Initialize kiku-dist.toml configuration file."""
    config_path = Path.cwd() / "kiku-dist.toml"

    if config_path.exists() and not force:
        console.print("[yellow]kiku-dist.toml already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(1)

    config_path.write_text(get_config_template())
    console.print(f"[green]✓ Created {config_path}[/green]")
    console.print()
    console.print("Next steps:")
    console.print("  1. Edit kiku-dist.toml with your project settings")
    console.print("  2. Run [bold]kiku-dist doctor[/bold] to verify setup")
    console.print("  3. Run [bold]kiku-dist plan --targets gh,container[/bold] to preview")


@app.command()
def doctor(
    ci: Annotated[
        bool,
        typer.Option("--ci", help="CI mode - exit with error on any issue"),
    ] = False,
    targets: Annotated[
        str | None,
        typer.Option("--targets", "-t", help="Comma-separated targets to check"),
    ] = None,
) -> None:
    """Check prerequisites: tools, secrets, OpenAPI, token scopes."""
    try:
        config = load_config()
    except FileNotFoundError:
        config = None

    target_list = targets.split(",") if targets else None
    result = run_doctor(config, target_list)

    print_doctor_report(result, console)

    if ci and result.failed > 0:
        raise typer.Exit(1)


@app.command()
def plan(
    targets: Annotated[
        str,
        typer.Option("--targets", "-t", help="Comma-separated targets"),
    ] = "gh,container,docs",
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show plan only, no changes"),
    ] = True,
) -> None:
    """Preview execution plan for specified targets."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    target_list = [t.strip() for t in targets.split(",")]

    console.print()
    console.print(Panel(
        f"[bold]{config.name}[/bold] v{config.version}",
        title="Release Plan",
        expand=False,
    ))
    console.print()

    # Import targets and generate plan
    from kiku_dist.targets import registry

    for target_name in target_list:
        target = registry.get(target_name)
        if target is None:
            console.print(f"[yellow]⚠ Unknown target: {target_name}[/yellow]")
            continue

        console.print(f"[bold]{target.name}[/bold] - {target.description}")
        steps = target.plan(config.model_dump())
        for i, step in enumerate(steps, 1):
            icon = "○" if dry_run else "●"
            console.print(f"  {icon} {i}. {step.name}")
            if step.command:
                console.print(f"     [dim]$ {step.command}[/dim]")
        console.print()


@app.command()
def release(
    bump: Annotated[
        str,
        typer.Argument(help="Version bump: patch | minor | major"),
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Simulate without actual release"),
    ] = False,
    no_git: Annotated[
        bool,
        typer.Option("--no-git", help="Skip git tag/commit"),
    ] = False,
) -> None:
    """Bump version, generate changelog, create release."""
    if bump not in ("patch", "minor", "major"):
        console.print(f"[red]Invalid bump type: {bump}. Use patch, minor, or major.[/red]")
        raise typer.Exit(1)

    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Releasing {config.name}[/bold]")
    console.print(f"  Current version: {config.version}")
    console.print(f"  Bump type: {bump}")
    console.print()

    # Build release-it command
    cmd_parts = ["npx", "release-it", bump]
    if dry_run:
        cmd_parts.append("--dry-run")
    if no_git:
        cmd_parts.extend(["--no-git.tag", "--no-git.commit"])

    cmd = " ".join(cmd_parts)

    if dry_run:
        console.print(f"[dim]Would run: {cmd}[/dim]")
        console.print("[yellow]Dry run - no changes made[/yellow]")
    else:
        import subprocess
        console.print(f"[dim]$ {cmd}[/dim]")
        result = subprocess.run(cmd_parts, capture_output=False)
        if result.returncode != 0:
            raise typer.Exit(result.returncode)


@app.command()
def publish(
    targets: Annotated[
        str,
        typer.Option("--targets", "-t", help="Comma-separated targets"),
    ] = "gh,ghcr,dockerhub,docs",
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Simulate without actual publish"),
    ] = False,
) -> None:
    """Publish to specified targets."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    target_list = [t.strip() for t in targets.split(",")]

    console.print()
    console.print(f"[bold]Publishing {config.name} v{config.version}[/bold]")
    console.print(f"  Targets: {', '.join(target_list)}")
    console.print(f"  Dry run: {dry_run}")
    console.print()

    from kiku_dist.targets import registry

    failed = []
    for target_name in target_list:
        target = registry.get(target_name)
        if target is None:
            console.print(f"[yellow]⚠ Unknown target: {target_name}[/yellow]")
            continue

        console.print(f"[bold]→ {target.name}[/bold]")
        try:
            result = target.execute(config.model_dump(), dry_run=dry_run)
            if result.success:
                console.print(f"  [green]✓ {result.message}[/green]")
                for artifact in result.artifacts:
                    console.print(f"    [dim]→ {artifact}[/dim]")
            else:
                console.print(f"  [red]✗ {result.message}[/red]")
                failed.append(target_name)
        except Exception as e:
            console.print(f"  [red]✗ Error: {e}[/red]")
            failed.append(target_name)
        console.print()

    if failed:
        console.print(f"[red]Failed targets: {', '.join(failed)}[/red]")
        raise typer.Exit(1)

    console.print("[green]✓ All targets published successfully[/green]")


@app.command()
def status() -> None:
    """Show current version, last release, pending changes."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print()
    console.print(f"[bold]{config.name}[/bold]")
    console.print(f"  Version: {config.version}")
    console.print(f"  CI Backend: {config.ci.primary}")
    console.print(f"  Repository: {config.ci.repo or '(not set)'}")
    console.print()

    # Check git for pending changes
    import subprocess

    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"  Last tag: {result.stdout.strip()}")
        else:
            console.print("  Last tag: (none)")
    except Exception:
        console.print("  Last tag: (git unavailable)")

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "HEAD", "-5"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print()
            console.print("  Recent commits:")
            for line in result.stdout.strip().split("\n")[:5]:
                console.print(f"    {line}")
    except Exception:
        pass


# CI runner subcommand
ci_app = typer.Typer(help="CI backend operations")
app.add_typer(ci_app, name="ci")


@ci_app.command("run")
def ci_run(
    backend: Annotated[
        str,
        typer.Option("--backend", "-b", help="CI backend: gha | gitlab | drone | jenkins"),
    ] = "gha",
    workflow: Annotated[
        str | None,
        typer.Option("--workflow", "-w", help="Workflow name to trigger"),
    ] = None,
    ref: Annotated[
        str | None,
        typer.Option("--ref", "-r", help="Git ref (tag/branch) to run against"),
    ] = None,
) -> None:
    """Trigger CI workflow from terminal."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not config.ci.repo:
        console.print("[red]Error: ci.repo not set in kiku-dist.toml[/red]")
        raise typer.Exit(1)

    workflow_name = workflow or "release"
    git_ref = ref or config.ci.branch

    console.print("[bold]Triggering CI workflow[/bold]")
    console.print(f"  Backend: {backend}")
    console.print(f"  Repo: {config.ci.repo}")
    console.print(f"  Workflow: {workflow_name}")
    console.print(f"  Ref: {git_ref}")
    console.print()

    if backend == "gha":
        import subprocess
        cmd = [
            "gh", "workflow", "run", f"{workflow_name}.yml",
            "--repo", config.ci.repo,
            "--ref", git_ref,
        ]
        console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
        console.print("[green]✓ Workflow triggered[/green]")
    else:
        console.print(f"[yellow]Backend '{backend}' requires manual trigger or API call.[/yellow]")
        console.print("See documentation for API examples.")


# Prepare subcommand
prepare_app = typer.Typer(help="Prepare launch kits for manual platforms")
app.add_typer(prepare_app, name="prepare")


@prepare_app.command("rapidapi")
def prepare_rapidapi(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("./dist/rapidapi"),
) -> None:
    """Prepare RapidAPI launch kit (description, assets, checklist)."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print("[bold]Preparing RapidAPI Launch Kit[/bold]")
    console.print()

    output.mkdir(parents=True, exist_ok=True)

    # Generate description
    description = f"""# {config.name}

{config.description}

## Features

- Fast, reliable API
- OpenAPI 3.0 specification
- Rate limiting included

## Endpoints

See the API specification for detailed endpoint documentation.
"""
    (output / "description.md").write_text(description)
    console.print("  [green]✓[/green] Created description.md")

    # Generate checklist
    checklist = f"""# RapidAPI Publication Checklist

## Pre-publication
- [ ] Verify OpenAPI spec is up to date
- [ ] Test all endpoints manually
- [ ] Set pricing tiers

## Publication Steps
1. Go to https://rapidapi.com/provider
2. Click "Add New API"
3. Upload OpenAPI spec from: {config.docs.openapi_path}
4. Copy description from: {output}/description.md
5. Configure pricing model
6. Set rate limits
7. Submit for review

## Post-publication
- [ ] Verify API is accessible
- [ ] Test via RapidAPI dashboard
- [ ] Monitor usage metrics
"""
    (output / "checklist.md").write_text(checklist)
    console.print("  [green]✓[/green] Created checklist.md")

    console.print()
    console.print(f"[green]✓ Launch kit ready:[/green] {output}")
    console.print()
    console.print("[yellow]⚠ RapidAPI requires manual publication.[/yellow]")
    console.print(f"  Follow the checklist: {output}/checklist.md")


@prepare_app.command("producthunt")
def prepare_producthunt(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("./dist/producthunt"),
) -> None:
    """Prepare Product Hunt launch kit (copy, assets, UTM links)."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print("[bold]Preparing Product Hunt Launch Kit[/bold]")
    console.print()

    output.mkdir(parents=True, exist_ok=True)

    # Generate launch copy
    launch_copy = f"""# {config.name} - Product Hunt Launch

## Tagline (60 chars max)
{config.description[:60] if config.description else 'Your tagline here'}

## Description (260 chars max)
{config.description[:260] if config.description else 'Your description here'}

## First Comment
Hey Product Hunt! 👋

We built {config.name} to solve [problem].

Key features:
- Feature 1
- Feature 2
- Feature 3

We'd love your feedback!

## UTM Links
- Landing: https://kikuai.dev/{config.name.lower()}?utm_source=producthunt&utm_medium=launch
- Docs: https://kikuai.dev/{config.name.lower()}/docs?utm_source=producthunt&utm_medium=launch

## Topics
- Developer Tools
- APIs
- Artificial Intelligence
"""
    (output / "launch_copy.md").write_text(launch_copy)
    console.print("  [green]✓[/green] Created launch_copy.md")

    # Generate checklist
    checklist = f"""# Product Hunt Launch Checklist

## 1 Week Before
- [ ] Prepare 1200x630 thumbnail
- [ ] Prepare 1270x760 gallery images (3-5)
- [ ] Create 30-second demo video
- [ ] Draft first comment
- [ ] Line up hunters/supporters

## Launch Day
1. Go to https://www.producthunt.com/posts/new
2. Upload media assets
3. Copy content from: {output}/launch_copy.md
4. Set launch time (12:01 AM PT recommended)
5. Post and engage!

## Post-Launch
- [ ] Respond to all comments
- [ ] Share on social media
- [ ] Update landing page with PH badge
- [ ] Thank supporters
"""
    (output / "checklist.md").write_text(checklist)
    console.print("  [green]✓[/green] Created checklist.md")

    console.print()
    console.print(f"[green]✓ Launch kit ready:[/green] {output}")
    console.print()
    console.print("[yellow]⚠ Product Hunt requires manual launch.[/yellow]")
    console.print(f"  Follow the checklist: {output}/checklist.md")


@prepare_app.command("listing")
def prepare_listing(
    product_dir: Annotated[
        Path,
        typer.Argument(help="Product directory (with openapi.yaml/json and README.md)"),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = Path("./dist/listing"),
    openapi: Annotated[
        str | None,
        typer.Option("--openapi", help="OpenAPI file path (auto-detect if not set)"),
    ] = None,
) -> None:
    """Generate marketplace listing from OpenAPI spec and docs."""
    from kiku_dist.prepare_listing import generate_listing, save_listing

    console.print("[bold]Generating Marketplace Listing[/bold]")
    console.print()

    product_dir = Path(product_dir).resolve()
    if not product_dir.exists():
        console.print(f"[red]Error: Directory not found: {product_dir}[/red]")
        raise typer.Exit(1)

    # Find OpenAPI spec
    openapi_path = None
    if openapi:
        openapi_path = product_dir / openapi
    else:
        for filename in ["openapi.yaml", "openapi.yml", "openapi.json"]:
            candidate = product_dir / filename
            if candidate.exists():
                openapi_path = candidate
                break

    if not openapi_path or not openapi_path.exists():
        console.print("[red]Error: OpenAPI spec not found. Use --openapi to specify.[/red]")
        raise typer.Exit(1)

    console.print(f"  OpenAPI: {openapi_path}")

    # Find README
    readme_path = None
    for filename in ["README.md", "readme.md", "Readme.md"]:
        candidate = product_dir / filename
        if candidate.exists():
            readme_path = candidate
            break

    if readme_path:
        console.print(f"  README: {readme_path}")

    console.print()

    try:
        listing = generate_listing(openapi_path, readme_path)
        files = save_listing(listing, Path(output))

        console.print("[green]✓ Generated listing files:[/green]")
        for f in files:
            console.print(f"  → {f}")
        console.print()
        console.print(f"[bold]Listing:[/bold] {listing['name']}")
        console.print(f"  Tagline: {listing['tagline']}")
        console.print(f"  Endpoints: {len(listing['endpoints'])}")
        console.print(f"  Tags: {', '.join(listing['tags'][:5])}")
        console.print(f"  Category: {listing['category']}")

    except Exception as e:
        console.print(f"[red]Error generating listing: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

