"""Dates sent by the Vigicrues service."""

from datetime import datetime

from ._errors import VigicruesResponseError


def parse_datetime(value: object) -> datetime:
    """Parse an ISO 8601 date and time with an offset, as sent with `FormatDate=iso`.

    The offset is kept as sent: UTC for observations, local time for forecasts.

    Raises:
        VigicruesResponseError: The value is not an ISO 8601 date and time with an
            offset.
    """
    if not isinstance(value, str):
        raise VigicruesResponseError(f"Expected a date and time, got {value!r}")
    try:
        result = datetime.fromisoformat(value)
    except ValueError as error:
        raise VigicruesResponseError(f"Invalid date and time {value!r}") from error
    if result.tzinfo is None:
        raise VigicruesResponseError(f"Date and time without offset {value!r}")
    return result
