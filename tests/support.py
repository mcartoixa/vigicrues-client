"""Helpers for the tests: recorded Vigicrues responses, served by a local server."""

from collections.abc import Awaitable, Mapping
from pathlib import Path
from typing import NamedTuple, Protocol

from vigicrues_client import VigicruesClient

RESPONSES_PATH = Path(__file__).parent / "responses"

# Content type of most recorded responses: see responses/README.md
JSON_UTF8 = "application/json;charset=UTF-8"


def recorded(file: str) -> bytes:
    """Return the body of a recorded response."""
    return (RESPONSES_PATH / file).read_bytes()


class Response(NamedTuple):
    """Response of the local server."""

    status: int
    content_type: str
    body: bytes


class Served(NamedTuple):
    """A client to a local server, started by `Serve`."""

    client: VigicruesClient
    requests: list[str]
    """Path and query string of each request received by the server."""


class Serve(Protocol):
    """Start a local server answering with the given response.

    `routes` maps request paths (e.g. `"/services/station.json"`) to other responses.
    """

    def __call__(
        self,
        status: int,
        content_type: str,
        body: bytes,
        routes: Mapping[str, Response] | None = None,
    ) -> Awaitable[Served]: ...
