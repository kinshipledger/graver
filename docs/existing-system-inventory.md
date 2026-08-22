# Existing system inventory: `graver`

Inspection dates: 2026-08-11; refreshed 2026-08-21

## What is present

`src/graver/` is an independently versioned Python package named `graver`. Its
project and Commitizen metadata currently use `v0.1.0`, while canonical prose refers
to `0.1.0`. It is a Find a Grave scraper/library with a Typer command-line
interface, SQLite persistence, and fixture-backed tests.

The current `develop` architecture includes `MemorialSummary`, immutable
acquisitions, the durable queue, explicit person-at-a-time task handling,
progressive-disclosure commands, alias provenance, and default-database selection.
Schema version 2 adds stable research subjects, subject-owned tasks, immutable
subject/task events, and memorial-ID compatibility for existing researcher workflows.

The pre-1.0 compatibility audit found no local `main` branch. `origin/HEAD` points
to `origin/master`; `master` contains the older scraper-era production state, while
`develop` contains the current acquisition, provenance, queue, alias, progressive-
disclosure CLI, and default-database architecture. No release tags or changelog are
present. These are current repository facts, not evidence that the planned branch,
tag, or release changes have occurred.

## Current behavior

### Commands

- `scrape-file <input-file> [--db DATABASE]` accepts memorial IDs or memorial URLs, de-duplicates IDs, retrieves full memorial pages, and saves them to SQLite.
- `scrape-url <url> [--db DATABASE]` retrieves and saves one full memorial.
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
- `admin aliases list`, `show`, `record`, and `retract` expose specialist Find a Grave redirect maintenance and immutable history without moving tasks or grave data.
- The earlier top-level task and alias commands remain functional as hidden compatibility aliases. They preserve existing arguments, output, and exit behavior but do not compete with ordinary workflows in root help.
- The console entry point is `graver = graver.cli:app`. Direct execution through
  `python -m graver.cli` is broken, and no `graver.__main__` module currently
  provides `python -m graver`.

Graver currently has no durable background-job engine, scheduler, or unattended
bulk-enrichment mode. Full memorial enrichment is intentionally person-at-a-time and
requires the current task approval. Search-summary acquisition does not authorize or
enable mass full-page enrichment. Provider permission for unattended Find a Grave
acquisition has not been established.

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
interpreters, and CAPTCHA-service integrations. Graver does not configure those
features explicitly, but default scraper construction enables automatic challenge
handling.

Current Graver tests require only a Requests-compatible injectable session and
ordinary retry, error, response, and parser behavior. They do not demonstrate a
need for challenge handling, proxy rotation, browser impersonation, CAPTCHA support,
fingerprint manipulation, or any other unique package capability. The installed
metadata labels the package production/stable and lists Python classifiers through
3.9. Because the audit made no network requests, it did not establish the package's
current maintenance or security-advisory status.

The approved audit result, **remove**, is now implemented. `cloudscraper25` is no
longer a runtime dependency or production/test import. Requests is an explicit
runtime dependency behind a small Graver-owned transport protocol and response
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
legacy rows remain unclassified because Graver does not infer their acquisition
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
- Family relationships, source evidence, FamilySearch matches, WikiTree matches, identity conclusions, and cemetery-tag decisions are not modeled.
- Legacy rows are deliberately not assigned a `detail_level` during migration because their acquisition level cannot be inferred reliably. They become classified when subsequently saved through the summary or full persistence path.
- Legacy rows deliberately do not receive fabricated observation records during migration because their original timestamp and exact observed payload are unknown.
- Some acquisition commands still reflect scraper implementation terminology. Their information architecture is intentionally deferred; this milestone changes only the research and alias-maintenance surfaces.
- `research_tasks` is now keyed by `subject_id`; `subject_memorials` keeps existing
  memorial-ID lookup convenient. The schema can represent a subject with zero or
  multiple memorials, but reviewed association, reassociation, merge, split,
  preferred-memorial selection, people without memorials, and family work packets
  remain unavailable until their evidence and correction policies are implemented.

## Test and environment status

The repository has a substantial fixture-backed test suite covering memorial parsing, search filters, cemetery pagination, merged/removed memorial handling, CLI behavior, SQLite persistence, additive migration, summary/full overwrite protection, atomic observation creation, observation immutability, foreign-key constraints, and queue idempotency.

The inherited suite mixes several responsibilities that should now be separated.
Betamax cassettes provide valuable real Find a Grave contract examples, but ordinary
execution is not explicitly locked to replay-only, Betamax warnings are globally
suppressed, and the project is locked to Betamax 0.8.1. Generic Betamax and Faker
smoke tests, incomplete or commented test bodies, time-seeded Faker providers,
`delete=False` temporary databases, direct environment mutation, and test tools in
runtime dependencies are legacy test-infrastructure debt rather than intentional
long-term design. `requests-mock` is already available and is the preferred boundary
for method, parameter, retry, and error-path tests.

