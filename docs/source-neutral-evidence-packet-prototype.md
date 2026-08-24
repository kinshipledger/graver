# Source-neutral evidence packet review prototype

**Status:** Initial S1 review blocked; revised for focused re-review; not implemented product behavior<br>
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

The blocked initial review and required corrections are preserved in the
[23 August 2026 S1 report](professional-researcher-s1-review-2026-08-23.md).

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

## 2. Identify every represented source and examined fixture

Every item carries these fields independently. `Unknown`, `not represented`, and
`not applicable` are explicit values rather than omissions.

| Item | Record creator represented | Repository or custodian represented | Access surface used | Source class | Carrier or record form represented | Representation actually examined | Workflow role |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Ada County clerk | Fictional Ada County Clerk archive | Local offline fixture | Civil marriage register | Bound civil register | Synthetic human transcription; no real image or register examined | Observation |
| M2 | Fictional index publisher; individual indexer unknown | Fictional Idaho Genealogy Index | Local offline fixture | Marriage index | Derivative searchable index | Synthetic index entry; no index image examined | Discovery lead and derivative observation |
| D1 | Idaho Bureau of Vital Statistics | Fictional Idaho State Archives vital-record collection | Local offline fixture | Civil death certificate | Certificate abstract representing selected fields | Synthetic structured abstract; no certificate image examined | Observation |
| C1 | U.S. Census Bureau; represented enumerator unknown | Fictional National Archives census collection | Local offline fixture | Population census schedule | Household schedule | Synthetic line transcription; no schedule image examined | Observation and household context |
| P1 | Fictional Ada County probate court; represented petitioner unknown | Fictional Ada County Clerk archive | Local offline fixture | Probate petition | Document in estate case file | Synthetic document transcription; no real file examined | Observation |
| P2 | Fictional Ada County probate court; signatory represented as Eleanor M. Reed | Fictional Ada County Clerk archive | Local offline fixture | Probate distribution receipt | Document in the same estate case file as P1 | Synthetic document transcription; no real file examined | Observation |
| F1 | Find a Grave memorial contributor represented as unknown | Find a Grave represented as publisher/custodian of the memorial page | Local retained offline fixture | Online memorial | User-contributed memorial page | Synthetic retained full-page text snapshot; no live page or underlying source examined | Observation and candidate lead |
| X1 | Fictional collaborative-tree contributors, individually unknown | Fictional Example Family Tree | Local retained offline fixture | Collaborative person profile | Mutable online profile | Synthetic candidate-profile snapshot; no live profile or attached record examined | Candidate discovery and comparison input |

Repository or custodian means the body represented as holding or publishing the
record representation. Access surface means where this review actually encountered
it. Neither is silently substituted for the record creator. A later authorized
adapter could encounter a similar record through a provider, archive, local image,
or researcher transcription without changing these distinctions.

These labels are an extensible minimum, not a closed taxonomy. An unfamiliar role,
record form, or historical structure remains available as attributed descriptive
text with a documented warning rather than being forced into the nearest listed
category.

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
role of witness. The represented supplier of the bride, groom, father, and event
statements is unknown. The witness role is preserved and is not converted into
kinship.

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

| Item represented | Value as represented in the examined fixture | Represented supplier or role |
| --- | --- | --- |
| Name | `Eleanor May Reed` | personal-information supplier not attributable from fixture; informant field names William Reed but does not expressly attribute this item |
| Death | `8 Nov. 1967, Boise` | medical certifier and supplier not represented in fixture |
| Birth | `14 Mar. 1892, Missouri` | supplier not attributable from fixture; possible informant dependence remains unknown |
| Father | `Henry Carter` | supplier not attributable from fixture; possible informant dependence remains unknown |
| Informant | `William Reed, husband` | William Reed is explicitly represented in the informant field; this does not attribute every certificate item to him |

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

The represented enumerator is unknown, as is the household member or other person
who supplied each response. The relationship label reports Eleanor's represented
relationship to the designated head. It does not by itself describe Eleanor's
relationship to every household member. Clara's shared surname and residence do not
establish kinship. Household membership is contextual evidence, not a family
conclusion.

