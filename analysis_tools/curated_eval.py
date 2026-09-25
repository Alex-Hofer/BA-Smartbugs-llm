"""Auswertung des curated-Hauptlaufs je Werkzeug nach ``eval/<runid>__<tool>/``.

Warum es dieses Skript gibt. Die beiden vorhandenen Exporte decken den
curated-Lauf nicht ab:

* ``build_eval.py`` liest ausschliesslich ``smartbugs/results/llmsmartaudit/``
  und erwartet die Taskverzeichnisse flach unter dem Lauf (``*/``). Der
  curated-Lauf ist eine Ebene tiefer nach DASP-Kategorie sortiert.
* ``gptscan_eval.py`` liest nur GPTScan-Laeufe, schreibt nach ``eval/<runid>/``
  -- der Laufname ``curated_v1_20260705`` ist aber bei allen drei Werkzeugen
  derselbe -- und schreibt ``eval/README.md`` neu.

Beide bleiben deshalb unangetastet. Was sich teilen laesst, wird importiert und
nicht kopiert: ``build_eval.read_task`` liest einen Taskordner,
``build_eval.task_state`` bestimmt den Zustand eines LLMSmartAudit-Tasks,
``evaluate_curated.load_mapping`` liefert die DASP-Zuordnung je Werkzeug --
einschliesslich der fuenf dort dokumentierten Zusatz-Mappings. Die Rohdaten
unter ``smartbugs/results/`` werden nur gelesen.

Erzeugt je Werkzeug:

    eval/<runid>__<tool>/findings.jsonl   eine Zeile je Finding
    eval/<runid>__<tool>/run_meta.json    Laufparameter, Zustaende, Kennzahlen
    eval/<runid>__<tool>/summary.md       Findings je Kategorie und je Contract
    eval/<runid>__<tool>/README.md        Herkunft, Spalten, Tragweite

und einmal je Lauf:

    eval/<runid>__metriken.md             Recall/Precision/F1 je DASP-Kategorie

Drei Dinge tut es bewusst nicht.

Es dupliziert keine Taxonomie. Klassifikation und Severity stammen bei jedem
Lauf aus ``smartbugs/tools/<tool>/findings.yaml``; der Rohname des Findings
reist in jeder Zeile mit, damit jede Ableitung ohne neuen Lauf wiederholbar
bleibt.

Es erfindet keine Angaben. Was ein Werkzeug nicht meldet -- LLMSmartAudit etwa
weder Zeilennummern noch Severity --, bleibt ``null``. Die Severity aus
findings.yaml reist getrennt als ``severity_doc``, damit sie nie mit einem
Urteil des Modells verwechselt wird.

Es laesst keinen Contract sauber aussehen, der nie analysiert wurde. ``state``
trennt "keine Findings" von "nicht uebersetzt", "Kontext ueberschritten" und
"gescheitert".

Aufruf:
    python analysis_tools/curated_eval.py
    python analysis_tools/curated_eval.py --run curated_v1_20260705 --tools gptscan
"""

import argparse
import collections
import datetime
import importlib.util
import json
import os
import pathlib
import re
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
RESULTS = REPO / "smartbugs" / "results"
EVAL = REPO / "eval"
TOOLS = ("gptscan", "llmsmartaudit", "slither-0.11.3")

DEGRADED_MARK = "analysis degraded"
DASP_RE = re.compile(r"\bDASP-(\d+)\b")
ENTRY_ARG = re.compile(r"'([^']*)'")


def _load(name, path=None):
    """Ein Nachbarskript nach Pfad laden -- beide sind Skripte, kein Paket."""
    path = path or (pathlib.Path(__file__).resolve().parent / (name + ".py"))
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_eval = _load("build_eval")
evaluate_curated = _load("evaluate_curated", REPO / "evaluate_curated.py")


# --------------------------------------------------------------- Rohdaten ---

def taxonomy(tool):
    """findings.yaml des Werkzeugs -- die einzige Quelle der Klassifikation."""
    import yaml
    path = REPO / "smartbugs" / "tools" / tool / "findings.yaml"
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def ground_truth():
    """(Kategorieordner, Dateiname) -> gelabelte Kategorien des Datensatzes.

    Bricht ab, wenn der Datensatz fehlt: Ohne Ground Truth entstuenden
    Auswertungen mit Recall "-" und leeren Labels, die die versionierten
    Dateien unter eval/ stillschweigend ueberschreiben wuerden.
    """
    path = REPO / "smartbugs-curated" / "vulnerabilities.json"
    if not path.exists():
        raise SystemExit(
            f"Ground Truth fehlt: {path}\n"
            "Der Datensatz smartbugs-curated ist nicht versioniert. Holen mit\n"
            "  git clone https://github.com/smartbugs/smartbugs-curated\n"
            "  git -C smartbugs-curated checkout 230e649\n"
            "(README, 'Wo die Ergebnisse liegen'); run_curated.ps1 tut dasselbe."
        )
    out = {}
    for entry in json.loads(path.read_text(encoding="utf-8")):
        p = pathlib.Path(entry["path"])
        out[(p.parts[1], p.name)] = sorted({v["category"] for v in entry["vulnerabilities"]})
    return out


