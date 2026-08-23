# Professional researcher review report

## Review record

- **Gate:** R1 — Evidence contract review
- **Review date:** 2026-08-23
- **Reviewer role and relevant experience:** Independent Professional Genealogist
  persona applying rigorous evidence-correlation and proof-standard expectations
- **Facilitator:** None; strict context-reset review
- **Product version or commit:** Review artifact merged at `7296865`
- **Issue:** [#26](https://github.com/mcqueary/graver/issues/26)
- **Environment and installation path:** Documentation-only review; no installation
- **Interface and documentation reviewed:**
  [`evidence-contract-review-prototype.md`](evidence-contract-review-prototype.md)

## Review objective

Determine whether the proposed evidence terminology, comparison workflow,
provenance presentation, acquisition receipt, citation, and conclusion controls
support defensible professional research before persistence is implemented.

## Scenario and artifacts

The reviewer used the fictional Eleanor May Carter scenario in the low-fidelity R1
artifact. It presents one active Find a Grave-centered subject, two fictional
FamilySearch-shaped candidates, a material parentage conflict, source-displayed
family links, assessment history, two example conclusions, an acquisition receipt,
and a draft citation. No implementation, live provider, roadmap, schema, or source
code was consulted.

## Tasks attempted

| Task | Completed? | Assistance required | Notes |
|---|---|---|---|
| Identify subject and candidate | Yes | None | Identities remained distinct. |
| Interpret candidate ordering | Yes | None | Review order was distinguished from probability and proof. |
| Correlate agreements, omissions, and conflict | Yes | None | Parentage was correctly treated as material. |
| Plan additional research | Yes | None | Original records, source quality, independence, timelines, and family reconstruction were required. |
| Evaluate states and dispositions | Yes | None | Several labels need stronger definitions. |
| Inspect receipt and citation | Yes | None | Both need more precise provenance language. |

## Research continuity observations

- Active subject and candidate context remained visible and distinct.
- Assessment history and stale-edit protection support accountability, provided
  visible history includes author, date, reason, state change, and prior entry.
- The workflow still requires an external log for research objectives, source
  evaluation, search scope, negative results, source dependence, hypotheses,
  changing online profiles, and reproducible evidence references.
- Generic evidence labels cannot reconstruct which observation or record supported
  a conclusion after later observations arrive.

## Evidence and conclusion observations

- Candidate ordering, evolving assessment, and identity conclusion are
  conceptually well separated.
- Agreement counts may nevertheless resemble confidence unless labeled as
  unweighted discovery-comparison counts.
- “Exact” must mean exact value agreement, not truth, independence, or identity.
- “Accepted” must mean accepted as the same person, not acceptance of every
  candidate assertion.
- The accepted example assigns an unsupported cause (“transcription error”) and
  calls records independent without analyzing their derivation or informants.
- A defensible conclusion needs inspectable evidence references and an analysis of
  source quality, informant knowledge, temporal proximity, and dependence when
  material.

## Persistence and provenance observations

- The receipt explains the operation's broad scope, but “updated” hides which
  displayed values changed and where the retained before-and-after observations
  can be inspected.
- “Immutable observations” should be expressed to researchers as dated snapshots
  retained without replacing earlier snapshots.
- The citation must describe only captured content. “Database and images” is
  unsupported when no image was captured or examined.
- Missing-on-page, not-collected, outside-scope, and unavailable information are
  materially different provenance conditions and must remain distinguishable.
- Source-displayed family links are useful leads but must carry their non-proof
  warning in headings and exported representations.

## Onboarding and terminology observations

- “Ready for decision” is a workflow state, not proof of evidentiary sufficiency or
  completion of reasonably exhaustive research.
- “Deferred” needs a reason and follow-up condition; “reopened” needs a reason and
  a link to the earlier assessment or conclusion.
- “Withdrawn” is a status applied to a prior conclusion, not a new identity
  determination.
- The active subject summary should be labeled as a working profile, with routes
  from material values to their evidentiary basis and conclusion status.

## Findings

| ID | Severity | Finding | Evidence | Recommended response |
|---|---|---|---|---|
| R1-01 | Blocking | Conclusion references are generic field names, not reconstructable evidence references. | Section 5 lists “birth, death, burial, father.” | Require inspectable observation/record, date, and assertion/comparison references beside the reasoning. |
| R1-02 | Important | The accepted example assigns an unsupported transcription-error cause. | Section 5 later decision. | Describe the Thomas assertion as conflicting and less reliable for stated reasons unless transcription is demonstrated. |
| R1-03 | Important | Claimed source independence is not analyzed. | Section 5 marriage/death example. | Address creator, informant, timing, derivation, and independence when material. |
| R1-04 | Important | “Database and images” implies image examination not established by the capture. | Section 7 citation. | Cite only content actually observed; include images only when identified and examined. |
| R1-05 | Important | Missing source information is conflated with uncaptured information. | Section 7 attribution note. | Record whether absent on page, not collected, outside scope, or unavailable. |
| R1-06 | Important | Assessment-state meanings and triggers are ambiguous. | Section 4 controls. | Define every state; require reasons for deferral and reopening; disclaim evidentiary endorsement. |
| R1-07 | Important | “Accepted” may imply acceptance of all candidate assertions. | Section 5 dispositions. | Label it accepted as the same person and preserve assertion-level uncertainty. |
| R1-08 | Important | “Related memorials” may imply proven kinship when separated from its disclaimer. | Section 3 family panel. | Use “Find a Grave-displayed relationship links” and carry the non-proof warning with every representation. |
| R1-09 | Follow-up | Agreement/conflict counts resemble a confidence score. | Section 2 ordering table. | Label them unweighted discovery-comparison counts, not evidentiary strength. |
| R1-10 | Important | “Exact” can imply factual truth or corroboration. | Section 3 classifications. | Use “exact value agreement” and define its limits. |
| R1-11 | Follow-up | Mother and spouse receive inconsistent classifications for absent comparison values. | Section 3 table. | Explain the distinction or use one “not stated; external research required” category. |
| R1-12 | Important | The acquisition receipt hides which current values changed. | Section 6 “existing memorials updated.” | Identify memorials and changed fields, with routes to earlier and later snapshots. |
| R1-13 | Follow-up | The negative probate search lacks reproducible scope. | Section 4 notes. | Capture collection, coverage, jurisdiction, date, variants, method, and limitations. |
| R1-14 | Follow-up | Subject vital details do not reveal whether they are observations or working conclusions. | Section 1 subject summary. | Label the working profile and link material values to evidence and status. |
| R1-15 | Follow-up | Visible history requirements are underspecified. | Section 4 history. | Show author, date, reason, changed state, and prior entry—not only a version. |

## Decisions and accepted terminology

The review accepts the separation among discovery order, assessment, and conclusion,
but requires safer labels and inspectable provenance. The following terms are the
working direction pending re-review:

- **Discovery review order**, not confidence ranking
- **Exact value agreement**, not exact evidence or proof
- **Accepted as the same person**, not acceptance of candidate assertions
- **Find a Grave-displayed relationship links — website display, not proven kinship**
- **Dated retained snapshots**, with earlier snapshots not replaced

## Blocking-finding resolution

R1-01 was unresolved in the artifact reviewed by this report. The revised artifact
demonstrates specific, durable, human-readable evidence references. The independent
[focused re-review](professional-researcher-r1-rereview-2026-08-23.md) verified all
seven minimum corrections and passed R1. No risk acceptance was required.

## Deferred questions

- What minimum external-research-log content belongs in later product scope?
- How should negative searches be represented without implying proof of absence?
- Which assertion-quality concepts are essential without overwhelming researchers?
- How should working subject-profile values expose evidence and conclusion status?

## Baseline comparison

Not applicable; this is the first R1 review of this artifact.

## Gate decision

- **Decision:** Does not pass
- **Decision maker:** Independent Professional Genealogist persona
- **Decision date:** 2026-08-23
- **Blocked milestone may proceed:** No
- **Conditions or follow-up issues:** Resolve the seven minimum changes enumerated
  below and conduct a focused R1 re-review.

Minimum changes required before re-review:

1. Demonstrate specific, inspectable conclusion evidence references.
2. Remove unsupported causal and source-independence claims from the example.
3. Define acceptance as a same-person conclusion only.
4. Define all assessment states and their required reasons or triggers.
5. Rename source-displayed relationship links and carry the non-proof warning.
6. Make the citation capture-faithful and distinguish absence from non-collection.
7. Show exactly what changed when acquisition revises a current representation.

## Next review trigger

Completed: the focused R1 re-review passed on 23 August 2026. The next engagement is
R2 after the complete curated offline workflow becomes experiential.
