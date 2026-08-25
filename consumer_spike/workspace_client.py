"""Exercise the documented workspace API from an installed graver wheel."""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

from graver.application import (
    AcquisitionReceipt,
    ApplicationError,
    CancellationRequested,
    CancellationToken,
    DisplayedRelationshipInput,
    MemorialDetailInput,
    MemorialSummaryBatch,
    MemorialSummaryInput,
    MemorialSummarySearchRequest,
    ProgressEvent,
    ResearchEnrichmentRequest,
    ResearchEnrichmentResult,
    ResearchQueueRequest,
    ResearchQueueResult,
    ResearchTaskDetail,
    ResearchTaskQuery,
    ResearchTaskRecord,
    ResearchTaskSummary,
    ResearchTaskUpdate,
    StaleResearchTask,
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
    summary = MemorialSummaryInput(
        memorial_id=1075,
        findagrave_url="https://www.findagrave.com/memorial/1075/george-washington",
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
    )
    events = []
    receipt = workspace.acquisition.search(
        MemorialSummarySearchRequest(memorial_id=1075, max_results=1),
        acquire=lambda _command: MemorialSummaryBatch((summary,), "fixture:1075"),
        progress=events.append,
    )
    assert isinstance(receipt, AcquisitionReceipt)
    assert all(isinstance(event, ProgressEvent) for event in events)
    assert receipt.memorial_ids == (1075,)
    assert receipt.memorials_created == 1
    assert receipt.observations_appended == 1
    assert [event.stage for event in events] == [
        "validation",
        "acquisition",
        "persistence",
        "completed",
    ]
    queued = workspace.work.queue(ResearchQueueRequest(priority=3))
    assert isinstance(queued, ResearchQueueResult)
    assert (queued.created, queued.existing) == (1, 0)
    tasks = workspace.work.list(ResearchTaskQuery(limit=5))
    assert len(tasks) == 1
    assert isinstance(tasks[0], ResearchTaskSummary)
    assert tasks[0].memorial_id == 1075
    detail = workspace.work.show(1075)
    assert isinstance(detail, ResearchTaskDetail)
    assert isinstance(detail.task, ResearchTaskRecord)
    researching = workspace.work.update(
        ResearchTaskUpdate(
            memorial_id=1075,
            expected_version=detail.task.version,
            status="researching",
            owner="installed-wheel consumer",
            review_note="Checking the public application contract.",
        )
    )
    assert researching.status == "researching"
    try:
        workspace.work.update(
            ResearchTaskUpdate(
                memorial_id=1075,
                expected_version=detail.task.version,
                status="ready_for_full_scrape",
            )
        )
    except StaleResearchTask as error:
        assert error.expected_version == detail.task.version
        assert error.actual_version == researching.version
    else:
        raise AssertionError("A stale installed-wheel update was accepted")
    approved = workspace.work.update(
        ResearchTaskUpdate(
            memorial_id=1075,
            expected_version=researching.version,
            status="ready_for_full_scrape",
        )
    )
    full = MemorialDetailInput(
        memorial_id=1075,
        findagrave_url=summary.findagrave_url,
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
        plot="Washington Family Tomb",
        original_name="",
        birth_place="Westmoreland County, Virginia",
        death_place="Mount Vernon, Virginia",
        coords="38.7077,-77.0861",
        has_bio=True,
        displayed_relationships=(
            DisplayedRelationshipInput(
                displayed_group="Spouse",
                memorial_id=100,
                url="https://www.findagrave.com/memorial/100/martha-washington",
                name="Martha Washington",
                life_text="1731–1802",
            ),
        ),
    )
    token = CancellationToken()

    def acquire_then_cancel(_url: str) -> MemorialDetailInput:
        token.cancel()
        return full

    try:
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075),
            acquire=acquire_then_cancel,
            cancellation=token,
        )
    except CancellationRequested as error:
        assert error.stage == "persistence"
    else:
        raise AssertionError("Cancellation after retrieval did not protect persistence")
    assert workspace.work.show(1075).task.version == approved.version
    enrichment_events = []
    enriched = workspace.acquisition.enrich(
        ResearchEnrichmentRequest(1075),
        acquire=lambda _url: full,
        progress=enrichment_events.append,
    )
    assert enriched.memorial_id == 1075
    assert isinstance(enriched, ResearchEnrichmentResult)
    assert enriched.status == "full_scrape_complete"
    assert [event.stage for event in enrichment_events] == [
        "validation",
        "acquisition",
        "persistence",
        "completed",
    ]
    completed = workspace.work.show(1075)
    assert completed.task.status == "full_scrape_complete"
    assert len(completed.observations) == 2
    assert completed.grave["birth_place"] == "Westmoreland County, Virginia"
    assert (
        completed.observations[-1]["payload"][
            "findagrave_displayed_relationship_links"
        ][0]["name"]
        == "Martha Washington"
    )
    try:
        full.name = "Changed"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Public acquisition input must be immutable")
    try:
        workspace.work.update(ResearchTaskUpdate(999, 1, status="researching"))
    except WorkItemNotFound as error:
        assert isinstance(error, ApplicationError)
        assert error.memorial_id == 999
        assert error.code == "resource_not_found"
        assert error.summary == "Work item 999 does not exist"
        assert dict(error.context) == {"memorial_id": 999}
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
