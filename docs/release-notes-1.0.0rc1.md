# graver 1.0.0rc1 release notes (draft)

These notes describe the intended first release candidate. They remain a draft
until the package version is changed, the release gates pass, and Release Please
creates the reviewed release pull request.

## Who should try the release candidate

`1.0.0rc1` is intended for researchers and application developers willing to test
the first supported graver contracts before `1.0.0`. Use copies or well-backed-up
research databases and report unclear behavior as well as defects.

## Researcher highlights

- A first-class `graver` command and supported `python -m graver` fallback.
- Explicit database creation, selection, inspection, and backed-up upgrades.
- Narrow Find a Grave summary acquisition followed by an explicit person-at-a-time
  queue, approval, and full enrichment workflow.
- Immutable summary and full observations, redirect provenance, and acquisition
  receipts that identify changed displayed values without rewriting old snapshots.
- Research subjects that keep internal person-level work independent of a memorial
  identifier without claiming genealogical identity.
- Fail-closed provider handling and an offline-by-default test contract. graver does
  not solve access challenges or provide unattended bulk acquisition.

FamilySearch discovery, production identity matching, WikiTree publishing, GEDCOM
interchange, background jobs, and the desktop interface are not included in this
release candidate.

## Breaking changes from the development-era 0.1 interface

- Hidden top-level task and alias commands were removed in favor of `graver work …`
  and `graver admin aliases …`.
- `scrape-url` and unattended `scrape-file` were removed. Use summary search, queue,
  explicit approval, and one-person enrichment.
- Search options now use consistent kebab-case names and explicit Boolean pairs.
- Successful `--json` output now uses a versioned envelope with the result under
  `data`.
- The package root no longer exports parser, transport, SQL, task, or alias helpers.
  Application clients use the typed `graver.application` boundary.
- Ordinary commands no longer migrate old databases implicitly.

The [command-line migration table](cli-migration.md) lists exact replacements. The
[JSON contract](cli-json.md) and [developer API guide](api.md) describe the supported
machine-facing boundaries.

## Database migration

New databases use schema version 5. Existing recognized legacy, unversioned, or
older versioned databases require the explicit command:

```shell
graver admin database upgrade /path/to/research.db
```

The command creates a verified sibling backup, runs ordered migrations in one
transaction, and validates the result. It does not fabricate missing provenance or
identity conclusions. Read the complete [database upgrade and recovery guide](database-upgrades.md)
before upgrading irreplaceable research.

## Developer contract

The supported synchronous application boundary is `graver.application`, led by
`open_workspace(path)`. It uses typed immutable requests, results, and application
errors; explicit database paths; short-lived internal SQLite connections; safe
progress and cancellation; and optimistic task concurrency. SQLite rows, Typer,
Rich, Requests, parser models, and transport mechanics are not public API types.

Python 3.11 through 3.14 are supported. The wheel, both command entry points, and an
independent consumer workflow are verified in CI.

## Security and provider access

graver uses a conventional Requests transport with explicit timeouts, transparent
identification, bounded retries, and fail-closed handling for access challenges,
`403`, and repeated `429` responses. The former challenge-handling transport and its
unused browser-emulation dependency chain were removed. Ordinary tests cannot open
network sockets, and recorded provider contracts run replay-only.

This change may cause acquisition to stop where an older development version tried
to handle a provider challenge automatically. That is intentional. Operational
delays and retry limits do not create authorization; the project access policy still
governs every provider integration.

The RC also introduces a published threat model and privacy/data-handling guide.
The CLI no longer creates a persistent `graver.log` merely by being imported or
run; explicit diagnostics go to standard error. Malformed provider links are typed
parse failures rather than assertions. Locked dependencies are audited with
`pip-audit`, and CodeQL analyzes Python changes and `main` on a weekly schedule.

Research databases are local, unencrypted SQLite files. Newly created databases
and upgrade backups use owner-only permissions where supported, but graver does not
silently change existing file permissions or claim secure deletion. Researchers
should use device access controls and full-disk encryption and review sensitive or
living-person information before sharing any database, export, or diagnostic text.

## Deprecations

There are no active deprecations in this release candidate. Obsolete hidden commands,
duplicate option spellings, accidental package-root imports, and unattended scrape
paths were removed before the supported 1.0 contract. Their replacements are listed
above and in the migration guide.

## Known limitations

- The primary interface is command-line only; the desktop application is later
  work.
- Find a Grave is an external mutable service. Layout or access-policy changes may
  stop acquisition until reviewed; the separate live canary is intentionally
  minimal and is not a bulk test.
- Full-record acquisition remains one explicitly approved memorial at a time.
- Displayed relationship links are website observations, not accepted kinship.
- Candidate ordering and internal evidence prototypes do not provide a production
  identity-matching workflow or automated conclusions.
- Database restoration is manual; graver creates and reports verified upgrade
  backups but does not overwrite research data automatically.
- Machine-readable CLI failures are not yet a versioned JSON error contract. Python
  clients can use the structured application exception taxonomy.

## Feedback requested

Please report installation problems, migration and recovery ambiguity, command help
that assumes developer knowledge, inconsistent CLI/API behavior, and anything that
makes provenance or saved changes difficult to understand. Do not attach private
research databases, credentials, cookies, or personal data to a public issue.
