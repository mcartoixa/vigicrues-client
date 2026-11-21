import asyncio
import importlib.metadata
from collections.abc import AsyncIterator, Mapping

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import BaseTestServer, TestServer

from vigicrues_client import VigicruesClient, VigicruesConnectionError


async def _echo(request: web.Request) -> web.Response:
    return web.Response(text=f"{request.path_qs}\n{request.headers['User-Agent']}")


async def _slow(request: web.Request) -> web.Response:
    await asyncio.sleep(1)
    return web.Response(text="too late")


async def _get_echo(
    client: VigicruesClient, params: Mapping[str, str] | None = None
) -> tuple[str, str]:
    """Return the path with query string and the User-Agent received by the server."""
    _, body = await client._get("echo", params)
    path_qs, user_agent = body.decode().split("\n")
    return path_qs, user_agent


@pytest.fixture
async def server() -> AsyncIterator[BaseTestServer]:
    app = web.Application()
    app.router.add_get("/echo", _echo)
    app.router.add_get("/slow", _slow)
    async with TestServer(app) as test_server:
        yield test_server


@pytest.fixture
def base_url(server: BaseTestServer) -> str:
    return str(server.make_url("/"))


async def test_client_sends_requests_to_base_url(base_url: str) -> None:
    async with VigicruesClient(base_url=base_url) as client:
        path_qs, _ = await _get_echo(client, {"CdStationHydro": "O262002001"})

    assert path_qs == "/echo?CdStationHydro=O262002001"


async def test_client_identifies_library_on_its_own_session(base_url: str) -> None:
    async with VigicruesClient(base_url=base_url) as client:
        _, user_agent = await _get_echo(client)

    version = importlib.metadata.version("vigicrues-client")
    assert user_agent == (
        f"vigicrues-client/{version} (+https://github.com/mcartoixa/vigicrues-client)"
    )


async def test_client_closes_its_own_session(base_url: str) -> None:
    client = VigicruesClient(base_url=base_url)
    await _get_echo(client)
    session = client._session

    await client.close()

    assert session is not None
    assert session.closed


async def test_client_creates_new_session_after_close(base_url: str) -> None:
    async with VigicruesClient(base_url=base_url) as client:
        await _get_echo(client)
        await client.close()

        path_qs, _ = await _get_echo(client)

    assert path_qs == "/echo"


async def test_client_uses_injected_session_as_is(base_url: str) -> None:
    async with (
        aiohttp.ClientSession(headers={"User-Agent": "caller/1.0"}) as session,
        VigicruesClient(session, base_url=base_url) as client,
    ):
        _, user_agent = await _get_echo(client)

    assert user_agent == "caller/1.0"


async def test_client_never_closes_injected_session(base_url: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with VigicruesClient(session, base_url=base_url) as client:
            await _get_echo(client)

        assert not session.closed


async def test_client_times_out_on_its_own_session(base_url: str) -> None:
    async with VigicruesClient(base_url=base_url, timeout=0.1) as client:
        with pytest.raises(VigicruesConnectionError) as error_info:
            await client._get("slow")

    assert isinstance(error_info.value.__cause__, TimeoutError)


async def test_client_times_out_on_injected_session(base_url: str) -> None:
    async with (
        aiohttp.ClientSession() as session,
        VigicruesClient(session, base_url=base_url, timeout=0.1) as client,
    ):
        with pytest.raises(VigicruesConnectionError) as error_info:
            await client._get("slow")

    assert isinstance(error_info.value.__cause__, TimeoutError)
