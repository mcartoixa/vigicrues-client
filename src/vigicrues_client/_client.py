"""Client for the Vigicrues service."""

import importlib.metadata
import json
from collections.abc import Awaitable, Mapping
from http import HTTPStatus
from types import TracebackType
from typing import Any, NamedTuple, Self

import aiohttp

from ._bulletins import parse_territory_bulletin
from ._errors import (
    VigicruesApiError,
    VigicruesBadValueError,
    VigicruesConnectionError,
    VigicruesError,
    VigicruesNotFoundError,
    VigicruesRateLimitError,
    VigicruesResponseError,
    VigicruesUnknownValueError,
)
from ._forecasts import NO_FORECAST_MESSAGES, parse_forecast
from ._models import (
    EntityType,
    Forecast,
    ObservationSeries,
    Quantity,
    RiverSection,
    RiverSectionSummary,
    RiverSectionVigilance,
    Station,
    StationSummary,
    Territory,
    TerritoryBulletin,
    TerritorySummary,
    VigilanceLevel,
    VigilanceLevels,
)
from ._observations import parse_observation_series
from ._referential import (
    find_entity,
    get_entities,
    parse_river_section,
    parse_river_section_summary,
    parse_station_summary,
    parse_territory,
    parse_territory_summary,
)
from ._stations import parse_station
from ._vigilance import parse_vigilance_levels

DEFAULT_BASE_URL = "https://www.vigicrues.gouv.fr"
DEFAULT_TIMEOUT = 30.0

_USER_AGENT = (
    f"vigicrues-client/{importlib.metadata.version('vigicrues-client')}"
    " (+https://github.com/mcartoixa/vigicrues-client)"
)


