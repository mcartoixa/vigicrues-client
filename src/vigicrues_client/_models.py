"""Domain types of the Vigicrues service."""

from enum import IntEnum, StrEnum


class Quantity(StrEnum):
    """Hydrometric quantity measured or forecast at a station.

    Values are the service's codes (`GrdSerie`, `GrdSimul`).

    Attributes:
        HEIGHT: Water height, in metres.
        FLOW: Flow rate.
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
