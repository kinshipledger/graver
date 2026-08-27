# graver roadmap

This roadmap shows the public direction of the graver research engine and the later
professional researcher product in broad stages. It is not a calendar or a promise
that every later idea will ship. Researcher feedback, professional review, security
and privacy findings, provider authorization, and measured implementation evidence
may change the order.

For detailed architectural reasoning, see the
[project context](docs/project-context.md). For verified current behavior, see the
[existing-system inventory](docs/existing-system-inventory.md). Private schedules,
entrepreneurial decisions, and unpublished critical-path planning are deliberately
outside this repository.

## Available now: 1.0.0rc1

- A local SQLite research database with explicit creation, selection, inspection,
  backed-up upgrades, and immutable history.
- Narrow Find a Grave summary acquisition followed by a person-by-person queue,
  explicit approval, and one-record enrichment.
- Retained summary and selected full-page observations with acquisition receipts,
  redirects, and source-displayed relationship links kept as observations rather
  than accepted identity or kinship.
- A supported `graver` command, versioned successful JSON output, and a documented
  synchronous typed Python application boundary.
- Offline evidence and candidate-contract foundations validated with fictional,
  FamilySearch-shaped fixtures.

The fixtures above do **not** constitute a live FamilySearch connection, candidate
search, or production identity-matching workflow.

## Stabilizing the graver engine for final 1.0

Final graver 1.0 is the stable engine finish line: core research behavior, workflow
rules, database lifecycle, CLI, application API, and extension boundaries. It is not
a claim that the later professional desktop product is complete.

- Resolve bounded release-candidate feedback and decision-safety findings.
- Establish the first reviewed graver icon and a small visual system before the
  project identity is propagated across organization and distribution surfaces.
- Add the initial researcher workflow, evidence reasoning, and client-architecture
  diagrams without making the documentation dependent on graphics alone.
- Make database targeting, acquisition receipts, recovery guidance, and retained
  data scope unmistakable to researchers.
- Stabilize the documented CLI, Python API, JSON, database migration, packaging,
  security, privacy, and release contracts.
- Repeat focused professional-genealogist, technical-publications, and security
  reviews where material behavior changes; include visual assets when they shape
  workflow or evidence meaning.

The production desktop product and live FamilySearch integration are not required
for graver engine 1.0.

## Professional researcher product after engine 1.0

- Publish a minimal, accessible static project website that directs researchers to
  authoritative installation, tutorial, release, feedback, security, privacy, and
  responsible-access resources without duplicating the documentation source of
  truth or introducing visitor tracking.
- Define and stage graver's **integration architecture** before substantial desktop
  or provider expansion. Keep three boundaries distinct: clients that present and
  operate research work; sources that discover, observe, or import material; and
  projections that produce purpose-specific outputs. Validate each contract through
  a bounded vertical slice before declaring it public and stable.
- Begin the production desktop product with database/workspace selection, the
  research queue, person detail, acquisition receipts, and provenance review.
- Define a bounded source-neutral research-reasoning foundation for researcher
  questions, candidate hypotheses, evidence correlation, conflicts, authored
  analysis, and the researcher's reviewed conclusions. Validate the contract with
  realistic professional-research scenarios before freezing persistence or GUI
  vocabulary.
- Prototype purpose-specific projections from that durable research record, starting
  with the highest-value researcher needs rather than committing immediately to
  every tree, report, interchange, or publishing format.
- Run information-architecture, interaction-continuity, accessibility, visual,
  security, privacy, and professional-researcher review gates as the interface
  develops.
- Preserve the command line as a supported operational client over the same
  application services used by the desktop interface. The CLI remains useful for
  administration, automation, recovery, advanced use, and testing; the desktop is
  intended to become the preferred everyday researcher experience.

## Later compatible development

- Add an authorized FamilySearch adapter to the validated candidate and evidence
  services.
- Allow any admitted discovery, observation, or import adapter to provide the first
  lead for a research subject without giving its provider special evidentiary
  standing.
- Make candidate discovery repeatable so later FamilySearch corrections, sources,
  relationships, and newly available candidates can be reviewed without rewriting
  earlier snapshots.
- Keep machine ordering explainable and separate from confidence, proof, and
  researcher-authored same-person conclusions.
- Consider WikiTree reconciliation only after the FamilySearch research workflow
  demonstrates value and preserves evidence and decision history.

## Conditional and exploratory work

- GEDCOM input, repeatable comparison, and privacy-filtered selective export.
- Additional source adapters admitted through the source-neutral scorecard and
  professional-review gates.
- Provider-authorized imports or background jobs with explicit authorization,
  budgets, pause conditions, audit history, and safe cancellation.
- Additional purpose-specific projections, family work packets, and broader
  relationship-aware workflows after the question-centered person-level research
  journey is proven usable.

These items are deliberately conditional. graver is not trying to become a
universal genealogy suite or infer relationships merely because software can draw
an enthusiastic line between two names.

## How roadmap changes are governed

- `ROADMAP.md` is the canonical public stage and feature summary.
- `docs/project-context.md` records detailed architectural reasoning and history.
- `docs/existing-system-inventory.md` records verified current implementation.
- Material direction changes update this roadmap; implementation details update the
  inventory; architectural decisions update the project context.
- Public roadmap changes never publish private commercial, scheduling, domain,
  financial, or entrepreneurial planning.

Suggestions are welcome through the repository's guided researcher-feedback and
issue forms. A proposed feature earns priority through demonstrated researcher
value, bounded scope, evidence integrity, responsible access, and maintainable
implementation—not merely because it would look impressive in a longer checklist.
