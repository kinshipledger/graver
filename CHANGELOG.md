# Changelog

All notable changes to graver are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Release Please maintains released sections from Conventional Commit pull-request
titles. Maintainers review every release pull request and add any needed upgrade,
compatibility, security, deprecation, or known-issue notes before merging it.

## [Unreleased]

### Added

- Added typed full-memorial and displayed-relationship acquisition inputs to the
  supported application API, with installed-wheel coverage of the complete offline
  workspace workflow.

graver is undergoing substantial pre-1.0 development. The current repository state
does not yet represent a supported production release.

### Changed

- Made ordinary tests fail closed on socket access, locked existing provider
  cassettes to replay-only mode, registered strict test-layer markers, and removed
  duplicate inherited smoke coverage and obsolete commented test bodies.
- Reduced redundant CI work by making branch coverage the complete Python 3.14 lane,
  focusing Windows on portability-sensitive contracts, and enforcing five-minute
  job ceilings. Removed two unused development dependencies.
- Machine-readable CLI results now use a versioned envelope with
  `schema_version`, a stable dotted `command` identifier, and the previous result
  payload under `data`. Pre-1.0 scripts that read top-level result fields must read
  them from `data` instead.
- `graver` remains the primary installed command, and `python -m graver` now invokes
  the same command application as a supported fallback. CI verifies both entry
  points and installs the built wheel as an isolated uv tool.
- Search options now use consistent researcher-facing kebab-case names. Tri-state
  filters use explicit pairs such as `--famous/--not-famous`, and deprecated Typer
  value-taking Boolean behavior has been removed.

### Removed

- Removed accidental parser, persistence, transport-driver, alias, and task-helper
  re-exports from the `graver` package root. Application clients must import the
  documented typed contract from `graver.application`; internal modules are not a
  supported replacement API.
- Removed the hidden pre-1.0 task and alias command names. Use `graver work …` for
  research tasks and `graver admin aliases …` for redirect maintenance. Removed
  duplicate and site-shaped search spellings including `--id`, `--cid`, `--max`,
  and camel-case options; use the names shown by `graver search --help`.
- Removed the legacy `scrape-url` and unattended `scrape-file` commands. Use
  `graver search` to retain summary observations, then `graver work queue`,
  `graver work mark`, and `graver work enrich` for explicit one-person full-record
  acquisition with task approval and provenance.
