import socket
from types import SimpleNamespace

import pytest
import requests
from pytest_socket import SocketBlockedError

from graver.api import Driver
from graver.transport import (
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT,
    RequestsTransport,
    TransportAccessBlocked,
    TransportConnectionError,
    TransportError,
    TransportRateLimited,
    TransportResponse,
    TransportResponseTooLarge,
    TransportTimeout,
)


def test_ordinary_suite_denies_live_socket_access() -> None:
    """An unmocked HTTP request fails before opening a network connection."""
    with pytest.warns(UserWarning, match="tried to use socket.socket"):
        with pytest.raises(SocketBlockedError):
            socket.socket()


def _response(status_code=200, text="ok", headers=None, url="https://example.test"):
    return TransportResponse(
        status_code=status_code,
        reason="OK" if status_code == 200 else "Error",
        headers=headers or {},
        url=url,
        content=text.encode(),
        text=text,
        history=(),
        request_url=url,
    )


class RecordingTransport:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return next(self.responses)


def test_default_driver_uses_requests_transport():
    driver = Driver()

    try:
        assert isinstance(driver.transport, RequestsTransport)
        assert type(driver.transport.session) is requests.Session
        assert driver.transport.session.headers["User-Agent"].startswith("graver/")
        assert "Mozilla" not in driver.transport.session.headers["User-Agent"]
    finally:
        driver.close()


def test_requests_transport_always_applies_explicit_timeout():
    session = SimpleNamespace(headers={})
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response._content = b"ok"
        response.request = requests.Request("GET", url).prepare()
        return response

    session.get = get
    transport = RequestsTransport(session=session, timeout=(1.5, 7.0))

    transport.get("https://example.test", timeout=None)

    assert calls == [("https://example.test", {"timeout": (1.5, 7.0), "stream": True})]


class StreamingResponse:
    def __init__(self, chunks, headers=None):
        self.status_code = 200
        self.reason = "OK"
        self.headers = headers or {}
        self.url = "https://example.test/large"
        self.request = SimpleNamespace(url=self.url)
        self.history = ()
        self._chunks = chunks
        self.closed = False

    def iter_content(self, chunk_size):
        assert chunk_size > 0
        yield from self._chunks

    def close(self):
        self.closed = True


def test_transport_rejects_declared_oversize_before_reading_body():
    response = StreamingResponse(
        [b"must not be read"], headers={"Content-Length": "11"}
    )
    session = SimpleNamespace(headers={}, get=lambda *args, **kwargs: response)

    with pytest.raises(TransportResponseTooLarge, match="10-byte safety limit"):
        RequestsTransport(session=session, max_response_bytes=10).get(response.url)

    assert response.closed


def test_transport_rejects_streamed_oversize_without_declared_length():
    response = StreamingResponse([b"123456", b"78901"])
    session = SimpleNamespace(headers={}, get=lambda *args, **kwargs: response)

    with pytest.raises(TransportResponseTooLarge, match="10-byte safety limit"):
        RequestsTransport(session=session, max_response_bytes=10).get(response.url)

    assert response.closed


def test_transport_accepts_response_exactly_at_limit():
    response = StreamingResponse([b"12345", b"", b"67890"])
    session = SimpleNamespace(headers={}, get=lambda *args, **kwargs: response)

    result = RequestsTransport(session=session, max_response_bytes=10).get(response.url)

    assert result.content == b"1234567890"
    assert result.text == "1234567890"
    assert response.closed


def test_transport_ignores_malformed_declared_length_and_measures_body():
    response = StreamingResponse([b"small"], headers={"CONTENT-LENGTH": "unknown"})
    session = SimpleNamespace(headers={}, get=lambda *args, **kwargs: response)

    result = RequestsTransport(session=session, max_response_bytes=10).get(response.url)

    assert result.content == b"small"


def test_transport_bounds_lightweight_preloaded_response_double():
    response = SimpleNamespace(
        status_code=200,
        reason="OK",
        headers={},
        url="https://example.test/double",
        request=SimpleNamespace(url="https://example.test/double"),
        history=(),
        content=b"12345678901",
        text="12345678901",
    )
    session = SimpleNamespace(headers={}, get=lambda *args, **kwargs: response)

    with pytest.raises(TransportResponseTooLarge, match="10-byte safety limit"):
        RequestsTransport(session=session, max_response_bytes=10).get(response.url)


