# Project context

## Resume checkpoint — 2026-08-22

The repository is on the single long-lived `main` branch with only
`https://github.com/mcqueary/graver.git` configured as `origin`. The obsolete
`pirtleshell/scrape-a-grave` upstream remote has been removed. Historical MIT
copyright provenance remains preserved, while the README makes clear that graver is
independently maintained and has no ongoing upstream affiliation.

The implemented foundation includes schema version 2 subject-owned research tasks,
explicit backed-up database upgrades, person-at-a-time acquisition, fail-closed
Requests transport, the researcher tutorial, trunk-based release automation, and a
dedicated branch-coverage CI job. The latest complete local run passed 340 tests and
measured 90.58% branch coverage against a 90% floor. Coveralls reporting, the six
honest README badges, Python 3.11–3.14 CI, Black, locked uv environments, wheel
verification, and Conventional Commit pull-request-title enforcement are current.
GitHub's CI run for the current checkpoint commit `b3f780a` completed successfully.
The coverage run exposed unclosed-SQLite `ResourceWarning`s that remain explicit
testing-lifecycle cleanup work.

The professional-researcher usability baseline and principal architecture response
are now recorded. They establish that candidate discovery, machine ranking,
researcher assessment, and reviewed identity conclusions must remain distinct. The
accepted [evidence assessment architecture](evidence-assessment-architecture.md) is
a pre-facade design gate: its offline vertical slice must validate the domain and
typed result shapes before the public workspace façade is frozen. Live FamilySearch
access and production GUI work remain deferred. The current leading implementation
step remains the subject-oriented repository and application-service refactor,
informed by this evidence contract, followed by the offline slice, API
hygiene/documentation, and the other pre-RC gates. GEDCOM remains a periodically
re-evaluated nice-to-have outside the critical path. No live FamilySearch, WikiTree,
production GUI, background-job, or GEDCOM implementation has begun.

Professional alignment is controlled by the canonical
[researcher review gates](researcher-review-gates.md). R1 blocks candidate/evidence
persistence until the evidence contract has been exercised with a researcher; R2
blocks the public workspace freeze and detailed evidence-GUI design until the
offline workflow has been validated; R3 blocks production-readiness claims and
downstream WikiTree/family workflow expansion until the production evidence
experience passes a repeat of the original professional review.

## Objective

Systematically connect well-researched people to the WikiTree World Tree, beginning with populations discovered from Find a Grave cemeteries.

## Operating model

```text
Find a Grave cemetery
  → scraper
  → SQLite research database
  → FamilySearch candidate discovery and research
  → evidence gathering and candidate comparison
  → reviewed identity conclusion
  → WikiTree candidate matching and relationship reconciliation
  → human review
  → approved WikiTree work or update
  → cemetery tag
```

Find a Grave observations must remain preserved as original provenance. Later research conclusions must be stored separately rather than replacing the original record.

## Identity and family research

Identity is not determined by name alone. FamilySearch research is a primary source of the evidence needed to assess identity. Candidate assessments should combine name variants, dates and places, family members, residences, occupation, military information when relevant, cemetery information, and source evidence.

The central model is an identity triangle:

```text
Find a Grave person ↔ FamilySearch person ↔ WikiTree person
```

Candidate discovery creates a hypothesis, not an identity conclusion. During FamilySearch research, candidate status, match signals, evidence, discrepancies, confidence, and reasoning may evolve. Only after that research should a reviewer explicitly accept the records as the same person, reject the match, or leave it unresolved. Once a person is reliably identified, their parents, spouses, and children can validate the model and identify related cemetery members.

The sequence is therefore:

```text
Find a Grave memorial or alias
  → FamilySearch candidate search
  → candidate hypothesis
  → evidence gathering and comparison
  → identity assessment
  → human review
  → accepted, rejected, or unresolved identity conclusion
  → WikiTree matching
```

A Find a Grave alias records only that the Find a Grave platform redirects one memorial to another. It may inform candidate research, but it neither requires nor automatically creates a genealogical identity conclusion.

The governing evidence contract is documented in
[Evidence assessment and identity conclusion architecture](evidence-assessment-architecture.md).
Machine-generated comparison may order candidates for review, but it is not proof
confidence and cannot create a conclusion. Only an explicit, reasoned, human-reviewed
decision may establish an accepted external identity association.

## Repeatable FamilySearch discovery

FamilySearch is a changing research system. A researcher may correct facts, attach
previously unattached sources, repair family relationships, or otherwise improve a
FamilySearch person through the FamilySearch web interface. Other contributors may
also make relevant changes. Candidate discovery must therefore be safely repeatable
for the same Find a Grave memorial at any time.

Each discovery execution should be retained as an immutable, timestamped search run
with its query inputs and outcome. Candidate data observed during a run should be
stored as a timestamped snapshot rather than overwriting prior observations. A new
run must be able to surface newly available candidates and material changes to
previous candidates, including changed facts, sources, and family attachments.

Re-running discovery must not erase or silently reset research status, reviewer
notes, prior assessments, or identity conclusions. Previously rejected or unresolved
candidates may be reconsidered when new evidence appears, but reopening them must be
an explicit, reviewable action. A candidate not returned by a later search should be
marked as absent from that run, not deleted or treated automatically as disproven.

## Human interface principles

The internal API and database may expose the full research model, but the
human-facing CLI must not mirror every API operation or persistence entity. Its
primary commands should represent recognizable research goals rather than tables,
implementation details, or provenance mechanics.

Use progressive disclosure with three interface layers:

1. Research workflows: a small top-level set for choosing the next person, viewing
   the current research picture, enriching a memorial, refreshing FamilySearch
   candidates, reviewing evidence, and recording a decision.
2. Contextual actions: uncommon choices displayed only when the current person or
   discrepancy requires human judgment.
3. Administrative diagnostics: data repair, detailed provenance inspection, alias
   maintenance, and other specialist operations grouped under an `admin` or `debug`
   namespace, or retained only in the Python API.

Find a Grave aliases are important internally but should normally appear only as a
concise notice when they affect the current research task. Alias chains, reverse
lookups, immutable alias history, and manual corrections should not compete with
ordinary research workflows in the main help surface.

Before exposing a command, determine whether a typical genealogical researcher will
recognize when and why to use it, whether it can be presented contextually inside an
existing workflow, and whether it is primarily diagnostic or administrative. New
FamilySearch functionality should follow the same rule: search runs, snapshots, and
change detection belong in the model, while the main user action should be a simple
task such as refreshing candidates for the current person.

