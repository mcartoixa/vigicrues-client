import json
from collections.abc import Awaitable, Callable

import pytest

from vigicrues_client import (
    RiverSection,
    RiverSectionStation,
    Territory,
    TerritoryRiverSection,
    VigicruesApiError,
    VigicruesBadValueError,
    VigicruesClient,
    VigicruesResponseError,
    VigicruesUnknownValueError,
)

from .support import JSON_UTF8, Response, Serve, recorded

TERRITORY_PATH = "/services/v1.1/TerEntVigiCru.json"
RIVER_SECTION_PATH = "/services/v1.1/TronEntVigiCru.json"
PLACEHOLDER = "A renseigner obligatoirement"


def _payload(*entities: dict[str, object]) -> bytes:
    """Return a referential body with the structure of the recorded ones."""
    return json.dumps({"ListEntVigiCru": list(entities)}).encode()


async def test_get_territory_returns_river_sections(serve: Serve) -> None:
    client, requests = await serve(200, JSON_UTF8, recorded("TerEntVigiCru_25.json"))

    territory = await client.get_territory("25")

    assert requests == [f"{TERRITORY_PATH}?CdEntVigiCru=25&TypEntVigiCru=5"]
    assert territory.code == "25"
    assert territory.name == "Garonne-Tarn-Lot"
    assert len(territory.river_sections) == 24
    assert territory.river_sections[0] == TerritoryRiverSection(
        "MP10", "Garonne marmandaise"
    )
    assert (
        TerritoryRiverSection("MP18", "Garonne toulousaine") in territory.river_sections
    )
    assert territory.river_sections[-1] == TerritoryRiverSection(
        "MP19", "Garonne volvestre"
    )


async def test_get_territory_raises_bad_value_for_rejected_code(serve: Serve) -> None:
    client, requests = await serve(
        200, JSON_UTF8, recorded("TerEntVigiCru_unknown.json")
    )

    with pytest.raises(VigicruesBadValueError) as error_info:
        await client.get_territory("99")

    assert error_info.value.message == "Code d'entité de vigilance crues inconnu."
    assert len(requests) == 1


async def test_get_territory_raises_unknown_value_for_territory_not_sent(
    serve: Serve,
) -> None:
    # The service answers "0" with all the territories
    client, requests = await serve(200, JSON_UTF8, recorded("TerEntVigiCru_0.json"))

    with pytest.raises(VigicruesUnknownValueError, match="Unknown territory '0'"):
        await client.get_territory("0")

    assert len(requests) == 1


async def test_get_territory_maps_placeholders_to_none(serve: Serve) -> None:
    client, _ = await serve(
        200,
        JSON_UTF8,
        _payload(
            {
                "CdEntVigiCru": "25",
                "LbEntVigiCru": PLACEHOLDER,
                "aNMoinsUn": [
                    {
                        "CdEntVigiCruInferieur": "A renseigner",
                        "LbEntVigiCruInferieur": PLACEHOLDER,
                    }
                ],
            }
        ),
    )

    territory = await client.get_territory("25")

    assert territory == Territory("25", None, (TerritoryRiverSection(None, None),))


@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(b"{}", "array for ListEntVigiCru", id="no entities"),
        pytest.param(
            _payload({"CdEntVigiCru": "25", "LbEntVigiCru": "Garonne-Tarn-Lot"}),
            "array for aNMoinsUn",
            id="no river sections",
        ),
    ],
)
async def test_get_territory_raises_on_invalid_payload(
    serve: Serve, body: bytes, match: str
) -> None:
    client, _ = await serve(200, JSON_UTF8, body)

    with pytest.raises(VigicruesResponseError, match=match):
        await client.get_territory("25")


async def test_get_river_section_returns_stations(serve: Serve) -> None:
    client, requests = await serve(200, JSON_UTF8, recorded("TronEntVigiCru_AP16.json"))

    section = await client.get_river_section("AP16")

    assert requests == [f"{RIVER_SECTION_PATH}?CdEntVigiCru=AP16&TypEntVigiCru=8"]
    assert section.code == "AP16"
    assert section.name == "Canche"
    assert section.territory_code == "29"
    assert len(section.stations) == 7
    assert section.stations[0] == RiverSectionStation("E541000101", "Estrée")
    assert RiverSectionStation("E540031001", "Brimeux") in section.stations
    assert section.stations[-1] == RiverSectionStation("E540651901", "Teneur")


async def test_get_river_section_finds_section_shadowed_by_another(
    serve: Serve,
) -> None:
    # The service answers MP1 with MP10, of the same territory
    shadowed_query = f"{RIVER_SECTION_PATH}?CdEntVigiCru=MP1&TypEntVigiCru=8"
    territory_query = f"{RIVER_SECTION_PATH}?CdEntVigiCru=25&TypEntVigiCru=5"
    client, requests = await serve(
        404,
        "text/plain",
        b"",
        routes={
            shadowed_query: Response(
                200, JSON_UTF8, recorded("TronEntVigiCru_MP1.json")
            ),
            territory_query: Response(
                200, JSON_UTF8, recorded("TronEntVigiCru_territory_25.json")
            ),
        },
    )

    section = await client.get_river_section("MP1")

    assert requests == [shadowed_query, territory_query]
    assert section.code == "MP1"
    assert section.name == "Ariège - Hers vif"
    assert section.territory_code == "25"
    assert len(section.stations) == 11
    assert section.stations[0] == RiverSectionStation("O102251002", "Ax-les-Thermes")
    assert section.stations[-1] == RiverSectionStation("O171253001", "Auterive [HE]")


