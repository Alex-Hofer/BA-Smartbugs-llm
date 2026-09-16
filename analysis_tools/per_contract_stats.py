"""Eine Zeile je Contract aus einem aufgezeichneten SmartBugs-Lauf.

Dieses Skript rechnet nichts neu aus. Jede Zahl steht schon in den
Rohergebnissen; sie wird hier nur je Contract zusammengetragen, weil die
vorhandenen Auswertungen (``gptscan_eval.py``, ``build_eval.py``) ausschliesslich
Laufsummen exportieren. Geschrieben wird nach ``eval/per_contract/``; die
Rohergebnisse unter ``smartbugs/results/`` bleiben unangetastet.

Quellen je Spalte -- keine Spalte wird geschaetzt:

* ``smartbugs.json``: Startzeit, Container-Dauer, Exit-Code, dazu TIMEOUT und
  MAIN aus dem Docker-Entrypoint. MAIN wird bewusst von dort gelesen und nicht
  aus ``run_meta.json``, weil die dortige Begruendung zu ``--main`` am Code
  widerlegt ist (``sb/smartbugs.py:124`` merkt eine Abweichung nur an).
* ``result.json``: Findings, errors, fails, infos -- also die Parser-Ausgabe.
* GPTScan zusaetzlich die Zeile ``GPTSCAN_META`` im ``result.log``.
* LLMSmartAudit zusaetzlich das ``result.log``. Dort stehen dieselben Woerter
  zweimal: als Vorab-Schaetzung vor jedem Aufruf und als echte Summe in der
  ChatDev-Statistik am Ende. Jede Kennzahl haengt deshalb an einem
  festgelegten Muster, nie am ersten passenden Vorkommen.

Zwei Regeln, die das Ergebnis ehrlich halten:

* **Fehlt eine Angabe, bleibt die Zelle leer** -- niemals 0. Ein Task, der vor
  der Metadatenzeile abgebrochen ist, hat keine Kosten von null, sondern keine
  bekannten Kosten.
* **Die Invariante "Phasenmarker = Usage-Bloecke"** wird je Contract geprueft.
  Eine Abweichung ist ein Befund: Sie zeigt die Phase, in der ein Lauf
  abgeschnitten wurde (Timeout-Netz, abgelehnter Aufruf). Sie wird ausgewiesen,
  nicht geglaettet.

Aufruf:
    python analysis_tools/per_contract_stats.py gptscan gptscan_mwefixed_v2_main \\
        --merge-run gptscan_mwefixed_v2_main_nomain
    python analysis_tools/per_contract_stats.py llmsmartaudit curated_v1_20260705
"""

import argparse
import csv
import importlib.util
import json
import os
import pathlib
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO_ROOT, "smartbugs", "results")
OUT_DIR = os.path.join(REPO_ROOT, "eval", "per_contract")


def _load(name):
    """Ein Nachbarskript nach Pfad laden -- beide sind Skripte, kein Paket."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Die Merge-Semantik und die Preise werden importiert, nicht kopiert: eine Kopie
# liefe irgendwann auseinander. tests/test_per_contract_stats.py haelt die
# Signaturen fest, damit eine Umbenennung laut scheitert.
build_eval = _load("build_eval")
gptscan_run_stats = _load("gptscan_run_stats")

DEGRADED_MARK = "analysis degraded"

PHASE = re.compile(r"\| \*\*phase_name\*\* \| (\w+) \|")
STAT_PROMPT = re.compile(r"\*\*num_prompt_tokens\*\*=(\d+)")
STAT_COMPLETION = re.compile(r"\*\*num_completion_tokens\*\*=(\d+)")
STAT_DURATION = re.compile(r"\*\*duration\*\*=([\d.]+)s")
PROMPT_EST = re.compile(r"num_prompt_tokens \(before adjustment\): (\d+)")
CONTEXT_LIMIT = re.compile(r"num_max_token: (\d+)")
USAGE_ONE = re.compile(r"prompt_tokens: (\d+)\s*\ncompletion_tokens: (\d+)")

SHARED_COLUMNS = [
    "run_id", "tool", "contract_id", "task_dir", "source_run", "start_unix",
    "duration_s", "exit_code", "main", "timeout_s", "state",
    "n_findings", "n_errors", "n_fails",
]

GPTSCAN_COLUMNS = SHARED_COLUMNS + [
    "tool_time_s", "llm_calls", "calls_skipped_budget", "calls_skipped_deadline",
    "prompt_tokens", "completion_tokens", "cost_usd",
    "files", "contracts", "functions", "loc",
    "contracts_after_filter", "contracts_after_step_1", "contracts_after_step_2",
    "contracts_after_static", "vul_before_static", "vul_after_static",
    "vul_after_merge", "degraded", "static_invalid_args",
]

LLMSA_COLUMNS = SHARED_COLUMNS + [
    "tool_time_s", "llm_calls", "phases", "calls_match_phases",
    "prompt_tokens", "completion_tokens", "cost_usd_est",
    "categories_checked", "max_prompt_est", "context_limit", "sb_timeout_stage",
]

PHASE_COLUMNS = [
    "run_id", "contract_id", "task_dir", "phase_index", "phase_name", "calls",
    "prompt_tokens", "completion_tokens", "max_prompt_est",
]


def columns(tool):
    """Die Spalten eines Werkzeugs, in fester Reihenfolge."""
    if tool == "gptscan":
        return GPTSCAN_COLUMNS
    if tool == "llmsmartaudit":
        return LLMSA_COLUMNS
    return SHARED_COLUMNS


def _read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _read_log(directory):
    path = os.path.join(directory, "result.log")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _entrypoint_args(smartbugs):
    """MAIN und TIMEOUT aus dem Entrypoint: ``FILENAME TIMEOUT BIN MAIN``."""
    entry = (smartbugs.get("docker") or {}).get("entrypoint") or ""
    args = re.findall(r"'([^']*)'", entry)
    timeout = int(args[2]) if len(args) > 2 and args[2].isdigit() else None
    main = int(args[4]) if len(args) > 4 and args[4].isdigit() else None
    return main, timeout


def _number(value):
    """Zahl oder None -- SmartBugs schreibt Dauer und Exit-Code als Strings."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _last_int(pattern, text):
    hits = pattern.findall(text)
    return int(hits[-1]) if hits else None


