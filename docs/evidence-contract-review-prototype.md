# Evidence contract review prototype

**Status:** Low-fidelity review artifact; not implemented product behavior<br>
**Gate:** R1 — Evidence contract review<br>
**Scenario:** Fictional and offline; no live provider data

## How to use this artifact

Act as the researcher responsible for deciding whether either external candidate
represents the same person as the active research subject. Read the panels in order,
then complete the review prompts at the end. The wording and information hierarchy
are under review; none of the controls below are implemented commands or screens.

## 1. Keep the active subject visible

### Active research subject

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

Two candidates were returned by the same fictional offline discovery run.

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

Ordering method: `fixture-ordering/1` — agreements first, then material conflicts,
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
| Birth | 14 Mar 1892 | 14 Mar 1892 | exact | Original observed dates agree. |
| Birthplace | Missouri | St. Louis, Missouri | compatible | Candidate is more specific; the memorial does not establish the city. |
| Death | 8 Nov 1967 | 8 Nov 1967 | exact | Original observed dates agree. |
| Burial | Morris Hill Cemetery, Boise | Morris Hill Cemetery, Boise | exact | Cemetery name and locality agree. |
| Father | Thomas Carter | Henry Carter | conflict — material | Both sources make affirmative, incompatible claims about the same relationship. Parentage may distinguish two people and requires resolution. |
| Mother | not stated | Alice Brown Carter | missing | The memorial supplies no value. Missing information is not negative evidence by itself. |
| Spouse | not stated | William Reed | review required | The candidate assertion has no memorial value to compare. Additional sources may corroborate or oppose it. |

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

### Related memorials observed on the source page

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

Review question: is **related memorial observation** sufficiently clear, or does
another term better prevent a displayed family link from being mistaken for a
proved relationship?

## 4. Record evolving assessment separately from a conclusion

### Assessment controls

Proposed states: **new**, **reviewing**, **deferred**, **reopened**, and
**ready for decision**.

Current state: **reviewing**<br>
Version: **3**

Research notes:

- Negative search: no probate record located in the first Ada County index search.
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

- **Accepted:** the reviewed evidence supports the same-person conclusion.
- **Rejected:** the reviewed evidence supports that this is a different person.
- **Unresolved:** the available evidence does not support acceptance or rejection.
- **Withdrawn:** a prior conclusion is no longer endorsed; the prior record remains.

A conclusion requires:

1. researcher or reviewer;
2. reasoned analysis;
3. references to the evidence and comparisons relied upon;
4. explicit treatment of every material conflict; and
5. the prior conclusion identifier when superseding or withdrawing a decision.

Example first decision:

> **Unresolved** — Parentage remains materially conflicting, and the available
> assertions appear derivative. Matching dates and burial place are substantial but
> do not resolve whether the profiles represent the same Eleanor Carter. Review by
> L. Researcher, 23 August 2026. Evidence references: birth, death, burial, father.

Example later decision after new evidence:

> **Accepted; supersedes conclusion C-001** — A contemporaneous marriage record and
> death certificate independently identify Henry Carter as father and William Reed
> as spouse. The memorial biography's Thomas Carter statement is treated as an
> unresolved transcription error, not silently discarded. Review by L. Researcher,
> 2 September 2026. Evidence references: prior comparison plus marriage and death
> certificate observations.

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
- 2 existing memorials updated from new summary observations
- 20 immutable observations appended
- 0 failures
- No full memorial pages retrieved

Suggested next action: `Queue the acquired people for review.`

The receipt reports the operation's effect. It does not claim that the acquired
facts are correct or that any memorial identifies a FamilySearch person.

## 7. Inspect a draft citation projection

### Draft Find a Grave citation

> Find a Grave, database and images, “Eleanor May Carter” (1892–1967), memorial
> 12345678, Morris Hill Cemetery, Boise, Ada County, Idaho; memorial page observed
> 21 August 2026, `https://www.findagrave.com/memorial/12345678`; contributor and
> image attribution not present in the captured observation.

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