### P1 and P2 — one probate packet, two observations

**P1 citation draft:** Estate of Henry Carter, petition for administration,
fictional Ada County probate file `PR-1931-417`, filed 3 April 1931, p. 2; synthetic
offline transcription created 23 August 2026; no real file examined.

P1 states: `The decedent left a daughter, Eleanor Reed of Boise.` It explicitly
represents a daughter relationship, but the represented petitioner, supplier of
that assertion, and basis of knowledge are unknown in this limited fixture.

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

**Citation draft:** Find a Grave, synthetic memorial page for “Eleanor May Carter
Reed (1892–1967),” fictional memorial `12345678`, represented full-page text snapshot
`F1-SNAP-2026-08-21`, captured and observed 21 August 2026; local offline review
fixture examined 23 August 2026; no live memorial, memorial image, contributor
profile, or underlying record examined.

- Website or publisher represented: Find a Grave
- Memorial contributor represented: unknown
- Stable represented locator: fictional memorial `12345678`
- Captured section: memorial heading, life dates, cemetery text, and biography text
- Material captured text: `Daughter of Thomas Carter.`
- Not collected or represented: contributor identity, edit history, memorial images,
  image attribution, and any underlying source for the father statement
- Supplier of the father assertion: unknown memorial contributor or editor

The observation remains visible even if later research judges it less reliable. Its
cause is unknown; the packet must not label it a transcription error without
evidence.

### X1 — candidate-profile snapshot

**Citation draft:** Example Family Tree, synthetic collaborative profile “Eleanor M.
Carter,” fictional profile `K1AB-CDE`, represented profile snapshot
`X1-SNAP-2026-08-21`, captured and observed 21 August 2026; local offline review
fixture examined 23 August 2026; no live profile or attached record examined.

- Name as represented: `Eleanor M. Carter`
- Birth as represented: `14 March 1892`
- Father as represented: `Henry Carter`
- Individual contributors or suppliers: unknown
- Attached support: none represented in the fixture
- Limitation: these are unsupported working-profile assertions, not reviewed facts
  or summaries of an examined record

### Representation-fidelity note

“Captured text/value” means the value retained from the representation actually
examined. It does not classify an underlying source as original. Each item separately
records its represented record form, the fixture actually examined, and any known
derivation.

The synthetic fixture states whether spelling, punctuation, abbreviations, line
breaks, illegibility, and omissions were preserved. In this artifact, quoted text
preserves the fictional spelling, capitalization, and punctuation supplied by the
fixture; layout and line breaks are not represented unless stated. A structured
abstract such as D1 explicitly omits unselected certificate fields and is not a
transcription of a complete record.

## 4. Preserve captured values and explicit transformations

| Assertion | Value as represented in examined fixture | Compared representation | Transformation | Limitation |
| --- | --- | --- | --- | --- |
| M1 bride | `Eleanor May Carter` | `eleanor may carter` | case-folding and whitespace normalization | No nickname or identity inference |
| M2 bride | `Eleanor M. Carter` | `eleanor m carter` | punctuation removal and case-folding | Middle initial remains less specific than middle name |
| D1 birth | `14 Mar. 1892` | `1892-03-14` | date parsing under stated Gregorian calendar rule | Parsing does not establish accuracy |
| C1 age | `18` on represented enumeration date | estimated 1891–1892 birth range | documented age-to-range calculation | Enumeration timing and reported age may be inaccurate |
| P2 signature | `Eleanor M. Reed` | `eleanor m reed` | punctuation removal and case-folding | Signature identity has not been independently authenticated |

The captured value remains primary. A transformation supports comparison only and
cannot overwrite the observation or imply that an underlying original record was
examined.

### Assertion suppliers, derivation, and dependence

These relationships travel with the assertions rather than depending on nearby
prose:

