from collections.abc import AsyncIterator, Mapping
from contextlib import AsyncExitStack

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from vigicrues_client import VigicruesClient

from .support import Response, Serve, Served


@pytest.fixture
async def serve() -> AsyncIterator[Serve]:
    async with AsyncExitStack() as stack:

        async def start(
            status: int,
            content_type: str,
            body: bytes,
            routes: Mapping[str, Response] | None = None,
        ) -> Served:
            default = Response(status, content_type, body)
            requests: list[str] = []

            async def handler(request: web.Request) -> web.Response:
                requests.append(request.path_qs)
                response = (routes or {}).get(request.path, default)
                return web.Response(
                    status=response.status,
                    body=response.body,
                    headers={"Content-Type": response.content_type},
                )

            app = web.Application()
            app.router.add_get("/{path:.*}", handler)
            server = await stack.enter_async_context(TestServer(app))
            client = await stack.enter_async_context(
                VigicruesClient(base_url=str(server.make_url("/")))
            )
            return Served(client, requests)

        yield start
