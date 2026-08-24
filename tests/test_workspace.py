"""Contract tests for the synchronous typed workspace composition."""

import concurrent.futures
import dataclasses
import sqlite3

import pytest

from graver import Memorial, MemorialMergedException, MemorialSummary
from graver.application import (
    CancellationRequested,
    CancellationToken,
    DatabaseBusy,
    DatabaseInspectionError,
    DatabaseOperationError,
    EnrichmentRedirectInvalid,
    MemorialSummarySearchRequest,
    ResearchEnrichmentRequest,
    ResearchQueueRequest,
    ResearchService,
    ResearchTaskQuery,
    ResearchTaskUpdate,
    StaleResearchTask,
    SummaryAcquisitionService,
    WorkItemNotFound,
    create_database,
    open_workspace,
)
from tests.test import Test


def test_workspace_opens_explicit_current_database_without_global_state(
    tmp_path,
) -> None:
    database = create_database(str(tmp_path / "workspace.db"))

    workspace = open_workspace(database)

    assert workspace.path == database
    assert workspace.database.path == database
    assert workspace.database.inspect().current is True
    assert workspace.work.list(ResearchTaskQuery(limit=5)) == ()
    assert workspace.work.queue(ResearchQueueRequest()).created == 0
    assert callable(workspace.work.update)
    with pytest.raises(WorkItemNotFound) as missing:
        workspace.work.show(1075)
    assert missing.value.memorial_id == 1075
    with pytest.raises(WorkItemNotFound) as missing_update:
        workspace.work.update(ResearchTaskUpdate(1075, 1, status="researching"))
    assert missing_update.value.memorial_id == 1075
    with pytest.raises(WorkItemNotFound) as missing_enrichment:
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075), acquire=lambda _url: None
        )
    assert missing_enrichment.value.memorial_id == 1075


def test_workspace_is_lightweight_immutable_and_connection_free(tmp_path) -> None:
    database = create_database(str(tmp_path / "workspace.db"))
    workspace = open_workspace(database)

    assert dataclasses.is_dataclass(workspace)
    assert not hasattr(workspace, "connection")
    assert not hasattr(workspace.database, "connection")
    assert not hasattr(workspace.work, "connection")
    with pytest.raises(dataclasses.FrozenInstanceError):
        workspace.path = tmp_path / "other.db"


def test_workspace_operations_open_thread_local_database_connections(tmp_path) -> None:
    """One workspace may be called from workers without sharing SQLite handles."""
    database = create_database(str(tmp_path / "workspace.db"))
    workspace = open_workspace(database)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        pages = tuple(
            executor.map(
                lambda _: workspace.work.list(ResearchTaskQuery(limit=5)), range(12)
            )
        )

    assert pages == ((),) * 12


@pytest.mark.parametrize(
    ("sqlite_message", "expected_type", "expected_code"),
    [
        ("database is locked", DatabaseBusy, "database_busy"),
        (
            "database disk image is malformed",
            DatabaseOperationError,
            "database_operation_failed",
        ),
    ],
)
def test_workspace_translates_sqlite_failures_without_leaking_storage_details(
    tmp_path, monkeypatch, sqlite_message, expected_type, expected_code
) -> None:
    """Application clients receive stable safe errors instead of SQLite text."""
    database = create_database(str(tmp_path / "workspace.db"))
    workspace = open_workspace(database)

    def fail_query(_service, _query):
        raise sqlite3.OperationalError(sqlite_message)

    monkeypatch.setattr(ResearchService, "query_tasks", fail_query)

    with pytest.raises(expected_type) as failure:
        workspace.work.list()

    assert failure.value.code == expected_code
    assert failure.value.context == {
        "database": str(database),
        "operation": "list research work",
    }
    assert sqlite_message not in failure.value.summary
    assert sqlite_message not in str(failure.value)
    assert isinstance(failure.value.__cause__, sqlite3.OperationalError)


