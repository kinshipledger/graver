# Evidence contract review prototype

**Status:** Revised after blocked R1 review; pending focused re-review; not implemented product behavior<br>
**Gate:** R1 — Evidence contract review<br>
**Scenario:** Fictional and offline; no live provider data

The initial review and unresolved gate decision are recorded in the
[23 August 2026 R1 report](professional-researcher-r1-review-2026-08-23.md).

## How to use this artifact

Act as the researcher responsible for deciding whether either external candidate
represents the same person as the active research subject. Read the panels in order,
then complete the review prompts at the end. The wording and information hierarchy
are under review; none of the controls below are implemented commands or screens.

## 1. Keep the active subject visible

### Active working research subject

**Eleanor May Carter**<br>
Born **14 March 1892**, Missouri<br>
Died **8 November 1967**, Boise, Idaho<br>
Buried **Morris Hill Cemetery**, Boise, Idaho<br>
Find a Grave memorial **12345678**

Current acquisition: full memorial observed 21 August 2026<br>
Research state: reviewing external candidates

> Context guard: every candidate, comparison, note, and conclusion in this review
> belongs to Eleanor's research subject. Changing candidates does not change the
> active subject.

## 2. Review candidate ordering without implying confidence

Two candidates were returned by the same fictional offline discovery run. The
counts below are unweighted discovery-comparison counts. They measure neither
evidentiary strength nor confidence.

| Order | Candidate | Evidence summary | Material conflicts | Unknowns |
| ---: | --- | --- | ---: | ---: |
| 1 | FamilySearch-shaped `K1AB-CDE` — Eleanor M. Carter | 3 agreements, 1 compatible value | 1 | 2 |
| 2 | FamilySearch-shaped `L2FG-HJK` — Eleanor May Carter | 2 agreements | 2 | 1 |

**Why candidate 1 appears first:** its birth date, death date, and burial place agree
with the observed memorial, and its birthplace is geographically compatible. Its
attached father conflicts with the father named in a memorial transcription. That
relationship conflict remains material and unresolved.

**What this ordering does not mean:** it is not a probability, proof statement,
confidence rating, or recommendation to accept candidate 1. Ordering cannot change
an assessment or create an identity conclusion.

Ordering method: `fixture-ordering/1` — value agreements first, then material conflicts,
then stable provider identifier. Missing data contributes neither agreement nor
conflict.

## 3. Compare one candidate without losing source context

### Candidate 1 — `K1AB-CDE`

Profile URL: `https://example.invalid/tree/person/K1AB-CDE`<br>
Snapshot observed: 21 August 2026<br>
Snapshot source: curated offline fixture

| Assertion | Find a Grave observation | Candidate snapshot | Classification | Explanation |
| --- | --- | --- | --- | --- |
| Name | Eleanor May Carter | Eleanor M. Carter | compatible | Middle initial is compatible with the observed middle name; it is not an exact textual match. |
| Birth | 14 Mar 1892 | 14 Mar 1892 | exact value agreement | The displayed values agree; this does not establish truth, source independence, or identity. |
| Birthplace | Missouri | St. Louis, Missouri | compatible | Candidate is more specific; the memorial does not establish the city. |
| Death | 8 Nov 1967 | 8 Nov 1967 | exact value agreement | The displayed values agree; this does not establish truth, source independence, or identity. |
| Burial | Morris Hill Cemetery, Boise | Morris Hill Cemetery, Boise | exact value agreement | Cemetery name and locality agree; the classification compares representations only. |
| Father | Thomas Carter | Henry Carter | conflict — material | Both sources make affirmative, incompatible claims about the same relationship. Parentage may distinguish two people and requires resolution. |
| Mother | not stated | Alice Brown Carter | not stated in comparison source | The memorial supplies no value; external research is required. Missing information is not negative evidence. |
| Spouse | not stated | William Reed | not stated in comparison source | The memorial supplies no comparison value; external research is required. The separate website-displayed family link below remains only a lead. |

