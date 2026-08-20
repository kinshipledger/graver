# Existing system inventory: `graver`

Inspection dates: 2026-08-11; refreshed 2026-08-19

## What is present

`src/graver/` is an independently versioned Python package named `graver` (version `0.1.0`). It is a Find a Grave scraper/library with a Typer command-line interface, a SQLite output path, fixture-backed tests, and a copied local virtual environment.

The refreshed inspection began from `develop` after commit `b2670a0` (`feat: add
person-at-a-time research workflow`) with two preserved uncommitted task-interface
fixes. `MemorialSummary`, immutable acquisitions, the durable queue, and explicit
person-at-a-time task handling are integrated and tested.

## Current behavior

### Commands

- `scrape-file <input-file> [--db DATABASE]` accepts memorial IDs or memorial URLs, de-duplicates IDs, retrieves full memorial pages, and saves them to SQLite.
- `scrape-url <url> [--db DATABASE]` retrieves and saves one full memorial.
- `search` queries Find a Grave's memorial search, including a cemetery ID option, name/date/location filters, and pagination. Search results are represented as `MemorialSummary` objects and persisted to the selected SQLite database before being emitted to logs.
- `use DATABASE`, `use --show`, and `use --clear` manage one researcher-facing default database selection without creating, migrating, or deleting databases. Explicit `--db` and `GRAVER_DB` remain higher-precedence temporary selections.
- `work queue`, `work list`, `work next`, `work show`, and `work mark` provide a person-centered, network-free research workflow. `work enrich` retrieves exactly one explicitly approved memorial.
- `admin aliases list`, `show`, `record`, and `retract` expose specialist Find a Grave redirect maintenance and immutable history without moving tasks or grave data.
- The earlier top-level task and alias commands remain functional as hidden compatibility aliases. They preserve existing arguments, output, and exit behavior but do not compete with ordinary workflows in root help.

### Retrieval and parsing

- A reusable requests session supplies a browser-like User-Agent.
- Retry behavior covers HTTP 500, 502, 503, 504, and 599 (three retries by default, with a 500 ms delay).
- Full memorial parsing handles canonical URLs, ordinary 404s, removed memorials, and merged memorial redirects.
- Cemetery search supports counting results and follows 20-result pages.
- The test suite uses recorded HTTP cassettes rather than live Find a Grave requests.

## Current SQLite databases

The local `src/graver/graves.db` is an ignored runtime byproduct of early human
command-line development, not a supported sample or repository fixture. The
ignored, untracked representative `src/graver/many_graves.db` contains 334 distinct
memorials discovered from a Morris Hill Cemetery search (Find a Grave cemetery ID
`2181249`). It has one table:

```text
graves
```

`graves.memorial_id` is the primary key. The current code can store the memorial URL, parsed name components, Find a Grave flags, birth/death values and places, memorial type, cemetery ID, burial place, plot, coordinates, biography presence, and the acquisition metadata `detail_level`, `summary_fetched_at`, and `full_fetched_at`. The local `many_graves.db` predates those three acquisition columns and the research tables; database initialization adds them safely to a working copy when it is opened through the application.

The 334 representative rows are intentionally search summaries, not full memorial-page scrapes. All contain an ID, URL, name, birth/death display values, memorial type, cemetery ID, and burial place; four contain plot text. None contains birth/death places, coordinates, or biography status. After migration, their acquisition fields remain null until they are seen again because the code deliberately avoids guessing the origin of legacy rows. This supports staged enrichment rather than scraping every individual page immediately.

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

- No `cemeteries` table exists in the supplied database, even though the code can create one; cemetery metadata is not written by the existing commands.
- `graves` remains a current-state acquisition table rather than immutable observation history. The new upserts protect richer data but do not retain earlier versions of changed source values.
- A small additive migration mechanism, fetch timestamps, successful and failed acquisition observations, foreign keys, supporting indexes, initial work-queue state, and alias provenance now exist.
- Family relationships, source evidence, FamilySearch matches, WikiTree matches, identity conclusions, and cemetery-tag decisions are not modeled.
- Legacy rows are deliberately not assigned a `detail_level` during migration because their acquisition level cannot be inferred reliably. They become classified when subsequently saved through the summary or full persistence path.
- Legacy rows deliberately do not receive fabricated observation records during migration because their original timestamp and exact observed payload are unknown.
- Some acquisition commands still reflect scraper implementation terminology. Their information architecture is intentionally deferred; this milestone changes only the research and alias-maintenance surfaces.

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

On 2026-08-20, after adding the progressive-disclosure CLI, the complete suite
passed in the current project environment: **246 passed**. Black check-only mode
also passed. Codex must not run Flake8 autonomously; human maintainers may run it
separately before release. Agent validation is limited to tests, Black check-only,
diff checks, and task-specific verification. A migration and CLI check on a
temporary copy of `many_graves.db` preserved all 334 rows and distinct
memorial IDs, queued 334 tasks idempotently, exercised the researcher workflow,
and fabricated zero aliases or acquisition observations. SQLite integrity and
foreign-key checks passed. The original database checksum remained
`7b952c7f1202c7f3b8260edc4b466c6f334052c801ba7596ebfa23bea912a3cc`.

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

The internal Python API remains complete. Hidden compatibility commands are a
deliberate automation policy rather than deprecated behavior; they can be reviewed
after downstream users have had an explicit migration window.

## Recommended smallest next change

Keep the existing scraper and its `graves` table as the **Find a Grave acquisition component**. The additive `cemeteries`, `memorial_observations`, and `research_tasks` layer now provides provenance and a practical queue.

The task-oriented CLI foundation is complete. Before beginning FamilySearch work,
complete the explicit research-database lifecycle. Add `graver init [DATABASE]` to
create a new database with the current schema and select it as the saved default.
With no argument it creates `./graves.db`; with an argument it uses the named path.
It must refuse to overwrite an existing file, require an existing parent directory,
leave the prior selection untouched on failure, clean up only a newly created
partial file, and report `Initialized and selected research database: PATH` after
successful initialization and validation.

Keep runtime research databases ignored. Do not commit `graves.db` or
`many_graves.db` as samples. Store schema and migrations in source control, build
ordinary test databases through deterministic project-specific factories, and
reserve committed binary SQLite fixtures for narrowly scoped historical migration
tests. Use hand-authored fictional or public-domain records for genealogical
semantics and edge cases. Use fixed-seed, explicit-locale Faker data behind the
domain factories for volume, variation, pagination, ordering, and performance
tests; assertions must use captured or overridden values rather than depending on
Faker's version-specific output. Historical geography and other meaningful domain
cases remain curated rather than randomly generated. After `init` is available,
remove implicit database creation from acquisition commands as a separate
compatibility change with actionable guidance to use `graver init` or
`graver use DATABASE`.

Modernize the inherited suite within the same milestone without attempting a large
cassette rewrite. Define parser/static-response, mocked-transport,
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

FamilySearch workflows should then extend the same `work` surface rather than
adding one command per persistence entity.

The next milestone should add the FamilySearch candidate-discovery and research
layer. A candidate is a hypothesis whose status, match signals, supporting and
conflicting evidence, confidence, and reasoning can evolve during research. A
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

- Use `many_graves.db` as the initial representative cemetery-search dataset while seeking additional cemeteries to assess cross-cemetery and duplicate behavior.
- Treat local `graves.db` and `many_graves.db` files as ignored researcher data, not
  repository samples or fixtures.
- Maintain the reproducible environment defined by `pyproject.toml`, `requirements.txt`, and `uv.lock`.
- Confirm current platform terms, rate limits, authentication, and API policies before any scaled retrieval or third-party integration.
