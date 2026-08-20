# Project context

## Objective

Systematically connect well-researched people to the WikiTree World Tree, beginning with populations discovered from Find a Grave cemeteries.

## Operating model

```text
Find a Grave cemetery
  → scraper
  → SQLite research database
  → FamilySearch candidate matching and research
  → evidence / identity model
  → WikiTree candidate matching and relationship reconciliation
  → human review
  → approved WikiTree work or update
  → cemetery tag
```

Find a Grave observations must remain preserved as original provenance. Later research conclusions must be stored separately rather than replacing the original record.

## Identity and family research

Identity is not determined by name alone. Candidate assessments should combine name variants, dates and places, family members, residences, occupation, military information when relevant, cemetery information, and source evidence.

The central model is an identity triangle:

```text
Find a Grave person ↔ FamilySearch person ↔ WikiTree person
```

Candidates need explicit confidence and reasoning. Discrepancies need human review. Once a person is reliably identified, their parents, spouses, and children can validate the model and identify related cemetery members.

## Safety principles

- Preserve source provenance and research history.
- Use explicit status and confidence fields.
- Keep identity and relationship decisions reviewable.
- Prepare WikiTree work packets before making changes.
- Do not automate external writes without user approval.
- Confirm Find a Grave, FamilySearch, and WikiTree access rules before scaling collection or integrations.

## Target persistent entities

The eventual SQLite model may include cemeteries, memorials, FamilySearch matches, WikiTree matches, research conclusions, relationships, sources/evidence, and work-queue tasks. Every research item must retain stable Find a Grave memorial and cemetery links.

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
3. Completed: provide a practical person-at-a-time task interface with explicit Find a Grave alias review.
4. Integrate FamilySearch search, retrieval, and candidate matching.
5. Integrate WikiTree profile search and reconciliation.
6. Generate evidence summaries, identity assessments, relationship reconciliation, and WikiTree work packets.
7. Extend the interface from person-at-a-time to reviewed family work packets.
