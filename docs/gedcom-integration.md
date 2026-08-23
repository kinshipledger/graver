# GEDCOM integration architecture

Status: exploratory nice-to-have; not implemented and not on the pre-1.0 critical
path. Re-evaluate after graver's core subject, work, provenance, API, and GUI
assumptions have been tested through real researcher workflows.

## Purpose

If demonstrated research needs justify it, GEDCOM should extend graver's evidence-
centered research workflow, not turn graver
into a general-purpose family-tree editor or make an interchange file authoritative.
GEDCOM contributes portable people, family relationships, events, sources, notes,
identifiers, and media references. graver contributes source-aware comparison,
repeatable research queues, discrepancy detection, reviewed mappings, reasoning,
confidence, and immutable decision history.

The central product proposition is:

> GEDCOM supplies a portable relationship graph and genealogical assertions;
> graver compares those assertions with observed evidence and supports reviewable
> conclusions.

## Re-evaluation gates

Do not begin implementation merely because this design exists. Reassess GEDCOM at
the 1.0 release-candidate review, after the first production GUI work-queue vertical
slice has been road-tested, and when a concrete import, comparison, or export need is
reported. Each review should ask:

- Which current researcher problem would GEDCOM solve better than existing work?
- Is the need import, comparison, research seeding, selective export, or merely file
  conversion better handled by another tool?
- Can graver preserve provenance and uncertainty without complicating its core API?
- Are representative privacy-safe files and independent consumer applications
  available for testing?
- Does the expected value justify parser, compatibility, privacy, and maintenance
  costs ahead of the next core roadmap item?

Until those questions have favorable evidence, GEDCOM remains documentation-only
and must not become a release criterion, schema dependency, public API promise, or
reason to delay core researcher workflows.

GEDCOM is one candidate import/export adapter under the broader
[source-neutral adapter strategy](source-adapter-strategy.md). It must pass the same
admission gates and scoring process as other candidates; its popularity does not
grant it roadmap priority.

## Candidate capability order

1. **Immutable import and inspection.** Read a GEDCOM dataset, identify its version
   and producer, validate its structure, preserve its file hash and import metadata,
   and report unsupported structures without changing research conclusions.
2. **Repeatable comparison.** Compare imported people, facts, and relationships with
   graver subjects and evidence. Reimporting a changed file creates a new snapshot
   and comparison run; it never overwrites earlier imports.
3. **Research seeding.** Allow reviewed imported assertions to create candidate
   subjects, facts, relationships, and work—not accepted identity conclusions.
4. **Reviewed mappings and relationships.** Record proposed, accepted, rejected,
   and superseded mappings between dataset-scoped people and research subjects,
   with evidence, reasoning, reviewer information, and immutable history.
5. **Selective export.** Produce privacy-reviewed GEDCOM 7 subsets such as one
   subject and immediate family, a family work packet, or reviewed changes. Whole-
   database export is deferred until its semantics and demand are demonstrated.
6. **GEDZIP and broader compatibility.** Consider bundled media and additional
   export targets only after ordinary `.ged` workflows are dependable.

## Domain boundaries

GEDCOM does not define graver's internal database or public API. The provider-neutral
domain must be able to represent:

- research subjects that do not originate with Find a Grave memorials;
- alternative, conflicting, and negative fact assertions;
- directional relationship assertions with roles, evidence, and review state;
- immutable external-dataset snapshots and repeatable comparison runs;
- dataset-scoped external people, families, sources, citations, notes, identifiers,
  extensions, and media references;
- proposed and reviewed mappings from external people to research subjects; and
- reviewed conclusions that remain distinct from imported assertions.

A GEDCOM cross-reference such as `@I42@` is meaningful only within one imported
dataset snapshot and must never become a graver subject identifier. Importing a
family record does not establish that its relationships are correct. Imported
values do not overwrite memorial observations, subject history, or conclusions.

The anticipated ownership shape is:

```text
research subject
  ├── observed, candidate, and concluded facts
  ├── relationship assertions and reviewed conclusions
  ├── evidence references
  └── reviewed external-record mappings

GEDCOM import snapshot
  ├── external person and family records
  ├── facts and relationship assertions
  ├── source, citation, note, identifier, and media references
  └── comparison runs and mapping proposals
```

## Versions and interoperability

The [FamilySearch GEDCOM 7 specification](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html)
is the preferred native import and first export target. A read boundary for GEDCOM
5.5.1 is also required because it remains common in existing applications; the
[official specification index](https://gedcom.io/specs/) confirms that 5.5.1 and 7
are distinct formats and they must not be silently conflated. Export to 5.5.1
requires a demonstrated consumer need. Unknown extensions and information that
cannot be represented must be preserved where feasible and reported explicitly,
never silently discarded.

Before choosing a parser library, evaluate supported GEDCOM versions, malformed-file
behavior, extension preservation, lossless or inspectable representation,
round-trip limitations, maintenance, security posture, licensing, performance, and
Python 3.11–3.14 support. Do not build a comprehensive parser until this evaluation
shows that an existing maintained implementation is unsuitable.

## Public API and user experience

GEDCOM operations belong behind the same synchronous, typed application workspace
used by the CLI and future GUI. Public services should accept explicit paths or
streams and return graver-owned results and errors; they must not expose parser
nodes, SQLite rows, or toolkit types. Import, comparison, mapping, and export are
separate operations with progress, cancellation, deterministic ordering, and stale-
update protection where applicable.

The CLI should expose researcher goals rather than the underlying tag vocabulary.
The future GUI should emphasize discrepancies and actionable research rather than
displaying an entire imported tree at once. Both adapters must use the same services
and contract tests.

## Provenance, privacy, and safety

- Record the source filename as safe metadata, file hash, byte size, GEDCOM version,
  producer metadata, import time, parser version, and any warnings.
- Treat each import as immutable. A revised file creates a new snapshot linked to
  its predecessor where known.
- Preserve original files only through an explicit retention policy; a hash and
  parsed snapshot do not by themselves authorize redistribution.
- Treat living-person data as sensitive. Inspection, logs, JSON, diagnostics,
  examples, exports, and GUI displays require privacy-conscious defaults.
- Export only deliberately selected, reviewed information and disclose omitted or
  downgraded structures.
- Use synthetic or explicitly sanitized fixtures in the repository. Never commit a
  researcher's private GEDCOM or GEDZIP file.

## Acceptance strategy

If authorized after re-evaluation, the first implementation milestone is read-only
and offline. It must cover small
GEDCOM 7 and 5.5.1 fixtures; duplicate and malformed records; unknown extensions;
conflicting facts; family relationships; citations; deterministic import hashes;
repeat imports; cancellation; rollback; and network denial. Contract tests must
prove that import creates no accepted mappings, relationships, or identity
conclusions.

Later comparison tests must exercise changed snapshots, stable subject candidates,
relationship-supported and relationship-conflicting matches, false-positive
rejection, and reproducible results. Export tests require structural validation,
round-trip characterization, privacy filtering, explicit loss reports, and opening
the generated file in at least one independent implementation before release.

## Deferred decisions

The parser library, detailed schema names, relationship vocabulary, comparison
scoring, file-retention policy, GUI presentation, GEDZIP support, 5.5.1 export, and
whole-database export remain open. They require prototypes and representative,
privacy-safe fixtures before becoming public compatibility promises.