## Safety principles

- Preserve source provenance and research history.
- Keep explainable candidate ranking, researcher assessment state, reasoning, and
  reviewed identity conclusions explicit and separate throughout research.
- Keep identity and relationship decisions reviewable.
- Prepare WikiTree work packets before making changes.
- Do not automate external writes without user approval.
- Confirm Find a Grave, FamilySearch, and WikiTree access rules before scaling collection or integrations.

## graver 1.0 contract decisions

graver 1.0 will define a stable Find a Grave acquisition and research-database
foundation. FamilySearch and WikiTree may follow in compatible 1.x releases when
they are additive evidence and candidate layers rather than replacements for the
foundation. The 1.0 compatibility promise will cover the documented researcher CLI,
documented Python facade, configuration format, explicit database migration policy,
versioned machine-readable output, and Python 3.11 through 3.14.

The installed `graver` command and `python -m graver` will both be supported. The
module entry point will be implemented through `graver.__main__`; the currently
broken direct execution of `graver.cli` is not a compatibility contract. Acquisition
search will retain useful researcher capabilities, but its public options will use
consistent kebab-case researcher terminology. Find a Grave's site-shaped parameter
names will remain internal mappings. Duplicate and camel-case spellings and hidden
pre-1.0 task and alias commands will be removed after their normalized replacements
are established and before the 1.0 release.

Machine-readable command output will use documented, command-specific, versioned
JSON envelopes rather than raw database rows. The root package will expose only a
documented public facade. Parsers, SQL and migration helpers, transport mechanics,
and wildcard constants are internal. `Driver` is transport infrastructure and will
not be part of the public 1.0 API; a public acquisition client should be introduced
only when a demonstrated external-caller use case requires one.

Package versions use PEP 440 form without a leading `v`; release tags may retain the
prefix. Commitizen is removed in favor of a smaller process: Conventional Commit
pull-request titles, squash merges, and Release Please as the sole version,
changelog, tag, and GitHub Release preparation tool. Every release must include
reviewed user-facing and developer-facing notes, with explicit migration, breaking,
security, deprecation, and known-issue sections when applicable. Release automation
remains manually triggered until the 1.0 release-candidate gates are complete.

`main` is the sole long-lived protected branch. Contributors work on short-lived
branches and open pull requests to `main`; `develop` is retired by this transition.
The former `master` branch was never a formal release or supported production
state and needs no archival tag beyond normal Git history. CI uses uv, offline tests,
wheel validation, and Python 3.11 through 3.14.

The package version must not change to `1.0.0rc1` until the public contract,
database lifecycle, generalized subject identity, explicit migrations, JSON
schemas, API hygiene and documentation, dependency cleanup, CLI cleanup, and the
supported-Python CI matrix are complete. A `1.0.0rc1` release will then validate
installation, entry points,
migration and recovery, supported platforms and Python versions, and the documented
CLI, Python, configuration, database, and JSON contracts before `1.0.0` is released.
When compatibility priorities conflict, preservation and recoverability of research
data take precedence over obsolete commands, option aliases, or accidental imports.

## Research subject identity

A Find a Grave memorial ID is an important source identifier and a convenient CLI
lookup key, but it must not become the permanent identity of a researched person or
work item. Before 1.0, introduce a stable internal research-subject key represented
as a canonical lowercase UUIDv4 string stored as SQLite `TEXT`. A
`research_subject` is an opaque organizational owner for person-level research
work, not an assertion that any two records describe the same genealogical person.
A subject created mechanically during migration is therefore an organizational
container, not an identity conclusion.

Schema version 2 introduces these entities:

- `research_subjects`, keyed by `subject_id`;
- `subject_memorials`, recording the current subject association for a memorial;
- immutable `research_subject_events`, recording accurately labeled subject
  lifecycle and association events;
- `research_tasks` rebuilt so that each task is owned by a subject; and
- immutable `research_task_events`, distinct from subject events and protected by
  no-update and no-delete triggers.

The schema enforces at most one current subject association for each memorial,
while permitting one subject to have zero or multiple associated memorials. That
structural capacity is not authorization to combine records: associating multiple
memorials with one subject is a reviewed identity decision and must remain
unavailable until evidence, review, conflict, and correction policies have been
approved. Manual association and reassociation, subject merge and split, and
preferred or canonical memorial selection are explicitly deferred. Redirects,
matching names, dates, or other inferred similarity must never merge subjects.

Find a Grave aliases remain entirely separate from subject membership. Memorial
observations remain owned by memorials, alias observations remain owned by their
alias sources, and research tasks become owned by subjects. FamilySearch and
WikiTree candidates will be hypotheses linked to subjects; only a reviewed
conclusion may establish an accepted external identity association. Later family
work packets will group subjects without replacing subject identity.

Ordinary researcher commands continue to accept memorial IDs as convenient
lookup keys and will not expose subject UUIDs by default. Until a reviewed preferred
memorial policy exists, the lowest associated memorial ID is the deterministic
display fallback for a subject with multiple memorials. This is only a display
choice, never a canonical identity assertion. Transitional pre-1.0 JSON behavior
will be preserved through compatibility projection until documented versioned JSON
envelopes replace it.

### Schema-version-2 migration invariants

The explicit version-1-to-version-2 upgrade retains the existing mandatory
backup, ordered migration, and transactional safeguards. The schema version advances
to 2 only in the same successful transaction as all version-2 changes. Once this
milestone is implemented, new databases will initialize directly at schema version
2.

Migration creates exactly one new subject for every existing `graves` row,
including graves without research tasks, and associate each memorial only with its
own migration-created subject. This one-subject-per-memorial rule is a mechanical
preservation strategy, not an identity conclusion. Every existing research task
will be copied exactly once to its memorial's associated subject, preserving every
task field and timestamp exactly. Existing grave, cemetery, memorial-observation,
alias, and alias-observation rows remain unchanged. Alias source and target graves
remain separate subjects, and a non-local alias target receives no subject.

Migration creates only accurately labeled mechanical provenance. Each migrated
subject receives the applicable creation and association event, and each existing
task receives one immutable `task_migrated` event containing an honest snapshot of
the task at migration time. That event must not claim to reconstruct earlier task
history. No identity conclusion, evidence assessment, detail level, fetch timestamp,
observation, alias, task, or historical task change may be fabricated. Failure rolls
back every version-2 change.

