"""Territory bulletins, from the HTML page `/bulletin_local/{territory}`."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from ._errors import VigicruesResponseError
from ._models import BulletinRiverSection, TerritoryBulletin, VigilanceLevel

# "Toutes les heures mentionnées sont des heures légales métropolitaine."
_PAGE_TIME_ZONE = ZoneInfo("Europe/Paris")
_PAGE_TIME = re.compile(r"(\d{2})\.(\d{2})\.(\d{4}) à (\d{2})h(\d{2})")
_SPACES = re.compile(r"\s+")

_LEVELS = {
    "green": VigilanceLevel.GREEN,
    "yellow": VigilanceLevel.YELLOW,
    "orange": VigilanceLevel.ORANGE,
    "red": VigilanceLevel.RED,
}


def parse_territory_bulletin(
    territory: str, body: bytes, encoding: str | None
) -> TerritoryBulletin:
    """Parse the page of the bulletin of a territory.

    Raises:
        VigicruesResponseError: The page does not have the expected structure.
    """
    page = BeautifulSoup(body, "html.parser", from_encoding=encoding)
    times = _parse_times(page)
    situation = _find_heading_text(page, "Qualification de la situation")
    general_comment = _find_heading_text(page, "Commentaire général sur la situation")
    if general_comment is None:
        raise _structure_error("no general comment")
    river_sections = tuple(
        _parse_river_section(row) for row in page.select("tr.vic-link-target")
    )
    # Only a page with nothing in vigilance has no river sections, and no situation:
    # an empty list must be safe to read as "all green".
    if situation is not None and not river_sections:
        raise _structure_error("situation without river sections")
    return TerritoryBulletin(
        territory_code=territory,
        publication_time=_get_time(times, "Date de publication de l'information"),
        next_update_time=_get_time(
            times, "Date de prochaine actualisation au plus tard"
        ),
        situation=situation,
        general_comment=general_comment,
        river_sections=river_sections,
    )


def _parse_times(page: BeautifulSoup) -> dict[str, str]:
    """Return the texts of the publication times, by label."""
    terms = page.select("dl.report-infos-list > dt")
    definitions = page.select("dl.report-infos-list > dd")
    if len(terms) != len(definitions):
        raise _structure_error("publication times")
    return {
        _get_text(term): _get_text(definition)
        for term, definition in zip(terms, definitions, strict=True)
    }


def _get_time(times: dict[str, str], label: str) -> datetime:
    text = times.get(label)
    if text is None:
        raise _structure_error(f"no {label!r}")
    match = _PAGE_TIME.fullmatch(text)
    if match is None:
        raise _structure_error(f"{label!r} is {text!r}")
    day, month, year, hour, minute = (int(group) for group in match.groups())
    try:
        # During the autumn change, an ambiguous time is taken as the first one.
        return datetime(year, month, day, hour, minute, tzinfo=_PAGE_TIME_ZONE)
    except ValueError as error:
        raise _structure_error(f"{label!r} is {text!r}") from error


def _find_heading_text(page: BeautifulSoup, heading_text: str) -> str | None:
    """Return the paragraphs next to a heading, or `None` without the heading."""
    for container in page.select(":has(> h2)"):
        headings = container.select(":scope > h2")
        if any(_get_text(heading) == heading_text for heading in headings):
            paragraphs = container.select(":scope > p")
            if not paragraphs:
                raise _structure_error(f"no text for {heading_text!r}")
            return "\n\n".join(_get_text(paragraph) for paragraph in paragraphs)
    return None


def _parse_river_section(row: Tag) -> BulletinRiverSection:
    code = row.get("id")
    if not isinstance(code, str):
        raise _structure_error("river section without code")
    levels = [
        _LEVELS[name] for name in row.get_attribute_list("class") if name in _LEVELS
    ]
    if len(levels) != 1:
        raise _structure_error(f"level of river section {code!r}")
    name = row.select_one('td[data-th="Tronçon"]')
    if name is None:
        raise _structure_error(f"name of river section {code!r}")
    comments = row.select('td[data-th="Commentaires et prévisions"] p')
    if not comments:
        raise _structure_error(f"comments of river section {code!r}")
    return BulletinRiverSection(
        code=code,
        name=_get_text(name),
        level=levels[0],
        comments=tuple(_get_text(comment) for comment in comments),
    )


def _get_text(element: Tag) -> str:
    """Return the text of an element: `<br>` as line breaks, spaces collapsed."""
    parts: list[str] = []
    for descendant in element.descendants:
        if isinstance(descendant, Tag) and descendant.name == "br":
            parts.append("\n")
        elif type(descendant) is NavigableString:
            # Line breaks in the source are mere spaces in HTML.
            parts.append(_SPACES.sub(" ", descendant))
    lines = (line.strip(" ") for line in "".join(parts).split("\n"))
    return "\n".join(lines).strip("\n")


def _structure_error(detail: str) -> VigicruesResponseError:
    return VigicruesResponseError(f"Unexpected bulletin page structure: {detail}")
