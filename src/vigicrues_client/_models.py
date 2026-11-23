"""Domain types of the Vigicrues service."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum


class Quantity(StrEnum):
    """Hydrometric quantity measured or forecast at a station.

    Values are the service's codes (`GrdSerie`, `GrdSimul`).

    Attributes:
        HEIGHT: Water height, in metres.
        FLOW: Flow rate, in cubic metres per second.
    """

    HEIGHT = "H"
    FLOW = "Q"


class VigilanceLevel(IntEnum):
    """Flood vigilance level of a river section, from the lowest to the highest.

    Values are the service's codes (`NivInfViCr`), so levels can be compared:
    `level >= VigilanceLevel.ORANGE`.
    """

    GREEN = 1
    YELLOW = 2
    ORANGE = 3
    RED = 4


class EntityType(StrEnum):
    """Type of a flood vigilance entity, as the service's `TypEntVigiCru` parameter."""

    TERRITORY = "5"
    STATION = "7"
    RIVER_SECTION = "8"


@dataclass(frozen=True, slots=True)
class Observation:
    """Value observed at a station at a given time.

    Attributes:
        time: Time of the observation, with the offset sent by the service (UTC).
        value: Observed value, in the unit of the series quantity.
    """

    time: datetime
    value: float


@dataclass(frozen=True, slots=True)
class ObservationSeries:
    """Recent values of a quantity observed at a station.

    Attributes:
        station_code: Code of the hydrometric station, e.g. `"O262002001"`.
        station_name: Name of the station, as sent by the service, e.g. `"Verdun [HE]"`.
        quantity: Observed quantity.
        observations: Observations, from the oldest to the latest.
    """

    station_code: str
    station_name: str
    quantity: Quantity
    observations: tuple[Observation, ...]

    @property
    def latest(self) -> Observation | None:
        """Latest observation, or `None` if the series is empty."""
        return self.observations[-1] if self.observations else None


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """Values forecast at a station for a given time, as three trends.

    The observed value may lie outside of the range between the low and high
    trends.

    Attributes:
        time: Time of the forecast, with the offset sent by the service (local
            time).
        low: Low trend: 9 chances in 10 of being exceeded.
        central: Central trend: 5 chances in 10 of being exceeded.
        high: High trend: 1 chance in 10 of being exceeded.
    """

    time: datetime
    low: float
    central: float
    high: float


@dataclass(frozen=True, slots=True)
class Forecast:
    """Forecast of a quantity at a station, after its latest observation.

    Attributes:
        station_code: Code of the hydrometric station, e.g. `"E540031001"`.
        station_name: Name of the station, as sent by the service, e.g. `"Brimeux"`.
        quantity: Forecast quantity.
        production_time: Time the forecast was produced, with the offset sent by
            the service (local time).
        comment: Comment sent with the forecast, in French, e.g. how to read the
            trends and when the forecast was made.
        points: Forecast values, from the earliest to the latest time.
    """

    station_code: str
    station_name: str
    quantity: Quantity
    production_time: datetime
    comment: str
    points: tuple[ForecastPoint, ...]


@dataclass(frozen=True, slots=True)
class HistoricalFlood:
    """Past flood recorded at a station.

    Attributes:
        name: Name of the flood, as sent by the service, e.g. `"Crue de mars 2020"`.
        height: Highest water height, in metres.
        flow: Highest flow rate, in cubic metres per second, or `None` if not known.
    """

    name: str
    height: float
    flow: float | None


@dataclass(frozen=True, slots=True)
class BasinStation:
    """Another station of the same river basin.

    Attributes:
        code: Code of the hydrometric station, e.g. `"E541000401"`.
        name: Name of the station, as sent by the service, e.g. `"Beutin"`.
        river: Name of the river, e.g. `"Canche"`.
    """

    code: str
    name: str
    river: str


@dataclass(frozen=True, slots=True)
class Station:
    """Hydrometric station of the flood vigilance network.

    Attributes:
        code: Code of the hydrometric station, e.g. `"E540031001"`.
        name: Name of the station, as sent by the service, e.g. `"Brimeux"`.
        river: Name of the river, e.g. `"Canche"`.
        commune_code: INSEE code of the commune, e.g. `"62177"`.
        territory_code: Code of the flood vigilance territory, e.g. `"29"`.
        is_forecast_station: Whether the service publishes forecasts for the
            station (not necessarily at all times).
        historical_floods: Notable past floods, in the order sent by the service.
        basin_stations: Other stations of the same river basin.
    """

    code: str
    name: str
    river: str
    commune_code: str
    territory_code: str
    is_forecast_station: bool
    historical_floods: tuple[HistoricalFlood, ...]
    basin_stations: tuple[BasinStation, ...]