@pytest.mark.parametrize(
    ("service_method", "invoke", "operation"),
    [
        ("get_task", lambda workspace: workspace.work.show(1075), "show research work"),
        (
            "queue_research",
            lambda workspace: workspace.work.queue(ResearchQueueRequest()),
            "queue research work",
        ),
        (
            "apply_task_update",
            lambda workspace: workspace.work.update(
                ResearchTaskUpdate(1075, 1, status="researching")
            ),
            "update research work",
        ),
        (
            "enrich_memorial",
            lambda workspace: workspace.acquisition.enrich(
                ResearchEnrichmentRequest(1075)
            ),
            "enrich memorial",
        ),
    ],
)
def test_each_workspace_area_translates_locked_database_failures(
    tmp_path, monkeypatch, service_method, invoke, operation
) -> None:
    """Every workspace service area exposes the same safe busy contract."""
    database = create_database(str(tmp_path / "workspace.db"))
    workspace = open_workspace(database)

    def fail_operation(_service, *_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(ResearchService, service_method, fail_operation)

    with pytest.raises(DatabaseBusy) as failure:
        invoke(workspace)

    assert failure.value.context == {
        "database": str(database),
        "operation": operation,
    }


def test_workspace_summary_search_translates_locked_database_failure(
    tmp_path, monkeypatch
) -> None:
    """Summary acquisition uses the same safe workspace database contract."""
    database = create_database(str(tmp_path / "workspace.db"))
    workspace = open_workspace(database)

    def fail_search(_service, *_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(SummaryAcquisitionService, "search", fail_search)

    with pytest.raises(DatabaseBusy) as failure:
        workspace.acquisition.search(MemorialSummarySearchRequest())

    assert failure.value.context == {
        "database": str(database),
        "operation": "search memorial summaries",
    }


def test_workspace_refuses_missing_or_legacy_database_without_creation(
    tmp_path,
) -> None:
    missing = tmp_path / "missing.db"

    with pytest.raises(DatabaseInspectionError):
        open_workspace(missing)

    assert not missing.exists()


def test_workspace_updates_by_revision_and_rejects_stale_clients(
    tmp_path, monkeypatch
) -> None:
    database = create_database(str(tmp_path / "workspace.db"))
    monkeypatch.setenv("DATABASE_NAME", str(database))
    values = Test.load_memorial_from_json("george-washington")
    MemorialSummary.from_dict(values).save()
    workspace = open_workspace(database)
    workspace.work.queue(ResearchQueueRequest())
    first_view = workspace.work.show(1075).task

    updated = workspace.work.update(
        ResearchTaskUpdate(1075, first_view.version, status="researching")
    )

    assert updated.status == "researching"
    assert updated.version == first_view.version + 1
    with pytest.raises(StaleResearchTask) as stale:
        workspace.work.update(
            ResearchTaskUpdate(1075, first_view.version, status="researching")
        )
    assert stale.value.memorial_id == 1075
    assert stale.value.expected_version == first_view.version
    assert stale.value.actual_version == updated.version
    assert workspace.work.show(1075).task.version == updated.version


def test_workspace_enrichment_reports_progress_and_persists_after_safe_checks(
    tmp_path, monkeypatch
) -> None:
    database = create_database(str(tmp_path / "workspace.db"))
    monkeypatch.setenv("DATABASE_NAME", str(database))
    values = Test.load_memorial_from_json("george-washington")
    MemorialSummary.from_dict(values).save()
    workspace = open_workspace(database)
    workspace.work.queue(ResearchQueueRequest())
    task = workspace.work.show(1075).task
    workspace.work.update(
        ResearchTaskUpdate(1075, task.version, status="ready_for_full_scrape")
    )
    events = []

    result = workspace.acquisition.enrich(
        ResearchEnrichmentRequest(1075),
        progress=events.append,
        acquire=lambda _url: Memorial.from_dict(values),
    )

    assert result.status == "full_scrape_complete"
    assert [(event.stage, event.completed, event.total) for event in events] == [
        ("validation", 0, 1),
        ("acquisition", 0, 1),
        ("persistence", 0, 1),
        ("completed", 1, 1),
    ]


def test_workspace_enrichment_rejects_mismatched_redirect_source(
    tmp_path, monkeypatch
) -> None:
    """A redirect that does not describe the requested memorial fails safely."""
    database = create_database(str(tmp_path / "workspace.db"))
    monkeypatch.setenv("DATABASE_NAME", str(database))
    values = Test.load_memorial_from_json("george-washington")
    MemorialSummary.from_dict(values).save()
    workspace = open_workspace(database)
    workspace.work.queue(ResearchQueueRequest())
    task = workspace.work.show(1075).task
    workspace.work.update(
        ResearchTaskUpdate(1075, task.version, status="ready_for_full_scrape")
    )
    redirect = MemorialMergedException(
        "mismatched redirect",
        "https://www.findagrave.com/memorial/999/source",
        "https://www.findagrave.com/memorial/1000/target",
    )

    with pytest.raises(EnrichmentRedirectInvalid):
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075),
            acquire=lambda _url: (_ for _ in ()).throw(redirect),
        )

    shown = workspace.work.show(1075)
    assert shown.task.status == "ready_for_full_scrape"
    assert shown.observations[-1]["fetch_outcome"] == "failure"