def backend_of(infos):
    """provider/model aus der Info-Zeile, die das Werkzeug selbst schreibt."""
    for i in infos:
        if "run: backend=" in i:
            provider, _, model = i.split("backend=", 1)[1].partition("/")
            return provider.strip(), model.split(",")[0].strip()
    return None, None


def state_of(tool, task):
    """Zustand eines Tasks -- nie 'clean', wenn nichts analysiert wurde."""
    findings, errors, fails = task["findings"], task["errors"], task["fails"]
    if tool == "llmsmartaudit":
        return build_eval.task_state(findings, errors, fails)
    if fails:
        return "failed"
    if any(DEGRADED_MARK in str(i) for i in task["infos"]):
        return "degraded"
    return "findings" if findings else "clean"


def read_run(tool, runid):
    """Alle Tasks eines Laufs, egal wie tief die Taskordner liegen."""
    rundir = RESULTS / tool / runid
    if not rundir.is_dir():
        raise SystemExit("kein Lauf unter %s" % rundir)
    labels = ground_truth()
    tasks = []
    for sbjson in sorted(rundir.rglob("smartbugs.json")):
        d = sbjson.parent
        task = build_eval.read_task(str(d), runid)
        rel = d.relative_to(rundir)
        task["task_dir"] = str(pathlib.PurePosixPath(*rel.parts))
        task["label_dir"] = rel.parts[0] if len(rel.parts) > 1 else ""
        task["labels"] = labels.get((task["label_dir"], d.name), [])
        meta = json.loads(sbjson.read_text(encoding="utf-8"))
        docker = meta.get("docker") or {}
        # Der Entrypoint ist "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN' '$MAIN'";
        # Slither kennt kein $MAIN und hat deshalb nur vier Argumente.
        argv = ENTRY_ARG.findall(docker.get("entrypoint") or "")
        task["image"] = docker.get("image")
        task["network"] = docker.get("network")
        task["solc"] = meta.get("solc")
        task["timeout_s"] = int(argv[2]) if len(argv) > 2 and argv[2].isdigit() else None
        task["main"] = argv[4] if len(argv) > 4 else None
        task["state"] = state_of(tool, task)
        tasks.append(task)
    return tasks


# ---------------------------------------------------------------- Findings ---

def finding_rows(tool, tasks, tax, mapping, stamp):
    """Eine Zeile je Finding, Feldnamen wie in den vorhandenen eval-Ordnern."""
    rows = []
    for t in tasks:
        provider, model = backend_of(t["infos"])
        for f in t["findings"]:
            name = f.get("name")
            entry = tax.get(name) or {}
            cls = entry.get("classification") or ""
            m = DASP_RE.search(cls)
            row = {
                "contract_id": t["contract_id"],
                "contract_file": t["contract_file"],
                "label_dir": t["label_dir"],
                "labels": t["labels"],
                "tool": tool,
                "provider": provider,
                "model": model,
                "category_raw": name,
                "dasp10": "DASP-%s" % m.group(1) if m else "",
                "dasp_category": mapping.get(name) or "",
                "classification_raw": cls,
                "category_defi_logic": build_eval.is_defi_logic(cls),
                "function": f.get("function"),
                "lines": ({"start": f.get("line"), "end": f.get("line_end")}
                          if f.get("line") is not None else None),
                "severity": f.get("severity") or f.get("impact"),
                "severity_doc": entry.get("severity"),
                "confidence": f.get("confidence"),
                "description": f.get("message") or f.get("description"),
                "run_id": t["run_id"],
                "timestamp": stamp,
            }
            rows.append(row)
    return rows


# --------------------------------------------------------------- Kennzahlen ---

def wilson(k, n, z=1.96):
    """Wilson-Intervall (95 %) fuer einen Anteil k von n; None, wenn n = 0.

    Ohne Fremdpaket, damit die Auswertung nur die Standardbibliothek braucht.
    Bei kleinen n ist das Intervall breit: 4 von 4 ergibt (0.51, 1.0).
    """
    if not n:
        return None
    import math
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(centre - half, 3), round(centre + half, 3))