class _Content(NamedTuple):
    """Content of a successful response."""

    type: str
    charset: str | None
    body: bytes


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
            VigicruesBadValueError: The service rejected the station code: unknown
                or invalid.
            VigicruesError: The observations could not be retrieved.
        """
        data = await self._get_json(
            "services/observations.json",
            {
                "CdStationHydro": station,
                "GrdSerie": quantity.value,
                "FormatDate": "iso",
            },
        )
        series = parse_observation_series(data)
        _check_quantity(quantity, series.quantity, "observations")
        return series

    async def get_station(self, station: str) -> Station:
        """Get the details of a station.

        Args:
            station: Code of the hydrometric station, e.g. `"E540031001"`.

        Raises:
            VigicruesBadValueError: The service rejected the station code: unknown
                or invalid.
            VigicruesError: The details could not be retrieved.
        """
        try:
            data = await self._get_json(
                "services/station.json", {"CdStationHydro": station}
            )
        except VigicruesResponseError as error:
            # The service answers an unknown station with the same HTTP 500 page as
            # an outage: the referential tells them apart.
            rejection_error = await self._get_rejection_error(
                self._get_referential("StaEntVigiCru.json", station, EntityType.STATION)
            )
            if rejection_error is None:
                raise
            raise rejection_error from error
        return parse_station(data)

    async def get_forecast(
        self, station: str, quantity: Quantity = Quantity.HEIGHT
    ) -> Forecast | None:
        """Get the latest forecast of a station.

        The forecast starts after the latest observation of the station.

        Args:
            station: Code of the hydrometric station, e.g. `"E540031001"`.
            quantity: Forecast quantity: heights in metres, or flow rates in cubic
                metres per second.

        Returns:
            The forecast, or `None` if the service has none for the station: none
            at the moment, not a forecast station (see
            `Station.is_forecast_station`), or unknown or invalid station code.

        Raises:
            VigicruesError: The forecast could not be retrieved.
        """
        try:
            data = await self._get_json(
                "services/v1.1/prevision.json",
                {
                    "CdEntVigiCru": station,
                    "TypEntVigiCru": EntityType.STATION.value,
                    "GrdSimul": quantity.value,
                    "FormatDate": "iso",
                },
            )
        except VigicruesApiError as error:
            # The service reports the absence of a forecast with code 204.
            if (
                error.code == HTTPStatus.NO_CONTENT
                and error.message in NO_FORECAST_MESSAGES
            ):
                return None
            raise
        forecast = parse_forecast(data)
        _check_quantity(quantity, forecast.quantity, "forecast")
        return forecast

    async def get_territory(self, territory: str) -> Territory:
        """Get a flood vigilance territory and its river sections.

        Args:
            territory: Code of the territory, e.g. `"25"`.

        Raises:
            VigicruesBadValueError: The service rejected the territory code: unknown
                or invalid.
            VigicruesUnknownValueError: The service sent no such territory.
            VigicruesError: The territory could not be retrieved.
        """
        entities = await self._get_referential(
            "TerEntVigiCru.json", territory, EntityType.TERRITORY
        )
        # The service answers some unknown codes (e.g. "0") with all the territories.
        entity = find_entity(entities, territory)
        if entity is None:
            raise VigicruesUnknownValueError(f"Unknown territory {territory!r}")
        return parse_territory(entity)

    async def get_river_section(self, section: str) -> RiverSection:
        """Get a river section, its territory and its stations.

        Args:
            section: Code of the river section, e.g. `"AP16"`.

        Raises:
            VigicruesBadValueError: The service rejected the river section code:
                unknown or invalid.
            VigicruesUnknownValueError: The service sent no such river section.
            VigicruesError: The river section could not be retrieved.
        """
        entities = await self._get_referential(
            "TronEntVigiCru.json", section, EntityType.RIVER_SECTION
        )
        entity = find_entity(entities, section)
        if entity is None and entities:
            # The service matches the code as a substring, and may send another
            # section even if the requested one exists ("MP1" gets "MP10"): look
            # for it among the river sections of the territory of the one sent.
            territory = parse_river_section(entities[0]).territory_code
            if territory is not None:
                entity = find_entity(
                    await self._get_referential(
                        "TronEntVigiCru.json", territory, EntityType.TERRITORY
                    ),
                    section,
                )
        if entity is None:
            raise VigicruesUnknownValueError(f"Unknown river section {section!r}")
        return parse_river_section(entity)

    async def get_territories(self) -> tuple[TerritorySummary, ...]:
        """Get all the flood vigilance territories.

        Returns:
            The territories, in the order sent by the service.

        Raises:
            VigicruesError: The territories could not be retrieved.
        """
        entities = await self._get_listing("TerEntVigiCru.json")
        return tuple(parse_territory_summary(entity) for entity in entities)

    async def get_river_sections(self) -> tuple[RiverSectionSummary, ...]:
        """Get all the river sections.

        Returns:
            The river sections, in the order sent by the service.

        Raises:
            VigicruesError: The river sections could not be retrieved.
        """
        entities = await self._get_listing("TronEntVigiCru.json")
        return tuple(parse_river_section_summary(entity) for entity in entities)

    async def get_stations(self) -> tuple[StationSummary, ...]:
        """Get all the stations of the flood vigilance network.

        The service sends them all at once (about 1.7 MB).

        Returns:
            The stations, in the order sent by the service.

        Raises:
            VigicruesError: The stations could not be retrieved.
        """
        entities = await self._get_listing("StaEntVigiCru.json")
        return tuple(parse_station_summary(entity) for entity in entities)

    async def get_vigilance_levels(self) -> VigilanceLevels:
        """Get the current flood vigilance levels of all the river sections.

        The service only sends them all at once, with their geometries (about
        2 MB), and only for metropolitan France: prefer this method to
        `get_vigilance_level` to follow several river sections.

        Raises:
            VigicruesError: The levels could not be retrieved.
        """
        return parse_vigilance_levels(
            await self._get_json("services/1/InfoVigiCru.geojson")
        )

    async def get_vigilance_level(self, section: str) -> VigilanceLevel:
        """Get the current flood vigilance level of a river section.

        Args:
            section: Code of the river section, e.g. `"AP16"`.

        Raises:
            VigicruesUnknownValueError: The service sent no level for the river
                section: unknown, or outside metropolitan France (e.g. `"GU1"`).
            VigicruesError: The level could not be retrieved.
        """
        level = (await self.get_vigilance_levels()).levels.get(section)
        if level is None:
            raise VigicruesUnknownValueError(
                f"No vigilance level for river section {section!r}"
            )
        return level

    async def get_territory_bulletin(self, territory: str) -> TerritoryBulletin:
        """Get the flood vigilance bulletin of a territory.

        The bulletin is read from the page of the territory on the Vigicrues web
        site: it may change without notice.

        Args:
            territory: Code of the territory, e.g. `"29"`.

        Raises:
            VigicruesBadValueError: The service rejected the territory code: unknown
                or invalid.
            VigicruesUnknownValueError: The service sent no such territory.
            VigicruesResponseError: The page does not have the expected structure.
            VigicruesError: The bulletin could not be retrieved.
        """
        try:
            body, encoding = await self._get_html(f"bulletin_local/{territory}")
        except VigicruesResponseError as error:
            # The service answers an unknown territory with the same HTTP 500 page as
            # an outage: the referential tells them apart.
            rejection_error = await self._get_rejection_error(
                self.get_territory(territory)
            )
            if rejection_error is None:
                raise
            raise rejection_error from error
        return parse_territory_bulletin(territory, body, encoding)

    async def get_river_section_vigilance(self, section: str) -> RiverSectionVigilance:
        """Get the current flood vigilance of a river section: level and texts.

        Reads the bulletin of the territory of the river section, like
        `get_territory_bulletin`: it may change without notice.

        Args:
            section: Code of the river section, e.g. `"MP18"`.

        Raises:
            VigicruesBadValueError: The service rejected a code: unknown or invalid.
            VigicruesUnknownValueError: The service sent no such river section.
            VigicruesResponseError: The service sent no territory for the river
                section, or its bulletin does not have the expected structure or
                does not list it.
            VigicruesError: The vigilance could not be retrieved.
        """
        river_section = await self.get_river_section(section)
        if river_section.territory_code is None:
            raise VigicruesResponseError(f"No territory for river section {section!r}")
        bulletin = await self.get_territory_bulletin(river_section.territory_code)
        if not bulletin.river_sections:
            # Only listed when one river section of the territory is in vigilance.
            return RiverSectionVigilance(
                river_section, VigilanceLevel.GREEN, (), bulletin
            )
        bulletin_section = next(
            (s for s in bulletin.river_sections if s.code == section), None
        )
        if bulletin_section is None:
            raise VigicruesResponseError(
                f"River section {section!r} not in the bulletin of territory"
                f" {river_section.territory_code!r}"
            )
        return RiverSectionVigilance(
            river_section, bulletin_section.level, bulletin_section.comments, bulletin
        )

    async def _get_rejection_error(
        self, lookup: Awaitable[object]
    ) -> VigicruesBadValueError | VigicruesUnknownValueError | None:
        """Return the error of a referential lookup if it rejects the code."""
        try:
            await lookup
        except (VigicruesBadValueError, VigicruesUnknownValueError) as error:
            return error
        except VigicruesRateLimitError:
            # The caller must slow down, whatever the original error.
            raise
        except VigicruesError:
            return None
        return None

    async def _get_referential(
        self, file: str, code: str, entity_type: EntityType
    ) -> list[dict[str, object]]:
        """Return the entities sent by the v1.1 referential for a code.

        The entities may not have the requested code: the service matches some
        codes loosely.
        """
        data = await self._get_json(
            f"services/v1.1/{file}",
            {"CdEntVigiCru": code, "TypEntVigiCru": entity_type.value},
        )
        return get_entities(data)

    async def _get_listing(self, file: str) -> list[dict[str, object]]:
        """Return all the entities of the v1.1 referential."""
        return get_entities(await self._get_json(f"services/v1.1/{file}"))

    async def _get_json(
        self, path: str, params: Mapping[str, str] | None = None
    ) -> object:
        content = await self._get(path, params)
        if content.type != "application/json":
            raise VigicruesResponseError(
                f"Unexpected content type {content.type!r} for {path}"
            )
        try:
            data: object = json.loads(content.body)
        except ValueError as error:
            raise VigicruesResponseError(f"Invalid JSON for {path}") from error
        _raise_for_api_error(data)
        return data

    async def _get_html(self, path: str) -> tuple[bytes, str | None]:
        """Return the body of an HTML page and its encoding, if the response sets it."""
        content = await self._get(path)
        if content.type != "text/html":
            raise VigicruesResponseError(
                f"Unexpected content type {content.type!r} for {path}"
            )
        return content.body, content.charset

    async def _get(
        self, path: str, params: Mapping[str, str] | None = None
    ) -> _Content:
        """Return the content of a successful response."""
        try:
            async with self._get_session().get(
                f"{self._base_url}/{path}", params=params, timeout=self._timeout
            ) as response:
                if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                    raise VigicruesRateLimitError(f"Too many requests for {path}")
                if response.status == HTTPStatus.NOT_FOUND:
                    raise VigicruesNotFoundError(f"HTTP status 404 for {path}")
                if not response.ok:
                    raise VigicruesResponseError(
                        f"HTTP status {response.status} for {path}"
                    )
                return _Content(
                    response.content_type, response.charset, await response.read()
                )
        except (aiohttp.ClientError, TimeoutError) as error:
            raise VigicruesConnectionError(f"Could not get {path}") from error

    def _get_session(self) -> aiohttp.ClientSession:
        # Created on first use: aiohttp expects sessions to be created in a coroutine.
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={"User-Agent": _USER_AGENT})
        return self._session


def _check_quantity(expected: Quantity, actual: Quantity, values: str) -> None:
    """Raise if the service sent values of another quantity than the requested one."""
    if actual is not expected:
        raise VigicruesResponseError(
            f"Expected {expected.name} {values}, got {actual.name}"
        )


def _raise_for_api_error(data: object) -> None:
    """Raise the error reported in a response body, if any.

    The service reports errors with HTTP 200, in several shapes:
    - `[{"error_msg": ..., "code": 400}]`
    - `{"error_msg": ..., "code": 400}`
    - `{"Scenario": {...}, "msg_error": ...}`
    - `{"Simul": {...}, "message": ..., "code": 204}`

    Code 400 means that a value of the request is unknown or invalid.
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
        message = error["error_msg"]
    elif "msg_error" in error:
        message = error["msg_error"]
    elif "message" in error and code is not None:
        message = error["message"]
    else:
        return
    if code == HTTPStatus.BAD_REQUEST:
        raise VigicruesBadValueError(str(message), code)
    raise VigicruesApiError(str(message), code)
