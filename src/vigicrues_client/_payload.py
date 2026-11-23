"""Typed access to the JSON values sent by the Vigicrues service."""

from ._errors import VigicruesResponseError
from ._models import Quantity

# Sent by the referential in place of the values it does not have.
_PLACEHOLDERS = frozenset({"A renseigner obligatoirement", "A renseigner"})


def as_object(value: object, name: str) -> dict[str, object]:
    """Return `value` as a JSON object, `name` describing it in errors."""
    if not isinstance(value, dict):
        raise VigicruesResponseError(
            f"Expected an object for {name}, got {value!r:.80}"
        )
    return value


def get_object(parent: dict[str, object], key: str) -> dict[str, object]:
    """Return the JSON object `parent[key]`."""
    return as_object(parent.get(key), key)


def get_list(parent: dict[str, object], key: str) -> list[object]:
    """Return the JSON array `parent[key]`."""
    value = parent.get(key)
    if not isinstance(value, list):
        raise VigicruesResponseError(f"Expected an array for {key}, got {value!r:.80}")
    return value


def get_str(parent: dict[str, object], key: str) -> str:
    """Return the JSON string `parent[key]`."""
    value = parent.get(key)
    if not isinstance(value, str):
        raise VigicruesResponseError(f"Expected a string for {key}, got {value!r:.80}")
    return value


def get_quantity(parent: dict[str, object], key: str) -> Quantity:
    """Return the quantity whose code is the JSON string `parent[key]`."""
    code = get_str(parent, key)
    try:
        return Quantity(code)
    except ValueError as error:
        raise VigicruesResponseError(f"Unknown quantity {code!r}") from error


def get_optional_str(parent: dict[str, object], key: str) -> str | None:
    """Return the JSON string `parent[key]`, or `None` for a placeholder value."""
    value = get_str(parent, key)
    return None if value in _PLACEHOLDERS else value


def get_bool(parent: dict[str, object], key: str) -> bool:
    """Return the JSON boolean `parent[key]`."""
    value = parent.get(key)
    if not isinstance(value, bool):
        raise VigicruesResponseError(f"Expected a boolean for {key}, got {value!r:.80}")
    return value


def get_int(parent: dict[str, object], key: str) -> int:
    """Return the JSON integer `parent[key]`."""
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise VigicruesResponseError(
            f"Expected an integer for {key}, got {value!r:.80}"
        )
    return value


def get_number(parent: dict[str, object], key: str) -> float:
    """Return the JSON number `parent[key]`, integer or not."""
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise VigicruesResponseError(f"Expected a number for {key}, got {value!r:.80}")
    return float(value)
