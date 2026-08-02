#!/usr/bin/env python3
"""Aggregate a GPTScan SmartBugs run over mwevariety_fixed.

Usage: python corpus_tools/analyze_run.py <run_dir>
Reads every task's result.json + GPTSCAN_META line from result.log and reports:
  - findings by MWE rule and severity
  - static-confirmation activity (candidates filtered by the static stage)
  - compile failures / degradation
  - total estimated cost
Writes <run_dir>.analysis.json next to corpus_tools/ and prints a summary.
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter

BA = Path(__file__).resolve().parent.parent


def meta_of(log: Path):
    if not log.is_file():
        return None
    txt = log.read_text(encoding="utf-8", errors="replace").replace("\r", "")
    m = None
    for line in txt.splitlines():
        if line.startswith("GPTSCAN_META "):
            m = line[len("GPTSCAN_META "):]
    if not m:
        return None
    try:
        return json.loads(m)
    except Exception:
        return None


def findings_of(result_json: Path):
    if not result_json.is_file():
        return []
    try:
        d = json.loads(result_json.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    return d.get("results") or d.get("findings") or []


def main() -> int:
    run = Path(sys.argv[1])
    tasks = sorted(run.rglob("result.json"))
    per_file, findings_rows = {}, []
    mwe = Counter()
    sev = Counter()
    static_ran = compile_fail = degraded = 0
    cost = 0.0
    for rj in tasks:
        name = rj.parent.name
        log = rj.parent / "result.log"
        meta = meta_of(log)
        fnd = findings_of(rj)
        raw = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        cf = ("InvalidCompilation" in raw) or ("Compile failed" in raw)
        compile_fail += int(cf)
        rec = {"findings": len(fnd), "compile_failed": cf}
        if meta:
            cost += float(meta.get("estimated_cost") or 0)
            s2 = meta.get("functions_after_step_2") or 0
            sa = meta.get("functions_after_static")
            vb = meta.get("vul_before_static") or 0
            va = meta.get("vul_after_static") or 0
            if s2 and sa is not None:
                static_ran += 1
            if vb > va:
                degraded += 1  # static stage rejected >=1 candidate
            rec.update(step2=s2, after_static=sa, vul_before=vb, vul_after=va)
        for f in fnd:
            fname = f.get("name") or ""
            mm = re.search(r"MWE-\d+", fname)
            rule = mm.group(0) if mm else (fname or "?")
            severity = (f.get("severity") or f.get("impact") or "?")
            mwe[str(rule)] += 1
            sev[str(severity).lower()] += 1
            findings_rows.append({"contract": name, "rule": str(rule),
                                  "name": fname, "line": f.get("line"),
                                  "severity": str(severity)})
        per_file[name] = rec

    with_find = sum(1 for r in per_file.values() if r["findings"] > 0)
    total_find = sum(r["findings"] for r in per_file.values())
    out = {
        "run": str(run), "tasks": len(tasks),
        "compile_failures": compile_fail,
        "compile_ok": len(tasks) - compile_fail,
        "static_stage_ran": static_ran,
        "contracts_static_filtered": degraded,
        "contracts_with_findings": with_find,
        "total_findings": total_find,
        "by_rule": dict(mwe.most_common()),
        "by_severity": dict(sev.most_common()),
        "estimated_cost_usd": round(cost, 4),
        "findings": findings_rows,
    }
    dst = BA / "corpus_tools" / (run.name + ".analysis.json")
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"tasks={out['tasks']}  compile_ok={out['compile_ok']}/{out['tasks']}"
          f"  static_ran={static_ran}  static_filtered={degraded}")
    print(f"findings: {total_find} auf {with_find} Contracts  |  Kosten ~${out['estimated_cost_usd']}")
    print(f"by_rule: {out['by_rule']}")
    print(f"by_severity: {out['by_severity']}")
    print(f"-> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
