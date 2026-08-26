# Changelog

All notable changes to graver are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Release Please maintains released sections from Conventional Commit pull-request
titles. Maintainers review every release pull request and add any needed upgrade,
compatibility, security, deprecation, or known-issue notes before merging it.

## [Unreleased]

## [1.0.0-rc.1](https://github.com/mcqueary/graver/compare/v0.1.0...v1.0.0-rc.1) (2026-08-25)

This is graver's first public release candidate. It is intended for careful
evaluation with copied or otherwise recoverable research data, not yet as a promise
of production stability.

### Highlights

- Added provenance-aware summary and full-memorial acquisition, immutable dated
  observations, explicit research tasks, and researcher-controlled enrichment.
- Added stable research subjects and source-neutral evidence packets without
  turning discovery ordering into confidence, proof, or an automated identity
  conclusion.
- Added explicit database creation, read-only schema inspection, and transactional,
  backed-up upgrades from recognized legacy databases.
- Added a typed public application API for future graphical and other clients while
  retaining `graver` as a first-class command-line tool.
- Added professional-researcher evidence reviews, security and privacy guidance,
  offline performance baselines, and fail-closed network testing.

### Upgrade and compatibility notes

- The distribution is installed as `graver-genealogy`; the command and Python
  import package remain `graver`. The `graver` project on PyPI is unrelated.
- Existing databases are never silently migrated by ordinary reads. Back up the
  database, inspect it, and use `graver admin database upgrade DATABASE` when an
  upgrade is required. See the migration guide before upgrading valuable data.
- Machine-readable command output now uses a versioned envelope with
  `schema_version`, `command`, and `data`. Pre-1.0 scripts that read result fields
  at the top level must read them from `data`.
- The supported Python API is the typed contract in `graver.application`. Accidental
  root-package exports and internal parser, SQL, transport, alias, and task helpers
  are no longer public API.
- Hidden pre-1.0 command aliases, duplicate/site-shaped search option spellings,
  `scrape-url`, and unattended `scrape-file` were removed. Use the documented
  `graver work ...` workflow and the option names shown by `graver search --help`.

### Security and provider access

- The default HTTP transport is an ordinary Requests-based client that stops on
  access challenges and repeated rate limiting; it does not solve challenges or
  attempt to conceal automation.
- Unattended provider acquisition remains disabled without documented authorization.
  The live compatibility canary is a separate, explicitly invoked, one-request
  maintainer check and is not part of ordinary tests or release automation.

### Known limitations and deferred scope

- This candidate has no graphical client. Its typed application boundary is the
  foundation for a later GUI, whose workflows will receive dedicated UX review.
- Find a Grave is a mutable external service; HTML changes can interrupt live
  acquisition even when offline tests remain green.
- FamilySearch, WikiTree, GEDCOM interchange, family work packets, and
  provider-governed background jobs are not part of this release candidate.
- The release candidate needs real-world feedback before the final `1.0.0`
  compatibility promise is made.


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
