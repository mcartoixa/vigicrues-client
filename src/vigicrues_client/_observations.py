"""Observations sent by `observations.json`."""

from ._models import Observation, ObservationSeries
from ._payload import as_object, get_list, get_number, get_object, get_quantity, get_str
from ._time import parse_datetime


def parse_observation_series(data: object) -> ObservationSeries:
    """Parse the response of `observations.json`."""
    series = get_object(as_object(data, "response"), "Serie")
    observations = [
        _parse_observation(as_object(item, "ObssHydro item"))
        for item in get_list(series, "ObssHydro")
    ]
    return ObservationSeries(
        station_code=get_str(series, "CdStationHydro"),
        station_name=get_str(series, "LbStationHydro"),
        quantity=get_quantity(series, "GrdSerie"),
        observations=tuple(sorted(observations, key=lambda o: o.time)),
    )


def _parse_observation(item: dict[str, object]) -> Observation:
    return Observation(
        time=parse_datetime(item.get("DtObsHydro")),
        value=get_number(item, "ResObsHydro"),
    )
