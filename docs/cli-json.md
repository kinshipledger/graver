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

Hidden pre-1.0 compatibility commands use the same envelope while they remain in
the package, but they are not part of the supported 1.0 command contract.

## Compatibility policy

Within schema version 1, graver may add optional fields to a command's `data` value.
It will not remove or rename documented fields, change their meaning, or change a
documented value type without a new schema version. Consumers should ignore unknown
fields and handle documented optional values.

A future JSON error contract, if introduced, will be additive at the envelope level
or use a new schema version. Human-readable terminal output remains intentionally
outside this machine contract.
