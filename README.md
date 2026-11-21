# vigicrues-client
[![PyPI - Package Version](https://img.shields.io/pypi/v/vigicrues-client)](https://pypi.org/project/vigicrues-client/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vigicrues-client)](https://pypi.org/project/vigicrues-client/)
[![PyPI - License](https://img.shields.io/pypi/l/vigicrues-client)](https://github.com/mcartoixa/vigicrues-client/blob/main/LICENSE)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/mcartoixa/vigicrues-client/build.yml?branch=main)](https://github.com/mcartoixa/vigicrues-client/actions/workflows/build.yml)
[![Codecov](https://img.shields.io/codecov/c/gh/mcartoixa/vigicrues-client)](https://app.codecov.io/gh/mcartoixa/vigicrues-client)

Python client for the Vigicrues API

## Development

Prerequisites: [uv](https://docs.astral.sh/uv/), which manages the Python interpreters, the virtual
environment (`.venv/`) and the dependencies; [Git](https://git-scm.com/).

### Build

```powershell
build.cmd [clean | compile | test | test-live | analyze | package | build | rebuild | release] [/log] [/NoPause] [/?]
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
