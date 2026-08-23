# Principal architecture analysis of the professional usability review

**Analysis date:** 2026-08-22
**Source review:** [Professional Genealogist Usability Review](professional-genealogist-usability-review-2026-08-22.md)
**Purpose:** Translate the professional-researcher review into product, domain,
application-service, interface, and roadmap consequences.

## Executive conclusion

The review identifies a boundary in the current product, not a failure of its
existing acquisition safeguards. graver preserves acquired Find a Grave records
carefully, but the visible workflow ends before correlation, conflict analysis, and
reasoned identity conclusions begin.

The architectural response must not be a single confidence percentage or a larger
collection of CLI switches. graver needs a researcher-controlled evidence model in
which these concepts remain separate and auditable:

```text
source observation
  → candidate discovery
  → machine-generated comparison signals and ranking
  → researcher assessment
  → reviewed identity conclusion
```

Machine assistance may prioritize research. It must never silently convert
similarity into genealogical identity.

## 1. Core friction points

### 1.1 The workflow ends before corroboration begins

The current visible journey supports Find a Grave search, summary persistence,
queueing, inspection, explicit approval, full acquisition, and acquisition-history
review. It exposes no FamilySearch candidate discovery or comparison workflow.

The researcher must leave graver to compare profiles and maintain reasoning in an
external system. That discontinuity creates avoidable risks:

- confusing similarly named people;
- losing the identifier or state of the candidate under review;
- overlooking contradictory relationships or localities;
- rediscovering a previously rejected candidate without its rejection rationale;
- failing to record a negative search; and
- separating the final conclusion from the evidence that supported it.

The implemented research subject is the correct neutral owner for future candidate
research. The missing layer is an explicit subject-linked candidate and evidence
workflow.

### 1.2 Workflow state cannot carry evidentiary meaning

Task status, priority, owner, and a free-text review note organize work. They cannot
reliably represent an evidence assessment or proof argument.

The product must distinguish all of the following:

- a candidate returned by a provider search;
- a machine-generated ordering of candidates;
- observed agreements, conflicts, missing values, and relationships;
- a researcher's evolving assessment;
- a reviewed identity conclusion; and
- a later conclusion that supersedes an earlier one.

Collapsing any of these into a generic status or confidence field would create an
opaque and professionally unsafe model.

### 1.3 Provenance is preserved but not sufficiently presented

The existing summary/full distinction, immutable observations, source URL, and
acquisition timestamp are strong foundations. The researcher nevertheless has to
inspect JSON or database-oriented output to understand what was saved.

Each state-changing operation should provide a human-readable receipt, and each
displayed assertion should support provenance inspection. A readable source
citation must be a projection of preserved provenance, not a substitute for that
provenance.

The README also presents a developer-oriented front door. Researcher capabilities,
limitations, first workflow, citations, backups, privacy, and recovery should
precede contributor tooling.

## 2. Architectural and logic gaps

### 2.1 Ranking is not a conclusion

A ranking answers which candidate merits attention first. An identity conclusion
answers whether the researcher believes two records represent the same person after
appropriate research and conflict resolution.

The machine layer may emit versioned comparison signals and a reproducible ranking.
It must not create an accepted external identity association or advance a task to an
identity-resolved state automatically.

The public vocabulary should prefer **candidate ranking** and **match signals** over
an unexplained **confidence score**. If a numeric value is retained for ordering, it
must state its limited purpose and expose every contributing signal.

### 2.2 Discovery must be repeatable and historically honest

FamilySearch changes over time. Each discovery execution therefore needs an
immutable run recording its criteria, time, outcome, and returned candidates. Each
observed candidate state needs a timestamped snapshot.

A later run must not:

- overwrite a prior snapshot;
- delete a candidate that is no longer returned;
- reset a rejection or unresolved assessment;
- treat absence from one result set as disproof; or
- accept a candidate because it ranks first.

### 2.3 Comparison must occur at the assertion level

Whole-profile similarity is insufficient. The comparison model must retain each
original observed value and separately record any normalized value used for
matching. Each signal needs:

- fact or relationship type;
- source-side assertion references;
- original and normalized values;
- agreement classification;
- contribution to candidate ordering, if any;
- a plain-language explanation;
- applicable source references; and
- researcher disposition.

Initial agreement classifications should include exact, compatible, inferred,
missing, material conflict, not comparable, and researcher review required.

Missing information must not count as agreement. Normalization must never overwrite
an observed value.

### 2.4 Conclusions require immutable human decisions

A reviewed conclusion needs an explicit disposition, researcher or reviewer,
decision time, reasoned analysis, evidence references, and treatment of material
conflicts. A later decision supersedes rather than edits or deletes the earlier
decision.

Accepted, rejected, unresolved, and withdrawn are conclusion dispositions. Candidate
workflow states such as new, reviewing, deferred, and reopened belong to the
assessment workflow and must not be conflated with conclusions.

### 2.5 Citations and persistence receipts are application results

