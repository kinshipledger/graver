[![CI](https://github.com/mcqueary/graver/actions/workflows/python-package.yml/badge.svg)](https://github.com/mcqueary/graver/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://coveralls.io/repos/github/mcqueary/graver/badge.svg)](https://coveralls.io/github/mcqueary/graver)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

graver
======

Scrape and Retrieve [FindAGrave](http://findagrave.com) memorial data and save them to an SQL database.

Graver supports responsible, researcher-directed acquisition and
provider-authorized data workflows. It is not designed to bypass access controls or
conceal automated activity. Users remain responsible for complying with applicable
laws, provider terms, and access policies. See the project
[access policy](docs/access-policy.md) for the acquisition and contribution rules.

Project direction and verified implementation status are maintained in the
canonical [project context](docs/project-context.md),
[existing-system inventory](docs/existing-system-inventory.md), and
[initial inspection guide](docs/initial-inspection.md).

Project changes and releases are documented in the [changelog](CHANGELOG.md).
Developers should also read the [contribution guide](CONTRIBUTING.md) and
[security policy](SECURITY.md).

New to Graver? Follow the [researcher tutorial](docs/tutorial.md) for a small,
safe, end-to-end workflow from database creation through one approved memorial
enrichment.


## Scraping
[FindAGrave](http://findagrave.com) is a free website providing access to and an opportunity to input cemetery information to an online database of cemetery records (over 226 million and counting). Often when doing genealogy research, you don't want to rely on a webpage's future and so you want to download the information to your local filesystem. ```graver```takes a list of Find A Grave memorial IDs or FindAGrave URLs, scrapes relevant genealogical data, and stores the contents in a SQLite3 database.


## Requirements

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

## Usage
### Install

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

For development, install every dependency group and run the test suite with:

```shell
uv sync --all-groups --locked
uv run --group test pytest
```

### Create or select a database

Create a new current-schema research database and select it as the default:

```shell
uv run graver init
uv run graver init research.db
```

With no argument, `init` creates `./graves.db`. A supplied path creates the named
database. Initialization refuses to overwrite any existing path, and it selects the
new database only after creation and validation succeed.

Choose an existing Graver database once, then use ordinary research commands
without repeating its path:

```shell
uv run graver use /path/to/research.db
uv run graver use --show
uv run graver use --clear
```

`use` stores the resolved absolute path in Graver's per-user configuration file;
it selects an existing database and does not create or migrate it. Database
selection follows this order:
an explicit `--db`, the `GRAVER_DB` environment variable, the saved selection,
then the existing `graves.db` default. `--db` is a temporary override for one
command and never changes the saved selection. An unavailable saved or environment
database is reported instead of silently falling back.

### Upgrade an older database

Selection and ordinary reads never migrate a database. If Graver reports that an
older database needs an upgrade, run the specialist maintenance command explicitly:

```shell
uv run graver admin database upgrade /path/to/research.db
```

Upgrade first inspects the database read-only, then creates a verified sibling
backup before applying ordered migrations transactionally. A current database is
reported as current without being rewritten or backed up. If the deterministic
backup path already exists, Graver refuses to replace it; preserve or rename that
backup before retrying. Failed post-backup upgrades retain the backup and report
recovery guidance, but restoration remains a deliberate human action.

Use `graver init` only to create a new database. Use `graver use DATABASE` to select
an existing compatible database without changing its schema.

### Scrape
```sh
uv run graver scrape-file <input-file>
```
The memorial data will be saved in a SQL database (default: `graves.db`), where it can be viewed with any SQLite viewer, or exported to CSV. 

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

### Administrative redirect maintenance

The `admin` namespace contains specialist maintenance and diagnostics. Find a
Grave redirects are retained as explicit provenance instead of silently moving
research to the destination memorial:

```shell
uv run graver admin aliases list --db graves.db --status active
uv run graver admin aliases show SOURCE_ID --db graves.db
uv run graver admin aliases record SOURCE_ID TARGET_ID --db graves.db --type merged
uv run graver admin aliases retract SOURCE_ID --db graves.db --reason "reviewed correction"
```

`work enrich` refuses a source with a known active alias before making a request.
If a new merge is discovered, it records the alias and failed full acquisition
for review, keeps the source task ready, and does not scrape or modify the target.
A research task is owned internally by a stable research subject, while existing
commands continue to use the memorial ID through which the person was discovered.
Aliases do not merge subjects or move, complete, or delete tasks. Earlier top-level
task and alias commands remain available as hidden compatibility aliases for
existing scripts, but are omitted from normal help output.

### Exporting
Future versions of `graver` will support direct export to CSV from the CLI, but for now, you can use SQLite3 to execute these commands, which will output the contents of `graves.db` to `graves.csv`:
```shell
$ sqlite3 graves.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output graves.csv
sqlite> select * from graves;
sqlite> .quit
```
Alternatively, you can do exactly the same thing by running a shell script like the following (this script is provided in `bin/export.sh`):
```shell
#!/bin/sh
sqlite3 graves.db <<EOF
.headers on
.mode csv
.output graves.csv
select * from graves;
.quit
EOF
```


## License

This is intended as a convenient tool for personal genealogy research. Please be aware of FindAGrave's [Terms of Service](https://secure.findagrave.com/terms.html).

MIT © [Larry McQueary](https://github.com/mcqueary), [Robert Pirtle](https://pirtle.xyz)
