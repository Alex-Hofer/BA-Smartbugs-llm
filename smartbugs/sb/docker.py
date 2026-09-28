# ===========================================================================
# NOTE: this file differs from SmartBugs upstream 7ddaf6c (= v2.1.1-7-g7ddaf6c).
#
# Every own change is wrapped in a pair of numbered marker comments; grep for
# "BA MODIFICATION" to list them all. Deleting the five marked blocks — and
# restoring the upstream code quoted inside block 4 — returns this file to its
# upstream state. The same convention is used in sb/tools.py; those two files
# are the only ones in sb/ that carry own code.
#
#   1  import time                       required by block 3
#   2  env passthrough in __docker_args  API key / model into the container
#   3  rmtree_retry()                    Windows temp-dir cleanup
#   4  call to rmtree_retry() in execute replaces shutil.rmtree(sbdir)
#   5  redaction of args["environment"]  keeps API keys out of the results
#
# Blocks 2 and 5 belong together: 2 forwards the secret, 5 removes it again
# before the arguments are persisted. Never keep 2 without 5.
# Rationale for all of them: docs/BA-EIGENANTEIL.md, section 2.1.
# ===========================================================================

import os
import shutil
import tempfile
# --- BA MODIFICATION 1: BEGIN ---
import time
# --- BA MODIFICATION 1: END ---
import traceback
from typing import TYPE_CHECKING, Any, Optional

import docker
import docker.models.containers
import requests

import sb.debug
import sb.errors
import sb.io

if TYPE_CHECKING:
    import sb.tasks


_client: Optional[docker.DockerClient] = None


def client() -> docker.DockerClient:
    global _client
    if not _client:
        try:
            _client = docker.from_env()
            _client.info()
        except Exception:
            sb.debug.log(traceback.format_exc())
            raise sb.errors.SmartBugsError(
                "Docker: Cannot connect to service. Is it installed and running?"
            )
    return _client


images_loaded = set()


def is_loaded(image: str) -> bool:
    if image in images_loaded:
        return True
    try:
        image_list = client().images.list(image)
    except Exception as e:
        raise sb.errors.SmartBugsError(f"Docker: checking for image {image} failed.\n{e}")
    if image_list:
        images_loaded.add(image)
        return True
    return False


def load(image: str) -> None:
    try:
        client().images.pull(image)
    except Exception as e:
        raise sb.errors.SmartBugsError(f"Docker: Loading image {image} failed.\n{e}")
    images_loaded.add(image)


def __docker_volume(task: "sb.tasks.Task") -> str:
    sbdir = tempfile.mkdtemp()
    sbdir_bin = os.path.join(sbdir, "bin")
    if task.tool.mode in ("bytecode", "runtime"):
        # sanitize hex code
        code_lines = sb.io.read_lines(task.absfn)
        code = code_lines[0].strip() if code_lines else ""
        if code.startswith("0x"):
            code = code[2:]
        _, filename = os.path.split(task.absfn)
        sb.io.write_text(os.path.join(sbdir, filename), code)
    else:
        shutil.copy(task.absfn, sbdir)
    if task.tool.bin:
        shutil.copytree(task.tool.absbin, sbdir_bin)
    else:
        os.mkdir(sbdir_bin)
    if task.solc_path:
        sbdir_bin_solc = os.path.join(sbdir_bin, "solc")
        shutil.copyfile(task.solc_path, sbdir_bin_solc)
    return sbdir


