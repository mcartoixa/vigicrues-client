import pytest

from vigicrues_client import (
    BasinStation,
    HistoricalFlood,
    VigicruesClient,
    VigicruesNotFoundError,
    VigicruesResponseError,
)

from .support import JSON_UTF8, Response, Serve, recorded

STATION_UNKNOWN = Response(500, "text/html", recorded("station_unknown.html"))
REFERENTIAL_PATH = "/services/v1.1/StaEntVigiCru.json"


async def test_get_station_returns_forecast_station(serve: Serve) -> None:
    client, requests = await serve(
        200, "application/json", recorded("station_E540031001.json")
    )

    station = await client.get_station("E540031001")

    assert requests == ["/services/station.json?CdStationHydro=E540031001"]
    assert station.code == "E540031001"
    assert station.name == "Brimeux"
    assert station.river == "Canche"
    assert station.commune_code == "62177"
    assert station.territory_code == "29"
    assert station.is_forecast_station
    assert station.historical_floods == (
        HistoricalFlood("Crue de novembre 2023", 2.09, 45.5),
        HistoricalFlood("Crue de janvier 2021", 2.02, 37.7),
        HistoricalFlood("Crue de mars 2020", 1.98, 32.8),
    )
    assert len(station.basin_stations) == 6
    assert station.basin_stations[0] == BasinStation("E541000401", "Beutin", "Canche")
    assert station.basin_stations[-1] == BasinStation(
        "E540651901", "Teneur", "Ternoise"
    )


async def test_get_station_returns_station_without_forecasts(serve: Serve) -> None:
    client, _ = await serve(
        200, "application/json", recorded("station_E541000401.json")
    )

    station = await client.get_station("E541000401")

    assert station.name == "Beutin"
    assert station.commune_code == "62124"
    assert station.territory_code == "29"
    assert not station.is_forecast_station
    # The service sends 0 for unknown flow rates
    assert station.historical_floods == (
        HistoricalFlood("Crue de janvier 2018", 2.92, None),
        HistoricalFlood("Crue de novembre 2023", 2.8, None),
        HistoricalFlood("Crue de février 2016", 2.73, None),
    )


async def test_get_station_raises_not_found_for_unknown_station(serve: Serve) -> None:
    client, requests = await serve(
        *STATION_UNKNOWN,
        routes={
            REFERENTIAL_PATH: Response(
                200, JSON_UTF8, recorded("StaEntVigiCru_unknown.json")
            )
        },
    )

    with pytest.raises(VigicruesNotFoundError) as error_info:
        await client.get_station("X000000000")

    assert error_info.value.message == "Code de station inconnu."
    assert requests == [
        "/services/station.json?CdStationHydro=X000000000",
        f"{REFERENTIAL_PATH}?CdEntVigiCru=X000000000&TypEntVigiCru=7",
    ]


@pytest.mark.parametrize(
    "referential",
    [
        pytest.param(
            Response(200, JSON_UTF8, recorded("StaEntVigiCru_E540031001.json")),
            id="known station",
        ),
        pytest.param(STATION_UNKNOWN, id="referential down too"),
        pytest.param(
            Response(200, JSON_UTF8, recorded("TronEntVigiCru_missing_type.json")),
            id="other referential error",
        ),
    ],
)
async def test_get_station_raises_original_error_for_known_station(
    serve: Serve, referential: Response
) -> None:
    client, _ = await serve(*STATION_UNKNOWN, routes={REFERENTIAL_PATH: referential})

    with pytest.raises(VigicruesResponseError, match="HTTP status 500"):
        await client.get_station("E540031001")


@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(
            b'{"CdStationHydro": "E540031001"}',
            "object for VigilanceCrues",
            id="no vigilance",
        ),
        pytest.param(
            b'{"CdStationHydro": "E540031001", "LbStationHydro": "Brimeux",'
            b' "LbCoursEau": "Canche", "CdCommune": "62177", "VigilanceCrues":'
            b' {"PereBoitEntVigiCru": {"CdEntVigiCru": "29"},'
            b' "StationPrevision": "t"}}',
            "boolean for StationPrevision",
            id="forecast flag",
        ),
    ],
)
async def test_get_station_raises_on_invalid_payload(
    serve: Serve, body: bytes, match: str
) -> None:
    client, _ = await serve(200, "application/json", body)

    with pytest.raises(VigicruesResponseError, match=match):
        await client.get_station("E540031001")


@pytest.mark.live
async def test_get_station_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        station = await client.get_station("E540031001")

    assert station.name == "Brimeux"
    assert station.is_forecast_station


@pytest.mark.live
async def test_get_station_raises_not_found_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        with pytest.raises(VigicruesNotFoundError):
            await client.get_station("X000000000")
