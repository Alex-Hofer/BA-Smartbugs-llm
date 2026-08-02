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
