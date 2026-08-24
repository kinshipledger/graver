"""Contract tests for the synchronous typed workspace composition."""

import dataclasses

import pytest

from graver import MemorialSummary
from graver.application import (
    DatabaseInspectionError,
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
