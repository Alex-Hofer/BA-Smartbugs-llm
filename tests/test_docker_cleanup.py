"""Regression tests for the temp-directory cleanup in ``sb/docker.py``.

Background
----------
``sb.docker.execute`` runs each task in a container with a temporary host
directory bind-mounted at ``/sb``, and removes that directory in its ``finally``
block. On Windows, Docker Desktop can still hold a handle on the mounted
directory when ``container.remove()`` has just returned, so ``os.rmdir()`` on
the (already emptied) ``bin`` subdirectory fails with ``WinError 5``.

The plain ``shutil.rmtree`` that used to sit there raised ``PermissionError``
out of the ``finally`` block. That is not a ``SmartBugsError``, so the retry
loop in ``sb/analysis.py`` did not catch it: the worker process died *before*
``result.json`` was written, while the main process still reported exit
status 0 — a silent, total loss of results. Observed on 2026-08-02 with Docker
Desktop server 29.0.1, reproducibly in all four worker processes.

These tests pin the two properties that prevent that loss: a transient lock is
survived, and a permanent one is reported instead of thrown.
"""

import os
import sys
import types

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMARTBUGS = os.path.join(REPO_ROOT, "smartbugs")

if SMARTBUGS not in sys.path:
    sys.path.insert(0, SMARTBUGS)


def _stub_docker_sdk() -> None:
    """Register placeholder modules for the Docker SDK and ``requests``.

    ``sb/docker.py`` imports both at module level and evaluates the annotation
    ``Optional[docker.DockerClient]`` at import time, but the cleanup helper
    under test touches only the file system. Stubbing keeps these tests
    runnable with the plain system interpreter, which has no Docker SDK.
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


def _populated_dir(tmp_path):
    """A temp directory shaped like the one ``__docker_volume`` builds."""
    sbdir = tmp_path / "sbdir"
    (sbdir / "bin").mkdir(parents=True)
    (sbdir / "bin" / "solc").write_bytes(b"binary")
    (sbdir / "Contract.sol").write_text("contract C {}", encoding="utf-8")
    return str(sbdir)


def test_removes_unlocked_directory(sb_docker, tmp_path):
    """The ordinary case: nothing holds the directory, it disappears."""
    sbdir = _populated_dir(tmp_path)

    assert sb_docker.rmtree_retry(sbdir) is True
    assert not os.path.exists(sbdir)


def test_survives_transient_lock(sb_docker, tmp_path, monkeypatch):
    """A lock that clears after a few attempts must not surface at all.

    This is the observed Windows behaviour: the handle is released within
    seconds, so the removal succeeds on a later attempt.
    """
    sbdir = _populated_dir(tmp_path)
    real_rmtree = sb_docker.shutil.rmtree
    attempts = []

    def flaky(path, *args, **kwargs):
        attempts.append(path)
        if len(attempts) < 3:
            raise PermissionError(5, "Zugriff verweigert", os.path.join(path, "bin"))
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(sb_docker.shutil, "rmtree", flaky)
    monkeypatch.setattr(sb_docker.time, "sleep", lambda _: None)

    assert sb_docker.rmtree_retry(sbdir) is True
    assert len(attempts) == 3
    assert not os.path.exists(sbdir)


def test_permanent_lock_is_reported_not_raised(sb_docker, tmp_path, monkeypatch):
    """A directory that never unlocks is logged and left behind, never thrown.

    The exception must not escape: it would run up through ``execute``'s
    ``finally`` block and discard an analysis that has already finished.
    """
    sbdir = _populated_dir(tmp_path)
    logged = []

    def always_locked(path, *args, **kwargs):
        raise PermissionError(5, "Zugriff verweigert", os.path.join(path, "bin"))

    monkeypatch.setattr(sb_docker.shutil, "rmtree", always_locked)
    monkeypatch.setattr(sb_docker.time, "sleep", lambda _: None)
    monkeypatch.setattr(sb_docker.sb.debug, "log", lambda msg: logged.append(msg))

    assert sb_docker.rmtree_retry(sbdir, attempts=4) is False
    assert os.path.exists(sbdir)
    assert len(logged) == 1
    assert sbdir in logged[0]
    assert "PermissionError" in logged[0]
