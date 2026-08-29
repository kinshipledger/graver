# Security threat model

This document records graver's final-`1.0.0` engine security boundaries,
assumptions, and known risks. It follows the practical threat-modeling pattern of identifying
assets, trust boundaries, threats, controls, and residual risk. It is a living
engineering record, not a certification.

**Assessment dates:** 2026-08-25; refreshed 2026-08-27

**Scope reviewed:** application source, transport/parser boundaries, SQLite and
configuration lifecycle, CLI output, dependencies, packaging, GitHub workflows,
tests, and public privacy/security documentation.

## Current scope and assumptions

graver is a local, single-researcher command-line application. It has no hosted
service, accounts, telemetry, remote synchronization, or production GUI. It reads
public web representations through HTTPS when the researcher explicitly requests
acquisition and stores research in a local SQLite database.

The current model trusts the operating-system account that runs graver. It does
not defend a database from an attacker who already controls that account or the
machine. Hosted services, shared databases, untrusted plugin execution, and a GUI
would create new boundaries and require a new review before release. Any future
small-team or shared-workspace capability must separately re-threat-model identity
and authentication, organization/workspace/case isolation, role authorization,
provider-credential ownership, auditability, concurrent edits, sharing and export,
remote synchronization, and incident response before it is offered to researchers.

## Assets

- Research databases, backups, observations, citations, notes, and conclusions.
- Information about living people or sensitive inferred relationships that a
  researcher may add, even when the original memorial data is public.
- Provider queries, URLs, cookies, and network metadata.
- Database integrity, immutable provenance, and decision history.
- Release artifacts, dependencies, automation credentials, and repository history.

## Data flows and trust boundaries

```text
researcher -> CLI -> typed application services -> local SQLite files
                         |
                         +-> injected HTTPS transport -> external provider

GitHub contributor -> pull request -> CI/security checks -> release artifact
```

Provider HTML, imported files, command arguments, configuration files, environment
variables, and database paths are untrusted inputs. Parser and transport types do
not cross the public application boundary. SQL values are parameter-bound; the
remaining dynamic identifiers and query fragments use fixed internal allowlists
and were manually reviewed for this assessment.

## Risk register

| ID | Risk | Rating | Current treatment |
|---|---|---:|---|
| SEC-001 | Research queries silently persisted in a default log | High | Fixed before RC: importing or running the CLI no longer creates a log file; explicit diagnostics use standard error. |
| SEC-002 | Local databases and backups expose sensitive research if the device or account is compromised | High | New files use owner-only permissions. SQLite is not encrypted; use OS access controls and full-disk encryption. Accepted local-app limitation, prominently documented. |
| SEC-003 | Provider-controlled text could include terminal control characters | Medium | Fixed: one CLI presentation boundary renders C0/C1 and bidirectional controls visibly in human output while retained evidence and JSON remain unchanged. Covered by adversarial tests; tracked in [issue 79](https://github.com/kinshipledger/graver/issues/79). |
| SEC-004 | An unexpectedly large provider response could consume excessive memory | Medium | Fixed: the Requests transport streams into a bounded 8 MiB buffer, rejects an oversized declared or observed body with a typed error, closes the response, and persists nothing. Covered by offline boundary tests; tracked in [issue 80](https://github.com/kinshipledger/graver/issues/80). |
| SEC-005 | Malformed provider HTML reached assertions that disappear under optimized Python | Medium | Fixed before RC: malformed links/counts produce typed parse failures. |
| SEC-006 | Dynamic SQL construction | Medium | Reviewed: identifiers and clauses come from fixed internal fields; values are bound. Ruff's generic S608 finding is documented rather than silently treated as proof of injection. CodeQL provides an independent check. |
| SEC-007 | Compromised dependency or build automation | High | Locked dependencies, full-SHA-pinned workflow actions, required CI `pip-audit` and Ruff security checks, Dependabot, CodeQL, isolated builds, least-privilege workflow permissions, and OIDC Trusted Publishing bound to `kinshipledger/graver`. No long-lived publishing token remains. |
| SEC-008 | Research data accidentally committed or shared | High | Database, GEDCOM, broad generated output, logs, environment, and credential artifacts are ignored; sharing guidance still requires human review. |
| SEC-009 | Local tampering with research history | Medium | Transactions, foreign keys, immutable-event triggers, backups, and integrity checks detect or prevent many changes. No cryptographic authorship or hostile-local-user protection is claimed. |
| SEC-010 | Disposable browser-review server misuse | Low | Loopback-only, fictional data, temporary database, not installed as a production interface. Reassess before any production browser or GUI service. |
| SEC-011 | Provider learns request metadata and query terms | Medium | Inherent to live acquisition. No telemetry or proxy concealment is used. Researchers choose when to make live requests. |
| SEC-012 | Upgrade damages irreplaceable research | High | Explicit upgrades, verified backups, transactions, rollback, structural validation, integrity and foreign-key checks, and recovery guidance. |
| SEC-013 | Future import adapters ingest hostile or privacy-sensitive content | High | Not implemented. Parsing limits, provenance, privacy classification, and adversarial fixtures are mandatory admission gates. |

## Security invariants

- No network request occurs during the default test suite.
- Access challenges, `403`, and repeated `429` responses fail closed.
- Database upgrades are explicit and backed up.
- Expected errors do not disclose tracebacks or secrets to ordinary users.
- JSON output contains only its documented envelope on standard output.
- No default persistent diagnostic log is created.
- No automated identity or kinship conclusion bypasses researcher review.
- Secrets, cookies, private genealogy data, and real research databases never
  belong in tests, issues, pull requests, or vulnerability reports.

## Release and review gates

The `1.0.0rc1` gate closed with all Critical and High findings fixed or covered by a
dated, explicit maintainer risk decision and user-facing mitigation. Dependency
audit, CodeQL, secret scanning, the offline suite, and packaging checks passed.

The focused final-`1.0.0` review on 2026-08-27 rechecked responsible access,
transport and parser bounds, CLI output, privacy documentation, packaging, workflow
permissions, action pinning, and the organization/PyPI migration. It found no
release-blocking defect. It did identify that locally required `pip-audit` and Ruff
security checks were not repeated by CI; the final-1.0 correction adds them to the
required quality lane. A full penetration test is disproportionate for the present
local CLI, but becomes
necessary before any hosted service, authentication, remote synchronization,
untrusted plugin execution, or network-accessible production interface.

Report vulnerabilities through [SECURITY.md](../SECURITY.md).
