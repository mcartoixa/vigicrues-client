"""Asynchronous Python client for Vigicrues, the French flood vigilance service."""

from ._client import VigicruesClient
from ._errors import (
    VigicruesApiError,
    VigicruesConnectionError,
    VigicruesError,
    VigicruesRateLimitError,
    VigicruesResponseError,
)
from ._models import Quantity, VigilanceLevel

__all__ = [
    "Quantity",
    "VigicruesApiError",
    "VigicruesClient",
    "VigicruesConnectionError",
    "VigicruesError",
    "VigicruesRateLimitError",
    "VigicruesResponseError",
    "VigilanceLevel",
]
