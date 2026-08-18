"""SmartBugs result parser for LLMSmartAudit.

Converts the tool's audit-report JSON (chatdev/audit_report.py::render_data)
into SmartBugs findings. The finding ``name`` equals the detector display
title from the tool's DETECTORS table, which is also the key used in this
tool's ``findings.yaml`` to attach classification, severity and descriptions.

Note: the tool reasons over source text and emits NO line numbers, so the
findings carry no line/line_end keys. Severities are documentation-assigned
defaults per category, not model verdicts.

Reporting errors and fails
--------------------------
Unlike GPTScan, this tool writes plain (un-wrapped) output, so an uncaught
exception reaches stderr in the shape ``sb.parse_utils.errors_fails`` expects
and is classified as a *fail* without any help from this parser. The audit in
``analysis_tools/parser_audit.py`` confirms that: across the 147 LLMSmartAudit
tasks in this project it finds no message that fails to reach ``result.json``.

What this parser adds on top is a distinct message per way of *not* getting a
report, so "the container produced nothing" can be told apart from "the report
was truncated" -- see :func:`_read_output_json`. The entrypoint
(``scripts/do_solidity.sh``) guarantees a well-formed placeholder report and a
non-zero exit when the tool produced none, so the common case already surfaces
as an error.
"""

import io
import json
import os
import re
import tarfile
from typing import Optional

import sb.io
import sb.parse_utils

VERSION = "2026/08/02"

# All finding names the tool can emit: exactly the keys of findings.yaml,
# which mirror the 41 detector titles in chatdev/audit_report.py::DETECTORS.
# Loading them from findings.yaml keeps a single source of truth.
FINDINGS = set(
    sb.io.read_yaml(os.path.join(os.path.dirname(__file__), "findings.yaml")).keys()
)


def _read_output_json(output: Optional[bytes], fails: set) -> Optional[dict]:
    """Extract the audit report /output.json from the tar SmartBugs collected.

    Each way of failing is reported on its own rather than collapsing into a
    single "no output" message, so the reason stays visible in the CSV.
    """
    if not output:
        fails.add("no tar archive collected from the container")
        return None
    try:
        with tarfile.open(fileobj=io.BytesIO(output)) as tar:
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                if m.name.rsplit("/", 1)[-1] == "output.json":
                    fh = tar.extractfile(m)
                    if fh is None:
                        continue
                    raw = fh.read().decode("utf-8", errors="replace")
                    try:
                        return json.loads(raw)
                    except ValueError as e:
                        fails.add(f"output.json is not valid JSON: {e}")
                        return None
    except tarfile.TarError as e:
        fails.add(f"tar archive from the container is unreadable: {e}")
        return None
    fails.add("tar archive contains no output.json")
    return None


# The tool prints its per-call token arithmetic to stdout
# (camel/model_backend.py:144-153), so the context budget of every call is
# recoverable from the captured log without touching the tool.
CONTEXT_LIMIT = re.compile(r"num_max_token:\s*(\d+)")
COMPLETION_BUDGET = re.compile(r"num_max_completion_tokens \(after adjustment\):\s*(\d+)")
AGENT_ABORT = "max_tokens_exceeded_by_camel"


def _context_state(log: list, infos: set, errors: set) -> None:
    """Report how much context each call actually had.

    Two ways a contract can be too large, and neither raises or exits non-zero:

    * ``num_max_token - num_prompt_tokens`` floors at 1
      (``_cap_completion_tokens``), so the request goes out with
      ``max_tokens=1``. The model answers with a single token and the detector
      records nothing. Reads as a clean contract unless caught here.
    * above the agent's own limit camel terminates the call and names the
      reason (``camel/agents/chat_agent.py:274``).

    Both are *errors*: the tool stayed up, the analysis did not happen.

    Only the floor itself is treated as an error, because it is the tool's own
    boundary rather than a threshold chosen here. A merely tight budget --- say
    80 tokens --- is just as useless in practice but has no non-arbitrary cut
    off, so it is reported through the info line instead, where the smallest
    budget of the run stays visible in the data.
    """
    limits, budgets, aborted = [], [], False
    for line in log:
        m = CONTEXT_LIMIT.search(line)
        if m:
            limits.append(int(m.group(1)))
        m = COMPLETION_BUDGET.search(line)
        if m:
            budgets.append(int(m.group(1)))
        if AGENT_ABORT in line:
            aborted = True

    if limits or budgets:
        infos.add(
            "context window: %s tokens, smallest completion budget: %s"
            % (min(limits) if limits else "unknown",
               min(budgets) if budgets else "unknown")
        )
    if budgets and min(budgets) <= 1:
        errors.add(
            "context window exhausted: the completion budget fell to %d token(s)"
            " (num_max_token=%s), so detector answers were cut off -- an empty"
            " finding list here does not mean the contract is clean"
            % (min(budgets), min(limits) if limits else "unknown")
        )
    if aborted:
        errors.add(
            "context window exceeded: the agent aborted a call with"
            " %s; the contract was not fully analysed" % AGENT_ABORT
        )