async def test_get_river_section_raises_unknown_value_for_code_inside_another(
    serve: Serve,
) -> None:
    # The service answers P16 with MP16, of territory 25
    query = f"{RIVER_SECTION_PATH}?CdEntVigiCru=P16&TypEntVigiCru=8"
    territory_query = f"{RIVER_SECTION_PATH}?CdEntVigiCru=25&TypEntVigiCru=5"
    client, requests = await serve(
        404,
        "text/plain",
        b"",
        routes={
            query: Response(200, JSON_UTF8, recorded("TronEntVigiCru_P16.json")),
            territory_query: Response(
                200, JSON_UTF8, recorded("TronEntVigiCru_territory_25.json")
            ),
        },
    )

    with pytest.raises(VigicruesUnknownValueError, match="Unknown river section 'P16'"):
        await client.get_river_section("P16")

    assert requests == [query, territory_query]


@pytest.mark.parametrize(
    ("code", "file", "message"),
    [
        pytest.param(
            "MP6",
            "TronEntVigiCru_unknown.json",
            "Problème dans l'exécution de la requête : tronçon",
            id="unknown",
        ),
        pytest.param(
            "ap16",
            "TronEntVigiCru_invalid.json",
            "Paramètre CdEntVigiCru invalide",
            id="invalid",
        ),
    ],
)
async def test_get_river_section_raises_bad_value_for_rejected_code(
    serve: Serve, code: str, file: str, message: str
) -> None:
    client, requests = await serve(200, JSON_UTF8, recorded(file))

    with pytest.raises(VigicruesBadValueError) as error_info:
        await client.get_river_section(code)

    assert error_info.value.message == message
    assert error_info.value.code == 400
    assert len(requests) == 1


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(_payload(), id="no section"),
        pytest.param(
            _payload(
                {
                    "CdEntVigiCru": "MP10",
                    "LbEntVigiCru": "Garonne marmandaise",
                    "aNPlusUn": {"CdEntVigiCruSuperieur": "A renseigner"},
                    "aNMoinsUn": [],
                }
            ),
            id="other section without territory",
        ),
    ],
)
async def test_get_river_section_raises_unknown_value_without_territory_to_search(
    serve: Serve, body: bytes
) -> None:
    client, requests = await serve(200, JSON_UTF8, body)

    with pytest.raises(VigicruesUnknownValueError, match="Unknown river section 'MP1'"):
        await client.get_river_section("MP1")

    assert len(requests) == 1


async def test_get_river_section_maps_placeholders_to_none(serve: Serve) -> None:
    client, _ = await serve(
        200,
        JSON_UTF8,
        _payload(
            {
                "CdEntVigiCru": "AP16",
                "LbEntVigiCru": PLACEHOLDER,
                "aNPlusUn": {"CdEntVigiCruSuperieur": "A renseigner"},
                "aNMoinsUn": [
                    {
                        "CdEntVigiCruInferieur": PLACEHOLDER,
                        "LbEntVigiCruInferieur": PLACEHOLDER,
                    }
                ],
            }
        ),
    )

    section = await client.get_river_section("AP16")

    assert section == RiverSection(
        "AP16", None, None, (RiverSectionStation(None, None),)
    )


async def test_get_river_section_raises_on_invalid_payload(serve: Serve) -> None:
    client, _ = await serve(
        200,
        JSON_UTF8,
        _payload({"CdEntVigiCru": "AP16", "LbEntVigiCru": "Canche", "aNMoinsUn": []}),
    )

    with pytest.raises(VigicruesResponseError, match="object for aNPlusUn"):
        await client.get_river_section("AP16")


@pytest.mark.parametrize(
    "get_entity",
    [
        pytest.param(lambda client: client.get_territory("25"), id="territory"),
        pytest.param(
            lambda client: client.get_river_section("AP16"), id="river section"
        ),
    ],
)
async def test_referential_passes_other_api_errors(
    serve: Serve, get_entity: Callable[[VigicruesClient], Awaitable[object]]
) -> None:
    client, _ = await serve(
        200, JSON_UTF8, recorded("TronEntVigiCru_missing_type.json")
    )

    with pytest.raises(VigicruesApiError) as error_info:
        await get_entity(client)

    assert not isinstance(error_info.value, VigicruesBadValueError)
    assert error_info.value.message == "Problème d'exécution du process"


@pytest.mark.live
async def test_get_territory_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        territory = await client.get_territory("25")

    assert territory.name == "Garonne-Tarn-Lot"
    assert any(section.code == "MP18" for section in territory.river_sections)


@pytest.mark.live
async def test_get_river_section_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        section = await client.get_river_section("AP16")

    assert section.name == "Canche"
    assert section.territory_code == "29"


@pytest.mark.live
async def test_get_shadowed_river_section_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        section = await client.get_river_section("MP1")

    assert section.code == "MP1"
    assert section.territory_code == "25"