def __docker_args(task: "sb.tasks.Task", sbdir: str) -> dict[str, Any]:
    args = {"volumes": {sbdir: {"bind": "/sb", "mode": "rw"}}, "detach": True, "user": 0}
    for k in ("image", "cpu_quota", "mem_limit", "network"):
        v = getattr(task.tool, k, None)
        if v is not None:
            args[k] = v
    if "network" not in args:
        args["network"] = "none"
    for k in ("cpu_quota", "mem_limit"):
        v = getattr(task.settings, k, None)
        if v is not None:
            args[k] = v
    filename = f"/sb/{os.path.split(task.absfn)[1]}"  # path in Linux Docker image
    timeout = task.settings.timeout or 0
    main = "1" if task.settings.main else "0"
    args["command"] = task.tool.command(filename, timeout, "/sb/bin", main)
    args["entrypoint"] = task.tool.entrypoint(filename, timeout, "/sb/bin", main)

    # --- BA MODIFICATION 2: BEGIN ---
    # Forward host environment variables declared in the tool's config.yaml
    # ("env: NAME1, NAME2, ...") into the container. This lets LLM-backed
    # tools (e.g. gptscan, llmsmartaudit) receive their API key and
    # provider/model selection at run time, instead of baking secrets into
    # the image. Only variables actually set on the host are forwarded.
    # Requires the "env" field added to sb/tools.py; without it, SmartBugs
    # refuses to load any tool whose config.yaml declares "env:".
    env_field = getattr(task.tool, "env", None)
    if env_field:
        names = [n.strip() for n in env_field.replace(",", " ").split() if n.strip()]
        env_passthrough = {n: os.environ[n] for n in names if n in os.environ}
        if env_passthrough:
            args["environment"] = env_passthrough
    # --- BA MODIFICATION 2: END ---

    return args


# --- BA MODIFICATION 3: BEGIN ---
def rmtree_retry(sbdir: str, attempts: int = 30, delay: float = 0.5) -> bool:
    """Delete a task's temporary directory, tolerating transient file locks.

    On Windows, Docker Desktop may still hold a handle on the bind-mounted
    directory when container.remove() has just returned. os.rmdir() on the
    (already emptied) "bin" subdirectory then fails with WinError 5. As this
    happens in the finally block of execute(), the PermissionError escapes as
    a non-SmartBugsError, which the retry loop in sb/analysis.py does not
    catch: the worker process dies before any result file is written, while
    the main process still exits with status 0.

    The lock is released within seconds, so retrying clears it. A directory
    that still cannot be removed is logged and left behind on purpose - a
    leftover temp directory must never discard a finished analysis.

    Returns True if the directory was removed.
    """
    for attempt in range(attempts):
        try:
            shutil.rmtree(sbdir)
            return True
        except OSError:
            if attempt == attempts - 1:
                sb.debug.log(
                    f"Could not remove temporary directory {sbdir}\n{traceback.format_exc()}"
                )
                return False
            time.sleep(delay)
    return False
# --- BA MODIFICATION 3: END ---


def execute(
    task: "sb.tasks.Task",
) -> tuple[Optional[int], list[str], Optional[bytes], dict[str, Any]]:
    sbdir = __docker_volume(task)
    args = __docker_args(task, sbdir)
    exit_code, logs, output, sb_bin_log, container = None, [], None, [], None
    try:
        container = client().containers.run(**args)
        try:
            result = container.wait(timeout=task.settings.timeout)
            exit_code = result["StatusCode"]
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            try:
                container.stop(timeout=10)
            except docker.errors.APIError:
                pass
        logs = container.logs().decode("utf8").splitlines()
        if task.tool.output:
            try:
                output, _ = container.get_archive(task.tool.output)
                output = b"".join(output)
            except docker.errors.NotFound:
                pass

    except Exception as e:
        raise sb.errors.SmartBugsError(f"Problem running Docker container: {e})")

    finally:
        try:
            container.kill()
        except Exception:
            pass
        try:
            container.remove()
        except Exception:
            pass
        try:
            sb_bin_log_path = os.path.join(sbdir, "bin", "log")
            sb_bin_log = sb.io.read_lines(sb_bin_log_path)
        except Exception:
            pass
        # --- BA MODIFICATION 4: BEGIN ---
        # Upstream line, restore it to undo this block:
        #         shutil.rmtree(sbdir)
        rmtree_retry(sbdir)
        # --- BA MODIFICATION 4: END ---

    # --- BA MODIFICATION 5: BEGIN ---
    # The returned args end up verbatim in results/**/smartbugs.json via
    # sb/analysis.py. Redact forwarded environment values (API keys!) so they
    # are never persisted; the container already received the real values.
    if "environment" in args:
        args["environment"] = {k: "<redacted>" for k in args["environment"]}
    # --- BA MODIFICATION 5: END ---

    return exit_code, logs, output, sb_bin_log, args
