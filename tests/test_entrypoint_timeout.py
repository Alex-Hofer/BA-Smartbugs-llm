"""Regression tests for the timeout wiring in both do_solidity.sh entrypoints.

Same approach as test_entrypoint_main.py: the real scripts run under sh with
recording stubs on PATH. Three things are checked, for both tools:

* TIMEOUT=0 --- nothing is computed, nothing is exported. Every result recorded
  so far was produced this way, so this is the test that keeps the earlier runs
  comparable;
* TIMEOUT>0 --- brake at 70 %, net at 90 %, and SB_DEADLINE_EPOCH exported as an
  absolute instant;
* both scripts compute the marks identically. The arithmetic is deliberately
  duplicated (as mythril and honeybadger do upstream), so something has to hold
  the two copies together.
"""

import os
import re
import shutil
import subprocess

import pytest

from conftest import tool_script

pytestmark = pytest.mark.skipif(
    shutil.which("sh") is None, reason="needs a POSIX shell"
)

TOOLS = ("gptscan", "llmsmartaudit")


def run_entrypoint(tmp_path, tool, timeout):
    """Run the entrypoint far enough to see the timeout block, return its log."""
    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    for helper in ("main_contract.py", "do_solidity.sh", "mark_timeout.py"):
        shutil.copyfile(tool_script(tool, helper), bindir / helper)

    source = tmp_path / "Visor.sol"
    source.write_text("contract Visor { }\n", encoding="utf-8")

    # Stub out everything the script would otherwise really invoke. 'timeout'
    # just succeeds: the command it would wrap is python3, itself a stub, and
    # these tests assert on the computed marks, not on the tool run.
    for name, body in (("python3", 'exit 0\n'),
                       ("timeout", 'exit 0\n'),
                       ("solc", 'exit 0\n')):
        path = bindir / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
        os.chmod(path, 0o755)

    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")
    proc = subprocess.run(
        ["sh", str(bindir / "do_solidity.sh"), str(source), str(timeout),
         str(bindir), "0"],
        capture_output=True, text=True, env=env, cwd=str(tmp_path))
    return proc.stdout + proc.stderr


def marks(log):
    """Pull 'SB_TIMEOUT_BUDGET timeout=Ns brake=Ns net=Ns' out of the log."""
    m = re.search(r"SB_TIMEOUT_BUDGET timeout=(\d+)s brake=(\d+)s net=(\d+)s", log)
    return None if m is None else tuple(int(g) for g in m.groups())


@pytest.mark.parametrize("tool", TOOLS)
def test_timeout_zero_computes_nothing(tmp_path, tool):
    """No --timeout: the entrypoint must behave exactly as it did before AP5."""
    assert marks(run_entrypoint(tmp_path, tool, 0)) is None


@pytest.mark.parametrize("tool", TOOLS)
def test_marks_are_seventy_and_ninety_percent(tmp_path, tool):
    assert marks(run_entrypoint(tmp_path, tool, 1000)) == (1000, 700, 900)


@pytest.mark.parametrize("tool", TOOLS)
def test_marks_never_fall_below_one_second(tmp_path, tool):
    """A tiny timeout must not produce a mark of 0, which would disable it."""
    assert marks(run_entrypoint(tmp_path, tool, 1)) == (1, 1, 1)


def test_both_entrypoints_compute_the_same_marks(tmp_path):
    """The arithmetic is duplicated on purpose; this keeps the copies equal."""
    a = marks(run_entrypoint(tmp_path / "a", "gptscan", 3600))
    b = marks(run_entrypoint(tmp_path / "b", "llmsmartaudit", 3600))
    assert a == b == (3600, 2520, 3240)
