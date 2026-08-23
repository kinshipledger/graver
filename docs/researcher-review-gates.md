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

## R1 — Evidence contract review

**Current status:** Does not pass. The
[23 August 2026 review](professional-researcher-r1-review-2026-08-23.md) identified
one blocking and nine important findings. The low-fidelity artifact has been
revised, but candidate/evidence persistence remains blocked until a focused
independent re-review verifies the seven minimum corrections.

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
