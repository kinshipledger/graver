# Canonical project documentation

This directory is the canonical, version-controlled source for the project
context, existing-system inventory, and roadmap.

The [researcher tutorial](tutorial.md) is the canonical end-to-end guide for
using the implemented command-line workflow.

The [access policy](access-policy.md) defines current project governance for
responsible acquisition behavior and contributions.

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

The outer project-level `docs/*.md` paths are local compatibility symbolic links
for tools and conversations that begin at the parent project root. Future
inventory, context, and roadmap changes must be made only in this directory.
The same rule applies to the tutorial and access policy: link to their canonical
paths in this directory rather than creating independent copies.
