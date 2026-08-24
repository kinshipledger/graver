"""Contract tests for the synchronous typed workspace composition."""

import dataclasses

import pytest

from graver import Memorial, MemorialSummary
from graver.application import (
    CancellationRequested,
    CancellationToken,
    DatabaseInspectionError,
    ResearchEnrichmentRequest,
    ResearchQueueRequest,
    ResearchTaskQuery,
    ResearchTaskUpdate,
    StaleResearchTask,
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
