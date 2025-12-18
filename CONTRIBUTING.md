# Contributing to KikuAI Distributor

First off, thank you for considering contributing to KikuAI Distributor! It's people like you that make `kiku-dist` such a great tool for the community.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kikuai/kiku-dist.git
   cd kiku-dist
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

## Workflow

1. **Create a branch**: Use a descriptive name like `feature/new-target` or `fix/issue-123`.
2. **Make your changes**: Follow the existing code style and ensure types are handled correctly with Pydantic.
3. **Add tests**: If you're adding a new feature or fixing a bug, please add corresponding tests in `tests/`.
4. **Run tests**:
   ```bash
   pytest
   ```
5. **Update documentation**: If your changes affect the CLI interface, update `README.md` and `PROJECT.md`.

## Coding Standards

- We use **Typer** for the CLI.
- We use **Pydantic** for configuration and data models.
- We follow **PEP 8** standards.
- Keep the CLI **CI-agnostic**—logic should not depend on environment variables specific to one CI provider unless it's in a specialized runner.

## Pull Request Process

1. Ensure all tests pass.
2. Update the `CHANGELOG.md` with your changes under the `[Unreleased]` section.
3. Submit the PR and wait for review.

---

*Happy hacking!*
