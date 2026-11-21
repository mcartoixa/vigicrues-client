"""Observations sent by `observations.json`."""

from ._errors import VigicruesResponseError
from ._models import Observation, ObservationSeries, Quantity
from ._payload import as_object, get_list, get_number, get_object, get_str
from ._time import parse_datetime


def parse_observation_series(data: object) -> ObservationSeries:
    """Parse the response of `observations.json`."""
    series = get_object(as_object(data, "response"), "Serie")
    quantity_code = get_str(series, "GrdSerie")
    try:
        quantity = Quantity(quantity_code)
    except ValueError as error:
        raise VigicruesResponseError(f"Unknown quantity {quantity_code!r}") from error
    observations = [
        _parse_observation(as_object(item, "ObssHydro item"))
        for item in get_list(series, "ObssHydro")
    ]
    return ObservationSeries(
        station_code=get_str(series, "CdStationHydro"),
        station_name=get_str(series, "LbStationHydro"),
        quantity=quantity,
        observations=tuple(sorted(observations, key=lambda o: o.time)),
    )


def _parse_observation(item: dict[str, object]) -> Observation:
    return Observation(
        time=parse_datetime(item.get("DtObsHydro")),
        value=get_number(item, "ResObsHydro"),
    )
