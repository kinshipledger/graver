# Professional Genealogist Usability Review

**Review date:** 2026-08-22
**Review perspective:** First-time end user applying rigorous genealogical evidence standards
**Purpose:** Preserve a baseline usability assessment for repetition after the project completes milestones addressing FamilySearch correlation, evidence assessment, citation clarity, and professional onboarding.

## Scope and review boundary

This review deliberately treated graver as a product encountered for the first time by a professional genealogical researcher. It evaluated only the visible command-line interface, command help, README, researcher tutorial, and access-policy documentation.

The review did not rely on knowledge of implementation details, database schemas, internal architecture, or development plans. It did not assess whether an unexposed backend capability might exist. Its conclusions describe what a researcher can discover, understand, and accomplish through the current user-facing product.

The intended research scenario was:

1. Acquire a batch of Find a Grave memorials.
2. Correlate those memorials with potential FamilySearch matches.
3. Evaluate the evidence for or against each proposed identity.
4. Preserve source information, reasoning, confidence, and conclusions in a form consistent with rigorous genealogical research.

The four review dimensions were:

1. Evidence corroboration flow
2. Confidence and proof standards
3. Data persistence clarity
4. Professional onboarding

## Executive assessment

In its reviewed user-facing form, graver is a careful Find a Grave acquisition and work-queue utility, not yet a Find a Grave–FamilySearch corroboration system.

It appears useful as a controlled way to collect memorial evidence while preserving acquisition history. It is not yet an environment in which a rigorous researcher could make, document, revisit, and defend identity conclusions according to professional genealogical evidence standards.

The most encouraging characteristic is restraint: the product does not visibly convert an unexplained algorithmic score into an asserted identity. Its staged acquisition workflow also distinguishes a search-result summary from a fully retrieved memorial. Those are sound foundations.

The principal gap is that the visible workflow stops at evidence acquisition. It does not yet provide the correlation, conflict analysis, source evaluation, confidence explanation, or reasoned-conclusion experience required for professional identity research.

## 1. Evidence corroboration flow

### Observed workflow

The visible workflow was:

```text
Find a Grave search
→ save summaries
→ queue memorials
→ inspect one memorial
→ approve it
→ retrieve its full page
→ review acquisition history
```

This flow is admirably deliberate. Requiring explicit approval before enriching one memorial reduces accidental acquisition and helps the researcher remain focused on a known record.

### Findings

No visible FamilySearch comparison workflow was available. In particular, the reviewed interface did not expose:

- FamilySearch candidate discovery
- A candidate list associated with the current research subject
- Side-by-side comparison of Find a Grave and FamilySearch facts
- Preservation of candidate identity while navigating between views
- Comparison of names, dates, places, relatives, and relationships
- Highlighting of agreements, discrepancies, or unresolved facts
- Source-to-assertion comparison
- Candidate rejection, deferral, or later reconsideration
- A research log for searches that returned no acceptable candidate

The practical result is that a researcher must leave graver, conduct FamilySearch research manually, and record the analysis elsewhere. This creates risks that a professional workflow should reduce: losing context, confusing similarly named people, overlooking contradictory relationships, or forgetting why a candidate was accepted or rejected.

The memorial-number-oriented interface helps anchor activity to a particular Find a Grave record. It does not provide household, family, locality, or relationship context, which is often essential when distinguishing people with similar names and dates.

### Baseline assessment

**0/5 for Find a Grave–FamilySearch corroboration.** The evaluated capability was not exposed in the product.

## 2. Confidence and proof standards

### Findings

No confidence-rated match was visible, so there was no confidence calculation to inspect. This is safer than presenting an opaque automatic score as a genealogical conclusion, but it leaves the professional assessment workflow unsupported.

The visible task controls consisted principally of:

- Status
- Priority
- Owner
- A free-text note

The command help did not communicate the evidentiary meaning of task statuses or state what level of research justified moving between them. A free-text note can preserve some reasoning, but it is not a structured proof assessment.

A professionally useful candidate assessment should eventually distinguish:

