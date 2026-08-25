# Database upgrades and recovery

graver research databases can contain work that is difficult or impossible to
recreate. Database upgrades are therefore explicit, backed up, transactional, and
separate from ordinary research commands.

This guide applies to databases created by older graver development versions,
including the early `0.1.0` database shape and summary-only databases populated by
cemetery searches. It does not turn an unrelated SQLite file into a graver database.

## Before upgrading

1. Stop other graver commands or applications using the database.
2. Confirm the exact database path. `graver use --show` reports the saved default;
   an explicit `--db` may still select a different database for one command.
3. Preserve any separate backup you already rely on. The automatic upgrade backup
   is an additional safeguard, not a substitute for your normal backup practice.
4. Make sure the database directory is writable and has enough free space for a
   second database file.

Do not test an upgrade on the only copy of irreplaceable research. When practical,
practice on a copy first.

## Run the upgrade

```shell
graver admin database upgrade /absolute/path/to/research.db
```

The command inspects the file before writing. It recognizes supported legacy,
unversioned, and older versioned graver schemas. It refuses missing files,
directories, symbolic links, unrelated or malformed SQLite files, unknown schema
shapes, and databases created by a newer graver schema.

If the database is already current, the command reports a no-op and creates no
backup. Otherwise it creates a verified sibling backup before beginning. For the
current schema version 5, the backup name is:

```text
research.db.pre-upgrade-v5.backup
```

graver will not overwrite an existing backup with that name. Preserve or rename an
older backup deliberately before trying again.

## What the upgrade preserves

Supported migrations preserve existing graves, cemetery data, acquisition
observations, redirects, research tasks, human-owned notes, task state, and recorded
timestamps. Later schemas add research subjects, immutable task and subject events,
offline evidence structures, source observations, and task revision numbers.

Migration-created subject associations and events are labeled as mechanical
organization. They do not assert that two records identify the same person. graver
does not invent source observations, acquisition dates, detail levels, candidates,
relationships, confidence, assessments, or identity conclusions when older data
cannot support them.

## Successful completion

After applying every ordered migration in one transaction, graver validates the
current schema, SQLite integrity, and foreign keys. Only then does the upgrade
complete. The backup remains beside the database; graver does not delete it
automatically.

Keep that backup until you have opened the upgraded database, inspected important
records, and completed enough ordinary work to be confident in the result. Store or
remove old backups according to your own research-retention policy.

## If an upgrade fails

Stop and preserve both files. Do not repeatedly rerun the command or overwrite the
original database.

- A failure before migration leaves the source database unchanged.
- A migration failure rolls back its transaction. The verified backup remains.
- A final validation failure leaves the backup in place and reports its path.
- graver never restores a backup automatically over research data.

Record the complete error, the graver version (`graver --version`), the operating
system, the source classification shown by the command, and both file paths. Report
the problem through the project's support or security channel as appropriate. Do
not upload a research database publicly; it may contain personal or sensitive data.

Restoration is a deliberate manual recovery operation and is not currently a graver
command. Before replacing any file, close all applications using it and make another
copy of both the failed database and verified backup. If you are uncertain, ask for
help before moving or replacing either file.

## After upgrading from pre-1.0 graver

Database migration does not restore removed command names or option spellings. See
the [pre-1.0 command-line migration](cli-migration.md) for those replacements and
the [researcher tutorial](tutorial.md) for the supported workflow. Machine-readable
command output uses the [versioned JSON contract](cli-json.md).
