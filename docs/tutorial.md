# Command-line quickstart: research one Find a Grave memorial

This quickstart is for developers, integrators, and genealogical researchers who
are comfortable entering commands in a terminal. You do not need to know Python,
SQLite, or Graver's internal design. If Graver is not installed yet, begin with
the [installation guide for researchers](first-time-setup.md).

This is a walkthrough of the Graver backend engine. It is not a preview of the
planned Kinship Ledger graphical application.

You will create a practice research file, search Find a Grave for one memorial,
and save selected details from its full page only after you approve that step.

The examples use the installed command `graver`.

## Before you begin

This quickstart uses two kinds of steps:

- **On your computer:** the step reads or changes only your local Graver research
  file. It does not contact Find a Grave.
- **Contacts Find a Grave:** the step asks the website for information. The
  quickstart clearly labels these steps before they happen.

Graver saves its work in a **research database**. Despite the name, this is one
file on your computer. The practice file in this quickstart is named `tutorial.db`.

Graver also uses two terms for its saved history:

- An **observation** is a dated copy of the supported details Graver saw during
  one search or full-page lookup.
- An **acquisition receipt** is the summary Graver shows after that operation. It
  explains what Graver saved.

A receipt records what happened. It does not prove that a website statement is
correct.

## The workflow

```text
Create and select a practice research file
  → search Find a Grave for one memorial
  → add the person to your work list
  → review the person
  → approve one full memorial-page lookup
  → see what Graver saved or changed
  → keep both the earlier and later dated observations
```

Graver does not automatically open every full memorial page. The researcher
chooses which memorial Graver may open. This limits requests to Find a Grave and
prevents Graver from gathering full-page details for an unattended list.

![The researcher journey from choosing a research file through deliberate retrieval and researcher evaluation](assets/researcher-journey.svg)

The diagram labels steps that stay on your computer, steps that contact Find a
Grave, saved history, and researcher decisions. Color is only a visual aid.

## 1. Check the installation

**On your computer**

Run:

```shell
graver --version
graver --help
```

Look for:

- a Graver version number after the first command; and
- a command list after the second, including `init`, `use`, `search`, and `work`.

