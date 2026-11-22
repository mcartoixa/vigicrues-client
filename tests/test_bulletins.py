import re
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from vigicrues_client import (
    BulletinRiverSection,
    VigicruesBadValueError,
    VigicruesClient,
    VigicruesRateLimitError,
    VigicruesResponseError,
    VigicruesUnknownValueError,
    VigilanceLevel,
)

from .support import JSON_UTF8, Response, Serve, recorded

HTML_UTF8 = "text/html; charset=UTF-8"
PARIS = ZoneInfo("Europe/Paris")
BULLETIN_UNKNOWN = Response(500, "text/html", recorded("station_unknown.html"))
TERRITORY_PATH = "/services/v1.1/TerEntVigiCru.json"
NO_VIGILANCE = "Pas de vigilance particulière requise."

TIMES = (
    "<dt>Date de publication de l'information</dt><dd>22.11.2026 à 05h59</dd>"
    "<dt>Date de prochaine actualisation au plus tard</dt><dd>22.11.2026 à 10h00</dd>"
)
GENERAL_COMMENT = (
    f"<div><h2>Commentaire général sur la situation</h2><p>{NO_VIGILANCE}</p></div>"
)
NAME_CELL = '<td data-th="Tronçon"><strong>Canche</strong></td>'
COMMENTS_CELL = '<td data-th="Commentaires et prévisions"><div><p>Crue.</p></div></td>'


def _page(times: str = TIMES, content: str = GENERAL_COMMENT) -> bytes:
    """Return a bulletin page with the structure of the recorded ones."""
    return (
        f'<html><body><dl class="report-infos-list">{times}</dl>{content}</body></html>'
    ).encode()


def _row(attributes: str, cells: str = NAME_CELL + COMMENTS_CELL) -> str:
    return f"{GENERAL_COMMENT}<table><tr {attributes}>{cells}</tr></table>"


async def test_get_territory_bulletin_returns_orange_territory(serve: Serve) -> None:
    client, requests = await serve(200, HTML_UTF8, recorded("bulletin_local_29.html"))

    bulletin = await client.get_territory_bulletin("29")

    assert requests == ["/bulletin_local/29"]
    assert bulletin.territory_code == "29"
    assert bulletin.publication_time == datetime(2026, 11, 22, 5, 59, tzinfo=PARIS)
    # Same time as the production of the vigilance levels
    assert bulletin.publication_time == datetime(2026, 11, 22, 4, 59, tzinfo=UTC)
    assert bulletin.next_update_time == datetime(2026, 11, 22, 10, 0, tzinfo=PARIS)
    assert bulletin.situation == "Crue importante sur la Canche et l'Authie."
    # One <br /> between the lines; HTML entities decoded
    assert bulletin.general_comment.split("\n") == [
        "Les fortes précipitations qui ont touché le Pas-de-Calais et la Somme la"
        " semaine dernière ont entraîné des inondations très importantes sur la"
        " Canche et l'Authie.",
        "Un temps relativement sec est attendu pour ce week-end sur les tronçons en"
        " vigilance.",
        "Mais les niveaux sur la Canche et sur l'Authie vont rester hauts ce week-end.",
    ]
    assert len(bulletin.river_sections) == 23
    assert bulletin.river_sections[0] == BulletinRiverSection(
        "AP6", "Liane", VigilanceLevel.GREEN, (NO_VIGILANCE,)
    )
    canche = next(s for s in bulletin.river_sections if s.code == "AP16")
    assert canche.name == "Canche"
    assert canche.level is VigilanceLevel.ORANGE
    assert len(canche.comments) == 3
    assert canche.comments[1] == "Crue importante pour la saison sur la Canche."
    assert canche.comments[2].startswith(
        "Décrue sur la Course et la Ternoise. Les niveaux de la Canche à Brimeux sont"
        " à l'étale."
    )
    assert {
        s.code for s in bulletin.river_sections if s.level is not VigilanceLevel.GREEN
    } == {"AP16"}