- Evidence items from conclusions
- Supporting, conflicting, and neutral evidence
- Exact, partial, inferred, and incompatible agreement
- Source quality and information quality
- Independent sources from sources that repeat the same underlying claim
- Negative searches and unresolved questions
- Machine-generated suggestions from researcher conclusions
- Researcher-entered reasoning
- Conclusion or confidence status and its defined meaning
- Reviewer identity and decision date
- Revision of a conclusion without erasing its earlier history

A numeric score could be useful for ranking candidates, but it should not masquerade as proof. The researcher should be able to see why each component affected the ranking, inspect the underlying evidence, override the suggestion, and remain responsible for the conclusion.

### Baseline assessment

**1/5 for proof support.** The product is appropriately cautious about making an identity claim, but it offers essentially no visible assistance for constructing a defensible one.

## 3. Data persistence clarity and citations

### Strengths

This was the strongest reviewed area. The tutorial clearly communicated that:

- Cemetery-search summaries differ from full memorial acquisitions.
- A summary does not prove that the full memorial page was observed.
- Enrichment retains both the summary and full observations.
- Acquisition history includes a source URL and timestamp.
- Full retrieval is limited to an explicitly approved memorial.
- “Fully enriched” means that the full page was processed successfully, not that every possible field necessarily contains a value.

That last qualification is especially important. It prevents an operational state from being mistaken for evidentiary completeness.

### Weaknesses

The visible product did not present a clearly defined genealogical citation containing elements such as:

- Memorial creator or contributor, when available
- Memorial title or decedent name
- Website and memorial number
- Stable URL
- Access date and time
- Nature of the captured page
- Whether the value is a transcription, derivative summary, or direct observation
- Field-level provenance when displayed values derive from different observations

SQLite storage and machine-readable JSON can support auditability, but neither is itself a professional source citation or readable evidence report.

The search workflow also saved results without showing a result table. A researcher should receive an immediate, understandable receipt stating:

- How many records were found
- How many were newly saved or updated
- Which database received them
- What kind of observation was recorded
- How to inspect the resulting records

Without that confirmation, persistence feels less transparent even if the stored data is internally sound.

The product should also make clear whether a newly acquired observation changes a displayed current value, how conflicts between observations are represented, and how the researcher can trace any displayed value back to the observation from which it came.

### Baseline assessment

**3/5 for persistence clarity.** Acquisition provenance is promising, but professional citation presentation and field-level traceability are not yet visible.

## 4. Onboarding for professional researchers

### Strengths

The researcher tutorial was the best entry point. It provided a staged workflow and useful symptom-oriented troubleshooting for a genealogist already comfortable entering terminal commands.

The responsible-access guidance was also clear and appropriately cautious about external services.

### Weaknesses

The main README presented a developer-oriented front door. A professional researcher encountered concepts such as:

- Build and status badges
- Git cloning
- `uv`
- Virtual environments
- Lockfiles
- Test and coverage commands
- SQL, schema, and JSON terminology
- Database migration language
- Architecture and developer documentation

These topics are legitimate project materials, but they dominate the initial experience. An archivist or genealogist should be able to understand the product’s purpose, limitations, and research workflow before learning about Python packaging or contribution tooling.

The README should lead with:

1. What graver does today
2. What graver does not yet do
3. A researcher-oriented quick start
4. A small professional research example
5. What information will be saved
6. How to inspect, cite, export, back up, and recover it
7. Privacy and responsible-access considerations

Until FamilySearch comparison exists, its absence should be stated plainly near the beginning rather than left for the researcher to discover.

The search help also exposed a large collection of provider-shaped filters and technical identifiers. Practical examples organized around common research intentions would be more approachable than requiring a new user to infer the correct combination of low-level options.

### Baseline assessment

**2/5 for professional onboarding.** It is usable by a technically confident genealogist, but it is not yet an accessible professional-researcher introduction.

## Overall suitability at the review baseline

### Suitable uses

At this baseline, a rigorous researcher could reasonably use graver for:

- Controlled Find a Grave acquisition
- Maintaining a local memorial collection
- Distinguishing summary retrieval from full-page retrieval
- Preserving acquisition observations
- Working through memorials one at a time

### Uses not yet adequately supported

The reviewed product should not yet be treated as the authoritative environment for:

