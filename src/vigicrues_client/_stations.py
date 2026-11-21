"""Station details sent by `station.json`."""

from ._models import BasinStation, HistoricalFlood, Station
from ._payload import as_object, get_bool, get_list, get_number, get_object, get_str


def parse_station(data: object) -> Station:
    """Parse the response of `station.json`."""
    station = as_object(data, "response")
    vigilance = get_object(station, "VigilanceCrues")
    return Station(
        code=get_str(station, "CdStationHydro"),
        name=get_str(station, "LbStationHydro"),
        river=get_str(station, "LbCoursEau"),
        commune_code=get_str(station, "CdCommune"),
        territory_code=get_str(
            get_object(vigilance, "PereBoitEntVigiCru"), "CdEntVigiCru"
        ),
        is_forecast_station=get_bool(vigilance, "StationPrevision"),
        historical_floods=tuple(
            _parse_historical_flood(as_object(item, "CruesHistoriques item"))
            for item in get_list(vigilance, "CruesHistoriques")
        ),
        basin_stations=tuple(
            _parse_basin_station(as_object(item, "StationsBassin item"))
            for item in get_list(vigilance, "StationsBassin")
        ),
    )


def _parse_historical_flood(item: dict[str, object]) -> HistoricalFlood:
    flow = get_number(item, "ValDebit")
    return HistoricalFlood(
        name=get_str(item, "LbUsuel"),
        height=get_number(item, "ValHauteur"),
        # The service sends 0 when the flow rate of the flood is not known.
        flow=None if flow == 0 else flow,
    )


def _parse_basin_station(item: dict[str, object]) -> BasinStation:
    return BasinStation(
        code=get_str(item, "CdStationHydro"),
        name=get_str(item, "LbStationHydro"),
        river=get_str(item, "LbCoursEau"),
    )
