import json
from collections.abc import Awaitable, Callable

import pytest

from vigicrues_client import (
    RiverSectionSummary,
    StationSummary,
    TerritorySummary,
    VigicruesClient,
    VigicruesResponseError,
)

from .support import JSON_UTF8, Serve, recorded

PLACEHOLDER = "A renseigner obligatoirement"

GetListing = Callable[[VigicruesClient], Awaitable[tuple[object, ...]]]


def _payload(*entities: dict[str, object]) -> bytes:
    """Return a referential body with the structure of the recorded ones."""
    return json.dumps({"ListEntVigiCru": list(entities)}).encode()


async def test_get_territories_returns_all_territories(serve: Serve) -> None:
    client, requests = await serve(200, JSON_UTF8, recorded("TerEntVigiCru_all.json"))

    territories = await client.get_territories()

    assert requests == ["/services/v1.1/TerEntVigiCru.json"]
    assert len(territories) == 20
    assert territories[0] == TerritorySummary("2", "Meuse-Moselle")
    assert TerritorySummary("25", "Garonne-Tarn-Lot") in territories
    assert TerritorySummary("973", "Guyane") in territories
    assert territories[-1] == TerritorySummary("999", "National")


async def test_get_river_sections_returns_all_river_sections(serve: Serve) -> None:
    client, requests = await serve(200, JSON_UTF8, recorded("TronEntVigiCru_all.json"))

    sections = await client.get_river_sections()

    assert requests == ["/services/v1.1/TronEntVigiCru.json"]
    assert len(sections) == 341
    assert sections[0] == RiverSectionSummary("AD1", "Adour amont - Echez")
    assert RiverSectionSummary("MP18", "Garonne toulousaine") in sections
    assert sections[-1] == RiverSectionSummary("VT9", "Creuse médiane")
    # Listed, although the service cannot send them by code
    assert {"MP1", "GA3", "ME1", "NO3"} <= {s.code for s in sections}


async def test_get_stations_returns_all_stations(serve: Serve) -> None:
    client, requests = await serve(
        200, JSON_UTF8, recorded("StaEntVigiCru_all_trimmed.json")
    )

    stations = await client.get_stations()

    assert requests == ["/services/v1.1/StaEntVigiCru.json"]
    assert stations == (
        StationSummary("5041000101", "Apatou", "Maroni"),
        StationSummary("5061000101", "St-Laurent-du-Maroni [Au port]", "Maroni"),
        StationSummary("E540031001", "Brimeux", "Canche"),
        StationSummary("Y980000302", "Porto-Vecchio [Pont de Bala]", "Bala"),
    )


@pytest.mark.parametrize(
    ("get_listing", "entity", "expected"),
    [
        pytest.param(
            VigicruesClient.get_territories,
            {"CdEntVigiCru": "25", "LbEntVigiCru": PLACEHOLDER},
            TerritorySummary("25", None),
            id="territory",
        ),
        pytest.param(
            VigicruesClient.get_river_sections,
            {"CdEntVigiCru": "MP18", "LbEntVigiCru": PLACEHOLDER},
            RiverSectionSummary("MP18", None),
            id="river section",
        ),
        pytest.param(
            VigicruesClient.get_stations,
            {
                "CdEntVigiCru": "E540031001",
                "LbEntVigiCru": PLACEHOLDER,
                "LbCoursEau": "A renseigner",
            },
            StationSummary("E540031001", None, None),
            id="station",
        ),
    ],
)
async def test_listings_map_placeholders_to_none(
    serve: Serve, get_listing: GetListing, entity: dict[str, object], expected: object
) -> None:
    client, _ = await serve(200, JSON_UTF8, _payload(entity))

    assert await get_listing(client) == (expected,)


@pytest.mark.parametrize(
    "get_listing",
    [
        pytest.param(VigicruesClient.get_territories, id="territories"),
        pytest.param(VigicruesClient.get_river_sections, id="river sections"),
        pytest.param(VigicruesClient.get_stations, id="stations"),
    ],
)
@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(b"{}", "array for ListEntVigiCru", id="no list"),
        pytest.param(
            _payload({"LbEntVigiCru": "Canche"}),
            "string for CdEntVigiCru",
            id="no code",
        ),
        pytest.param(
            _payload({"CdEntVigiCru": "AP16"}), "string for LbEntVigiCru", id="no name"
        ),
    ],
)
async def test_listings_raise_on_invalid_payload(
    serve: Serve, get_listing: GetListing, body: bytes, match: str
) -> None:
    client, _ = await serve(200, JSON_UTF8, body)

    with pytest.raises(VigicruesResponseError, match=match):
        await get_listing(client)


async def test_get_stations_raises_without_river(serve: Serve) -> None:
    client, _ = await serve(
        200,
        JSON_UTF8,
        _payload({"CdEntVigiCru": "E540031001", "LbEntVigiCru": "Brimeux"}),
    )

    with pytest.raises(VigicruesResponseError, match="string for LbCoursEau"):
        await client.get_stations()


@pytest.mark.live
async def test_get_territories_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        territories = await client.get_territories()

    assert TerritorySummary("25", "Garonne-Tarn-Lot") in territories


@pytest.mark.live
async def test_get_river_sections_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        sections = await client.get_river_sections()

    assert RiverSectionSummary("MP18", "Garonne toulousaine") in sections


@pytest.mark.live
async def test_get_stations_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        stations = await client.get_stations()

    assert StationSummary("E540031001", "Brimeux", "Canche") in stations
