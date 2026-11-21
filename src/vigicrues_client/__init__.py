"""Asynchronous Python client for Vigicrues, the French flood vigilance service."""

from ._client import VigicruesClient
from ._errors import (
    VigicruesApiError,
    VigicruesConnectionError,
    VigicruesError,
    VigicruesNotFoundError,
    VigicruesRateLimitError,
    VigicruesResponseError,
)
from ._models import (
    BasinStation,
    HistoricalFlood,
    Observation,
    ObservationSeries,
    Quantity,
    Station,
    VigilanceLevel,
)

__all__ = [
    "BasinStation",
    "HistoricalFlood",
    "Observation",
    "ObservationSeries",
    "Quantity",
    "Station",
    "VigicruesApiError",
    "VigicruesClient",
    "VigicruesConnectionError",
    "VigicruesError",
    "VigicruesNotFoundError",
    "VigicruesRateLimitError",
    "VigicruesResponseError",
    "VigilanceLevel",
]