def test_transport_accepts_lightweight_preloaded_response_double():
    response = SimpleNamespace(
        status_code=200,
        reason="OK",
        headers={},
        url="https://example.test/double",
        request=SimpleNamespace(url="https://example.test/double"),
        history=(),
        content=b"small",
        text="fixture text",
    )
    session = SimpleNamespace(headers={}, get=lambda *args, **kwargs: response)

    result = RequestsTransport(session=session, max_response_bytes=10).get(response.url)

    assert result.content == b"small"
    assert result.text == "fixture text"


def test_default_response_limit_is_finite_and_positive():
    assert DEFAULT_MAX_RESPONSE_BYTES == 8 * 1024 * 1024


def test_nonpositive_response_limit_is_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        RequestsTransport(session=SimpleNamespace(headers={}), max_response_bytes=0)


def test_driver_accepts_small_injected_transport():
    transport = RecordingTransport([_response()])

    response = Driver(transport=transport).get(
        "https://example.test", params={"memorial": 1}
    )

    assert response.text == "ok"
    assert transport.calls == [("https://example.test", {"params": {"memorial": 1}})]


def test_requests_transport_preserves_cookies_and_redirect_history(requests_mock):
    session = requests.Session()
    session.cookies.set("existing", "cookie", domain="example.test")
    requests_mock.get(
        "https://example.test/start",
        status_code=302,
        headers={"Location": "https://example.test/final", "Set-Cookie": "key=value"},
    )
    requests_mock.get("https://example.test/final", text="finished")

    response = RequestsTransport(session=session).get("https://example.test/start")

    assert response.text == "finished"
    assert response.url == "https://example.test/final"
    assert [item.status_code for item in response.history] == [302]
    assert requests_mock.request_history[0].headers["Cookie"] == "existing=cookie"


@pytest.mark.parametrize(
    "exception, expected",
    [
        (requests.ConnectTimeout("slow"), TransportTimeout),
        (requests.ConnectionError("offline"), TransportConnectionError),
        (requests.RequestException("request failed"), TransportError),
    ],
)
def test_requests_transport_maps_third_party_failures(exception, expected):
    session = SimpleNamespace(
        headers={},
        get=lambda *args, **kwargs: (_ for _ in ()).throw(exception),
    )

    with pytest.raises(expected):
        RequestsTransport(session=session).get("https://example.test")


@pytest.mark.parametrize(
    "response",
    [
        _response(status_code=403),
        _response(text="<div id='cf-chl-widget'>Checking your browser</div>"),
        _response(text="<title>Just a moment...</title><form id='challenge-form'>"),
    ],
)
def test_driver_fails_closed_on_access_denial_or_challenge(response):
    transport = RecordingTransport([response])

    with pytest.raises(TransportAccessBlocked, match="will not attempt to bypass"):
        Driver(transport=transport).get("https://example.test")

    assert len(transport.calls) == 1


def test_driver_stops_after_repeated_rate_limit(monkeypatch):
    transport = RecordingTransport(
        [_response(status_code=429), _response(status_code=429)]
    )
    sleeps = []
    monkeypatch.setattr("graver.api.sleep", sleeps.append)

    with pytest.raises(TransportRateLimited, match="human review"):
        Driver(transport=transport, max_retries=5, retry_ms=10).get(
            "https://example.test"
        )

    assert sleeps == [0.02]
    assert len(transport.calls) == 2


def test_default_timeout_is_finite_connect_and_read_pair():
    assert len(DEFAULT_TIMEOUT) == 2
    assert all(value > 0 for value in DEFAULT_TIMEOUT)


def test_http_failure_uses_graver_owned_error():
    response = _response(status_code=500)

    with pytest.raises(TransportError) as raised:
        response.raise_for_status()

    assert raised.type.__module__ == "graver.transport"


def test_successful_response_does_not_raise():
    _response().raise_for_status()
