# Existing system inventory: `graver`

Inspection dates: 2026-08-11; refreshed 2026-08-22

## What is present

`src/graver/` is an independently versioned Python package named `graver`, currently
at normalized package version `0.1.0`. It is a Find a Grave scraper/library with a
Typer command-line interface, SQLite persistence, and fixture-backed tests.

The current architecture includes `MemorialSummary`, immutable
acquisitions, the durable queue, explicit person-at-a-time task handling,
progressive-disclosure commands, alias provenance, and default-database selection.
Schema version 2 adds stable research subjects, subject-owned tasks, immutable
subject/task events, and memorial-ID compatibility for existing researcher workflows.

`main` is the sole long-lived release and integration branch. Short-lived branches
use pull requests and squash merges. The obsolete `master` branch was never a
formal release or supported production state and has been retired. `develop` is
retired by the release-workflow transition. No release tags exist yet.

The only configured Git remote is `origin`, pointing to
`https://github.com/mcqueary/graver.git`. The obsolete local `upstream` remote to
`pirtleshell/scrape-a-grave` was removed on 2026-08-22, and GitHub presents graver as
an independent repository rather than a fork. The Git history nevertheless begins
with Robert Pirtle's 2016 MIT-licensed commits and later refactors descend from that
work. The applicable historical copyright notice therefore remains in `LICENSE`;
the README describes the historical inspiration while explicitly disclaiming an
ongoing affiliation or upstream relationship. Rewriting history or removing the
notice is not planned.

## Current behavior

### Commands

- `search` queries Find a Grave's memorial search, including a cemetery ID option, name/date/location filters, and pagination. Search results are represented as `MemorialSummary` objects and persisted to the selected SQLite database before being emitted to logs.
- `init [DATABASE]` exclusively creates a new complete current-schema database,
  validates it, and saves its absolute path as the default. It defaults to
  `./graves.db`, requires an existing parent directory, and refuses every existing
  filesystem entry.
- `use DATABASE`, `use --show`, and `use --clear` manage one researcher-facing default database selection without creating, migrating, or deleting databases. Explicit `--db` and `GRAVER_DB` remain higher-precedence temporary selections.
- `admin database upgrade DATABASE` read-only inspects a recognized older schema,
  creates a verified deterministic sibling backup, applies ordered migrations in a
  transaction, and validates schema, integrity, and foreign keys. Current databases
  are a no-op; backup collisions, unknown schemas, and newer versions fail safely.
- `work queue`, `work list`, `work next`, `work show`, and `work mark` provide a person-centered, network-free research workflow. `work enrich` retrieves exactly one explicitly approved memorial.
- The pre-1.0 `scrape-url` and `scrape-file` commands have been removed. Summary
  search followed by explicit queueing, approval, and one-person `work enrich` is
  the supported full-record acquisition path. No unattended file loop remains.
- `admin aliases list`, `show`, `record`, and `retract` expose specialist Find a Grave redirect maintenance and immutable history without moving tasks or grave data.
- The earlier top-level task and alias compatibility commands are removed. Their
  supported replacements are the researcher-facing `work` hierarchy and specialist
  `admin aliases` hierarchy.
- The console entry point is `graver = graver.cli:app`. `graver.__main__` invokes
  the same application for supported `python -m graver` execution. Direct
  execution of the implementation module `graver.cli` is not a public contract.

graver currently has no durable background-job engine, scheduler, or unattended
bulk-enrichment mode. Full memorial enrichment is intentionally person-at-a-time and
requires the current task approval. Search-summary acquisition does not authorize or
enable mass full-page enrichment. Provider permission for unattended Find a Grave
acquisition has not been established.

The 2026-08-24
[provider acquisition and import decision](provider-import-decision.md) closes the
pre-1.0 policy gate: bounded researcher-directed acquisition remains conditional on
provider policy, while unattended Find a Grave acquisition is not authorized. A
public background-job engine, scheduler, general import API, and provider adapter
are deferred beyond `1.0.0rc1` until a concrete authorized workflow justifies their
contracts.

### Retrieval and parsing

- An internal synchronous transport backed by `requests.Session` supplies a
  transparent `graver/<version>` User-Agent, preserves ordinary cookies and
  redirects, and applies explicit 5-second connect and 30-second read timeouts.
- Current retry behavior covers HTTP 408, 429, 500, 502, 503, 504, and 599, with
  five retries by default and a 500 ms base delay for transient statuses. The
  `429` path permits one bounded retry, honors a numeric `Retry-After` up to 60
  seconds or uses exponential backoff, then stops for human review if rate limiting
  repeats. A `403` or recognized challenge page stops immediately without retry or
  bypass behavior.
- Full memorial parsing handles canonical URLs, ordinary 404s, removed memorials, and merged memorial redirects.
- Cemetery search supports counting results and follows 20-result pages.
- The test suite uses recorded HTTP cassettes rather than live Find a Grave requests.

