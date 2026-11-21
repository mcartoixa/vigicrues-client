import pytest

from vigicrues_client import Quantity, VigilanceLevel


@pytest.mark.parametrize(
    ("code", "quantity"), [("H", Quantity.HEIGHT), ("Q", Quantity.FLOW)]
)
def test_quantity_from_service_code(code: str, quantity: Quantity) -> None:
    assert Quantity(code) is quantity


@pytest.mark.parametrize(
    ("code", "level"),
    [
        (1, VigilanceLevel.GREEN),
        (2, VigilanceLevel.YELLOW),
        (3, VigilanceLevel.ORANGE),
        (4, VigilanceLevel.RED),
    ],
)
def test_vigilance_level_from_service_code(code: int, level: VigilanceLevel) -> None:
    assert VigilanceLevel(code) is level


def test_vigilance_levels_are_ordered() -> None:
    assert (
        VigilanceLevel.GREEN
        < VigilanceLevel.YELLOW
        < VigilanceLevel.ORANGE
        < VigilanceLevel.RED
    )
