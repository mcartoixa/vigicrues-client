"""Entities sent by the v1.1 referential (`TerEntVigiCru`, `TronEntVigiCru`...)."""

from ._models import (
    RiverSection,
    RiverSectionStation,
    RiverSectionSummary,
    StationSummary,
    Territory,
    TerritoryRiverSection,
    TerritorySummary,
)
from ._payload import as_object, get_list, get_object, get_optional_str, get_str


def get_entities(data: object) -> list[dict[str, object]]:
    """Return the entities of a referential response."""
    return [
        as_object(item, "ListEntVigiCru item")
        for item in get_list(as_object(data, "response"), "ListEntVigiCru")
    ]


def find_entity(
    entities: list[dict[str, object]], code: str
) -> dict[str, object] | None:
    """Return the entity with the given code, if any."""
    return next(
        (entity for entity in entities if get_str(entity, "CdEntVigiCru") == code),
        None,
    )


def parse_territory(entity: dict[str, object]) -> Territory:
    """Parse a territory with its river sections."""
    return Territory(
        code=get_str(entity, "CdEntVigiCru"),
        name=get_optional_str(entity, "LbEntVigiCru"),
        river_sections=tuple(
            TerritoryRiverSection(
                code=get_optional_str(child, "CdEntVigiCruInferieur"),
                name=get_optional_str(child, "LbEntVigiCruInferieur"),
            )
            for child in _get_children(entity)
        ),
    )


def parse_river_section(entity: dict[str, object]) -> RiverSection:
    """Parse a river section with its parent territory and its stations."""
    return RiverSection(
        code=get_str(entity, "CdEntVigiCru"),
        name=get_optional_str(entity, "LbEntVigiCru"),
        territory_code=get_optional_str(
            get_object(entity, "aNPlusUn"), "CdEntVigiCruSuperieur"
        ),
        stations=tuple(
            RiverSectionStation(
                code=get_optional_str(child, "CdEntVigiCruInferieur"),
                name=get_optional_str(child, "LbEntVigiCruInferieur"),
            )
            for child in _get_children(entity)
        ),
    )


def parse_territory_summary(entity: dict[str, object]) -> TerritorySummary:
    """Parse a territory of the list of all the territories."""
    return TerritorySummary(
        code=get_str(entity, "CdEntVigiCru"),
        name=get_optional_str(entity, "LbEntVigiCru"),
    )


def parse_river_section_summary(entity: dict[str, object]) -> RiverSectionSummary:
    """Parse a river section of the list of all the river sections."""
    return RiverSectionSummary(
        code=get_str(entity, "CdEntVigiCru"),
        name=get_optional_str(entity, "LbEntVigiCru"),
    )


def parse_station_summary(entity: dict[str, object]) -> StationSummary:
    """Parse a station of the list of all the stations."""
    return StationSummary(
        code=get_str(entity, "CdEntVigiCru"),
        name=get_optional_str(entity, "LbEntVigiCru"),
        river=get_optional_str(entity, "LbCoursEau"),
    )


def _get_children(entity: dict[str, object]) -> list[dict[str, object]]:
    return [as_object(item, "aNMoinsUn item") for item in get_list(entity, "aNMoinsUn")]
