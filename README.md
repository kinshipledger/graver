[![CI](https://github.com/mcqueary/graver/actions/workflows/python-package.yml/badge.svg)](https://github.com/mcqueary/graver/actions/workflows/python-package.yml)
[![Coverage Status](https://coveralls.io/repos/github/mcqueary/graver/badge.svg?branch=main)](https://coveralls.io/github/mcqueary/graver?branch=main)
[![PyPI prerelease](https://img.shields.io/pypi/v/graver-genealogy?label=PyPI&include_prereleases)](https://pypi.org/project/graver-genealogy/)
[![Python: 3.11–3.14](https://img.shields.io/badge/Python-3.11%E2%80%933.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Lint: Ruff](https://img.shields.io/badge/lint-Ruff-D7FF64?logo=ruff&logoColor=261230)](https://docs.astral.sh/ruff/)
[![Package manager: uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9?logo=uv)](https://docs.astral.sh/uv/)

graver
======

graver is a local, provenance-aware research engine with a supported command-line
interface and a documented Python application API. Its current workflow builds a
research database from [Find a Grave](https://www.findagrave.com/) memorials, then
lets researchers review and enrich records one person at a time.

graver preserves summary and selected full-page observations separately, maintains
a durable research queue, and records acquisition history without treating a
memorial as a proven genealogical identity. FamilySearch matching, reviewed identity
conclusions, WikiTree integration, and a desktop interface are planned but are not
available yet.

New to command-line tools? Start with the
[plain-language setup guide](docs/first-time-setup.md). Then follow the
[researcher tutorial](docs/tutorial.md) for a small, safe workflow from database
creation through one approved memorial enrichment.

graver supports responsible, researcher-directed acquisition and
provider-authorized data workflows. It is not designed to bypass access controls or
conceal automated activity. Users remain responsible for complying with applicable
laws, provider terms, and access policies. See the project
[access policy](docs/access-policy.md) for the acquisition and contribution rules.

Maintainers can use the separately documented [live compatibility canary](docs/live-canary.md)
to check one stable public memorial after parser or transport changes. It is an
explicit, one-request diagnostic—not part of the ordinary test suite or a bulk
acquisition tool.

## What graver does

- Saves narrow Find a Grave search results as summary observations in SQLite.
- Queues acquired memorials for researcher-directed review.
- Observes a memorial's full page only after the researcher explicitly approves
  that person, retaining selected structured fields rather than a complete page
  archive.
- Preserves immutable acquisition observations alongside the current record.
- Captures Find a Grave-displayed relationship links from full memorial pages as
  dated website observations—not as proven family relationships.
- Records Find a Grave redirects for review without silently merging people or
  transferring research.

The command line is the current researcher and maintenance interface to the graver
engine. It is useful for technically comfortable researchers, scripting,
administration, recovery, and precise API-parity testing. It is not presented as the
complete graphical workspace intended for everyday professional-research use, nor
is graver yet a cross-platform identity-matching or family-tree publishing system.

## Current status and direction

The published `1.0.0rc1` release candidate provides the local Find a Grave
acquisition, research-queue, provenance, CLI, and typed application foundations
described above. Final 1.0 stabilizes the **graver engine**: its core behavior,
workflow rules, database lifecycle, CLI, application API, and extension boundaries.
It does not claim completion of the later professional desktop product or live
FamilySearch integration.

After the engine reaches 1.0, the professional researcher product begins its own
development and acceptance path with a desktop work queue and person-detail workflow
over the same application services. An authorized live FamilySearch adapter and
repeatable candidate discovery may follow that foundation; researcher-authored
identity conclusions, WikiTree reconciliation, GEDCOM, and additional source
adapters remain later or conditional work. Internal fictional FamilySearch-shaped
fixtures validate evidence contracts but are not a live FamilySearch integration.

See the concise public [roadmap](ROADMAP.md) for these stages and the detailed
[project context](docs/project-context.md) for their architectural reasoning. The
roadmap is directional rather than a dated feature promise.

## Installation

[uv](https://docs.astral.sh/uv/getting-started/installation/) installs `graver` in
an isolated tool environment and can supply the compatible Python runtime it needs.
The [first-time setup guide](docs/first-time-setup.md) explains uv, the terminal,
the command path, the local research database, and exactly what installation does
and does not change. The project supports Python 3.11 through 3.14.

Install uv on macOS or Linux:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Other supported installation methods, including Homebrew and WinGet, are
listed in the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

Install the published release candidate explicitly:

```shell
uv tool install 'graver-genealogy==1.0.0rc1'
graver --version
```

The published distribution is named `graver-genealogy` because the shorter PyPI
name belongs to an unrelated project. The application, command, Python import
package, and repository all remain `graver`. Installing `graver` from PyPI would
install different software.

This installs `graver` for your user account and places the command on your
terminal's command path. It does not create a database or contact a genealogy
provider. If uv reports that its tool directory is not on the path, run
`uv tool update-shell` and follow its instructions. Upgrade a published installation
with `uv tool upgrade graver-genealogy`.

Trying the release candidate? Please report a reproducible
[software defect](https://github.com/mcqueary/graver/issues/new?template=bug-report.yml)
or share
[researcher-workflow feedback](https://github.com/mcqueary/graver/issues/new?template=researcher-feedback.yml).
Remove private research data before posting; security vulnerabilities belong in a
[private advisory](https://github.com/mcqueary/graver/security/advisories/new).

Source checkouts, tests, and unreleased development installations are documented
separately in the [contribution guide](CONTRIBUTING.md). The installed `graver`
command is the ordinary researcher interface.

## Getting started

### Create or select a database

Create a new current-schema research database and select it as the default:

```shell
graver init
graver init research.db
```

With no argument, `init` creates `./graves.db`. A supplied path creates the named
database. Initialization refuses to overwrite any existing path, and it selects the
new database only after creation and validation succeed.

Choose an existing graver database once, then use ordinary research commands
without repeating its path:

```shell
graver use /path/to/research.db
graver use --show
graver use --clear
```

`use` selects an existing database and does not create or upgrade it. An explicit
global `--db` applies to one command without changing the saved selection, for
example `graver --db /path/to/client.db work list`. The saved selection is an
OS-level preference shared by every terminal and working directory for your user
account; it is not scoped to the current folder or shell session. Run `graver use
--show` whenever you need to confirm which database is active, and prefer an
explicit `--db` for commands involving multiple client or research projects.
Genealogy has enough mysteries; the active database should not be one of them.

### Upgrade an older database

Selection and ordinary reads never migrate a database. If graver reports that an
older database needs an upgrade, run the specialist maintenance command explicitly:

```shell
graver admin database upgrade /path/to/research.db
```

Upgrade first inspects the database, then creates a verified backup before changing
it. A current database is left untouched. graver refuses to overwrite an existing
backup and reports recovery guidance if an upgrade fails.

Use `graver init` only to create a new database. Use `graver use DATABASE` to select
an existing compatible database without changing its schema.

### Acquire summary records

Use a narrow search to save summary records without retrieving every individual
memorial page. For example:

```shell
graver search --memorial-id 1075 --max-results 1
```

The command returns a concise acquisition receipt distinguishing new memorials,
existing memorials, retained dated snapshots, and any current displayed values that
changed.

Search processes at most 20 summaries by default. Use `--max-results` with another
positive number when a smaller or larger bounded result set is intentional.

Search is a live operation. Keep queries narrow, stop if the provider reports an
access restriction, and consult `graver search --help` for the current filters.
The [researcher tutorial](docs/tutorial.md) explains the complete recommended
workflow. Review the [access policy](docs/access-policy.md) before using any live
acquisition command.

### Research workflow

Use `work` for normal person-by-person research. Queue acquired memorials, choose
the next person, review the current picture, record a decision, and enrich only
an explicitly approved person:

```shell
graver work queue --cemetery-id 2181249
graver work next
graver work show MEMORIAL_ID
graver work mark MEMORIAL_ID --status ready_for_full_scrape
graver work enrich MEMORIAL_ID
```

`work enrich` accepts exactly one memorial and only proceeds when its durable
task is in `ready_for_full_scrape`. Listing, showing, marking, choosing, and
queueing people make no network requests. Use `work show --history` when detailed
acquisition provenance is needed; ordinary output keeps that detail summarized.
The [research-state guide](docs/research-states.md) defines every state, its plain-
language meaning, and its network consequence.

### Redirect review

Find a Grave redirects are retained for review instead of silently moving research
to the destination memorial. When a redirect affects the current person,
`work show` explains the next action. Detailed inspection and correction commands
are available under:

```shell
graver admin aliases --help
```

`work enrich` refuses a source with a known active alias before making a request.
If a new merge is discovered, it records the alias and failed full acquisition
for review, keeps the source task ready, and does not scrape or modify the target.
Redirects do not merge people or move, complete, or delete research tasks.

### Basic CSV export

graver does not yet provide a dedicated export command. The SQLite command-line
tool can export the current `graves` table to CSV. `sqlite3` is a separate system
utility and is not installed with graver. Confirm the selected database with
`graver use --show`, then pass that exact path rather than assuming `graves.db`:

```shell
$ sqlite3 /absolute/path/reported/by-use-show.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output graves.csv
sqlite> select * from graves;
sqlite> .quit
```

This exports the current memorial rows only; it does not include the complete
observation, task, redirect, or event history. Preserve the database itself when
that provenance matters.

## Documentation

For researchers:

- [First-time setup in plain language](docs/first-time-setup.md)
- [Researcher tutorial](docs/tutorial.md)
- [Acquisition scope and citation limits](docs/acquisition-scope.md)
- [Database upgrades and recovery](docs/database-upgrades.md)
- [Access policy](docs/access-policy.md)
- [Documentation index](docs/README.md)

For contributors and maintainers:

- [Public roadmap](ROADMAP.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contribution guide](CONTRIBUTING.md)
- [Developer API guide](docs/api.md)
- [Command-line JSON contract](docs/cli-json.md)
- [Pre-1.0 command-line migration](docs/cli-migration.md)
- [1.0.0rc1 release notes](docs/release-notes-1.0.0rc1.md)
- [Maintainer release process](docs/releasing.md)
- [Performance and responsiveness](docs/performance.md)
- [Security policy](SECURITY.md)
- [Security threat model](docs/security-threat-model.md)
- [Privacy and data handling](docs/privacy-and-data-handling.md)
- [Project context and roadmap](docs/project-context.md)
- [Verified implementation inventory](docs/existing-system-inventory.md)
- [Initial inspection guide](docs/initial-inspection.md)

Longer-term ideas—including GEDCOM interchange—are indexed with the other
architecture documents in [docs](docs/README.md). They are not part of the current
researcher workflow.

Research stays in the local database you select; graver has no telemetry, account,
or cloud synchronization. Local genealogy can still be sensitive—especially when
it includes living people, private notes, or inferred relationships—so read the
[privacy and data-handling guide](docs/privacy-and-data-handling.md) before sharing
a database or export. The [threat model](docs/security-threat-model.md) documents
current protections and limitations without pretending a local SQLite file is a
fortress with a moat.

Project changes and releases are documented in the [changelog](CHANGELOG.md).

## Development

Contributor setup, tests, coverage, code style, and pull-request expectations are
documented in the [contribution guide](CONTRIBUTING.md). The locked development
environment can be installed with `uv sync --all-groups --locked`.

## License

This is intended as a convenient tool for personal genealogy research. Review and
comply with the current terms of any external service you use through graver.

graver is distributed under the [MIT License](LICENSE). The license file retains
the applicable historical copyright notices.
