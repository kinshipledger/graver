# Professional researcher R1 focused re-review

## Review record

- **Gate:** R1 — Evidence contract review
- **Review date:** 2026-08-23
- **Reviewer role:** Independent Professional Genealogist persona
- **Review method:** Strict context reset; focused verification only
- **Product version or commit:** Revised artifact merged at `d08a918`
- **Issue:** [#26](https://github.com/kinshipledger/graver/issues/26)
- **Artifact reviewed:**
  [`evidence-contract-review-prototype.md`](evidence-contract-review-prototype.md)
- **Material excluded:** Source code, schemas, tests, roadmaps, architecture,
  GitHub history, and the initial R1 report

## Review objective

Verify only the seven minimum corrections required by the initial blocked R1
review, identify any new blocker introduced by those revisions, and determine
whether candidate/evidence persistence may proceed.

## Focused verification

### 1. Specific, inspectable evidence references — Verified

Section 5 requires references to particular observations or records, relevant
assertions, and observation dates. The examples identify snapshot IDs,
record-observation IDs, comparison IDs, dates, and assertion categories. This gives
a researcher a credible route from a conclusion back to the evidence examined.

### 2. Unsupported causal and independence claims — Verified

The later conclusion no longer diagnoses a transcription error. It says the cause
is unknown and explains why the assertion is judged less reliable. It identifies
William Reed as the death-certificate informant and does not treat the marriage and
death records as independent for their repeated assertions.

### 3. Acceptance limited to a same-person conclusion — Verified

“Accepted as the same person” expressly does not accept every assertion on either
profile. Each assertion retains its own evidentiary status.

### 4. Assessment states and required triggers — Verified

All five states are defined. Deferral requires a reason and follow-up condition or
review date. Reopening requires a reason and link to the earlier record. Ready for
decision is a workflow choice, not confidence, proof, certification of exhaustive
research, or automatic permission to conclude.

### 5. Source-displayed relationship links — Verified

The heading “Find a Grave-displayed relationship links — website display, not
proven kinship” states the limit directly. The contract requires the warning to
travel with the values in every display, citation, export, and machine-readable
representation.

### 6. Capture-faithful citation language — Verified

The citation says “memorial database,” identifies the retained snapshot, and says
that contributor information, images, attribution, and underlying sources were
outside the fictional capture scope and not collected. It does not imply that an
image or underlying record was examined.

### 7. Changed values and snapshot history — Verified

The receipt identifies each affected memorial, its before-and-after value, and the
earlier and later snapshot identifiers. It says dated snapshots were retained
without replacing earlier snapshots.

## New blockers

None. The revisions do not convert discovery order, website displays, repeated
assertions, or assessment states into proof.

## Blocking-finding resolution

Initial finding R1-01 is resolved and independently verified. All seven minimum
corrections are verified. No risk acceptance is required.

## Gate decision

- **Decision:** Pass
- **Decision maker:** Independent Professional Genealogist persona
- **Decision date:** 2026-08-23
- **Blocked milestone may proceed:** Yes
- **Conditions:** The accepted terminology and invariants must remain part of the
  implementation contract. Non-blocking findings remain candidates for R2 or the
  ordinary backlog.

## Next review trigger

R2 begins when the complete curated, offline evidence workflow is available as an
experiential adapter or prototype. It must be reviewed before the public workspace
façade or detailed evidence-GUI information architecture is frozen.
