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
DEFAULT_MAX_RESPONSE_BYTES = 8 * 1024 * 1024
RESPONSE_CHUNK_BYTES = 64 * 1024
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


class TransportResponseTooLarge(TransportError):
    """The provider response exceeded Graver's configured safety limit."""


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
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    ) -> None:
        if max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes
        self.session.headers["User-Agent"] = _user_agent()

    def get(self, url: str, **kwargs: Any) -> TransportResponse:
        request_kwargs = dict(kwargs)
        request_kwargs["timeout"] = self.timeout
        request_kwargs["stream"] = True
        try:
            response = self.session.get(url, **request_kwargs)
        except requests.Timeout as ex:
            raise TransportTimeout(f"Request timed out for {url}") from ex
        except requests.ConnectionError as ex:
            raise TransportConnectionError(f"Could not connect to {url}") from ex
        except requests.RequestException as ex:
            raise TransportError(f"Request failed for {url}: {ex}") from ex
        return _response_from_requests(response, self.max_response_bytes)

    def close(self) -> None:
        self.session.close()


def _response_from_requests(
    response: requests.Response, max_response_bytes: int
) -> TransportResponse:
    response_url = getattr(response, "url", "")
    request = getattr(response, "request", None)
    request_url = getattr(request, "url", response_url)
    url = response_url or request_url
    headers = dict(getattr(response, "headers", {}))
    try:
        _reject_declared_oversize(headers, max_response_bytes, url)
        content = _read_bounded_content(response, max_response_bytes, url)
        history = tuple(
            _response_from_requests(item, max_response_bytes)
            for item in getattr(response, "history", ())
        )
        return TransportResponse(
            status_code=response.status_code,
            reason=getattr(response, "reason", "") or "",
            headers=headers,
            url=url,
            content=content,
            text=_response_text(response, content),
            history=history,
            request_url=request_url,
        )
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()


def _reject_declared_oversize(
    headers: Mapping[str, str], max_response_bytes: int, url: str
) -> None:
    declared = next(
        (
            value
            for name, value in headers.items()
            if name.casefold() == "content-length"
        ),
        None,
    )
    try:
        declared_bytes = int(declared) if declared is not None else None
    except (TypeError, ValueError):
        declared_bytes = None
    if declared_bytes is not None and declared_bytes > max_response_bytes:
        raise TransportResponseTooLarge(
            f"Response from {url} exceeds the {max_response_bytes}-byte safety limit"
        )


def _read_bounded_content(
    response: requests.Response, max_response_bytes: int, url: str
) -> bytes:
    preloaded = getattr(response, "_content", None)
    if getattr(response, "raw", None) is None and isinstance(preloaded, bytes):
        if len(preloaded) > max_response_bytes:
            raise TransportResponseTooLarge(
                f"Response from {url} exceeds the "
                f"{max_response_bytes}-byte safety limit"
            )
        return preloaded

    iter_content = getattr(response, "iter_content", None)
    if callable(iter_content):
        chunks = []
        total = 0
        for chunk in iter_content(chunk_size=RESPONSE_CHUNK_BYTES):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_response_bytes:
                raise TransportResponseTooLarge(
                    f"Response from {url} exceeds the "
                    f"{max_response_bytes}-byte safety limit"
                )
            chunks.append(chunk)
        return b"".join(chunks)

    content = response.content
    if len(content) > max_response_bytes:
        raise TransportResponseTooLarge(
            f"Response from {url} exceeds the {max_response_bytes}-byte safety limit"
        )
    return content


def _response_text(response: requests.Response, content: bytes) -> str:
    if isinstance(response, requests.Response):
        response._content = content
        response._content_consumed = True
    text = getattr(response, "text", None)
    return text if isinstance(text, str) else content.decode(errors="replace")


def _user_agent() -> str:
    try:
        package_version = version("graver")
    except PackageNotFoundError:  # pragma: no cover - source tree without install
        package_version = "development"
    return f"graver/{package_version}"