def _shared_row(tool, directory, run_id, source_run, run_root=None):
    smartbugs = _read_json(os.path.join(directory, "smartbugs.json"))
    result = _read_json(os.path.join(directory, "result.json"))
    findings = result.get("findings") or []
    infos = result.get("infos") or []
    errors = result.get("errors") or []
    fails = result.get("fails") or []
    main, timeout = _entrypoint_args(smartbugs)
    contract_file = smartbugs.get("filename") or os.path.basename(
        directory.rstrip("/\\"))
    # Der Ordnername allein genuegt nicht: smartbugs-curated enthaelt
    # 0x627fa62c....sol zweimal, unter reentrancy/ und unter
    # unchecked_low_level_calls/. Beide Tasks tragen dieselbe contract_id.
    task_dir = (os.path.relpath(directory, run_root) if run_root
                else os.path.basename(directory.rstrip("/\\")))
    # Schraegstriche, auch unter Windows: die Tabelle ist versioniert und wird
    # auf anderen Systemen gelesen.
    task_dir = task_dir.replace(os.sep, "/")
    exit_code = _number((smartbugs.get("result") or {}).get("exit_code"))
    return {
        "run_id": run_id,
        "tool": tool,
        "contract_id": build_eval.contract_id(contract_file),
        "task_dir": task_dir,
        "dir": directory,
        "source_run": source_run or run_id,
        "start_unix": _number((smartbugs.get("result") or {}).get("start")),
        "duration_s": _number((smartbugs.get("result") or {}).get("duration")),
        "exit_code": int(exit_code) if exit_code is not None else None,
        "main": main,
        "timeout_s": timeout,
        "n_findings": len(findings),
        "n_errors": len(errors),
        "n_fails": len(fails),
        # Rohmaterial fuer die Merge-Entscheidung; steht in keiner Spalte.
        "findings": findings,
        "infos": infos,
        "errors": errors,
        "fails": fails,
    }


def _gptscan_state(row, degraded):
    """fails vor degraded vor findings: ein unbestimmtes Ergebnis gewinnt."""
    if row["fails"]:
        return "failed"
    if degraded:
        return "degraded"
    if row["findings"]:
        return "findings"
    return "clean"


def _gptscan_row(directory, row):
    meta = gptscan_run_stats.meta_of(
        pathlib.Path(directory) / "result.log") or {}
    degraded = any(DEGRADED_MARK in i for i in row["infos"])
    row.update({
        "tool_time_s": meta.get("used_time"),
        "llm_calls": meta.get("llm_calls"),
        "calls_skipped_budget": meta.get("llm_calls_skipped_budget"),
        "calls_skipped_deadline": meta.get("llm_calls_skipped_deadline"),
        "prompt_tokens": meta.get("token_sent"),
        "completion_tokens": meta.get("token_received"),
        "cost_usd": meta.get("estimated_cost"),
        "files": meta.get("files"),
        "contracts": meta.get("contracts"),
        "functions": meta.get("functions"),
        "loc": meta.get("loc"),
        "contracts_after_filter": meta.get("contracts_after_filter"),
        "contracts_after_step_1": meta.get("contracts_after_step_1"),
        "contracts_after_step_2": meta.get("contracts_after_step_2"),
        "contracts_after_static": meta.get("contracts_after_static"),
        "vul_before_static": meta.get("vul_before_static"),
        "vul_after_static": meta.get("vul_after_static"),
        "vul_after_merge": meta.get("vul_after_merge"),
        "degraded": degraded,
        "static_invalid_args": any("Invalid args" in e for e in row["errors"]),
        "state": _gptscan_state(row, degraded),
    })
    # Token- und Call-Zahlen stehen als Fliesskommazahlen in den Metadaten.
    for key in ("prompt_tokens", "completion_tokens", "llm_calls",
                "calls_skipped_budget", "calls_skipped_deadline"):
        if isinstance(row[key], float):
            row[key] = int(row[key])
    return row


