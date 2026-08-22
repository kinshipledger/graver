# Research one Find a Grave memorial with graver

This tutorial is for genealogical researchers who are comfortable entering
commands but do not need to know Python or SQLite. It creates a dedicated
database, acquires a deliberately small summary result set, and retrieves one
full memorial only after you approve it.

Commands below assume the installed command is named `graver`. If you are
working from a source checkout, use `uv run graver` anywhere the examples say
`graver`.

## The workflow

```text
Find a Grave search
  → summary record persisted
  → research task queued
  → person inspected
  → explicit enrichment approval
  → one full-page retrieval
  → immutable acquisition observation
  → enriched current record
```

graver does not automatically retrieve every full memorial page. Summary
searches can establish a useful research queue with fewer requests; a researcher
then decides which one person merits a full retrieval. This reduces load on Find
a Grave and prevents unattended bulk enrichment.

## 1. Verify the installation

These commands are offline:

```shell
graver --version
graver --help
```

Success means the first command reports graver's installed version and the
second lists commands including `init`, `use`, `search`, and `work`. At any point,
append `--help` at the level you need, for example `graver work --help` or
`graver work enrich --help`.

## 2. Create an isolated tutorial database

Create a new directory yourself, enter it, and initialize the database. The
directory name is only an example; use a location you can identify later.

```shell
mkdir graver-tutorial
cd graver-tutorial
graver init tutorial.db
graver use --show
```

The `init` success message identifies the absolute path:

```text
Initialized and selected research database: /.../graver-tutorial/tutorial.db
```

`use --show` should report that same absolute path. Both graver commands are
offline. Keep the path: it distinguishes this practice database from other
research databases.

The three database commands have deliberately separate jobs:

- `graver init DATABASE` creates a new current-schema database and selects it.
  It refuses every existing path. With no argument, it creates `./graves.db`.
- `graver use DATABASE` selects an existing compatible database without creating
  or upgrading it.
- `graver admin database upgrade DATABASE` creates a required sibling backup and
  explicitly upgrades a recognized older database. Selection and ordinary reads
  never migrate a database.

You should not need the upgrade command for the newly initialized tutorial
database.

## 3. Acquire one small summary result set

The following recommended example contacts Find a Grave. It asks for memorial
ID `1075`, the public George Washington memorial, and caps processing at one
result:

```shell
graver search --id 1075 --max-results 1
```

Success means the search completed and any returned summary was saved in the
selected tutorial database. The current search command does not print a result
table. Find a Grave is a changing live service, so the memorial is not promised
to appear first—or to be returned at all. You will identify it after queueing by
looking for literal memorial ID `1075`. If this example stops being reliable,
substitute a memorial ID you already know, or use a narrow cemetery query shown
by `graver search --help`; keep `--max-results` small.

Search results are summary records. They may contain a name, dates, source URL,
and cemetery context, but they are not evidence that graver observed the full
memorial page.

## 4. Queue and inspect a person

These commands are offline:

```shell
graver work queue
graver work list --limit 10
graver work next
graver work show 1075
```

`work queue` should say how many people were added and how many were already
present. Repeating it is safe. `work list` identifies people by memorial ID;
look for `1075`, or choose another literal ID returned by your search and use it
in place of `1075` below. `work next` normally selects the next `unprocessed`
person. `work show` should identify the person, the `unprocessed` research state,
the cemetery context, `summary` acquisition level, and an acquisition-observation
count.

In the commands that follow, `1075` is literal only if that memorial was acquired.
In generic examples, `MEMORIAL_ID` is a placeholder and must be replaced with the
number you selected.

## 5. Approve and enrich exactly one memorial

Approval is offline:

```shell
graver work mark 1075 --status ready_for_full_scrape \
  --note "Approved during the tutorial"
graver work show 1075
```

Success means graver reports that the status and note were updated. The second
command should show `ready_for_full_scrape` and offer `graver work enrich 1075`
as the next action. Only this one task was approved.

Enrichment is the tutorial's second live Find a Grave operation:

```shell
graver work enrich 1075
```

Success includes the stable message `The full memorial was retrieved` and a
completed task state. graver retrieves only the approved memorial—no related
memorials and no other queued people.

Inspect the result offline:

```shell
graver work show 1075
graver work show 1075 --history
graver work show 1075 --json
```

Verify the following semantic facts rather than exact borders, spacing, paths,
or timestamps:

