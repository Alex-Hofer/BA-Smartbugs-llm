"""SmartBugs result parser for GPTScan.

Converts GPTScan's JSON report (utils.convert_output) into SmartBugs findings.
The finding ``name`` equals GPTScan's ``output.title`` (e.g. "MWE-200: ..."),
which is the key used in this tool's ``findings.yaml`` to attach the SWC/DASP
classification, severity and descriptions.
"""

import io
import json
import os
import tarfile
from typing import Optional

import sb.parse_utils


VERSION = "2026/06/30"

# All finding names GPTScan can emit (the rule output titles). `findings`
# returned by parse() is a subset of this set.
FINDINGS = {
    "MWE-200: Insecure LP Token Value Calculation",
    "MWE-201: Insecure Vote Calculation",
    "MWE-202: Insecure Token Buying Behavior",
    "MWE-203: Approval Not Revoked",
    "MWE-204: Unsafe First Deposit",
    "MWE-205: Front Running",
    "MWE-206: No Slippage Limit Check",
    "MWE-207: Unauthorized Transfer",
    "MWE-208: Wrong Order for Checkpoint",
    "MWE-209: Wrong Order for Interest or ExchangeRate",
}


def _read_output_json(output: Optional[bytes]) -> Optional[dict]:
    """Extract GPTScan's /output.json from the tar archive SmartBugs collected."""
    if not output:
        return None
    try:
        with tarfile.open(fileobj=io.BytesIO(output)) as tar:
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                # the results file, not the .metadata.json sidecar
                if m.name.endswith("output.json") or m.name.rsplit("/", 1)[-1] == "output.json":
                    fh = tar.extractfile(m)
                    if fh is not None:
                        return json.loads(fh.read().decode("utf-8", errors="replace"))
    except Exception:
        return None
    return None


def _meta_info(log: list) -> Optional[str]:
    """Turn the entrypoint's 'GPTSCAN_META {json}' line into a concise info."""
    for line in log:
        if line.startswith("GPTSCAN_META "):
            payload = line[len("GPTSCAN_META "):].strip()
            try:
                meta = json.loads(payload)
                cost = meta.get("estimated_cost")
                calls = meta.get("llm_calls")
                provider = meta.get("provider")
                model = meta.get("model")
                parts = []
                if provider or model:
                    parts.append(f"backend={provider}/{model}")
                if calls is not None:
                    parts.append(f"llm_calls={calls}")
                if cost is not None:
                    parts.append(f"est_cost_usd={float(cost):.4f}")
                return "GPTScan run: " + ", ".join(parts) if parts else None
            except Exception:
                return None
    return None


def parse(
    exit_code: Optional[int], log: list, output: Optional[bytes]
) -> tuple:
    findings: list = []
    infos: set = set()
    errors, fails = sb.parse_utils.errors_fails(exit_code, log)

    meta = _meta_info(log)
    if meta:
        infos.add(meta)

    result = _read_output_json(output)
    if result is None:
        if not errors and not fails:
            fails.add("no GPTScan output produced")
        return findings, infos, errors, fails

    if result.get("message"):
        infos.add(str(result["message"]))

    for r in result.get("results", []) or []:
        finding = {"name": r.get("title", "GPTScan finding")}
        if r.get("severity"):
            finding["severity"] = str(r["severity"]).lower()

        affected = r.get("affectedFiles") or []
        msg_parts = []
        if r.get("description"):
            msg_parts.append(str(r["description"]))
        if r.get("recommendation"):
            msg_parts.append("Recommendation: " + str(r["recommendation"]))

        if affected:
            first = affected[0]
            fn = first.get("filePath")
            if fn:
                finding["filename"] = os.path.basename(fn)
            rng = first.get("range", {}) or {}
            start = (rng.get("start", {}) or {}).get("line")
            end = (rng.get("end", {}) or {}).get("line")
            if isinstance(start, int):
                finding["line"] = start
            if isinstance(end, int):
                finding["line_end"] = end
            if len(affected) > 1:
                extra = []
                for af in affected[1:]:
                    r2 = af.get("range", {}) or {}
                    s2 = (r2.get("start", {}) or {}).get("line")
                    e2 = (r2.get("end", {}) or {}).get("line")
                    extra.append(f"{os.path.basename(af.get('filePath', '?'))}:{s2}-{e2}")
                msg_parts.append("Also affects: " + ", ".join(extra))

        if r.get("code"):
            msg_parts.append(f"GPTScan code: {r['code']}")
        if msg_parts:
            finding["message"] = "\n".join(msg_parts)

        findings.append(finding)

    return findings, infos, errors, fails
