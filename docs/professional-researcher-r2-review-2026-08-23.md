# Professional researcher review report

## Review record

- **Gate:** R2
- **Review date:** 23 August 2026
- **Reviewer role and relevant experience:** Independent professional genealogist and end user applying professional standards for evidence correlation, provenance, conflict resolution, and defensible identity conclusions
- **Facilitator:** Self-directed moderated-review sequence; no developer assistance
- **Product version or commit:** Not inspected, in accordance with the review boundary
- **Issue:** GitHub issue #27; not inspected, modified, or closed
- **Environment and installation path:** Fresh disposable offline R2 session launched from the repository package directory as directed by the review guide
- **Interface and documentation reviewed:** Visible R2 offline browser workspace; `docs/r2-offline-workflow-review-guide.md`; the R2 section of `docs/researcher-review-gates.md`; canonical professional researcher report template

## Review objective

Determine whether the researcher-facing offline workflow preserves subject and candidate continuity, distinguishes discovery order and assessment state from an identity conclusion, exposes conflicts and provenance, retains earlier reasoning and observations, and supports defensible deferral, reopening, conclusion, and supersession without developer knowledge or database access.

## Scenario and artifacts

The review used only the fictional, offline Eleanor May Carter case presented in the disposable browser workspace. No live provider data were used.

The active working subject was Eleanor May Carter, born 14 March 1892 in Missouri, died 8 November 1967 in Boise, Idaho, buried in Morris Hill Cemetery, and associated with Find a Grave memorial 12345678. The interface correctly warned that these displayed details were source observations rather than automatically accepted facts.

The initial candidates were:

- K1AB-CDE, Eleanor M. Carter, review order 1; and
- L2FG-HJK, Eleanor May Carter, review order 2.

The strongest evidence was not a single matching field but the correlation of the exact displayed birth date, exact displayed death date, and burial place for K1AB-CDE. Important missing evidence included original or independently derived evidence establishing parentage and adequate provenance for the spouse assertion. The material conflict was Thomas Carter versus Henry Carter as father.

Candidate order indicated only a review aid based on the displayed comparison counts: K1AB-CDE had more agreements and fewer conflicts. It did not indicate probability, confidence, proof, source quality, a recommendation, or an identity conclusion.

The later fixture added a statement that a 1912 marriage record named Henry Carter and William Reed, described as an original marriage-register image with no informant stated. K1AB-CDE gained a second retained snapshot. L2FG-HJK disappeared from the later discovery run but remained visibly preserved and labeled “Absent from latest run · retained.”

## Tasks attempted

| Task | Completed? | Assistance required | Notes |
|---|---|---|---|
| Confirm the active working subject | Yes | None | Subject remained visible throughout the workflow. |
| Compare both candidates | Yes | None | Both comparison tables and candidate source snapshots were inspected. |
| Explain candidate ordering | Yes | None | Ordering was understood as review priority, not confidence or proof. |
| Identify agreement, missing evidence, and conflict | Yes | None | Correlated vital and burial agreements, missing parentage provenance, and the Thomas/Henry conflict were apparent. |
| Record the negative search and unresolved question | Yes | None | The control inserted a fixed negative-search entry and parentage question. |
| Defer the candidate | Yes | None | State changed to deferred, version 2, with a recorded reason. |
| Run later fixture discovery | Yes | None | K1AB-CDE changed; L2FG-HJK became absent but remained retained. |
| Identify what changed | Yes, with avoidable effort | None | The new marriage-record fields had to be found by manually comparing raw snapshot text. |
| Reopen and recover prior reasoning | Yes | None | The deferral reason and current research note remained visible; history could be expanded. |
| Record an unresolved identity conclusion | Yes | None | The earlier unresolved conclusion was preserved. |
| Examine the new evidence | Yes | None | The visible evidence was a terse assertion embedded in the candidate snapshot, not an inspectable cited record. |
| Supersede the earlier conclusion | Mechanically yes; evidentially unsafe | None | A single button created a same-person conclusion whose analysis and evidence references the reviewer could not inspect or author. |
| Explain the final conclusion | Yes | None | It accepts only that the subject and K1AB-CDE are the same person; it does not accept every candidate assertion, prove Henry Carter’s parentage, validate the spouse or mother assertions, erase Thomas Carter, establish the cause of that conflict, or convert displayed source values into accepted facts. |

## Research continuity observations

- The active subject remained prominent and unchanged during comparison, deferral, refresh, reopening, decision, and supersession. I did not lose subject context.
- Candidate context was also stable. Provider-shaped identifiers appeared with candidate names, and the later-run absence of L2FG-HJK was conspicuous.
- The earlier L2FG-HJK candidate, its comparison, and its source snapshot remained accessible after it disappeared from discovery.
- The assessment retained the negative search, unresolved question, current note, deferral reason, reopening event, author, timestamp, version, and history identifier.
- The prior unresolved conclusion remained visible after supersession, and the later conclusion visibly named the identifier it superseded.
- No external notes were necessary to click through the prescribed fixture. Professional analysis would nevertheless require external notes or copied identifiers because the interface did not attach inspectable evidence references or citations to either conclusion, did not provide a researcher-authored analysis surface, and presented snapshot content as raw structured text.
- The changed candidate was identifiable only by opening retained snapshots and manually comparing their raw contents. The interface did not summarize which assertions were added, removed, or changed.

