"""Export a SmartBugs LLMSmartAudit run into the evaluation format.

Produces, per run id, under ``eval/<runid>/``:

* ``findings.jsonl``  one line per finding, field names shared with the GPTScan
                      export so both tools can be concatenated;
* ``run_meta.json``   what was run, with what, how long it took and what it
                      cost;
* ``summary.md``      findings per category and per contract, failure rates,
                      contracts without findings.

Three things this deliberately does *not* do.

It does not copy the taxonomy. ``smartbugs/tools/llmsmartaudit/findings.yaml``
is the single source for classification and severity; every derived field here
is computed from it at export time, and the raw classification string travels
with each row so any derivation can be redone without re-running the analysis.

It does not invent per-finding data. The tool emits no line numbers, no
function names, no confidence and no severity --- it reasons over source text.
Those fields stay ``null``. The severity from findings.yaml is exported
separately as ``severity_doc``, so it can never be mistaken for a model
verdict.

It does not let a contract that was never analysed look clean. ``task_state``
separates "no findings" from "context exceeded", "no output" and "failed";
usage: python analysis_tools/build_eval.py RUNID [RUNID ...]
"""

import collections
import datetime
import glob
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SB = os.path.join(REPO_ROOT, "smartbugs")
TAXONOMY = os.path.join(SB, "tools", "llmsmartaudit", "findings.yaml")

DASP = re.compile(r"\bDASP-(\d+)\b")

# Prices for deepseek-v4-flash, back-computed from the curated_v1_20260705 run
# ($2.44 at 12.55M prompt / 3.52M completion tokens), keeping the 1:4.07
# input/output ratio of the published deepseek-chat prices. The tool's own
# accounting is unusable: chatdev/statistics.py::prompt_cost has no entry for
# this model id and reports $0.0000 throughout. The authoritative figure is the
# DeepSeek invoice; both are recorded in run_meta.json.
PRICE_PROMPT_PER_M = 0.0908
PRICE_COMPLETION_PER_M = 0.3695

USAGE = re.compile(r"prompt_tokens: (\d+)\s*\ncompletion_tokens: (\d+)")


def dasp10(classification: str) -> str:
    """The DASP class findings.yaml states, or "" if it states none."""
    m = DASP.search(classification or "")
    return "DASP-%s" % m.group(1) if m else ""


def is_defi_logic(classification: str) -> bool:
    """Is this one of the DeFi logic categories, in the GPTScan sense?

    Only the explicit ``logic/DeFi`` label qualifies. See
    tests/test_build_eval.py for why the plain ``logic`` labels do not.
    """
    return (classification or "").startswith("logic/DeFi")


def task_state(findings: list, errors: list, fails: list) -> str:
    """One of findings / context_exceeded / no_output / failed / clean.

    Order matters: a context abort explains the empty finding list, so it
    outranks the generic "no report" and "exception" messages that accompany
    it.
    """
    if findings:
        return "findings"
    if any("context window" in m for m in errors):
        return "context_exceeded"
    if any("no report produced" in m for m in errors) or errors:
        return "no_output"
    if fails:
        return "failed"
    return "clean"


