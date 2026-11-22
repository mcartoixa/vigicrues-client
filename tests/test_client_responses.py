import aiohttp
import pytest
from aiohttp.test_utils import unused_port

from vigicrues_client import (
    VigicruesApiError,
    VigicruesBadValueError,
    VigicruesClient,
    VigicruesConnectionError,
    VigicruesNotFoundError,
    VigicruesRateLimitError,
    VigicruesResponseError,
)

from .support import JSON_UTF8, Serve, recorded


async def test_get_json_returns_data(serve: Serve) -> None:
    client, _ = await serve(200, JSON_UTF8, recorded("TronEntVigiCru_AP16.json"))

    data = await client._get_json("data")

    assert isinstance(data, dict)
    assert data["ListEntVigiCru"][0]["CdEntVigiCru"] == "AP16"


async def test_get_json_returns_empty_list(serve: Serve) -> None:
    client, _ = await serve(200, JSON_UTF8, b"[]")

    assert await client._get_json("data") == []


@pytest.mark.parametrize(
    ("file", "content_type", "message", "code"),
    [
        pytest.param(
            "TronEntVigiCru_unknown.json",
            JSON_UTF8,
            "Problème dans l'exécution de la requête : tronçon",
            400,
            id="error_msg in a list",
        ),
        pytest.param(
            "observations_unknown.json",
            "application/json",
            "Code de station inconnu",
            400,
            id="error_msg in an object",
        ),
        pytest.param(
            "TronEntVigiCru_missing_type.json",
            JSON_UTF8,
            "Problème d'exécution du process",
            None,
            id="msg_error",
        ),
        pytest.param(
            "prevision_no_forecast.json",
            JSON_UTF8,
            "Problème dans l'exécution de la requête : prévision",
            204,
            id="message and code",
        ),
    ],
)
async def test_get_json_raises_errors_reported_with_http_200(
    serve: Serve, file: str, content_type: str, message: str, code: int | None
) -> None:
    client, _ = await serve(200, content_type, recorded(file))

    with pytest.raises(VigicruesApiError) as error_info:
        await client._get_json("data")

    assert error_info.value.message == message
    assert error_info.value.code == code
    # Code 400: unknown or invalid value
    assert type(error_info.value) is (
        VigicruesBadValueError if code == 400 else VigicruesApiError
    )


async def test_get_json_raises_not_found_for_http_404(serve: Serve) -> None:
    client, _ = await serve(
        404, "text/html; charset=UTF-8", recorded("page_not_found.html")
    )

    with pytest.raises(VigicruesNotFoundError, match="HTTP status 404"):
        await client._get_json("data")


@pytest.mark.parametrize(
    ("status", "file", "content_type", "match"),
    [
        pytest.param(
            500,
            "station_unknown.html",
            "text/html",
            "HTTP status 500",
            id="site under maintenance",
        ),
        pytest.param(
            200,
            "page_not_found.html",
            "text/html; charset=UTF-8",
            "Unexpected content type 'text/html'",
            id="HTML page with HTTP 200",
        ),
    ],
)
async def test_get_json_raises_on_unexpected_responses(
    serve: Serve, status: int, file: str, content_type: str, match: str
) -> None:
    client, _ = await serve(status, content_type, recorded(file))

    with pytest.raises(VigicruesResponseError, match=match):
        await client._get_json("data")


async def test_get_json_raises_on_invalid_json(serve: Serve) -> None:
    client, _ = await serve(200, JSON_UTF8, recorded("TronEntVigiCru_AP16.json")[:100])

    with pytest.raises(VigicruesResponseError, match="Invalid JSON"):
        await client._get_json("data")


async def test_get_json_raises_on_too_many_requests(serve: Serve) -> None:
    client, _ = await serve(429, "text/html", b"")

    with pytest.raises(VigicruesRateLimitError):
        await client._get_json("data")


async def test_get_json_raises_when_service_unreachable() -> None:
    async with VigicruesClient(base_url=f"http://127.0.0.1:{unused_port()}") as client:
        with pytest.raises(VigicruesConnectionError) as error_info:
            await client._get_json("data")

    assert isinstance(error_info.value.__cause__, aiohttp.ClientConnectionError)
