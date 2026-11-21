from datetime import UTC, datetime, timedelta

import pytest

from vigicrues_client import VigicruesResponseError
from vigicrues_client._time import parse_datetime


def test_parse_datetime_keeps_utc_offset() -> None:
    # DtObsHydro in observations.json
    result = parse_datetime("2026-10-20T22:05:00+00:00")

    assert result == datetime(2026, 10, 20, 22, 5, tzinfo=UTC)
    assert result.utcoffset() == timedelta(0)


def test_parse_datetime_keeps_local_offset() -> None:
    # DtProdSimul in v1.1 prevision.json
    result = parse_datetime("2026-11-21T05:25:13+01:00")

    assert result.utcoffset() == timedelta(hours=1)


def test_parse_datetime_same_instant_with_utc_and_local_offsets() -> None:
    # The same forecast production time, from v1.1 prevision.json and previsions.json
    assert parse_datetime("2026-11-21T05:25:13+01:00") == parse_datetime(
        "2026-11-21T04:25:13+00:00"
    )


@pytest.mark.parametrize(
    ("value", "match"),
    [
        pytest.param("2026-11-21T10:00:00", "without offset", id="no offset"),
        pytest.param("21.11.2026 à 09h56", "Invalid date", id="bulletin format"),
        pytest.param(1795278478040, "Expected a date", id="milliseconds"),
        pytest.param(None, "Expected a date", id="missing"),
    ],
)
def test_parse_datetime_rejects_unexpected_values(value: object, match: str) -> None:
    with pytest.raises(VigicruesResponseError, match=match):
        parse_datetime(value)
