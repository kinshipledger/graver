"""Contract tests for neutral stored-record reads and foreground retrieval."""

from collections.abc import Mapping
from dataclasses import replace

import pytest

from graver.application import (
    CancellationRequested,
    CancellationToken,
    MemorialDetailInput,
    MemorialFetchAliasBlocked,
    MemorialFetchFailed,
    MemorialFetchRedirected,
    MemorialFetchRedirectInvalid,
    MemorialFetchRequest,
    MemorialObservationRecord,
    MemorialRecordDetail,
    MemorialRecordInputError,
    MemorialRecordQuery,
    MemorialRecordSummary,
    MemorialRedirectInput,
    MemorialSummaryBatch,
    MemorialSummaryInput,
    MemorialSummarySearchRequest,
    ResearchQueueRequest,
    create_database,
    open_workspace,
)

MEMORIAL_ID = 410001


def summary() -> MemorialSummaryInput:
    return MemorialSummaryInput(
        memorial_id=MEMORIAL_ID,
        findagrave_url=("https://www.findagrave.com/memorial/410001/ada-example"),
        prefix=None,
        name="Ada Example",
        suffix=None,
        nickname=None,
        maiden_name="Sample",
        famous=False,
        veteran=False,
        birth="1881",
        death="1952",
        memorial_type="Burial",
        cemetery_id=77001,
        burial_place="Example Cemetery, Sample County, Arkansas",
        plot="Row 4",
    )


def detail(name: str = "Ada M. Example") -> MemorialDetailInput:
    return MemorialDetailInput(
        memorial_id=MEMORIAL_ID,
        findagrave_url=summary().findagrave_url,
        prefix=None,
        name=name,
        suffix=None,
        nickname=None,
        maiden_name="Sample",
        famous=False,
        veteran=False,
        birth="1881",
        death="1953",
        memorial_type="Burial",
        cemetery_id=77001,
        burial_place="Example Cemetery, Sample County, Arkansas",
        plot="Row 5",
        original_name="Ada May Example",
        birth_place="Sample County, Arkansas",
        death_place="Sample County, Arkansas",
        coords="36.0000,-92.0000",
        has_bio=True,
        date_added="2026-09-19",
    )


def make_workspace(tmp_path, *, two_versions: bool = False):
    database = create_database(str(tmp_path / "records.db"))
    workspace = open_workspace(database)
    request = MemorialSummarySearchRequest(memorial_id=MEMORIAL_ID, max_results=1)
    first = summary()
    workspace.acquisition.search(
        request,
        acquire=lambda _request: MemorialSummaryBatch((first,), "fixture:first"),
    )
    if two_versions:
        second = replace(first, name="Ada M. Example", death="1953", plot="Row 5")
        workspace.acquisition.search(
            request,
            acquire=lambda _request: MemorialSummaryBatch((second,), "fixture:second"),
        )
    return workspace


def test_records_list_and_show_without_research_task(tmp_path) -> None:
    workspace = make_workspace(tmp_path, two_versions=True)

    assert workspace.work.list() == ()
    records = workspace.records.list()
    shown = workspace.records.show(MEMORIAL_ID)

    assert records == (
        MemorialRecordSummary(
            memorial_id=MEMORIAL_ID,
            name="Ada M. Example",
            birth="1881",
            death="1953",
            cemetery_id=77001,
            burial_place="Example Cemetery, Sample County, Arkansas",
            detail_level="summary",
            findagrave_url=summary().findagrave_url,
            saved_version_count=2,
            last_observed_at=records[0].last_observed_at,
        ),
    )
    assert isinstance(shown, MemorialRecordDetail)
    assert shown.record.name == "Ada M. Example"
    assert shown.record.plot == "Row 5"
    assert len(shown.observations) == 2
    assert all(
        isinstance(observation, MemorialObservationRecord)
        for observation in shown.observations
    )
    assert [item.snapshot.name for item in shown.observations] == [
        "Ada Example",
        "Ada M. Example",
    ]
    assert not isinstance(shown.record, Mapping)
    assert not isinstance(shown.observations[0], Mapping)
    assert shown.alias.path == (MEMORIAL_ID,)


def test_record_queries_validate_simple_bounds() -> None:
    with pytest.raises(MemorialRecordInputError):
        MemorialRecordQuery(cemetery_id=0)
    with pytest.raises(MemorialRecordInputError):
        MemorialRecordQuery(limit=0)
    with pytest.raises(MemorialRecordInputError):
        MemorialFetchRequest(0)


