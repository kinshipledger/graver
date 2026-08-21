# Existing system inventory: `graver`

Inspection dates: 2026-08-11; refreshed 2026-08-20

## What is present

`src/graver/` is an independently versioned Python package named `graver`. Its
project and Commitizen metadata currently use `v0.1.0`, while canonical prose refers
to `0.1.0`. It is a Find a Grave scraper/library with a Typer command-line
interface, SQLite persistence, and fixture-backed tests.

The current `develop` architecture includes `MemorialSummary`, immutable
acquisitions, the durable queue, explicit person-at-a-time task handling,
progressive-disclosure commands, alias provenance, and default-database selection.

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

### Retrieval and parsing

- A reusable requests session supplies a browser-like User-Agent.
- Retry behavior covers HTTP 500, 502, 503, 504, and 599 (three retries by default, with a 500 ms delay).
- Full memorial parsing handles canonical URLs, ordinary 404s, removed memorials, and merged memorial redirects.
- Cemetery search supports counting results and follows 20-result pages.
- The test suite uses recorded HTTP cassettes rather than live Find a Grave requests.

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

New databases contain application-owned schema metadata at version 1. Read-only
inspection distinguishes the known 0.1 full grave shape, the representative
summary-only legacy shape, structurally current pre-metadata databases, current
versioned databases, future versions, empty databases, unrelated SQLite files, and
unknown or malformed inputs. Required structural evidence is necessary before a
legacy classification is assigned.

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
- A durable, indexed research queue with constrained statuses, priorities, ownership/review fields, and timestamps.
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
- `research_tasks.memorial_id` is currently both the task primary key and a foreign
  key to `graves`. That memorial-centered identity cannot yet represent a researched
  person with multiple memorials, a person without a Find a Grave memorial, or a
  later family-level work packet.

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

The task-oriented CLI foundation and explicit database initialization and migration
are complete, but the current memorial-centered
task identity, raw JSON, broad exports, compatibility aliases,
dependency boundaries, and stale CI must not be frozen as the 1.0 contract. Before
beginning FamilySearch work, follow the ordered pre-1.0 roadmap in
`docs/project-context.md`, beginning with the contract and explicit database
lifecycle. `graver init [DATABASE]` now creates a new database with the current
schema and selects it as the saved default. With no argument it creates
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
Generalized research subjects, versioned JSON,
normalized acquisition options, hidden-command removal, and `python -m graver` are
not implemented yet.

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
should follow reviewed identity research. Do not introduce unattended
cemetery-wide enrichment yet.

## Before implementation

- Use read-only snapshots of `many_graves.db` only for explicitly authorized manual
  representative checks while seeking additional cemeteries to assess
  cross-cemetery and duplicate behavior; use generated or sanitized fixtures for
  repeatable automated tests.
- Treat local `graves.db` and `many_graves.db` files as ignored researcher data, not
  repository samples or fixtures.
- Maintain the reproducible environment defined by `pyproject.toml`, `requirements.txt`, and `uv.lock`.
- Confirm current platform terms, rate limits, authentication, and API policies before any scaled retrieval or third-party integration.