@dataclass(frozen=True, slots=True)
class TerritoryRiverSection:
    """River section of a flood vigilance territory.

    Values the service does not have are `None`.

    Attributes:
        code: Code of the river section, e.g. `"MP18"`.
        name: Name of the river section, e.g. `"Garonne toulousaine"`.
    """

    code: str | None
    name: str | None


@dataclass(frozen=True, slots=True)
class Territory:
    """Flood vigilance territory, monitored by one flood forecasting service.

    Values the service does not have are `None`.

    Attributes:
        code: Code of the territory, e.g. `"25"`.
        name: Name of the territory, e.g. `"Garonne-Tarn-Lot"`.
        river_sections: River sections of the territory, in the order sent by the
            service.
    """

    code: str
    name: str | None
    river_sections: tuple[TerritoryRiverSection, ...]


@dataclass(frozen=True, slots=True)
class RiverSectionStation:
    """Hydrometric station of a river section.

    Values the service does not have are `None`.

    Attributes:
        code: Code of the hydrometric station, e.g. `"E540031001"`.
        name: Name of the station, as sent by the service, e.g. `"Brimeux"`.
    """

    code: str | None
    name: str | None


@dataclass(frozen=True, slots=True)
class RiverSection:
    """River section, the unit that flood vigilance levels apply to.

    Values the service does not have are `None`.

    Attributes:
        code: Code of the river section, e.g. `"AP16"`.
        name: Name of the river section, e.g. `"Canche"`.
        territory_code: Code of the flood vigilance territory, e.g. `"29"`.
        stations: Stations of the river section, in the order sent by the service.
    """

    code: str
    name: str | None
    territory_code: str | None
    stations: tuple[RiverSectionStation, ...]


@dataclass(frozen=True, slots=True)
class VigilanceLevels:
    """Current flood vigilance levels of the river sections of metropolitan France.

    Attributes:
        time: Production time of the levels, with the offset sent by the service
            (UTC).
        levels: Vigilance level of each river section, by river section code, e.g.
            `"AP16"`.
    """

    time: datetime
    levels: Mapping[str, VigilanceLevel]


@dataclass(frozen=True, slots=True)
class BulletinRiverSection:
    """Vigilance of a river section, as described in the bulletin of its territory.

    Attributes:
        code: Code of the river section, e.g. `"AP16"`.
        name: Name of the river section, e.g. `"Canche"`.
        level: Vigilance level of the river section.
        comments: Comments and forecasts, in French, one per paragraph, e.g.
            `("Pas de vigilance particulière requise.",)`.
    """

    code: str
    name: str
    level: VigilanceLevel
    comments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerritoryBulletin:
    """Flood vigilance bulletin of a territory.

    Texts are in French, with their line breaks.

    Attributes:
        territory_code: Code of the territory, e.g. `"29"`.
        publication_time: Publication time, in metropolitan France local time.
        next_update_time: Time of the next publication at the latest, in
            metropolitan France local time.
        situation: Qualification of the situation, or `None` when no river section
            of the territory is in vigilance.
        general_comment: General comment on the situation, e.g.
            `"Pas de vigilance particulière requise."`.
        river_sections: River sections of the territory, in the order of the
            bulletin. Empty when no river section of the territory is in
            vigilance.
    """

    territory_code: str
    publication_time: datetime
    next_update_time: datetime
    situation: str | None
    general_comment: str
    river_sections: tuple[BulletinRiverSection, ...]


@dataclass(frozen=True, slots=True)
class RiverSectionVigilance:
    """Current flood vigilance of a river section, from the bulletin of its territory.

    Attributes:
        section: The river section, with its territory and stations.
        level: Vigilance level of the river section.
        comments: Comments and forecasts on the river section, in French, one per
            paragraph. Empty when no river section of the territory is in
            vigilance: see the general comment of the bulletin.
        bulletin: Bulletin of the territory: publication times, territory texts.
    """

    section: RiverSection
    level: VigilanceLevel
    comments: tuple[str, ...]
    bulletin: TerritoryBulletin
