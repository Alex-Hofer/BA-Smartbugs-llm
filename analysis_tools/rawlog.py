"""Shared helpers for reading the raw material SmartBugs stores per task.

A SmartBugs task directory holds four artefacts:

===================  ==========================================================
``smartbugs.json``   task log: tool config, exit code, duration, environment
``result.log``       everything the container wrote to stdout/stderr
``result.tar``       the file(s) SmartBugs pulled out of the container
``result.json``      what the tool's ``parser.py`` made of the three above
===================  ==========================================================

Only the first three are raw material; ``result.json`` is derived and can be
regenerated at any time with ``python -m sb.reparse``.

De-wrapping ``result.log``
--------------------------
GPTScan logs through ``rich``, which renders every log record as a padded,
hard-wrapped block and right-aligns a ``source.py:LINE`` marker on the record's
first physical line::

    [07:13:59] Traceback (most recent call last):                   tasks.py:177
                 File
               "/usr/local/lib/python3.10/site-packages/crytic_compile/
               platform/solc.py", line 575, in _run_solc

``sb.parse_utils.exceptions()`` cannot see such a traceback: the first line does
not *end* with ``"Traceback (most recent call last):"`` and every following line
is indented, so the "first unindented line ends the traceback" rule never fires.
That is the mechanical reason for GPTScan's silent failures.

:func:`log_records` reverses the rendering by dropping the ``source.py:LINE``
marker and the leading timestamp, then joining a record's continuation lines
with a single space.

Known limitation: reflowing cannot be exact, and no heuristic fixes it.
``rich`` pads every rendered line to the block width, so a line ending at that
width may have been broken at a space (consumed) or inside a token (not
consumed) --- the two are indistinguishable afterwards. The space-join is right
for prose and occasionally inserts a space into a long unbroken token, e.g.
``crytic_compile/ platform/solc.py``. The effect is cosmetic and confined to
long paths; exception classes and message wording reflow correctly. Nothing is
lost either way, since ``result.log`` itself is never modified.
"""

import io
import json
import os
import re
import tarfile
from typing import Any, Optional

TASK_LOG = "smartbugs.json"
TOOL_LOG = "result.log"
TOOL_OUTPUT = "result.tar"
PARSER_OUTPUT = "result.json"

# ``rich`` right-aligns the emitting source location on a record's first line.
_RICH_SRC = re.compile(r"\s+[\w.\-/]{1,80}\.(?:py|pyx):\d{1,7}\s*$")
# The marker sits at the very end of the line, so only the tail is searched.
# Scanning whole lines is quadratic: ``\s+ ... $`` retries at every whitespace
# run, and LLMSmartAudit writes single log lines hundreds of kilobytes long.
_RICH_SRC_TAIL = 160
# ... and prefixes it with a timestamp, e.g. "[07:13:59] " or "[07/01/26 07:13:58] ".
_RICH_TS = re.compile(r"^\[[\d/:. ]+\]\s")


def squash(text: str) -> str:
    """Strip *all* whitespace.

    Marker lookups against squashed text are immune to ``rich``'s line breaks,
    which is why every detector in :mod:`analysis_tools.parser_audit` matches
    against ``squash(...)`` rather than against the raw log.

    ``split()``/``join()`` rather than a regex: the largest log in this project
    is 25 MB and gets squashed once per audit run.
    """
    return "".join(text.split())


def log_records(lines: list[str]) -> list[str]:
    """Reassemble ``rich``-wrapped console output into logical records.

    Plain (non-``rich``) output is passed through unchanged: an unindented line
    always starts a new record, so a raw stderr traceback keeps its own frames
    as separate records, exactly as ``sb.parse_utils`` expects to see them.
    """
    records: list[str] = []
    current: list[str] = []          # parts, joined once -- "current += part" on a
    for raw in lines:                # str would be quadratic on a 25 MB log
        line = raw.rstrip()
        if not line:
            continue
        tail = line[-_RICH_SRC_TAIL:]
        m = _RICH_SRC.search(tail)
        if m:
            line = line[: len(line) - len(tail) + m.start()]
        body = _RICH_TS.sub("", line).strip()
        if not body:
            continue
        # A record starts on a line carrying the source marker, on a timestamped
        # line, or on any line that begins at column 0 (i.e. is not a wrap).
        starts_record = bool(m) or bool(_RICH_TS.match(line)) or not line.startswith(" ")
        if starts_record and current:
            records.append(" ".join(current))
            current = []
        current.append(body)
    if current:
        records.append(" ".join(current))
    return records


