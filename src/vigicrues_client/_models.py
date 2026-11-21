"""Domain types of the Vigicrues service."""

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
