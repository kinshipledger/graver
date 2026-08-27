# Professional researcher review gates

**Status:** Active project governance
**Established:** 2026-08-22

## Purpose

Professional researcher review is an explicit product and release control, not an
informal consultation or a calendar reminder. Reviews occur when a researcher-facing
decision is concrete enough to experience, still inexpensive to change, and
important to the meaning or continuity of genealogical research.

The gates below keep professional alignment on the development path without asking
researchers to review repository refactors, dependency changes, migrations, CI, or
other infrastructure that does not alter their experience.

Technical-publications review complements these gates but does not replace them.
A technical writer evaluates whether instructions are findable, consistent, and
usable; a professional genealogist evaluates whether their meaning remains safe for
research and evidence. The final-1.0 review described below deliberately uses both
roles without asking either reviewer to repeat the other's work.

Any visual artifact that frames research flow, source quality, evidence comparison,
confidence, identity, kinship, provenance, or a consequential action is part of the
review packet. The reviewer evaluates what the visual implies as well as what its
caption says; a diagram cannot quietly claim more than the underlying workflow.

Researcher-facing reviews also test plain-language comprehension. At least one
review perspective must represent a capable genealogist who is not highly technical,
does not know graver's internal vocabulary, and describes ordinary research without
software or database terminology. The reviewer first explains the workflow in their
own words without a supplied glossary, then identifies unfamiliar, ambiguous, or
needlessly technical language and the action they believe each control or step will
perform. Correct implementation terminology does not excuse researcher-facing copy
that requires technical translation.

Every reviewed diagram or instruction set must declare its intended audience. A
researcher-facing artifact must lead with familiar research actions and consequences;
machine values and implementation concepts belong in secondary detail. Developer-
facing artifacts may use precise technical vocabulary but must not be mistaken for
onboarding material.

## Governing rule

> A professional-researcher review gate is complete only when the review occurred
> against an experiential artifact, its findings were recorded, and every blocking
> finding was resolved or explicitly accepted with a written rationale.

A plan, document review by the development team, automated test, or statement that
researcher review will happen later does not complete a gate.

## Gate register

