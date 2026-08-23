# Source-neutral evidence packet review prototype

**Status:** Fictional contract artifact; not implemented product behavior<br>
**Review:** S1 — focused source-contract review<br>
**Scenario:** Offline and synthetic; no live provider or real-person data

## Purpose and review boundary

This artifact asks whether one small evidence packet preserves distinctions shared
by several genealogical source classes without turning graver into a universal tree
editor, record ontology, or document repository. It tests researcher understanding,
not a database schema, public file format, scoring formula, or screen layout.

The examples are intentionally fictional. No real certificate, census image,
probate file, repository request, or provider page was examined. The synthetic
citations and representations exist only to test the proposed contract.

The packet must not:

- establish identity or kinship automatically;
- treat a platform, index, transcription, or OCR output as the underlying record;
- treat missing information as negative evidence;
- imply that repeated assertions are independent;
- flatten conflicting assertions into one preferred fact;
- infer relationships merely from a household, surname, or estate appearance;
- expose a numeric probability or proof-confidence score; or
- commit graver to supporting these source classes or this packet structure.

## 1. Keep the research question and subject distinct from sources

### Working research subject

**Eleanor May Carter Reed**<br>
Born about **1892**, reportedly in Missouri<br>
Died reportedly **8 November 1967**, Boise, Idaho

**Research question:** Do the observed records support that Eleanor May Carter, who
married William Reed in Ada County in 1912, was a daughter of Henry Carter—and how
should the conflicting Find a Grave statement naming Thomas Carter be treated?

This working summary organizes research. Its displayed values are not automatically
accepted facts. Every material value must remain traceable to an observation or a
reviewed conclusion.

## 2. Identify source class, carrier, access surface, and workflow role

| Packet item | Source class | Representation actually used | Access surface | Workflow role |
| --- | --- | --- | --- | --- |
| M1 | Civil marriage register | Synthetic human transcription representing a register entry; no real image exists | Offline review fixture | Observation |
| M2 | Marriage index | Synthetic derivative index entry | Offline review fixture | Discovery lead and derivative observation |
| D1 | Civil death certificate | Synthetic structured abstract representing selected certificate fields; no real image exists | Offline review fixture | Observation |
| C1 | 1910 census schedule | Synthetic line-by-line transcription representing one household; no real image exists | Offline review fixture | Observation and context |
| P1 | Probate petition | Synthetic document transcription from a fictional estate packet | Offline review fixture | Observation |
| P2 | Probate distribution receipt | Synthetic document transcription from the same fictional estate packet | Offline review fixture | Observation |
| F1 | Find a Grave memorial | Previously retained fictional full-page snapshot | Offline review fixture | Observation and candidate lead |

The repository, record creator, access platform, carrier, and source class are
separate metadata. A later live adapter could encounter the same record through a
provider, archive, local image, or researcher transcription without changing the
meaning of those distinctions.

## 3. Inspect source representations without flattening assertions

### M1 — marriage register representation

**Citation draft:** Ada County, Idaho, marriage register 7, p. 142, entry for
William Reed and Eleanor May Carter, 18 June 1912; synthetic offline review fixture,
created 23 August 2026; no real register or image examined.

- Record creator represented: Ada County clerk
- Representation used: synthetic human transcription
- Recorded date: 18 June 1912
- Bride as written: `Eleanor May Carter`
- Groom as written: `William Reed`
- Bride's father as written: `Henry Carter`
- Witness as written: `Alice B. Carter`
- Informant or supplier of each item: not stated in the represented entry
- Capture limitation: surrounding entries, signatures, corrections, and an original
  image were outside this fictional fixture

**Derived assertions:** a marriage event was recorded for the named parties; the
entry displayed Henry Carter as the bride's father; Alice B. Carter appeared in the
role of witness. The witness role is preserved and is not converted into kinship.

### M2 — derivative marriage index

**Citation draft:** “Idaho Marriages, 1910–1920,” synthetic index entry for Eleanor
M. Carter and Wm. Reed, 18 June 1912, index locator `IDX-1912-8841`; offline review
fixture observed 23 August 2026; underlying register cited as book 7, page 142 but
not examined through this representation.

- Bride as indexed: `Eleanor M. Carter`
- Groom as indexed: `Wm. Reed`
- Father: not indexed
- Derivation statement: the fixture says it was indexed from M1
- Capture limitation: no index image, indexer identity, or correction history exists

M2 is separately observable but not independent corroboration of the values it
derives from M1.

### D1 — death certificate representation

**Citation draft:** Idaho Bureau of Vital Statistics, death certificate abstract,
Eleanor May Reed, certificate `1967-ADA-004218`, 8 November 1967; synthetic offline
review fixture created 23 August 2026; no real certificate image examined.

| Item represented | Original representation | Reported source or role |
| --- | --- | --- |
| Name | `Eleanor May Reed` | certificate heading |
| Death | `8 Nov. 1967, Boise` | medical/certificate section; certifier not represented in fixture |
| Birth | `14 Mar. 1892, Missouri` | personal-information section |
| Father | `Henry Carter` | personal-information section |
| Informant | `William Reed, husband` | informant field |

