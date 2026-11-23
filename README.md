# vigicrues-client
[![PyPI - Package Version](https://img.shields.io/pypi/v/vigicrues-client)](https://pypi.org/project/vigicrues-client/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vigicrues-client)](https://pypi.org/project/vigicrues-client/)
[![PyPI - License](https://img.shields.io/pypi/l/vigicrues-client)](https://github.com/mcartoixa/vigicrues-client/blob/main/LICENSE)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/mcartoixa/vigicrues-client/build.yml?branch=main)](https://github.com/mcartoixa/vigicrues-client/actions/workflows/build.yml)
[![Codecov](https://img.shields.io/codecov/c/gh/mcartoixa/vigicrues-client)](https://app.codecov.io/gh/mcartoixa/vigicrues-client)

Asynchronous Python client for [Vigicrues](https://www.vigicrues.gouv.fr/), the French flood
vigilance service: water heights and flow rates observed at the hydrometric stations, flood vigilance
levels and bulletins of the river sections.

This project is not affiliated with Vigicrues. It reads the services and pages of the Vigicrues web
site, which are not documented as a public API: they may change without notice.

## Installation

Requires Python 3.11 or later.

```powershell
pip install vigicrues-client
```

## Usage

```python
import asyncio

from vigicrues_client import Quantity, VigicruesClient, VigilanceLevel


async def main() -> None:
    async with VigicruesClient() as client:
        # Water heights observed at a station, in metres
        heights = await client.get_observations("O262002001")
        if heights.latest is not None:
            print(f"{heights.station_name}: {heights.latest.value} m")

        # Flow rates, in cubic metres per second
        flows = await client.get_observations("E540031001", Quantity.FLOW)
        if flows.latest is not None:
            print(f"{flows.station_name}: {flows.latest.value} m³/s")

        # Flood vigilance of a river section: level and forecaster's comments
        vigilance = await client.get_river_section_vigilance("MP18")
        print(f"{vigilance.section.name}: {vigilance.level.name}")
        for comment in vigilance.comments:
            print(comment)
        print(vigilance.bulletin.general_comment)

        # Levels of all the river sections of metropolitan France at once
        levels = await client.get_vigilance_levels()
        in_vigilance = [
            code
            for code, level in levels.levels.items()
            if level >= VigilanceLevel.YELLOW
        ]
        print(f"In vigilance at {levels.time}: {in_vigilance}")


asyncio.run(main())
```

| Method | Returns |
|---|---|
| `get_observations(station, quantity)` | Recent heights or flow rates observed at a station |
| `get_forecast(station, quantity)` | Latest forecast of heights or flow rates at a station (low, central and high trends), or `None` if there is none |
| `get_station(station)` | Details of a station: river, territory, historical floods, stations of the basin |
| `get_territory(territory)` | A flood vigilance territory and its river sections |
| `get_river_section(section)` | A river section, its territory and its stations |
| `get_vigilance_levels()` | Vigilance levels of all the river sections of metropolitan France |
| `get_vigilance_level(section)` | Vigilance level of a river section |
| `get_territory_bulletin(territory)` | Vigilance bulletin of a territory: situation, comments, levels of the river sections |
| `get_river_section_vigilance(section)` | Vigilance level and comments of a river section, with the bulletin of its territory |

The bulletins are read from the HTML pages of the Vigicrues web site, and are the most likely to break
when the site changes.

### HTTP session

By default, the client creates its own [aiohttp](https://docs.aiohttp.org/) session and closes it
with the client. An application can pass its own session instead, which the client never closes:

```python
async with aiohttp.ClientSession() as session:
    client = VigicruesClient(session)
    series = await client.get_observations("O262002001")
```

### Errors

All the errors derive from `VigicruesError`:

| Error | Raised when |
|---|---|
| `VigicruesConnectionError` | The service could not be reached or did not answer in time (`timeout` argument of the client, in seconds) |
| `VigicruesRateLimitError` | The service refused the request: too many requests (HTTP 429). Avoid bursts of requests |
| `VigicruesBadValueError` | The service rejected a code: unknown or invalid (it does not tell them apart) |
| `VigicruesUnknownValueError` | The service sent nothing for a code that it did not reject |
| `VigicruesResponseError` | The service sent an unexpected response: HTTP error, unexpected content or page structure |
| `VigicruesNotFoundError` | The service does not have the requested resource (HTTP 404); a `VigicruesResponseError` |
| `VigicruesApiError` | The service reported another error in its response; base class of `VigicruesBadValueError` |

## Development

Prerequisites: [uv](https://docs.astral.sh/uv/), which manages the Python interpreters, the virtual
environment (`.venv/`) and the dependencies; [Git](https://git-scm.com/).

### Build

```powershell
build.cmd [analyze|build|clean|compile|package|rebuild|release|test|test-live] [/log] [/NoPause] [/?]
```

```bash
./build.sh [analyze|build|clean|compile|package|rebuild|release|test|test-live] [--log] [--help]
```

| Target | Content |
|---|---|
| `clean` | Removes the virtual environment (`.venv/`, recreated right away) and the build outputs (`tmp/`) |
| `compile` | Formatting, lint and type checks |
| `test` | `compile`, then the tests with coverage (JUnit, Cobertura and HTML reports in `tmp/`) |
| `test-live` | The tests that call the real Vigicrues service (marked `live`, excluded from `test`); also run weekly and on demand by the `test-live` GitHub workflow |
| `analyze` | Lines of code (`tmp/cloc-results.xml`) |
| `package` | Wheel and source distribution in `tmp/out/bin/` |
| `build` (default) | `compile`, `test` and `analyze` |
| `rebuild` | `clean`, then `build` |
| `release` | `rebuild`, then `package` |

The build first updates `.venv` to the latest allowed dependencies (`uv sync --upgrade`), then runs
the target with [Invoke](https://www.pyinvoke.org/) (`tasks.py`). The output is also written to
`build.log`. Set `UV_PYTHON` (e.g. `3.11`) to build with another Python version: this recreates
`.venv` with it.

### Individual commands

```powershell
# Create .venv with the Python version from .python-version and install the latest allowed dependencies
uv sync --upgrade

# Run a command in that environment
uv run python -c "import vigicrues_client"

# Static checks: lint, formatting, types (configured in pyproject.toml)
uv run ruff check
uv run ruff format --check
uv run mypy

# Tests (tests marked `live` call the real Vigicrues service and only run with `-m live`)
uv run pytest
uv run pytest -m live

# Tests on another Python version, in a temporary environment (.venv is left untouched)
uv run --isolated --python 3.11 pytest
```

### Release

The version number is written in `pyproject.toml`; `main` keeps the last released one until the next
release. Pushing a tag `v<version>` publishes that version on [PyPI](https://pypi.org/project/vigicrues-client/):
the `build` workflow checks that the tag matches the version in `pyproject.toml`, builds and tests on
every Python version, then uploads the packages built by that same run. Publication uses
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/): PyPI accepts uploads from the
`build.yml` workflow in the `pypi` environment of this repository, no token is stored.

A published version can never be uploaded again, even after its deletion: fix a bad release with a new
version.

```powershell
# 1. Check the parsing of the live Vigicrues service, set the new version, then commit and push to
#    main and wait for the build to pass
build.cmd test-live
uv version 0.3.0

# 2. Tag the commit: the build of the tag publishes the version on PyPI
git tag v0.3.0
git push origin v0.3.0

# 3. Once published, create the GitHub release with notes describing the changes (fails if the tag
#    does not exist, rather than creating it)
gh release create v0.3.0 --verify-tag --notes-file notes.md
```
