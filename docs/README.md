# Canonical project documentation

This directory is the canonical, version-controlled source for the project
context, existing-system inventory, and roadmap.

The [researcher tutorial](tutorial.md) is the canonical end-to-end guide for
using the implemented command-line workflow.

The [access policy](access-policy.md) defines current project governance for
responsible acquisition behavior and contributions.

The [developer API guide](api.md) documents the supported pre-1.0 typed application
boundary for CLI, future GUI, and other client adapters.

The [source-neutral adapter strategy](source-adapter-strategy.md) defines graver's
scope boundary, adapter roles, admission gates, prioritization scorecard, and
professional-review cadence. It is a guardrail against both source-specific core
design and unfocused expansion into a universal genealogy application.

The [trust, transparency, and openness architecture](trust-transparency-architecture.md)
defines the visible evidence, comparison, workflow, and conclusion layers needed
for professional trust; distinguishes computational replay from genealogical
reproducibility; and defines independently verifiable research artifacts.

The [source-neutral evidence packet review prototype](source-neutral-evidence-packet-prototype.md)
is the fictional, offline artifact for focused source-contract review S1. It tests
shared provenance, relationship, comparison-trace, and audit-portability
distinctions without defining a public format or implemented adapter.
The [initial S1 professional review](professional-researcher-s1-review-2026-08-23.md)
blocked the contract and records the corrections now awaiting focused re-review.

The [GEDCOM integration architecture](gedcom-integration.md) records a deliberately
optional, periodically re-evaluated direction for immutable import, comparison,
relationships, privacy, and selective export.

The [Professional Genealogist Usability Review](professional-genealogist-usability-review-2026-08-22.md)
preserves the first rigorous researcher-facing usability baseline. The accompanying
[principal architecture analysis](professional-usability-feedback-analysis-2026-08-22.md)
translates that review into product and engineering priorities.

The [evidence assessment and identity conclusion architecture](evidence-assessment-architecture.md)
defines the boundary between candidate discovery, machine ranking, researcher
assessment, and reviewed conclusions. It is the governing contract for the planned
offline evidence vertical slice and later FamilySearch-facing clients.

The [evidence contract review prototype](evidence-contract-review-prototype.md) is
the fictional, low-fidelity artifact for professional researcher gate R1. It is not
implemented product behavior.

The [first R1 professional researcher review](professional-researcher-r1-review-2026-08-23.md)
records the blocking and important findings from that artifact. R1 did not pass;
the [focused R1 re-review](professional-researcher-r1-rereview-2026-08-23.md)
subsequently verified all seven minimum corrections and passed the gate.

The [professional researcher review gates](researcher-review-gates.md) define the
R1 contract review, R2 offline-workflow validation, and R3 production acceptance
checkpoints. Each engagement uses the canonical
[professional researcher review report template](templates/professional-researcher-review-report.md).

The [R2 offline workflow review guide](r2-offline-workflow-review-guide.md) runs the
fictional ambiguous case through a disposable local browser adapter backed by the
real offline evidence service. It is a moderated-review artifact, not a production
GUI or supported public interface.

The [first R2 professional review](professional-researcher-r2-review-2026-08-23.md)
records the blocking decision-safety and citation-traceability findings that now
await focused re-review.

The [focused R2 re-review](professional-researcher-r2-rereview-2026-08-23.md)
records the remaining evidence-selection and negative-search presentation defects.
The [final focused verification](professional-researcher-r2-final-verification-2026-08-23.md)
confirmed both corrections with no new blockers, so R2 passes.

The outer project-level `docs/*.md` paths are local compatibility symbolic links
for tools and conversations that begin at the parent project root. Future
inventory, context, and roadmap changes must be made only in this directory.
The same rule applies to the tutorial and access policy: link to their canonical
paths in this directory rather than creating independent copies.