After migration, task creation and changes to status, priority, owner, or review
note create immutable task events. Events retain a timestamp, an actor or reviewer
when supplied, a reason where the operation requires one, and structured before and
after values. A no-op task update creates no event. Task events describe the task's
work-state history; subject events describe subject lifecycle and memorial
association history, so the two streams must not be conflated.

This implemented milestone does not include subject merge or split, manual memorial
association or reassociation, preferred/canonical memorial decisions, FamilySearch
or WikiTree persistence, versioned JSON envelopes, or hidden-command removal.

## Public application API and desktop boundary

### Naming convention

The canonical name of the core library, application services, and command-line
tool is **graver**, styled in lowercase in prose as well as in identifiers. Backticks
identify literal commands, imports, packages, and other code—not the product name
in ordinary prose. Cemetery-to-World-Tree remains the broader project context.
The future desktop application may use a separate product name, which remains an
open decision and must not alter graver's package or public API identity.

Cemetery-to-World-Tree is expected to contain a separate installable,
researcher-facing desktop application. PyQt6 is the leading toolkit candidate, but
the final toolkit, GUI package name, distribution model, and cross-platform
installer strategy remain open. The GUI may be independently packaged and
versioned. Whether it lives in another nested repository or a future top-level
monorepo is a separate repository-governance decision; no repository restructuring
is part of this plan.

The desktop application will be a sibling component that depends on graver as an
installed library. It must not be part of `graver.cli`, and graver must never depend
on it. The GUI owns windows, widgets, navigation, dialogs, presentation state, and
GUI-specific background-worker integration. It imports only graver's documented
public facade and must not access SQLite schema details, private SQL helpers, Typer
commands, Rich output, parsers, or transport implementation.

```text
Desktop GUI ─────┐
graver CLI       ├──→ graver public application API
Other clients    ┘        → domain rules
                          → repositories and units of work
                          → acquisition services
                          → SQLite persistence
```

The CLI and GUI are peer adapters. Domain rules, transactions, provenance, and
acquisition semantics must not be reimplemented independently in either adapter.
The production GUI should begin after graver 1.0 with a stable database and work-
queue vertical slice, then grow as compatible FamilySearch and WikiTree services
arrive. Another desktop toolkit or non-desktop client must remain possible.

### Workspace facade

The leading graver 1.0 application-API shape is a synchronous, typed workspace
facade, subject to validation by a small consumer spike:

```python
workspace = graver.open_workspace(database_path)

workspace.database.inspect()
workspace.work.list(...)
workspace.work.next(...)
workspace.work.show(...)
workspace.work.update(...)
workspace.acquisition.search(...)
workspace.acquisition.enrich(...)
```

These names illustrate ownership and discoverability; they do not freeze the exact
public class or method names. A workspace is opened from an explicit database path
and does not resolve CLI configuration or global defaults. The CLI resolves
`--db`, `GRAVER_DB`, and saved preferences before opening it. A GUI owns its selected
workspace path and passes it explicitly.

The workspace owns cohesive access to a database, not a permanently open SQLite
connection. Connections remain internal and are opened per operation or controlled
unit of work, never moved between GUI threads, and never returned to callers.
Public callers receive no connections, cursors, SQLite rows, SQL fragments, or
persistence-shaped dictionaries. Stateless service functions remain useful as
testable internal building blocks, but a workspace facade is preferred publicly for
discoverability, cohesive resource ownership, and GUI ergonomics without requiring
global state or a long-lived connection.

The core API should remain synchronous initially. Desktop clients can invoke it in
worker threads and translate neutral callbacks into toolkit signals. Asyncio must
not be introduced merely in anticipation of a GUI; whether later acquisition needs
it remains an open decision driven by a concrete integration.

### Public API contract

Before `1.0.0rc1`, graver must document supported import paths; typed domain models;
typed command and query objects for nontrivial operations; typed results; a stable
exception taxonomy; explicit database and transaction ownership; deterministic
ordering and pagination; stable identifier semantics; nullability and enum-
extension policy; thread-safety; progress and cooperative cancellation boundaries;
stale-update detection; injectable acquisition transport, clock, UUID generator,
and other nondeterministic boundaries; logging behavior; semantic-versioning policy;
and consumer-oriented examples.

Typed Python objects are the primary in-process contract for GUI and other library
clients. Raw dictionaries are not the preferred API. Versioned JSON remains a
separate CLI and machine-readable serialization contract. Both Python results and
JSON envelopes will project the same application results; raw database rows define
neither contract, and JSON serialization belongs outside domain and persistence
layers. Transitional CLI JSON compatibility remains intact until the versioned-
envelope milestone.

Application services return typed information or raise documented typed exceptions.
They must not print, render Rich content, invoke Typer, prompt, call `sys.exit`,
import Qt, emit Qt signals, assume an event loop, or return terminal-formatted
strings. Standard-library logging is appropriate when needed, with presentation
left to the client.

The planned exception hierarchy must let clients distinguish invalid requests or
domain transitions; missing subjects or tasks; missing or invalid databases;
required upgrades and newer-than-supported schemas; backup or migration failures;
configuration failures; blocked external access; required authentication; rate
limits; unavailable external services; timeouts and transport failures; changed or
unparseable source pages; cancellation; stale-data conflicts; and busy or locked
databases. Each exception exposes a stable machine classification, structured
context, and a safe human summary without leaking tracebacks, credentials, cookies,
or raw sensitive responses.

### Progress, cancellation, and concurrency

Long operations report toolkit-neutral typed events through ordinary Python
callbacks or protocols. Events identify the operation, stage, completed count,
optional total, and safe message or context. A callback runs in the calling worker's
thread; a GUI adapter translates it into Qt signals, while the CLI adapts the same
events into terminal progress.

Cancellation uses a neutral token or protocol and is checked before requests,
between pages or items, and before a transaction begins. It must not interrupt a
transaction where invariants could be violated, and a committed operation must not
be reported as cancelled. Partial external observations are persisted only under
explicit provenance rules.

Operations document whether they are read-only or mutating. Mutations use short,
explicit transactions. No SQLite connection is shared across threads. Task updates
accept an expected version, timestamp, or equivalent concurrency token so stale GUI
state cannot silently overwrite newer work; results include enough identity and
version information to refresh. Busy or locked database failures receive typed
handling. WAL mode may be evaluated later but is not the public concurrency
contract. The exact concurrency-token representation remains open.

### Service areas and adapter responsibilities

Application services should follow researcher goals rather than mirror tables:

