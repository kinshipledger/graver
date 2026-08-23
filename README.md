[![CI](https://github.com/mcqueary/graver/actions/workflows/python-package.yml/badge.svg)](https://github.com/mcqueary/graver/actions/workflows/python-package.yml)
[![Coverage Status](https://coveralls.io/repos/github/mcqueary/graver/badge.svg?branch=main)](https://coveralls.io/github/mcqueary/graver?branch=main)
[![Python: 3.11–3.14](https://img.shields.io/badge/Python-3.11%E2%80%933.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Package manager: uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9?logo=uv)](https://docs.astral.sh/uv/)

graver
======

Build a local, provenance-aware research database from
[Find a Grave](https://www.findagrave.com/) memorials, then review and enrich records
one person at a time.

graver preserves summary and full-page observations separately, maintains a durable
research queue, and records acquisition history without treating a memorial as a
proven genealogical identity. FamilySearch matching, reviewed identity conclusions,
WikiTree integration, and a desktop interface are planned but are not available yet.

New to graver? Follow the [researcher tutorial](docs/tutorial.md) for a small,
safe workflow from database creation through one approved memorial enrichment.

graver supports responsible, researcher-directed acquisition and
provider-authorized data workflows. It is not designed to bypass access controls or
conceal automated activity. Users remain responsible for complying with applicable
laws, provider terms, and access policies. See the project
[access policy](docs/access-policy.md) for the acquisition and contribution rules.

## What graver does

- Saves narrow Find a Grave search results as summary observations in SQLite.
- Queues acquired memorials for researcher-directed review.
- Retrieves a full memorial only after the researcher explicitly approves that
  person for enrichment.
- Preserves immutable acquisition observations alongside the current record.
- Records Find a Grave redirects for review without silently merging people or
  transferring research.

graver is currently a command-line application intended for local research. It is
not yet a cross-platform identity-matching or family-tree publishing system.

## Installation

[uv](https://docs.astral.sh/uv/getting-started/installation/) is required to
install and run `graver`. A separate Python installation is optional: uv uses
the version pinned in `.python-version` and downloads it when necessary. The
project supports Python 3.11 through 3.14.

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

Clone the repository, enter its root directory, and synchronize the environment
from the committed lockfile:

```shell
git clone https://github.com/mcqueary/graver.git
cd graver
uv sync --locked
```

This creates a virtual environment at `.venv` and installs `graver` with its
locked dependencies. Run the command-line application through uv; activating
the virtual environment is not required:

```shell
uv run graver --help
```

## Getting started

### Create or select a database

Create a new current-schema research database and select it as the default:

```shell
uv run graver init
uv run graver init research.db
```

With no argument, `init` creates `./graves.db`. A supplied path creates the named
database. Initialization refuses to overwrite any existing path, and it selects the
new database only after creation and validation succeed.

Choose an existing graver database once, then use ordinary research commands
without repeating its path:

```shell
uv run graver use /path/to/research.db
uv run graver use --show
uv run graver use --clear
```

`use` selects an existing database and does not create or upgrade it. An explicit
`--db` applies to one command without changing the saved selection. Run
`graver use --show` whenever you need to confirm which database is active.

### Upgrade an older database

Selection and ordinary reads never migrate a database. If graver reports that an
older database needs an upgrade, run the specialist maintenance command explicitly:

```shell
uv run graver admin database upgrade /path/to/research.db
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
uv run graver search --id 1075 --max-results 1
```

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
uv run graver work queue --cemetery-id 2181249
uv run graver work next
uv run graver work show MEMORIAL_ID
uv run graver work mark MEMORIAL_ID --status ready_for_full_scrape
uv run graver work enrich MEMORIAL_ID
```

`work enrich` accepts exactly one memorial and only proceeds when its durable
task is in `ready_for_full_scrape`. Listing, showing, marking, choosing, and
queueing people make no network requests. Use `work show --history` when detailed
acquisition provenance is needed; ordinary output keeps that detail summarized.

### Redirect review

Find a Grave redirects are retained for review instead of silently moving research
to the destination memorial. When a redirect affects the current person,
`work show` explains the next action. Detailed inspection and correction commands
are available under:

```shell
uv run graver admin aliases --help
```

`work enrich` refuses a source with a known active alias before making a request.
If a new merge is discovered, it records the alias and failed full acquisition
for review, keeps the source task ready, and does not scrape or modify the target.
Redirects do not merge people or move, complete, or delete research tasks.

### Basic CSV export

graver does not yet provide a dedicated export command. The SQLite command-line
tool can export the current `graves` table to CSV:

```shell
$ sqlite3 graves.db
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

- [Researcher tutorial](docs/tutorial.md)
- [Access policy](docs/access-policy.md)
- [Documentation index](docs/README.md)

For contributors and maintainers:

- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Project context and roadmap](docs/project-context.md)
- [Verified implementation inventory](docs/existing-system-inventory.md)
- [Initial inspection guide](docs/initial-inspection.md)

Longer-term ideas—including GEDCOM interchange—are indexed with the other
architecture documents in [docs](docs/README.md). They are not part of the current
researcher workflow.

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