| Assertion or group | Represented supplier | Known derivation or shared provenance | Researcher evaluation of supplier knowledge |
| --- | --- | --- | --- |
| M1 bride, groom, event, and father fields | Unknown | Same represented register entry | Undetermined |
| M2 bride, groom, and event fields | Unknown indexer | Fixture expressly says M2 derives from M1 | Secondary/derived from M1 for repeated values |
| D1 personal-information fields | Not attributable from fixture; William Reed is named only as record informant | Possible common informant, but item-level dependence is unknown | Undetermined for each personal-information assertion |
| D1 death field | Medical supplier/certifier not represented | Dependence on personal-information fields not represented | Undetermined |
| C1 household responses | Unknown enumerator and unknown respondent | Same household schedule and enumeration event | Undetermined |
| P1 daughter assertion | Unknown petitioner or supplier | Same probate proceeding as P2 | Undetermined |
| P2 signature/participation | Eleanor M. Reed represented as signatory | Same probate proceeding as P1; no claim that P2 copied P1 | Undetermined; the fixture represents a signature but does not authenticate the signer or establish knowledge of a relationship |
| F1 father assertion | Unknown memorial contributor or editor | Underlying source and dependence unknown | Undetermined |
| X1 profile assertions | Unknown collaborative contributors | No attached support represented; dependence on F1 or other sources unknown | Undetermined |

Observed role, represented supplier, known derivation, shared provenance, and the
researcher's evaluation of information quality are separate. `Firsthand`,
`secondary`, and `undetermined` are evaluations of the represented supplier's likely
knowledge when an evaluation is made; they do not change captured text or guarantee
accuracy. Unknown dependence never becomes a claim of independence.

## 5. Review one candidate-specific comparison trace

**Comparison context:** `S1-fixture-context/1`<br>
**Rule manifest:** `S1-rules/1`<br>
**Researcher overrides:** none<br>
**Purpose:** deterministic review ordering only

| Trace | Inputs | Rule and version | Classification | Ordering effect | Researcher-readable explanation |
| --- | --- | --- | --- | ---: | --- |
| T1 | M1 bride assertion: captured `Eleanor May Carter`, compared as `eleanor may carter` ↔ X1 name assertion: captured `Eleanor M. Carter`, compared as `eleanor m carter`; X1 is an unsupported profile assertion | `name/middle-initial-compatible/1` | compatible | +1 | X1's middle initial is compatible with M1's represented middle name. This is not exact textual agreement or identity proof. |
| T2 | D1 birth assertion: captured `14 Mar. 1892`, compared as `1892-03-14` ↔ X1 unsupported birth assertion: captured `14 March 1892`, compared as `1892-03-14` | `date/exact-value/1` | exact value agreement | +1 | Parsed displayed dates agree. This establishes neither accuracy nor source independence. |
| T3 | C1 age assertion: captured `18`, compared as estimated 1891–1892 birth range ↔ X1 unsupported birth assertion: captured `14 March 1892`, compared as `1892-03-14` | `date/range-contains/1` | compatible | +1 | X1's represented date falls inside the range calculated from C1's represented census age. |
| T4 | M1 father assertion: captured `Henry Carter`, unchanged for comparison, supplier unknown ↔ X1 unsupported father assertion: captured `Henry Carter`, unchanged, contributor unknown | `relationship/displayed-value/1` | exact value agreement | +1 | M1 and X1 display the same father value. X1 is unsupported, and dependence and reliability remain unknown. |
| T5 | F1 father assertion: captured `Thomas Carter`, unchanged, contributor unknown ↔ X1 unsupported father assertion: captured `Henry Carter`, unchanged, contributor unknown | `relationship/conflicting-value/1` | material conflict | 0 | The two affirmative father assertions conflict and require research. The conflict is not offset by agreements. |
| T6 | M2: father field not represented ↔ X1 unsupported father assertion: captured `Henry Carter`, unchanged | `missing/neutral/1` | not stated in comparison source | 0 | M2 supplies no father value. Missing information is neither support nor conflict. |

The trace has no probability or proof score. The total contribution may sort a
candidate for review, but the visible explanation leads with agreements, unknowns,
and the unresolved material conflict. No trace can update an assessment or create a
conclusion.

