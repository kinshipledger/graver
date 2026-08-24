"""Exercise the documented workspace API from an installed graver wheel."""

from __future__ import annotations

import sys
from pathlib import Path

from graver.application import (
    ApplicationError,
    CancellationRequested,
    CancellationToken,
    ResearchEnrichmentRequest,
    ResearchQueueRequest,
    ResearchTaskQuery,
    ResearchTaskUpdate,
    WorkItemNotFound,
    create_database,
    open_workspace,
)


def main(database: Path) -> None:
    """Create, open, inspect, and query one disposable workspace database."""
    created = create_database(str(database))
    workspace = open_workspace(created)
    assert workspace.database.inspect().current
    assert workspace.work.list(ResearchTaskQuery(limit=5)) == ()
    assert workspace.work.queue(ResearchQueueRequest()).created == 0
    try:
        workspace.work.update(ResearchTaskUpdate(1075, 1, status="researching"))
    except WorkItemNotFound as error:
        assert isinstance(error, ApplicationError)
        assert error.memorial_id == 1075
        assert error.code == "resource_not_found"
        assert error.summary == "Work item 1075 does not exist"
        assert dict(error.context) == {"memorial_id": 1075}
        try:
            error.context["memorial_id"] = 1  # type: ignore[index]
        except TypeError:
            pass
        else:
            raise AssertionError("Application error context must be immutable")
    else:
        raise AssertionError("Missing installed-wheel work item was not reported")
    token = CancellationToken()
    token.cancel()
    try:
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075), cancellation=token
        )
    except CancellationRequested as error:
        assert error.stage == "validation"
        assert error.code == "operation_cancelled"
        assert dict(error.context) == {
            "operation": "enrich_memorial",
            "stage": "validation",
        }
    else:
        raise AssertionError("Cancelled acquisition did not stop before retrieval")
    assert not hasattr(workspace, "connection")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
