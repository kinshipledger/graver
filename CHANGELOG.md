# Changelog

All notable changes to graver are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Release Please maintains released sections from Conventional Commit pull-request
titles. Maintainers review every release pull request and add any needed upgrade,
compatibility, security, deprecation, or known-issue notes before merging it.

## [Unreleased]

graver is undergoing substantial pre-1.0 development. The current repository state
does not yet represent a supported production release.

### Changed

- Machine-readable CLI results now use a versioned envelope with
  `schema_version`, a stable dotted `command` identifier, and the previous result
  payload under `data`. Pre-1.0 scripts that read top-level result fields must read
  them from `data` instead.

### Removed

- Removed the legacy `scrape-url` and unattended `scrape-file` commands. Use
  `graver search` to retain summary observations, then `graver work queue`,
  `graver work mark`, and `graver work enrich` for explicit one-person full-record
  acquisition with task approval and provenance.