The application layer should return typed acquisition receipts containing the
target database, provider, requested scope, record and observation counts, failures,
time range, and next action. CLI and GUI adapters should project the same result.

A citation service should derive readable citations from immutable observations and
the source metadata actually captured. It must clearly distinguish provider values,
normalized comparison values, researcher assertions, machine inferences, and
reviewed conclusions.

## 3. Interface and workflow adjustments

### 3.1 Stable comparison workspace

The future desktop experience should keep three contexts visible together:

```text
research subject and candidates
  | evidence comparison
  | assessment and conclusion
```

The active subject must remain persistently visible. Provider identity must be
unambiguous. Candidate facts must never appear as accepted subject facts merely
because the candidate is selected.

### 3.2 Evidence matrix and detail drawer

The principal comparison should be a fact-and-relationship matrix showing Find a
Grave values, FamilySearch values, assessment labels, and source counts. Color may
reinforce exact, compatible, incomplete, conflicting, and missing states but must
never be the only indicator.

Selecting a comparison opens a detail view containing original values, normalized
values, citations, observation dates, related assertions, comparison explanation,
researcher comments, and prior assessments.

### 3.3 Explainable candidate ordering

Do not lead with a percentage. Prefer a summary such as:

> Ranked first of four candidates — five supporting signals, one material conflict,
> and three unknowns.

An expandable explanation must show every signal and its effect. Conclusion controls
remain visually and logically separate from ranking.

### 3.4 Deliberate decision workflow

Candidate actions should include continue researching, defer, reject, accept as the
same person, and withdraw or supersede a prior conclusion. Acceptance requires
reasoning and explicit handling of material conflicts; it must not be a one-click
action from a candidate list.

### 3.5 Visible persistence feedback and researcher-first onboarding

Search and enrichment should immediately report what was created, changed,
unchanged, observed, and unsuccessful, along with the selected database and next
action.

Documentation should provide separate researcher and contributor entrances. The
researcher path leads with current capabilities and limitations, a short workflow,
annotated output, citation examples, backup and recovery, privacy, and a glossary of
research terms.

## 4. Actionable roadmap issues

### Issue 1 — Model repeatable candidate discovery and immutable snapshots

**User story:** As a genealogical researcher, I want discovery runs and candidate
snapshots preserved for each research subject so that I can rerun searches, detect
changes, and revisit candidates without losing history.

**Acceptance criteria:**

- Re-running discovery never overwrites a run or snapshot.
- Changed provider data produces a new snapshot.
- Candidates absent from a later run remain historically visible.
- No candidate is accepted automatically.
- Candidate data belongs to a research subject rather than directly to a memorial.
- Offline fixtures cover multiple candidates, changed relationships, no results,
  and repeated discovery.

### Issue 2 — Implement explainable evidence assessment and reviewed conclusions

**User story:** As a professional researcher, I want to inspect supporting,
conflicting, missing, and derivative evidence before recording an identity
conclusion so that candidate ranking cannot be mistaken for genealogical proof.

**Acceptance criteria:**

- Every ranking explains its positive, negative, and neutral signals.
- Original and normalized values remain separately available.
- Missing facts do not count as agreement.
- Rankings never create conclusions.
- Accepted, rejected, unresolved, and withdrawn conclusions require human action.
- Later decisions supersede rather than erase earlier decisions.
- A highly ranked candidate with a material conflict remains unaccepted.

### Issue 3 — Deliver a shared comparison workflow for future clients

**User story:** As a researcher, I want a stable view of the subject, candidates,
relationships, conflicts, and my assessment so that I do not confuse profiles or
lose context.

**Acceptance criteria:**

- Typed application results support both CLI and future GUI adapters.
- The active subject cannot change implicitly when a candidate is selected.
- Candidate data is visibly distinct from accepted subject conclusions.
- Agreement states have text labels and accessible presentation.
- Unsaved reasoning is protected by the client.
- A workflow test covers multiple candidates, a material conflict, deferral, and
  later resumption without external notes.

### Issue 4 — Make persistence, citations, and onboarding researcher-readable

**User story:** As a genealogist, I want every acquisition to explain what was saved
and provide readable provenance so that I can trust and cite evidence without
opening SQLite.

**Acceptance criteria:**

- Search and enrichment return typed created, changed, unchanged, observed, and
  failed counts.
- Receipts identify the database, source type, and next action.
- Every displayed acquired fact can expose its originating observation.
- A readable citation can be generated without direct database access.
- The README leads with researcher value and current limitations.
- Developer setup is clearly separated from researcher onboarding.

## Recommended delivery order

```text
evidence contract
  → offline candidate and snapshot model
  → explainable comparison services
  → reviewed conclusion service
  → typed client projections
  → comparison interface
```

Acquisition receipts and researcher-first documentation can proceed independently
because they improve the current product and exercise the same typed application
boundary.

The governing product rule is:

> Automation may prioritize evidence for review; only the researcher may make the
> genealogical conclusion.
