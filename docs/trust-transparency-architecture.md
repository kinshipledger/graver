# Trust, transparency, and openness architecture

Status: governing trust contract and pre-1.0 design input.

## Trust proposition

Professional trust does not follow merely from open source, deterministic output,
configurable rules, or a polished explanation. It requires a researcher to inspect
what was observed, understand every transformation and comparison that affected the
workflow, retain conflicts and limitations, control the conclusion, and reconstruct
the evidence and reasoning later.

graver therefore distinguishes:

- **computational reproducibility:** identical inputs, software, rules, and
  configuration produce the same comparison and review order; and
- **genealogical reproducibility:** another qualified researcher can locate or
  inspect the cited representations, evaluate their provenance and informants,
  reconstruct the correlation and conflicts, and assess the written conclusion.

Both matter. Computational replay is not genealogical proof.

## Four visible trust layers

1. **Source layer:** exact retained observations, provenance, citations, capture
   scope, limitations, and earlier/later snapshots.
2. **Comparison layer:** original and normalized values, classifications, missing
   and conflicting data, applied rule and version, ordering effect, overrides, and a
   researcher-readable explanation for this candidate.
3. **Workflow layer:** researcher-authored questions, searches, notes, deferrals,
   reopening reasons, selected evidence, conflict treatment, overrides, and history.
4. **Conclusion layer:** explicit disposition, analysis, inspectable evidence
   references, source and informant limitations, authorship, date, and immutable
   withdrawal or supersession.

The interface and exports must make these layers understandable without requiring a
genealogist to read Python, SQL, regular expressions, or configuration syntax.

Candidate ordering is a discovery decision, not a genealogical conclusion. It may
be implemented with rules, statistics, machine learning, or a combination, provided
its relevant inputs and effects are inspectable and it cannot change assessment or
conclusion state. A numeric contribution must not be presented as a probability or
confidence unless it is genuinely calibrated and validated for a stated population
and purpose. Ordinary presentation should prefer plain-language comparison reasons,
material conflicts, and unknowns.

## Rule transparency

Default comparison and ordering rules should eventually have:

- a stable rule identifier and semantic version;
- plain-language purpose and behavior;
- author or maintainer and change history;
- intended record classes, places, periods, languages, and other scope limits;
- cited methodological or historical basis where applicable;
- required inputs, transformations, and possible classifications;
- synthetic positive, negative, conflict, and boundary examples;
- known limitations and observed false-positive or false-negative cases; and
- a deterministic manifest or hash sufficient to identify the exact rules used.

Every comparison trace must identify the input snapshots and assertions, original
and normalized representations, applied rules and versions, researcher overrides,
ordering effects, and explanations. Changing a rule or override creates a new
comparison context; it never rewrites earlier observations, assessments, or
conclusions.

Open and configurable rules strengthen auditability but do not establish validity.
The project must not initially create a general plugin ecosystem or invite arbitrary
rule packs. Regional or period-specific rules require provenance, scope,
limitations, validation examples, review, and explicit activation. Community rules
never silently become universal defaults.

Some safeguards are invariants rather than preferences and cannot be configured
away:

- missing information does not automatically become contrary evidence;
- candidate order cannot create or alter a conclusion;
- source-displayed relationships do not automatically become proved kinship;
- original observations and contrary assertions are never silently rewritten;
- conclusions retain their exact evidence references and conflict treatment; and
- withdrawal or supersession never erases decision history.

## Researcher control and AI provenance

The researcher deliberately authors or approves research questions, negative
searches, deferral and reopening reasons, selected evidence, analysis, treatment of
material conflicts, and conclusions. Software may organize or draft material but
cannot attribute an unreviewed conclusion to the researcher.

Any future AI-generated or AI-assisted transcription, extraction, normalization,
candidate explanation, citation, summary, or analysis must retain the tool/model or
service identity, version where available, generation time, source inputs, relevant
configuration, and human review state. AI provenance is not a disclaimer that
excuses unreliable output; it enables verification and correction. Sensitive data
and provider terms remain governed by the access and privacy policies.

## Portability and independent verification

Researchers must not depend on hidden database knowledge to recover the meaning of
their work. Before a production evidence workflow claims professional readiness,
graver should define a versioned, privacy-conscious audit bundle capable of carrying
the observations, citations, comparison context, assessments, conclusions, selected
evidence, conflicts, and history required to interpret that work. It is an
audit/export projection, not graver's internal database schema or a new universal
genealogy format.

The source-neutral evidence-packet prototype should test this minimum bundle before
the public evidence API is frozen. A later public format requires explicit version,
compatibility, validation, redaction, and migration rules. Synthetic fixtures and a
small validator/replay example should demonstrate independent interpretation. Do
not build a second production engine merely to call it a reference implementation;
the smallest independently useful verifier is preferred.

## Independent verification materials

Keep available and versioned:

- evidence terminology and integrity invariants;
- default comparison and candidate-ordering definitions;
- citation and provenance projections;
- portable audit-bundle specification and validation rules, once approved;
- synthetic fixtures, validation methodology, known limitations, and change
  histories; and
- documentation sufficient to understand each researcher-facing outcome.

These materials ensure that the researcher can understand and recover the research
without trusting an opaque conclusion.

## Acceptance gates

Before source-facing public API freeze:

1. A professional reviewer can explain why each candidate was ordered as shown.
2. Every comparison exposes exact inputs, transformations, rule context, conflicts,
   unknowns, and overrides in researcher-readable form.
3. Replaying the same recorded context produces the same ordering.
4. No rule or score can mutate assessment or conclusion state.
5. The source-neutral evidence packet demonstrates an audit-bundle projection with
   no direct database access.
6. A focused Professional Genealogist review has no unresolved blocking trust
   finding.

Before a production evidence-workflow claim:

1. A privacy-safe export retains the visible trust layers and can be validated
   independently.
2. Known limitations and validation cases are published.
3. AI-assisted content, if any, is attributable and visibly reviewed or unreviewed.
4. The production workflow passes the established professional and UX review gates.

The same trust and audit contract applies to every supported client. A future GUI,
CLI, or other adapter may improve workflow and presentation but cannot become the
only means of interpreting comparison logic, citations, evidence selection,
conflicts, or conclusion history.