def load_taxonomy() -> dict:
    import yaml
    with open(TAXONOMY, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def backend(infos: list) -> tuple:
    for i in infos:
        if i.startswith("LLMSmartAudit run: backend="):
            value = i.split("backend=", 1)[1]
            provider, _, model = value.partition("/")
            return provider, model
    return "", ""


def read_task(directory: str) -> dict:
    result = os.path.join(directory, "result.json")
    meta = os.path.join(directory, "smartbugs.json")
    out = {"dir": directory, "contract_file": None, "duration": None,
           "exit_code": None, "findings": [], "infos": [], "errors": [],
           "fails": [], "prompt": 0, "completion": 0, "calls": 0}
    if os.path.exists(meta):
        m = json.load(open(meta, encoding="utf-8"))
        out["contract_file"] = m.get("filename")
        out["duration"] = (m.get("result") or {}).get("duration")
        out["exit_code"] = (m.get("result") or {}).get("exit_code")
        out["start"] = (m.get("result") or {}).get("start")
    if os.path.exists(result):
        r = json.load(open(result, encoding="utf-8"))
        for k in ("findings", "infos", "errors", "fails"):
            out[k] = r.get(k) or []
    log = os.path.join(directory, "result.log")
    if os.path.exists(log):
        text = open(log, encoding="utf-8", errors="replace").read()
        pairs = USAGE.findall(text)
        out["calls"] = len(pairs)
        out["prompt"] = sum(int(a) for a, _ in pairs)
        out["completion"] = sum(int(b) for _, b in pairs)
    return out


def export(runid: str) -> dict:
    taxonomy = load_taxonomy()
    run_dir = os.path.join(SB, "results", "llmsmartaudit", runid)
    if not os.path.isdir(run_dir):
        raise SystemExit("kein Lauf unter %s" % run_dir)
    out_dir = os.path.join(REPO_ROOT, "eval", runid)
    os.makedirs(out_dir, exist_ok=True)

    tasks = [read_task(d) for d in sorted(glob.glob(os.path.join(run_dir, "*/")))]
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    rows, states, categories = [], collections.Counter(), collections.Counter()
    per_contract, unmapped = {}, set()
    provider = model = ""
    for t in tasks:
        p, m = backend(t["infos"])
        provider, model = provider or p, model or m
        contract_file = t["contract_file"] or os.path.basename(t["dir"].rstrip("/\\"))
        contract_id = os.path.basename(contract_file)
        if contract_id.endswith(".sol"):
            contract_id = contract_id[:-4]
        state = task_state(t["findings"], t["errors"], t["fails"])
        states[state] += 1
        per_contract[contract_id] = (len(t["findings"]), state)

        for f in t["findings"]:
            name = f.get("name", "")
            entry = taxonomy.get(name) or {}
            if not entry:
                unmapped.add(name)
            classification = entry.get("classification", "")
            categories[name] += 1
            rows.append({
                "contract_id": contract_id,
                "contract_file": contract_file,
                "tool": "llmsmartaudit",
                "provider": p or provider,
                "model": m or model,
                "category_raw": name,
                "category_defi_logic": is_defi_logic(classification),
                "dasp10": dasp10(classification),
                "classification_raw": classification,
                "function": None,     # tool emits none
                "lines": None,        # tool emits none
                "severity": None,     # tool emits none
                "severity_doc": entry.get("severity"),  # from findings.yaml
                "description": f.get("message"),
                "confidence": None,   # tool emits none
                "run_id": runid,
                "timestamp": stamp,
            })

    with open(os.path.join(out_dir, "findings.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    prompt = sum(t["prompt"] for t in tasks)
    completion = sum(t["completion"] for t in tasks)
    cost = prompt / 1e6 * PRICE_PROMPT_PER_M + completion / 1e6 * PRICE_COMPLETION_PER_M
    duration = sum(t["duration"] or 0 for t in tasks)

    failures = [
        {"contract_id": os.path.basename(t["contract_file"] or t["dir"])[:-4],
         "exit_code": t["exit_code"],
         "errors": t["errors"], "fails": t["fails"]}
        for t in tasks
        if task_state(t["findings"], t["errors"], t["fails"]) not in ("findings", "clean")
    ]

    meta = {
        "run_id": runid,
        "generated": stamp,
        "smartbugs_version": "2.1.1",
        "tool_yaml_version": "smartbugs/tools/llmsmartaudit/config.yaml @ 1.0",
        "parser_version": "2026/08/02 + context-state (2026-08-15)",
        "taxonomy": "smartbugs/tools/llmsmartaudit/findings.yaml (41 detectors)",
        "image": "smartbugs/llmsmartaudit:1.0",
        "provider": provider,
        "model": model,
        "analysis_mode": "SmartContractTA (fixed in scripts/do_solidity.sh)",
        "invocation": {
            "main": False,
            "main_note": ("--main not used: SmartBugs enforces it itself at task "
                          "collection (sb/smartbugs.py:124, exact filename==contract); "
                          "4/143 curated and 0/96 mwevariety files pass that check."),
            "processes": 3,
            "timeout_s": 3600 if "curated" in runid else 7200,
            "env": {"LLM_PROVIDER": "deepseek", "LLM_MODEL": "deepseek-v4-flash",
                    "LLM_CONTEXT_TOKENS": "65536"},
        },
        "contracts": len(tasks),
        "states": dict(states),
        "findings_total": len(rows),
        "categories_seen": len(categories),
        "categories_unmapped": sorted(unmapped),
        "duration_s_sum": round(duration, 1),
        "tokens": {"prompt": prompt, "completion": completion, "llm_calls": sum(t["calls"] for t in tasks)},
        "cost_usd_estimated": round(cost, 2),
        "cost_note": ("Estimated from token counts; the tool reports $0.0000 because "
                      "chatdev/statistics.py::prompt_cost has no entry for "
                      "deepseek-v4-flash. Authoritative figure: DeepSeek invoice."),
        "fields_not_emitted_by_tool": ["function", "lines", "severity", "confidence"],
        "failures": failures,
    }
    with open(os.path.join(out_dir, "run_meta.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    write_summary(os.path.join(out_dir, "summary.md"), runid, meta, categories,
                  per_contract, taxonomy)
    return meta


def write_summary(path, runid, meta, categories, per_contract, taxonomy) -> None:
    total = meta["contracts"]
    states = meta["states"]
    lines = [
        "# %s" % runid,
        "",
        "Erzeugt %s aus `smartbugs/results/llmsmartaudit/%s`." % (meta["generated"], runid),
        "Backend %s/%s, Modus %s, MAIN=0." % (meta["provider"], meta["model"], meta["analysis_mode"]),
        "",
        "## Zustaende",
        "",
        "| Zustand | Contracts | Anteil |",
        "|---|---:|---:|",
    ]
    labels = {
        "findings": "Findings gemeldet",
        "clean": "vollstaendig geprueft, keine Findings",
        "context_exceeded": "Kontext ueberschritten - NICHT analysiert",
        "no_output": "kein Report",
        "failed": "abgebrochen",
    }
    for state, count in sorted(states.items(), key=lambda kv: -kv[1]):
        lines.append("| %s | %d | %.1f %% |" % (labels.get(state, state), count, 100 * count / total))
    lines += [
        "",
        "Die Zeile *Kontext ueberschritten* ist kein Ergebnis. Diese Contracts",
        "wurden nie analysiert; sie duerfen weder als 'clean' noch in einer",
        "Precision-Rechnung auftauchen.",
        "",
        "## Findings je Kategorie",
        "",
        "| Kategorie | Findings | DASP | DeFi-Logik | Severity (aus findings.yaml) |",
        "|---|---:|---|---|---|",
    ]
    for name, count in categories.most_common():
        e = taxonomy.get(name) or {}
        c = e.get("classification", "")
        lines.append("| %s | %d | %s | %s | %s |" % (
            name, count, dasp10(c) or "-", "ja" if is_defi_logic(c) else "nein",
            e.get("severity", "-")))

    ranked = sorted(per_contract.items(), key=lambda kv: (-kv[1][0], kv[0]))
    lines += [
        "",
        "## Findings je Contract",
        "",
        "%d Contracts mit mindestens einem Finding, %d ohne." % (
            sum(1 for _, (n, _) in ranked if n), sum(1 for _, (n, _) in ranked if not n)),
        "",
        "| Contract | Findings | Zustand |",
        "|---|---:|---|",
    ]
    for cid, (n, state) in ranked:
        lines.append("| %s | %d | %s |" % (cid, n, labels.get(state, state)))
    lines += [
        "",
        "## Aufwand",
        "",
        "- LLM-Calls: %d" % meta["tokens"]["llm_calls"],
        "- Prompt-Tokens: %d" % meta["tokens"]["prompt"],
        "- Completion-Tokens: %d" % meta["tokens"]["completion"],
        "- Kosten geschaetzt: $%.2f (%s)" % (meta["cost_usd_estimated"], meta["cost_note"]),
        "- Summe Task-Laufzeit: %.0f s" % meta["duration_s_sum"],
        "",
        "## Nicht vom Werkzeug geliefert",
        "",
        "`function`, `lines`, `severity`, `confidence` sind in findings.jsonl `null`.",
        "Das Werkzeug liest Quelltext als Text und meldet weder Positionen noch",
        "Schweregrade. `severity_doc` traegt den dokumentationsseitigen Default aus",
        "findings.yaml und ist kein Urteil des Modells.",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    for rid in sys.argv[1:]:
        m = export(rid)
        print("%s: %d Contracts, %d Findings, %s, ~$%.2f"
              % (rid, m["contracts"], m["findings_total"], m["states"], m["cost_usd_estimated"]))