def test_foreground_fetch_saves_without_changing_task_state(tmp_path) -> None:
    workspace = make_workspace(tmp_path)
    workspace.work.queue(ResearchQueueRequest())
    task_before = workspace.work.show(MEMORIAL_ID).task
    events = []

    result = workspace.acquisition.fetch(
        MemorialFetchRequest(MEMORIAL_ID),
        acquire=lambda _url: detail(),
        progress=events.append,
    )

    task_after = workspace.work.show(MEMORIAL_ID).task
    shown = workspace.records.show(MEMORIAL_ID)
    assert result.outcome == "saved"
    assert result.observation_id == shown.observations[-1].observation_id
    assert shown.record.detail_level == "full"
    assert shown.record.original_name == "Ada May Example"
    assert len(shown.observations) == 2
    assert task_after.status == task_before.status == "unprocessed"
    assert task_after.version == task_before.version
    assert [event.stage for event in events] == [
        "validation",
        "acquisition",
        "persistence",
        "completed",
    ]


def test_foreground_fetch_cancels_before_acquisition_and_before_save(tmp_path) -> None:
    workspace = make_workspace(tmp_path)
    initial_count = len(workspace.records.show(MEMORIAL_ID).observations)
    before = CancellationToken()
    before.cancel()
    calls = []

    with pytest.raises(CancellationRequested) as cancelled:
        workspace.acquisition.fetch(
            MemorialFetchRequest(MEMORIAL_ID),
            cancellation=before,
            acquire=lambda url: calls.append(url),
        )

    assert cancelled.value.stage == "validation"
    assert calls == []
    assert len(workspace.records.show(MEMORIAL_ID).observations) == initial_count

    after = CancellationToken()

    def acquire(_url):
        after.cancel()
        return detail()

    with pytest.raises(CancellationRequested) as cancelled:
        workspace.acquisition.fetch(
            MemorialFetchRequest(MEMORIAL_ID),
            cancellation=after,
            acquire=acquire,
        )

    assert cancelled.value.stage == "persistence"
    assert len(workspace.records.show(MEMORIAL_ID).observations) == initial_count


def test_foreground_fetch_records_failure_without_creating_task(tmp_path) -> None:
    workspace = make_workspace(tmp_path)

    def fail(_url):
        raise RuntimeError("fixture failure")

    with pytest.raises(MemorialFetchFailed) as failure:
        workspace.acquisition.fetch(MemorialFetchRequest(MEMORIAL_ID), acquire=fail)

    assert failure.value.error_type == "RuntimeError"
    shown = workspace.records.show(MEMORIAL_ID)
    assert workspace.work.list() == ()
    assert len(shown.observations) == 2
    recorded = shown.observations[-1]
    assert recorded.fetch_outcome == "failure"
    assert recorded.snapshot is None
    assert recorded.error_type == "RuntimeError"
    assert recorded.error_message == "fixture failure"


def test_foreground_fetch_records_redirect_and_blocks_old_identifier(tmp_path) -> None:
    workspace = make_workspace(tmp_path)
    redirect = MemorialRedirectInput(
        source_url=summary().findagrave_url,
        target_url="https://www.findagrave.com/memorial/410002/ada-example",
    )

    with pytest.raises(MemorialFetchRedirected) as moved:
        workspace.acquisition.fetch(
            MemorialFetchRequest(MEMORIAL_ID), acquire=lambda _url: redirect
        )

    assert moved.value.target_memorial_id == 410002
    shown = workspace.records.show(MEMORIAL_ID)
    assert shown.alias.path == (MEMORIAL_ID, 410002)
    assert shown.observations[-1].target_memorial_id == 410002
    assert workspace.work.list() == ()

    with pytest.raises(MemorialFetchAliasBlocked):
        workspace.acquisition.fetch(
            MemorialFetchRequest(MEMORIAL_ID), acquire=lambda _url: detail()
        )


def test_foreground_fetch_rejects_mismatched_redirect(tmp_path) -> None:
    workspace = make_workspace(tmp_path)
    redirect = MemorialRedirectInput(
        source_url="https://www.findagrave.com/memorial/999/wrong-source",
        target_url="https://www.findagrave.com/memorial/410002/ada-example",
    )

    with pytest.raises(MemorialFetchRedirectInvalid):
        workspace.acquisition.fetch(
            MemorialFetchRequest(MEMORIAL_ID), acquire=lambda _url: redirect
        )

    shown = workspace.records.show(MEMORIAL_ID)
    assert shown.alias.path == (MEMORIAL_ID,)
    assert shown.observations[-1].fetch_outcome == "failure"
    assert shown.observations[-1].target_memorial_id is None
