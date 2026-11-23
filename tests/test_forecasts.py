import json
from datetime import datetime, timedelta, timezone

import pytest

from vigicrues_client import (
    ForecastPoint,
    Quantity,
    VigicruesApiError,
    VigicruesBadValueError,
    VigicruesClient,
    VigicruesResponseError,
)

from .support import JSON_UTF8, Serve, recorded

PREVISION_PATH = "/services/v1.1/prevision.json"
# Offset sent by the service in winter (local time)
CET = timezone(timedelta(hours=1))


def _payload(points: list[dict[str, object]], quantity: str = "H") -> bytes:
    """Return a prevision.json body with the structure of the recorded ones."""
    return json.dumps(
        {
            "Simul": {
                "CdEntVigiCru": "E540031001",
                "LbEntVigiCru": "Brimeux",
                "GrdSimul": quantity,
                "DtProdSimul": "2026-11-23T14:21:24+01:00",
                "CommentSimul": "Prévision réalisée le 23/11/2026 à 14h15.",
                "Prevs": points,
            }
        }
    ).encode()


def _point(time: str, value: object = 1.84) -> dict[str, object]:
    return {
        "DtPrev": time,
        "ResMinPrev": 1.68,
        "ResMoyPrev": value,
        "ResMaxPrev": 1.91,
    }


async def test_get_forecast_returns_heights(serve: Serve) -> None:
    client, requests = await serve(
        200, JSON_UTF8, recorded("prevision_E540031001.json")
    )

    forecast = await client.get_forecast("E540031001")

    assert requests == [
        f"{PREVISION_PATH}?CdEntVigiCru=E540031001&TypEntVigiCru=7&GrdSimul=H"
        "&FormatDate=iso"
    ]
    assert forecast is not None
    assert forecast.station_code == "E540031001"
    assert forecast.station_name == "Brimeux"
    assert forecast.quantity is Quantity.HEIGHT
    assert forecast.production_time == datetime(2026, 11, 23, 14, 21, 24, tzinfo=CET)
    assert forecast.comment.startswith(
        "Comment lire les courbes de prévision (tendances) : la tendance basse a 9"
        " chances sur 10 d'être dépassée."
    )
    assert forecast.comment.endswith("\nPrévision réalisée le 23/11/2026 à 14h15.")
    assert len(forecast.points) == 27
    assert forecast.points[0] == ForecastPoint(
        datetime(2026, 11, 23, 21, 0, tzinfo=CET), 1.68, 1.84, 1.91
    )
    assert forecast.points[-1] == ForecastPoint(
        datetime(2026, 11, 24, 23, 0, tzinfo=CET), 1.28, 1.52, 1.72
    )


async def test_get_forecast_returns_flow_rates(serve: Serve) -> None:
    client, requests = await serve(
        200, JSON_UTF8, recorded("prevision_E540031001_Q.json")
    )

    forecast = await client.get_forecast("E540031001", Quantity.FLOW)

    assert requests == [
        f"{PREVISION_PATH}?CdEntVigiCru=E540031001&TypEntVigiCru=7&GrdSimul=Q"
        "&FormatDate=iso"
    ]
    assert forecast is not None
    assert forecast.quantity is Quantity.FLOW
    assert len(forecast.points) == 27
    assert forecast.points[0] == ForecastPoint(
        datetime(2026, 11, 23, 21, 0, tzinfo=CET), 24.29, 26.54, 28.99
    )


@pytest.mark.parametrize(
    "file",
    [
        pytest.param("prevision_no_forecast.json", id="no forecast at the moment"),
        pytest.param(
            "prevision_not_forecast_station.json", id="not a forecast station"
        ),
        pytest.param("prevision_unknown.json", id="unknown station"),
    ],
)
async def test_get_forecast_returns_none_without_forecast(
    serve: Serve, file: str
) -> None:
    client, _ = await serve(200, JSON_UTF8, recorded(file))

    assert await client.get_forecast("E540031001") is None


async def test_get_forecast_passes_other_messages_with_code_204_on(
    serve: Serve,
) -> None:
    client, _ = await serve(200, JSON_UTF8, recorded("prevision_invalid_quantity.json"))

    with pytest.raises(VigicruesApiError) as error_info:
        await client.get_forecast("E540031001")

    assert error_info.value.message == "Paramètre GrdSimul invalide"
    assert error_info.value.code == 204


async def test_get_forecast_passes_known_messages_with_other_codes_on(
    serve: Serve,
) -> None:
    # Shape of prevision_unknown.json, with the code of the other services
    client, _ = await serve(
        200,
        JSON_UTF8,
        b'{"Simul":{"Prevs":[]},"message":"Code de station inconnu","code":400}',
    )

    with pytest.raises(VigicruesBadValueError):
        await client.get_forecast("X000000000")


async def test_get_forecast_raises_on_other_quantity(serve: Serve) -> None:
    client, _ = await serve(200, JSON_UTF8, recorded("prevision_E540031001.json"))

    with pytest.raises(VigicruesResponseError, match="Expected FLOW forecast"):
        await client.get_forecast("E540031001", Quantity.FLOW)


async def test_get_forecast_sorts_points(serve: Serve) -> None:
    client, _ = await serve(
        200,
        JSON_UTF8,
        _payload(
            [
                _point("2026-11-23T22:00:00+01:00", 1.83),
                _point("2026-11-23T21:00:00+01:00", 2),
            ]
        ),
    )

    forecast = await client.get_forecast("E540031001")

    assert forecast is not None
    assert forecast.points == (
        ForecastPoint(datetime(2026, 11, 23, 21, 0, tzinfo=CET), 1.68, 2.0, 1.91),
        ForecastPoint(datetime(2026, 11, 23, 22, 0, tzinfo=CET), 1.68, 1.83, 1.91),
    )


@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(b"{}", "object for Simul", id="no Simul"),
        pytest.param(
            b'{"Simul": {"Prevs": {}}}', "array for Prevs", id="points not an array"
        ),
        pytest.param(
            _payload([]).replace(b'"LbEntVigiCru"', b'"Lb"'),
            "string for LbEntVigiCru",
            id="no station name",
        ),
        pytest.param(_payload([], quantity="X"), "Unknown quantity 'X'", id="quantity"),
        pytest.param(
            _payload([]).replace(b"2026-11-23T14:21:24+01:00", b"23/11/2026 14:21"),
            "Invalid date",
            id="production time",
        ),
        pytest.param(
            _payload([]).replace(b'"CommentSimul"', b'"Comment"'),
            "string for CommentSimul",
            id="no comment",
        ),
        pytest.param(
            _payload([_point("2026-11-23T21:00:00+01:00", None)]),
            "number for ResMoyPrev",
            id="no value",
        ),
        pytest.param(
            _payload([_point("2026-11-23T21:00:00")]),
            "Date and time without offset",
            id="point time",
        ),
    ],
)
async def test_get_forecast_raises_on_invalid_payload(
    serve: Serve, body: bytes, match: str
) -> None:
    client, _ = await serve(200, JSON_UTF8, body)

    with pytest.raises(VigicruesResponseError, match=match):
        await client.get_forecast("E540031001")


@pytest.mark.live
async def test_get_forecast_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        forecast = await client.get_forecast("E540031001")

    # Brimeux is a forecast station, but may have no forecast at the moment
    if forecast is not None:
        assert forecast.station_code == "E540031001"
        assert forecast.quantity is Quantity.HEIGHT
        assert forecast.production_time.tzinfo is not None
        assert forecast.points


@pytest.mark.live
async def test_get_forecast_returns_none_for_unknown_station_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        assert await client.get_forecast("X000000000") is None