def _llmsa_row(directory, row):
    log = _read_log(directory)
    phases = PHASE.findall(log)
    calls = USAGE_ONE.findall(log)
    prompt = _last_int(STAT_PROMPT, log)
    completion = _last_int(STAT_COMPLETION, log)
    duration = STAT_DURATION.findall(log)
    estimates = [int(x) for x in PROMPT_EST.findall(log)]
    output = _read_json(os.path.join(directory, "output.json"))
    sb_timeout = (output.get("sb_timeout") or {}) if isinstance(output, dict) else {}
    row.update({
        "tool_time_s": float(duration[-1]) if duration else None,
        "llm_calls": len(calls),
        "phases": len(phases),
        "calls_match_phases": len(calls) == len(phases),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "cost_usd_est": None if prompt is None or completion is None else (
            prompt / 1e6 * build_eval.PRICE_PROMPT_PER_M
            + completion / 1e6 * build_eval.PRICE_COMPLETION_PER_M),
        "categories_checked": _categories_checked(row["infos"]),
        "max_prompt_est": max(estimates) if estimates else None,
        "context_limit": _last_int(CONTEXT_LIMIT, log),
        "sb_timeout_stage": sb_timeout.get("stage"),
        "state": build_eval.task_state(row["findings"], row["errors"], row["fails"]),
    })
    return row


def _categories_checked(infos):
    for info in infos:
        hit = re.search(r"categories checked: (\d+)/(\d+)", info)
        if hit:
            return int(hit.group(1))
    return None


def _shared_state(row):
    if row["fails"]:
        return "failed"
    if row["findings"]:
        return "findings"
    return "clean"


def task_row(tool, directory, run_id="", source_run="", run_root=None):
    """Eine Zeile fuer einen Task-Ordner; unbekannte Werte bleiben ``None``."""
    row = _shared_row(tool, directory, run_id, source_run, run_root)
    if tool == "gptscan":
        return _gptscan_row(directory, row)
    if tool == "llmsmartaudit":
        return _llmsa_row(directory, row)
    row["state"] = _shared_state(row)
    return row


def phase_rows(directory, run_id="", task_dir=None):
    """Eine Zeile je Phase: Tokens dem Phasenmarker davor zugeordnet.

    Der Marker einer Phase steht im Log vor ihrem Usage-Block. Eine Phase ohne
    Usage-Block behaelt ``calls`` 0 und leere Token-Zellen -- so bleibt der
    abgeschnittene Aufruf sichtbar.
    """
    log = _read_log(directory)
    smartbugs = _read_json(os.path.join(directory, "smartbugs.json"))
    contract = build_eval.contract_id(
        smartbugs.get("filename") or os.path.basename(directory.rstrip("/\\")))
    task = task_dir or os.path.basename(directory.rstrip("/\\"))
    marks = [(m.start(), m.group(1)) for m in PHASE.finditer(log)]
    rows = []
    for index, (position, name) in enumerate(marks, start=1):
        end = marks[index][0] if index < len(marks) else len(log)
        section = log[position:end]
        calls = USAGE_ONE.findall(section)
        estimates = [int(x) for x in PROMPT_EST.findall(section)]
        rows.append({
            "run_id": run_id,
            "contract_id": contract,
            "task_dir": task,
            "phase_index": index,
            "phase_name": name,
            "calls": len(calls),
            "prompt_tokens": sum(int(a) for a, _ in calls) if calls else None,
            "completion_tokens": sum(int(b) for _, b in calls) if calls else None,
            "max_prompt_est": max(estimates) if estimates else None,
        })
    return rows


def _undecided(tool, row):
    """Darf ein Nachlauf fuer diesen Task sprechen?

    GPTScan: nur wo der Hauptlauf mit ``fails`` endete -- die Regel von
    ``gptscan_eval.py:725-730``. LLMSmartAudit: wo der Task gar nicht
    entschieden wurde, also auch bei Kontextabbruch -- ``build_eval.is_decided``.
    """
    if tool == "llmsmartaudit":
        return not build_eval.is_decided(row)
    return bool(row["fails"])


