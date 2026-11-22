"""Vigilance levels sent by `InfoVigiCru.geojson`."""

from ._errors import VigicruesResponseError
from ._models import VigilanceLevel, VigilanceLevels
from ._payload import as_object, get_int, get_list, get_object, get_str
from ._time import parse_datetime


def parse_vigilance_levels(data: object) -> VigilanceLevels:
    """Parse the response of `InfoVigiCru.geojson`, ignoring the geometries."""
    collection = as_object(data, "response")
    sections = [
        get_object(as_object(feature, "features item"), "properties")
        for feature in get_list(collection, "features")
    ]
    return VigilanceLevels(
        time=parse_datetime(collection.get("DtHrInfoVigiCru")),
        levels={
            get_str(section, "CdEntCru"): _parse_level(section) for section in sections
        },
    )


def _parse_level(section: dict[str, object]) -> VigilanceLevel:
    level = get_int(section, "NivInfViCr")
    try:
        return VigilanceLevel(level)
    except ValueError as error:
        raise VigicruesResponseError(f"Unknown vigilance level {level!r}") from error
