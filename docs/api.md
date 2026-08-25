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
consumer spike validate this design. The package root deliberately re-exports no
application symbols; clients must choose the documented `graver.application`
boundary explicitly.

Pre-1.0 code that imported parser or persistence objects directly from `graver`
must migrate to the typed application API. For example, replace
`from graver import queue_memorials` with `open_workspace(...).work.queue(...)`.
Parser, SQL, transport, and compatibility functions remain internal even when a
module-level implementation still exists.

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

The workspace façade currently contains database inspection; typed work-queue list,
show, idempotent queue, and concurrency-safe update operations; and
researcher-directed summary search and single-record enrichment. The supported
lower-level `EvidenceService` supplies the reviewed offline evidence contract;
workspace evidence composition remains deferred until its client ergonomics are
ready. Clients should not import internal packet, transport, persistence, or CLI
modules to fill that temporary gap.

Expected lookup failures are translated to `WorkItemNotFound`, which carries the
requested memorial identifier without exposing SQL detail or a legacy exception
type. Presentation adapters decide how to display that typed failure.

## Error contract

All supported application failures inherit from `ApplicationError`. Adapters may
rely on three presentation-neutral fields:

- `code`: a stable machine-readable classification for routing;
- `summary`: a safe, whitespace-normalized explanation for people; and
- `context`: immutable structured values safe for logs and interface state.

Clients should catch the most specific documented exception when behavior differs,
or `ApplicationError` at their outer presentation boundary. They must not parse
exception wording. Current classifications include `invalid_request`,
`resource_not_found`, `invalid_state`, `stale_data`, `operation_cancelled`,
`database_busy`, other database lifecycle and operation failures, and acquisition
failure or block outcomes. New classifications may be added without changing the
meaning of existing ones.

The workspace translates SQLite busy/locked conditions to `DatabaseBusy`. Other
unexpected SQLite operation failures become `DatabaseOperationError`. Both report
the database and attempted operation without exposing raw SQL or SQLite diagnostics;
the original exception remains available through Python exception chaining for
developer diagnostics. Database creation, inspection, and upgrade retain their more
specific lifecycle exceptions.

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

The installed-wheel consumer exercises an offline discovery and comparison through
`EvidenceService` after obtaining the subject identifier from a typed task detail.
It confirms that candidate agreement affects review ordering only and that no
identity conclusion appears unless a researcher explicitly records one.

## Acquisition boundary

`workspace.acquisition.search()` accepts a typed `MemorialSummarySearchRequest` and
returns an immutable `AcquisitionReceipt`. The receipt distinguishes newly created
memorial entities from existing memorials receiving another observation, reports
the number of dated snapshots appended, and gives field-level before/after values
when a new summary changes the current displayed representation. It does not expose
SQL rows, declare source statements correct, queue research tasks, or imply that a
full memorial page was examined.

```python
from graver.application import MemorialSummarySearchRequest

receipt = workspace.acquisition.search(
    MemorialSummarySearchRequest(memorial_id=1075, max_results=1)
)
print(receipt.observations_appended, receipt.memorials_created)
```

Tests and authorized adapters may inject a callable returning a
`MemorialSummaryBatch` of `MemorialSummaryInput` values. Persistence remains owned
by graver and occurs only after acquisition and cancellation checks succeed. A
batch containing duplicate memorial IDs is rejected before mutation.

`workspace.acquisition.enrich()` performs one explicitly approved memorial operation.
Its optional acquisition callable returns a `MemorialDetailInput`, including any
`DisplayedRelationshipInput` values observed on the provider page. Those displayed
links remain source observations and never become proven kinship. This typed seam
supports offline consumer tests and authorized adapters without exposing the legacy
parser model. Network-capable clients remain responsible for the project
[access policy](access-policy.md).

```python
from graver.application import MemorialDetailInput, ResearchEnrichmentRequest

result = workspace.acquisition.enrich(
    ResearchEnrichmentRequest(memorial_id=1075),
    acquire=lambda url: MemorialDetailInput(
        memorial_id=1075,
        findagrave_url=url,
        prefix="",
        name="George Washington",
        suffix="",
        nickname="",
        maiden_name="",
        famous=True,
        veteran=True,
        birth="22 Feb 1732",
        death="14 Dec 1799",
        memorial_type="Burial",
        cemetery_id=641532,
        burial_place="Mount Vernon Estate",
        plot="",
        original_name="",
        birth_place="Westmoreland County, Virginia",
        death_place="Mount Vernon, Virginia",
        coords="",
        has_bio=True,
    ),
)
```

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

## Threading and transaction ownership

A workspace may be retained by an application and invoked from different worker
threads, but a single operation runs synchronously in its calling thread. Every
operation opens, uses, and closes its own SQLite connection in that thread. graver
never returns a connection to clients or moves one between threads. A GUI should run
potentially blocking work in a worker thread and marshal results, progress events,
and typed errors back through its toolkit adapter.

Transactions belong to one service operation. Cancellation is honored only at the
documented safe boundaries outside a transaction; optimistic versions protect task
updates from stale views. A `DatabaseBusy` result is retryable only after the client
or researcher decides how and when to retry—graver does not silently loop behind the
interface.

## Required checks

Public application changes must pass:

```shell
make lint
make typecheck
make doccheck
uv run pytest
```

CI also builds the wheel, verifies both `graver` and `python -m graver`, installs
the artifact as an isolated uv tool, and runs `consumer_spike/workspace_client.py`.
The spike uses only documented imports to create, open, inspect, query, queue, update,
and enrich work in a disposable database. It injects summary and full-record
acquisition; verifies progress, cancellation before persistence, optimistic
concurrency, immutable inputs and errors, typed results, and retained observations;
and makes no provider request. It is a GUI-readiness contract test, not a production
client.

Mypy is deliberately scoped to the application-facing modules. Google-style
docstring checks require useful public module, class, function, and method contracts;
constructor and magic-method docstrings are not duplicated when their class already
documents the contract.