If either command fails, stop and use the [troubleshooting section](#troubleshooting).

## 2. Record your current research file

**On your computer**

Graver remembers which research file to use. Before selecting the practice file,
check whether another file is already selected:

```shell
graver use --show
```

If Graver displays a file location, copy it somewhere safe. You will need it to
restore your earlier selection at the end of the quickstart. If Graver says that no
database is selected, continue.

A **complete file location** shows exactly where a file is stored. For example:

```text
/Users/your-name/Documents/graver-tutorial/tutorial.db
```

Windows displays file locations differently, often beginning with a drive letter,
such as `C:\Users\your-name\Documents\graver-tutorial\tutorial.db`.

## 3. Create the practice research file

**On your computer**

Run these commands one at a time:

```shell
mkdir graver-tutorial
cd graver-tutorial
graver init tutorial.db
graver use --show
```

The first command creates a folder named `graver-tutorial`. The second command
moves the terminal into that folder. The third creates `tutorial.db` there and
selects it as Graver's current research file.

Look for the complete location of `tutorial.db` in the last two command results.
Copy that location somewhere safe. It tells you which file contains this practice
work and lets you return to it later.

`graver init` will not replace a file that already exists. If Graver says
`tutorial.db` already exists, stop and see [Troubleshooting](#troubleshooting).

You will not need Graver's database-upgrade command in this quickstart. Creating,
selecting, upgrading, and deleting a database are separate actions. Merely
selecting a database does not create, upgrade, or delete it.

## 4. Search for one memorial

**Contacts Find a Grave**

This example searches for memorial number `1075`, the public George Washington
memorial, and stops after one result:

```shell
graver search --memorial-id 1075 --max-results 1
```

This quickstart uses `1075` in every later command. If you choose another memorial,
write its number here and replace `1075` every time it appears:

```text
My memorial number: ____________________
```

Look for a receipt that says what Graver saved. It should report the number of
new or previously known memorials and confirm that Graver kept a dated observation.

Find a Grave changes over time. Memorial `1075` may eventually be unavailable. If
the search returns no result, stop here or repeat the quickstart later with a memorial
number you already know. Keep `--max-results 1` so the search remains small.

This search saves only the summary details returned by the search page. It does
not mean that Graver opened the full memorial page. It also does not mean that the
website's statements are correct.

## 5. Add and inspect the person

**On your computer**

The commands below use `1075`. If you searched for a different memorial, replace
`1075` with your memorial number before running each command.

Run:

```shell
graver work queue
graver work list --limit 10
graver work next
graver work show 1075
```

Look for:

- a message saying how many people were added to the work list;
- memorial number `1075` in the list; and
- the expected person's name and cemetery in the displayed details.

The displayed status should be `Unprocessed [unprocessed]`. This means that the
person is on your work list, but Graver has not recorded this item as started. The
acquisition level should be `summary`, meaning Graver has saved search-result details
but has not yet opened the full memorial page.

The [research-state guide](research-states.md) explains the other human-readable
statuses and the exact labels shown beside them.

## 6. Approve one full-page lookup

Approving the lookup and performing it are separate steps.

### Record your approval

**On your computer**

Run this as one line:

```shell
graver work mark 1075 --status ready_for_full_scrape --note "Approved during the quickstart"
```

Then inspect the person again:

```shell
graver work show 1075
```

Look for `Approved for enrichment [ready_for_full_scrape]`. This status means that
you approved a later full-page lookup for this one memorial. Recording the approval
did not contact Find a Grave and did not approve any other person.

### Perform the approved lookup

**Contacts Find a Grave**

Run:

```shell
graver work enrich 1075
```

Graver opens only the approved memorial. It does not open relatives' memorials or
process other people in the work list.

Look for a receipt describing what Graver saved from the full memorial page. The
receipt may report:

- details that appeared for the first time;
- details whose displayed values differ from the earlier search result;
- details that appeared earlier but were not saved from the later page;
- displayed values that agree; and
- relationship links displayed by Find a Grave.

Interpret the receipt carefully:

- Graver keeps the earlier and later observations. A later value does not erase
  or automatically replace an earlier value.
- Matching values show agreement between the saved observations. They are not
  automatically independent support for the claim.
- A missing later value does not tell you whether Find a Grave omitted it, Graver
  did not collect or save it, or it was not examined.
- A relationship displayed by Find a Grave is a provider claim. It does not prove
  identity or kinship.
- The receipt explains what Graver saved. It does not decide which claim is true.

If the live request fails, stop rather than repeatedly retrying. The approval and
earlier search result remain in your research file. Inspect them safely with
`graver work show 1075 --history`, then try the live request later.

## 7. Review the saved result

**On your computer**

Run:

```shell
graver work show 1075
graver work show 1075 --history
```

Look for:

- the expected person's name and cemetery;
- `Enrichment complete [full_scrape_complete]`;
- an acquisition level of `full`; and
- both the earlier search observation and the later full-page observation in the
  saved history.

Here, `full` has a narrow meaning: Graver opened the full memorial page and saved
the supported fields it found there. It does not mean that research is complete.
It also does not mean that every field had a value or that Graver saved the entire
page, biography text, images, contributor details, or every displayed item.

Optional details such as plot, coordinates, biography presence, and birth or death
places may be absent. An absent optional detail does not by itself mean that the
lookup failed. The
[acquisition-scope guide](acquisition-scope.md) explains exactly which categories
Graver saves and what remains outside its scope.

## 8. Stop and return later

Graver saves the work list, statuses, current memorial details, dated observations,
and notes in `tutorial.db`. You may close the terminal at any time.

Later, run:

```shell
graver use --show
graver work next
graver work list --limit 10
graver work show 1075
```

If `graver use --show` displays the practice file, you are ready to continue. If
another research file is selected, use the complete location you copied earlier.
Put it inside quotation marks, as in this macOS example:

```shell
graver use "/Users/your-name/Documents/graver-tutorial/tutorial.db"
```

On Windows, the same command may look like:

```shell
graver use "C:\Users\your-name\Documents\graver-tutorial\tutorial.db"
```

Replace the example with the complete location Graver displayed on your computer.
Quotation marks keep a location containing spaces together.

## 9. Finish or clean up

Keeping `tutorial.db` for later practice is safe and is the simplest choice.

If another research file was selected before the quickstart, restore it with
`graver use`, followed by the complete location you recorded in step 2. Put the
location inside quotation marks. Confirm the restored selection with:

```shell
graver use --show
```

If no research file was selected before the quickstart and you do not want Graver
to keep using the practice file, run:

```shell
graver use --clear
```

This clears Graver's saved selection. It does not delete or change `tutorial.db`.

To remove the practice file, first restore or clear the selection as described
above. Then open the folder shown in the complete file location and move only
`tutorial.db` to the Trash or Recycle Bin. Do not delete the whole folder if it
contains anything else.

## When Graver contacts Find a Grave

Only `graver search` and `graver work enrich` contact Find a Grave in this
quickstart. Every other step stays on your computer.

Find a Grave may be slow, unavailable, or may refuse an automated request. The site
may display a verification page or block the request. You do not need to change
Graver's settings when this happens. Stop and try again later rather than repeatedly
retrying. A website failure does not necessarily mean that Graver or your research
file is broken.

## Troubleshooting

| What you see | Safe next step |
| --- | --- |
| `graver: command not found` or “`graver` is not recognized” | Return to the [installation guide for researchers](first-time-setup.md), complete the command-path step, close the terminal, open it again, and run `graver --version`. |
| `tutorial.db` already exists | Graver will not overwrite it. If it is an earlier practice file, select it with `graver use tutorial.db`. Otherwise choose another name, such as `tutorial-2.db`, and use that name throughout the quickstart. |
| No database is selected | Run `graver use` followed by the complete location of `tutorial.db` in quotation marks, then confirm with `graver use --show`. |
| Graver cannot find or use the database | Check that the complete location and filename exactly match what you copied. Graver will not quietly choose another file. |
| Graver says the database needs an upgrade | Stop. Do not continue this quickstart with that file. Read the [database-upgrade guide](database-upgrades.md) before deciding whether to make a backup copy and upgrade it. |
| The search returns no memorial | Stop or try later with a memorial number you already know. Keep `--max-results 1`. Do not run rapid repeated searches. |
| Find a Grave shows a verification page, blocks access, or times out | Stop and try later. You may still use the commands marked **On your computer** to inspect saved work. |
| `work next` shows no person | Run `graver work list --limit 10`. If the list is empty, confirm that the search saved a memorial, then run `graver work queue`. |
| Graver refuses the full-page lookup | Run `graver work show` followed by your memorial number. If you intend to approve that memorial, repeat step 6 before running `graver work enrich` followed by the same number. |
| The full-page lookup succeeds but some details are absent | A successful full-page lookup may still leave optional details blank. Graver does not invent missing facts. |
| Anything else fails | Stop and copy the complete error message. Also record the result of `graver --version`, the selected research file from `graver use --show`, and whether the failed step was marked **On your computer** or **Contacts Find a Grave**. Do not publish private genealogy data. |

For more command detail, run `graver --help`, `graver COMMAND --help`, or a more
specific command such as `graver work show --help`.

Software developers who need Graver's machine-readable output can use
`graver work show 1075 --json` and the [command-line JSON contract](cli-json.md).