## Evidence and conclusion observations

- The interface clearly separated candidate review order, assessment state, and explicit conclusion history. Candidate order could not create a conclusion.
- The ordering warning was strong: comparison counts were unweighted, and the interface stated that one strong conflict could matter more than several agreements.
- The material father conflict remained visible after new evidence and after the same-person conclusion. The final narrative appropriately stated that the conflict’s cause was unknown.
- “Exact value agreement” was consistently distinguished from truth, independence, and identity.
- Missing mother, spouse, and burial information was labeled unknown or not stated rather than treated as negative evidence.
- The negative-search entry was recordable but too abbreviated for professional negative-evidence analysis. It named the index span and a limitation, but did not visibly preserve the search date, searched names and variants, search method, or full scope.
- The unresolved question was clearly preserved.
- The unresolved conclusion correctly stated that matching dates and burial did not resolve the parentage conflict or identity.
- The final conclusion said “accepted as the same person” and retained the warning that acceptance did not accept every assertion. This terminology is sound.
- Decision safety was inadequate. The supersession control created a final same-person conclusion with one click. The reviewer was not shown a pre-decision analysis, could not select or verify evidence references, could not state the standard applied, and could not edit the rationale.
- The final narrative claimed that “correlated records” supported the conclusion, but the visible new material was only one brief marriage-record statement embedded in a candidate snapshot. The interface did not display the record itself, its complete citation, repository or custodian, record locator, parties and witnesses, or a separate observation identifier tied to the conclusion.

## Persistence and provenance observations

- Earlier candidate snapshots were visibly retained with observation timestamps and identifiers.
- The absent candidate remained preserved rather than being silently removed.
- Assessment and conclusion histories were append-only in the visible experience. Supersession preserved the earlier conclusion and named its identifier.
- The candidate snapshot disclosed that the original candidate support was a derivative family-group transcription with no linked original record. That limitation was useful and appropriately visible.
- The added marriage-register statement disclosed that the informant was not stated. This was useful but insufficient as a professional citation or source analysis.
- Comparison rows could not be followed directly to separately identified source observations and citations. In particular, the Thomas Carter assertion was visible as a conflict but no control exposed the cited Find a Grave observation supporting it.
- “Inspect latest source observation” displayed raw key-value content. It did not provide a researcher-readable citation, source description, provenance chain, or assertion-to-observation links.
- Opaque snapshot identifiers and timestamps assisted technical persistence but did not substitute for citations or evidence references in the conclusion.
- The workflow did not visibly provide an acquisition or change receipt. The researcher had to compare two raw snapshots to determine that the later K1AB-CDE snapshot added `new_record` and `record_note` fields.

## Onboarding and terminology observations

- “Active working subject,” “review order,” “exact value agreement,” “material conflict,” “absent from latest run · retained,” “identity unresolved,” and “accepted as the same person” were understandable and evidence-conscious.
- The distinction between displayed observations and accepted facts was unusually clear.
- “Source observation” was less satisfactory because the displayed content was a candidate snapshot containing a mixture of profile assertions and a summary of a purported external marriage record. A researcher could mistake the embedded summary for examination of the record itself.
- The numbered Compare–Defer–Refresh–Reopen–Decide–Supersede sequence was easy to follow but may encourage completion of the prescribed sequence rather than an evidence-dependent decision.
- Raw JSON-like text, UUID-style identifiers, and machine timestamps are not a suitable primary presentation for many researchers. They increase cognitive load and make manual copying more likely.
- No developer assistance was required, but the absence of researcher controls meant I could only accept the fixture’s prewritten search note, questions, reasons, and conclusions.

## Findings