async def test_get_territory_bulletin_returns_yellow_territory(serve: Serve) -> None:
    client, _ = await serve(200, HTML_UTF8, recorded("bulletin_local_18.html"))

    bulletin = await client.get_territory_bulletin("18")

    assert bulletin.situation == (
        "Crue habituelle pour la saisons, modérée avec débordements localement"
        " dommageables."
    )
    # Two <br /> between the paragraphs
    paragraphs = bulletin.general_comment.split("\n\n")
    assert len(paragraphs) == 4
    assert paragraphs[2] == (
        "Pour des informations plus détaillées, veuillez consulter les commentaires"
        " liés aux tronçons."
    )
    assert len(bulletin.river_sections) == 22
    assert {
        s.code: s.level
        for s in bulletin.river_sections
        if s.level is not VigilanceLevel.GREEN
    } == {
        "RS18": VigilanceLevel.YELLOW,
        "RS31": VigilanceLevel.YELLOW,
        "RS41": VigilanceLevel.YELLOW,
    }
    assert bulletin.river_sections[0].comments[2] == (
        "Pour suivre l'évolution de la situation, consulter les prévisions graphiques"
        " sur Vigicrues à la station de Belfort"
    )


async def test_get_territory_bulletin_returns_green_territory(serve: Serve) -> None:
    client, _ = await serve(200, HTML_UTF8, recorded("bulletin_local_25.html"))

    bulletin = await client.get_territory_bulletin("25")

    assert bulletin.publication_time == datetime(2026, 11, 21, 15, 55, tzinfo=PARIS)
    assert bulletin.next_update_time == datetime(2026, 11, 22, 10, 0, tzinfo=PARIS)
    assert bulletin.situation is None
    assert bulletin.general_comment == NO_VIGILANCE
    assert bulletin.river_sections == ()


async def test_get_territory_bulletin_reads_encoding_from_page(serve: Serve) -> None:
    # Without charset in the response, the page's <meta charset="utf-8"> applies
    client, _ = await serve(200, "text/html", recorded("bulletin_local_25.html"))

    bulletin = await client.get_territory_bulletin("25")

    assert bulletin.general_comment == NO_VIGILANCE


@pytest.mark.parametrize(
    ("territory", "referential", "error_type", "match"),
    [
        pytest.param(
            "99",
            "TerEntVigiCru_unknown.json",
            VigicruesBadValueError,
            "Code d'entité de vigilance crues inconnu.",
            id="rejected",
        ),
        pytest.param(
            "0",
            "TerEntVigiCru_0.json",
            VigicruesUnknownValueError,
            "Unknown territory '0'",
            id="not sent",
        ),
    ],
)
async def test_get_territory_bulletin_raises_referential_error_for_unknown_territory(
    serve: Serve,
    territory: str,
    referential: str,
    error_type: type[Exception],
    match: str,
) -> None:
    client, requests = await serve(
        *BULLETIN_UNKNOWN,
        routes={TERRITORY_PATH: Response(200, JSON_UTF8, recorded(referential))},
    )

    with pytest.raises(error_type, match=match) as error_info:
        await client.get_territory_bulletin(territory)

    assert isinstance(error_info.value.__cause__, VigicruesResponseError)
    assert requests == [
        f"/bulletin_local/{territory}",
        f"{TERRITORY_PATH}?CdEntVigiCru={territory}&TypEntVigiCru=5",
    ]


@pytest.mark.parametrize(
    "referential",
    [
        pytest.param(
            Response(200, JSON_UTF8, recorded("TerEntVigiCru_25.json")),
            id="known territory",
        ),
        pytest.param(BULLETIN_UNKNOWN, id="referential down too"),
    ],
)
async def test_get_territory_bulletin_raises_original_error_for_known_territory(
    serve: Serve, referential: Response
) -> None:
    client, _ = await serve(*BULLETIN_UNKNOWN, routes={TERRITORY_PATH: referential})

    with pytest.raises(VigicruesResponseError, match="HTTP status 500"):
        await client.get_territory_bulletin("25")


