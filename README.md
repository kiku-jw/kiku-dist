# 菊 KikuAI Distributor

[![Version](https://img.shields.io/badge/version-0.1.0-black?style=for-the-badge)](https://github.com/kiku-jw/kiku-dist)
[![Python](https://img.shields.io/badge/python-3.11+-black?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-AGPL--3.0-black?style=for-the-badge)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/CI-Success-black?style=for-the-badge&logo=github-actions)](.github/workflows)

> Maintenance mode: kept public as a reusable release-automation reference, but not under active product development.

**CLI-first, CI-agnostic release automation for KikuAI API products.**

KikuAI Distributor (`kiku-dist`) is a specialized tool designed to orchestrate the entire release cycle of API products—from version bumping and container building to documentation deployment and marketplace preparation. It is built to be **CI-agnostic**, keeping your release logic in your codebase, not hidden in CI yaml files.

---

## ⚡ Quick Start

```bash
# 1. Install
pipx install git+https://github.com/kiku-jw/kiku-dist.git

# 2. Initialize
kiku-dist init

# 3. Check prerequisites (tools, tokens, API access)
kiku-dist doctor

# 4. Preview your release
kiku-dist plan --targets gh,container,docs

# 5. Execute
kiku-dist release patch
kiku-dist publish --targets gh,container,docs
```

---

## 🏗 Key Principles

- 🐚 **CLI-First**: Everything is a command. Zero manual UI clicks in dashboards.
- ⚙️ **CI-Agnostic**: Core logic lives in the CLI. GHA, GitLab, or Jenkins are just runners.
- 🩺 **Self-Healing**: `doctor` command verifies scopes, tool presence, and connectivity before you ship.
- 📝 **Marketplace Ready**: Built-in support for generating RapidAPI and Product Hunt launch kits.
- 🛡 **Dry-Run Default**: Preview every action to ensure safety.

---

## 🛠 Command Reference

### Core Commands

| Command | Description |
|:---|:---|
| `kiku-dist init` | Scaffolds `kiku-dist.toml` with project defaults. |
| `kiku-dist doctor` | Deep-checks prerequisites: `gh`, `docker`, `GH_TOKEN` scopes, etc. |
| `kiku-dist plan` | Visualizes the execution steps for specified targets. |
| `kiku-dist status` | Shows current version, last tag, and recent commit history. |

### Release Flow

| Command | Description |
|:---|:---|
| `kiku-dist release <type>` | Bumps version (`patch`, `minor`, `major`), updates changelog, and tags git. |
| `kiku-dist publish` | Publishes artifacts to selected targets (GitHub, GHCR, Docker Hub, Docs). |
| `kiku-dist ci run` | Triggers a workflow on your primary CI backend from the local terminal. |

### Marketplace Helpers

| Command | Description |
|:---|:---|
| `kiku-dist prepare listing` | Generates marketplace copy and `metadata.json` from OpenAPI + README. |
| `kiku-dist prepare rapidapi` | Generates a full RapidAPI launch kit with checklist and MCP instructions. |
| `kiku-dist prepare producthunt` | Generates Product Hunt copy, UTM links, and media checklists. |

---

## 🎯 Distribution Targets

| Target | Backend | Description |
|:---|:---|:---|
| `gh` | GitHub | Creates a GitHub Release with auto-generated release notes. |
| `container` | Docker | Builds and pushes multi-arch images to GHCR and Docker Hub. |
| `docs` | MkDocs | Builds and deploys Material-docs and ReDoc to GitHub Pages. |
| `pr-dirs` | Git | Automates PRs to directories like "awesome-lists" or API catalogs. |
| `rapidapi` | Marketplace | Generates artifacts for manual or semi-auto upload to RapidAPI Hub. |

---

## ☁️ CI Integration

Distributor comes with production-ready templates for the following backends:

- [GitHub Actions](ci_templates/gha/)
- [GitLab CI](ci_templates/gitlab-ci.yml)
- [Drone / Woodpecker](ci_templates/.drone.yml)
- [Jenkins](ci_templates/Jenkinsfile)

To use, simply copy the relevant template to your repository. All templates inherit `kiku-dist` logic, ensuring consistency across environments.

---

## ⚙️ Configuration

Configuration is managed via `kiku-dist.toml`. Example structure:

```toml
name = "masker-api"
version = "1.0.0"
description = "Privacy-first PII Redaction API"

[ci]
primary = "gha"
repo = "KikuAI/masker-api"
branch = "main"

[container]
registry = ["ghcr", "dockerhub"]
platforms = ["linux/amd64", "linux/arm64"]

[docs]
provider = "mkdocs"
openapi_path = "openapi.json"
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our development workflow.

## 📄 License

Distributed under the AGPL-3.0 License. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ by <b>KikuAI</b>
</p>
