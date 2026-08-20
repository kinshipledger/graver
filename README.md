[![CI](https://github.com/mcqueary/graver/actions/workflows/python-package.yml/badge.svg)](https://github.com/mcqueary/graver/actions/workflows/python-package.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://coveralls.io/repos/github/mcqueary/graver/badge.svg)](https://coveralls.io/github/mcqueary/graver)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

graver
======

Scrape and Retrieve [FindAGrave](http://findagrave.com) memorial data and save them to an SQL database.

Project direction and verified implementation status are maintained in the
canonical [project context](docs/project-context.md),
[existing-system inventory](docs/existing-system-inventory.md), and
[initial inspection guide](docs/initial-inspection.md).


## Scraping
[FindAGrave](http://findagrave.com) is a free website providing access to and an opportunity to input cemetery information to an online database of cemetery records (over 226 million and counting). Often when doing genealogy research, you don't want to rely on a webpage's future and so you want to download the information to your local filesystem. ```graver```takes a list of Find A Grave memorial IDs or FindAGrave URLs, scrapes relevant genealogical data, and stores the contents in a SQLite3 database.


## Requirements

[uv](https://docs.astral.sh/uv/getting-started/installation/) is required to
install and run `graver`. A separate Python installation is optional: uv uses
the version pinned in `.python-version` and downloads it when necessary. The
project supports Python 3.10 or newer.

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

### Scrape
```sh
uv run graver scrape-file <input-file>
```
The memorial data will be saved in a SQL database (default: `graves.db`), where it can be viewed with any SQLite viewer, or exported to CSV. 

### Research tasks

Queue existing memorials, inspect them, and explicitly approve one memorial at a
time for full-page enrichment:

```shell
uv run graver queue-memorials --db graves.db --cemetery-id 2181249
uv run graver list-tasks --db graves.db --status unprocessed
uv run graver show-task MEMORIAL_ID --db graves.db
uv run graver update-task MEMORIAL_ID --db graves.db --status ready_for_full_scrape
uv run graver scrape-task MEMORIAL_ID --db graves.db
```

`scrape-task` accepts exactly one memorial and only proceeds when its durable
task is in `ready_for_full_scrape`. Listing, showing, updating, and queueing tasks
make no network requests.

### Memorial aliases and merged memorials

Find a Grave redirects are retained as explicit provenance instead of silently
moving research to the destination memorial:

```shell
uv run graver list-aliases --db graves.db --status active
uv run graver show-alias SOURCE_ID --db graves.db
uv run graver record-alias SOURCE_ID TARGET_ID --db graves.db --type merged
uv run graver retract-alias SOURCE_ID --db graves.db --reason "reviewed correction"
```

`scrape-task` refuses a source with a known active alias before making a request.
If a new merge is discovered, it records the alias and failed full acquisition
for review, keeps the source task ready, and does not scrape or modify the target.
A research task always remains attached to the memorial ID through which the
person was discovered.

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