Runtime dependencies currently include pytest, Faker, Betamax, and a typing package,
and `dill` has no source usage found by the audit. Test and typing tools have not yet
been fully separated from application dependencies.

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

Current `--json` paths serialize raw API dictionaries whose fields closely follow
SQLite rows and internal alias-resolution structures. Those outputs are deterministic
and useful for current tests, but they are not documented, versioned, command-specific
1.0 schemas. The hidden compatibility commands remain implemented and tested today;
their approved pre-1.0 removal has not yet occurred.

No desktop GUI currently exists. Current CLI and Python boundaries still expose a
mixture of persistence-shaped dictionaries, root-level functions, SQLite-oriented
details, and CLI-coupled presentation behavior. The broad root exports described
above are not a stable 1.0 application API. No workspace facade, typed public result
layer, neutral progress or cancellation protocol, optimistic concurrency control,
or GUI integration has been implemented.

The approved target is a separate installable desktop component, with PyQt6 as the
leading but not mandated toolkit candidate, depending only on Graver's documented
public application facade. In that target design, SQLite connections and schema
details remain internal, connections are scoped per operation or unit of work and
never shared across GUI threads, and CLI and GUI remain peer adapters. The facade,
its exact names, and its typed contracts are planned work, not current behavior.
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

- Both the project version and Commitizen version are `v0.1.0`; normalized package
  metadata must not include the tag-style `v` prefix.
- `requires-python` is `>=3.10`, but classifiers still claim Python 3.8 and 3.9 as
  well as 3.10 through 3.14.
- The GitHub Actions workflow still installs Poetry, keys its cache from
  `poetry.lock`, and tests Python 3.8 through 3.12. The repository has moved to uv,
  has no `poetry.lock`, and does not validate the approved Python 3.11-through-3.14
  release matrix.
- No changelog, release workflow, release tags, or locally visible release history
  defines a current public compatibility contract.

## Approved pre-1.0 direction

Keep the existing scraper and its `graves` table as the **Find a Grave acquisition component**. The additive `cemeteries`, `memorial_observations`, and `research_tasks` layer now provides provenance and a practical queue.

The task-oriented CLI, explicit database lifecycle, and schema-v2 subject ownership
are complete, but raw JSON, broad exports, compatibility aliases,
dependency boundaries, and stale CI must not be frozen as the 1.0 contract. Before
beginning FamilySearch work, follow the ordered pre-1.0 roadmap in
`docs/project-context.md`; the next planned work is the subject-oriented internal
repository/application-service refactor, followed by the dedicated API-hygiene and
documentation milestone before the public workspace facade is frozen.
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
Versioned JSON, normalized acquisition options, hidden-command removal, and
`python -m graver` are not implemented yet.

The implemented current schema is version 2. It uses canonical lowercase UUIDv4
`TEXT` subject IDs and adds
`research_subjects`, `subject_memorials`, immutable `research_subject_events`,
subject-keyed `research_tasks`, and immutable `research_task_events`. A subject is an
opaque organizational owner for person-level research, not a genealogical identity
conclusion. Migration mechanically creates one subject for every grave and
associates only that memorial with it, including for graves without tasks. It does
not merge records because of aliases, redirects, names, dates, or similarity.

The association constraint permits at most one current subject per memorial and
structurally permits a subject to have zero or multiple memorials. Multiple-
memorial association is nevertheless a reviewed identity decision and will remain
unavailable until its evidence and correction policy exists. Memorial observations
remain memorial-owned, alias observations remain alias-source-owned, and tasks
become subject-owned. Aliases do not confer subject membership. FamilySearch and
WikiTree candidates will be subject-linked hypotheses, while later family work
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
canonical identity. Existing pre-1.0 JSON will be compatibility-projected until the
separate versioned-envelope milestone. Merge, split, manual association or
reassociation, preferred memorial selection, external-platform persistence,
versioned envelopes, and hidden-command removal remain explicitly deferred.

The public application-service facade is now planned alongside the subject-oriented
API work rather than as a late packaging-only cleanup. New subject operations should
use internal repositories and typed application services, keep persistence rows and
SQL private, and move the `work` CLI toward the same operations future GUI clients
will call. A synchronous workspace opened from an explicit database path is the
leading design because it offers cohesive ownership and discoverability without a
long-lived connection; the CLI, not the workspace, continues to resolve database
configuration and precedence.

After that planned subject-oriented API/CLI service refactor, a dedicated **API
hygiene and documentation** milestone will run before the workspace facade is
frozen. It is planned work, not current behavior, and remains separate from the
completed version-2 migration. It will establish explicit public imports and
`__all__` exports, complete
public type contracts and Graver-owned results and exceptions, and useful Google-
style docstrings across the supported boundary. Typer, Rich, SQLite connections and
rows, SQL helpers, parsers, Requests objects, `Driver`, and transport implementation
types will remain outside the public facade.

