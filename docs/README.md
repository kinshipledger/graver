# Canonical project documentation

The repository root promotes the public project contracts: the
[README](../README.md), [roadmap](../ROADMAP.md),
[changelog](../CHANGELOG.md), [contribution guide](../CONTRIBUTING.md),
[Code of Conduct](../CODE_OF_CONDUCT.md), [security policy](../SECURITY.md), and
[license](../LICENSE). This page maps the supporting researcher, developer,
architecture, review, and maintenance documents that remain in `docs/`.

The root [public roadmap](../ROADMAP.md) is the canonical concise stage and feature
summary. This directory contains the detailed, version-controlled
[project context and architectural history](project-context.md) and the
[verified existing-system inventory](existing-system-inventory.md). The
[initial inspection](initial-inspection.md) remains as dated historical context;
current behavior is recorded in the inventory.

The [visual identity and documentation graphics guide](visual-identity.md) records
the brand relationship, icon brief, diagram priorities, asset provenance, and
visual-review cadence.

The [first-time setup guide](first-time-setup.md) explains the terminal, uv,
command path, installation boundary, and local research database for readers who
do not routinely use developer tools.

The [researcher tutorial](tutorial.md) is the canonical end-to-end guide for
using the implemented command-line workflow.

The [research-state guide](research-states.md) explains every workflow state in
plain language, what it permits, and whether any network activity occurs.

The [acquisition-scope and citation guide](acquisition-scope.md) defines what
summary and full acquisition retain, what `full` does not promise, and what a
responsible citation or external research log must still supply.

The [access policy](access-policy.md) defines current project governance for
responsible acquisition behavior and contributions.

The [security threat model](security-threat-model.md) records assets, trust
boundaries, controls, known risks, and release gates. The companion
[privacy and data-handling guide](privacy-and-data-handling.md) explains what local
research data is retained, disclosed to providers, and safe to share.

The [provider acquisition and import decision](provider-import-decision.md) applies
that policy to the `1.0.0rc1` scope: bounded researcher-directed operations remain,
while unattended Find a Grave acquisition, a public job engine, and speculative
import APIs are deferred pending a concrete authorized workflow.

The [developer API guide](api.md) documents the supported pre-1.0 typed application
boundary for CLI, future GUI, and other client adapters.

The [command-line JSON contract](cli-json.md) defines the versioned envelope and
command identifiers used by supported machine-readable CLI results.

The [pre-1.0 command-line migration](cli-migration.md) maps removed compatibility
commands and provider-shaped search spellings to the supported CLI.

The [database upgrade and recovery guide](database-upgrades.md) explains the
explicit backed-up migration workflow, preservation guarantees, safe failure
behavior, and the limits of manual recovery.

The [1.0.0rc1 release notes](release-notes-1.0.0rc1.md) summarize the published
researcher and developer changes, compatibility breaks, deferred scope, and known
limitations. The [maintainer release process](releasing.md) defines the review gates
and manually triggered Release Please workflow.
The [bounded technical-publications review](technical-publications-review-2026-08-25.md)
records the final-1.0 researcher-documentation gate and its required corrections.
The [1.0.0rc1 readiness audit](rc1-readiness-audit.md) preserves the prepublication
review of the frozen public surfaces and release gates.

The [performance and responsiveness guide](performance.md) defines the generated
offline baseline, non-blocking weekly/manual measurement workflow, interpretation
rules, and provisional targets for the future desktop vertical slice.

The [live compatibility canary](live-canary.md) documents the explicitly invoked,
one-request Find a Grave transport/parser check, its safe result categories, and
the boundary separating it from ordinary offline tests and release automation.

The [source-neutral integration strategy](source-adapter-strategy.md) defines graver's
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
blocked the contract. The
[focused S1 re-review](professional-researcher-s1-rereview-2026-08-23.md) verified
every correction and passed the bounded internal contract.

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
records the original blocking decision-safety and citation-traceability findings.

The [focused R2 re-review](professional-researcher-r2-rereview-2026-08-23.md)
records the remaining evidence-selection and negative-search presentation defects.
The [final focused verification](professional-researcher-r2-final-verification-2026-08-23.md)
confirmed both corrections with no new blockers, so R2 passes.

The outer project-level `docs/*.md` paths are local compatibility symbolic links
for tools and conversations that begin at the parent project root. Future
inventory, context, and roadmap changes must be made only in this directory.
The same rule applies to the tutorial and access policy: link to their canonical
paths in this directory rather than creating independent copies.