def merge_rows(tool, main, extra):
    """Einen Nachlauf einmischen und sagen, welche Contracts er uebernahm.

    Der Nachlauf ersetzt nur unentschiedene Tasks und kann keinen Contract
    hinzufuegen, den der Hauptlauf nicht hatte -- die Korpusgroesse ist der
    Nenner jeder Prozentangabe.
    """
    by_id = {row["contract_id"]: row for row in extra}
    rows, replaced = [], []
    for row in main:
        candidate = by_id.get(row["contract_id"])
        if candidate is not None and _undecided(tool, row):
            rows.append(candidate)
            replaced.append(candidate["contract_id"])
        else:
            rows.append(row)
    return rows, replaced


def _cell(value):
    if value is None:
        return None          # csv schreibt dafuer eine leere Zelle
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def write_csv(path, tool, rows, header=None):
    """Die Tabelle schreiben: UTF-8 ohne BOM, Komma, Punkt als Dezimalzeichen."""
    header = header or columns(tool)
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key)) for key in header})
    return path


def read_run(tool, runid, results=RESULTS):
    """Alle Task-Ordner eines Laufs -- erkannt an ihrer ``smartbugs.json``."""
    root = os.path.join(results, tool, runid)
    if not os.path.isdir(root):
        raise SystemExit("kein Lauf unter %s" % root)
    dirs = []
    for base, _, files in os.walk(root):
        if "smartbugs.json" in files:
            dirs.append(base)
    return [task_row(tool, d, run_id=runid, source_run=runid, run_root=root)
            for d in sorted(dirs)]


def _sum(rows, key):
    values = [r.get(key) for r in rows if isinstance(r.get(key), (int, float))]
    return sum(values), len(values)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tool", help="gptscan, llmsmartaudit oder slither-0.11.3")
    ap.add_argument("runid")
    ap.add_argument("--merge-run", action="append", default=[],
                    help="Nachlauf einmischen, z. B. der _nomain- oder _retry-Lauf")
    ap.add_argument("--results", default=RESULTS)
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args(argv)

    rows = read_run(args.tool, args.runid, args.results)
    replaced_all = []
    for extra in args.merge_run:
        rows, replaced = merge_rows(args.tool, rows,
                                    read_run(args.tool, extra, args.results))
        replaced_all += replaced
        print("eingemischt: %s ersetzt %d Task(s): %s"
              % (extra, len(replaced), ", ".join(replaced) or "-"))
    for row in rows:
        row["run_id"] = args.runid

    out = os.path.join(args.out_dir, "%s__%s.csv" % (args.runid, args.tool))
    write_csv(out, args.tool, rows)
    print("geschrieben: %s (%d Zeilen)" % (out, len(rows)))

    if args.tool == "llmsmartaudit":
        phases = []
        for row in rows:
            # Der Task-Ordner steht in der Zeile; ihn ueber den Namen zu suchen
            # wuerde den doppelten Dateinamen in curated zweimal zaehlen.
            phases += phase_rows(row["dir"], run_id=args.runid,
                                 task_dir=row["task_dir"])
        out_phases = os.path.join(args.out_dir,
                                  "%s__%s__phases.csv" % (args.runid, args.tool))
        write_csv(out_phases, args.tool, phases, header=PHASE_COLUMNS)
        print("geschrieben: %s (%d Zeilen)" % (out_phases, len(phases)))

    print("Tasks: %d | Findings: %d auf %d Contracts | mit errors: %d | mit fails: %d"
          % (len(rows), sum(r["n_findings"] for r in rows),
             sum(1 for r in rows if r["n_findings"]),
             sum(1 for r in rows if r["n_errors"]),
             sum(1 for r in rows if r["n_fails"])))
    states = {}
    for row in rows:
        states[row["state"]] = states.get(row["state"], 0) + 1
    print("Zustaende: " + ", ".join("%s %d" % kv for kv in sorted(states.items())))
    for key in ("duration_s", "tool_time_s", "prompt_tokens", "completion_tokens",
                "llm_calls", "cost_usd", "cost_usd_est"):
        total, count = _sum(rows, key)
        if count:
            print("  %-18s Summe %15.4f  (n=%d von %d)"
                  % (key, total, count, len(rows)))

    broken = [r["contract_id"] for r in rows if r.get("calls_match_phases") is False]
    if broken:
        print("HINWEIS: Phasenmarker != Usage-Bloecke bei %d Contract(s): %s"
              % (len(broken), ", ".join(broken)))
        print("  Das ist ein Befund, kein Fehler der Tabelle: dort wurde ein Lauf "
              "mitten in einer Phase abgeschnitten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
