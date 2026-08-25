# Changelog

All notable changes to graver are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Release Please maintains released sections from Conventional Commit pull-request
titles. Maintainers review every release pull request and add any needed upgrade,
compatibility, security, deprecation, or known-issue notes before merging it.

## [1.0.0-rc.1](https://github.com/mcqueary/graver/compare/v0.1.0...v1.0.0-rc.1) (2026-08-25)


### ⚠ BREAKING CHANGES

* **api:** finalize public boundary and CI hygiene
* **cli:** normalize public command contract

### Features

* **api:** add optimistic task updates ([#63](https://github.com/mcqueary/graver/issues/63)) ([fcd0771](https://github.com/mcqueary/graver/commit/fcd0771d1e8c60c54e767a6728d50cae2514e31c))
* **api:** add progress and cancellation contracts ([#64](https://github.com/mcqueary/graver/issues/64)) ([f89abe0](https://github.com/mcqueary/graver/commit/f89abe0fccb55def5777daecfbfa346d0329986a))
* **api:** add stable application errors ([#65](https://github.com/mcqueary/graver/issues/65)) ([14cd65b](https://github.com/mcqueary/graver/commit/14cd65b572531d153fbd5f090fc493364dc56341))
* **api:** add summary acquisition receipts ([#66](https://github.com/mcqueary/graver/issues/66)) ([7db4a0d](https://github.com/mcqueary/graver/commit/7db4a0d5fd0b7821c8ebd1e0ed19207e6447f77b))
* **api:** add workspace consumer boundary ([#62](https://github.com/mcqueary/graver/issues/62)) ([b08bede](https://github.com/mcqueary/graver/commit/b08bedefb39eb3007e1c1ed3965e89b61a7a284b))
* **api:** complete installed-wheel consumer contract ([4cbf3c4](https://github.com/mcqueary/graver/commit/4cbf3c45bdf545a7abacf50f18dd8513c280a230))
* **cli:** support first-class entry points ([789b85f](https://github.com/mcqueary/graver/commit/789b85fdf3b483c9078ab9adc15f61b6ff4b142e))
* **cli:** version machine-readable results ([da34421](https://github.com/mcqueary/graver/commit/da34421e77ee19e0ff952cf50737bbbf25e44c4c))
* **evidence:** add offline assessment workflow ([#47](https://github.com/mcqueary/graver/issues/47)) ([6b2a243](https://github.com/mcqueary/graver/commit/6b2a243f7726a6950f79ce9c8b2fa0bf8263ec6a))
* **evidence:** add source-neutral packet validation ([#59](https://github.com/mcqueary/graver/issues/59)) ([defa2ac](https://github.com/mcqueary/graver/commit/defa2ac56ed3325025151b659b98c279fa55e2be))
* **evidence:** enforce traceable research conclusions ([#52](https://github.com/mcqueary/graver/issues/52)) ([abb47a8](https://github.com/mcqueary/graver/commit/abb47a857c2224a497033ced81192a552b94c696))
* **evidence:** project records into evidence packets ([#60](https://github.com/mcqueary/graver/issues/60)) ([67ebb72](https://github.com/mcqueary/graver/commit/67ebb728e643e1e049677e426f433fe282d099f1))
* **review:** add R2 workflow adapter ([#48](https://github.com/mcqueary/graver/issues/48)) ([e909b9b](https://github.com/mcqueary/graver/commit/e909b9b5b79574f9b2511cb27f58fb6c2fdc66a6))


### Bug Fixes

* **release:** pin first candidate version ([#89](https://github.com/mcqueary/graver/issues/89)) ([7f58a62](https://github.com/mcqueary/graver/commit/7f58a6207cf32ea09ca36c2af9831416c701caca))


### Performance Improvements

* add offline responsiveness baseline ([#76](https://github.com/mcqueary/graver/issues/76)) ([e8474c9](https://github.com/mcqueary/graver/commit/e8474c98ec00e9ba2595cdb4b9941b9df0b2dc32))


### Documentation

* add professional genealogist usability review ([c3b5be7](https://github.com/mcqueary/graver/commit/c3b5be7e250f15fbebe6aaf68fe23d648f389350))
* add professional researcher review gates ([12d04fe](https://github.com/mcqueary/graver/commit/12d04fe231ab0e410871fccf8f6235fbc9649565))
* add rc1 migration and release guides ([#75](https://github.com/mcqueary/graver/issues/75)) ([66e129a](https://github.com/mcqueary/graver/commit/66e129a14799585f02600489d75c9869d40ec664))
* add source-neutral evidence review ([#55](https://github.com/mcqueary/graver/issues/55)) ([77fad3f](https://github.com/mcqueary/graver/commit/77fad3f43820f8a02ed7a990db610e16a1c7725c))
* clarify naming and GEDCOM direction ([aeb9163](https://github.com/mcqueary/graver/commit/aeb9163cb74e4d63773943f7e54efa0a68903d05))
* clarify project ancestry ([b3f780a](https://github.com/mcqueary/graver/commit/b3f780aa96681f91882f2e51e71c3d93bb55eb23))
* clarify researcher-facing README ([#43](https://github.com/mcqueary/graver/issues/43)) ([01cebb6](https://github.com/mcqueary/graver/commit/01cebb6f21fb616faee2c25504fe197aefa43f3d))
* close provider and import scope gate ([#68](https://github.com/mcqueary/graver/issues/68)) ([83b8558](https://github.com/mcqueary/graver/commit/83b8558b2f6b3f192616ce89a497fbb2ed2b27c6))
* complete R1 evidence review ([#46](https://github.com/mcqueary/graver/issues/46)) ([1162b23](https://github.com/mcqueary/graver/commit/1162b230230dd3d5607436b84aef335c0e1a7859))
* define evidence assessment architecture ([e6da3f5](https://github.com/mcqueary/graver/commit/e6da3f56097483fc37f27910fcb30d3f0a5847d7))
* define source-neutral trust strategy ([#54](https://github.com/mcqueary/graver/issues/54)) ([3841977](https://github.com/mcqueary/graver/commit/3841977555dc26912da345d489c85d69d0f9c1bb))
* prepare evidence contract review ([#44](https://github.com/mcqueary/graver/issues/44)) ([7296865](https://github.com/mcqueary/graver/commit/7296865ee17b3a2307c771225ca95681461e2744))
* record completed security scans ([532c60d](https://github.com/mcqueary/graver/commit/532c60dadb2a5f0fe8239fe168a067356483634e))
* record resume checkpoint ([d9d0a7f](https://github.com/mcqueary/graver/commit/d9d0a7f9473de2360c22ed74f1d9cdd013ec1376))
* record S1 evidence contract pass ([#58](https://github.com/mcqueary/graver/issues/58)) ([5b8f50f](https://github.com/mcqueary/graver/commit/5b8f50f336cd00dede4f9116c826db065f8bd77b))
* record trusted publisher setup ([#86](https://github.com/mcqueary/graver/issues/86)) ([36b3824](https://github.com/mcqueary/graver/commit/36b3824e29867a5abd122ae241d2f62795dd2f21))
* resolve S1 evidence contract findings ([#57](https://github.com/mcqueary/graver/issues/57)) ([9bea2ed](https://github.com/mcqueary/graver/commit/9bea2edc81632786b25e64d6d21c2a5533dd02f9))
* respond to blocked R1 review ([#45](https://github.com/mcqueary/graver/issues/45)) ([d08a918](https://github.com/mcqueary/graver/commit/d08a918004261496b8b1c7444c90d83cc068f509))


### Code Refactoring

* **api:** finalize public boundary and CI hygiene ([2ce520e](https://github.com/mcqueary/graver/commit/2ce520e69faaf1a562ba978cfb014880eccb06b0))
* **cli:** normalize public command contract ([9d3e3c0](https://github.com/mcqueary/graver/commit/9d3e3c0eb5b2adf7c82acffdc28387bd87d03aa4))

## [Unreleased]

### Added

- Added an explicitly invoked, one-request live Find a Grave compatibility canary
  with sanitized human and JSON reports; it remains outside ordinary tests, CI,
  release automation, and researcher-facing commands.
- Added a deterministic offline performance harness, weekly/manual baseline
  workflow, retained machine-readable reports, and provisional GUI responsiveness
  budgets without adding a pull-request timing gate.
- Added researcher-safe database upgrade and recovery guidance, draft `1.0.0rc1`
  release notes, and a manually gated maintainer release checklist.
- Added typed full-memorial and displayed-relationship acquisition inputs to the
  supported application API, with installed-wheel coverage of the complete offline
  workspace workflow.

graver is undergoing substantial pre-1.0 development. The current repository state
does not yet represent a supported production release.

### Changed

- Adopted `graver-genealogy` as the installable distribution name because the PyPI
  name `graver` belongs to unrelated software. The product name, repository,
  command, and Python import package remain `graver`.

- Completed the pre-1.0 API-hygiene pass with installed-wheel evidence-service
  coverage, canonical-document indexing, CI checks for maintenance scripts, and
  removal of only corroborated unreachable private scaffolding.
- Summary batches now validate the database once at the operation boundary instead
  of reopening schema validation for every memorial, preventing large transactions
  from tripping over their own SQLite lock.
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