### Assertion provenance on demand

**Find a Grave father assertion**

- Original representation: `Daughter of Thomas Carter`
- Observation: full memorial snapshot, 21 August 2026
- Location in observation: biography transcription
- Source limitation: user-contributed memorial text; underlying source not identified

**Candidate father assertion**

- Original representation: `Father: Henry Carter (1860–1931)`
- Observation: candidate snapshot, 21 August 2026
- Attached support: derivative family-group transcription; original record not linked
- Source limitation: both assertions may depend on unsourced or derivative material

The conflict is visible, but neither side is automatically preferred.

### Find a Grave-displayed relationship links — website display, not proven kinship

The full Find a Grave observation also captured the page's dedicated family panel:

| Displayed relationship group | Related memorial | Displayed life detail |
| --- | --- | --- |
| Parents | Thomas Carter — memorial `22334455` | 1861–1938 |
| Parents | Clara May Jones Carter — memorial `33445566` | 1865–1942 |
| Spouse | William Reed — memorial `44556677` | 1889–1954; married 1912 |
| Siblings | Alice Carter Morgan — memorial `55667788` | 1895–1971 |

Each entry preserves the displayed group label, related memorial ID and URL, name,
life text, any separately parseable dates, and observation timestamp. It means only
that Find a Grave displayed the relationship on Eleanor's page at that time. graver
has not yet retrieved the linked pages, verified reciprocity, or concluded that the
people are related. A later observation may add, remove, or relabel links without
rewriting this snapshot.

The non-proof warning is part of the heading and must travel with these values in
every display, citation, export, and machine-readable representation.

## 4. Record evolving assessment separately from a conclusion

### Assessment controls

Proposed states:

- **New:** no substantive candidate assessment has begun.
- **Reviewing:** research and comparison are in progress.
- **Deferred:** work is intentionally paused; a reason and follow-up condition or
  review date are required.
- **Reopened:** a prior assessment or conclusion requires renewed review; a reason
  and link to the earlier record are required.
- **Ready for decision:** the researcher elects to consider a conclusion. This is a
  workflow state—not confidence, proof, certification of reasonably exhaustive
  research, or permission to conclude automatically.

Current state: **reviewing**<br>
Version: **3**

Research notes:

- Negative search: no entry located for Eleanor Carter, Eleanor Reed, or Eleanor M.
  Carter in the fictional Ada County Probate Index, 1900–1970, surname and variant
  search, conducted 21 August 2026. The index may omit unindexed or out-of-county
  proceedings; this result is not proof that no probate record exists.
- Unresolved question: which father is supported by an original or independently
  derived record?
- Candidate disposition: defer until parentage and spouse evidence are checked.

Proposed action: **Defer candidate**<br>
Required reason: `Parentage conflict requires independent evidence.`

Saving this action would append history rather than replace prior notes. A client
editing version 2 would be refused as stale instead of overwriting version 3.

## 5. Make a reviewed conclusion explicitly

Candidate order and assessment state cannot populate this decision.

Proposed dispositions:

- **Accepted as the same person** (short interface label: **Accepted**): the reviewed
  evidence supports the same-person conclusion. It does not accept every assertion
  on either profile; each assertion retains its own evidentiary status.
- **Rejected as a different person** (short interface label: **Rejected**): the
  reviewed evidence supports that this is a different person.
- **Unresolved:** the available evidence does not support acceptance or rejection.
- **Withdrawn:** status applied to a prior conclusion that is no longer endorsed;
  it is not a new identity determination, and the prior record remains.

A conclusion requires:

1. researcher or reviewer;
2. reasoned analysis;
3. specific, inspectable references to the observations or records and assertions
   relied upon, including observation date;
4. explicit treatment of every material conflict; and
5. the prior conclusion identifier when superseding or withdrawing a decision.

Example first decision:

> **Unresolved** — Parentage remains materially conflicting, and the available
> assertions appear derivative. Matching dates and burial place are substantial but
> do not resolve whether the profiles represent the same Eleanor Carter. Review by
> L. Researcher, 23 August 2026. Evidence references: Find a Grave full memorial
> snapshot observed 21 August 2026, birth/death/burial and biography-father
> assertions; FamilySearch-shaped candidate snapshot K1AB-CDE observed 21 August
> 2026, birth/death/burial and father assertions; comparison C-001 rows 2–7.

Example later decision after new evidence:

> **Accepted as the same person; supersedes conclusion C-001** — A 1912 marriage
> record names Henry Carter as Eleanor's father and William Reed as spouse. A 1967
> death certificate repeats both claims, but its informant was William and the
> records are not treated as independent for those assertions. Correlated residence,
> age, and associates support the identity conclusion. The memorial biography's
> Thomas Carter assertion remains conflicting and is judged less reliable because
> it cites no underlying source; its cause is unknown and it is not discarded.
> Review by L. Researcher, 2 September 2026. Evidence references: marriage-record
> observation MR-014 observed 28 August 2026, spouse/father/informant assertions;
> death-certificate observation DC-009 observed 30 August 2026,
> identity/father/spouse/informant assertions; comparison C-004; prior conclusion
> C-001.

Both decisions remain in history. The later decision does not edit C-001.

## 6. Inspect what acquisition says was saved

### Draft acquisition receipt

**Find a Grave summary search completed**<br>
Database: `/research/carter-family.db`<br>
Requested scope: cemetery `2181249`, maximum 20 results<br>
Started: 21 August 2026, 10:14:03 MDT<br>
Completed: 21 August 2026, 10:14:05 MDT

- 20 records discovered
- 18 new memorials created
- 2 existing memorial working representations changed from new summary observations:
  - memorial `11223344`: death year `1966` → `1967`; inspect snapshots O-018 and O-041
  - memorial `99887766`: burial place `Morris Hill Cemetery` → `Morris Hill Cemetery, Boise, Idaho`; inspect snapshots O-019 and O-042
- 20 dated snapshots retained without replacing earlier snapshots
- 0 failures
- No full memorial pages retrieved

Suggested next action: `Queue the acquired people for review.`

The receipt reports the operation's effect. It does not claim that the acquired
facts are correct or that any memorial identifies a FamilySearch person.

## 7. Inspect a draft citation projection

### Draft Find a Grave citation

> Find a Grave, memorial database, “Eleanor May Carter” (1892–1967), memorial
> 12345678, Morris Hill Cemetery, Boise, Ada County, Idaho; memorial page observed
> 21 August 2026, `https://www.findagrave.com/memorial/12345678`; retained full-page
> snapshot O-001. Contributor information, images, image attribution, and underlying
> sources were outside this fictional capture's scope and were not collected; this
> citation does not imply that an image or underlying record was examined.

This projection uses only captured metadata. Missing contributor, image, and
underlying-source details are identified rather than invented. The immutable
observation remains available for inspection.

## 8. R1 review prompts

Please respond as a professional genealogical researcher, not as a software
developer:

1. Identify the active research subject and the candidate currently under review.
2. Explain what candidate 1's first-place ordering means—and what it does not mean.
3. Identify the most important agreement, missing item, and material conflict.
4. State what additional research you would perform before deciding identity.
5. Evaluate the assessment states and the four conclusion dispositions. Which terms
   are unclear, misleading, or incomplete?
6. Is the separation among ordering, assessment, and conclusion sufficiently clear?
7. Does the acquisition receipt clearly explain what was saved and what was not?
8. Does the draft citation expose enough provenance and missing information for
   professional use?
9. Identify any issue that could cause mistaken identity, lost reasoning, hidden
   conflict, or false confidence. Mark each finding **blocking**, **important**, or
   **follow-up**.
10. List any information you would still need to keep in an external research log.

Do not approve implementation merely because every required section is present. The
gate passes only if the terminology and workflow support defensible research.