That milestone will review broad root and wildcard exports, hidden commands,
commented-out or empty test scaffolding, obsolete compatibility helpers, and unused
dependencies. Removal requires corroborating repository, test, coverage or static-
analysis, import/export, and compatibility evidence rather than one linter warning;
research-data migration paths remain protected. Compatibility-sensitive removals
receive release notes. Separate commits will cover export/type boundaries,
evidenced dead-code and dependency removal, Google-style docstrings and installed-
wheel API examples, bounded CI enforcement, and migration/release notes.

Tools for docstring style and presence, typing, unused-code detection, and
documentation build/link validation remain to be evaluated and documented before
becoming release gates. Enforcement will use bounded deterministic commands scoped
initially to the public API and changed files where appropriate, without recreating
the previous Flake8 loop. Acceptance requires tested public imports, complete useful
public docstrings and types, no third-party or implementation-type leakage, offline
installed-wheel examples for workspace opening, work inspection, concurrency-safe
task updates, and injected acquisition, evidenced removals, release notes, and green
reproducible checks. The researcher tutorial remains separate from this developer
API reference.

Before the release candidate, the planned facade must define typed requests,
results, exceptions, progress, cancellation, threading, transaction ownership,
stale-update handling, deterministic ordering, identifier and enum policies,
injectable transport and nondeterminism, logging, supported imports, and public
documentation. A separate top-level consumer spike against the built wheel will
validate those contracts before `1.0.0rc1`; it is not a production GUI. Production
GUI work follows Graver 1.0 and begins with the stable workspace/work-queue vertical
slice before expanding alongside FamilySearch, reviewed identity, WikiTree, and
family-work services.

After the typed application boundary and researcher-directed acquisition have been
validated, provider authorization gates and import-first/provider-neutral job
abstractions are planned before any public background-job API is frozen. Authorized
structured-data import may provide a scalable path without scraping. Any live
background runner remains provider-gated, single-request by default, budgeted,
resumable, fail-closed on access challenges, and shared by CLI and GUI through the
application service. A scheduler will invoke bounded work and exit rather than
requiring a permanent daemon at first. These are future architectural constraints,
not implemented acquisition behavior.

For pre-1.0 compatibility, acquisition and write paths still initialize a missing or
empty database with the current schema. They no longer migrate recognized legacy
databases implicitly. Removing that remaining implicit creation behavior is still a
separate roadmap milestone.

The planned testing-modernization milestone should avoid a large cassette rewrite.
It will define parser/static-response, mocked-transport,
temporary-database/workflow, and recorded-contract layers. Deny network access by
default; make existing Betamax cases replay-only and explicitly marked; sanitize all
recorded traffic; and require a deliberate maintainer-only refresh process. Move new
parser cases to curated HTML/JSON fixtures and new transport cases to
`requests-mock`. Trial VCR.py through pytest-recording on a few representative
contracts before deciding whether to migrate the remaining cassettes or eliminate
record/replay entirely.

Replace time-based Faker and Python randomness with fixed, reported seeds and an
explicit locale. Move all test-only packages out of runtime dependencies. Replace
leaking temporary files and global environment mutation with pytest-managed
lifecycle fixtures. Remove generic tool smoke tests, empty tests, and commented-out
bodies. Register strict `unit`, `integration`, `recorded`, and `slow` markers;
evaluate importlib mode for the `src` layout; and establish branch-coverage reporting
and a modest non-regression threshold from the measured baseline rather than an
arbitrary target.

Add a distinct live-contract maintenance probe after the offline test boundaries are
established. It should retrieve the public George Washington memorial at
`https://www.findagrave.com/memorial/1075/george-washington`, execute one tightly
constrained summary search, and optionally check one cemetery page, for a total of no
more than two or three requests per run. It should validate minimum semantic parsing
invariants rather than mutable content and classify results as `compatible`,
`schema_changed`, `access_blocked`, `site_unavailable`, `canary_changed`, or
`probe_error`.

Mark the probe `live_contract` and exclude it from ordinary tests, pull-request
checks, cassette recording, and the human CLI. It must use short timeouts, minimal
retries, no database writes, no fixture refresh, and sanitized diagnostics. Start
with manual pre-release and parser-change execution from a normal developer
environment; trial a weekly scheduled runner only if Cloudflare does not make its
signal unreliable. Confirm current Find a Grave terms, robots directives, and
automation guidance before scheduling it. Do not let an unclassified live-site or
runner failure automatically block an unrelated release.

After the pre-1.0 sequence and the `1.0.0rc1` validation are complete, FamilySearch
workflows should extend the same `work` surface rather than adding one command per
persistence entity. A candidate is a hypothesis whose status, match signals,
supporting and conflicting evidence, confidence, and reasoning can evolve during
research. A
reviewed identity conclusion must come afterward and explicitly record an
accepted, rejected, or unresolved result. It must not be required before the
FamilySearch research needed to support it.

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
- Maintain the reproducible environment defined by `pyproject.toml`, `requirements.txt`, and `uv.lock`.
- Confirm current platform terms, rate limits, authentication, and API policies before any scaled retrieval or third-party integration.
