"""The LLMSmartAudit entrypoint refuses to start without ``LLM_MODEL``.

Until 2026-09-24 the image carried ``ENV LLM_MODEL=deepseek-chat`` and
``run.py`` has the same default, so a host that forgot the variable ran against
a model the provider had switched off: every call answered HTTP 400, the tool
burned its retry budget and the task ended hours later without a report
(``docs/BA-BETRIEB.md``, Fallstrick 2). The image bakes no model any more and
``scripts/do_solidity.sh`` exits 2 with a placeholder report before any tool
code runs. A silent default would be the worse failure: it would pick the
backend for the user and the mistake would only show in the cost figures.

The tests run the real script with ``sh`` and stubs on PATH, the technique of
``test_entrypoint_main.py``. With a model set the script carries on to
``cd /app``, which does not exist on the host, so it ends with exit 1 there ---
after the guard, before any tool is started.
"""

import json
import os
import re
import shutil
import subprocess

import pytest

from conftest import tool_script

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCKERFILE = os.path.join(REPO_ROOT, "LLMSmartAuditTool-main", "LLMSmartAuditTool-main",
                          "Dockerfile.smartbugs")

pytestmark = pytest.mark.skipif(
    shutil.which("sh") is None, reason="needs a POSIX shell"
)


def make_stub(bindir, name: str, body: str) -> None:
    path = os.path.join(bindir, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("#!/bin/sh\n" + body)
    os.chmod(path, 0o755)


def run_entrypoint(tmp_path, **env_overrides):
    """Run the LLMSmartAudit entrypoint with MAIN=0 and no timeout."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    shutil.copyfile(tool_script("llmsmartaudit", "do_solidity.sh"), bindir / "do_solidity.sh")
    calls = tmp_path / "calls.txt"
    make_stub(str(bindir), "python3", f'echo "python3 $@" >> "{calls}"\nexit 0\n')
    for util in ("rm", "mkdir", "cp"):
        make_stub(str(bindir), util, f'echo "{util} $@" >> "{calls}"\nexit 0\n')
    src = tmp_path / "a.sol"
    src.write_text("contract A { }\n", encoding="utf-8")
    output = tmp_path / "output.json"

    env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    env["TMPDIR"] = str(tmp_path / "tmp")
    os.makedirs(env["TMPDIR"], exist_ok=True)
    # Keep the placeholder report off the host's root directory.
    env["SB_OUTPUT_JSON"] = str(output).replace("\\", "/")
    env.update(env_overrides)
    proc = subprocess.run(
        ["sh", str(bindir / "do_solidity.sh"), str(src), "0", str(bindir), "0"],
        capture_output=True, text=True, env=env,
    )
    recorded = calls.read_text(encoding="utf-8") if calls.exists() else ""
    return proc, output, recorded


def test_missing_model_exits_2_with_a_placeholder_report(tmp_path):
    proc, output, recorded = run_entrypoint(tmp_path)

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "LLM_MODEL" in proc.stdout
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["findings"] == []
    assert report["categories_checked"] == 0
    assert report["categories_total"] == 41
    assert "LLM_MODEL not set" in report["error"]
    assert "run.py" not in recorded          # no tool code was started


def test_an_empty_model_is_refused_like_a_missing_one(tmp_path):
    proc, output, _ = run_entrypoint(tmp_path, LLM_MODEL="")

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert output.exists()


def test_a_set_model_passes_the_guard(tmp_path):
    proc, output, _ = run_entrypoint(tmp_path, LLM_MODEL="deepseek-v4-flash")

    assert proc.returncode != 2, proc.stdout + proc.stderr
    assert "LLMSA_META" in proc.stdout and "deepseek-v4-flash" in proc.stdout
    assert not output.exists()               # the guard wrote nothing


def test_the_image_bakes_no_model():
    """The counterpart of the guard: without it a baked default would win silently."""
    with open(DOCKERFILE, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    assert not any(re.match(r"\s*ENV\s+LLM_MODEL\b", line) for line in lines)
