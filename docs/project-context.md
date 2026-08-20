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

Database ownership should become intentional through two complementary researcher
actions:

- `graver init` creates and selects `./graves.db`.
- `graver init DATABASE` creates and selects the named database.
- `graver use DATABASE` selects an existing database without creating or migrating
  it; `use --show` and `use --clear` inspect or clear that preference.

Initialization must refuse to overwrite any existing file, require the parent
directory to exist, initialize and validate the complete current schema, and save
the new default only after success. A partial failure must remove only the newly
created incomplete file and leave the previous selection unchanged. The concise
success message should be `Initialized and selected research database: PATH`.

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

The eventual SQLite model may include cemeteries, memorials, FamilySearch discovery runs, candidate snapshots, FamilySearch candidates, candidate assessments, sources/evidence, reviewed identity conclusions, WikiTree matches, relationships, and work-queue tasks. Candidate hypotheses and evolving assessments must remain distinguishable from final reviewed conclusions. Every research item must retain stable Find a Grave memorial and cemetery links.

## Find a Grave alias ownership

A research task remains attached to the memorial ID through which the person was
discovered. An alias identifies a possible canonical Find a Grave target but does
not automatically transfer, merge, complete, or delete research work. Source and
target graves, acquisition observations, tasks, and later conclusions remain
separate. Alias observations form their own immutable provenance stream, and a
retraction is an explicit local research decision rather than an inference from a
retrieval failure.

Initial work states may include `unprocessed`, `researching`, `familysearch_match_found`, `identity_resolved`, `wikitree_match_found`, `wikitree_profile_missing`, `relationship_reconciliation_needed`, `ready_for_review`, `completed`, and `unable_to_resolve`.

## Roadmap

1. Completed: inspect and preserve the existing scraper and SQLite database.
2. Completed: add persistent research-management and work-queue capability.
3. Completed: provide functional person-at-a-time task handling and explicit Find a Grave alias review.
4. Completed: refine the CLI into a small, task-oriented `work` surface with
   progressive disclosure; move alias maintenance under `admin aliases` while
   retaining hidden compatibility commands and the complete Python API.
5. Complete the explicit research-database lifecycle: add `graver init [DATABASE]`
   to create and select a new database safely, establish the repository fixture
   policy with deterministic domain factories, curated edge cases, and seeded Faker
   volume data; modernize test isolation, network safety, dependency grouping, and
   test classification; reduce Betamax to a replay-only compatibility layer and
   evaluate its incremental replacement; add the bounded, explicitly invoked live
   Find a Grave contract probe; and then remove implicit database creation from
   acquisition commands in a separately tested compatibility change.
6. Add repeatable FamilySearch candidate discovery and research storage behind simple researcher workflows, including immutable search runs and candidate snapshots, detection of new or materially changed candidates, candidate status, match signals, evidence, discrepancies, evolving confidence, reasoning, reviewer fields, and immutable decision history.
7. Add explicit human-reviewed identity conclusions only after FamilySearch evidence gathering: accepted, rejected, or unresolved.
8. Integrate WikiTree profile search and reconciliation for identities sufficiently supported by reviewed research.
9. Generate evidence summaries, identity assessments, relationship reconciliation, and WikiTree work packets.
10. Extend the interface from person-at-a-time to reviewed family work packets.
