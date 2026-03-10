# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-18

### Added
- Initial release of KikuAI Distributor.
- Core CLI commands: `init`, `doctor`, `plan`, `release`, `publish`, `status`, `ci run`.
- Marketplace preparation: `prepare listing`, `prepare rapidapi`, `prepare producthunt`.
- Supported Targets: `gh` (GitHub Release), `container` (GHCR/Docker Hub), `docs` (MkDocs/ReDoc), `pr-dirs` (Awesome-lists), `rapidapi` (Listing package).
- CI Templates: GitHub Actions, GitLab CI, Drone, Jenkins.
- Python-based OpenAPI validation and metadata extraction.
- CI Runner for programmatic workflow triggering.

[Unreleased]: https://github.com/kiku-jw/kiku-dist/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kiku-jw/kiku-dist/releases/tag/v0.1.0
