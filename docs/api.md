# Developer API guide

`graver.application` is the supported typed import boundary for application clients
during pre-1.0 development. It gives the CLI, future desktop GUI, and other adapters
one domain vocabulary without exposing SQLite connections, SQL rows, Typer, terminal
rendering, parsers, Requests objects, or transport implementations.

The boundary is intentionally synchronous. Each service opens short-lived database
connections for an operation and closes them before returning. Clients supply an
explicit database path; CLI default-database resolution remains a CLI responsibility.

## Stability

The names in `graver.application.__all__` are intentional and contract-tested, but
the project is still pre-1.0. Changes will be documented in release notes, and the
1.0 compatibility contract will be frozen only after the workspace façade and GUI
consumer spike validate this design. The broad imports retained at package root are
legacy compatibility conveniences, not the future façade.

Application code should prefer the synchronous workspace façade from
`graver.application`:

```python
from graver.application import ResearchTaskQuery, open_workspace

workspace = open_workspace("research.db")
inspection = workspace.database.inspect()
tasks = workspace.work.list(ResearchTaskQuery(limit=10))
```

`open_workspace()` requires an explicit, existing current database. It never reads
CLI defaults, creates a missing file, or upgrades an older schema. The workspace is
immutable and holds no SQLite connection; each operation owns a short-lived internal
unit of work.

The façade currently contains database inspection; typed work-queue list, show,
idempotent queue, and concurrency-safe update operations; and researcher-directed
single-record enrichment. Evidence and broader acquisition namespaces will be added
only after their contracts are ready. Clients should not import internal packet,
transport, persistence, or CLI modules to fill those temporary gaps.

Expected lookup failures are translated to `WorkItemNotFound`, which carries the
requested memorial identifier without exposing SQL detail or a legacy exception
type. Presentation adapters decide how to display that typed failure.

Every typed task record carries an integer `version`. Supply that value as
`expected_version` when constructing `ResearchTaskUpdate`; a meaningful successful
update increments it. If another client changed the task first,
`workspace.work.update()` raises `StaleResearchTask` with the expected and actual
versions. Reload the task, show the researcher the intervening state, and let them
decide whether to reapply their edit. A stale request is rejected even when its
requested values happen to match the newer state.

Lower-level typed services remain supported during pre-1.0 development:

```python
from graver.application import (
    ResearchService,
    ResearchTaskQuery,
    ResearchTaskUpdate,
    create_database,
)
```

## Offline database and work-queue example

```python
from graver.application import (
    ResearchService,
    ResearchTaskQuery,
    ResearchTaskUpdate,
    create_database,
)

database = create_database("research.db")
service = ResearchService(str(database))

tasks = service.query_tasks(ResearchTaskQuery(limit=10))
if tasks:
    updated = service.apply_task_update(
        ResearchTaskUpdate(
            memorial_id=tasks[0].memorial_id,
            expected_version=service.get_task(tasks[0].memorial_id).task.version,
            status="researching",
            review_note="Beginning evidence review.",
        )
    )
    print(updated.status)
```

Database creation refuses to overwrite an existing path. Query and update operations
require a current supported schema and never silently migrate an older database.
Use `inspect_database()` and the explicit `upgrade_database()` specialist operation
when building lifecycle tooling.

## Evidence services

`EvidenceService` accepts typed discovery, comparison, assessment, source-observation,
and conclusion inputs. Candidate ordering remains distinct from researcher assessment
and reviewed identity conclusions. Client adapters must not reinterpret ordering as
confidence or silently convert candidate data into accepted facts.

Evidence and research services return graver-owned immutable result objects or raise
graver-owned exceptions. Presentation adapters translate those outcomes into CLI
exit codes, JSON, dialogs, or future GUI state; the services themselves do not emit
terminal or toolkit-specific output.

## Acquisition boundary

`workspace.acquisition.enrich()` performs one explicitly approved memorial operation.
Its optional acquisition callable supports offline consumer tests without requiring
a live provider. Network-capable clients remain responsible for the project
[access policy](access-policy.md).

Long operations accept an optional `ProgressObserver`. It receives immutable
`ProgressEvent` values synchronously in the operation's calling thread; a GUI should
invoke the operation in its worker thread and translate those callbacks into toolkit
signals. Stages are extensible strings, while operation names and count semantics are
part of the documented contract. Observers must return normally and must not perform
domain mutations.

`CancellationToken` is thread-safe and requires no event loop. For enrichment,
cancellation is checked before validation, before retrieval, and after retrieval but
before persistence begins. Once the persistence transaction starts, it is allowed to
complete; a committed operation is never subsequently reported as cancelled.

```python
from graver.application import CancellationToken, ResearchEnrichmentRequest

token = CancellationToken()
result = workspace.acquisition.enrich(
    ResearchEnrichmentRequest(memorial_id=1075),
    progress=lambda event: print(event.stage, event.completed, event.total),
    cancellation=token,
)
```

## Required checks

Public application changes must pass:

```shell
make lint
make typecheck
make doccheck
uv run pytest
```

CI also builds the wheel, installs that artifact in an isolated environment, and
runs `consumer_spike/workspace_client.py`. The spike uses only documented imports to
create, open, inspect, query, queue, and exercise typed update failures in a
disposable database. It is a GUI-readiness contract test, not a production client.

Mypy is deliberately scoped to the application-facing modules. Google-style
docstring checks require useful public module, class, function, and method contracts;
constructor and magic-method docstrings are not duplicated when their class already
documents the contract.
