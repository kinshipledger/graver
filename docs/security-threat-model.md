# Security threat model

This document records graver's pre-`1.0.0rc1` security boundaries, assumptions,
and known risks. It follows the practical threat-modeling pattern of identifying
assets, trust boundaries, threats, controls, and residual risk. It is a living
engineering record, not a certification.

**Assessment date:** 2026-08-25

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
would create new boundaries and require a new review before release.

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
| SEC-003 | Provider-controlled text could include terminal control characters | Medium | Fixed: one CLI presentation boundary renders C0/C1 and bidirectional controls visibly in human output while retained evidence and JSON remain unchanged. Covered by adversarial tests; tracked in [issue 79](https://github.com/mcqueary/graver/issues/79). |
| SEC-004 | An unexpectedly large provider response could consume excessive memory | Medium | Explicit timeouts and bounded retries exist; response-size limiting is tracked in [issue 80](https://github.com/mcqueary/graver/issues/80). |
| SEC-005 | Malformed provider HTML reached assertions that disappear under optimized Python | Medium | Fixed before RC: malformed links/counts produce typed parse failures. |
| SEC-006 | Dynamic SQL construction | Medium | Reviewed: identifiers and clauses come from fixed internal fields; values are bound. Ruff's generic S608 finding is documented rather than silently treated as proof of injection. CodeQL provides an independent check. |
| SEC-007 | Compromised dependency or build automation | High | Locked dependencies, pinned workflow actions, Dependabot, `pip-audit`, CodeQL, isolated builds, and least-privilege workflow permissions. |
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

Before `1.0.0rc1`, all Critical and High findings must be fixed or have a dated,
explicit maintainer risk decision with user-facing mitigation. Dependency audit,
CodeQL, secret scanning where the repository plan permits it, the offline suite,
and packaging checks must pass. Medium findings must be tracked and assessed for
RC impact.

Before final `1.0.0`, obtain an independent targeted review of database lifecycle,
transport/parser boundaries, CLI output, packaging, and privacy documentation.
A full penetration test is disproportionate for the present local CLI, but becomes
necessary before any hosted service, authentication, remote synchronization,
untrusted plugin execution, or network-accessible production interface.

Report vulnerabilities through [SECURITY.md](../SECURITY.md).
