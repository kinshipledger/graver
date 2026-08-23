# Source-neutral adapter strategy

Status: architectural guardrail and selection process. This document does not
commit graver to a particular provider, record class, import format, or new
pre-1.0 feature.

## Product boundary

graver remains a focused, evidence-aware research workflow—not a general-purpose
genealogy suite, universal record harvester, tree editor, document-management
system, or replacement for specialist research tools. Its core value is preserving
observations, comparing attributed assertions, managing reviewable research work,
and recording conclusions without confusing discovery order with proof.

Find a Grave is the implemented acquisition surface and cemetery-led research is
the first proven workflow. The core application model should nevertheless avoid
assuming that every subject originates in a cemetery or that every useful source
arrives through a live provider. Source neutrality is an incremental design
constraint, not a promise to support every conceivable genealogical source.

New integration work must begin with a demonstrated researcher problem. Popularity
of a platform, format, or record class is not by itself sufficient justification.

## Keep four dimensions separate

Requirements and APIs must distinguish:

- **source class:** memorial, marriage record, death certificate, census schedule,
  probate file, newspaper, research log, and similar evidence-bearing material;
- **carrier format:** HTML, API response, GEDCOM, CSV, JSON, PDF, image, OCR, or a
  structured offline package;
- **access surface:** local file, manual capture, archive, provider website, or an
  authorized API; and
- **workflow role:** discovery, observation capture, import, comparison, assessment,
  conclusion, or export.

A platform is where a representation was encountered; it is not necessarily the
record creator, repository, original source, or authority for every displayed
assertion. A file format transports assertions; it does not establish their truth.

## Adapter roles

Adapters may implement more than one role, but the operations and results remain
separate:

1. **Discovery adapters** return leads or candidate records for review. Ordering is
   not proof or confidence.
2. **Observation adapters** capture an attributable source representation as an
   immutable snapshot.
3. **Import adapters** inspect researcher-controlled data and create external
   snapshots and candidate assertions—not accepted facts, relationships, or
   identities.
4. **Export adapters** project deliberately selected research for another consumer
   and disclose omissions, transformations, privacy filtering, and representational
   loss.

Provider, parser, OCR, SQLite, terminal, and GUI types do not cross the public
application boundary. Adapters return graver-owned typed results and errors. The
core must preserve the observed representation, provenance, individual assertions,
known roles and informants, explicit versus inferred relationships, missing or
uncaptured information, search scope, snapshot changes, warnings, and inspectable
evidence references. An adapter never creates a reviewed conclusion automatically.
The [trust, transparency, and openness architecture](trust-transparency-architecture.md)
also requires candidate-specific comparison traces and an independently
interpretable audit projection; a technically open adapter is not sufficient when
its researcher-facing outcome remains opaque.

These are compatibility pressures on the public API, not permission to invent a
comprehensive genealogical ontology before real workflows require one. Standardize
only distinctions demonstrated by reviewed examples.

## Admission gates and scoring

An adapter candidate is ineligible until all of these gates pass:

1. Access and use are authorized and consistent with the access policy.
2. Provenance can be retained faithfully without converting unknown information
   into evidence of absence.
3. Privacy and sensitive-data risks have a workable control model.
4. Representative, privacy-safe offline fixtures can exercise the contract.
5. Imported or discovered assertions remain separate from reviewed conclusions.

Eligible candidates receive a recorded score:

| Criterion | Weight |
| --- | ---: |
| Demonstrated researcher value | 25% |
| Architectural learning and reuse | 20% |
| Provenance and citation fidelity | 20% |
| Access stability and authorization | 15% |
| Representative fixture availability | 10% |
| Implementation and maintenance cost | 10% |

Scores support comparison; they do not replace judgment. Each proposal must name
the user problem, intended adapter role, smallest useful vertical slice, explicit
non-goals, review evidence, maintenance owner, and exit criteria. Re-score the
remaining candidates after each completed adapter because implementation experience
may change their value or cost.

## Current candidate order

This is a hypothesis to test, not a delivery commitment:

1. A small, internal source-neutral evidence packet exercised with synthetic civil,
   census, and probate examples. It validates the contract without choosing a live
   provider or public interchange format.
2. A template-driven research-log CSV/TSV import, if professional users demonstrate
   demand. It requires an explicit preview and column-mapping step rather than
   guessing arbitrary schemas.
3. An offline marriage-record vertical slice, because it exercises identity,
   events, relationships, informants, witnesses, original and derivative
   representations, and citations.
4. Census household observations, preserving co-residence and reported roles
   without manufacturing kinship.
5. Multi-document probate packets, after the simpler source contract is proven.

FamilySearch remains strategically important as a candidate-discovery and evidence
surface, subject to its authorization gate. GEDCOM remains a conditional assertion-
exchange adapter whose first plausible value is immutable inspection and repeatable
comparison. Newspapers/OCR, land and directory timelines, and DNA require distinct
provenance, privacy, or interpretation work and are not near-term commitments.

## Review and documentation cadence

The project closes the loop with a Professional Genealogist at these points:

- before freezing source-neutral public types;
- before implementing a materially new evidence family whose semantics have not
  already been reviewed;
- after the first usable vertical slice for that family;
- after every two completed adapters or six months, whichever comes first;
- before releasing changes to conclusion, citation, relationship, privacy, or
  research-export behavior; and
- whenever implementation would require developers to invent unsupported
  genealogical meaning.

Each engagement uses a specific research scenario, privacy-safe artifacts, explicit
questions, pass/block criteria, a dated report, and roadmap issues for findings.
Blocking evidentiary findings prevent the affected contract from being frozen or
presented as production-ready.

At each release-candidate review and source-portfolio review, reconcile this
strategy, the project context, existing-system inventory, API guide, access policy,
GEDCOM direction, professional-review gates, tutorial, and README. Remove stale
claims, confirm current non-goals, and defer or delete speculative work that no
longer justifies its cost.

The traceability rule is:

```text
researcher problem
  -> reviewed scenario
  -> bounded capability requirement
  -> gated and scored adapter proposal
  -> smallest vertical slice
  -> experiential review
  -> continue, revise, defer, or stop
```
