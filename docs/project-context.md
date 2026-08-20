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
5. Add repeatable FamilySearch candidate discovery and research storage behind simple researcher workflows, including immutable search runs and candidate snapshots, detection of new or materially changed candidates, candidate status, match signals, evidence, discrepancies, evolving confidence, reasoning, reviewer fields, and immutable decision history.
6. Add explicit human-reviewed identity conclusions only after FamilySearch evidence gathering: accepted, rejected, or unresolved.
7. Integrate WikiTree profile search and reconciliation for identities sufficiently supported by reviewed research.
8. Generate evidence summaries, identity assessments, relationship reconciliation, and WikiTree work packets.
9. Extend the interface from person-at-a-time to reviewed family work packets.
