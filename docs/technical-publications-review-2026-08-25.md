# Technical-publications review — 2026-08-25

## Scope and method

This bounded review evaluated only the researcher-facing material named in issue
#95: README installation and getting started, first-time setup, the researcher
tutorial, root and ordinary workflow help, acquisition-scope and citation guidance,
and documented recovery language. It did not review architecture, internal APIs,
CI, historical audits, or roadmap prose.

The review used a nondeveloper task perspective and asked whether a researcher can
identify prerequisites, predict local and network effects, recognize success,
recover safely, and find capture and citation limitations at the point of need.

## Findings

### TP-01 — Live search permits an undisclosed unlimited default

- **Severity:** Blocking
- **Surface:** `graver search --help`
- **Finding:** The command description does not say that search contacts Find a
  Grave. The `--max-results` option defaults to `0`, described as “no limit,” but
  neither the command nor the option directs researchers toward a finite limit.
  README and tutorial guidance is safer, yet a user relying on command help alone
  can initiate broader acquisition than intended.
- **Required correction:** Mark search as live in command help, give it a
  conservative finite default or require an explicit finite choice, and explain
  how to request a different bounded result count. Preserve an explicit advanced
  unlimited mode only if its access-policy implications are deliberately approved.

### TP-02 — Offline effects are not consistently stated in command help

- **Severity:** Important
- **Surface:** `init`, `use`, `work queue`, `work next`, and `work show` help
- **Finding:** The tutorial correctly identifies these actions as offline, but a
  researcher entering through help cannot consistently distinguish database-only
  commands from network operations. `init` also omits its refusal to overwrite an
  existing path from its concise help.
- **Required correction:** Add short effect statements to ordinary command help:
  offline/local for creation, selection, queueing, and inspection; live for search
  and enrichment; and overwrite refusal for initialization.

### TP-03 — Ordinary tutorial verification drifts into developer contracts

- **Severity:** Important
- **Surface:** Tutorial section 5
- **Finding:** The main success checklist asks ordinary researchers to inspect a
  JSON schema version, command identifier, timestamp field, and internal data path.
  These are valuable developer diagnostics but interrupt the evidence- and
  provenance-oriented researcher path.
- **Required correction:** Lead with human-readable verification. Move JSON
  envelope details to an optional technical troubleshooting subsection linked to
  the machine-readable contract.

### TP-04 — Folder selection assumes navigation knowledge

- **Severity:** Follow-up
- **Surface:** First-time setup and tutorial database creation
- **Finding:** The guide defines the terminal well, but “enter a folder you
  recognize” assumes knowledge of `cd` and platform path syntax. The tutorial gives
  `mkdir` and `cd` commands without explaining their effect.
- **Recommended correction:** Explain that `mkdir` creates a folder and `cd` moves
  the terminal into it; identify where the folder is created or point readers to a
  familiar absolute location.

### TP-05 — Researcher capture and citation boundaries are strong

- **Severity:** Observation
- **Surface:** Acquisition-scope guide and tutorial
- **Finding:** Summary versus full acquisition, retained versus unretained content,
  mutable current values, relationship-link limits, and conservative citation
  language are discoverable and consistent. Troubleshooting distinguishes local
  failures from live-provider failures and gives safe stop conditions.
- **Action:** Preserve these distinctions during corrections.

### TP-06 — Contributor material is appropriately separated

- **Severity:** Observation
- **Surface:** README, first-time setup, and contribution guide
- **Finding:** The ordinary installation path now uses the installed `graver`
  command and routes Git, source checkout, tests, and development environments to
  the contribution guide. The first-time guide clearly explains installation
  changes, non-effects, command-path recovery, and the database as the file
  containing the research work.
- **Action:** Preserve this boundary.

## Disposition

**BLOCKED**

TP-01 must be corrected before final 1.0 approval. TP-02 and TP-03 should be
corrected in the same bounded documentation/help pass. TP-04 may remain a tracked
follow-up if it cannot be resolved without making the setup path more complex.

After corrections, request a short professional-genealogist verification limited
to evidentiary meaning, acquisition-scope accuracy, and network consequences. A
repeat of the complete RC workflow is unnecessary unless the corrections materially
change that workflow.

## Correction record

The following corrections were prepared after the initial disposition:

- TP-01: search help now identifies a live operation; live searches default to a
  finite 20 summaries; `--max-results` accepts only positive bounded values.
- TP-02: ordinary database and work help now labels offline effects; enrichment
  identifies its one approved live retrieval; initialization states that it will
  not overwrite an existing path.
- TP-03: the ordinary tutorial verifies human-readable state, acquisition level,
  provenance, and memorial context. JSON envelope details are isolated in an
  optional technical subsection.
- TP-04: the tutorial now explains what `mkdir` and `cd` do and advises readers to
  choose a familiar, backed-up location.

Automated documentation, help, behavior, and complete offline tests passed after
these corrections. The initial **BLOCKED** disposition remains part of the review
record. Release-gate status is **PENDING SEMANTIC VERIFICATION** until a professional
genealogist confirms that the revised language preserves evidentiary meaning,
capture-scope accuracy, and network consequences.

## Professional-genealogist semantic verification

The focused independent verification subsequently returned **PASS** with no new
blocking semantic problem. It verified that:

- offline database, queue, inspection, state, and preference actions remain clearly
  distinct from live search and enrichment;
- the finite search default and positive override do not imply provider
  authorization;
- state approval remains offline and separate from one explicit live enrichment;
- `full` and “enrichment complete” remain limited to selected structured retention;
- missing-information and citation distinctions remain intact;
- moving JSON details to an optional subsection preserves researcher-visible
  provenance meaning; and
- no revised language overstates proof, confidence, identity, validation,
  completeness, kinship, or authorization.

Final technical-publications gate disposition: **PASS**.
