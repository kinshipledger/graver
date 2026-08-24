"""Contract tests for the synchronous typed workspace composition."""

import dataclasses

import pytest

from graver.application import (
    DatabaseInspectionError,
    ResearchQueueRequest,
    ResearchTaskQuery,
    WorkItemNotFound,
    create_database,
    open_workspace,
)


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
    assert not hasattr(workspace.work, "update")
    with pytest.raises(WorkItemNotFound) as missing:
        workspace.work.show(1075)
    assert missing.value.memorial_id == 1075


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
