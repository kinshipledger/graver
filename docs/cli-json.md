# Command-line JSON contract

graver provides versioned JSON for commands that advertise `--json` and for the
specialist alias-recording commands whose result is already machine-readable. This
document defines schema version 1 of that output.

## Envelope

Every successful JSON result is one UTF-8 JSON object followed by a newline:

```json
{
  "command": "work.show",
  "data": {},
  "schema_version": 1
}
```

- `schema_version` identifies the top-level envelope contract. Consumers must
  reject versions they do not support rather than guessing.
- `command` is a stable dotted identifier for the operation that produced the
  result. It is independent of shell spacing and executable invocation.
- `data` contains the command-specific result. Its type may be an object, array,
  or `null`, as documented for that command.

Keys are emitted in deterministic lexical order. Unicode is emitted directly,
timestamps use the stored ISO 8601 representation, and optional values are JSON
`null`. Scripts must parse JSON rather than depend on key order or whitespace.

Schema version 1 defines successful results. Invalid command syntax and operational
failures continue to use a nonzero exit status and a human-readable diagnostic on
standard error; they do not promise a JSON error envelope yet. Successful JSON
commands write no explanatory prose to standard output.

For the 1.0 CLI contract, exit status `1` identifies an operational failure after a
valid invocation, while exit status `2` identifies invalid command usage or input.
The diagnostic wording is not a machine contract. Scripts should branch on the exit
status, parse stdout only after success, and use the typed Python application API
when they require structured failure codes and context.

## Supported command identifiers

| Command | `command` value | `data` |
| --- | --- | --- |
| `graver work list --json` | `work.list` | Array of research-task summaries |
| `graver work next --json` | `work.next` | Complete current record for the selected person |
| `graver work show ID --json` | `work.show` | Complete current record for the requested person |
| `graver work mark ID --json` | `work.mark` | Updated research-task summary |
| `graver work enrich ID --json` | `work.enrich` | Completed one-person enrichment result |
| `graver admin aliases list --json` | `admin.aliases.list` | Array of reviewed redirect mappings |
| `graver admin aliases show ID --json` | `admin.aliases.show` | Redirect resolution and immutable history |
| `graver admin aliases record …` | `admin.aliases.record` | Recorded redirect and history |
| `graver admin aliases retract …` | `admin.aliases.retract` | Retracted redirect and history |

The complete person record currently contains the established `task`, `grave`,
`cemetery`, `observations`, and `alias` projections. These are application-facing
compatibility projections, not direct SQLite rows. Subject UUIDs and private SQL
structures are intentionally absent.

The removed pre-1.0 compatibility commands are not part of this contract. Scripts
must use the documented `work` and `admin aliases` command identifiers.

## Compatibility policy

Within schema version 1, graver may add optional fields to a command's `data` value.
It will not remove or rename documented fields, change their meaning, or change a
documented value type without a new schema version. Consumers should ignore unknown
fields and handle documented optional values.

A JSON error envelope is not required for 1.0. If a demonstrated external CLI
consumer later requires one, it will be additive at the envelope level or use a new
schema version and must cover parser, configuration, database, and application
failures consistently. Human-readable terminal output remains intentionally outside
this machine contract.
