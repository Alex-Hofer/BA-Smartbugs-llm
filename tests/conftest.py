"""Shared plumbing for the parser regression tests.

The tool parsers live at ``smartbugs/tools/<tool>/parser.py`` and are loaded by
SmartBugs from a file path rather than imported as a package
(``sb/parsing.py::get_parser``). :func:`load_parser` does the same, so the tests
exercise the module exactly as SmartBugs will.

Fixtures
--------
``tests/fixtures/<tool>/<case>/`` holds the *unmodified* raw material of a real
task from ``smartbugs/results`` --- ``result.log``, ``result.tar`` and
``smartbugs.json``. ``tests/fixtures/MANIFEST.json`` records which run each came
from. Every fixture was checked for API keys before being copied in; the
project's own ``analysis_tools/secret_scan.py`` re-checks them on every commit.

Logs above 100 KB are stored gzipped (LLMSmartAudit writes its entire
multi-agent transcript to stdout). The compression is lossless --- the bytes a
test sees are the bytes the container produced.

Material that is *constructed* rather than recorded is built by the
``synthetic_*`` helpers, and every test using one says ``synthetic`` in its
name. Two reasons occur:

* the failure mode never happened in the 19 recorded runs --- a timeout, an
  empty archive, malformed JSON, a missing ``GPTSCAN_META``, the budget cap;
* the failure mode *did* happen, but only alongside another one, so a recorded
  task cannot show which branch fired. ``success: false`` occurs in 44 tasks,
  always together with a non-zero exit code; a report ``error`` field occurs in
  ``backend_rejected`` for the same reason.

The distinction matters when reading a failure: a synthetic test asserts
designed behaviour, a recorded one asserts observed behaviour.
"""

import gzip
import importlib.util
import io
import json
import os
import sys
import tarfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMARTBUGS = os.path.join(REPO_ROOT, "smartbugs")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

# The parsers import sb.parse_utils / sb.io.
if SMARTBUGS not in sys.path:
    sys.path.insert(0, SMARTBUGS)


def load_parser(tool: str):
    """Import ``smartbugs/tools/<tool>/parser.py`` the way SmartBugs does."""
    path = os.path.join(SMARTBUGS, "tools", tool, "parser.py")
    spec = importlib.util.spec_from_file_location(f"tools.{tool}.parser", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tool_script(tool: str, name: str) -> str:
    """Path of a file in ``smartbugs/tools/<tool>/scripts/``.

    SmartBugs copies that directory into the container as ``/sb/bin`` and hands
    the path to the entrypoint as ``$BIN``, so this is the same material the
    container sees.
    """
    return os.path.join(SMARTBUGS, "tools", tool, "scripts", name)


def load_tool_script(tool: str, name: str):
    """Import a helper from ``smartbugs/tools/<tool>/scripts/`` by path.

    The helpers are not importable as a package --- inside the container they
    are plain scripts next to the entrypoint. Loading them by path is what the
    entrypoint effectively does when it calls ``python3 $BIN/<name>``.
    """
    path = tool_script(tool, f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"tools.{tool}.scripts.{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def gptscan():
    """The GPTScan parser module, loaded once per test session."""
    return load_parser("gptscan")


@pytest.fixture(scope="session")
def llmsmartaudit():
    """The LLMSmartAudit parser module, loaded once per test session."""
    return load_parser("llmsmartaudit")


def raw(tool: str, case: str) -> tuple:
    """Load a recorded task as ``(exit_code, log_lines, tar_bytes)``."""
    d = os.path.join(FIXTURES, tool, case)
    with open(os.path.join(d, "smartbugs.json"), encoding="utf-8") as fh:
        exit_code = json.load(fh)["result"]["exit_code"]

    plain, packed = os.path.join(d, "result.log"), os.path.join(d, "result.log.gz")
    if os.path.exists(plain):
        with open(plain, encoding="utf-8", errors="replace") as fh:
            log = fh.read().splitlines()
    else:
        with gzip.open(packed, "rt", encoding="utf-8", errors="replace") as fh:
            log = fh.read().splitlines()

    tar_path = os.path.join(d, "result.tar")
    tar = open(tar_path, "rb").read() if os.path.exists(tar_path) else None
    return exit_code, log, tar


def parse(parser, tool: str, case: str) -> dict:
    """Run *parser* over a recorded task and return the four output sets."""
    findings, infos, errors, fails = parser.parse(*raw(tool, case))
    return {"findings": findings, "infos": infos, "errors": errors, "fails": fails}


# --------------------------------------------------------------------------- #
# Synthetic raw material, for failure modes the recorded runs never produced
# --------------------------------------------------------------------------- #

def synthetic_tar(content: bytes, name: str = "output.json") -> bytes:
    """A tar archive as ``container.get_archive()`` would return it."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def synthetic_empty_tar() -> bytes:
    """A well-formed but memberless tar --- nothing was collected."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w"):
        pass
    return buf.getvalue()


def contains(messages, needle: str) -> bool:
    """Is *needle* mentioned anywhere in a set of parser messages?"""
    return any(needle in m for m in messages)
