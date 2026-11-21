"""Client for the Vigicrues service."""

import importlib.metadata
import json
from collections.abc import Mapping
from http import HTTPStatus
from types import TracebackType
from typing import Any, Self

import aiohttp

from ._errors import (
    VigicruesApiError,
    VigicruesConnectionError,
    VigicruesRateLimitError,
    VigicruesResponseError,
)

DEFAULT_BASE_URL = "https://www.vigicrues.gouv.fr"
DEFAULT_TIMEOUT = 30.0

_USER_AGENT = (
    f"vigicrues-client/{importlib.metadata.version('vigicrues-client')}"
    " (+https://github.com/mcartoixa/vigicrues-client)"
)


class VigicruesClient:
    """Asynchronous client for the Vigicrues service.

    Use it as an asynchronous context manager, or call `close` when done:

        async with VigicruesClient() as client:
            ...

    Args:
        session: HTTP session to send the requests with, e.g. one shared by the
            application. The client never closes it. When omitted, the client
            creates its own session on first use, identified by a library
            User-Agent, and closes it with the client.
        base_url: Root URL of the Vigicrues service.
        timeout: Maximum duration of each request, in seconds.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session
        self._owns_session = session is None
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP session if the client created it."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def _get_json(
        self, path: str, params: Mapping[str, str] | None = None
    ) -> object:
        content_type, body = await self._get(path, params)
        if content_type != "application/json":
            raise VigicruesResponseError(
                f"Unexpected content type {content_type!r} for {path}"
            )
        try:
            data: object = json.loads(body)
        except ValueError as error:
            raise VigicruesResponseError(f"Invalid JSON for {path}") from error
        _raise_for_api_error(data)
        return data

    async def _get(
        self, path: str, params: Mapping[str, str] | None = None
    ) -> tuple[str, bytes]:
        """Return the content type and the body of a successful response."""
        try:
            async with self._get_session().get(
                f"{self._base_url}/{path}", params=params, timeout=self._timeout
            ) as response:
                if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                    raise VigicruesRateLimitError(f"Too many requests for {path}")
                if not response.ok:
                    raise VigicruesResponseError(
                        f"HTTP status {response.status} for {path}"
                    )
                return response.content_type, await response.read()
        except (aiohttp.ClientError, TimeoutError) as error:
            raise VigicruesConnectionError(f"Could not get {path}") from error

    def _get_session(self) -> aiohttp.ClientSession:
        # Created on first use: aiohttp expects sessions to be created in a coroutine.
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={"User-Agent": _USER_AGENT})
        return self._session


def _raise_for_api_error(data: object) -> None:
    """Raise the error reported in a response body, if any.

    The service reports errors with HTTP 200, in several shapes:
    - `[{"error_msg": ..., "code": 400}]`
    - `{"error_msg": ..., "code": 400}`
    - `{"Scenario": {...}, "msg_error": ...}`
    - `{"Simul": {...}, "message": ..., "code": 204}`
    """
    error: dict[Any, Any]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        error = data[0]
    elif isinstance(data, dict):
        error = data
    else:
        return
    code = error.get("code")
    code = code if isinstance(code, int) else None
    if "error_msg" in error:
        raise VigicruesApiError(str(error["error_msg"]), code)
    if "msg_error" in error:
        raise VigicruesApiError(str(error["msg_error"]), code)
    if "message" in error and code is not None:
        raise VigicruesApiError(str(error["message"]), code)