- the research state is `full_scrape_complete`;
- the acquisition level is `full`;
- `full_fetched_at` has a timestamp in JSON output;
- provenance includes a successful `full` acquisition observation;
- the original summary observation still exists;
- the Find a Grave source URL still identifies memorial `1075`;
- the cemetery ID or cemetery context remains present.

`--history` intentionally reveals immutable observation detail. `--json` exposes
the complete current machine-readable record, including fields that ordinary
human output summarizes. Optional values such as plot, coordinates, biography,
birth or death places may legitimately be absent. **Fully enriched** means the
full memorial page was successfully observed and persisted, not that every
optional field was populated.

## 6. Stop and resume safely

graver persists the queue, task state, current memorial data, and observations in
`tutorial.db`. You may close the terminal and later resume with:

```shell
graver use --show
graver work next
graver work list --limit 10
graver work show 1075
```

If you selected another database in the meantime, return to the tutorial with
`graver use /absolute/path/to/graver-tutorial/tutorial.db`. A one-command `--db`
option temporarily overrides the selection but does not replace it.

## 7. Optional cleanup

Keeping `tutorial.db` for later practice is safe. If you decide to remove it,
first display and record the exact absolute path, then clear only graver's saved
preference:

```shell
graver use --show
graver use --clear
```

`use --clear` does not delete or alter the database. Delete the file only with a
specific, non-recursive operation appropriate to your operating system after you
have verified the exact path. Never use a broad wildcard or recursive deletion
for tutorial cleanup.

## Live-service safety

Only `search` and `work enrich` contact Find a Grave; initialization, selection,
queueing, inspection, approval, and cleanup of the preference are offline. This
tutorial intentionally makes a very small number of requests. Cloudflare may
block, challenge, or delay access, and Find a Grave may time out or be unavailable.
Stop rather than repeatedly retrying. A live-site failure does not necessarily
mean the local installation or tutorial database is broken.

The automated tutorial workflow test uses deterministic mocks, rejects unexpected
network access, and never contacts Find a Grave.

## Troubleshooting

| Symptom | Safe next step |
| --- | --- |
| `graver: command not found` | Confirm graver was installed in the current environment. In a source checkout, try `uv run graver --help`. |
| Unsupported Python or incomplete installation | Reinstall using the project's documented uv workflow, then rerun `graver --version`. Retain the Python, uv, and graver versions if asking for help. |
| `tutorial.db` already exists | `init` will not overwrite it. Keep it and select it with `graver use tutorial.db` if it is compatible, or choose a new explicit filename. |
| No selected database | Run `graver use --show`, then `graver use /absolute/path/to/tutorial.db`. |
| Missing or invalid database path | Check the exact path and filename. `use` requires an existing, usable graver database and will not silently fall back. |
| Database requires explicit upgrade | Preserve the reported path and run `graver admin database upgrade DATABASE` only when you intend to create a backup and migrate that database. |
| Backup collision during upgrade | Preserve or rename the existing deterministic backup; graver will not overwrite it or begin migration. |
| No search results | Recheck the current `graver search --help`, try a known memorial ID or narrow cemetery query, and keep the result limit small. Do not loop rapid retries. |
| Cloudflare challenge or access block | Stop. Wait and use Find a Grave normally in a browser if appropriate; do not repeatedly automate retries. |
| Timeout or Find a Grave outage | Stop and try later. Offline commands can still inspect already persisted work. |
| Empty work queue | Confirm the search persisted a summary, confirm the selected database with `use --show`, then run `work queue`. |
| No actionable `work next` result | `work next` defaults to `unprocessed`. Use `work list` to see other states or `work next --status STATUS` when you intentionally want another state. |
| Task state prevents enrichment | Inspect the person, then explicitly run `work mark MEMORIAL_ID --status ready_for_full_scrape` if approval is appropriate. |
| Enrichment succeeds but optional fields are absent | This is valid: full acquisition records what the page supplied; it does not invent missing facts. |
| Unsure whether failure is local or live | If `init`, `use --show`, and `work show` succeed but `search` or `enrich` fails, the problem may be live access or a site/schema change. If offline commands fail, retain their exact error and selected database path. |
| Need command details | Use `graver --help`, `graver COMMAND --help`, or nested help such as `graver work show --help`. |
| Reporting a problem | Retain the command (remove secrets), graver/Python versions, semantic error text, selected database path, whether the step was offline or live, and whether Cloudflare appeared. Do not publish private genealogy data or configuration contents. |
