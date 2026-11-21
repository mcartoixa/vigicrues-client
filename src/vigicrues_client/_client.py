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
    VigicruesError,
    VigicruesNotFoundError,
    VigicruesRateLimitError,
    VigicruesResponseError,
)
from ._models import EntityType, ObservationSeries, Quantity, Station
from ._observations import parse_observation_series
from ._stations import parse_station

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

    async def get_observations(
        self, station: str, quantity: Quantity = Quantity.HEIGHT
    ) -> ObservationSeries:
        """Get the recent values observed at a station.

        The service keeps about one month of heights, and several months of flow
        rates.

        Args:
            station: Code of the hydrometric station, e.g. `"O262002001"`.
            quantity: Observed quantity: heights in metres, or flow rates in cubic
                metres per second.

        Returns:
            The values, from the oldest to the latest. The series is empty if the
            station does not measure the quantity.

        Raises:
            VigicruesNotFoundError: The service does not know the station.
            VigicruesError: The observations could not be retrieved.
        """
        try:
            data = await self._get_json(
                "services/observations.json",
                {
                    "CdStationHydro": station,
                    "GrdSerie": quantity.value,
                    "FormatDate": "iso",
                },
            )
        except VigicruesApiError as error:
            # The only other cause is an invalid GrdSerie, which the client never sends.
            if error.code == HTTPStatus.BAD_REQUEST:
                raise VigicruesNotFoundError(error.message, error.code) from error
            raise
        series = parse_observation_series(data)
        if series.quantity is not quantity:
            raise VigicruesResponseError(
                f"Expected {quantity.name} observations, got {series.quantity.name}"
            )
        return series

    async def get_station(self, station: str) -> Station:
        """Get the details of a station.

        Args:
            station: Code of the hydrometric station, e.g. `"E540031001"`.

        Raises:
            VigicruesNotFoundError: The service does not know the station.
            VigicruesError: The details could not be retrieved.
        """
        try:
            data = await self._get_json(
                "services/station.json", {"CdStationHydro": station}
            )
        except VigicruesResponseError as error:
            # The service answers an unknown station with the same HTTP 500 page as
            # an outage: the referential tells them apart.
            unknown_station_error = await self._get_unknown_station_error(station)
            if unknown_station_error is None:
                raise
            raise VigicruesNotFoundError(
                unknown_station_error.message, unknown_station_error.code
            ) from error
        return parse_station(data)

    async def _get_unknown_station_error(
        self, station: str
    ) -> VigicruesApiError | None:
        """Return the referential's error if it does not know the station."""
        try:
            await self._get_json(
                "services/v1.1/StaEntVigiCru.json",
                {"CdEntVigiCru": station, "TypEntVigiCru": EntityType.STATION.value},
            )
        except VigicruesApiError as error:
            # The only other cause is an invalid TypEntVigiCru, which the client
            # never sends.
            return error if error.code == HTTPStatus.BAD_REQUEST else None
        except VigicruesError:
            return None
        return None

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