An override may change review ordering only. It must be visible, dated, attributed,
reasoned, versioned, and replayable. It cannot alter captured text, observations,
citations, provenance, suppliers, derivation or dependence, transformations,
missing-information treatment, material-conflict status or permanence, relationship
meaning, assessment history, or the requirement for a researcher-authored
conclusion. No override can manufacture identity, kinship, or source independence.

### Replay receipt

Given the same six input assertion references, captured values, normalized values,
rule manifest, rule versions, and absence of overrides, replay produced the same six
classifications and ordering contributions. Replay demonstrates computational
reproducibility only. It does not establish the candidate's identity or the truth of
the father assertion.

Genealogical reproduction additionally requires the exported captured
representations or complete transcriptions, capture-faithful citations and scope,
assertion suppliers, derivation and dependence links, search logs, researcher-
authored analysis, selected evidence, unresolved conflicts, conflict treatment, and
decision history. A hash can verify that referenced content has not changed; it
cannot make omitted or inaccessible content inspectable.

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
| X1 | Henry Carter displayed as father on an unsupported collaborative profile | Explicit source-displayed profile assertion; contributor, support, and dependence are unknown |

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

### Material-conflict permanence

Once a conflict is identified as material to an assessment or conclusion, it cannot
be silently removed, downgraded, neutralized, or omitted by evidence selection,
rules, overrides, later assessment, conclusion, supersession, or export. Every later
record concerning that research question must include the conflict and its current
treatment, or explicitly explain—with author, date, evidence, and reason—why it no
longer bears on the question.

Correction, reclassification, or retraction never deletes the contrary observation
or earlier treatment. The history preserves who made the change, when, why, what
evidence was considered, and the before/after classification. Selecting favorable
evidence cannot exclude F1 while its father assertion remains material.

## 8. Inspect the minimum audit projection

The proposed audit projection is a human- and machine-readable view of selected
research, not a database dump or universal interchange standard. This fictional
packet would contain:

1. packet format identifier and version;
2. creation time, producing application/version, and privacy/redaction statement;
3. research question and stable local subject identifier;
4. each selected source representation—and every representation required by the
   material-conflict invariant—with citation, provenance, capture scope,
   limitations, observation date, and content hash or stable snapshot reference;
5. captured assertions and separately labeled normalized representations;
6. explicit roles, source-displayed relationships, contextual associations, and
   separately labeled inferences;
7. assertion-level suppliers, known derivation, shared provenance, dependence or
   unknown dependence, and separately labeled researcher evaluations of information
   quality;
8. comparison context, rules and versions, overrides, classifications, explanations,
   every material conflict, unknowns, and ordering effects;
9. negative searches and unresolved questions;
10. assessment and decision history included in the export;
11. any conclusion's exact selected evidence references, analysis, material-conflict
    treatment, author, date, and supersession link; and
12. validation warnings, omissions, unsupported structures, and a deterministic
    manifest covering the exported components.

The projection does not require inclusion of copyrighted images or sensitive data.
Omission and redaction must be explicit. A recipient should be able to determine
what was observed and why a conclusion was made even when an image cannot be
redistributed.

Every reference necessary to interpret the packet resolves to human-readable
content contained within the packet or to a fully cited external representation.
Local subject, snapshot, assertion, conflict, rule, conclusion, and supersession
identifiers supplement that content; they never substitute for it. A packet includes
the cited values, roles, transformations, explanations, analyses, conclusions, and
history needed to understand each link without a graver installation or database.

When copyright, privacy, availability, or selection prevents inclusion, the packet
identifies the omitted or inaccessible material, why it is absent, how it may be
located when permitted, and how the absence limits independent review. A content
hash or manifest entry proves neither inspectability nor evidentiary sufficiency.

Format identifiers, application versions, hashes, rule identifiers, and manifests
must be accompanied by researcher-readable labels and explanations. They support
integrity and replay but are not the professional-facing explanation by themselves.

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
