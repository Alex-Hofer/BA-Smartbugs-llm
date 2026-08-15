"""Liest die GPTSCAN_META-Zeilen eines SmartBugs-GPTScan-Laufs aus.

Die Rohergebnisse unter smartbugs/results/ bleiben unangetastet; dieses Skript
liest nur. Ausgegeben werden Token-, Kosten- und Laufzeitkennzahlen je Task und
in Summe -- die Grundlage fuer die Kostenhochrechnung und spaeter fuer
eval/<runid>/run_meta.json.

Aufruf:
    python analysis_tools/gptscan_run_stats.py <RUNDIR> [--json OUT.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys


def meta_of(log_path: pathlib.Path) -> dict | None:
    """Die letzte GPTSCAN_META-Zeile eines result.log, oder None."""
    try:
        raw = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    found = None
    for line in raw.splitlines():
        if line.startswith("GPTSCAN_META "):
            try:
                found = json.loads(line[len("GPTSCAN_META "):].strip())
            except ValueError:
                found = {}
    return found


def task_rows(rundir: pathlib.Path) -> list[dict]:
    rows = []
    for sbjson in sorted(rundir.rglob("smartbugs.json")):
        taskdir = sbjson.parent
        try:
            sb = json.loads(sbjson.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            sb = {}
        meta = meta_of(taskdir / "result.log") or {}
        res = {}
        rj = taskdir / "result.json"
        if rj.exists():
            try:
                res = json.loads(rj.read_text(encoding="utf-8", errors="replace"))
            except ValueError:
                res = {}
        # Laufzeit/Exit-Code stehen in smartbugs.json unter "result", der
        # tatsaechlich verwendete MAIN-Wert im Docker-Entrypoint.
        sbres = sb.get("result", {}) or {}
        entry = (sb.get("docker", {}) or {}).get("entrypoint", "") or ""
        rows.append({
            "contract": taskdir.name,
            "dir": str(taskdir),
            "duration": sbres.get("duration"),
            "exit_code": sbres.get("exit_code"),
            "entrypoint": entry,
            "main": entry.rstrip().endswith("'1'"),
            "findings": len(res.get("findings", []) or []),
            "finding_names": [f.get("name") for f in (res.get("findings", []) or [])],
            "n_errors": len(res.get("errors", []) or []),
            "n_fails": len(res.get("fails", []) or []),
            "errors": res.get("errors", []) or [],
            "fails": res.get("fails", []) or [],
            "infos": res.get("infos", []) or [],
            "meta": meta,
            "cost": meta.get("estimated_cost"),
            "llm_calls": meta.get("llm_calls"),
            "used_time": meta.get("used_time"),
            "loc": meta.get("loc"),
            "prompt_tokens": meta.get("token_sent"),
            "completion_tokens": meta.get("token_received"),
            "dry_run": meta.get("dry_run"),
        })
    return rows


def summarise(rows: list[dict]) -> dict:
    def nums(key):
        return [r[key] for r in rows if isinstance(r.get(key), (int, float))]

    costs, durs = nums("cost"), nums("duration")
    pt, ct, calls = nums("prompt_tokens"), nums("completion_tokens"), nums("llm_calls")
    return {
        "tasks": len(rows),
        "cost_sum": sum(costs), "cost_n": len(costs),
        "cost_avg": (sum(costs) / len(costs)) if costs else None,
        "cost_med": statistics.median(costs) if costs else None,
        "cost_max": max(costs) if costs else None,
        "dur_sum": sum(durs), "dur_avg": (sum(durs) / len(durs)) if durs else None,
        "dur_med": statistics.median(durs) if durs else None,
        "dur_max": max(durs) if durs else None,
        "prompt_tokens_sum": sum(pt), "completion_tokens_sum": sum(ct),
        "llm_calls_sum": sum(calls),
        "findings_sum": sum(r["findings"] for r in rows),
        "contracts_with_findings": sum(1 for r in rows if r["findings"] > 0),
        "tasks_with_errors": sum(1 for r in rows if r["n_errors"]),
        "tasks_with_fails": sum(1 for r in rows if r["n_fails"]),
        "tasks_degraded": sum(1 for r in rows
                              if any("analysis degraded" in i for i in r["infos"])),
        "tasks_without_meta": sum(1 for r in rows if not r["meta"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rundir", type=pathlib.Path)
    ap.add_argument("--json", type=pathlib.Path, help="Rohzeilen als JSON ablegen")
    args = ap.parse_args()

    if not args.rundir.is_dir():
        print(f"kein Verzeichnis: {args.rundir}", file=sys.stderr)
        return 2

    rows = task_rows(args.rundir)
    s = summarise(rows)
    print(f"Lauf:                 {args.rundir}")
    print(f"Tasks:                {s['tasks']}")
    print(f"Findings gesamt:      {s['findings_sum']} auf {s['contracts_with_findings']} Contracts")
    print(f"Kosten (n={s['cost_n']}): sum ${s['cost_sum']:.4f} | avg ${(s['cost_avg'] or 0):.5f}"
          f" | med ${(s['cost_med'] or 0):.5f} | max ${(s['cost_max'] or 0):.5f}")
    print(f"Laufzeit:             sum {s['dur_sum']:.0f}s | avg {(s['dur_avg'] or 0):.1f}s"
          f" | med {(s['dur_med'] or 0):.1f}s | max {(s['dur_max'] or 0):.1f}s")
    print(f"Tokens:               prompt {s['prompt_tokens_sum']} | completion {s['completion_tokens_sum']}"
          f" | llm_calls {s['llm_calls_sum']}")
    print(f"Tasks mit errors:     {s['tasks_with_errors']}")
    print(f"Tasks mit fails:      {s['tasks_with_fails']}")
    print(f"Tasks 'degraded':     {s['tasks_degraded']}   (nicht uebersetzt -> 'keine Findings' unbestimmt)")
    print(f"Tasks ohne META:      {s['tasks_without_meta']}")

    if args.json:
        args.json.write_text(json.dumps({"summary": s, "tasks": rows}, indent=1),
                             encoding="utf-8")
        print(f"geschrieben: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