async def test_get_territory_bulletin_raises_rate_limit_from_referential(
    serve: Serve,
) -> None:
    client, _ = await serve(
        *BULLETIN_UNKNOWN, routes={TERRITORY_PATH: Response(429, "text/html", b"")}
    )

    with pytest.raises(VigicruesRateLimitError):
        await client.get_territory_bulletin("99")


async def test_get_territory_bulletin_raises_on_other_content_type(
    serve: Serve,
) -> None:
    client, _ = await serve(200, JSON_UTF8, recorded("TerEntVigiCru_25.json"))

    with pytest.raises(VigicruesResponseError, match="Unexpected content type"):
        await client.get_territory_bulletin("25")


@pytest.mark.parametrize(
    ("body", "match"),
    [
        pytest.param(_page(content=""), "no general comment", id="no general comment"),
        pytest.param(
            _page(content="<div><h2>Commentaire général sur la situation</h2></div>"),
            "no text for 'Commentaire général",
            id="heading without text",
        ),
        pytest.param(
            _page(times=TIMES.split("<dt>Date de prochaine")[0]),
            "no 'Date de prochaine actualisation",
            id="no next update",
        ),
        pytest.param(
            _page(times=TIMES.replace("22.11.2026 à 05h59", "22/11/2026 05:59")),
            "is '22/11/2026 05:59'",
            id="time format",
        ),
        pytest.param(
            _page(times=TIMES.replace("22.11.2026 à 05h59", "32.11.2026 à 05h59")),
            "is '32.11.2026 à 05h59'",
            id="invalid date",
        ),
        pytest.param(
            _page(times=f"{TIMES}<dt>Autre date</dt>"),
            "publication times",
            id="time without value",
        ),
        pytest.param(
            _page(content=_row('class="vic-link-target green"')),
            "river section without code",
            id="section without code",
        ),
        pytest.param(
            _page(content=_row('id="AP16" class="vic-link-target purple"')),
            "level of river section 'AP16'",
            id="unknown level",
        ),
        pytest.param(
            _page(
                content=_row('id="AP16" class="vic-link-target orange"', COMMENTS_CELL)
            ),
            "name of river section 'AP16'",
            id="section without name",
        ),
        pytest.param(
            _page(content=_row('id="AP16" class="vic-link-target orange"', NAME_CELL)),
            "comments of river section 'AP16'",
            id="section without comments",
        ),
        pytest.param(
            _page(
                content="<div><h2>Qualification de la situation</h2><p>Crue.</p></div>"
                + GENERAL_COMMENT
            ),
            "situation without river sections",
            id="situation without sections",
        ),
    ],
)
async def test_get_territory_bulletin_raises_on_unexpected_structure(
    serve: Serve, body: bytes, match: str
) -> None:
    client, _ = await serve(200, HTML_UTF8, body)

    with pytest.raises(
        VigicruesResponseError,
        match=f"^Unexpected bulletin page structure: .*{re.escape(match)}",
    ):
        await client.get_territory_bulletin("29")


async def test_get_territory_bulletin_parses_synthesized_page(serve: Serve) -> None:
    # Guards the synthesized pages above: valid unless broken on purpose
    client, _ = await serve(
        200, HTML_UTF8, _page(content=_row('id="AP16" class="vic-link-target red"'))
    )

    bulletin = await client.get_territory_bulletin("29")

    assert bulletin.river_sections == (
        BulletinRiverSection("AP16", "Canche", VigilanceLevel.RED, ("Crue.",)),
    )


@pytest.mark.live
async def test_get_territory_bulletin_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        bulletin = await client.get_territory_bulletin("29")

    assert bulletin.publication_time.tzinfo is not None
    assert bulletin.general_comment


@pytest.mark.live
async def test_get_territory_bulletin_raises_bad_value_from_vigicrues() -> None:
    async with VigicruesClient() as client:
        with pytest.raises(VigicruesBadValueError):
            await client.get_territory_bulletin("99")
