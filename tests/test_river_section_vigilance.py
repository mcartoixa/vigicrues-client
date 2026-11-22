import json

import pytest

from vigicrues_client import (
    VigicruesBadValueError,
    VigicruesClient,
    VigicruesResponseError,
    VigilanceLevel,
)

from .support import JSON_UTF8, Response, Serve, recorded

HTML_UTF8 = "text/html; charset=UTF-8"
RIVER_SECTION_PATH = "/services/v1.1/TronEntVigiCru.json"


def _routes(section: str, territory: str) -> dict[str, Response]:
    """Serve the recorded river section, and the recorded bulletin of a territory."""
    return {
        RIVER_SECTION_PATH: Response(
            200, JSON_UTF8, recorded(f"TronEntVigiCru_{section}.json")
        ),
        f"/bulletin_local/{territory}": Response(
            200, HTML_UTF8, recorded(f"bulletin_local_{territory}.html")
        ),
    }


async def test_get_river_section_vigilance_returns_section_in_vigilance(
    serve: Serve,
) -> None:
    client, requests = await serve(404, "text/plain", b"", _routes("AP16", "29"))

    vigilance = await client.get_river_section_vigilance("AP16")

    assert requests == [
        f"{RIVER_SECTION_PATH}?CdEntVigiCru=AP16&TypEntVigiCru=8",
        "/bulletin_local/29",
    ]
    assert vigilance.section.code == "AP16"
    assert vigilance.section.name == "Canche"
    assert vigilance.level is VigilanceLevel.ORANGE
    assert len(vigilance.comments) == 3
    assert vigilance.comments[1] == "Crue importante pour la saison sur la Canche."
    assert vigilance.bulletin.territory_code == "29"
    assert vigilance.bulletin.situation == "Crue importante sur la Canche et l'Authie."


async def test_get_river_section_vigilance_returns_green_section_in_listed_territory(
    serve: Serve,
) -> None:
    # Territory 18 is in vigilance, so its green sections are listed too
    client, _ = await serve(404, "text/plain", b"", _routes("RS17", "18"))

    vigilance = await client.get_river_section_vigilance("RS17")

    assert vigilance.section.name == "Allan"
    assert vigilance.level is VigilanceLevel.GREEN
    assert vigilance.comments == ("Pas de vigilance particulière requise.",)


async def test_get_river_section_vigilance_returns_green_section_of_green_territory(
    serve: Serve,
) -> None:
    # The Domoticz use case: territory 25 is all green, its page lists no sections
    client, requests = await serve(404, "text/plain", b"", _routes("MP18", "25"))

    vigilance = await client.get_river_section_vigilance("MP18")

    assert requests == [
        f"{RIVER_SECTION_PATH}?CdEntVigiCru=MP18&TypEntVigiCru=8",
        "/bulletin_local/25",
    ]
    assert vigilance.section.name == "Garonne toulousaine"
    assert vigilance.section.territory_code == "25"
    assert vigilance.level is VigilanceLevel.GREEN
    assert vigilance.comments == ()
    assert vigilance.bulletin.general_comment == (
        "Pas de vigilance particulière requise."
    )


async def test_get_river_section_vigilance_raises_for_section_not_in_bulletin(
    serve: Serve,
) -> None:
    # Bulletin of territory 18 served for territory 29: AP16 is not listed
    client, _ = await serve(
        404,
        "text/plain",
        b"",
        {
            RIVER_SECTION_PATH: Response(
                200, JSON_UTF8, recorded("TronEntVigiCru_AP16.json")
            ),
            "/bulletin_local/29": Response(
                200, HTML_UTF8, recorded("bulletin_local_18.html")
            ),
        },
    )

    with pytest.raises(
        VigicruesResponseError,
        match="River section 'AP16' not in the bulletin of territory '29'",
    ):
        await client.get_river_section_vigilance("AP16")


async def test_get_river_section_vigilance_raises_without_territory(
    serve: Serve,
) -> None:
    client, requests = await serve(
        200,
        JSON_UTF8,
        json.dumps(
            {
                "ListEntVigiCru": [
                    {
                        "CdEntVigiCru": "AP16",
                        "LbEntVigiCru": "Canche",
                        "aNPlusUn": {"CdEntVigiCruSuperieur": "A renseigner"},
                        "aNMoinsUn": [],
                    }
                ]
            }
        ).encode(),
    )

    with pytest.raises(
        VigicruesResponseError, match="No territory for river section 'AP16'"
    ):
        await client.get_river_section_vigilance("AP16")

    assert len(requests) == 1


async def test_get_river_section_vigilance_raises_bad_value_for_unknown_section(
    serve: Serve,
) -> None:
    client, requests = await serve(
        200, JSON_UTF8, recorded("TronEntVigiCru_unknown.json")
    )

    with pytest.raises(VigicruesBadValueError):
        await client.get_river_section_vigilance("MP6")

    assert len(requests) == 1


@pytest.mark.live
async def test_get_river_section_vigilance_from_vigicrues() -> None:
    # The Domoticz use case: alert level and texts of the Garonne in Toulouse
    async with VigicruesClient() as client:
        vigilance = await client.get_river_section_vigilance("MP18")

    assert vigilance.section.territory_code == "25"
    assert vigilance.bulletin.general_comment
    # Comments only when the bulletin lists the river sections of the territory
    assert bool(vigilance.comments) == bool(vigilance.bulletin.river_sections)
    if not vigilance.comments:
        assert vigilance.level is VigilanceLevel.GREEN
