"""Internal synchronous HTTP transport for Graver acquisition.

Third-party client and response types stop at this module.  The application and
parser layers consume only the deliberately small Graver-owned protocol below.
"""

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Mapping, Optional, Protocol, Sequence

import requests


DEFAULT_CONNECT_TIMEOUT_SECONDS = 5.0
DEFAULT_READ_TIMEOUT_SECONDS = 30.0
DEFAULT_TIMEOUT = (
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_READ_TIMEOUT_SECONDS,
)


class TransportError(Exception):
    """A request failed at Graver's transport boundary."""


class TransportTimeout(TransportError):
    """The provider did not respond within Graver's configured timeout."""


class TransportConnectionError(TransportError):
    """Graver could not connect to the provider."""


class TransportAccessBlocked(TransportError):
    """The provider denied or challenged access; Graver will not bypass it."""


class TransportRateLimited(TransportError):
    """The provider repeatedly limited access and requires human review."""


@dataclass(frozen=True)
class TransportResponse:
    """The limited response information used by Graver parsers."""

    status_code: int
    reason: str
    headers: Mapping[str, str]
    url: str
    content: bytes
    text: str
    history: Sequence["TransportResponse"]
    request_url: str

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return
        category = "Client Error" if self.status_code < 500 else "Server Error"
        message = f"{self.status_code} {category}: {self.reason} for url: {self.url}"
        raise TransportError(message)


class HttpTransport(Protocol):
    """Minimal injectable synchronous transport used by current acquisition."""

    def get(self, url: str, **kwargs: Any) -> TransportResponse:
        """Retrieve one URL and return a Graver-owned response."""


class RequestsTransport:
    """Conventional Requests-backed transport with explicit bounded timeouts."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers["User-Agent"] = _user_agent()

    def get(self, url: str, **kwargs: Any) -> TransportResponse:
        request_kwargs = dict(kwargs)
        request_kwargs["timeout"] = self.timeout
        try:
            response = self.session.get(url, **request_kwargs)
        except requests.Timeout as ex:
            raise TransportTimeout(f"Request timed out for {url}") from ex
        except requests.ConnectionError as ex:
            raise TransportConnectionError(f"Could not connect to {url}") from ex
        except requests.RequestException as ex:
            raise TransportError(f"Request failed for {url}: {ex}") from ex
        return _response_from_requests(response)

    def close(self) -> None:
        self.session.close()


def _response_from_requests(response: requests.Response) -> TransportResponse:
    history = tuple(
        _response_from_requests(item) for item in getattr(response, "history", ())
    )
    response_url = getattr(response, "url", "")
    request = getattr(response, "request", None)
    request_url = getattr(request, "url", response_url)
    content = response.content
    return TransportResponse(
        status_code=response.status_code,
        reason=getattr(response, "reason", "") or "",
        headers=dict(getattr(response, "headers", {})),
        url=response_url or request_url,
        content=content,
        text=getattr(response, "text", content.decode(errors="replace")),
        history=history,
        request_url=request_url,
    )


def _user_agent() -> str:
    try:
        package_version = version("graver")
    except PackageNotFoundError:  # pragma: no cover - source tree without install
        package_version = "development"
    return f"graver/{package_version}"