def _meta(log: list) -> dict:
    """Parse the entrypoint's 'LLMSA_META {json}' line (provider/model/filename)."""
    for line in log:
        if line.startswith("LLMSA_META "):
            try:
                return json.loads(line[len("LLMSA_META "):].strip())
            except ValueError:
                return {}
    return {}


def parse(
    exit_code: Optional[int], log: list, output: Optional[bytes]
) -> tuple:
    """Turn one LLMSmartAudit task into ``(findings, infos, errors, fails)``.

    Called by ``sb/parsing.py``, both during a run and on every ``sb.reparse``
    of an existing result directory. The argument types are SmartBugs' stable
    parser contract: *log* is a list of lines, *output* the raw tar SmartBugs
    pulled out of the container (or None).

    The log is only read for the entrypoint's ``LLMSA_META`` line --- the
    report inside the tar is authoritative for provider, model and results,
    because the entrypoint can only report what it *asked* for, not what the
    tool actually used.
    """
    findings: list = []
    infos: set = set()
    errors, fails = sb.parse_utils.errors_fails(exit_code, log)

    _context_state(log, infos, errors)

    meta = _meta(log)
    filename = meta.get("filename")

    result = _read_output_json(output, fails)
    if result is None:
        return findings, infos, errors, fails

    # The report itself is authoritative for the backend actually used.
    provider = result.get("provider") or meta.get("provider")
    model = result.get("model") or meta.get("model")
    if provider or model:
        infos.add(f"LLMSmartAudit run: backend={provider}/{model}")
    total = result.get("categories_total")
    checked = result.get("categories_checked")
    if total is not None and checked is not None:
        infos.add(f"categories checked: {checked}/{total}")
        # No category checked means no analysis happened, whatever else the
        # report says -- an empty finding list must not read as "clean".
        if checked == 0:
            errors.add(f"LLMSmartAudit checked 0 of {total} detector categories:"
                       " the contract was not analysed")
    if result.get("error"):
        errors.add(str(result["error"]))

    # Timeout marker (AP5): stamped by the entrypoint when the run was cut
    # short. It goes into *errors*, never into *fails* -- the run was stopped on
    # purpose and produced a usable, if incomplete, result. The coverage figure
    # above already says how incomplete.
    sb_timeout = result.get("sb_timeout")
    if isinstance(sb_timeout, dict) and sb_timeout.get("hit"):
        stage = str(sb_timeout.get("stage", "unknown"))
        detail = sb_timeout.get("detail") or ""
        if total is not None and checked is not None:
            coverage = f" after {checked} of {total} detector categories"
        else:
            coverage = ""
        errors.add(f"TIMEOUT_{stage.upper()}: run cut short"
                   f"{coverage}" + (f" -- {detail}" if detail else ""))

    for f in result.get("findings", []) or []:
        finding = {"name": f.get("name", "LLMSmartAudit finding")}
        if filename:
            finding["filename"] = filename
        if f.get("severity"):
            finding["severity"] = str(f["severity"]).lower()

        msg_parts = []
        if f.get("description"):
            msg_parts.append(str(f["description"]))
        if f.get("detector"):
            msg_parts.append(f"Detector: {f['detector']}")
        if f.get("classification"):
            msg_parts.append(f"Classification: {f['classification']}")
        if msg_parts:
            finding["message"] = "\n".join(msg_parts)

        findings.append(finding)

    return findings, infos, errors, fails