def metrics(tasks, mapping):
    """Recall/Precision/F1 je curated-Kategorie -- Zaehlweise wie evaluate_curated.py.

    Zusaetzlich je Kategorie die Basisrate (Anteil der Contracts mit diesem
    Label an allen Contracts des Laufs: die Precision, die ein Werkzeug
    erreichte, das die Kategorie auf jedem Contract meldet) und das
    Wilson-Intervall des Recalls.
    """
    n_tasks = len(tasks)
    per_cat = collections.defaultdict(lambda: {"contracts": 0, "detected": 0, "flagged": 0})
    for t in tasks:
        for cat in t["labels"]:
            per_cat[cat]["contracts"] += 1
        found = {mapping.get(f.get("name")) for f in t["findings"]}
        found.discard(None)
        for cat in t["labels"]:
            if cat in found:
                per_cat[cat]["detected"] += 1
        for cat in found:
            per_cat[cat]["flagged"] += 1
    out = {}
    # Alphabetisch, nicht in Begegnungsreihenfolge: per_cat wird auch aus dem
    # Set `found` befuellt, dessen Reihenfolge je Python-Prozess wechselt
    # (Hash-Randomisierung). Ohne Sortierung unterscheiden sich zwei Laeufe
    # des Skripts in der Reihenfolge der Kategorien in run_meta.json, obwohl
    # alle Zahlen gleich sind.
    for cat, v in sorted(per_cat.items()):
        rec = v["detected"] / v["contracts"] if v["contracts"] else None
        prec = v["detected"] / v["flagged"] if v["flagged"] else None
        f1 = (2 * prec * rec / (prec + rec)
              if prec is not None and rec is not None and (prec + rec) else None)
        out[cat] = dict(v, recall=rec, precision=prec, f1=f1,
                        prevalence=(v["contracts"] / n_tasks if n_tasks else None),
                        recall_ci95=wilson(v["detected"], v["contracts"]))
    c = sum(v["contracts"] for v in per_cat.values())
    d = sum(v["detected"] for v in per_cat.values())
    fl = sum(v["flagged"] for v in per_cat.values())
    rec = d / c if c else None
    prec = d / fl if fl else None
    out["GESAMT"] = {
        "contracts": c, "detected": d, "flagged": fl, "recall": rec, "precision": prec,
        "f1": (2 * prec * rec / (prec + rec)
               if prec is not None and rec is not None and (prec + rec) else None),
        "prevalence": None,
        "recall_ci95": wilson(d, c),
    }
    return out


def gptscan_meta(tasks):
    """Summen aus GPTSCAN_META -- nur, was tatsaechlich protokolliert ist."""
    out = collections.Counter()
    seen = 0
    for t in tasks:
        log = pathlib.Path(t["dir"]) / "result.log"
        if not log.exists():
            continue
        m = re.search(r"GPTSCAN_META (\{.*?\})", log.read_text(encoding="utf-8",
                                                               errors="replace"), re.S)
        if not m:
            continue
        try:
            meta = json.loads(m.group(1))
        except ValueError:
            continue
        seen += 1
        for k in ("llm_calls", "token_sent", "token_received",
                  "vul_before_static", "vul_after_static"):
            out[k] += meta.get(k) or 0
        out["estimated_cost"] += meta.get("estimated_cost") or 0
        if (meta.get("llm_calls") or 0) > 0:
            out["contracts_with_llm_call"] += 1
        if (meta.get("vul_before_static") or 0) > (meta.get("vul_after_static") or 0):
            out["contracts_static_discarded"] += 1
    out["tasks_with_meta"] = seen
    return out


