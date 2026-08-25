from datetime import datetime, timezone

import pytest

from graver._live_contract import (
    CANARY_URL,
    ProbeAcquisition,
    acquire_canary,
    run_live_contract,
)
from graver.api import Memorial, MemorialParseException
from graver.transport import (
    TransportAccessBlocked,
    TransportResponse,
)


def _response(status=200, content=b"fixture"):
    return TransportResponse(
        status_code=status,
        reason="OK",
        headers={"Content-Type": "text/html"},
        url=CANARY_URL,
        content=content,
        text=content.decode(),
        history=(),
        request_url=CANARY_URL,
    )


def _memorial(**changes):
    values = {
        "memorial_id": 1075,
        "findagrave_url": CANARY_URL,
        "prefix": None,
        "name": "George Washington",
        "suffix": None,
        "nickname": None,
        "maiden_name": None,
        "famous": True,
        "veteran": True,
        "birth": "22 Feb 1732",
        "death": "14 Dec 1799",
        "memorial_type": "Burial",
        "cemetery_id": 641532,
        "burial_place": "Mount Vernon Estate",
        "plot": None,
        "original_name": None,
        "birth_place": None,
        "death_place": None,
        "coords": None,
        "has_bio": True,
    }
    values.update(changes)
    return Memorial(**values)


def _at_noon():
    return datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def test_compatible_result_is_sanitized_and_versioned():
    result = run_live_contract(
        lambda: ProbeAcquisition(_memorial(), _response(content=b"private page"), 1),
        now=_at_noon,
    )

    assert result.compatible
    assert result.classification == "compatible"
    assert result.request_count == 1
    assert result.schema_version == 1
    assert result.checked_at == "2026-08-24T12:00:00+00:00"
    assert result.response_sha256
    assert "private page" not in str(result.to_dict())


@pytest.mark.parametrize(
    "memorial, classification",
    [
        (_memorial(cemetery_id=None, burial_place=None), "schema_changed"),
        (_memorial(name="George Washington, revised"), "canary_changed"),
    ],
)
def test_semantic_failures_are_distinguished(memorial, classification):
    result = run_live_contract(
        lambda: ProbeAcquisition(memorial, _response(), 1), now=_at_noon
    )

    assert result.classification == classification
    assert not result.compatible


def test_access_block_is_classified_without_sensitive_response_data():
    error = MemorialParseException("provider denied access")
    error.__cause__ = TransportAccessBlocked("challenge details")

    result = run_live_contract(lambda: (_ for _ in ()).throw(error), now=_at_noon)

    assert result.classification == "access_blocked"
    assert result.status_code is None
    assert result.response_sha256 is None


def test_acquisition_disables_retries_and_enforces_one_request(monkeypatch):
    class FailingTransport:
        calls = 0

        def get(self, url, **kwargs):
            self.calls += 1
            return _response(status=500)

    transport = FailingTransport()

    with pytest.raises(MemorialParseException):
        acquire_canary(transport)

    assert transport.calls == 1
