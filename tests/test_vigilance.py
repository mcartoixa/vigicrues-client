import json
from datetime import UTC, datetime

import pytest

from vigicrues_client import (
    VigicruesClient,
    VigicruesResponseError,
    VigicruesUnknownValueError,
    VigilanceLevel,
)

from .support import Serve, recorded

GEOJSON = "application/json; charset=utf-8"


def _payload(
    *sections: dict[str, object], time: object = "2026-11-22T04:59:43+00:00"
) -> bytes:
    """Return an InfoVigiCru.geojson body with the structure of the recorded one."""
    return json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": section, "geometry": None}
                for section in sections
            ],
            "DtHrInfoVigiCru": time,
        }
    ).encode()


async def test_get_vigilance_levels_returns_levels(serve: Serve) -> None:
    client, requests = await serve(
        200, GEOJSON, recorded("InfoVigiCru_trimmed.geojson")
    )

    levels = await client.get_vigilance_levels()

    assert requests == ["/services/1/InfoVigiCru.geojson"]
    assert levels.time == datetime(2026, 11, 22, 4, 59, 43, tzinfo=UTC)
    assert levels.levels == {
        "RS18": VigilanceLevel.YELLOW,
        "RS31": VigilanceLevel.YELLOW,
        "RS41": VigilanceLevel.YELLOW,
        "AP16": VigilanceLevel.ORANGE,
        "MP18": VigilanceLevel.GREEN,
        "NO14": VigilanceLevel.YELLOW,
        "DO10": VigilanceLevel.GREEN,
    }


@pytest.mark.parametrize(
    ("section", "level"),
    [
        pytest.param("MP18", VigilanceLevel.GREEN, id="green"),
        pytest.param("RS18", VigilanceLevel.YELLOW, id="yellow"),
        pytest.param("AP16", VigilanceLevel.ORANGE, id="orange"),
    ],
)
async def test_get_vigilance_level_returns_level(
    serve: Serve, section: str, level: VigilanceLevel
) -> None:
    client, _ = await serve(200, GEOJSON, recorded("InfoVigiCru_trimmed.geojson"))

    assert await client.get_vigilance_level(section) is level


async def test_get_vigilance_level_returns_red_level(serve: Serve) -> None:
    # Never observed: 4 is inferred from the scale of levels
    client, _ = await serve(
        200, GEOJSON, _payload({"CdEntCru": "AP16", "NivInfViCr": 4})
    )

    assert await client.get_vigilance_level("AP16") is VigilanceLevel.RED


@pytest.mark.parametrize(
    "section",
    [
        pytest.param("MP6", id="unknown"),
        pytest.param("GU1", id="outside metropolitan France"),
    ],
)
async def test_get_vigilance_level_raises_unknown_value_for_section_not_sent(
    serve: Serve, section: str
) -> None:
    client, _ = await serve(200, GEOJSON, recorded("InfoVigiCru_trimmed.geojson"))

    with pytest.raises(
        VigicruesUnknownValueError,
        match=f"No vigilance level for river section '{section}'",
    ):
        await client.get_vigilance_level(section)


@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(
            _payload({"CdEntCru": "AP16", "NivInfViCr": 5}),
            "Unknown vigilance level 5",
            id="unknown level",
        ),
        pytest.param(
            _payload({"CdEntCru": "AP16", "NivInfViCr": "3"}),
            "integer for NivInfViCr",
            id="level as text",
        ),
        pytest.param(
            _payload({"CdEntCru": "AP16", "NivInfViCr": 3.0}),
            "integer for NivInfViCr",
            id="level as decimal",
        ),
        pytest.param(
            _payload({"CdEntCru": "AP16", "NivInfViCr": 3}, time=None),
            "Expected a date and time",
            id="no time",
        ),
        pytest.param(
            b'{"features": [{"type": "Feature"}]}',
            "object for properties",
            id="no properties",
        ),
    ],
)
async def test_get_vigilance_levels_raises_on_invalid_payload(
    serve: Serve, body: bytes, match: str
) -> None:
    client, _ = await serve(200, GEOJSON, body)

    with pytest.raises(VigicruesResponseError, match=match):
        await client.get_vigilance_levels()


@pytest.mark.live
async def test_get_vigilance_levels_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        levels = await client.get_vigilance_levels()

    assert levels.time.tzinfo is not None
    assert "MP18" in levels.levels