A no-network dependency audit on 2026-08-21 reviewed the source usage, lockfile,
tests, and installed package metadata and MIT license. The primary references are
the [`cloudscraper25` repository](https://github.com/zinzied/cloudscraper25) and
[PyPI project](https://pypi.org/project/cloudscraper25/). The lockfile identifies
version 2.7.0 artifacts published 2025-05-27 and transitive dependencies on Requests,
requests-toolbelt, js2py, PyCryptodome, pyOpenSSL, pyparsing, and websocket-client.
The package metadata advertises challenge and Turnstile handling, browser/user-agent
emulation, stealth and proxy features, fingerprint behavior, JavaScript
interpreters, and CAPTCHA-service integrations. graver does not configure those
features explicitly, but default scraper construction enables automatic challenge
handling.

Current graver tests require only a Requests-compatible injectable session and
ordinary retry, error, response, and parser behavior. They do not demonstrate a
need for challenge handling, proxy rotation, browser impersonation, CAPTCHA support,
fingerprint manipulation, or any other unique package capability. The installed
metadata labels the package production/stable and lists Python classifiers through
3.9. Because the audit made no network requests, it did not establish the package's
current maintenance or security-advisory status.

On 2026-08-21, GitHub reported 20 Dependabot vulnerabilities on the repository's
default branch (8 high, 9 moderate, and 3 low) after a historical push. Review found
that 17 came from an obsolete frozen `requirements.txt`; the remaining alerts
identified outdated packages in the active development graph. On 2026-08-22, the
obsolete export was removed, runtime and development dependencies were separated,
and the complete locked graph was upgraded to mutually compatible stable releases.
An audit of the exported locked graph reported no known vulnerabilities. Weekly
Dependabot checks now cover both Python dependencies and GitHub Actions. Hosting-
service alert counts remain dated observations rather than release criteria;
`1.0.0rc1` requires no unresolved known vulnerability without an explicit,
documented risk decision.

The pre-RC security review now has a public
[threat model](security-threat-model.md) and
[privacy/data-handling guide](privacy-and-data-handling.md). The CLI no longer
creates a persistent log at import or normal startup; requested diagnostics go to
standard error. Provider HTML link failures use typed parse errors rather than
optimization-sensitive assertions. `make security` performs a locked dependency
audit with `pip-audit` and Ruff production security checks; manually reviewed S608
findings are limited to fixed internal SQL identifiers with parameter-bound values.
The pinned CodeQL workflow analyzes pull requests, `main`, and a weekly schedule.
GitHub secret scanning and push protection are enabled; the enablement check on
2026-08-25 reported no secret alerts. CodeQL had not yet completed its first run at
the time of this inventory update, so no clean-analysis claim is made here.
No hosted service, account system, telemetry, remote synchronization, database
encryption, or secure-erasure facility exists.

The approved audit result, **remove**, is now implemented. `cloudscraper25` is no
longer a runtime dependency or production/test import. Requests is an explicit
runtime dependency behind a small graver-owned transport protocol and response
model; third-party session, response, and exception types do not form the planned
public application contract. Tests can inject the internal transport directly or
continue supplying Requests-compatible Betamax sessions. The replacement does not
authorize automated provider access.

## Current SQLite databases

The local `src/graver/graves.db` is an ignored runtime byproduct of early human
command-line development, not a supported sample or repository fixture.

On 2026-08-20, a read-only inspection recorded the latest local representative
snapshot of the ignored `many_graves.db`. It was a 155,648-byte regular file, not a
symlink, with SHA-256
`affb436218b5ba2b7ac13448b12f6bddfd5fc99ff9ed21bf9c2a14d8360c678c`.
It contained 334 `graves` rows and 334 distinct memorial IDs, plus six application
tables:

```text
cemeteries
graves
memorial_alias_observations
memorial_aliases
memorial_observations
research_tasks
```

The additive `graves` columns were already present, but the database had no
`graver_schema` metadata and was classified as **current pre-version-metadata**.
One row had a non-null `detail_level`, no rows had a summary fetch timestamp, one
row had a full fetch timestamp, and one memorial observation already existed. It
contained no aliases, alias observations, or research tasks. SQLite integrity was
`ok`, and the foreign-key check returned no violations.

This differs from the database's earlier historical summary-only, `graves`-only
shape. The ignored file is mutable researcher data and had previously been opened
through application workflows; the inspection does not attribute its changes to a
particular earlier command. This dated snapshot is evidence about the current
migration implementation, not a repository contract or a promise that the local
database will remain unchanged.

`graves.memorial_id` is the primary key. The current code can store the memorial
URL, parsed name components, Find a Grave flags, birth/death values and places,
memorial type, cemetery ID, burial place, plot, coordinates, biography presence,
and the acquisition metadata `detail_level`, `summary_fetched_at`, and
`full_fetched_at`.

New databases contain application-owned schema metadata at version 2. Read-only
inspection distinguishes the known 0.1 full grave shape, the representative
summary-only legacy shape, structurally current pre-metadata databases, explicit
version-1 databases requiring upgrade, current version-2 databases, future versions,
empty databases, unrelated SQLite files, and unknown or malformed inputs. Required
structural evidence is necessary before a legacy classification is assigned.

The population originated as 334 cemetery-search summaries. Its current mutable
state includes the acquisition values and observation counted above; unclassified
legacy rows remain unclassified because graver does not infer their acquisition
origin. This supports staged enrichment rather than scraping every individual page
immediately.

### What it preserves well

- Stable Find a Grave memorial ID and canonical URL.
- Cemetery ID when available.
- A useful first-pass cemetery-search population without requiring individual memorial requests.
- An explicit distinction between search-summary and full-page acquisition.
- Separate UTC fetch timestamps for summary and full retrieval.
- Safe SQLite upserts: a later summary refresh cannot downgrade a `full` row or clear full-page-only fields.
- Immutable JSON observations for each new summary or full acquisition, written atomically with the current-state `graves` upsert.
- Cemetery metadata with first/last observed timestamps; a memorial save can create a metadata-light cemetery stub without an extra request.
- Stable lowercase UUIDv4 research subjects, one current subject association per
  memorial, and subject-owned tasks with constrained statuses, priorities,
  ownership/review fields, and timestamps.
- Immutable subject and task events. Schema migration labels mechanical subject
  creation and association honestly and creates one `task_migrated` snapshot per
  existing task without claiming prior history.
- Database-enforced observation immutability and foreign-key integrity on application connections.
- Explicit current-state memorial aliases plus immutable alias observations. Active chains resolve transitively with cycle prevention and defensive read-time detection.
- Alias ownership remains with the discovered/source memorial: redirects do not transfer, merge, complete, or delete research tasks.

### Important limitations

- The current local snapshot has a `cemeteries` table, but its presence is not a
  stable fixture guarantee because the ignored database remains mutable user data.
- `graves` remains a current-state acquisition table rather than immutable observation history. The new upserts protect richer data but do not retain earlier versions of changed source values.
- Ordered explicit migration, fetch timestamps, successful and failed acquisition observations, foreign keys, supporting indexes, initial work-queue state, and alias provenance now exist.
- Accepted family relationships, live FamilySearch matches, WikiTree matches, and
  cemetery-tag decisions are not modeled. The current schema now contains an internal,
  fixture-only evidence model for discovery snapshots, comparison signals,
  assessments, and reviewed identity conclusions; it is not a live provider or
  user-facing matching feature.
- Legacy rows are deliberately not assigned a `detail_level` during migration because their acquisition level cannot be inferred reliably. They become classified when subsequently saved through the summary or full persistence path.
- Legacy rows deliberately do not receive fabricated observation records during migration because their original timestamp and exact observed payload are unknown.
- Some acquisition commands still reflect scraper implementation terminology. Their information architecture is intentionally deferred; this milestone changes only the research and alias-maintenance surfaces.
- Full memorial acquisition now captures structured Find a Grave-displayed
  relationship links with the displayed group, linked memorial ID and URL, name,
  life text, separately available birth/death text, and marriage year. They live
  only in the immutable full-observation payload and are explicitly website
  displays—not accepted family relationships, reciprocal evidence, automatic
  linked-page retrieval, or research-subject associations.
- `research_tasks` is now keyed by `subject_id`; `subject_memorials` keeps existing
  memorial-ID lookup convenient. The schema can represent a subject with zero or
  multiple memorials, but reviewed association, reassociation, merge, split,
  preferred-memorial selection, people without memorials, and family work packets
  remain unavailable until their evidence and correction policies are implemented.

## Test and environment status

The repository has a substantial fixture-backed test suite covering memorial parsing, search filters, cemetery pagination, merged/removed memorial handling, CLI behavior, SQLite persistence, additive migration, summary/full overwrite protection, atomic observation creation, observation immutability, foreign-key constraints, and queue idempotency.
The 2026-08-24 documentation-contract addition brought the complete offline suite to
456 passing tests in 7.37 seconds locally. Local branch coverage immediately before
that documentation-only addition was 94.45% against the 90% floor.

CI avoids counting the same evidence repeatedly: the coverage job is also the full
Python 3.14 lane, Python 3.11–3.13 retain full Linux runs, macOS retains a full
platform run, and Windows runs a focused portability contract after its full suite
was measured at 2m32s of test time versus tens of seconds on the other hosted
platforms. Every required job has a five-minute ceiling and a documented four-minute
review threshold.

A separate non-required performance workflow now measures deterministic generated
100- and 10,000-record workspaces weekly and on manual request. It retains versioned
JSON reports for 90 days and records setup cost, database size, workspace validation,
work-list, task-detail, task-update, latency, and peak traced Python allocation. It
does not use providers, real research data, or PR timing thresholds. A 100,000-record
capacity probe remains explicit and manual until its cost is understood.
The initial Apple Silicon/Python 3.14 run completed both datasets in about 12 seconds.
At 10,000 tasks, median open/validation, list-50, show, and update operations remained
between 63 and 80 milliseconds. The first run also found repeated per-record schema
validation that could lock a large batch; summary persistence now validates once at
the operation boundary, protected by a focused regression test.

The inherited suite still mixes several responsibilities, but its external-access
boundary is now explicit. Pytest disables socket access by default through
`pytest-socket`; existing sanitized Betamax interactions are replay-only and are
automatically marked `recorded`; and strict marker registration covers the planned
`unit`, `integration`, `recorded`, and `slow` layers. A missing cassette interaction
fails rather than contacting a provider. The duplicate inherited Faker smoke test,
empty assertions, and obsolete commented test bodies have been removed.
`requests-mock` remains the preferred boundary for method, parameter, retry, and
error-path tests. Betamax is retained temporarily for 61 existing replay contracts;
new tests should prefer static parser fixtures and explicit transport mocks while a
small, evidence-based replacement trial determines whether another cassette tool is
actually simpler.

Runtime dependencies are limited to packages imported by the installed application.
Pytest, Faker, Betamax, and typing support are isolated in test or development
groups, and the unused `dill` dependency has been removed. The unused
`pytest-integration` plugin and `types-python-dateutil` stub have also been
removed after repository, marker, import, and mypy-scope checks found no active role.
The obsolete frozen
`requirements.txt` export has been removed; `pyproject.toml` and `uv.lock` are the
authoritative dependency inputs. Dependabot proposes weekly grouped updates for the
Python lock graph and GitHub Actions; CI and a locked-graph vulnerability audit are
the acceptance gates rather than automatic merging.

On 2026-08-20, after adding explicit new-database initialization, the complete suite
passed in the current project environment: **295 passed**. Black check-only mode
also passed. Codex must not run Flake8 autonomously; human maintainers may run it
separately before release. Agent validation is limited to tests, Black check-only,
diff checks, and task-specific verification.

On 2026-08-20, the completed explicit-upgrade implementation was also verified
against a temporary byte-identical copy of the read-only local snapshot described
above. Upgrade from current pre-version-metadata to schema version 1 succeeded. All
334 graves and distinct memorial IDs remained, and hashes of every existing table's
ordered row values were unchanged. The upgrade fabricated no observations, aliases,
alias observations, research tasks, detail levels, or fetch timestamps. SQLite
integrity remained `ok`, and the foreign-key check returned no violations.

The verified backup retained the pre-metadata schema and identical logical row
values. Its file checksum differed because SQLite's backup API may create a
different consistent page image; byte identity is not required for logical backup
identity. The original source checksum remained
`affb436218b5ba2b7ac13448b12f6bddfd5fc99ff9ed21bf9c2a14d8360c678c`
before and after verification.

`many_graves.db` remains ignored mutable user data and must not be committed. It is
neither a test fixture nor a stable project input. Repeatable automated migration
tests must continue to use generated or deliberately sanitized historical fixtures.

## Researcher CLI structure

The default help surface now separates three concerns: existing acquisition
commands, `work` for ordinary person-at-a-time research, and `admin` for advanced
maintenance and diagnostics. The top-level `use` command selects the default
research database without introducing a general configuration namespace. All
database-aware CLI commands share the precedence `--db`, `GRAVER_DB`, saved
selection, then `graves.db`; invalid environment or saved selections fail rather
than silently falling through. Ordinary task display leads with the person and
research state, summarizes provenance, and reveals redirect warnings only when
they affect the selected person. Full acquisition payloads require `--history` or
`--json`. `work next` defaults to `unprocessed`, the least ambiguous actionable
state in the current task model, and uses the queue's deterministic priority,
activity, and memorial-ID ordering.

The root package currently re-exports a broad set of models, exceptions, task and
alias functions, transport infrastructure through `Driver`, and wildcard constants.
The README does not define that collection as a supported Python API. It is therefore
an accidental import surface, not yet a suitable 1.0 facade.

Supported `--json` paths now wrap application-facing compatibility projections in
the documented schema-version-1 envelope: `schema_version`, a stable dotted
`command` identifier, and command-specific `data`. The envelope is deterministic,
keeps subject UUIDs and private SQL structures out of the CLI, and permits additive
optional fields within version 1. Runtime JSON errors are not yet a documented
contract; syntax and operational failures retain nonzero exits and human-readable
standard-error diagnostics. The 1.0 decision uses exit status 1 for operational
failure and 2 for invalid usage rather than introducing a partial JSON error schema.
The removed hidden compatibility commands are not part of the supported contract.

No desktop GUI currently exists. Compatibility modules still contain a mixture of
persistence-shaped dictionaries and SQLite-oriented details, but the package root no
longer re-exports them. An internal synchronous
`ResearchService` and the private subject-task repository now own typed queue, list,
show, update, and one-person enrichment workflows; the visible `work` adapter uses
that service, while existing root functions remain compatibility projections. The
service enforces approval and alias preconditions before injected acquisition and
maps success, redirect, and recorded failure outcomes to typed results or errors;
existing acquisition persistence helpers remain internal compatibility boundaries.
The documented pre-1.0 typed boundary exists at `graver.application`, with
contract-tested `__all__` exports and no CLI, transport, or SQLite implementation
types. The package root deliberately exports no application symbols, so clients must
choose that supported boundary explicitly. The synchronous workspace, optimistic task concurrency, toolkit-neutral
progress events, and cooperative cancellation token are implemented. No desktop GUI
or toolkit integration has been implemented.

The approved target is a separate installable desktop component, with PyQt6 as the
leading but not mandated toolkit candidate, depending only on graver's documented
public application boundary and later workspace facade. In that target design,
SQLite connections and schema
details remain internal, connections are scoped per operation or unit of work and
never shared across GUI threads, and CLI and GUI remain peer adapters. Final frozen
1.0 names and the complete service surface remain planned work.
The completed researcher tutorial supplies a useful behavioral acceptance workflow
for future CLI/application-API/GUI parity tests.

Provider-governed jobs, authorized imports, scheduling adapters, policy snapshots,
request budgets, durable checkpoints, and immutable attempt history are approved
planning concepts only. No such service or public command currently exists. The
canonical [access and acquisition policy](access-policy.md) now governs
project-maintained acquisition behavior and accepted contributions. The
planned policy keeps unattended Find a Grave enrichment disabled without written
permission, an approved API, an authorized export, or another documented provider
mechanism permitting it. Rate limits, jitter, backoff, resumability, quiet hours,
and budgets are operational safeguards only and do not create authorization or
override provider terms, policies, controls, or instructions.

## Packaging, CI, and release status

- Package version `0.1.0` and Python support metadata are normalized for Python
  3.11 through 3.14. Commitizen is no longer a dependency.
- GitHub Actions uses uv for locked installation, offline tests, Black, lock
  consistency, wheel construction, and Python 3.11-through-3.14 validation on
  Ubuntu, with Python 3.14 coverage on macOS and Windows. One dedicated Ubuntu
  Python 3.14 job measures branch coverage, enforces the measured 90% non-regression
  floor, writes Cobertura XML, and publishes it to Coveralls. The 2026-08-22 local
  baseline was 91% across 2,090 statements and 564 branches with 340 passing tests.
  GitHub's CI run for commit `b3f780a` completed successfully after the coverage
  workflow was introduced.
- Conventional Commit pull-request titles and squash merging provide commit
  hygiene. Release Please is configured as the sole changelog/version/tag/GitHub
  Release preparation tool, but remains manually triggered before the 1.0 release
  gates are satisfied.
- `CHANGELOG.md`, `CONTRIBUTING.md`, and `SECURITY.md` establish the release-note,
  contribution, and private-reporting practices. No release tags exist yet.

The baseline coverage run also reported numerous unclosed-SQLite
`ResourceWarning`s. That lifecycle finding was resolved on 2026-08-23 with a shared
internal connection factory that preserves transaction semantics and closes on
context exit, including exception paths. Focused commit/rollback tests protect the
boundary, and pytest now treats SQLite resource warnings and unraisable finalizer
warnings as errors rather than suppressing them.

The 2026-08-23 Windows/Python 3.14 lane passed all 340 tests but took 9m28s inside
pytest. Its slow-test report showed that fixture setup—not dependency installation
or individual assertions—dominated the run. The autouse isolation fixture was
constructing a complete SQLite schema for every test, and database tests could
construct another. Test isolation now uses one session-built, empty current-schema
template copied to a distinct pytest-managed path for each test. The general
database fixture no longer uses an undeleted `NamedTemporaryFile` or directly
mutates the process environment. Tests continue to receive independent databases;
the optimization does not share mutable SQLite state. The protected Windows rerun
completed pytest in 63.34s and the whole required lane in 1m24s, down from 9m28s
and 9m51s respectively.

## Approved pre-1.0 direction

Keep the existing scraper and its `graves` table as the **Find a Grave acquisition component**. The additive `cemeteries`, `memorial_observations`, and `research_tasks` layer now provides provenance and a practical queue.

The task-oriented CLI, explicit database lifecycle, schema-v2 subject ownership,
additive schema-v4 offline evidence structures, and versioned successful-result JSON
envelopes and CLI cleanup are complete, but broad exports, dependency boundaries,
and accidental internal APIs must not be frozen as the 1.0
contract. Before beginning FamilySearch work, follow the ordered pre-1.0 roadmap in
`docs/project-context.md`. The subject-oriented application service now provides
typed task queries, updates, summaries, records, details, queue requests/results,
one-person enrichment results, and workflow errors. Every visible `work` command
uses that boundary while legacy dictionary- and tuple-returning functions remain
compatibility projections. The internal offline evidence-assessment vertical slice
is implemented without a public CLI or live provider. The first professional review
gate R2 attempt did not pass; its decision-safety and citation-traceability
corrections are implemented. Two focused re-reviews verified evidence-selection
fidelity and negative-search reproducibility, so R2 passes; the public workspace
facade remains unfrozen for architectural work rather than because of an open R2
blocker.
`graver init [DATABASE]` now
creates a new database with the current schema and selects it as the saved default.
With no argument it creates
`./graves.db`; with an argument it uses the named path. It refuses to overwrite an
existing filesystem entry, requires an existing parent directory, leaves the prior
selection untouched on failure, and cleans up only its own newly created partial
file after schema or validation failure. A configuration-write failure preserves
the valid initialized database without claiming it was selected.

Keep runtime research databases ignored. Do not commit `graves.db` or
`many_graves.db` as samples. Store schema and migrations in source control, build
ordinary test databases through deterministic project-specific factories, and
reserve committed binary SQLite fixtures for narrowly scoped historical migration
tests. Use hand-authored fictional or public-domain records for genealogical
semantics and edge cases. Use fixed-seed, explicit-locale Faker data behind the
domain factories for volume, variation, pagination, ordering, and performance
tests; assertions must use captured or overridden values rather than depending on
Faker's version-specific output. Historical geography and other meaningful domain
cases remain curated rather than randomly generated. Now that `init` is available,
removing implicit database creation from acquisition commands remains a separate
compatibility change with actionable guidance to use `graver init` or
`graver use DATABASE`.

Schema inspection, new-database initialization, current-schema validation, and
legacy migration are now separate operations. `graver use DATABASE`, selection,
ordinary CLI reads, and API reads remain non-mutating; outdated schemas receive
actionable guidance for `graver admin database upgrade DATABASE`. That explicit
specialist workflow creates a verified backup, performs ordered transactional
migration, and validates the result without automatically restoring over user data.
Normalized acquisition options, hidden-command removal, versioned successful-result
JSON, and `python -m graver` are implemented.

Typer remains the current CLI adapter framework and is retained provisionally
through 1.0 preparation for its nested-command, typed-conversion, generated-help,
completion, and testing value. It is not part of the planned public application API.
The former value-taking Boolean search options now use explicit paired flags and no
longer emit Typer deprecation warnings. Rich-rendered help remains protected by
semantic presentation-boundary tests. The cleaned adapter currently satisfies the
approved Typer retention criteria; recurring unsupported behavior or disproportionate
framework maintenance would still trigger migration to direct Click before 1.0.

The implemented current schema is version 5. The schema-v2 foundation uses
canonical lowercase UUIDv4 `TEXT` subject IDs and adds
`research_subjects`, `subject_memorials`, immutable `research_subject_events`,
subject-keyed `research_tasks`, and immutable `research_task_events`. A subject is an
opaque organizational owner for person-level research, not a genealogical identity
conclusion. Migration mechanically creates one subject for every grave and
associates only that memorial with it, including for graves without tasks. It does
not merge records because of aliases, redirects, names, dates, or similarity.

Schema v3 adds empty-on-migration evidence structures for immutable offline
discovery runs, provider-scoped candidates and snapshots, comparison signals,
concurrency-checked current assessments with immutable history, and immutable
reviewed conclusions. The version-2-to-version-3 migration creates no candidates,
assessments, comparisons, conclusions, relationships, or identity associations.
Schema v4 adds immutable, citation-bearing source observations without fabricating
them during migration. Schema v5 adds optimistic-concurrency task revisions; existing
tasks begin at revision 1 without changing their human-owned values or timestamps.

The association constraint permits at most one current subject per memorial and
structurally permits a subject to have zero or multiple memorials. Multiple-
memorial association is nevertheless a reviewed identity decision and will remain
unavailable until its evidence and correction policy exists. Memorial observations
remain memorial-owned, alias observations remain alias-source-owned, and tasks
become subject-owned. Aliases do not confer subject membership. FamilySearch and
WikiTree candidates are designed as subject-linked hypotheses, while later family work
packets will group subjects rather than replace them.

The version-1-to-version-2 migration preserves the mandatory explicit backup,
ordered transaction, and rollback behavior. It copies each task exactly once with
all fields and timestamps unchanged, leaves existing acquisition and alias data
unchanged, and advances the schema version only within the successful transaction.
It creates only honestly labeled mechanical provenance: subject creation and
association events and one `task_migrated` snapshot for each migrated task. That
snapshot does not reconstruct prior task history. Subsequent task creation and
status, priority, owner, or review-note changes create immutable task events; no-op
updates do not. Acquisition completion and failed or redirected attempts also
retain accurately labeled task activity. Subject and task events retain distinct
meanings.

Ordinary CLI output keeps subject UUIDs internal and preserves memorial IDs as
researcher lookup keys. The lowest associated memorial ID is only a deterministic
temporary display fallback where no reviewed preferred memorial exists; it is not
canonical identity. Existing pre-1.0 result fields remain compatibility-projected
inside the implemented versioned envelope. Merge, split, manual association or
reassociation, preferred memorial selection, and live external-provider adapters
remain explicitly deferred.

The initial public application-service boundary is implemented at
`graver.application`. It explicitly exports typed database lifecycle, research, and
evidence services while excluding `Driver`, transport objects, CLI frameworks, and
SQLite types. Import-contract tests, bounded mypy enforcement, Google-convention
docstring coverage, a developer API guide, and installed-wheel import verification
protect that boundary. Persistence rows and SQL remain private to repository/service
implementations. The first synchronous workspace composition is now implemented at
`graver.application.open_workspace`: it accepts an explicit current database,
exposes typed database inspection plus work list, show, idempotent queue, and
concurrency-safe update operations, owns no long-lived connection, and performs no
CLI configuration lookup. Meaningful task updates increment a revision; stale writes
raise a typed `StaleResearchTask` without changing newer state. The workspace also
exposes one-person enrichment with synchronous neutral progress events and
cooperative cancellation before retrieval and persistence. Its public injection
seam accepts immutable `MemorialDetailInput` values and separately labeled
`DisplayedRelationshipInput` observations rather than the legacy parser model.
Evidence remains available through the supported lower-level `EvidenceService`;
workspace evidence composition and the final 1.0 surface freeze remain pending the
RC-readiness contract audit.

The researcher-directed summary `search` command delegates to
`workspace.acquisition.search()` using a typed provider-specific request. The
service owns explicit database persistence and returns an immutable receipt with
source, memorial identifiers, new/existing counts, appended-observation count, and
field-level before/after changes to the current displayed representation. The CLI
renders the same receipt in researcher language. Search does not queue tasks, infer
correctness, or claim full-page acquisition. Full-record retrieval is limited to
the typed, explicitly approved one-person enrichment service. The legacy direct-URL
and unattended file-loop commands were removed rather than promoted into the public
application API.

Supported failures now share `ApplicationError` with a stable machine-readable
`code`, safe normalized `summary`, and immutable structured `context`. Existing
specific domain exception names remain available. The workspace translates locked
or busy SQLite failures to `DatabaseBusy` and other operation failures to
`DatabaseOperationError` without exposing raw SQLite messages. Its connection-free
composition is exercised concurrently from multiple worker threads; every call owns
and closes its connection in the calling thread.

The dedicated **API hygiene and documentation** milestone is complete: explicit
imports, a deliberately empty package-root export surface, typed graver-owned
results and exceptions, bounded mypy/docstring gates, offline developer guidance,
canonical-document indexing, and installed-wheel consumer validation are
implemented. Typer, Rich, SQLite connections and rows, SQL helpers, parsers,
Requests objects, `Driver`, and transport implementation types remain outside the
boundary as intended.

The final audit corroborated dependency use through direct imports, tests, the
locked graph, exports, and compatibility responsibilities. No runtime dependency
was removable without deleting active behavior. One unreachable private subject
lookup helper and inert scaffolding were removed; research-data migrations and the
active internal compatibility persistence seams were retained. Maintenance scripts
now participate in both local and CI formatting and lint checks.

Ruff now enforces Google-convention public docstring coverage, and mypy enforces the
listed application-facing modules through deterministic local, pre-commit, and CI
commands. The `deadcode` package was removed after its AST visitor failed on
supported Python 3.14; unused-code decisions require corroborating repository,
tests, coverage, exports, and compatibility evidence instead. Top-level canonical
documents are required to be discoverable from the docs index, and all local
Markdown links remain validated. Optimistic task concurrency is implemented. The
installed-wheel consumer verifies workspace creation and
inspection, typed summary and full-record injection, task queueing and meaningful
updates, stale-write rejection, progress, cancellation after retrieval but before
persistence, immutable boundary values and errors, retained observations, and
successful enrichment without private imports or provider requests. It also invokes
the supported offline evidence service for citation-bearing observation, candidate
discovery, comparison, and review ordering while confirming that no conclusion is
created automatically. The researcher tutorial remains separate from this developer
API reference.

Before the release candidate, the planned facade must define typed requests,
results, exceptions, progress, cancellation, threading, transaction ownership,
stale-update handling, deterministic ordering, identifier and enum policies,
injectable transport and nondeterminism, logging, supported imports, and public
documentation. The separate top-level consumer spike now validates the implemented
workspace contract against the built wheel; it is not a production GUI. Production
GUI work follows graver 1.0 and begins with the stable workspace/work-queue vertical
slice before expanding alongside FamilySearch, reviewed identity, WikiTree, and
family-work services.

The accepted
[evidence assessment and identity conclusion architecture](evidence-assessment-architecture.md)
is now implemented as an internal, completely offline vertical slice using curated
FamilySearch-shaped fixtures. The current schema preserves immutable discovery runs and
candidate snapshots, assertion-level comparison signals, explainable review
ordering, concurrency-checked assessments, reproducible negative searches,
unresolved questions, citation-bearing source observations, and immutable
superseding conclusions. Conclusions require inspectable same-subject evidence
references, and the R2 adapter requires authored analysis and explicit treatment of
material conflicts before same-person supersession. It performs no
provider request, adds no public persistence-shaped CLI, creates no automatic
identity association, and cannot accept an identity automatically.

The first R1 professional review on 23 August 2026 did not pass. A focused
independent re-review verified all seven semantic and provenance corrections with
no new blockers and passed R1. The internal persistence and application-service
slice now implements that accepted contract. A disposable, loopback-only browser
adapter backed by the real evidence service is available for the moderated R2
workflow; it is not installed product functionality, a production GUI, or a public
API. The first R2 review and first focused re-review are recorded as blocked. A final
focused professional verification confirmed both remaining corrections with no new
blockers, so R2 passes.

The first focused re-review remained blocked: unresolved conclusions substituted a
candidate snapshot for the researcher's selected source observation, and the saved
negative-search display omitted date, variants, and method. The adapter now retains
the exact selected source observation for unresolved conclusions and visibly
restores all three negative-search fields. The final narrow re-review verified both
behaviors and introduced no new blocker.

The typed application boundary and researcher-directed acquisition have been
validated, and the provider gate now defers public import, job, and scheduler APIs
beyond rc1. Authorized structured-data import may later provide a scalable path
without scraping, but only after a concrete workflow passes its source and
authorization gates. Any future live background runner remains provider-gated,
single-request by default, budgeted, resumable, fail-closed on access challenges,
and shared by CLI and GUI through the application service. A future scheduler would
invoke bounded work and exit rather than requiring a permanent daemon at first.
These are deferred architectural constraints, not implemented acquisition behavior
or pre-1.0 compatibility promises.

graver currently has no GEDCOM parser, import snapshot, family-relationship model,
GEDCOM comparison service, subject-mapping workflow, or export capability. Current
schema-version-2 subjects and tasks are therefore not yet a family graph. No current
database or CLI behavior should be described as GEDCOM-compatible.

GEDCOM remains an exploratory nice-to-have, not a pre-1.0 release criterion or
active schema/API dependency. Its value will be re-evaluated at the 1.0 release-
candidate review, after the first production GUI work-queue vertical slice has been
road-tested, and when a concrete researcher need emerges. If later approved, work
begins with offline immutable inspection and repeatable comparison using synthetic
or sanitized fixtures. Imported records remain dataset-scoped assertions and cannot
automatically create accepted subject mappings, relationships, facts, or identity
conclusions. Reviewed mappings, relationship workflows, privacy-filtered selective
export, GEDZIP, and broader compatibility remain separately gated possibilities in
the canonical
[GEDCOM integration architecture](gedcom-integration.md).

The planned [source-neutral adapter strategy](source-adapter-strategy.md) now
governs future source expansion. It separates source class, carrier format, access
surface, and workflow role; defines discovery, observation, import, and export
adapter roles; and requires authorization, provenance, privacy, offline-fixture,
and conclusion-safety gates before candidates are scored. No generic evidence
packet, research-log importer, civil-record adapter, census adapter, probate
adapter, or universal source ontology is currently implemented. These are bounded
contract probes or conditional candidates, not current capabilities or 1.0 feature
commitments.

The planned [trust, transparency, and openness architecture](trust-transparency-architecture.md)
records four visible trust layers, computational versus genealogical
reproducibility, rule-version and comparison-trace requirements, invariant evidence
safeguards, future AI provenance, and a minimum independently interpretable audit
projection. Current comparison persistence records original assertion mappings,
normalized values, an algorithm version, numeric ordering contributions, and
plain-language explanations; current typed comparison records do not yet expose the
entire replay context, and no portable audit-bundle specification or independent
validator is implemented. No configurable rule-pack system or rules marketplace is
implemented.

The fictional source-neutral evidence packet passed focused S1 professional review
after correction of item-level provenance, assertion suppliers and dependence,
attributable comparison inputs, material-conflict permanence, self-contained audit
references, genealogical-reproducibility requirements, descriptive open
vocabularies, and ordering-only override constraints. A bounded internal, in-memory
typed packet and validator now exercise those distinctions against the fictional S1
items. An internal projector can now combine existing immutable source-observation,
candidate-snapshot, and comparison-signal domain records with explicit S1 metadata;
it fails when metadata is incomplete, references do not resolve, or a comparison's
claimed captured value differs from its observation. The types are not exported from
`graver.application`, and no packet tables, serializer, public format, replay engine,
provider adapter, or user workflow exists.

For pre-1.0 compatibility, acquisition and write paths still initialize a missing or
empty database with the current schema. They no longer migrate recognized legacy
databases implicitly. Removing that remaining implicit creation behavior is still a
separate roadmap milestone.

The testing-modernization milestone deliberately avoids a large cassette rewrite.
Default socket denial, replay-only recorded contracts, strict marker registration,
sanitization, fixed Faker seeding, isolated temporary database/configuration
fixtures, test-only dependency grouping, and obsolete-test cleanup are implemented.
The suite retains 61 recorded contracts while new parser cases favor curated static
HTML/JSON and new transport cases favor `requests-mock`.

Remaining work is to classify more tests by layer, introduce clearer domain fixture
factories with an explicit locale, evaluate importlib mode for the `src` layout, and
trial VCR.py through pytest-recording on a few representative contracts before
deciding whether to migrate the remaining cassettes or eliminate record/replay
entirely. Branch coverage now measures 94.45% locally against the 90% non-regression
floor; future increases should come only from meaningful behavioral tests.

The implemented `make canary` maintenance probe retrieves the public George
Washington memorial at
`https://www.findagrave.com/memorial/1075/george-washington`. It permits one
top-level request attempt with retries disabled, validates minimum semantic parsing
invariants rather than mutable page content, and classifies results as `compatible`,
`schema_changed`, `access_blocked`, `site_unavailable`, `canary_changed`, or
`probe_error`. `make canary-json` emits the versioned machine-readable result.

The probe is excluded from ordinary tests, pull-request checks, release automation,
cassette recording, and the human CLI. It uses short timeouts, no database writes,
no fixture refresh, no user configuration, and sanitized diagnostics. It is manually
invoked before releases and after material parser or transport changes. It is not
scheduled; current provider terms, robots directives, and automation guidance must
be reviewed before that policy changes. An unclassified live-site or runner failure
does not automatically block an unrelated release. See
[live-canary.md](live-canary.md).

After the offline contract slice and the `1.0.0rc1` validation are complete, an
authorized live FamilySearch adapter may extend the same application services and
`work` surface rather than adding one command per persistence entity. A candidate is
a hypothesis whose assessment state, explainable match signals, supporting and
conflicting evidence, and reasoning can evolve during research. Candidate ranking
is decision support, not proof confidence. A reviewed identity conclusion must come
after the supporting research and explicitly record an accepted, rejected,
unresolved, or withdrawn result.

Candidate discovery must be safely repeatable for the same memorial at any time so
that later FamilySearch corrections, newly attached sources, repaired family
relationships, and new candidate possibilities can be observed. Each execution
should create an immutable search-run record and timestamped candidate snapshots.
Re-running discovery must preserve reviewer notes, research status, assessments,
and conclusions; it should highlight new or materially changed candidates for
review rather than silently resetting decisions. Candidates absent from a later
result set must be retained and marked absent from that run rather than deleted.

The FamilySearch implementation must preserve a rich internal model without exposing
every search-run, snapshot, comparison, or assessment operation as a separate
top-level CLI command. The primary user action should be a simple task such as
refreshing candidates for the current person, with new possibilities, material
changes, discrepancies, and required decisions presented contextually.

Find a Grave aliases remain platform-redirection provenance only. They may inform
FamilySearch candidate research but do not automatically assert genealogical
identity. WikiTree integration, relationship reconciliation, and work packets
should follow reviewed identity research. Find a Grave unattended full-record or
cemetery-wide acquisition remains disabled unless the documented authorization gate
is satisfied.

## Before implementation

- Use read-only snapshots of `many_graves.db` only for explicitly authorized manual
  representative checks while seeking additional cemeteries to assess
  cross-cemetery and duplicate behavior; use generated or sanitized fixtures for
  repeatable automated tests.
- Treat local `graves.db` and `many_graves.db` files as ignored researcher data, not
  repository samples or fixtures.
- Maintain the reproducible environment defined by `pyproject.toml` and `uv.lock`.
- Confirm current platform terms, rate limits, authentication, and API policies before any scaled retrieval or third-party integration.