- database lifecycle and workspace opening;
- research-subject lookup;
- work selection, listing, inspection, and mutation;
- memorial summary/full acquisition and provenance;
- alias diagnostics and reviewed maintenance;
- future FamilySearch discovery and assessment;
- future WikiTree reconciliation; and
- future family work packets.

Acquisition remains memorial-specific; person-level work belongs to subjects. The
CLI owns option parsing, database-precedence resolution, terminal and Rich
presentation, progress bars, approved confirmations, exit-code translation, and CLI
JSON serialization. Application services own validation, domain transitions,
transactions, schema requirements, provenance, acquisition semantics, subject/task
ownership, and typed errors and results. Parity tests must prove that CLI commands
use the same application operations available to GUI clients rather than duplicating
behavior.

Schema version 2, safe migration, immutable events, memorial-ID compatibility, and
existing `work` behavior are now implemented. An internal synchronous research
service and private subject-task repository now provide queue, list, show, and
update operations. The visible `work` adapter uses that service, existing root
functions remain compatibility projections, and enrichment is service-coordinated
while its legacy acquisition persistence functions remain in place. The remaining
subject-oriented API refactor must avoid creating a temporary raw public API and
proceed in this order:

1. Finish relocating subject-task persistence and transactions behind internal
   repositories and application services.
2. Add typed results and exceptions for migrated work operations.
3. Replace the compatibility dictionaries at the CLI boundary only after parity
   projections and tests exist.
4. Preserve current human CLI behavior and the tutorial through adapter tests.

The entire eventual facade need not land in that refactor, but every new subject
operation must move toward it instead of adding another root-level raw function.
Representative-database migration remains a separately authorized temporary-copy
verification; the canonical inventory records only behavior actually implemented.

### API hygiene and documentation milestone

After the subject-oriented schema, application-service, and CLI refactor is stable,
but before the workspace facade is frozen as graver's 1.0 contract, complete a
dedicated API hygiene and documentation milestone. Keep it separate from the
schema-version-2 migration and from substantial behavioral changes.

The intended public API will use Google-style docstrings. Every supported public
module, class, protocol, exception, function, method, typed command, query, and
result object needs a useful docstring describing its purpose, arguments, return
value, raised graver-owned exceptions, side effects, transaction behavior, thread
and cancellation expectations, and a short example where useful. Self-explanatory
private helpers, tests, and trivial accessors do not need verbose documentation.
Docstrings must explain contracts rather than merely repeat names or annotations.

Complete type annotations across the supported boundary and define explicit public
import paths and `__all__` exports. Public exceptions and results are graver-owned.
CLI and presentation types, Typer, Rich, SQLite connections and rows, SQL helpers,
parsers, Requests objects, and internal transport implementations stay outside the
facade. The API guide will document stability expectations and additive enum
evolution.

Dead-code cleanup requires corroborating evidence from repository searches, tests,
coverage where appropriate, static analysis, import/export inspection, and the
documented compatibility contract. One unused-code warning is insufficient. Review
broad root exports and wildcard imports, `Driver`, hidden compatibility commands,
commented-out tests, empty fixtures and hooks, unused dependencies, and obsolete
compatibility helpers. Remove only code demonstrated to be unused or explicitly
approved as obsolete. Migration paths that protect researcher data remain even when
ordinary code no longer calls them. Plausible external imports or commands removed
before 1.0 receive migration or release notes.

Developer API documentation will include concise offline examples for opening a
workspace, inspecting work, updating a task with stale-update protection, and
invoking acquisition through injected services. Network-capable examples must be
marked explicitly. Examples support CLI parity and the future GUI consumer while
remaining distinct from the researcher tutorial.

Before adding release gates, evaluate and document narrowly scoped tools for
Google-style docstring presence and style, type checking, unused-code detection,
and documentation build/link validation. Prefer one deterministic command per
validation category, initially scoped to the documented public API and changed
files where appropriate, with bounded correction rules. Record each tool and its
rationale before adding dependencies or CI requirements; do not recreate the prior
unbounded Flake8 workflow.

Use separate commits for public exports and type boundaries; evidenced dead-code
and dependency removal; Google-style docstrings and API examples; bounded CI
enforcement; and migration and release notes. Mechanical documentation changes must
not be folded into schema migrations or substantial behavioral commits.

Completion requires useful Google-style docstrings and complete types for every
supported public symbol; explicitly tested public imports; no transport, CLI,
presentation, or database implementation types leaking through the facade;
installed-wheel examples without source-tree assumptions; retained evidence for
dead-code removals; release notes for compatibility-sensitive removals; and bounded,
reproducible, green documentation, typing, and unused-code checks. A future GUI
consumer must be able to discover and understand the API without reading CLI or SQL
implementation code.

### Documentation and contract validation

The public facade requires a canonical `docs/api.md` or equivalent guide covering
supported imports, workspace lifecycle, queries and commands, results and
exceptions, progress and cancellation, threading, transactions, temporary-database
and injected-transport examples, compatibility boundaries, and a GUI-consumer
example. Docstrings alone are insufficient.

Contract tests must cover supported imports; typed requests and results; exception
classification and context; absence of service output, exits, and prompts; absence
of Typer, Rich, or Qt below adapters; deterministic ordering and pagination;
progress-event ordering; cancellation before requests and at safe transaction
boundaries; stale-update rejection; thread-isolated database operations; mocked
transport injection; CLI use of application services; Python and JSON projections
of the same results; wheel installation and public API use; and compatibility of the
documented facade after 1.0.

Before `1.0.0rc1`, a separate top-level consumer spike will install graver from its
built wheel and import only documented APIs. It is not the production GUI and adds
no Qt dependency to graver. It will open and validate a temporary database, list
work, display one subject and memorial, update one task with optimistic concurrency,
exercise typed errors, receive mocked-acquisition progress, and safely cancel a
mocked long operation without direct SQLite or private imports. It may use PyQt6 if
that remains preferred. Its findings may refine the facade before the release
candidate.

After graver 1.0, the production GUI should grow incrementally through workspace
selection, initialization and upgrade guidance; work queue and subject detail; one-
person acquisition and provenance review; status, notes, and conflict handling;
FamilySearch candidate discovery and evidence assessment; reviewed identity
conclusions; WikiTree reconciliation and work packets; and family-level workflows.

## Provider-governed background acquisition

The canonical [access and acquisition policy](access-policy.md) governs current
project-maintained acquisition behavior and accepted contributions. The architecture
below is planned work and must remain subordinate to that policy.