The certificate contains information supplied through different roles. This packet
does not assume the informant supplied the medical information, or that a husband's
knowledge of parentage was direct or contemporary.

### C1 — census household representation

**Citation draft:** 1910 United States census, Ada County, Idaho, population
schedule, fictional enumeration district 44, sheet 8A, dwelling 126, Henry Carter
household; synthetic line transcription created for offline review, 23 August 2026;
no real schedule image examined.

| Name as represented | Relationship to designated head | Age | Birthplace |
| --- | --- | ---: | --- |
| Henry Carter | Head | 49 | Ohio |
| Alice Carter | Wife | 46 | Missouri |
| Eleanor Carter | Daughter | 18 | Missouri |
| Clara Carter | Boarder | 21 | Idaho |

The relationship label reports Eleanor's represented relationship to the designated
head. It does not by itself describe Eleanor's relationship to every household
member. Clara's shared surname and residence do not establish kinship. Household
membership is contextual evidence, not a family conclusion.

### P1 and P2 — one probate packet, two observations

**P1 citation draft:** Estate of Henry Carter, petition for administration,
fictional Ada County probate file `PR-1931-417`, filed 3 April 1931, p. 2; synthetic
offline transcription created 23 August 2026; no real file examined.

P1 states: `The decedent left a daughter, Eleanor Reed of Boise.` It explicitly
represents a daughter relationship, but the petitioner and basis of knowledge are
not included in this limited fixture.

**P2 citation draft:** Estate of Henry Carter, distribution receipt signed
`Eleanor M. Reed`, fictional Ada County probate file `PR-1931-417`, 17 September
1931; synthetic offline transcription created 23 August 2026; no real file examined.

P2 shows that a person using that name signed a distribution receipt. It does not
state a relationship. Any inference that she received property as Henry's daughter
must remain separately labeled and must cite both the receipt and the applicable
distribution context, which is not present in this fixture.

P1 and P2 are distinct documents in one represented estate file. Their shared file
context must remain visible; two documents do not automatically equal two
independent informants.

### F1 — conflicting memorial representation

The retained fictional memorial snapshot states `Daughter of Thomas Carter.` It is
user-contributed text with no underlying source identified. The observation remains
visible even if later research judges it less reliable. Its cause is unknown; the
packet must not label it a transcription error without evidence.

## 4. Preserve original representations and explicit transformations

| Assertion | Original representation | Compared representation | Transformation | Limitation |
| --- | --- | --- | --- | --- |
| M1 bride | `Eleanor May Carter` | `eleanor may carter` | case-folding and whitespace normalization | No nickname or identity inference |
| M2 bride | `Eleanor M. Carter` | `eleanor m carter` | punctuation removal and case-folding | Middle initial remains less specific than middle name |
| D1 birth | `14 Mar. 1892` | `1892-03-14` | date parsing under stated Gregorian calendar rule | Parsing does not establish accuracy |
| C1 age | `18` on represented enumeration date | estimated 1891–1892 birth range | documented age-to-range calculation | Enumeration timing and reported age may be inaccurate |
| P2 signature | `Eleanor M. Reed` | `eleanor m reed` | punctuation removal and case-folding | Signature identity has not been independently authenticated |

The original representation remains primary. A transformation supports comparison
only and cannot overwrite the observation.

## 5. Review one candidate-specific comparison trace

**Comparison context:** `S1-fixture-context/1`<br>
**Rule manifest:** `S1-rules/1`<br>
**Researcher overrides:** none<br>
**Purpose:** deterministic review ordering only

| Trace | Inputs | Rule and version | Classification | Ordering effect | Researcher-readable explanation |
| --- | --- | --- | --- | ---: | --- |
| T1 | M1 bride ↔ candidate name `Eleanor M. Carter` | `name/middle-initial-compatible/1` | compatible | +1 | The candidate's middle initial is compatible with the represented middle name. This is not exact textual agreement or identity proof. |
| T2 | D1 birth ↔ candidate birth `14 March 1892` | `date/exact-value/1` | exact value agreement | +1 | Parsed displayed dates agree. This establishes neither accuracy nor source independence. |
| T3 | C1 age range ↔ candidate birth `14 March 1892` | `date/range-contains/1` | compatible | +1 | The candidate date falls inside the range calculated from the represented census age. |
| T4 | M1 father Henry ↔ candidate father Henry | `relationship/displayed-value/1` | exact value agreement | +1 | Both representations display Henry Carter as father. Dependence and reliability remain unevaluated. |
| T5 | F1 father Thomas ↔ candidate father Henry | `relationship/conflicting-value/1` | material conflict | 0 | The two affirmative father assertions conflict and require research. The conflict is not offset by agreements. |
| T6 | M2 father absent ↔ candidate father Henry | `missing/neutral/1` | not stated in comparison source | 0 | The index supplies no father value. Missing information is neither support nor conflict. |

The trace has no probability or proof score. The total contribution may sort a
candidate for review, but the visible explanation leads with agreements, unknowns,
and the unresolved material conflict. No trace can update an assessment or create a
conclusion.

