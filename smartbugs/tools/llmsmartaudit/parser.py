"""SmartBugs result parser for LLMSmartAudit.

Converts the tool's audit-report JSON (chatdev/audit_report.py::render_data)
into SmartBugs findings. The finding ``name`` equals the detector display
title from the tool's DETECTORS table, which is also the key used in this
tool's ``findings.yaml`` to attach classification, severity and descriptions.

Note: the tool reasons over source text and emits NO line numbers, so the
findings carry no line/line_end keys. Severities are documentation-assigned
defaults per category, not model verdicts.
"""

import io
import json
import os
import tarfile
from typing import Optional

import sb.io
import sb.parse_utils

VERSION = "2026/07/05"

# All finding names the tool can emit: exactly the keys of findings.yaml,
# which mirror the 41 detector titles in chatdev/audit_report.py::DETECTORS.
# Loading them from findings.yaml keeps a single source of truth.
FINDINGS = set(
    sb.io.read_yaml(os.path.join(os.path.dirname(__file__), "findings.yaml")).keys()
)


def _read_output_json(output: Optional[bytes]) -> Optional[dict]:
    """Extract the audit report /output.json from the tar archive SmartBugs collected."""
    if not output:
        return None
    try:
        with tarfile.open(fileobj=io.BytesIO(output)) as tar:
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                if m.name.rsplit("/", 1)[-1] == "output.json":
                    fh = tar.extractfile(m)
                    if fh is not None:
                        return json.loads(fh.read().decode("utf-8", errors="replace"))
    except Exception:
        return None
    return None


def _meta(log: list) -> dict:
    """Parse the entrypoint's 'LLMSA_META {json}' line (provider/model/filename)."""
    for line in log:
        if line.startswith("LLMSA_META "):
            try:
                return json.loads(line[len("LLMSA_META "):].strip())
            except Exception:
                return {}
    return {}


def parse(
    exit_code: Optional[int], log: list, output: Optional[bytes]
) -> tuple:
    findings: list = []
    infos: set = set()
    errors, fails = sb.parse_utils.errors_fails(exit_code, log)

    meta = _meta(log)
    filename = meta.get("filename")

    result = _read_output_json(output)
    if result is None:
        if not errors and not fails:
            fails.add("no LLMSmartAudit output produced")
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