This section records an architectural policy finding, not legal advice. On
2026-08-21, planning reviewed the
[Ancestry Terms and Conditions](https://www.ancestry.com/c/legal/termsandconditions),
identified there as effective 2026-05-12, and the
[Ancestry Community Rules](https://www.ancestry.com/c/legal/community-rules).
Both apply to services that include Find a Grave. Without extensively quoting or
attempting a definitive legal interpretation, graver adopts the conservative policy
that unattended acquisition is unavailable unless its intended use has an explicit
authorization basis. Current terms, technical documentation, robots policies, and
provider instructions must be reviewed again before implementation, before enabling
an integration, and before each applicable release.

Request spacing does not establish permission. Rate limits, randomized jitter,
exponential backoff, resumability, quiet hours, and request budgets are operational
safeguards only. They do not override terms of service, robots policies, access
controls, or provider instructions. A user's acknowledgement of provider terms does
not authorize graver to implement access the provider prohibits.

graver will plan three complementary acquisition modes:

1. Interactive person-at-a-time or small supervised acquisition.
2. Bulk import from authorized files, exports, or datasets.
3. Durable background acquisition only for providers and projects where the
   intended automation is explicitly permitted.

Unattended acquisition is enabled only for an official API, authorized export or
import, licensed dataset, or documented or written permission covering the intended
use. Find a Grave unattended full-record acquisition remains disabled pending that
authorization. Ordinary researcher-directed single-record acquisition remains a
separate capability and is still subject to the applicable terms and instructions.
graver must not implement CAPTCHA or challenge solving, proxy or IP rotation,
browser-fingerprint manipulation, user-agent cycling, credential sharing, or other
circumvention.

Before any provider adapter or unattended operation is implemented or enabled, a
pre-implementation gate requires a dated review of current provider terms and
technical documentation, a documented authorization basis, maintainer approval,
legal review when the intended use is uncertain, and contract tests using mocked
transports rather than live bulk traffic. Contributions intended to circumvent
access controls or facilitate unauthorized systematic downloading will not be
accepted.

### `cloudscraper25` dependency and transport audit

On 2026-08-21, a no-network audit reviewed graver's source, lockfile, tests, and the
installed `cloudscraper25` 2.7.0 distribution metadata and license. Primary package
references are the
[`cloudscraper25` source repository](https://github.com/zinzied/cloudscraper25) and
[`cloudscraper25` package page](https://pypi.org/project/cloudscraper25/). The
installed distribution declares the MIT license and identifies version 2.7.0; the
locked artifacts were published 2025-05-27. Its metadata labels the package
production/stable but lists Python classifiers only through 3.9. Maintenance,
security advisories, and supported-Python claims must be rechecked from those
primary sources before dependency changes because this offline audit did not query
current hosting-service state.

At the time of the audit, graver imported `cloudscraper25` in `graver.api`. The default
`Driver` calls `cloudscraper25.create_scraper()` without restrictive options and
then uses the resulting Requests-compatible session only through `get`, including
query parameters, ordinary redirect behavior, response status, headers, and body.
graver implements its own status retry loop and `Retry-After` handling. It does not
set an explicit request timeout at this boundary. Session cookies and generated
headers may be inherited from the dependency, but graver has no documented need for
Cloudflare-specific cookies or headers.

No graver source configures proxy rotation, stealth mode, CAPTCHA services,
fingerprint settings, browser impersonation, or a challenge interpreter explicitly.
However, the default scraper itself automatically detects and handles supported
challenges. The installed package also ships Cloudflare challenge and Turnstile
handling, JavaScript interpreters, browser/user-agent emulation, stealth and proxy
management, fingerprint behavior, and CAPTCHA-service integrations. Its transitive
runtime dependencies include Requests, requests-toolbelt, js2py, PyCryptodome,
pyOpenSSL, pyparsing, and websocket-client. Those unused capabilities and their
dependency surface are inconsistent with graver's fail-closed provider policy even
though graver does not explicitly configure most of them.

Current tests inject a Betamax Requests session for recorded parser contracts and
use `requests-mock` for retry and failure behavior. Some `Driver` tests construct
the default session, but assertions exercise ordinary Requests-compatible HTTP
semantics rather than challenge solving or other unique `cloudscraper25` behavior.
No test establishes that graver requires browser impersonation, challenge handling,
proxy rotation, CAPTCHA support, fingerprint manipulation, or another capability a
conventional client cannot provide.

Audit result: **remove**, now implemented. graver's demonstrated requirements are a
conventional session, cookies where legitimately supplied, explicit transparent
headers, redirects, explicit timeouts, conservative bounded retries, and injectable
transports. A maintained conventional client such as Requests or httpx can
reasonably provide those capabilities without the unused circumvention-oriented
surface. The approved replacement occurred before provider-governed background
acquisition and `1.0.0rc1`, with transport and parser contract tests kept offline.
The replacement decision does not authorize automated access; provider
authorization remains an independent gate. graver now uses an internal synchronous
transport boundary backed by Requests, with an explicit graver user agent, finite
connect and read timeouts, graver-owned response and error types, bounded transient
retries, and fail-closed handling for access challenges, `403`, and repeated `429`
responses.
The broader transport remains internal and injectable; Requests types do not define
the planned public application API.

### Import-first bulk capability

The first scalable path should be a typed import service for official exports,
licensed datasets, and authorized researcher-supplied files without live scraping.
It will retain explicit source, licensing or
authorization, and provenance metadata; validate inputs; provide a dry-run summary;
report duplicates and conflicts; import transactionally; and support idempotent
resume where practical. Summary-versus-full classification must follow known source
metadata only. Imports must never fabricate observations, acquisition timestamps,
or detail classifications.

Import results must be suitable for both CLI and GUI adapters. Adapters may later
support CSV, JSON, SQLite, or approved provider exports, but the first implementation
will select the smallest useful authorized format after inspecting real use cases
rather than promising every format. Public visibility of data does not itself grant
redistribution rights; licensing and authorization responsibility must remain clear
to the researcher.

### Provider-neutral durable jobs

The planned background-work subsystem is independent of Find a Grave and of CLI or
GUI presentation. Candidate entities are a job, job item, attempt, provider-policy
snapshot, schedule metadata, progress checkpoint, and pause/cancellation state.
Jobs must contain declarative operation specifications, never runnable Python code
or arbitrary shell commands.

Each job retains a stable identifier, operation type, explicit target set or query
snapshot, creation time and requester, provider, policy and authorization basis,
status, total items, completed/failed/skipped/blocked counts, next eligible time,
request budget, last progress and failure, and immutable attempt history. Provider
policy snapshots retain the terms URL, review date, authorization basis, permitted
rate and execution window, budgets, and any deterministic jitter configuration.

Execution initially permits at most one worker per database and one concurrent
request. It uses provider-specific minimum
intervals, hourly and daily budgets, optional permitted execution windows, durable
checkpoints, idempotent restart, and bounded work per invocation. Before activation,
the client presents an estimated request count and duration. Jobs support pause,
resume, cancel, and inspection; use cooperative cancellation at safe boundaries;
keep database transactions short; share no SQLite connection across threads; and
continue only while their provider policy permits the operation.

No universal production delay is approved. Provider permission determines whether
live automation is allowed and, if so, its operational limits. Random jitter may
smooth authorized traffic only when it remains subordinate to the permitted minimum
interval, never raises traffic beyond budgets, is injectable and deterministic in
tests, and is recorded as policy configuration. It cannot establish authorization
or substitute for hourly and daily limits.

### Fail-closed stop and retry policy

The runner immediately pauses a job and requires human review on a CAPTCHA,
Cloudflare or other access challenge, authentication change or `401`, `403`,
explicit access-block message, policy uncertainty or a robots/provider-policy change,
repeated `429`, or repeated parsing failures that suggest a source-schema change.
No automatic mechanism may work around a provider block.

For `429`, the runner honors `Retry-After` when present and pauses rather than
repeatedly probing. A bounded cooldown is required, and repeated occurrences require
human review. Genuinely transient timeouts and `5xx` responses may use bounded
exponential backoff with a fixed attempt limit. Every attempt is recorded, and
repeated failure must never result in faster retries.

### Scheduling, API, and client integration

Scheduling is an adapter over the durable job application service, initially using
this bounded invocation model:

```text
scheduler invokes bounded job runner
  → runner processes eligible items within its budget
  → runner checkpoints and exits
```

Cron, launchd, Task Scheduler, a local CI-like scheduler, or a future GUI scheduler
can invoke the same service without requiring graver to ship a permanent daemon.
Exact CLI names remain provisional; a progressive-disclosure `graver jobs ...`
surface is plausible, with ordinary help focused on goals and status and advanced
policy diagnostics kept under administrative surfaces.

The workspace facade will expose typed job specifications, statuses, progress,
cancellation, structured provider-block outcomes, request-budget estimates, and
immutable attempt history through an illustrative `workspace.jobs` service. It
returns no terminal rendering or Qt types. CLI and GUI adapters call the same job
services, and production GUI scheduling remains an adapter rather than a second job
engine.

Job specifications, logs, events, and exports must contain no credentials. External
content storage is minimized; diagnostic responses are redacted; source terms,
authorization metadata, stable source URLs, acquisition timestamps, outcomes, and
user-visible retention behavior are preserved. Public availability creates no
assumption that redistribution is allowed.

Offline contract tests will cover deterministic scheduler eligibility, hourly and
daily budgets, single concurrency, injected deterministic jitter, pause/resume and
restart, idempotent checkpoints, crash recovery, safe cancellation, `Retry-After`,
circuit breaking for challenges, CAPTCHA, `401`, `403`, and repeated `429`, bounded
transient retries, no retry on access blocks, progress events, CLI/API parity, GUI-
consumer compatibility, immutable attempts, and import validation and provenance.
They must deny real network access. The live contract probe remains separate and
must never exercise bulk behavior.

## Research database lifecycle

SQLite research databases are mutable user data, not source artifacts. The default
runtime filename `graves.db`, representative databases such as `many_graves.db`, and
other researcher-created databases must remain ignored by Git and must not be
published merely to provide an example. The schema and migrations belong in source
control. Ordinary tests should build isolated temporary databases from small,
readable fictional or public-domain fixtures. Test data should be created through
deterministic, project-specific factories: hand-authored records for genealogical
meaning and edge cases, and seeded Faker data for volume and variation. Faker must
remain behind those domain factories, use fixed seeds and explicit locales, and not
be used for assertions that depend on a particular library-generated value. Curated
cases should cover partial dates, repeated and variant names, relationships,
conflicting evidence, aliases, missing fields, non-ASCII text, and summary-to-full
enrichment. Generated places are opaque test values, not substitutes for curated
historical-geography cases. A binary SQLite fixture is appropriate only when a
small, purpose-specific historical database is necessary to verify a migration and
cannot be reconstructed without defeating the test.

Database ownership should become intentional through distinct operations:

- `graver init` creates and selects `./graves.db`.
- `graver init DATABASE` creates and selects the named database.
- `graver use DATABASE` selects an existing database without creating or migrating
  it; `use --show` and `use --clear` inspect or clear that preference.
- A specialist `graver admin database upgrade DATABASE` workflow inspects an
  outdated database, creates a verified backup, and performs an explicit,
  transactional migration with recovery safeguards.

Initialization must refuse to overwrite any existing file, require the parent
directory to exist, initialize and validate the complete current schema, and save
the new default only after success. A partial failure must remove only the newly
created incomplete file and leave the previous selection unchanged. The concise
success message should be `Initialized and selected research database: PATH`.

Validation, initialization, and migration must remain separate. `use` validates
without mutation. If the selected database is outdated, it reports the detected
format and directs the researcher to the specialist upgrade workflow rather than
altering the database during a read. An upgrade must preserve a recoverable original,
validate the migrated result before selection, fail safely on an unknown or newer
format, and never fabricate provenance that the legacy data cannot support.

After `init` is established, implicit database creation by acquisition commands
should be removed in a separate compatibility milestone. Missing database errors
should direct the researcher to `graver init` or `graver use DATABASE`. Explicit
`--db` remains a one-command override and must never change the saved selection.

## Testing strategy

The offline suite should distinguish four complementary layers:

1. Domain and parser tests feed curated HTML or JSON directly to parsers without an
   HTTP session. They cover genealogical semantics, missing and malformed fields,
   removed and merged pages, source variants, and summary-to-full behavior.
2. Transport tests use explicit HTTP mocks to verify methods, URLs, query and POST
   parameters, headers, redirects, retry policy, timeouts, and failures. Request
   construction should not require a recorded cassette.
3. Persistence and researcher-workflow tests use isolated temporary SQLite
   databases and exercise schema, migrations, transactions, provenance,
   configuration precedence, and CLI behavior.
4. A small recorded-contract suite replays sanitized interactions actually observed
   from external platforms to verify the complete transport-to-domain pipeline.

Ordinary tests and CI must deny live network access. Recorded tests must default to
replay-only and fail when an interaction is absent; recording or refreshing a
cassette requires an explicit maintainer workflow and authorization. Recorded
fixtures must remove credentials, cookies, Cloudflare and session identifiers,
personal data not needed by the test, and other sensitive or unstable metadata.
Authenticated FamilySearch or WikiTree traffic requires an especially strict review
before any sanitized fixture may be committed.

Betamax remains a temporary compatibility mechanism for the existing cassette
inventory, not the foundation for new tests. First lock it to replay-only and mark
the recorded-contract tests. Then migrate parser coverage to static response
fixtures and transport behavior to `requests-mock`. Trial a small conversion of the
remaining contract cases to the actively maintained VCR.py/pytest-recording stack;
complete that migration only if it is demonstrably simpler and stable. Remove the
cassette layer entirely if static fixtures and transport mocks provide the same
useful coverage.

Test infrastructure must also follow these rules:

- Faker uses a fixed default seed and explicit locale behind domain factories;
  Python randomness is seeded consistently, time-based reseeding is forbidden, and
  failures report the seed needed for reproduction.
- Temporary files, databases, configuration, environment variables, and connections
  use pytest lifecycle fixtures and are always cleaned up. Tests never read or alter
  a developer's runtime database or user configuration.
- Test frameworks, Faker, record/replay tools, mocks, and coverage tools belong only
  in test dependency groups, not the installed application's runtime dependencies.
- Vestigial tool smoke tests, empty tests, and commented-out test bodies should be
  removed or replaced by assertions about graver behavior.
- Register meaningful `unit`, `integration`, `recorded`, and `slow` markers and
  enable strict marker checking. Evaluate pytest importlib mode against the current
  `src` layout before adopting it.
- Branch-coverage reporting now runs once per CI workflow on Ubuntu/Python 3.14.
  The measured 2026-08-22 baseline is 91%, with a 90% non-regression floor and a
  Coveralls report. Raise the floor only as meaningful behavior is covered;
  coverage percentage must not substitute for useful assertions. The same run
  exposed unclosed-SQLite `ResourceWarning`s that remain lifecycle-cleanup work and
  must not be hidden by coverage configuration.

### Live Find a Grave contract probe

Add a separate, explicitly invoked `live_contract` maintenance probe to answer a
different question from recorded tests: whether the current Find a Grave site still
satisfies graver's minimum parsing contract. It is not part of ordinary local tests,
pull-request validation, cassette recording, or the researcher-facing CLI. The
designated full-memorial canary is the stable public George Washington memorial:

`https://www.findagrave.com/memorial/1075/george-washington`

Each run should make only two or three requests: retrieve that memorial, perform one
tightly constrained search expected to yield a summary, and optionally retrieve one
stable cemetery page if cemetery parsing remains operationally important. Use short
timeouts, minimal retries, no database writes, no fixture updates, and no
authenticated session. Assert semantic invariants rather than exact mutable content:
the response is not an access challenge or generic error; the memorial ID, name, and
cemetery or burial linkage are recognizable; parsing does not silently produce an
empty object; and a search result exposes its ID, URL, name, and burial context.

Classify outcomes as `compatible`, `schema_changed`, `access_blocked`,
`site_unavailable`, `canary_changed`, or `probe_error`. A failure artifact may retain
the timestamp, page type, status, final URL, redirects, content type, parser stage,
missing invariant, response hash, and a small sanitized structural excerpt. It must
never expose cookies, credentials, Cloudflare identifiers, unnecessary personal
data, or automatically commit a response or refresh a fixture.

Begin with manual execution before releases and parser changes, then run it
periodically from a normal developer environment. Trial a weekly scheduled job only
after confirming that its runner produces a reliable signal rather than Cloudflare
false positives. Before any scheduled live access, review the current Find a Grave
terms, robots directives, and published automation guidance; unclear policy requires
maintainer review rather than assuming permission. A live failure is diagnostic and
must not automatically block an unrelated release until its category is understood.

## Target persistent entities

The eventual SQLite model may include stable research subjects, cemeteries,
memorials, subject-to-platform identifiers, FamilySearch discovery runs, candidate
snapshots, FamilySearch candidates, candidate assessments, sources/evidence,
reviewed identity conclusions, WikiTree matches, relationships, and work-queue
items. Candidate hypotheses and evolving assessments must remain distinguishable
from final reviewed conclusions. Find a Grave records must retain stable memorial
and cemetery links without requiring every subject to have a memorial.

## Find a Grave alias ownership

In the current schema, a research task is owned by a research subject, while
memorial IDs remain compatible researcher-facing lookup keys. An alias does not
automatically transfer, merge, complete, or delete that work. Source and target
graves and their acquisition observations remain separate provenance even when both
are later associated with one research subject. Alias
observations form their own immutable provenance stream, and a retraction is an
explicit local research decision rather than an inference from a retrieval failure.

Initial work states may include `unprocessed`, `researching`, `familysearch_match_found`, `identity_resolved`, `wikitree_match_found`, `wikitree_profile_missing`, `relationship_reconciliation_needed`, `ready_for_review`, `completed`, and `unable_to_resolve`.

## GEDCOM and relationship-aware research

GEDCOM is an exploratory nice-to-have rather than a pre-1.0 dependency or committed
feature milestone. Its potential first value to graver is immutable import and
repeatable comparison, not bulk creation of
accepted people or conversion into a general-purpose tree editor. Imported people,
facts, families, and relationships are external assertions until they are mapped
and reviewed. A GEDCOM cross-reference is scoped to one imported snapshot and never
becomes a research-subject identifier.

The core direction already requires subjects without memorials, evidence-aware
relationships, and reviewed conclusions for genealogy research independently of
GEDCOM. Do not enlarge or freeze the public API, schema, or release scope solely to
anticipate GEDCOM. If later evidence supports implementation, external dataset
snapshots and mapping proposals must remain outside the internal identity model.

Re-evaluate its value at the 1.0 release-candidate review, after the first production
GUI work-queue vertical slice has been road-tested, and when concrete researcher
needs arise. GEDCOM must not delay the foundational subject, provenance, API, CLI,
testing, release, or GUI work. The candidate ownership, provenance, privacy, API,
testing, and interoperability constraints are retained in the canonical
[GEDCOM integration architecture](gedcom-integration.md).

## Roadmap

Completed foundation:

1. Inspected and preserved the scraper and SQLite persistence foundation.
2. Added the task-oriented CLI, alias maintenance, database selection,
   initialization, explicit backed-up upgrades, and the researcher tutorial.
3. Replaced `cloudscraper25` with a conventional Requests-backed internal transport,
   explicit timeouts and transparent identification, bounded retries, and
   fail-closed access handling.
4. Added schema version 2 research-subject ownership, one-subject-per-memorial
   migration, immutable subject/task events, subject-owned tasks, and memorial-ID
   compatibility across existing work CLI and API operations while preserving
   human output, transitional JSON, aliases, observations, and tutorial behavior.

Pre-1.0 sequence:

5. Build subject-oriented repositories and application services, move `work` CLI
   operations from the existing root functions onto those services, keep SQL private,
   preserve behavior through adapter-parity tests, and retain extension points for
   the accepted evidence-assessment contract.
6. Prepare low-fidelity evidence-workflow artifacts and complete professional review
   gate R1. Resolve or explicitly accept every blocking finding before implementing
   candidate or evidence persistence.
7. Implement the offline evidence vertical slice using curated FamilySearch-shaped
   fixtures: immutable discovery runs and candidate snapshots, assertion-level
   comparison signals, explainable candidate ordering, evolving assessments,
   negative searches and unresolved questions, and immutable reviewed conclusions.
   Perform no live FamilySearch request, expose no persistence-shaped public CLI,
   and allow no automatic identity acceptance.
8. Complete professional review gate R2 against the end-to-end offline workflow.
   Resolve or explicitly accept every blocking finding before freezing the public
   workspace façade or detailed evidence-GUI information architecture.
9. Complete the dedicated API hygiene and documentation milestone: explicit public
   exports and type boundaries, Google-style public docstrings, evidenced dead-code
   cleanup, offline API examples, and bounded documentation/type/unused-code checks.
10. Complete a dependency-security and software-supply-chain milestone: triage all
   GitHub dependency alerts against the default branch and current lockfile, update or
   remove affected direct and transitive packages, verify the locked dependency
   graph and built wheel, enable bounded automated dependency/security checks, and
   document supported reporting and remediation practices. Treat alert counts as
   dated observations rather than release criteria; `1.0.0rc1` requires no
   unresolved known vulnerability without an explicit, documented risk decision.
11. Modernize offline test boundaries, default network denial, deterministic domain
   fixtures and Faker, temporary lifecycle, markers, replay-only contracts, and the
   bounded live-contract probe.
12. Define and freeze the public graver workspace facade, typed requests and results,
   documented imports and stability policy, exception taxonomy, transaction and
   threading contract, progress, cancellation, stale-update handling, injectable
   transport and nondeterminism, semantic-versioning policy, and typed candidate,
   evidence, assessment, conclusion, acquisition-receipt, and provenance projections
   validated by the offline slice.
13. Move remaining researcher-directed acquisition and CLI workflows onto those
   application services, validate the shared boundaries, and add CLI/API parity
   tests while preserving the tutorial's human workflow. Add researcher-readable
   acquisition receipts without exposing raw persistence entities.
14. Validate researcher-directed acquisition against the current access policy, then
   complete each provider's authorization and policy gate. Any pre-1.0 import support
   must use authorized data, and no unattended Find a Grave enrichment is enabled.
15. Define import-first boundaries and provider-neutral background-job services
   before any public job API is frozen. Provider-specific unattended adapters remain
   unavailable unless their authorization gate is satisfied.
16. Complete remaining runtime/test dependency separation; retain `Driver` and
   implementation mechanics as internal details.
17. Add command-specific versioned JSON envelopes as adapter projections of the same
   typed application results.
18. Normalize acquisition options and remove duplicate, site-shaped, and hidden
   pre-1.0 compatibility paths.
19. Support `python -m graver` through `graver.__main__`.
20. Maintain the uv-based Python 3.11-through-3.14 CI, Conventional Commit PR-title
   enforcement, reviewed changelog, and manually gated Release Please workflow.
21. Finish the public API guide, database and 0.1 migration instructions,
   compatibility and release notes, and the later authorized branch/tag plan.
22. Build the separate consumer spike against the installed wheel, validating the
   documented facade without private imports or direct SQLite access. It may
   exercise mocked jobs but performs no live bulk acquisition.
23. Resolve spike findings and complete any required provider-neutral job-service
   contracts without enabling an unauthorized provider adapter. Prepare
   `1.0.0rc1` without weakening migration,
   provenance, concurrency, or offline-test guarantees.
24. Validate the release candidate, re-evaluate whether GEDCOM has demonstrated
    enough value for later implementation, and release graver `1.0.0` after the core
    findings are resolved. GEDCOM is not a release criterion.

Post-1.0 compatible sequence:

25. Begin the production desktop GUI with workspace/database lifecycle, work queue,
   subject detail, and one-person acquisition/provenance review.
26. Connect an authorized live FamilySearch adapter to the already validated
   candidate, evidence, assessment, and conclusion application services. Live data
   must not redefine the offline-tested domain semantics.
27. Implement import-first bulk acquisition for the smallest demonstrated authorized
   formats not already supported in 1.0.
28. Add provider-authorized background acquisition only after a repeated policy and
   permission review; production GUI scheduling uses the same durable job service.
29. Extend GUI and CLI evidence-research workflows over those services.
30. Complete professional review gate R3 by repeating the original professional
    usability audit against the production evidence workflow. Resolve or explicitly
    accept every blocking finding before claiming production readiness or expanding
    into WikiTree and family workflows.
31. Add WikiTree reconciliation, evidence summaries, and family work packets.
32. Extend the production GUI across the complete reviewed research workflow.
33. After the GUI work-queue vertical slice has been road-tested, re-evaluate GEDCOM
    using concrete researcher needs. Only if justified, begin immutable GEDCOM 7 and
    5.5.1 inspection and repeatable comparison; reviewed mappings, relationships,
    and privacy-filtered selective export remain separately approved later stages.

Open decisions include the final GUI toolkit and package name, nested-repository
versus future-monorepo governance, exact facade class and method names, the exact
concurrency token, whether concrete later acquisition needs asyncio, GUI packaging
and distribution, and cross-platform installer strategy. GEDCOM parser selection,
comparison scoring, file retention, and GEDZIP scope remain conditional questions,
not active design dependencies. The approved dependency
direction remains a separate GUI component using only graver's documented API.