def ground_truth_commit():
    """Kurz-Hash des lokalen smartbugs-curated-Clones, sonst None.

    run_curated.ps1 pinnt den Clone auf 230e649 (16.06.2024); der Wert hier
    haelt fest, gegen welchen Stand die Auswertung tatsaechlich gerechnet wurde.
    """
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO / "smartbugs-curated"), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def build_meta(tool, runid, tasks, rows, mapping, stamp):
    """Der Inhalt von run_meta.json fuer ein Werkzeug: Herkunft, Zustaende,
    Kennzahlen, Recall/Precision je Kategorie und die Fehlerliste.

    Tokens und Kosten je nach Werkzeug: GPTScan aus GPTSCAN_META, LLMSmartAudit
    aus den Token-Zahlen mit den Preisen aus build_eval, Slither keine.
    """
    durations = [t["duration"] for t in tasks if t["duration"]]
    starts = [(t.get("start"), t["duration"]) for t in tasks
              if t.get("start") and t["duration"]]
    wall = None
    if starts:
        wall = (max(s + d for s, d in starts) - min(s for s, _ in starts)) / 60
    states = collections.Counter(t["state"] for t in tasks)
    first = tasks[0] if tasks else {}
    provider, model = backend_of(first.get("infos", []))
    meta = {
        "run_id": runid,
        "tool": tool,
        "generated": stamp,
        "generated_by": "analysis_tools/curated_eval.py",
        "smartbugs_version": "2.1.1",
        "results_dir": "smartbugs/results/%s/%s" % (tool, runid),
        "taxonomy": "smartbugs/tools/%s/findings.yaml" % tool,
        "ground_truth": "smartbugs-curated/vulnerabilities.json",
        "ground_truth_commit": ground_truth_commit(),
        "image": first.get("image"),
        "network": first.get("network"),
        "provider": provider,
        "model": model,
        "invocation": {
            "timeout_s": first.get("timeout_s"),
            "main": first.get("main"),
            "main_note": ("MAIN wird aus dem Docker-Entrypoint gelesen, nicht "
                          "aus einem Laufprotokoll."),
        },
        "contracts": len(tasks),
        "states": dict(sorted(states.items())),
        "findings_total": len(rows),
        "findings_dasp_mapped": sum(1 for r in rows if r["dasp_category"]),
        "findings_unmapped": sum(1 for r in rows if not r["dasp_category"]),
        "findings_with_lines": sum(1 for r in rows if r["lines"]),
        "findings_with_function": sum(1 for r in rows if r["function"]),
        "contracts_with_findings": sum(1 for t in tasks if t["findings"]),
        "categories_seen": len({r["category_raw"] for r in rows}),
        "unmapped_by_severity": dict(collections.Counter(
            (r["severity"] or r["severity_doc"] or "unbekannt")
            for r in rows if not r["dasp_category"]).most_common()),
        "tasks_with_errors": sum(1 for t in tasks if t["errors"]),
        "tasks_with_fails": sum(1 for t in tasks if t["fails"]),
        "duration_s_sum": round(sum(durations), 1) if durations else None,
        "duration_s_median": round(statistics.median(durations), 1) if durations else None,
        "wallclock_min": round(wall, 1) if wall is not None else None,
        "metrics_contract_level": metrics(tasks, mapping),
        "metrics_note": ("Zaehlweise und DASP-Zuordnung stammen aus "
                         "evaluate_curated.py; Findings ohne DASP-Klassifikation "
                         "gehen nicht in Recall und Precision ein."),
    }
    if tool == "gptscan":
        g = gptscan_meta(tasks)
        meta["tokens"] = {"prompt": int(g["token_sent"]),
                          "completion": int(g["token_received"]),
                          "llm_calls": int(g["llm_calls"])}
        meta["cost_usd"] = round(g["estimated_cost"], 4)
        meta["cost_note"] = ("Summe des Feldes estimated_cost aus GPTSCAN_META; "
                             "GPTScan rechnet selbst mit den Token-Zahlen der API.")
        meta["prefilter"] = {
            "contracts_with_llm_call": int(g["contracts_with_llm_call"]),
            "note": ("Contracts, fuer die der Keyword-Vorfilter mindestens einen "
                     "LLM-Aufruf ausloeste. Die uebrigen werden ohne LLM-Aufruf "
                     "verworfen; fuer sie kann kein Finding entstehen."),
        }
        meta["static_stage"] = {
            "vul_before_static": int(g["vul_before_static"]),
            "vul_after_static": int(g["vul_after_static"]),
            "contracts_with_discarded_candidates": int(g["contracts_static_discarded"]),
        }
    elif tool == "llmsmartaudit":
        prompt = sum(t["prompt"] for t in tasks)
        completion = sum(t["completion"] for t in tasks)
        meta["tokens"] = {"prompt": prompt, "completion": completion,
                          "llm_calls": sum(t["calls"] for t in tasks)}
        meta["cost_usd"] = round(prompt / 1e6 * build_eval.PRICE_PROMPT_PER_M
                                 + completion / 1e6 * build_eval.PRICE_COMPLETION_PER_M, 2)
        meta["cost_note"] = ("Aus den Token-Zahlen geschaetzt. Das Werkzeug selbst "
                             "meldet $0.0000, weil chatdev/statistics.py::prompt_cost "
                             "keinen Eintrag fuer dieses Modell hat. Massgeblich ist "
                             "die DeepSeek-Rechnung.")
        meta["fields_not_emitted_by_tool"] = ["function", "lines", "severity", "confidence"]
    else:
        meta["tokens"] = None
        meta["cost_usd"] = 0.0
        meta["cost_note"] = "Statische Analyse, keine LLM-Aufrufe."
    meta["failures"] = [
        {"contract_id": t["contract_id"], "state": t["state"],
         "exit_code": t["exit_code"], "errors": t["errors"], "fails": t["fails"]}
        for t in tasks if t["fails"] or t["errors"]
        or t["state"] not in ("findings", "clean")
    ]
    return meta


# ----------------------------------------------------------------- Ausgabe ---

def ci(interval):
    """Wilson-Intervall als Prozentbereich, Gedankenstrich wenn undefiniert."""
    if not interval:
        return "–"
    return "%d–%d %%" % (round(100 * interval[0]), round(100 * interval[1]))


def pct(v):
    """Anteil als ganze Prozentzahl, Gedankenstrich wenn undefiniert."""
    return "%.0f %%" % (100 * v) if v is not None else "–"


def num(n):
    """Tausender mit schmalem Leerzeichen, wie im uebrigen Repository."""
    return "{:,}".format(n).replace(",", " ")


