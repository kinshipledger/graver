# First-time setup for researchers

This guide is for genealogical researchers who want to use graver locally and do
not routinely work with Python or command-line tools. You do not need to understand
Python, SQLite, or software development to follow it.

## Four terms before you begin

**Terminal** means the text-based application where you type graver commands. On
macOS, open **Terminal**; on Windows, open **PowerShell**; on Linux, open your usual
terminal application. A command runs only after you type or paste it and press
Enter.

**uv** is the installer and tool manager used to install graver. It can obtain a
compatible Python runtime for graver, keep graver separate from other applications,
and place the `graver` command where your terminal can find it. You do not otherwise
need to use or learn Python.

**Command path** is the list of places your terminal checks when you type a command.
If installation succeeds but the terminal says `graver: command not found` or
PowerShell says that `graver` is not recognized, uv can add its tool directory to
that list. Run `uv tool update-shell`, follow its message, close the terminal, and
open it again.

**Local database** means the single file where graver stores the acquired memorial
records, dated observations, research queue, notes, and history for that project.
The database uses SQLite internally, but you do not need SQLite software for the
ordinary graver workflow. Treat this file as research material: know where it is,
back it up, and do not publish it without reviewing it for private information.

## What installation changes

Installing the release candidate with uv:

- installs graver for your user account in an isolated tool environment;
- installs or selects a compatible Python runtime for that environment when needed;
- makes the `graver` command available to your terminal; and
- records enough tool information for uv to upgrade or uninstall graver later.

Installation does **not**:

- create a research database;
- contact Find a Grave or another genealogy provider;
- upload genealogy data, create an account, or enable cloud synchronization;
- change an existing family tree, GEDCOM file, or research database; or
- install the graver source code and contributor test tools in your working folder.

The first database file is created only when you deliberately run `graver init`.
Live provider access occurs only when you later run a live acquisition command such
as `graver search` or an approved `graver work enrich`.

## Install uv

Use the official [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
and choose the method appropriate for your computer. Its macOS/Linux and Windows
PowerShell commands are also reproduced in the project [README](../README.md#installation).

After installation, close and reopen the terminal, then check uv:

```shell
uv --version
```

If the command is not found, return to the uv installation instructions before
continuing.

## Install and verify graver

Install the published release candidate:

```shell
uv tool install 'graver-genealogy==1.0.0rc1'
graver --version
graver --help
```

The distribution is called `graver-genealogy`, but the command you type is
`graver`. Do not install the unrelated PyPI distribution named simply `graver`.

If uv says its tool directory is not on your command path, run:

```shell
uv tool update-shell
```

Then close the terminal, open it again, and retry `graver --version`.

## Choose where the research database will live

Before creating a database, use the terminal to enter a folder you recognize and
intend to back up. For a practice run, the tutorial uses a new folder named
`graver-tutorial`. Running this command there:

```shell
graver init tutorial.db
```

creates `tutorial.db` in that folder and selects it as the active database. graver
prints the full path after creation. Confirm it at any time with:

```shell
graver use --show
```

The selected database contains the research work. Selecting a different database
changes where later commands read and write; it does not move, combine, or delete
either file. `graver use --clear` forgets the saved selection but does not delete
the database.

## Continue with the guided workflow

The [researcher tutorial](tutorial.md) walks through a small practice project from
database creation through one deliberately approved memorial enrichment. It labels
every step as offline or live and includes symptom-oriented troubleshooting.

Developer source checkouts, tests, and contribution tools are intentionally kept
out of this setup path. They are documented separately in the
[contribution guide](../CONTRIBUTING.md).
