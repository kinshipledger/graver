# R2 offline workflow review guide

**Status:** Moderated-review artifact; not production functionality<br>
**Scenario:** Fictional and offline; no live provider data

R2 passed on 23 August 2026 after the initial review, a focused re-review, and a
final narrow verification. This guide preserves the validated scenario for future
regression reviews. A future reviewer should not be coached with the historical
answers below; provide only the visible workflow and applicable review questions.

This local review workspace exercises graver's real offline evidence service through
a deliberately temporary browser interface. It is not the future GUI, a supported
command, or the public workspace API. Its database is created in a temporary
directory and deleted when the facilitator stops the session.

## Start the review

From the repository package directory, run:

```console
uv run python -m review.r2_adapter
```

The adapter binds only to the local loopback interface and opens a browser. It makes
no provider request and does not read graver's configured database. Stop it with
Control-C. Use a fresh session for each reviewer.

## Moderation discipline

Give the reviewer only this guide, the visible interface, and the task sequence
below. Do not explain schema, identifiers, ordering code, or intended answers.
Observe where assistance or external notes become necessary.

1. Confirm the active working subject and compare both candidates.
2. Explain why the first candidate appears first and what that order does not mean.
3. Identify the strongest agreement, the missing evidence, and the material
   conflict.
4. Record the negative search and unresolved question, then defer the candidate.
5. Run the later fixture discovery. Determine what changed and which earlier
   candidate is now absent.
6. Resume the deferred assessment and recover its earlier reasoning.
7. Record an unresolved identity conclusion.
8. Inspect the new source observation, then supersede the earlier conclusion.
9. Explain what the final same-person conclusion does and does not accept.

## Focused re-review checks

The reviewer must verify, from the visible workflow rather than implementation
claims, that:

1. Same-person supersession cannot be completed without researcher-authored
   analysis, explicit treatment of the material father conflict, and deliberate
   selection of inspectable evidence records.
2. Every selected record exposes a readable citation, observation date, assertions,
   and provenance, and the saved conclusion retains direct references to it.
3. Comparison assertions show where both displayed values came from.
4. The later discovery run identifies each changed field and links the earlier and
   later retained snapshots.
5. Deferral records reproducible negative-search details, and reopening visibly
   links to its prior assessment record.

Record any later regression result in a new dated report. Do not overwrite the
initial or focused R2 reports; they are part of the project decision history.

Use the canonical
[professional researcher review report template](templates/professional-researcher-review-report.md)
to record the moderated session. The review is not complete until all R2 exit
criteria in the [researcher review gates](researcher-review-gates.md) are met.
