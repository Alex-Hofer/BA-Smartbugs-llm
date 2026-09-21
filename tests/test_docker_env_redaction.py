"""Regression tests for the API-key passthrough and its redaction in ``sb/docker.py``.

Background
----------
SmartBugs does not forward host environment variables into tool containers.
For the two LLM-backed scanners there is therefore no way to hand over an API
key at run time other than baking it into the image, which would carry the
secret into every copy of that image.

``BA MODIFICATION 2`` adds the forwarding: the names listed under ``env:`` in a
tool's ``config.yaml`` are looked up on the host and passed to
``containers.run``. ``BA MODIFICATION 5`` takes the values back out again
immediately before ``execute`` returns, because the returned argument dict is
written verbatim into every ``results/**/smartbugs.json`` by ``sb/analysis.py``.

The two belong together and must never drift apart: forwarding without
redaction writes the key in clear text into the measurement data — the defect
that produced the 62 affected files recorded in the protocol (error #13).
These tests pin both halves, plus the allowlist property that only *declared*
and *actually set* variables are forwarded.
"""

import os
import sys
import types

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMARTBUGS = os.path.join(REPO_ROOT, "smartbugs")

if SMARTBUGS not in sys.path:
    sys.path.insert(0, SMARTBUGS)

SECRET = "sk-must-never-be-persisted-0123456789"


def _stub_docker_sdk() -> None:
    """Register placeholder modules for the Docker SDK and ``requests``.

    ``sb/docker.py`` imports both at module level and evaluates the annotation
    ``Optional[docker.DockerClient]`` at import time. The code under test never
    reaches a real daemon, so stubs keep these tests runnable with the plain
    system interpreter, which has no Docker SDK.
    """
    if "docker" not in sys.modules:
        docker = types.ModuleType("docker")
        docker.DockerClient = object
        docker.errors = types.ModuleType("docker.errors")
        docker.errors.APIError = Exception
        docker.errors.NotFound = Exception
        models = types.ModuleType("docker.models")
        containers = types.ModuleType("docker.models.containers")
        containers.Container = object
        models.containers = containers
        docker.models = models
        sys.modules.update(
            {
                "docker": docker,
                "docker.errors": docker.errors,
                "docker.models": models,
                "docker.models.containers": containers,
            }
        )
    if "requests" not in sys.modules:
        requests = types.ModuleType("requests")
        requests.exceptions = types.ModuleType("requests.exceptions")
        requests.exceptions.ReadTimeout = Exception
        requests.exceptions.ConnectionError = Exception
        sys.modules.update(
            {"requests": requests, "requests.exceptions": requests.exceptions}
        )


@pytest.fixture(scope="module")
def sb_docker():
    """The ``sb.docker`` module, imported against stubbed third-party SDKs."""
    _stub_docker_sdk()
    import sb.docker

    return sb.docker


def _task(env_field, tmp_path):
    """A task stub shaped like the real one, for a tool declaring ``env_field``.

    Only the attributes ``__docker_args`` and ``execute`` actually read are
    provided; ``env`` is the field that ``sb/tools.py`` adds to the dataclass.
    """
    contract = tmp_path / "Contract.sol"
    contract.write_text("contract C {}", encoding="utf-8")

    tool = types.SimpleNamespace(
        image="smartbugs/gptscan:1.0",
        cpu_quota=None,
        mem_limit=None,
        network="bridge",
        mode="solidity",
        bin=None,
        absbin=None,
        output="/output.json",
        env=env_field,
        command=lambda *a: "cmd",
        entrypoint=lambda *a: "entry",
    )
    settings = types.SimpleNamespace(timeout=1800, main=False, cpu_quota=None, mem_limit=None)
    return types.SimpleNamespace(
        tool=tool, settings=settings, absfn=str(contract), solc_path=None
    )


def _docker_args(sb_docker, task, sbdir):
    """Call the module-private ``__docker_args`` without tripping name mangling."""
    return getattr(sb_docker, "__docker_args")(task, sbdir)


# --- BA MODIFICATION 2: the allowlist ---------------------------------------