| Gate | Tracking issue | Trigger | Review artifact | Blocks |
|---|---|---|---|---|
| R1 — Evidence contract review | [#26](https://github.com/mcqueary/graver/issues/26) | Subject-oriented service boundary is stable and low-fidelity evidence workflow artifacts are ready | Terminology, evidence matrix, ranking explanation, decision flow, acquisition receipt, and citation example | Candidate/evidence persistence implementation |
| R2 — Offline workflow validation | [#27](https://github.com/mcqueary/graver/issues/27) | Fixture-driven evidence slice works end to end | Moderated ambiguous-case workflow and recorded usability report | Public workspace façade freeze and detailed evidence-GUI design |
| R3 — Evidence-workflow acceptance | [#28](https://github.com/mcqueary/graver/issues/28) | Production GUI supports candidate comparison and reviewed conclusions | Repeat of the original professional usability audit using ordinary installation and documentation | Declaring the evidence workflow production-ready and expanding it into WikiTree/family workflows |

R1–R3 govern the current evidence workflow. Materially new source families use the
same governing rule through focused source reviews rather than waiting for another
large numbered gate:

- **Source contract review:** before source-facing public types are frozen or a new
  evidence family introduces unreviewed genealogical semantics.
- **Source vertical-slice review:** after its first usable, privacy-safe workflow and
  before the adapter is described as production-ready.
- **Portfolio review:** after every two completed adapters or six months, whichever
  comes first, to re-score candidates and stop, defer, or narrow work that no longer
  advances demonstrated researcher needs.

These focused reviews follow the same artifact, report, severity, and blocking-
finding rules as the numbered gates. The canonical selection criteria and scope
guardrails are in the
[source-neutral integration strategy](source-adapter-strategy.md).

### S1 — Source-neutral evidence packet contract review

**Current status:** Passed on focused re-review. The fictional
[source-neutral evidence packet prototype](source-neutral-evidence-packet-prototype.md)
uses synthetic marriage/death, census, probate, and memorial representations to
test shared distinctions, a deterministic comparison trace, and a minimum audit
projection. It adds no provider, parser, public format, schema, or runtime behavior.

The [initial S1 report](professional-researcher-s1-review-2026-08-23.md) records
seven blocking, three important, and one follow-up finding tracked in
[#56](https://github.com/mcqueary/graver/issues/56). The
[focused S1 re-review](professional-researcher-s1-rereview-2026-08-23.md) verified
all ten corrected requirements, found no new blocker, and passed the gate.

S1 now permits a bounded internal implementation prototype of the reviewed shared
distinctions. It does not approve a public packet format, frozen public schema,
provider adapter, exhaustive source taxonomy, or automated identity or kinship
conclusion.

Entry criteria are satisfied when the artifact accurately labels all content as
synthetic, carries explicit non-goals, and can be reviewed without developer or
schema knowledge. Exit requires a dated report, resolution or explicit acceptance
of every blocking finding, and reconciliation of the trust, evidence, source-
adapter, API, and roadmap documents.

## R1 — Evidence contract review

**Current status:** Passed. The initial
[23 August 2026 review](professional-researcher-r1-review-2026-08-23.md) identified
one blocking and nine important findings. The independent
[focused re-review](professional-researcher-r1-rereview-2026-08-23.md) verified all
seven minimum corrections with no new blockers. Candidate/evidence persistence may
proceed under the accepted contract; R2 subsequently passed as recorded below.

### Objective

Validate the meaning and presentation of candidate, evidence, ranking, assessment,
conflict, citation, and conclusion concepts before persistence makes those concepts
expensive to change.

### Entry criteria

- Remaining subject-oriented repository and application-service refactor is stable.
- No raw persistence row is being proposed as the public result contract.
- A low-fidelity subject/candidate comparison artifact exists.
- The artifact contains at least two plausible candidates and one material conflict.
- Proposed evidence classifications and conclusion dispositions are defined.
- A candidate-ranking explanation is visible and clearly separated from the human
  conclusion.
- Example acquisition receipt and Find a Grave citation are available.
- Review uses no live FamilySearch request and no production GUI is required.

### Researcher tasks

1. Identify the active research subject and the candidate under review.
2. Interpret agreements, missing information, and a material conflict.
3. Explain what the proposed candidate ranking means.
4. Determine what further research is needed.
5. Review the proposed defer, reject, accept, unresolved, withdraw, and supersede
   vocabulary.
6. Inspect the example persistence receipt and citation.

### Questions to answer

- Is any term likely to imply proof or certainty that the evidence does not support?
- Can machine ordering be mistaken for a human conclusion?
- Are supporting, conflicting, missing, derivative, and unresolved evidence
  distinguishable?
- Are the conclusion requirements sufficient for a reasoned decision?
- Are the receipt and citation understandable without database inspection?
- What information would still require an external note?

### Exit criteria

- A dated report uses the canonical review-report template.
- Every blocking semantic or workflow finding is resolved or explicitly accepted
  with rationale.
- Accepted terminology and decision rules are reflected in the evidence architecture.
- The GitHub gate issue links the report and resolution changes.

## R2 — Offline workflow validation

**Current status:** Passed. The
[23 August 2026 review](professional-researcher-r2-review-2026-08-23.md) found two
blocking failures: a same-person conclusion could supersede an earlier conclusion
without researcher-authored analysis or inspectable evidence selection, and material
assertions lacked visible citation-level traceability. The correction slice now
requires authored analysis, explicit conflict treatment, and real same-subject
evidence references; it also exposes citations, provenance, comparison references,
and changed values.

The [first focused re-review](professional-researcher-r2-rereview-2026-08-23.md)
verified supersession safeguards, assertion traceability, and change visibility, but
kept R2 blocked because an unresolved conclusion did not retain the evidence the
researcher selected and the saved negative-search display omitted reproducibility
details. After those two narrow corrections, the
[final focused verification](professional-researcher-r2-final-verification-2026-08-23.md)
confirmed exact evidence-selection fidelity and complete visible negative-search
reproducibility with no new blockers. R2 therefore passes. The public workspace
façade and detailed evidence-UX design may proceed under the validated contract.

### Objective

Validate research continuity and evidentiary control after the complete offline
candidate/evidence slice exists, but before its typed results are frozen as the
public workspace contract.

### Entry criteria

- Curated fixtures represent multiple plausible candidates.
- At least one candidate changes between discovery runs.
- At least one prior candidate is absent from a later run but remains preserved.
- The scenario includes a material fact or relationship conflict, missing data, and
  a derivative or non-independent source.
- The workflow supports negative searches, unresolved questions, deferral,
  reopening, and immutable conclusion supersession.
- The workflow is available through an experiential test adapter or prototype, not
  merely unit-level domain calls.

### Researcher tasks

```text
review subject
  → inspect multiple candidates
  → examine agreements, sources, and conflicts
  → record a negative search and unresolved question
  → defer a candidate
  → resume the research later
  → record a conclusion
  → supersede that conclusion after changed evidence
```

### Observations to capture

- Loss of active-person or active-candidate context
- Confusion between ranking, assessment, and conclusion
- Missed or misunderstood material conflicts
- Inability to trace a fact to its observation and citation
- External notes, spreadsheets, identifiers, or manual copying required
- Difficulty recovering prior reasoning
- Accidental or premature conclusions

### Exit criteria

- A dated moderated-review report is complete.
- Blocking continuity, provenance, or decision-safety findings are resolved or
  explicitly accepted with rationale.
- The public workspace façade and detailed GUI information architecture have not
  been frozen before resolution.
- The GitHub gate issue links the report, findings, and resolution changes.

## R3 — Evidence-workflow acceptance

### Objective

Determine whether the production GUI and ordinary documentation expose the sound
research model without hiding provenance, encouraging premature conclusions, or
requiring developer knowledge.

### Entry criteria

- A normally installable production GUI supports subject context, candidate
  comparison, evidence inspection, assessment, and reviewed conclusions.
- Researcher onboarding, citations, backups, recovery, privacy, and limitations are
  documented.
- The reviewer can use an isolated project without repository or schema knowledge.
- Known live-provider limitations and authorization requirements are stated.

### Review method

Repeat the
[Professional Genealogist Usability Review](professional-genealogist-usability-review-2026-08-22.md)
from scratch. Do not brief the reviewer on implementation details. Use ordinary
installation, visible help, the normal GUI, and researcher documentation.

Compare the results with the original baseline:

| Dimension | Original baseline |
|---|---:|
| Find a Grave–FamilySearch corroboration | 0/5 |
| Confidence and proof support | 1/5 |
| Persistence and citation clarity | 3/5 |
| Professional onboarding | 2/5 |

### Exit criteria

- A dated independent acceptance report is complete.
- The report identifies improvements and regressions.
- Blocking findings are resolved or explicitly accepted with rationale.
- The product is not described as production-ready for evidence assessment until
  the gate is complete.
- The GitHub gate issue links the report and final decision.

## Researcher review queue

Questions that arise between gates belong here rather than triggering repeated
interruptions. Remove an item only when its answer is recorded in a gate report or
an approved architecture decision.

Initial queue:

- Is **material conflict** understandable and appropriately scoped?
- Is **candidate ranking** safely distinguished from confidence and proof?
- Which citation elements are indispensable for professional use?
- Is withdrawing a conclusion meaningfully distinct from rejecting a candidate?
- How should indirect, conflicting, and derivative evidence be represented without
  imposing false precision?
- What is the minimum useful treatment of negative searches and unresolved
  questions?
- Which relationship comparisons provide the most value without overwhelming the
  researcher?
- What reviewer attribution is appropriate for a single-user local application?
- Which distinctions in synthetic civil, census, and probate examples are genuinely
  shared source-contract needs rather than premature ontology design?
- Which adapter candidate solves the strongest demonstrated researcher problem
  after authorization, provenance, privacy, fixture, and conclusion-safety gates?
- Can a researcher understand and reproduce candidate ordering from the visible
  comparison trace without reading source code or configuration syntax?
- Does the audit projection retain everything needed to interpret observations,
  transformations, selected evidence, conflicts, and conclusions independently?
- Is any configurable rule weakening an evidence-integrity safeguard that should be
  invariant?

## Finding severity

### Blocking

The issue could cause mistaken identity, lost provenance, unreviewed conclusions,
destructive research-history changes, material misunderstanding of evidence, or
inability to complete the target workflow. The blocked milestone cannot proceed
without resolution or explicit documented risk acceptance.

### Important

The issue creates substantial friction or weakens professional usefulness but does
not make the workflow unsafe. It receives a tracked issue and target milestone.

### Follow-up

The issue is a bounded usability improvement or future opportunity. It remains in
the backlog with enough context to reproduce it.

## Engagement discipline

Use short consultations between formal gates only when a decision has genuine
genealogical meaning, such as citation elements, evidence terminology, conclusion
vocabulary, negative searches, conflicts, or relationship evidence. Present one
concrete example and a bounded question.

Do not engage the professional researcher merely to validate internal refactors,
dependency changes, migration mechanics, CI, test organization, or adapter changes
that preserve visible behavior.

## Final-1.0 technical-publications gate

Tracking issue [#95](https://github.com/mcqueary/graver/issues/95) defines a bounded
professional technical-publications review before final `1.0.0`. It begins only
after the RC findings for acquisition scope ([#94](https://github.com/mcqueary/graver/issues/94)),
research-state and network terminology ([#92](https://github.com/mcqueary/graver/issues/92)),
and first-time onboarding ([#91](https://github.com/mcqueary/graver/issues/91))
are reflected in the researcher-facing material. If the enrichment change receipt
in [#93](https://github.com/mcqueary/graver/issues/93) is ready, its terminology and
instructions join the review packet.

The technical writer reviews only the README installation/getting-started path,
researcher tutorial, core command help, acquisition-scope and citation guidance,
and the errors or recovery language encountered in that workflow. Architecture
documents, historical audits, internal API material, CI, and roadmap prose remain
out of scope unless ordinary researcher instructions require them.

The review answers whether prerequisites precede actions; terms agree across help
and prose; offline, network, and database-changing operations are distinguishable;
safe recovery is findable; content is organized around researcher tasks; and
capture/citation limitations appear when they matter. It also asks a low-technical-
literacy reviewer to paraphrase the ordinary workflow without a glossary, predict
what each consequential action will do, and flag wording that is accurate only to a
software specialist. Its dated report uses the same Blocking, Important, Follow-up,
and Observation severities and an explicit PASS, PASS WITH FOLLOW-UPS, or BLOCKED
disposition. Style preferences alone do not become release blockers; language that
causes a reasonable researcher to misunderstand an action or its consequence may.

After corrections, a professional genealogist performs a short semantic
verification limited to evidentiary meaning, capture-scope accuracy, and network
consequences. The complete RC workflow is repeated only if the review caused a
material workflow change. Unresolved blocking findings require a recorded risk
decision before final `1.0.0`.

## Front-end UX and UI review cadence

Production front-end work uses small, decision-timed reviews rather than a single
late design sign-off. Each review receives a concrete artifact, written objectives,
representative tasks, recorded findings, and an explicit disposition. Purely
internal refactors do not trigger these reviews.

1. **Information architecture and content review:** before navigation, terminology,
   subject/candidate context, or evidence hierarchy is frozen. Use low-fidelity
   flows and include a professional researcher, a low-technical-literacy usability
   perspective, and a UX lead. Require unaided paraphrase of the primary workflow;
   do not teach the product vocabulary before measuring comprehension.
2. **Interaction and continuity review:** after the primary workflow is clickable
   but before production widget implementation is expensive to change. Exercise
   interruption, resumption, conflicts, errors, empty states, and stale edits.
3. **Visual-system and accessibility review:** before the component system and
   production layouts are declared stable. Check keyboard-only operation, focus,
   semantics, contrast, scaling, reduced motion, error recovery, and platform
   conventions; include disabled users or an accessibility specialist when
   practical. Include icon comprehension, light/dark rendering, diagram meaning,
   and consistency with the documented visual system.
4. **Pre-release usability review:** against an installable release candidate with
   representative data and ordinary documentation. R3 supplies the professional
   evidence-workflow portion; additional usability and accessibility findings are
   recorded separately rather than diluted into R3.

A front-end phase cannot pass its corresponding design freeze with an unresolved
blocking finding unless the risk, rationale, owner, and review date are explicitly
accepted. Important findings receive tracked issues. Follow-up observations remain
in the UX backlog with enough context to reproduce them.
