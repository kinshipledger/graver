# 1.0.0rc1 readiness audit

This dated audit records the release-contract state on 25 August 2026. It is a
checklist, not a declaration that the release candidate has shipped.

## Contract status

| Surface | Status | Evidence |
|---|---|---|
| Distribution identity | Ready | Install `graver-genealogy`; run and import `graver`. Wheel and source-archive smoke tests enforce the distinction. |
| Researcher CLI | Ready | The supported root, work, and administrative hierarchy is documented and exercised by CLI contract tests. |
| Python application API | Ready | Typed, adapter-neutral public imports and an installed-wheel consumer spike are tested. |
| Machine-readable output | Ready | Versioned JSON envelopes, deterministic projections, and error behavior are contract-tested. |
| Database lifecycle | Ready | Explicit creation, read-only inspection, backed-up ordered upgrades, schema refusal, rollback, integrity, and foreign keys are covered. |
| Evidence behavior | Ready for RC scope | Required professional-researcher R1, R2, and S1 reviews passed; future GUI review gates remain future scope. |
| Provider access | Ready for RC scope | Researcher-directed acquisition is fail-closed. Unattended provider acquisition remains disabled without documented authorization. |
| Portability | Ready | Python 3.11–3.14, macOS, and the bounded Windows contract are CI-covered. |
| Security and privacy | Ready for RC scope | Threat model, privacy guidance, security checks, secret scanning, response bounds, and terminal sanitization are in place. |
| Release automation | Implemented, setup pending | Tagged artifacts are built separately and published with PyPI Trusted Publishing; the GitHub environment and pending PyPI publisher still require one-time configuration. |

## Remaining release gates

1. Configure the protected `pypi` GitHub environment and pending Trusted Publisher
   for `graver-genealogy`.
2. Prepare and review the temporary Release Please prerelease configuration; verify
   by dry run that it proposes `1.0.0rc1` and a GitHub prerelease.
3. Run the full locked validation and `make release-check` on the final release pull
   request.
4. Review the generated changelog and release notes as user-facing documents.
5. Merge the release pull request, deliberately trigger publication, and verify the
   GitHub and PyPI artifacts after publication.

The production GUI, its R3 UX review, provider-governed background jobs, FamilySearch,
WikiTree, family packets, and GEDCOM are not release-candidate gates unless the RC
scope is deliberately expanded.
