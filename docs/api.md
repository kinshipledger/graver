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

Application code should import from `graver.application`:

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
            status="in_review",
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

`ResearchService.enrich_memorial()` performs one explicitly approved memorial
operation. Its optional acquisition callable exists for injected adapters and offline
tests. Network-capable clients remain responsible for the project
[access policy](access-policy.md), progress presentation, and cancellation UX.

## Required checks

Public application changes must pass:

```shell
make lint
make typecheck
make doccheck
uv run pytest
```

Mypy is deliberately scoped to the application-facing modules. Google-style
docstring checks require useful public module, class, function, and method contracts;
constructor and magic-method docstrings are not duplicated when their class already
documents the contract.