### Replay receipt

Given the same six input assertion references, original values, normalized values,
rule manifest, rule versions, and absence of overrides, replay produced the same six
classifications and ordering contributions. Replay demonstrates computational
reproducibility only. It does not establish the candidate's identity or the truth of
the father assertion.

## 6. Distinguish explicit, contextual, and inferred relationships

| Observation | What is represented | Contract treatment |
| --- | --- | --- |
| M1 | `Henry Carter` in a bride's-father field | Explicit source-displayed relationship assertion; not automatically accepted |
| M1 | Alice B. Carter as witness | Observed role; no kinship inferred |
| D1 | William Reed labeled husband and informant | Explicit source-displayed role/relationship with informant context |
| C1 | Eleanor labeled daughter of household head | Explicit relationship to designated head only |
| C1 | Clara shares household and surname | Contextual association; no relationship assertion created |
| P1 | Eleanor Reed named as daughter of decedent | Explicit source-displayed relationship assertion with unknown informant basis |
| P2 | Eleanor M. Reed signed receipt | Observed participant role; possible relationship remains an inference |
| F1 | Thomas Carter named in contributed memorial text | Explicit source-displayed assertion with unresolved conflict and weak provenance |

## 7. Represent capture scope, missing information, and negative searches

Each observation states what representation was used and what was outside capture
scope. `Not collected`, `not represented in the fixture`, `not stated in the
record`, and `searched but not located within stated coverage` are distinct.

Example negative search:

- Repository: fictional Ada County Clerk archive
- Collection: probate general index
- Coverage: 1925–1940, surnames A–Z
- Jurisdiction: Ada County, Idaho
- Date searched: 23 August 2026
- Names and variants: Eleanor Carter, Eleanor Reed, Eleanor M. Carter, Eleanor M.
  Reed
- Method: exact surname entries plus manual page review under Carter and Reed
- Result: no separate estate file for Eleanor located
- Limitations: index may omit misfiled, transferred, sealed, or out-of-county
  proceedings; no docket or neighboring jurisdiction was searched

This result is a documented search observation, not proof that no proceeding
existed.

## 8. Inspect the minimum audit projection

The proposed audit projection is a human- and machine-readable view of selected
research, not a database dump or universal interchange standard. This fictional
packet would contain:

1. packet format identifier and version;
2. creation time, producing application/version, and privacy/redaction statement;
3. research question and stable local subject identifier;
4. each selected source representation, citation, provenance, capture scope,
   limitations, observation date, and content hash or stable snapshot reference;
5. original assertions and separately labeled normalized representations;
6. explicit roles, source-displayed relationships, contextual associations, and
   separately labeled inferences;
7. comparison context, rules and versions, overrides, classifications, explanations,
   conflicts, unknowns, and ordering effects;
8. negative searches and unresolved questions;
9. assessment and decision history included in the export;
10. any conclusion's exact selected evidence references, analysis, material-conflict
    treatment, author, date, and supersession link; and
11. validation warnings, omissions, unsupported structures, and a deterministic
    manifest covering the exported components.

The projection does not require inclusion of copyrighted images or sensitive data.
Omission and redaction must be explicit. A recipient should be able to determine
what was observed and why a conclusion was made even when an image cannot be
redistributed.

## 9. Review prompts

Review only this artifact as a Professional Genealogist. Do not consult graver's
source code, schema, roadmap, or intended implementation.

1. Can you distinguish the record creator, repository, access surface, source class,
   and representation actually examined for every item?
2. Do the citation drafts accurately describe only the synthetic representations
   used, without implying that an unavailable image or underlying original was
   examined?
3. Are original, derivative, transcribed, normalized, contextual, explicit,
   inferred, missing, and negative-search information kept meaningfully distinct?
4. Are informants, witnesses, household roles, and probate participants represented
   without manufacturing kinship or independence?
5. Can you explain every comparison classification and ordering effect without
   reading a rules file or treating the result as confidence or proof?
6. Does the comparison trace preserve enough exact context for computational replay?
   What remains necessary for genealogical reproducibility?
7. Can every material conflict remain visible through assessment, conclusion,
   supersession, and export?
8. Would the minimum audit projection let another qualified researcher understand
   what was observed, transformed, selected, and concluded without querying graver's
   database?
9. Which proposed fields or distinctions are unnecessary, overly technical, or
   premature? Which indispensable distinctions are missing?
10. Does this contract remain focused, or is it drifting toward an unachievable
    universal genealogy model?
11. Identify findings as **blocking**, **important**, or **follow-up**, and explain
    the concrete correction needed.

## S1 decision rule

S1 passes only if the reviewer can interpret the packet without developer coaching
and finds no unresolved blocking defect in source fidelity, assertion attribution,
relationship restraint, comparison transparency, conflict permanence, researcher
control, or audit portability. Passing approves the shared distinctions for a
bounded internal implementation prototype; it does not approve a public file
format, schema, provider adapter, source-class roadmap commitment, or identity
automation.
