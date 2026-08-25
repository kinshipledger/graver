"""Internal implementation of the explicitly invoked live provider canary."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .api import Driver, Memorial, MemorialParseException
from .transport import (
    HttpTransport,
    RequestsTransport,
    TransportAccessBlocked,
    TransportConnectionError,
    TransportResponse,
    TransportTimeout,
)

CANARY_URL = "https://www.findagrave.com/memorial/1075/george-washington"
CANARY_MEMORIAL_ID = 1075
CANARY_NAME = "George Washington"
CANARY_CEMETERY_ID = 641532
CANARY_TIMEOUT = (5.0, 15.0)


@dataclass(frozen=True)
class ProbeAcquisition:
    """Parsed memorial and sanitized metadata from one acquisition attempt."""

    memorial: Memorial
    response: TransportResponse
    request_count: int


@dataclass(frozen=True)
class LiveContractResult:
    """Sanitized, machine-readable outcome of one live compatibility probe."""

    schema_version: int
    checked_at: str
    classification: str
    target_url: str
    request_count: int
    status_code: int | None
    final_url: str | None
    redirect_count: int
    content_type: str | None
    response_sha256: str | None
    memorial_id: int | None
    name: str | None
    cemetery_id: int | None
    burial_place: str | None
    missing_invariants: tuple[str, ...]
    message: str

    @property
    def compatible(self) -> bool:
        """Return whether the provider still satisfies the minimum contract."""

        return self.classification == "compatible"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation without response content."""

        return asdict(self)


class _SingleRequestTransport:
    """Enforce one top-level request even if a caller is misconfigured."""

    def __init__(self, delegate: HttpTransport) -> None:
        self.delegate = delegate
        self.calls = 0
        self.response: TransportResponse | None = None

    def get(self, url: str, **kwargs: Any) -> TransportResponse:
        if self.calls:
            raise RuntimeError("The live canary permits exactly one request attempt.")
        self.calls += 1
        self.response = self.delegate.get(url, **kwargs)
        return self.response

    def close(self) -> None:
        close = getattr(self.delegate, "close", None)
        if close is not None:
            close()


def acquire_canary(
    transport: HttpTransport | None = None,
) -> ProbeAcquisition:
    """Retrieve and parse the canary once, with retries disabled."""

    guarded = _SingleRequestTransport(
        transport or RequestsTransport(timeout=CANARY_TIMEOUT)
    )
    driver = Driver(transport=guarded, max_retries=0, timeout=CANARY_TIMEOUT)
    try:
        memorial = Memorial.parse(CANARY_URL, driver=driver)
        if guarded.response is None:  # pragma: no cover - defensive invariant
            raise RuntimeError("The canary parser made no request.")
        return ProbeAcquisition(memorial, guarded.response, guarded.calls)
    finally:
        driver.close()


def run_live_contract(
    acquire: Callable[[], ProbeAcquisition] = acquire_canary,
    *,
    now: Callable[[], datetime] | None = None,
) -> LiveContractResult:
    """Run the canary and classify its result without exposing page content."""

    checked_at = (now or (lambda: datetime.now(timezone.utc)))().isoformat()
    try:
        acquired = acquire()
    except MemorialParseException as exc:
        cause = exc.__cause__
        if isinstance(cause, TransportAccessBlocked):
            classification = "access_blocked"
        elif isinstance(cause, (TransportTimeout, TransportConnectionError)):
            classification = "site_unavailable"
        else:
            classification = "schema_changed"
        return _failure(checked_at, classification, str(exc))
    except (TransportTimeout, TransportConnectionError) as exc:
        return _failure(checked_at, "site_unavailable", str(exc))
    except Exception as exc:  # noqa: BLE001 - maintenance boundary must classify
        return _failure(checked_at, "probe_error", str(exc))

    memorial = acquired.memorial
    response = acquired.response
    missing = tuple(
        label
        for label, value in (
            ("memorial_id", memorial.memorial_id),
            ("name", memorial.name),
            (
                "cemetery_or_burial_linkage",
                memorial.cemetery_id or memorial.burial_place,
            ),
        )
        if not value
    )
    classification = "compatible"
    message = "The live memorial satisfies graver's minimum parsing contract."
    if missing:
        classification = "schema_changed"
        message = "The response parsed incompletely; inspect the named invariants."
    elif (
        memorial.memorial_id != CANARY_MEMORIAL_ID
        or memorial.name != CANARY_NAME
        or memorial.cemetery_id != CANARY_CEMETERY_ID
    ):
        classification = "canary_changed"
        message = "The page parsed, but stable canary identity values changed."

    return LiveContractResult(
        schema_version=1,
        checked_at=checked_at,
        classification=classification,
        target_url=CANARY_URL,
        request_count=acquired.request_count,
        status_code=response.status_code,
        final_url=response.url,
        redirect_count=len(response.history),
        content_type=response.headers.get("Content-Type"),
        response_sha256=hashlib.sha256(response.content).hexdigest(),
        memorial_id=memorial.memorial_id,
        name=memorial.name,
        cemetery_id=memorial.cemetery_id,
        burial_place=memorial.burial_place,
        missing_invariants=missing,
        message=message,
    )


def _failure(checked_at: str, classification: str, message: str) -> LiveContractResult:
    return LiveContractResult(
        schema_version=1,
        checked_at=checked_at,
        classification=classification,
        target_url=CANARY_URL,
        request_count=1,
        status_code=None,
        final_url=None,
        redirect_count=0,
        content_type=None,
        response_sha256=None,
        memorial_id=None,
        name=None,
        cemetery_id=None,
        burial_place=None,
        missing_invariants=(),
        message=message,
    )
