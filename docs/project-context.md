# Project context

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
- Use explicit candidate status, confidence, and reasoning fields throughout research.
- Keep identity and relationship decisions reviewable.
- Prepare WikiTree work packets before making changes.
- Do not automate external writes without user approval.
- Confirm Find a Grave, FamilySearch, and WikiTree access rules before scaling collection or integrations.

## Graver 1.0 contract decisions

Graver 1.0 will define a stable Find a Grave acquisition and research-database
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

Package versions will be normalized without a leading `v`; release tags may retain
the prefix. Test frameworks, fixtures, typing tools, and coverage or recording tools
will move out of runtime dependencies, and unused runtime dependencies will be
removed. The stale Poetry-based workflow will be replaced with uv-based installation,
offline tests, wheel construction, and validation across Python 3.11 through 3.14.

The protected release branch will become `main`, with `develop` retained for
integration. Before `master` is retired or renamed, its historical production state
will receive an archival tag. Branch and tag changes require a later, explicitly
authorized repository-administration task; this plan does not perform them.

The package version must not change to `1.0.0rc1` until the public contract,
database lifecycle, generalized subject identity, explicit migrations, JSON
schemas, dependency cleanup, CLI cleanup, and supported-Python CI matrix are
complete. A `1.0.0rc1` release will then validate installation, entry points,
migration and recovery, supported platforms and Python versions, and the documented
CLI, Python, configuration, database, and JSON contracts before `1.0.0` is released.
When compatibility priorities conflict, preservation and recoverability of research
data take precedence over obsolete commands, option aliases, or accidental imports.

## Research subject identity

A Find a Grave memorial ID is an important source identifier and a convenient CLI
lookup key, but it must not become the permanent identity of a researched person or
work item. Before 1.0, introduce a stable internal research-subject or person key.
The model must support a memorial-centered researcher workflow while allowing
multiple external platform identifiers, multiple memorials or aliases for one
person, people without a Find a Grave memorial, and later family-level work packets.
Existing `work` commands may continue accepting a memorial ID when it resolves
unambiguously to a subject.

Find a Grave graves, aliases, observations, and current memorial-centered tasks must
be migrated without losing identifiers, provenance, status, priority, ownership,
notes, timestamps, or immutable history. FamilySearch candidates and WikiTree
profiles should attach to the stable subject as additive hypotheses and evidence.
Family-level work should reference subjects rather than changing the meaning of a
subject key.

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
  removed or replaced by assertions about Graver behavior.
- Register meaningful `unit`, `integration`, `recorded`, and `slow` markers and
  enable strict marker checking. Evaluate pytest importlib mode against the current
  `src` layout before adopting it.
- Establish branch-coverage reporting from the measured baseline, then introduce a
  modest non-regression threshold and raise it only as meaningful behavior is
  covered; coverage percentage must not substitute for useful assertions.

### Live Find a Grave contract probe

Add a separate, explicitly invoked `live_contract` maintenance probe to answer a
different question from recorded tests: whether the current Find a Grave site still
satisfies Graver's minimum parsing contract. It is not part of ordinary local tests,
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

In the current schema, a research task remains attached to the memorial ID through
which the person was discovered. Until the subject-identity migration is complete,
an alias does not automatically transfer, merge, complete, or delete that work.
Afterward, source and target graves and their acquisition observations must remain
separate provenance even when both are associated with one research subject. Alias
observations form their own immutable provenance stream, and a retraction is an
explicit local research decision rather than an inference from a retrieval failure.

Initial work states may include `unprocessed`, `researching`, `familysearch_match_found`, `identity_resolved`, `wikitree_match_found`, `wikitree_profile_missing`, `relationship_reconciliation_needed`, `ready_for_review`, `completed`, and `unable_to_resolve`.

## Roadmap

Completed foundation:

- Inspected and preserved the existing scraper and SQLite database.
- Added persistent research-management and work-queue capability.
- Added functional person-at-a-time task handling and explicit Find a Grave alias
  review.
- Refined the CLI into a small, task-oriented `work` surface with progressive
  disclosure and moved alias maintenance under `admin aliases`, while retaining
  current internal capabilities and hidden compatibility commands for pre-1.0
  review.

Pre-1.0 release sequence:

1. Define and document the complete Graver 1.0 CLI, Python, configuration,
   database, migration, JSON, supported-Python, and compatibility contract.
2. Add `graver init [DATABASE]` with refusal to overwrite and selection only after
   successful current-schema creation and validation.
3. Separate database inspection, validation, initialization, and explicit migration;
   add the planned `graver admin database upgrade DATABASE` workflow with backup,
   transactional upgrade, recovery, and unknown/newer-format safeguards.
4. Introduce a stable research-subject identity and migrate current memorial-centered
   tasks and provenance without losing existing memorial data.
5. Modernize network denial, deterministic domain fixtures and Faker, temporary
   database lifecycle, test layers and markers, replay-only contracts, and the
   separate bounded live-contract probe.
6. Separate runtime dependencies from test, typing, fixture, recording, coverage,
   and development tools; remove unused runtime dependencies.
7. Normalize acquisition options to kebab-case researcher terminology, remove
   duplicate and site-shaped public spellings, and remove hidden pre-1.0 task and
   alias compatibility commands.
8. Reduce root exports to the documented public Python facade and keep `Driver`,
   parsers, transport mechanics, SQL helpers, and wildcard constants internal.
9. Introduce documented, command-specific, versioned JSON schemas and stable
    machine-readable error behavior.
10. Support `python -m graver` through `graver.__main__` alongside the console entry
    point.
11. Replace stale Poetry CI with uv-based installation, offline tests, wheel checks,
    and Python 3.11-through-3.14 validation.
12. Add database migration instructions, 0.1-to-1.0 compatibility notes, public
    contract documentation, release notes, and the later authorized branch/tag
    transition plan.
13. Prepare and validate `1.0.0rc1` without weakening database recovery or offline
    test guarantees.
14. Release `1.0.0` after release-candidate findings are resolved.
15. Add repeatable FamilySearch candidate discovery and research storage behind
    simple researcher workflows, including immutable search runs and candidate
    snapshots, change detection, evidence, discrepancies, evolving confidence,
    reasoning, reviewer fields, and immutable decision history.

Later compatible roadmap work includes explicit reviewed identity conclusions,
WikiTree profile search and reconciliation, evidence summaries and work packets, and
the progression from person-at-a-time research to reviewed family work packets.