def write_summary(path, tool, runid, tasks, rows, meta, tax):
    """summary.md schreiben: Zustaende, Recall/Precision/F1 je Kategorie,
    Findings je Kategorie und die 15 Contracts mit den meisten Findings."""
    L = []
    A = L.append
    A("# %s -- %s" % (runid, tool))
    A("")
    A("Erzeugt %s aus `%s` durch `analysis_tools/curated_eval.py`."
      % (meta["generated"], meta["results_dir"]))
    if meta["model"]:
        A("Backend %s/%s, Timeout %s s, MAIN=%s."
          % (meta["provider"], meta["model"], meta["invocation"]["timeout_s"],
             meta["invocation"]["main"]))
    else:
        A("Statische Analyse, Image `%s`, Timeout %s s."
          % (meta["image"], meta["invocation"]["timeout_s"]))
    A("")
    A("## Zustaende")
    A("")
    A("| Zustand | Contracts | Anteil |")
    A("|---|---:|---:|")
    total = len(tasks) or 1
    erklaerung = {
        "findings": "Findings gemeldet",
        "clean": "keine Findings, Contract wurde analysiert",
        "degraded": "nicht uebersetzt -- Ergebnis unbestimmt, NICHT sauber",
        "context_exceeded": "Kontext ueberschritten -- NICHT analysiert",
        "no_output": "kein Bericht erzeugt",
        "failed": "gescheitert",
    }
    for state, n in sorted(meta["states"].items(), key=lambda kv: -kv[1]):
        A("| %s | %d | %.1f %% |" % (erklaerung.get(state, state), n, 100 * n / total))
    A("")
    A("Nur der Zustand *keine Findings* ist ein Ergebnis. Ein Contract, der nicht")
    A("uebersetzt wurde oder den Kontext sprengte, darf weder als sauber gelten")
    A("noch in eine Precision-Rechnung eingehen.")
    A("")
    A("## Recall / Precision / F1 je DASP-Kategorie")
    A("")
    A("| Kategorie | Contracts | Erkannt | Recall | Geflaggt | Precision | F1 |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    m = meta["metrics_contract_level"]
    for cat in sorted(k for k in m if k != "GESAMT"):
        v = m[cat]
        A("| %s | %d | %d | %s | %d | %s | %s |"
          % (cat, v["contracts"], v["detected"], pct(v["recall"]), v["flagged"],
             pct(v["precision"]), pct(v["f1"])))
    v = m["GESAMT"]
    A("| **GESAMT** | **%d** | **%d** | **%s** | **%d** | **%s** | **%s** |"
      % (v["contracts"], v["detected"], pct(v["recall"]), v["flagged"],
         pct(v["precision"]), pct(v["f1"])))
    A("")
    A("%s der %s Findings tragen keine DASP-Klassifikation und gehen weder in"
      % (num(meta["findings_unmapped"]), num(meta["findings_total"])))
    A("Recall noch in Precision ein.")
    A("")
    A("## Findings je Kategorie")
    A("")
    A("| Kategorie | Findings | DASP | Severity (aus findings.yaml) |")
    A("|---|---:|---|---|")
    per_cat = collections.Counter(r["category_raw"] for r in rows)
    for name, n in per_cat.most_common():
        entry = tax.get(name) or {}
        m = DASP_RE.search(entry.get("classification") or "")
        A("| %s | %d | %s | %s |"
          % (name, n, m.group(0) if m else "-", entry.get("severity") or "-"))
    A("")
    A("## Findings je Contract")
    A("")
    counts = sorted((len(t["findings"]) for t in tasks), reverse=True)
    A("Mittel %.1f, Median %d, Maximum %d, Contracts ohne Findings %d."
      % (sum(counts) / len(counts) if counts else 0,
         statistics.median(counts) if counts else 0,
         counts[0] if counts else 0, counts.count(0)))
    A("")
    top = sorted(tasks, key=lambda t: -len(t["findings"]))[:15]
    A("| Contract | Kategorie (Label) | Findings | Zustand |")
    A("|---|---|---:|---|")
    for t in top:
        A("| %s | %s | %d | %s |"
          % (t["contract_id"], t["label_dir"] or "-", len(t["findings"]), t["state"]))
    A("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def write_readme(path, tool, runid, meta):
    """README.md des Ordners schreiben: Herkunft, Entstehung, Bedeutung der
    Spalten und was sich aus den Zahlen schliessen laesst und was nicht, mit
    eigenen Absaetzen je Werkzeug."""
    L = []
    A = L.append
    A("# %s__%s" % (runid, tool))
    A("")
    A("## Woher die Daten stammen")
    A("")
    A("| | |")
    A("|---|---|")
    A("| Lauf | `%s` |" % runid)
    A("| Werkzeug | `%s` |" % tool)
    A("| Image | `%s` |" % meta["image"])
    A("| Modell | %s |" % (("`%s/%s`" % (meta["provider"], meta["model"]))
                           if meta["model"] else "keines -- statische Analyse"))
    A("| Datensatz | `smartbugs-curated`, 143 gelabelte Contracts, DASP-Top-10 |")
    A("| Contracts im Lauf | %d |" % meta["contracts"])
    A("| Timeout je Task | %s s |" % meta["invocation"]["timeout_s"])
    A("| Rohergebnisse | `%s` (result.json und smartbugs.json je Task versioniert; Logs und Archive im Release-Zip, siehe README) |" % meta["results_dir"])
    A("| Erzeugt am | %s |" % meta["generated"])
    A("")
    A("Der Lauf fand am 05./06.07.2026 statt (Datum im Laufnamen). Von den")
    A("Rohergebnissen sind je Task `result.json` und `smartbugs.json` versioniert;")
    A("Logs und Archive liegen im Release-Zip (README, \"Wo die Ergebnisse")
    A("liegen\"). Dieser Ordner ist die daraus abgeleitete Auswertung.")
    A("")
    A("## Wie die Dateien entstanden sind")
    A("")
    A("```")
    A("python analysis_tools/curated_eval.py --run %s --tools %s" % (runid, tool))
    A("```")
    A("")
    A("Das Skript liest ausschliesslich; es setzt keinen einzigen API-Aufruf ab")
    A("und veraendert nichts unter `smartbugs/results/`.")
    A("")
    A("## Was in den Dateien steht")
    A("")
    A("**`findings.jsonl`** -- eine Zeile je Finding, JSON pro Zeile.")
    A("")
    A("| Feld | Bedeutung |")
    A("|---|---|")
    A("| `contract_id` | Dateiname ohne `.sol`. **Kein Schluessel**: der Datensatz fuehrt `0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` sowohl unter `reentrancy` als auch unter `unchecked_low_level_calls`; eindeutig ist erst das Paar `(label_dir, contract_id)`. |")
    A("| `contract_file` | Pfad, wie SmartBugs ihn protokolliert hat |")
    A("| `label_dir`, `labels` | Kategorie des Datensatzes bzw. die Labels der Ground Truth |")
    A("| `category_raw` | Name des Findings, wie das Werkzeug ihn meldet |")
    A("| `classification_raw`, `dasp10` | Klassifikation aus `%s` |" % meta["taxonomy"])
    A("| `dasp_category` | daraus abgeleiteter curated-Kategoriename, leer wenn keine Zuordnung |")
    A("| `category_defi_logic` | ob die Klassifikation DeFi-Logik im Sinne GPTScans ist |")
    A("| `function`, `lines` | Fundstelle, sofern das Werkzeug sie meldet -- sonst `null` |")
    A("| `severity`, `confidence` | Urteil des Werkzeugs, sofern vorhanden |")
    A("| `severity_doc` | Severity aus findings.yaml -- Dokumentations-Default, **kein** Urteil des Werkzeugs |")
    A("| `description` | Begruendungstext des Werkzeugs |")
    A("| `run_id`, `timestamp` | Lauf und Zeitpunkt des Exports |")
    A("")
    A("**`run_meta.json`** -- Laufparameter, Zustandsverteilung, Token, Kosten,")
    A("Recall/Precision/F1 je Kategorie und die Liste aller Tasks, die nicht")
    A("sauber durchliefen.")
    A("")
    A("**`summary.md`** -- dieselben Zahlen als Tabellen zum Lesen.")
    A("")
    A("## Was man daraus schliessen darf")
    A("")
    A("* Wie viele Findings dieses Werkzeug auf diesem Korpus meldet und wie sie")
    A("  sich auf die Kategorien verteilen.")
    A("* Contract-Level-Recall gegen die Ground Truth: ob das Werkzeug zu einem")
    A("  gelabelten Contract mindestens ein passendes Finding meldet.")
    A("* Wie oft das Werkzeug ueberhaupt zu einem Ergebnis kam (Spalte *Zustand*).")
    A("")
    A("## Was man daraus nicht schliessen darf")
    A("")
    A("1. **Kein Precision-Mass im ueblichen Sinn.** Der Datensatz labelt genau")
    A("   *eine* Primaer-Schwachstelle je Contract. Ein zutreffender")
    A("   Sekundaer-Befund zaehlt hier als False Positive; die Precision-Werte")
    A("   sind Untergrenzen.")
    A("2. **Nur DASP-klassifizierte Findings zaehlen.** %s der %s Findings dieses"
      % (num(meta["findings_unmapped"]), num(meta["findings_total"])))
    A("   Laufs tragen keine DASP-Zuordnung und gehen weder in Recall noch in")
    A("   Precision ein. Keine Zuordnung heisst nicht belanglos.")
    A("3. **Contract-Level, nicht zeilengenau.** Ein Werkzeug, das viel meldet,")
    with_lines, total = meta["findings_with_lines"], meta["findings_total"]
    if tool == "gptscan":
        share = ("alle %s Findings" % num(total) if with_lines == total
                 else "%s der %s Findings" % (num(with_lines), num(total)))
        A("   trifft haeufiger zufaellig. GPTScan selbst emittiert Zeilen (%s" % share)
        A("   dieses Laufs tragen `lines`); zeilengenau ausgewertet wird trotzdem")
        A("   nicht, weil LLMSmartAudit grundsaetzlich keine Zeilennummern emittiert")
        A("   und nur ein gemeinsames Mass die drei Werkzeuge vergleichbar haelt.")
    elif tool.startswith("slither"):
        A("   trifft haeufiger zufaellig. Slither selbst ist hier das genaueste")
        A("   Werkzeug (%s der %s Findings tragen `lines`, %s zusaetzlich eine"
          % (num(with_lines), num(total), num(meta["findings_with_function"])))
        A("   Funktion); zeilengenau ausgewertet wird trotzdem nicht, weil")
        A("   LLMSmartAudit grundsaetzlich keine Zeilennummern emittiert und nur ein")
        A("   gemeinsames Mass die drei Werkzeuge vergleichbar haelt.")
    else:
        A("   trifft haeufiger zufaellig. Zeilengenau laesst sich nicht auswerten,")
        A("   weil LLMSmartAudit grundsaetzlich keine Zeilennummern emittiert.")
    A("4. **`severity_doc` ist kein Urteil.** Der Wert kommt aus findings.yaml und")
    A("   ist je Detektorname konstant.")
    if tool.startswith("slither"):
        A("5. **Ein Lauf genuegt hier -- anders als bei den KI-Werkzeugen.** Slither ist")
        A("   deterministisch: gleicher Contract, gleiche Version, gleiches Ergebnis.")
        A("   Die Streuung, die den beiden KI-Werkzeugen anhaengt (GPTScan 74 %,")
        A("   LLMSmartAudit 61,4 % Lauf-zu-Lauf-Uebereinstimmung), betrifft diese")
        A("   Baseline nicht -- siehe `docs/BA-WERKZEUGE-IM-VERGLEICH.md`, Abschnitt 4.4.")
    else:
        A("5. **Ein Lauf ist keine Verteilung.** LLM-gestuetzte Werkzeuge sind nicht")
        A("   deterministisch; fuer GPTScan sind 74 % Lauf-zu-Lauf-Uebereinstimmung")
        A("   gemessen (`docs/BA-GPTSCAN-VERGLEICH.md`, Abschnitt 4).")
    A("6. **Kein Werkzeugvergleich ueber Korpora hinweg.** GPTScans Zieldomaene")
    A("   ist DeFi-Logik, nicht DASP. Auf diesem Korpus misst man, was es *nicht*")
    A("   sucht -- siehe `docs/BA-WERKZEUGE-IM-VERGLEICH.md`.")
    if tool == "gptscan":
        A("7. **Die Kostenangabe ist GPTScans eigene Schaetzung** aus `GPTSCAN_META`,")
        A("   nicht die Abrechnung des Anbieters.")
    if tool == "llmsmartaudit":
        A("7. **Die Kostenangabe ist gerechnet, nicht gemessen.** Sie folgt den")
        A("   Preisen in `build_eval.py`; massgeblich ist die DeepSeek-Rechnung.")
    if tool.startswith("slither"):
        A("7. **Die Baseline ist kein Ziel.** Slither dient als Referenzpunkt;")
        A("   seine %.1f %% unklassifizierten Findings sind ueberwiegend"
          % (100 * meta["findings_unmapped"] / (meta["findings_total"] or 1)))
        A("   Informational- und Optimization-Hinweise.")
    A("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def write_metrics(path, runid, per_tool):
    """eval/<runid>__metriken.md schreiben: Gesamtbild und je Werkzeug die
    Kategorietabelle mit Wilson-Intervall und Basisrate. *per_tool* ordnet
    jedem Werkzeug sein run_meta zu."""
    L = []
    A = L.append
    A("# Recall, Precision und F1 je DASP-Kategorie -- `%s`" % runid)
    A("")
    A("Erzeugt durch `analysis_tools/curated_eval.py` aus den Rohergebnissen unter")
    A("`smartbugs/results/<werkzeug>/%s/`. Die Zaehlweise und die" % runid)
    A("DASP-Zuordnung stammen aus `evaluate_curated.py`; dieselben Zahlen gibt")
    A("dessen Konsolenausgabe aus (System-Python oder SmartBugs-venv, beide mit")
    A("PyYAML):")
    A("")
    A("```powershell")
    A("python evaluate_curated.py --suffix %s `"
      % runid.replace("curated_", ""))
    A("    --tools gptscan llmsmartaudit slither-0.11.3 --csv")
    A("```")
    A("")
    gt = next((m.get("ground_truth_commit") for m in per_tool.values()
               if m.get("ground_truth_commit")), None)
    A("Ground Truth: `smartbugs-curated/vulnerabilities.json` auf Commit `%s`"
      % (gt or "unbekannt (kein lokaler Clone)"))
    A("(`run_curated.ps1` pinnt den Clone auf `230e649`, 16.06.2024).")
    A("")
    A("Alle Werte sind **Contract-Level**: ein gelabelter Contract gilt als")
    A("erkannt, wenn das Werkzeug mindestens ein Finding meldet, dessen")
    A("DASP-Klassifikation auf die gelabelte Kategorie abbildet.")
    A("")
    A("## Gesamtbild")
    A("")
    A("| Werkzeug | Recall | Precision | F1 | Findings | davon DASP-zugeordnet | Kosten |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for tool, meta in per_tool.items():
        v = meta["metrics_contract_level"]["GESAMT"]
        A("| %s | %s | %s | %s | %s | %s | $%.2f |"
          % (tool, pct(v["recall"]), pct(v["precision"]), pct(v["f1"]),
             num(meta["findings_total"]), num(meta["findings_dasp_mapped"]),
             meta["cost_usd"]))
    A("")
    for tool, meta in per_tool.items():
        A("## %s" % tool)
        A("")
        A("| Kategorie | Contracts | Erkannt | Recall | Recall 95-%-Intervall | Geflaggt | Precision | Basisrate | F1 |")
        A("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        m = meta["metrics_contract_level"]
        for cat in sorted(k for k in m if k != "GESAMT"):
            v = m[cat]
            A("| %s | %d | %d | %s | %s | %d | %s | %s | %s |"
              % (cat, v["contracts"], v["detected"], pct(v["recall"]), ci(v.get("recall_ci95")),
                 v["flagged"], pct(v["precision"]), pct(v.get("prevalence")), pct(v["f1"])))
        v = m["GESAMT"]
        A("| **GESAMT** | **%d** | **%d** | **%s** | **%s** | **%d** | **%s** | – | **%s** |"
          % (v["contracts"], v["detected"], pct(v["recall"]), ci(v.get("recall_ci95")),
             v["flagged"], pct(v["precision"]), pct(v["f1"])))
        A("")
        A("*Basisrate*: Anteil der Contracts mit diesem Label an allen %d Contracts"
          % meta["contracts"])
        A("des Laufs -- die Precision, die ein Werkzeug erreichte, das die Kategorie")
        A("auf jedem Contract meldet. Eine Precision knapp ueber der Basisrate")
        A("unterscheidet sich kaum vom Raten. *Recall 95-%-Intervall*: Wilson-Intervall;")
        A("bei Kategorien mit acht oder weniger Contracts ist es mindestens 30")
        A("Prozentpunkte breit, der Punktwert allein traegt dort wenig.")
        A("")
        A("%s der %s Findings tragen keine DASP-Klassifikation und gehen weder in"
          % (num(meta["findings_unmapped"]), num(meta["findings_total"])))
        A("Recall noch in Precision ein (%.1f %%)."
          % (100 * meta["findings_unmapped"] / (meta["findings_total"] or 1)))
        A("")
    A("## Die wichtigste Einschraenkung")
    A("")
    slither = next((m for t, m in per_tool.items() if t.startswith("slither")), None)
    if slither:
        sev = slither["unmapped_by_severity"]
        info_opt = sev.get("Informational", 0) + sev.get("Optimization", 0)
        A("%s der %s Slither-Findings (%.1f %%) haben weder in SmartBugs'"
          % (num(slither["findings_unmapped"]), num(slither["findings_total"]),
             100 * slither["findings_unmapped"] / (slither["findings_total"] or 1)))
        A("`findings.yaml` noch ueber die kanonischen Zusatz-Mappings in")
        A("`evaluate_curated.py` (`timestamp` -> DASP-8, `weak-prng` -> DASP-6,")
        A("`unchecked-lowlevel`/`unchecked-send`/`unchecked-transfer` -> DASP-4)")
        A("eine DASP-Zuordnung und")
        A("gehen deshalb nicht in Recall und Precision ein. Keine Zuordnung heisst")
        A("nicht belanglos: nach der Impact-Stufe des jeweiligen Detektors sind")
        A("%s davon Informational oder Optimization, %s Low, %s Medium und %s High."
          % (num(info_opt), num(sev.get("Low", 0)), num(sev.get("Medium", 0)),
             num(sev.get("High", 0))))
        A("Die Herleitung steht in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`,")
        A("Abschnitt 4.1 und 5.")
        A("")
    A("Weitere Einschraenkungen stehen je Werkzeug in der `README.md` des")
    A("zugehoerigen Ordners `eval/%s__<werkzeug>/`." % runid)
    A("")
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


# -------------------------------------------------------------------- Main ---

def export(tool, runid, stamp):
    """Einen Lauf fuer ein Werkzeug auswerten und nach eval/<runid>__<tool>/
    schreiben. Gibt (run_meta, Ausgabeordner) zurueck."""
    tax = taxonomy(tool)
    mapping = evaluate_curated.load_mapping(
        REPO / "smartbugs" / "tools" / tool / "findings.yaml", tool)
    tasks = read_run(tool, runid)
    rows = finding_rows(tool, tasks, tax, mapping, stamp)
    meta = build_meta(tool, runid, tasks, rows, mapping, stamp)

    outdir = EVAL / ("%s__%s" % (runid, tool))
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "findings.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (outdir / "run_meta.json").write_text(
        json.dumps(meta, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    write_summary(outdir / "summary.md", tool, runid, tasks, rows, meta, tax)
    write_readme(outdir / "README.md", tool, runid, meta)
    return meta, outdir


def main(argv=None):
    """Kommandozeile: jedes Werkzeug aus --tools exportieren, bei mehr als
    einem zusaetzlich die Metrikdatei schreiben. Rueckgabe 0."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", default="curated_v1_20260705")
    ap.add_argument("--tools", nargs="+", default=list(TOOLS))
    args = ap.parse_args(argv)

    stamp = datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat()
    per_tool = {}
    for tool in args.tools:
        meta, outdir = export(tool, args.run, stamp)
        per_tool[tool] = meta
        v = meta["metrics_contract_level"]["GESAMT"]
        print("%-16s %3d Contracts, %5d Findings (%d DASP-zugeordnet), "
              "Recall %s, Precision %s -> %s"
              % (tool, meta["contracts"], meta["findings_total"],
                 meta["findings_dasp_mapped"], pct(v["recall"]), pct(v["precision"]),
                 os.path.relpath(outdir, REPO)))
    if len(per_tool) > 1:
        path = EVAL / ("%s__metriken.md" % args.run)
        write_metrics(path, args.run, per_tool)
        print("geschrieben: %s" % os.path.relpath(path, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