def test_workspace_enrichment_cancels_before_network_or_persistence(
    tmp_path, monkeypatch
) -> None:
    database = create_database(str(tmp_path / "workspace.db"))
    monkeypatch.setenv("DATABASE_NAME", str(database))
    values = Test.load_memorial_from_json("george-washington")
    MemorialSummary.from_dict(values).save()
    workspace = open_workspace(database)
    workspace.work.queue(ResearchQueueRequest())
    task = workspace.work.show(1075).task
    ready = workspace.work.update(
        ResearchTaskUpdate(1075, task.version, status="ready_for_full_scrape")
    )
    token = CancellationToken()
    token.cancel()
    calls = []

    with pytest.raises(CancellationRequested) as cancelled:
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075),
            cancellation=token,
            acquire=lambda url: calls.append(url),
        )

    assert cancelled.value.stage == "validation"
    assert calls == []
    assert workspace.work.show(1075).task.version == ready.version


def test_workspace_enrichment_cancels_after_retrieval_before_transaction(
    tmp_path, monkeypatch
) -> None:
    database = create_database(str(tmp_path / "workspace.db"))
    monkeypatch.setenv("DATABASE_NAME", str(database))
    values = Test.load_memorial_from_json("george-washington")
    MemorialSummary.from_dict(values).save()
    workspace = open_workspace(database)
    workspace.work.queue(ResearchQueueRequest())
    task = workspace.work.show(1075).task
    ready = workspace.work.update(
        ResearchTaskUpdate(1075, task.version, status="ready_for_full_scrape")
    )
    token = CancellationToken()

    def acquire(_url):
        token.cancel()
        return Memorial.from_dict(values)

    with pytest.raises(CancellationRequested) as cancelled:
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075),
            cancellation=token,
            acquire=acquire,
        )

    assert cancelled.value.stage == "persistence"
    shown = workspace.work.show(1075)
    assert shown.task.version == ready.version
    assert all(
        observation["acquisition_level"] != "full" for observation in shown.observations
    )


def test_workspace_enrichment_propagates_acquirer_cancellation_without_failure_record(
    tmp_path, monkeypatch
) -> None:
    database = create_database(str(tmp_path / "workspace.db"))
    monkeypatch.setenv("DATABASE_NAME", str(database))
    values = Test.load_memorial_from_json("george-washington")
    MemorialSummary.from_dict(values).save()
    workspace = open_workspace(database)
    workspace.work.queue(ResearchQueueRequest())
    task = workspace.work.show(1075).task
    ready = workspace.work.update(
        ResearchTaskUpdate(1075, task.version, status="ready_for_full_scrape")
    )

    def cancel_acquisition(_url):
        raise CancellationRequested("enrich_memorial", "acquisition")

    with pytest.raises(CancellationRequested):
        workspace.acquisition.enrich(
            ResearchEnrichmentRequest(1075), acquire=cancel_acquisition
        )

    shown = workspace.work.show(1075)
    assert shown.task.version == ready.version
    assert all(
        observation["fetch_outcome"] != "failure" for observation in shown.observations
    )