# Final line of a Python traceback: "pkg.mod.SomeError: message".
# The dotted prefix is an *atomic* group: without it, a record full of Solidity
# member chains (``pool.state.reserves.asset``) sends the engine into
# exponential backtracking at every start position.
_FINAL_EXC = re.compile(
    r"(?>(?:[A-Za-z_]\w*\.)*)[A-Za-z_]\w*"
    r"(?:Error|Exception|Interrupt|Exit|Timeout|Failure)"
    r":\s"
)


def final_exception(record: str) -> Optional[str]:
    """Return the outermost ``Module.Error: message`` of a de-wrapped traceback.

    Chained tracebacks ("During handling of the above exception, another
    exception occurred") end up in a single record; the *last* match is the one
    that actually escaped, which is the same choice ``sb.parse_utils.exceptions``
    makes for unwrapped tracebacks.
    """
    matches = list(_FINAL_EXC.finditer(record))
    if not matches:
        return None
    return record[matches[-1].start():].strip()


def read_task(task_dir: str) -> dict[str, Any]:
    """Load one task directory's raw material plus its parser output.

    Returns a dict with keys ``dir``, ``task_log``, ``exit_code``, ``tool``,
    ``runid``, ``filename``, ``log_lines``, ``records``, ``tar_state``,
    ``output_json`` and ``parser_output``. Missing or unreadable artefacts are
    reported through ``tar_state`` / ``None`` values rather than raising, so an
    audit run never aborts on a single damaged task.
    """
    task_log = _read_json(os.path.join(task_dir, TASK_LOG)) or {}

    log_path = os.path.join(task_dir, TOOL_LOG)
    log_lines: list[str] = []
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8", errors="replace") as fh:
            log_lines = fh.read().splitlines()

    output_json, tar_state = None, "missing"
    tar_path = os.path.join(task_dir, TOOL_OUTPUT)
    if os.path.exists(tar_path):
        tar_state = "ok"
        try:
            with tarfile.open(tar_path) as tar:
                members = [m for m in tar.getmembers() if m.isfile()]
                if not members:
                    tar_state = "empty"
                for m in members:
                    if m.name.rsplit("/", 1)[-1] != "output.json":
                        continue
                    fh = tar.extractfile(m)
                    if fh is None:
                        continue
                    try:
                        output_json = json.loads(fh.read().decode("utf-8", errors="replace"))
                    except ValueError:
                        tar_state = "bad-json"
        except (tarfile.TarError, OSError):
            tar_state = "unreadable"

    return {
        "dir": task_dir,
        "task_log": task_log,
        "exit_code": task_log.get("result", {}).get("exit_code"),
        "tool": task_log.get("tool", {}).get("id", "?"),
        "runid": task_log.get("runid", "?"),
        "filename": task_log.get("filename", "?"),
        "log_lines": log_lines,
        "records": log_records(log_lines),
        "tar_state": tar_state,
        "output_json": output_json,
        "parser_output": _read_json(os.path.join(task_dir, PARSER_OUTPUT)),
    }


def find_task_dirs(roots: list[str]) -> list[str]:
    """Every directory below *roots* that holds a SmartBugs task log."""
    found: set[str] = set()
    for root in roots:
        for path, _dirs, files in os.walk(root):
            if TASK_LOG in files:
                found.add(path)
    return sorted(found)


def _read_json(path: str) -> Optional[Any]:
    """Parse a JSON file, or return None if it is missing or malformed."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None
