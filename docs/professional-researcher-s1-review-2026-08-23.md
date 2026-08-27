# Professional researcher S1 review — 2026-08-23

## Review record

- **Gate:** S1 — Source-neutral evidence packet contract review
- **Review date:** 23 August 2026
- **Reviewer role:** Professional Genealogist, reviewing under professional evidence
  and reproducibility expectations
- **Product version or commit:** Artifact merged at `77fad3f`
- **Tracking issue:** [#56](https://github.com/kinshipledger/graver/issues/56)
- **Artifact:** [Source-neutral evidence packet review prototype](source-neutral-evidence-packet-prototype.md)
- **Method:** Strict context reset; artifact-only review without source code, schema,
  roadmap, or implementation knowledge

## Review objective

Determine whether the fictional source-neutral packet preserves source identity,
assertion attribution, relationship restraint, comparison transparency, conflict
permanence, researcher control, and independently interpretable audit portability
across synthetic marriage/death, census, probate, candidate-profile, and memorial
representations.

## Findings

### S1-01 — Source identity is not complete for every packet item

- **Severity:** Blocking
- **Artifact sections:** 2–3
- **Finding:** The artifact conceptually separates creator, repository, platform,
  carrier, source class, and representation examined, but does not display every
  value for each item. The memorial lacks adequate item-level identity and snapshot
  provenance.
- **Required correction:** Give every item explicit creator, represented repository
  or custodian, access surface, source class, carrier or record form, representation
  examined, and unknown/inapplicable values. Add a capture-faithful memorial
  citation and snapshot identity.

### S1-02 — Most citations are capture-faithful, but F1 is uncited

- **Severity:** Blocking
- **Artifact section:** 3, F1
- **Finding:** Six citations disclose their synthetic scope, but the central
  conflicting memorial assertion cannot be tied to a particular represented
  memorial and observation.
- **Required correction:** Identify the fictional website or publisher, memorial
  title and stable locator, representation, capture and observation dates, scope,
  and absence of a live memorial or underlying source.

### S1-03 — “Original representation” is terminologically misleading

- **Severity:** Important
- **Artifact sections:** 3–4
- **Finding:** “Original” may describe source provenance and can falsely imply that
  an underlying record or image was examined when the artifact used a synthetic
  transcription or abstract.
- **Required correction:** Use “value as represented in the examined fixture” or
  “captured text/value.” Classify source and representation separately, and state
  whether spelling, punctuation, abbreviations, line breaks, illegibility, and
  omissions were preserved.

### S1-04 — Roles are restrained, but assertion-level attribution is incomplete

- **Severity:** Important
- **Artifact sections:** 3 and 6
- **Finding:** The artifact avoids manufactured kinship but does not consistently
  attribute each material assertion to its represented supplier or explicitly mark
  that supplier unknown.
- **Required correction:** Keep creator, informant, certifier, enumerator,
  petitioner, witness, signatory, and subject roles distinct. Attribute assertions
  individually, with unknown permitted.

### S1-05 — Candidate-side provenance is missing

- **Severity:** Blocking
- **Artifact section:** 5
- **Finding:** Comparison classifications and ordering effects are readable, but
  candidate values are not tied to exact observations or reviewed conclusions.
- **Required correction:** Show the precise reference, represented value,
  transformation, and provenance on both comparison sides. Label unsupported
  working-profile values honestly.

### S1-06 — Replay is plausible but genealogical reproducibility is incomplete

- **Severity:** Important
- **Artifact sections:** 5 and 8
- **Finding:** The receipt could support computational replay. Genealogical
  reproduction also needs inspectable content, citations, scope, suppliers,
  derivation/dependence, searches, analysis, and conflict treatment.
- **Required correction:** Require exported representations or complete
  transcriptions and the full evidentiary and analytical context. A hash verifies
  sameness but does not make inaccessible content inspectable.

### S1-07 — Conflict visibility is promised but not invariant

- **Severity:** Blocking
- **Artifact sections:** 3, 5, and 8
- **Finding:** A selective export might omit unfavorable evidence because the
  contract does not require every material conflict bearing on a conclusion to
  persist through its lifecycle.
- **Required correction:** Once identified as material, a conflict cannot be
  silently removed, neutralized, or omitted. Later records must include it or
  explicitly document why it no longer bears on the question. Retraction or
  correction preserves prior treatment, author, date, and reason.

### S1-08 — Audit portability depends on implicit local links

- **Severity:** Blocking
- **Artifact section:** 8
- **Finding:** Stable identifiers and hashes may resolve only inside graver and do
  not by themselves carry readable evidence.
- **Required correction:** Every interpretive reference resolves within the packet
  or to an explicitly identified external representation. Include readable cited
  content, roles, transformations, analysis, conclusions, and history, and report
  inaccessible or omitted material and its effect.

### S1-09 — Evidence dependence and information quality need explicit treatment

- **Severity:** Blocking
- **Artifact sections:** 2–3, 6, and 8
- **Finding:** Some derivation and shared-file relationships appear in prose but are
  not portable at assertion level. Repeated occurrences could appear independent.
- **Required correction:** Represent known common source, informant, copying,
  proceeding, and unknown dependence. Preserve separately any researcher evaluation
  of informant knowledge as firsthand, secondary, or undetermined.

### S1-10 — The contract remains bounded, with limited ontology drift

- **Severity:** Follow-up
- **Artifact sections:** Purpose, 2, 6, and 8
- **Finding:** Scope restraint is currently credible, but vocabularies could expand
  into an attempted model of every historical practice.
- **Required correction:** Preserve unfamiliar roles and structures descriptively
  rather than forcing them into a closed universal taxonomy.

### S1-11 — Researcher configurability is insufficiently bounded

- **Severity:** Blocking
- **Artifact section:** 5
- **Finding:** The artifact reports that no override was used but does not define
  what an override may change.
- **Required correction:** Overrides affect review ordering only and remain visible,
  dated, attributed, reasoned, and replayable. They cannot alter observations,
  provenance, derivation, attribution, conflict permanence, missing-information
  treatment, or researcher-authored conclusion requirements.

## Review assessment

The contract remains appropriately bounded and shows strong restraint around
kinship, ordering, missing information, and synthetic citation scope. Its main
weakness is that several trustworthy behaviors exist only as nearby explanatory
prose. The portable contract must carry them as explicit, self-contained
relationships and invariants.

## S1 disposition

**BLOCKED**

No source-neutral packet implementation or source-facing public API freeze may
proceed until a focused re-review verifies the blocking corrections or an unresolved
blocker receives explicit, documented risk acceptance.

## Next review trigger

Perform a focused, context-reset re-review after the artifact provides complete
item identity and citation provenance, assertion-level supplier and dependence
metadata, fully attributable comparison inputs, conflict permanence, self-contained
portable references, genealogical-reproducibility requirements, bounded overrides,
and open descriptive vocabularies.
