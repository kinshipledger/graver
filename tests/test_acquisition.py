"""Contract tests for typed memorial-summary acquisition receipts."""

import dataclasses
import sqlite3

import pytest

import graver.acquisition as acquisition
from graver import MemorialSummary
from graver._sqlite import connect_database
from graver.application import (
    AcquisitionFieldChange,
    CancellationRequested,
    CancellationToken,
    DatabaseBusy,
    MemorialSearchFailed,
    MemorialSummaryBatch,
    MemorialSummaryInput,
    MemorialSummarySearchRequest,
    ResearchInputError,
    create_database,
    open_workspace,
)
from tests.test import Test


def _george_summary() -> MemorialSummaryInput:
    values = Test.load_memorial_from_json("george-washington")
    return MemorialSummaryInput.from_mapping(
        MemorialSummary.from_dict(values).to_dict()
    )


def test_summary_search_receipt_distinguishes_new_existing_and_changed_values(
    tmp_path,
) -> None:
    """Receipts explain persistence while immutable observations accumulate."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)
    first = _george_summary()
    command = MemorialSummarySearchRequest(memorial_id=1075, max_results=1)
    events = []

    created = workspace.acquisition.search(
        command,
        acquire=lambda _command: MemorialSummaryBatch((first,), "fixture:first"),
        progress=events.append,
    )
    changed_input = dataclasses.replace(first, name="George Washington, revised")
    changed = workspace.acquisition.search(
        command,
        acquire=lambda _command: MemorialSummaryBatch(
            (changed_input,), "fixture:second"
        ),
    )

    assert created.source == "fixture:first"
    assert created.memorial_ids == (1075,)
    assert created.observations_appended == 1
    assert created.memorials_created == 1
    assert created.memorials_existing == 0
    assert created.changed_memorials == 0
    assert created.changes == ()
    assert [event.stage for event in events] == [
        "validation",
        "acquisition",
        "persistence",
        "completed",
    ]
    assert changed.source == "fixture:second"
    assert changed.memorials_created == 0
    assert changed.memorials_existing == 1
    assert changed.changed_memorials == 1
    assert changed.changes == (
        AcquisitionFieldChange(1075, "name", first.name, changed_input.name),
    )
    with connect_database(database) as connection:
        current_name = connection.execute(
            "SELECT name FROM graves WHERE memorial_id = 1075"
        ).fetchone()[0]
        observations = connection.execute(
            """SELECT payload_json FROM memorial_observations
               WHERE memorial_id = 1075 ORDER BY observation_id"""
        ).fetchall()
    assert current_name == changed_input.name
    assert len(observations) == 2
    assert first.name in observations[0][0]
    assert changed_input.name in observations[1][0]


def test_summary_search_reports_progress_and_honors_safe_cancellation(tmp_path) -> None:
    """Cancellation after retrieval prevents all summary persistence."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)
    token = CancellationToken()
    events = []

    def acquire(_command):
        token.cancel()
        return MemorialSummaryBatch((_george_summary(),), "fixture:cancel")

    with pytest.raises(CancellationRequested) as cancelled:
        workspace.acquisition.search(
            MemorialSummarySearchRequest(memorial_id=1075),
            acquire=acquire,
            progress=events.append,
            cancellation=token,
        )

    assert cancelled.value.stage == "persistence"
    assert [event.stage for event in events] == ["validation", "acquisition"]
    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM graves").fetchone()[0] == 0


def test_summary_search_rejects_duplicate_batch_before_persistence(tmp_path) -> None:
    """Malformed adapter batches cannot create partial observations."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)
    summary = _george_summary()

    with pytest.raises(ResearchInputError):
        workspace.acquisition.search(
            MemorialSummarySearchRequest(),
            acquire=lambda _command: MemorialSummaryBatch((summary, summary)),
        )

    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM graves").fetchone()[0] == 0


def test_summary_search_rolls_back_the_complete_batch_on_persistence_failure(
    tmp_path, monkeypatch
) -> None:
    """One failed summary cannot leave an earlier batch item committed."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)
    first = _george_summary()
    second = dataclasses.replace(
        first,
        memorial_id=1076,
        findagrave_url="https://www.findagrave.com/memorial/1076/fixture",
    )
    save = acquisition.legacy_api._save_grave
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fixture persistence failure")
        return save(*args, **kwargs)

    monkeypatch.setattr(acquisition.legacy_api, "_save_grave", fail_second)

    with pytest.raises(MemorialSearchFailed):
        workspace.acquisition.search(
            MemorialSummarySearchRequest(),
            acquire=lambda _command: MemorialSummaryBatch((first, second)),
        )

    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM graves").fetchone()[0] == 0
        assert (
            connection.execute("SELECT COUNT(*) FROM memorial_observations").fetchone()[
                0
            ]
            == 0
        )


def test_summary_search_preserves_sqlite_failures_for_workspace_translation(
    tmp_path, monkeypatch
) -> None:
    """Database failures remain distinct for the workspace error boundary."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)

    def fail_persistence(_self, _retrieved):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(
        acquisition.SummaryAcquisitionService, "_persist", fail_persistence
    )

    with pytest.raises(DatabaseBusy) as failure:
        workspace.acquisition.search(
            MemorialSummarySearchRequest(memorial_id=1075),
            acquire=lambda _command: MemorialSummaryBatch((_george_summary(),)),
        )
    assert failure.value.code == "database_busy"


def test_summary_search_wraps_adapter_failures_without_transport_types(
    tmp_path,
) -> None:
    """Clients receive a stable acquisition failure from injected adapters."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)

    def fail(_command):
        raise RuntimeError("provider details")

    with pytest.raises(MemorialSearchFailed) as failure:
        workspace.acquisition.search(MemorialSummarySearchRequest(), acquire=fail)

    assert failure.value.code == "acquisition_failed"
    assert failure.value.context == {
        "operation": "search_memorial_summaries",
        "error_type": "RuntimeError",
    }
    assert "provider details" not in failure.value.summary


def test_summary_search_preserves_adapter_cancellation(tmp_path) -> None:
    """An adapter cancellation remains distinct from acquisition failure."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)

    def cancel(_command):
        raise CancellationRequested("search_memorial_summaries", "acquisition")

    with pytest.raises(CancellationRequested):
        workspace.acquisition.search(MemorialSummarySearchRequest(), acquire=cancel)


def test_summary_search_rejects_untyped_adapter_values(tmp_path) -> None:
    """An adapter cannot pass arbitrary persistence-shaped objects."""
    database = create_database(str(tmp_path / "research.db"))
    workspace = open_workspace(database)

    with pytest.raises(MemorialSearchFailed):
        workspace.acquisition.search(
            MemorialSummarySearchRequest(),
            acquire=lambda _command: MemorialSummaryBatch((object(),)),
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cemetery_id": 0},
        {"memorial_id": 0},
        {"contributor_id": 0},
        {"max_results": -1},
        {"page": 0},
        {"birth_year_filter": "unsupported"},
        {"death_year_filter": "unsupported"},
        {"order_by": "unsupported"},
        {"date_filter": 2},
        {"photo_filter": "unsupported"},
        {"gps_filter": "unsupported"},
        {"famous": True, "sponsored": False},
        {"cenotaph": True, "monument": False},
        {"exact_name": False, "fuzzy_names": True},
    ],
)
def test_summary_search_request_rejects_invalid_combinations(kwargs) -> None:
    """Domain validation is available to every adapter, not only the CLI."""
    with pytest.raises(ResearchInputError):
        MemorialSummarySearchRequest(**kwargs)
