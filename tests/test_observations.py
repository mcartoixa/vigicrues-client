import json
from datetime import UTC, datetime

import pytest

from vigicrues_client import (
    Observation,
    Quantity,
    VigicruesApiError,
    VigicruesBadValueError,
    VigicruesClient,
    VigicruesResponseError,
)

from .support import Serve, recorded


def _payload(observations: list[dict[str, object]], quantity: str = "H") -> bytes:
    """Return an observations.json body with the structure of the recorded ones."""
    return json.dumps(
        {
            "Serie": {
                "CdStationHydro": "O262002001",
                "LbStationHydro": "Verdun [HE]",
                "GrdSerie": quantity,
                "ObssHydro": observations,
            }
        }
    ).encode()


async def test_get_observations_returns_heights(serve: Serve) -> None:
    client, _ = await serve(
        200, "application/json", recorded("observations_O262002001.json")
    )

    series = await client.get_observations("O262002001")

    assert series.station_code == "O262002001"
    assert series.station_name == "Verdun [HE]"
    assert series.quantity is Quantity.HEIGHT
    assert len(series.observations) == 2577
    assert series.observations[0] == Observation(
        datetime(2026, 10, 20, 22, 5, tzinfo=UTC), -0.92
    )
    assert series.latest == Observation(
        datetime(2026, 11, 21, 18, 45, tzinfo=UTC), -0.87
    )


async def test_get_observations_requests_heights_with_iso_dates(serve: Serve) -> None:
    client, requests = await serve(
        200, "application/json", recorded("observations_O262002001.json")
    )

    await client.get_observations("O262002001")

    assert requests == [
        "/services/observations.json?CdStationHydro=O262002001&GrdSerie=H&FormatDate=iso"
    ]


async def test_get_observations_returns_flow_rates(serve: Serve) -> None:
    client, requests = await serve(
        200, "application/json", recorded("observations_E540031001_Q_trimmed.json")
    )

    series = await client.get_observations("E540031001", Quantity.FLOW)

    assert requests == [
        "/services/observations.json?CdStationHydro=E540031001&GrdSerie=Q&FormatDate=iso"
    ]
    assert series.station_name == "Brimeux"
    assert series.quantity is Quantity.FLOW
    assert series.observations[0] == Observation(
        datetime(2026, 7, 27, 23, 0, tzinfo=UTC), 9.8
    )
    assert series.latest == Observation(
        datetime(2026, 11, 21, 18, 40, tzinfo=UTC), 45.5
    )


async def test_get_observations_returns_empty_series_when_quantity_not_measured(
    serve: Serve,
) -> None:
    client, _ = await serve(
        200, "application/json", recorded("observations_O262002001_Q.json")
    )

    series = await client.get_observations("O262002001", Quantity.FLOW)

    assert series.quantity is Quantity.FLOW
    assert series.latest is None


async def test_get_observations_raises_on_other_quantity(serve: Serve) -> None:
    client, _ = await serve(
        200, "application/json", recorded("observations_O262002001.json")
    )

    with pytest.raises(VigicruesResponseError, match="Expected FLOW observations"):
        await client.get_observations("O262002001", Quantity.FLOW)


async def test_get_observations_raises_bad_value_for_unknown_station(
    serve: Serve,
) -> None:
    client, _ = await serve(
        200, "application/json", recorded("observations_unknown.json")
    )

    with pytest.raises(VigicruesBadValueError) as error_info:
        await client.get_observations("X000000000")

    assert error_info.value.message == "Code de station inconnu"


async def test_get_observations_passes_other_api_errors_on(serve: Serve) -> None:
    # Shape of observations_unknown.json, with an error code never observed
    client, _ = await serve(
        200, "application/json", b'{"error_msg":"Erreur interne","code":500}'
    )

    with pytest.raises(VigicruesApiError) as error_info:
        await client.get_observations("O262002001")

    assert not isinstance(error_info.value, VigicruesBadValueError)
    assert error_info.value.code == 500


async def test_get_observations_sorts_observations(serve: Serve) -> None:
    client, _ = await serve(
        200,
        "application/json",
        _payload(
            [
                {"DtObsHydro": "2026-11-21T10:05:00+00:00", "ResObsHydro": -0.82},
                {"DtObsHydro": "2026-11-21T10:00:00+00:00", "ResObsHydro": -1},
            ]
        ),
    )

    series = await client.get_observations("O262002001")

    assert series.observations == (
        Observation(datetime(2026, 11, 21, 10, 0, tzinfo=UTC), -1.0),
        Observation(datetime(2026, 11, 21, 10, 5, tzinfo=UTC), -0.82),
    )


async def test_get_observations_returns_empty_series(serve: Serve) -> None:
    client, _ = await serve(200, "application/json", _payload([]))

    series = await client.get_observations("O262002001")

    assert series.observations == ()
    assert series.latest is None


@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(b"{}", "object for Serie", id="no Serie"),
        pytest.param(
            b'{"Serie": {"CdStationHydro": "O262002001", "GrdSerie": "H",'
            b' "ObssHydro": []}}',
            "string for LbStationHydro",
            id="no station name",
        ),
        pytest.param(
            b'{"Serie": {"GrdSerie": "H", "ObssHydro": {}}}',
            "array for ObssHydro",
            id="observations not an array",
        ),
        pytest.param(_payload([], quantity="X"), "Unknown quantity 'X'", id="quantity"),
        pytest.param(
            _payload([{"DtObsHydro": "2026-11-21T10:00:00+00:00"}]),
            "number for ResObsHydro",
            id="no value",
        ),
        pytest.param(
            _payload([{"DtObsHydro": "21.11.2026", "ResObsHydro": -0.83}]),
            "Invalid date",
            id="date",
        ),
    ],
)
async def test_get_observations_raises_on_invalid_payload(
    serve: Serve, body: bytes, match: str
) -> None:
    client, _ = await serve(200, "application/json", body)

    with pytest.raises(VigicruesResponseError, match=match):
        await client.get_observations("O262002001")


@pytest.mark.live
async def test_get_observations_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        series = await client.get_observations("O262002001")

    assert series.station_code == "O262002001"
    assert series.quantity is Quantity.HEIGHT
    assert series.latest is not None
    assert series.latest.time.tzinfo is not None


@pytest.mark.live
async def test_get_observations_of_flow_rates_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        series = await client.get_observations("E540031001", Quantity.FLOW)

    assert series.station_code == "E540031001"
    assert series.quantity is Quantity.FLOW
    assert series.latest is not None
