# Privacy and data handling

Genealogical information deserves careful handling even when an individual fact
was found on a public website. Correlation, private notes, living-person details,
and inferred relationships can make a local research collection more sensitive
than any single source.

## What graver handles

graver may retain memorial observations, names, dates, places, displayed website
relationship links, citations, research notes, candidate assessments, negative
searches, identity conclusions, provenance, and immutable history. Researchers may
also enter information about living people or sensitive family circumstances.

Public availability is not a privacy classification. Treat a database according
to its most sensitive content.

## Where information goes

- Research data is stored in the SQLite database the researcher selects.
- Verified upgrade backups are stored beside that database.
- The saved default-database preference is stored in the operating system's user
  configuration directory.
- graver has no telemetry, cloud account, hosted synchronization, or analytics.
- Live acquisition sends the requested URL, query parameters, IP/network metadata,
  and a transparent graver user agent to the external provider over HTTPS.
- The CLI does not create a persistent log by default. Explicit diagnostic output
  goes to the terminal's standard-error stream and may include query details at
  debug level.

New databases, backups, and temporary configuration writes use owner-only file
permissions where the operating system supports them. graver does not silently
change permissions on an existing database. SQLite files are not encrypted by
graver; use a protected user account, full-disk encryption, secure backups, and an
appropriately protected device.

## Safe research and sharing practices

- Keep the working database and its backups out of shared or cloud-synchronized
  folders unless that sharing is intentional and suitably protected.
- Minimize collection of living-person and sensitive information.
- Review citations, notes, exports, screenshots, and diagnostic output before
  sharing them or attaching them to an issue.
- Use fictional or sanitized fixtures for bug reports and tests.
- Do not commit databases, exports, cookies, credentials, or `.env` files.
- Confirm provider terms, lawful authority, professional obligations, and consent
  requirements for the intended research and jurisdiction.

Immutable provenance protects research integrity, but it also means a correction
does not silently erase earlier observations. Backups and filesystem copies may
retain deleted content. graver therefore does not claim secure erasure. If a
privacy deletion is required, identify and handle the working database, backups,
exports, logs created by other tools, and storage-provider copies together.

## Regulatory posture

graver is open-source software, not a declaration that every use is compliant with
privacy law or professional ethics. Applicability depends on who operates it, whose
data is handled, location, purpose, scale, sharing, and whether a hosted or
commercial service is involved. The project does not claim blanket GDPR, CCPA, or
other regulatory compliance.

Seek qualified advice before operating graver as a service, processing living-
person data at scale, combining sensitive datasets, serving users across
jurisdictions, selling or sharing personal information, or introducing accounts,
telemetry, cloud storage, collaboration, or automated decision-making.
