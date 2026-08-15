"""Regression tests for the MAIN wiring in both do_solidity.sh entrypoints.

The entrypoints are the only place where MAIN can be honoured: SmartBugs passes
it as ``$4`` (``sb/docker.py:120``) and nothing downstream sees it. These tests
run the real scripts with ``sh``, with ``python3`` and the file utilities
replaced by recording stubs on PATH, and check three things:

* ``MAIN=1`` and the file is named after one of its contracts --- the helper is
  invoked and the reduced file is what the tool gets to see;
* ``MAIN=1`` and it is not --- exit 127, before the tool is started;
* ``MAIN=0`` --- the helper is never invoked and the tool gets the original
  file. Every result recorded so far was produced this way, so this is the test
  that keeps the older runs comparable.

The scripts cannot run to completion outside their container (they ``cd`` into
an image-specific directory and exit 1 when it is absent). That is deliberate
here: the MAIN block sits at the top, so everything under test has already
happened by then, and no tool is ever started on the host.
"""

import os
import shutil
import subprocess

import pytest

from conftest import tool_script

pytestmark = pytest.mark.skipif(
    shutil.which("sh") is None, reason="needs a POSIX shell"
)

MATCHING = "contract Visor { }\nlibrary Unused { }\n"
NOT_MATCHING = "contract Stream { }\ncontract StreamFactory { }\n"


def make_stub(bindir, name: str, body: str) -> None:
    path = os.path.join(bindir, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("#!/bin/sh\n" + body)
    os.chmod(path, 0o755)


def sandbox(tmp_path, tool: str, source_name: str, source: str):
    """A $BIN directory holding the tool's scripts plus recording stubs."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for helper in ("main_contract.py", "do_solidity.sh"):
        shutil.copyfile(tool_script(tool, helper), bindir / helper)

    calls = tmp_path / "calls.txt"
    # The helper is the only python3 call in the MAIN block; record it and
    # perform the copy the real helper would, so the script can carry on.
    make_stub(str(bindir), "python3",
              f'echo "python3 $@" >> "{calls}"\n'
              'for a in "$@"; do last="$a"; done\n'
              'src=""; for a in "$@"; do case "$a" in *.sol) '
              'if [ -z "$src" ]; then src="$a"; fi;; esac; done\n'
              'cp "$src" "$last" 2>/dev/null\n'
              'exit 0\n')
    # Keep the container-only file operations off the host filesystem.
    for util in ("rm", "mkdir", "cp"):
        make_stub(str(bindir), util, f'echo "{util} $@" >> "{calls}"\nexit 0\n')

    src = tmp_path / source_name
    src.write_text(source, encoding="utf-8")
    return bindir, src, calls


def run(bindir, src, main: str, tmp_path):
    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    env["TMPDIR"] = str(tmp_path / "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)
    return subprocess.run(
        ["sh", str(bindir / "do_solidity.sh"), str(src), "0", str(bindir), main],
        capture_output=True, text=True, env=env,
    )


def recorded(calls) -> str:
    return calls.read_text(encoding="utf-8") if calls.exists() else ""


@pytest.mark.parametrize("tool", ["gptscan", "llmsmartaudit"])
def test_main_0_leaves_the_original_file_untouched(tool, tmp_path):
    """The behaviour every recorded run was produced with."""
    bindir, src, calls = sandbox(tmp_path, tool, "10_Visor.sol", MATCHING)

    result = run(bindir, src, "0", tmp_path)

    assert "main_contract.py" not in recorded(calls)
    assert result.returncode != 127
    assert src.read_text(encoding="utf-8") == MATCHING


@pytest.mark.parametrize("tool", ["gptscan", "llmsmartaudit"])
def test_main_1_reduces_the_source_before_the_tool_runs(tool, tmp_path):
    bindir, src, calls = sandbox(tmp_path, tool, "10_Visor.sol", MATCHING)

    result = run(bindir, src, "1", tmp_path)

    log = recorded(calls)
    assert "main_contract.py" in log
    assert str(src) in log
    assert result.returncode != 127


@pytest.mark.parametrize("tool", ["gptscan", "llmsmartaudit"])
def test_main_1_keeps_the_original_file_name_for_the_tool(tool, tmp_path):
    """Reports, WareHouse directories and parsers key off the file name."""
    bindir, src, calls = sandbox(tmp_path, tool, "10_Visor.sol", MATCHING)

    run(bindir, src, "1", tmp_path)

    for line in recorded(calls).splitlines():
        if "main_contract.py" in line:
            assert line.rstrip().endswith("10_Visor.sol")
            break
    else:
        pytest.fail("the helper was never called")


@pytest.mark.parametrize("tool", ["gptscan", "llmsmartaudit"])
def test_main_1_exits_127_when_the_file_names_no_contract(tool, tmp_path):
    """The helper's 127 has to reach SmartBugs unchanged.

    Swallowing it would turn "this file has no main contract" into a silent
    analysis of the whole flattened source --- the very thing MAIN prevents.
    """
    bindir, src, calls = sandbox(tmp_path, tool, "62_Locke.sol", NOT_MATCHING)
    # A helper that refuses, as the real one does for this file.
    make_stub(str(bindir), "python3",
              f'echo "python3 $@" >> "{calls}"\nexit 127\n')

    result = run(bindir, src, "1", tmp_path)

    assert result.returncode == 127
