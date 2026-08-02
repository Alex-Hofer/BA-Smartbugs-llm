"""Aggregate a SmartBugs gptscan run into one Markdown summary report.

Walks a SmartBugs results tree (…/<TOOL>/<RUNID>/<FILENAME>/result.json), reads
each contract's findings (from result.json) and run metadata (from the
`GPTSCAN_META {…}` line in result.log), and writes a combined Markdown report:
findings per contract, findings per category (with SWC/DASP labels), and grand
totals (LLM calls, tokens, cost). Works for both --dry-run and live result trees.

Usage:
    python scripts/aggregate_smartbugs.py <results_dir> [out.md]
"""

import glob
import json
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None

_TAXONOMY = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "taxonomy", "findings.yaml"))


def load_taxonomy():
    if yaml is None or not os.path.exists(_TAXONOMY):
        return {}
    with open(_TAXONOMY, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_meta(result_log):
    try:
        with open(result_log, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("GPTSCAN_META "):
                    return json.loads(line[len("GPTSCAN_META "):].strip())
    except Exception:
        pass
    return {}


def collect(results_dir):
    rows = []
    for rj in glob.glob(os.path.join(results_dir, "**", "result.json"), recursive=True):
        try:
            with open(rj, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        meta = read_meta(os.path.join(os.path.dirname(rj), "result.log"))
        rows.append({
            "contract": os.path.basename(os.path.dirname(rj)),
            "findings": data.get("findings", []) or [],
            "errors": data.get("errors", []) or [],
            "fails": data.get("fails", []) or [],
            "meta": meta,
        })
    rows.sort(key=lambda r: r["contract"])
    return rows


def render(rows, taxonomy, dry):
    L = []
    mode = "Dry-run projection" if dry else "Live run"
    L.append(f"# GPTScan via SmartBugs — {mode} summary")
    L.append("")
    provider = next((r["meta"].get("provider") for r in rows if r["meta"].get("provider")), "?")
    model = next((r["meta"].get("model") for r in rows if r["meta"].get("model")), "?")
    L.append(f"Backend: **{provider} / {model}**  ·  Contracts: **{len(rows)}**")
    L.append("")

    # per contract
    L.append("## Per contract")
    L.append("")
    L.append("| Contract | Findings | Categories | LLM calls | Cost (USD) |")
    L.append("| --- | --- | --- | --- | --- |")
    tot_calls = tot_cost = tot_sent = tot_recv = 0
    cat_counts = {}
    tot_findings = 0
    for r in rows:
        m = r["meta"]
        calls = m.get("llm_calls", 0) or 0
        cost = m.get("estimated_cost", 0) or 0
        tot_calls += calls
        tot_cost += cost
        tot_sent += m.get("token_sent", 0) or 0
        tot_recv += m.get("token_received", 0) or 0
        cats = []
        for fnd in r["findings"]:
            name = fnd.get("name", "?")
            cats.append(name.split(":")[0])  # MWE id
            cat_counts[name] = cat_counts.get(name, 0) + 1
            tot_findings += 1
        note = ""
        if r["fails"]:
            note = " ⚠fail"
        L.append(f"| {r['contract']}{note} | {len(r['findings'])} | "
                 f"{', '.join(sorted(set(cats))) or '—'} | {calls} | {cost:.4f} |")
    L.append(f"| **Total** | **{tot_findings}** | | **{tot_calls}** | **{tot_cost:.4f}** |")
    L.append("")

    # per category
    L.append("## Findings per category")
    L.append("")
    L.append("| Category (MWE) | Taxonomy | Count |")
    L.append("| --- | --- | --- |")
    if cat_counts:
        for name, cnt in sorted(cat_counts.items(), key=lambda kv: -kv[1]):
            clazz = (taxonomy.get(name) or {}).get("classification", "n/a")
            L.append(f"| {name} | {clazz} | {cnt} |")
    else:
        L.append("| _none_ | | 0 |")
    L.append("")

    # totals
    L.append("## Totals")
    L.append("")
    L.append(f"- Contracts scanned: **{len(rows)}**")
    L.append(f"- Findings: **{tot_findings}**")
    L.append(f"- LLM calls{' (projected)' if dry else ''}: **{tot_calls}**")
    L.append(f"- Tokens sent / received: **{int(tot_sent)} / {int(tot_recv)}**")
    L.append(f"- Estimated cost{' (projected)' if dry else ''}: **${tot_cost:.4f}**")
    fails = [r["contract"] for r in rows if r["fails"]]
    if fails:
        L.append(f"- Contracts with tool failures: {', '.join(fails)}")
    L.append("")
    return "\n".join(L)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    results_dir = sys.argv[1]
    out_md = sys.argv[2] if len(sys.argv) > 2 else os.path.join(results_dir, "summary.md")
    rows = collect(results_dir)
    dry = any(r["meta"].get("dry_run") for r in rows)
    md = render(rows, load_taxonomy(), dry)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    print(f"\n[written] {out_md}")


if __name__ == "__main__":
    main()