- FamilySearch candidate comparison
- Identity resolution
- Confidence assessment
- Genealogical proof arguments
- Conflict analysis
- Negative-search logging
- Formal source citations
- Relationship-based correlation

The foundation appears conscientious about provenance and avoiding overstatement. The visible product nevertheless stops at evidence acquisition rather than supporting the complete research cycle of collection, correlation, analysis, conflict resolution, and reasoned conclusion.

## Requirements for a meaningful future re-review

Repeat this review only after the relevant capabilities are visible to an ordinary user. Do not award credit merely because internal models, database structures, or plans exist.

The re-review should exercise a realistic case containing at least:

- One Find a Grave memorial with a plausible FamilySearch candidate
- At least one meaningful discrepancy in a name, date, place, or relationship
- More than one plausible candidate, if practical
- A supporting relationship or family connection
- A source that repeats another source rather than independently corroborating it
- An unresolved fact or negative search
- A researcher decision that is later reconsidered

### Re-review checklist: corroboration

- Can the researcher discover or enter FamilySearch candidates without losing the Find a Grave context?
- Are candidates unmistakably separated from accepted identity conclusions?
- Can facts and relationships be compared side by side?
- Are agreements, discrepancies, missing values, and contradictions visible?
- Can a candidate be rejected, deferred, or reopened with its history intact?
- Can the researcher record negative searches and unresolved questions?
- Does navigation minimize the risk of acting on the wrong person or profile?

### Re-review checklist: confidence and proof

- Is every confidence or ranking value explained?
- Can the researcher inspect the evidence contributing to it?
- Is an algorithmic ranking clearly separated from a human conclusion?
- Can the researcher disagree with or override the ranking?
- Are source quality, information quality, and evidence character represented meaningfully?
- Can conflicting evidence be recorded without forcing premature resolution?
- Are reasoning, reviewer, date, and conclusion history preserved?
- Does the language avoid implying that a score constitutes genealogical proof?

### Re-review checklist: persistence and citations

- Does every acquisition show an immediate save receipt?
- Can the researcher tell precisely what was saved and where?
- Can every displayed assertion be traced to one or more observations?
- Are prior observations preserved when displayed values change?
- Is a readable source citation available?
- Does the citation distinguish summaries, full pages, transcriptions, and derivative information?
- Are access dates, URLs, record identifiers, contributors, and other available citation elements retained?
- Can evidence and citations be exported without requiring direct database inspection?

### Re-review checklist: onboarding

- Can a professional genealogist understand the product before encountering developer setup?
- Is there an explicit statement of current capabilities and limitations?
- Is there a researcher-first quick start with realistic output examples?
- Are installation, database selection, backup, export, and recovery explained in plain language?
- Are common research tasks expressed as workflows rather than collections of technical options?
- Are developer and contributor instructions clearly separated from researcher onboarding?

## Suggested future evaluation method

For comparability, the future reviewer should again avoid source-code and schema inspection. The evaluation should use only:

- The normal installation path offered to users
- The main README and researcher documentation
- Visible CLI or GUI help
- A new, isolated research database
- The ordinary Find a Grave acquisition workflow
- The ordinary FamilySearch candidate workflow, once available
- User-visible history, citations, exports, and troubleshooting

Record screenshots or terminal transcripts for each major decision point. Note where the researcher must consult external notes, manually copy identifiers, infer undocumented meanings, or leave the application. These points indicate workflow friction or threats to evidentiary continuity.

## Context hand-off for resumption

When this review is resumed, begin from the following question:

> Has graver progressed from a careful evidence-acquisition utility into a researcher-controlled environment for correlating evidence and documenting defensible identity conclusions?

Reassess the product from scratch rather than comparing implementation claims. Use the baseline scores only as reference points:

| Dimension | Baseline |
|---|---:|
| Find a Grave–FamilySearch corroboration | 0/5 |
| Confidence and proof support | 1/5 |
| Persistence and citation clarity | 3/5 |
| Professional onboarding | 2/5 |

The future review should identify both improvement and regression. In particular, scrutinize whether new automation introduces opaque assumptions, whether additional features obscure provenance, and whether a GUI merely makes an unsafe conclusion easier to accept. Ease of use should increase researcher velocity without weakening evidentiary control.
