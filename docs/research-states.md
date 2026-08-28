# Research states and network activity

graver keeps research workflow separate from network acquisition. Changing a
research state records an offline decision in the selected database; it does not
contact Find a Grave. Only an explicit acquisition command, such as `search` or
`work enrich`, makes a live request.

Human-facing output uses readable labels while retaining the stable machine values
shown below for commands, scripts, and API clients.

| Human label | Machine value | Meaning | What it permits | Network consequence |
| --- | --- | --- | --- | --- |
| Unprocessed | `unprocessed` | The person is queued, but research has not started. | Review the person or begin research. | Offline; does not approve retrieval. |
| Research in progress | `researching` | A researcher is actively reviewing the person. | Continue review and record the next decision. | Offline; does not approve retrieval. |
| Approved for enrichment | `ready_for_full_scrape` | A researcher has approved one later full-page retrieval for this memorial. | A separate `graver work enrich MEMORIAL_ID` command may retrieve this one memorial. | Setting the state is offline; `work enrich` is the live action. |
| Enrichment complete | `full_scrape_complete` | Selected supported fields from a full memorial page have been retained as a dated observation. | Review the retained observation and acquisition history. | The state itself is offline and does not make another request. |
| Ready for review | `ready_for_review` | The current research is ready for a researcher's review. | Review the work and record the resulting decision. | Offline; does not approve retrieval. |
| Research complete | `completed` | The researcher considers the current workflow task complete. This state does not by itself establish identity, kinship, factual accuracy, or satisfaction of a proof standard. | No action is required unless research is reopened. | Offline; does not approve retrieval. |
| Unable to resolve | `unable_to_resolve` | The available evidence does not currently resolve the research question. | Preserve the unresolved result or resume when new evidence is available. | Offline; does not approve retrieval. |

`Approved for enrichment` is permission, not proof or confidence. It says only
that the researcher intentionally authorized the later retrieval of one named
memorial. It does not establish identity, validate facts, or authorize related or
queued memorials.

The `full_scrape_complete` machine value is retained for compatibility. In
researcher language, “full” means that graver observed the full memorial page and
retained its supported structured fields; it does not mean that graver archived
the entire page. See the [acquisition-scope guide](acquisition-scope.md) for the
precise capture boundary.

Use `graver work show MEMORIAL_ID` to see the current state and its next action.
Use `graver work mark MEMORIAL_ID --status MACHINE_VALUE` to record a state change.
Both commands are offline.
