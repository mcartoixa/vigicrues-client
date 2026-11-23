"""Forecasts sent by `prevision.json`."""

from ._models import Forecast, ForecastPoint
from ._payload import as_object, get_list, get_number, get_object, get_quantity, get_str
from ._time import parse_datetime

# Sent with code 204 when there is no forecast for the station: none at the moment,
# not a forecast station, unknown or invalid station code.
NO_FORECAST_MESSAGES = frozenset(
    {
        "Problème dans l'exécution de la requête : prévision",
        "Cette station n'est pas une station de prévisions",
        "Code de station inconnu",
    }
)


def parse_forecast(data: object) -> Forecast:
    """Parse the response of `prevision.json`."""
    simul = get_object(as_object(data, "response"), "Simul")
    points = [
        _parse_point(as_object(item, "Prevs item")) for item in get_list(simul, "Prevs")
    ]
    return Forecast(
        station_code=get_str(simul, "CdEntVigiCru"),
        station_name=get_str(simul, "LbEntVigiCru"),
        quantity=get_quantity(simul, "GrdSimul"),
        production_time=parse_datetime(simul.get("DtProdSimul")),
        comment=get_str(simul, "CommentSimul"),
        points=tuple(sorted(points, key=lambda p: p.time)),
    )


def _parse_point(item: dict[str, object]) -> ForecastPoint:
    return ForecastPoint(
        time=parse_datetime(item.get("DtPrev")),
        low=get_number(item, "ResMinPrev"),
        central=get_number(item, "ResMoyPrev"),
        high=get_number(item, "ResMaxPrev"),
    )