| ID | Severity | Finding | Evidence | Recommended response |
|---|---|---|---|---|
| R2-B01 | Blocking | The same-person supersession is not decision-safe because it can be created with one click without researcher-authored analysis or inspectable evidence references. | The enabled “Supersede: accepted as same person” control immediately created the conclusion “Correlated records support the same-person conclusion,” while the visible new evidence was only a terse marriage-record summary inside the candidate snapshot. | Before a same-person conclusion can be saved, require the researcher-facing workflow to present and permit review of the reasoned analysis, the evidence relied upon, source-quality and dependence considerations, and explicit treatment of every material conflict. The saved conclusion must retain those inspectable references. |
| R2-B02 | Blocking | Material assertions and conclusions cannot be traced to adequate source observations and citations through the visible interface. | The Thomas-versus-Henry comparison had no visible route to the Find a Grave observation; the marriage evidence lacked a complete citation or separate observation identity; neither conclusion displayed evidence references. | Provide visible, researcher-readable routes from each material comparison and conclusion to the exact observation and citation used, including enough provenance to identify and evaluate the source. |
| R2-I01 | Important | The later discovery does not summarize what changed. | K1AB-CDE showed two snapshots, but the addition of the marriage-record fields was apparent only through manual comparison of raw snapshot text. | Present an explicit, dated change summary identifying added, removed, and changed assertions while preserving access to both snapshots. |
| R2-I02 | Important | The negative-search record lacks enough detail for professional reuse or evaluation. | The entry named the Ada County Probate Index, 1900–1970, and a coverage limitation, but not the search date, names and variants searched, or search method. | Retain and display the search date, repository or collection, coverage, jurisdiction, searched names and variants, method, result, and limitations. |
| R2-I03 | Important | The fixed controls do not demonstrate researcher control over notes, reasons, questions, or conclusions. | Clicking controls inserted predetermined content; no visible editing or evidence-selection step was offered. | Allow the researcher-facing workflow to record and review the researcher’s own negative search, unresolved question, deferral and reopening reasons, conclusion analysis, and evidence references. |
| R2-I04 | Important | The reopening history does not visibly link its reason to the new source observation. | History stated only “The marriage record is now available,” while the source summary and snapshot identifier appeared elsewhere. | Display an inspectable evidence reference with the reopening reason so the trigger can be recovered without manual copying. |
| R2-F01 | Follow-up | Raw structured text, opaque identifiers, and machine timestamps reduce accessibility and readability. | Source observations and retained snapshots appeared as JSON-like blocks with UUIDs and UTC timestamps. | Add researcher-readable labels, localized dates, field-level changes, and formatted citations while retaining technical identifiers as secondary details. |
| R2-F02 | Follow-up | The interface explains what ordering does not mean more clearly than why this particular order was produced. | Counts and warnings were visible, but no concise candidate-specific ordering explanation appeared. | Add a plain-language explanation that the first candidate is reviewed first because its displayed values produce more agreements and fewer conflicts under the current discovery comparison, without implying evidentiary weight. |

## Decisions and accepted terminology

The following terms are suitable for continued researcher-facing use:

- **Active working subject**, provided the observation-versus-fact warning remains attached.
- **Review order**, provided it remains expressly separated from confidence and proof.
- **Exact value agreement**, provided the current warning that agreement does not establish truth, independence, or identity remains visible.
- **Material conflict**.
- **Absent from latest run · retained**.
- **Identity unresolved**.
- **Accepted as the same person**, provided the interface continues to state that the conclusion does not accept every assertion.
- **Supersedes**, when the earlier conclusion remains visible and linked.

The final same-person conclusion accepts only the identity proposition that the active working subject and candidate K1AB-CDE represent the same person. It does not accept every assertion in K1AB-CDE; prove that Henry Carter was Eleanor’s father; prove Alice Brown Carter was her mother; independently validate William Reed as spouse; establish why the memorial named Thomas Carter; erase or resolve the Thomas/Henry conflict; establish the truth of matching dates and places merely because they agree; or make L2FG-HJK irrelevant to the retained research history.

No architecture or product-document decisions were made in this review.

## Blocking-finding resolution

- **R2-B01:** Unresolved. The visible workflow did not provide researcher-authored analysis or inspectable evidence references before saving the same-person supersession. No risk acceptance was presented within the permitted review materials.
- **R2-B02:** Unresolved. The visible workflow did not provide citation-level traceability from material assertions and conclusions to the observations relied upon. No risk acceptance was presented within the permitted review materials.

## Deferred questions

- Can a researcher write, revise, and review the conclusion analysis before saving it?
- Can each conclusion cite specific observations and assertions through visible, durable references?
- Can the Thomas Carter assertion be opened directly from the conflict row and evaluated in its original observed context?
- Will a new record such as the marriage register appear as its own source observation with a complete citation rather than as a summary field inside a candidate snapshot?
- Can the researcher record complete negative-search scope and limitations?
- Will changed assertions be summarized without requiring manual comparison of raw snapshots?

## Baseline comparison

This was not a repeat of an earlier R2 experiential workflow, so no prior scores were available.

| Dimension | Prior score | Current score | Explanation |
|---|---:|---:|---|
| Evidence corroboration | N/A | N/A | Qualitative review found clear comparisons but insufficient source-level support for the final conclusion. |
| Confidence and proof support | N/A | N/A | Ordering warnings were strong; final decision safety was inadequate. |
| Persistence and citation clarity | N/A | N/A | Persistence was strong, but citation and conclusion traceability were insufficient. |
| Professional onboarding | N/A | N/A | The sequence was understandable, but raw representations and fixed controls limited professional use. |

## Gate decision

- **Decision:** Does not pass
- **Decision maker:** Independent professional genealogist and end-user reviewer
- **Decision date:** 23 August 2026
- **Blocked milestone may proceed:** No
- **Conditions or follow-up issues:** Resolve R2-B01 and R2-B02 and verify them through another context-separated professional researcher workflow before the gate proceeds.

## Next review trigger

Conduct the next professional-researcher engagement when the visible offline workflow requires and preserves researcher-reviewed conclusion analysis, provides direct citation-level routes from every material comparison and conclusion to its observations, and allows the reviewer to complete the same deferral-through-supersession sequence without relying on raw snapshot comparison or prewritten conclusions.
