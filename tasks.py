"""Build tasks, run by build.cmd / build.sh with Invoke (`uv run invoke --list`)."""

import functools
import re
import shutil
import sys
from pathlib import Path
from typing import TextIO
from xml.etree import ElementTree

from invoke.context import Context
from invoke.tasks import task

PROJECT_NAME = "vigicrues-client"

ROOT_PATH = Path(__file__).parent
BUILD_LOG_PATH = ROOT_PATH / "build.log"
BUILD_OUTPUT_PATH = ROOT_PATH / "tmp"
BUILD_TEST_INTERMEDIATE_OUTPUT_PATH = BUILD_OUTPUT_PATH / "tst"
BUILD_BINARY_ARTEFACTS_OUTPUT_PATH = BUILD_OUTPUT_PATH / "out" / "bin"

_ANSI_ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


@functools.cache
def _build_log() -> TextIO:
    """Open build.log, emptied on first use in each build."""
    return BUILD_LOG_PATH.open("w", encoding="utf-8")


class _BuildOutput:
    """Stream writing to the console and, without colours, to build.log."""

    def __init__(self, console: TextIO) -> None:
        self._console = console

    def write(self, text: str) -> int:
        self._console.write(text)
        _build_log().write(_ANSI_ESCAPE_SEQUENCE.sub("", text))
        return len(text)

    def flush(self) -> None:
        self._console.flush()
        _build_log().flush()


def _echo(message: str) -> None:
    output = _BuildOutput(sys.stdout)
    output.write(f"{message}\n")
    # Keeps the order with the commands' outputs, written unbuffered by Invoke.
    output.flush()


def _run(c: Context, command: str, env: dict[str, str] | None = None) -> None:
    _echo(f"> {command}")
    c.run(
        command,
        env=env or {},
        out_stream=_BuildOutput(sys.stdout),
        err_stream=_BuildOutput(sys.stderr),
    )


def _pytest_verbosity(c: Context) -> str:
    return " -v" if c.config.get("verbose", False) else ""


@task
def verbose(c: Context) -> None:
    """Make the tasks that follow verbose (e.g. `invoke verbose test`)."""
    # Invoke shares the configuration between all the tasks of a run.
    c.config.verbose = True


@task
def clean(c: Context) -> None:
    """Remove the build outputs (tmp/)."""
    _echo(f"> remove {BUILD_OUTPUT_PATH}")
    if BUILD_OUTPUT_PATH.exists():
        shutil.rmtree(BUILD_OUTPUT_PATH)


@task(name="compile")
def do_compile(c: Context) -> None:
    """Check formatting, lint and types (static checks replace compilation)."""
    _run(c, "ruff format --check")
    _run(c, "ruff check")
    _run(c, "mypy")


@task(pre=[do_compile])
def test(c: Context) -> None:
    """Run the tests with coverage: JUnit, Cobertura and HTML reports in tmp/."""
    junit_results_path = BUILD_OUTPUT_PATH / f"{PROJECT_NAME}-junit-results.xml"
    cobertura_results_path = BUILD_OUTPUT_PATH / f"{PROJECT_NAME}-cobertura-results.xml"
    html_results_path = BUILD_OUTPUT_PATH / f"{PROJECT_NAME}-cobertura-results"
    BUILD_TEST_INTERMEDIATE_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    _run(
        c,
        f'pytest{_pytest_verbosity(c)} --junitxml="{junit_results_path}"'
        " --cov --cov-report=term"
        f' --cov-report=xml:"{cobertura_results_path}"'
        f' --cov-report=html:"{html_results_path}"',
        env={"COVERAGE_FILE": str(BUILD_TEST_INTERMEDIATE_OUTPUT_PATH / ".coverage")},
    )
    line_rate = ElementTree.parse(cobertura_results_path).getroot().get("line-rate")
    _echo(f"Line coverage: {line_rate}")


@task
def test_live(c: Context) -> None:
    """Run the tests that call the real Vigicrues service (marked `live`)."""
    _run(c, f"pytest{_pytest_verbosity(c)} -m live")


@task
def analyze(c: Context) -> None:
    """Count the lines of code: cloc-compatible report in tmp/cloc-results.xml."""
    BUILD_OUTPUT_PATH.mkdir(exist_ok=True)
    # "[...]" keeps pygount's default folders to skip (hidden folders, __pycache__...):
    # its help also mentions "..." but that one replaces the defaults.
    # Recorded responses are data, not code.
    _run(
        c,
        'pygount --format=cloc-xml --folders-to-skip="[...],responses,tmp"'
        f' --out="{BUILD_OUTPUT_PATH / "cloc-results.xml"}" "{ROOT_PATH}"',
    )


@task
def package(c: Context) -> None:
    """Build the wheel and the source distribution in tmp/out/bin/."""
    _run(
        c,
        "uv build --no-create-gitignore"
        f' --out-dir "{BUILD_BINARY_ARTEFACTS_OUTPUT_PATH}"',
    )


@task(pre=[do_compile, test, analyze], default=True)
def build(c: Context) -> None:
    """Compile, test and analyze."""


@task(pre=[clean, build])
def rebuild(c: Context) -> None:
    """Clean, then build."""


@task(pre=[rebuild, package])
def release(c: Context) -> None:
    """Rebuild, then package."""