def test_forwards_only_declared_and_set_variables(sb_docker, tmp_path, monkeypatch):
    """``environment`` carries exactly the declared names that exist on the host.

    A name in ``env:`` that is unset must not appear at all — forwarding it as
    an empty string would override a default inside the image.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)
    monkeypatch.setenv("GPTSCAN_MODEL", "deepseek-v4-flash")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    task = _task("DEEPSEEK_API_KEY, OPENAI_API_KEY, GPTSCAN_MODEL", tmp_path)
    args = _docker_args(sb_docker, task, str(tmp_path))

    assert args["environment"] == {
        "DEEPSEEK_API_KEY": SECRET,
        "GPTSCAN_MODEL": "deepseek-v4-flash",
    }


def test_undeclared_host_variable_is_not_forwarded(sb_docker, tmp_path, monkeypatch):
    """A variable set on the host but absent from ``env:`` stays on the host.

    The field is an allowlist, not a filter: the container must not inherit the
    developer's whole environment.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)
    monkeypatch.setenv("UNRELATED_TOKEN", "must-not-leak")

    task = _task("DEEPSEEK_API_KEY", tmp_path)
    args = _docker_args(sb_docker, task, str(tmp_path))

    assert "UNRELATED_TOKEN" not in args["environment"]


def test_tool_without_env_field_gets_no_environment(sb_docker, tmp_path, monkeypatch):
    """Tools that declare nothing keep upstream behaviour: no ``environment`` key.

    This is what keeps the patch inert for Slither and the other 30+ tools.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)

    task = _task(None, tmp_path)
    args = _docker_args(sb_docker, task, str(tmp_path))

    assert "environment" not in args


# --- BA MODIFICATION 5: the redaction ---------------------------------------


def _run_execute(sb_docker, task, monkeypatch, tmp_path):
    """Drive ``execute`` against a fake container, returning its argument dict.

    The container is stubbed at ``client()``, so nothing contacts a daemon; the
    temp directory is a real one, since ``execute`` removes it in ``finally``.
    """
    sbdir = tmp_path / "sbdir"
    (sbdir / "bin").mkdir(parents=True)
    seen = {}

    class FakeContainer:
        def wait(self, timeout=None):
            return {"StatusCode": 0}

        def logs(self):
            return b"done"

        def get_archive(self, path):
            return ([b""], None)

        def kill(self):
            pass

        def remove(self):
            pass

    class FakeContainers:
        def run(self, **kwargs):
            # capture what the container actually received, before redaction
            seen.update(kwargs)
            return FakeContainer()

    monkeypatch.setattr(
        sb_docker, "client", lambda: types.SimpleNamespace(containers=FakeContainers())
    )
    monkeypatch.setattr(sb_docker, "__docker_volume", lambda _t: str(sbdir), raising=False)
    # __docker_volume is looked up as a module global inside execute()
    sb_docker.__dict__["__docker_volume"] = lambda _t: str(sbdir)

    *_, args = sb_docker.execute(task)
    return args, seen


def test_execute_returns_redacted_values(sb_docker, tmp_path, monkeypatch):
    """The returned args never carry a real value — they are persisted verbatim.

    ``sb/analysis.py`` writes this dict into ``results/**/smartbugs.json``. If
    the secret survived here, it would sit in clear text in the measurement
    data of every single task.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)
    task = _task("DEEPSEEK_API_KEY", tmp_path)

    args, _ = _run_execute(sb_docker, task, monkeypatch, tmp_path)

    assert args["environment"] == {"DEEPSEEK_API_KEY": "<redacted>"}
    assert SECRET not in repr(args)


def test_container_still_receives_the_real_value(sb_docker, tmp_path, monkeypatch):
    """Redaction must happen *after* the run, not instead of the passthrough.

    Without this test, replacing the forwarded values with ``<redacted>`` up
    front would still satisfy the test above while silently breaking every
    analysis: the tool would authenticate with the literal string.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)
    task = _task("DEEPSEEK_API_KEY", tmp_path)

    _, seen = _run_execute(sb_docker, task, monkeypatch, tmp_path)

    assert seen["environment"] == {"DEEPSEEK_API_KEY": SECRET}


def test_redaction_keeps_the_variable_names(sb_docker, tmp_path, monkeypatch):
    """Which variables were forwarded stays reconstructable from the results.

    The names carry no secret and are needed to tell afterwards how a run was
    parameterised — dropping the key entirely would lose that.
    """
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)
    monkeypatch.setenv("GPTSCAN_PROVIDER", "deepseek")
    task = _task("DEEPSEEK_API_KEY, GPTSCAN_PROVIDER", tmp_path)

    args, _ = _run_execute(sb_docker, task, monkeypatch, tmp_path)

    assert sorted(args["environment"]) == ["DEEPSEEK_API_KEY", "GPTSCAN_PROVIDER"]
    assert set(args["environment"].values()) == {"<redacted>"}
