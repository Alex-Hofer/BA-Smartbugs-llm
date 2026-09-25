"""Erzeugt die Auswertung eines GPTScan-Laufs unter eval/<runid>/.

Die SmartBugs-Rohergebnisse unter smartbugs/results/ werden ausschliesslich
GELESEN und bleiben unveraendert. Erzeugt werden:

    eval/<runid>/findings.jsonl   eine Zeile je Finding
    eval/<runid>/run_meta.json    Laufparameter, Versionen, Kosten, Fehlerliste
    eval/<runid>/summary.md       Findings je Kategorie/Contract, Fehlerquote
    eval/<runid>/comparison_<baseline>.md   Vergleich gegen einen Altlauf
    eval/README.md                Zuordnung Ordner -> Lauf (wird fortgeschrieben)

Das SWC/DASP-Mapping wird NICHT hier gepflegt, sondern aus
smartbugs/tools/gptscan/findings.yaml gelesen. Diese Datei ist die einzige
Wahrheit; 8 der 10 MWE-Regeln sind dort bewusst als
"BUSINESS-LOGIC (no SWC/DASP)" markiert.

Zustandsbegriffe nach docs/BA-ERRORS-VS-FAILS.md:
    findings  Verdachtsfall ueber den Contract
    errors    Werkzeug hat ein Problem bemerkt, abgefangen und weitergearbeitet
    fails     Werkzeug wurde ausgehebelt, ein Ergebnis kam nicht zustande
    degraded  Contract nicht uebersetzt -> ein Lauf ohne Findings ist hier
              UNBESTIMMT, nicht sauber, und wird nie als "keine Findings" gezaehlt.

Aufruf:
    python analysis_tools/gptscan_eval.py <RUNID> [--baseline RUNID]
                                          [--merge-run RUNID] [--no-compare]
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import re
import statistics
import subprocess
import sys
import tarfile
import io

REPO = pathlib.Path(__file__).resolve().parent.parent
RESULTS = REPO / "smartbugs" / "results" / "gptscan"
CORPUS = REPO / "smartbugs" / "samples" / "gptscan" / "mwevariety_fixed"
EVAL = REPO / "eval"
TOOLDIR = REPO / "smartbugs" / "tools" / "gptscan"
MAIN_SCRIPT = TOOLDIR / "scripts" / "main_contract.py"

DEGRADED_MARK = "analysis degraded"

# Prefix the tool parsers put on a timeout entry in `errors` (AP5).
TIMEOUT_MARK = "TIMEOUT_"


# --------------------------------------------------------------------------- #
# Taxonomie aus findings.yaml -- nicht hier duplizieren, nur lesen
# --------------------------------------------------------------------------- #

def load_taxonomy() -> dict:
    """findings.yaml -> {finding_name: {...}}.

    PyYAML liegt im SmartBugs-venv; faellt es aus, wird der Lauf abgebrochen
    statt das Mapping zu raten.
    """
    import yaml  # noqa: PLC0415  -- bewusst lazy, nur hier gebraucht
    with (TOOLDIR / "findings.yaml").open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    tax = {}
    for name, e in (raw or {}).items():
        cls = str(e.get("classification", ""))
        dasp = re.findall(r"DASP-\d+", cls)
        swc = re.findall(r"SWC-\d+", cls)
        tax[name] = {
            "classification": cls,
            # Business-Logic heisst: es gibt kein redliches Gegenstueck in
            # SWC/DASP. Dann bleibt dasp10 leer -- nicht mit "related" fuellen,
            # das ist bewusst nur ein dokumentierter Hinweis.
            "defi_logic": cls.startswith("BUSINESS-LOGIC"),
            "dasp10": dasp[0] if dasp else "",
            "swc": swc[0] if swc else "",
            "severity_yaml": e.get("severity"),
            "gptscan_code": e.get("gptscan_code"),
            "mwe": e.get("mwe"),
            "method": e.get("method"),
            "related": e.get("related", ""),
        }
    return tax


# --------------------------------------------------------------------------- #
# Analysierte Quelle rekonstruieren (fuer Funktionszuordnung)
# --------------------------------------------------------------------------- #

_FUNC = re.compile(
    r"\b(?:function\s+(?P<fn>[A-Za-z_]\w*)"
    r"|(?P<ctor>constructor)\s*\("
    r"|(?P<recv>receive|fallback)\s*\("
    r"|modifier\s+(?P<mod>[A-Za-z_]\w*))"
)


def _strip_noise(src: str) -> str:
    """Kommentare und String-Literale durch Leerzeichen ersetzen.

    Nur fuer die Klammerzaehlung. Zeilenumbrueche bleiben erhalten, damit die
    Zeilennummern stimmen.
    """
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in src[i:j])); i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append("".join(ch if ch == "\n" else " " for ch in src[i:j])); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def function_spans(src: str) -> list[tuple[int, int, str]]:
    """[(startzeile, endzeile, name)] je Funktion/Modifier mit Rumpf.

    Heuristik, kein Solidity-Parser: gefunden wird der Deklarationskopf, das
    Ende ueber Klammerzaehlung. Deklarationen ohne Rumpf (Interfaces, abstrakt)
    enden auf ';' und werden uebersprungen. Reicht fuer die Zuordnung
    Zeilennummer -> Funktionsname; wo sie nicht greift, bleibt das Feld leer.
    """
    clean = _strip_noise(src)
    nl = [0]
    for i, ch in enumerate(clean):
        if ch == "\n":
            nl.append(i + 1)

    def line_of(pos: int) -> int:
        """Zeilennummer (ab 1) zur Zeichenposition *pos*, per Binaersuche
        ueber die Zeilenanfaenge in ``nl``."""
        lo, hi = 0, len(nl) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if nl[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    spans = []
    for m in _FUNC.finditer(clean):
        name = m.group("fn") or m.group("ctor") or m.group("recv") or m.group("mod")
        brace = clean.find("{", m.end())
        semi = clean.find(";", m.end())
        if brace < 0 or (0 <= semi < brace):
            continue  # Deklaration ohne Rumpf
        depth, i, n = 0, brace, len(clean)
        while i < n:
            if clean[i] == "{":
                depth += 1
            elif clean[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        spans.append((line_of(m.start()), line_of(min(i, n - 1)), name))
    return spans


def analysed_source(contract_file: pathlib.Path, meta: dict, main: bool,
                    python: str) -> tuple[str | None, str]:
    """Der Quelltext, den GPTScan tatsaechlich gesehen hat, plus Herkunft.

    Unter --main reduziert main_contract.py die Datei IM CONTAINER und stellt
    das Original wieder her, falls die Reduktion nicht mehr uebersetzt
    (--verify-compile). Welcher der beiden Faelle eintrat, verraet die
    Zeilenzahl in GPTSCAN_META['loc']: hier wird die Reduktion auf dem Host
    nachgebaut und ihre Laenge mit loc verglichen. Stimmt keine der beiden
    Varianten, wird nichts geraten -- dann gibt es keine Funktionszuordnung.
    """
    loc = meta.get("loc")
    try:
        full = contract_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, "unlesbar"
    if not isinstance(loc, int):
        return (full, "voll") if not main else (None, "unbekannt")

    if full.count("\n") == loc:
        return full, "voll"
    if not main:
        return None, "unbekannt"

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / contract_file.name
        proc = subprocess.run([python, str(MAIN_SCRIPT), str(contract_file), str(out)],
                              capture_output=True, text=True)
        if proc.returncode == 0 and out.exists():
            red = out.read_text(encoding="utf-8", errors="replace")
            if red.count("\n") == loc:
                return red, "main-reduziert"
    return None, "unbekannt"


# --------------------------------------------------------------------------- #
# Lauf einlesen
# --------------------------------------------------------------------------- #

def meta_of(log: pathlib.Path) -> dict:
    """Die letzte GPTSCAN_META-Zeile eines result.log als dict; {} ohne Zeile
    oder ohne Datei."""
    m = {}
    try:
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("GPTSCAN_META "):
                try:
                    m = json.loads(line[len("GPTSCAN_META "):].strip())
                except ValueError:
                    m = {}
    except OSError:
        pass
    return m


def raw_results(tar: pathlib.Path) -> list[dict]:
    """GPTScans eigene results aus result.tar -- fuer code/recommendation."""
    if not tar.exists():
        return []
    try:
        with tarfile.open(tar) as t:
            for mem in t.getmembers():
                if mem.isfile() and mem.name.rsplit("/", 1)[-1] == "output.json":
                    fh = t.extractfile(mem)
                    if fh is None:
                        continue
                    return json.loads(fh.read().decode("utf-8", "replace")).get("results") or []
    except (tarfile.TarError, ValueError, OSError):
        return []
    return []


def read_run(rundir: pathlib.Path, tax: dict, python: str, run_id: str) -> list[dict]:
    """Alle Tasks eines Laufs als Datensaetze."""
    tasks = []
    for sbjson in sorted(rundir.rglob("smartbugs.json")):
        td = sbjson.parent
        try:
            sb = json.loads(sbjson.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            sb = {}
        res = {}
        rj = td / "result.json"
        if rj.exists():
            try:
                res = json.loads(rj.read_text(encoding="utf-8", errors="replace"))
            except ValueError:
                res = {}
        meta = meta_of(td / "result.log")
        sbres = sb.get("result", {}) or {}
        entry = (sb.get("docker", {}) or {}).get("entrypoint", "") or ""
        main = entry.rstrip().endswith("'1'")
        infos = res.get("infos", []) or []

        cfile = CORPUS / td.name
        src, origin = analysed_source(cfile, meta, main, python)
        spans = function_spans(src) if src else []

        raw = raw_results(td / "result.tar")
        tasks.append({
            "run_id": run_id,
            "contract_id": td.name[:-4] if td.name.endswith(".sol") else td.name,
            "contract_file": str(cfile.relative_to(REPO)).replace("\\", "/"),
            "task_dir": str(td.relative_to(REPO)).replace("\\", "/"),
            "main": main,
            "source_origin": origin,
            "spans": spans,
            "exit_code": sbres.get("exit_code"),
            "duration": sbres.get("duration"),
            "start": sbres.get("start"),
            "findings": res.get("findings", []) or [],
            "raw": raw,
            "errors": res.get("errors", []) or [],
            "fails": res.get("fails", []) or [],
            "infos": infos,
            "degraded": any(DEGRADED_MARK in i for i in infos),
            # Timeout marker (AP5). Read out of errors for the same reason
            # "degraded" is read out of infos: the parser has already
            # normalised it, and result.json carries no raw report.
            "timeout_hit": any(str(e).startswith(TIMEOUT_MARK)
                               for e in (res.get("errors") or [])),
            "timeout_stage": next(
                (str(e).split(":", 1)[0][len(TIMEOUT_MARK):].lower()
                 for e in (res.get("errors") or [])
                 if str(e).startswith(TIMEOUT_MARK)), ""),
            "meta": meta,
        })
    return tasks


def finding_rows(tasks: list[dict], tax: dict) -> list[dict]:
    """Eine Zeile je Finding aller Tasks, mit den Feldern von findings.jsonl.

    Klassifikation aus *tax*, code/recommendation aus GPTScans Rohbefund an
    derselben Position, die Funktion heuristisch aus den Funktionsspannen des
    Tasks (leer, wo keine Spanne die Zeile umschliesst).
    """
    rows = []
    for t in tasks:
        meta = t["meta"]
        ts = (datetime.datetime.fromtimestamp(t["start"], datetime.timezone.utc).isoformat()
              if isinstance(t["start"], (int, float)) else None)
        # GPTScans Rohbefunde in derselben Reihenfolge wie die geparsten
        for idx, f in enumerate(t["findings"]):
            name = f.get("name", "")
            tx = tax.get(name, {})
            raw = t["raw"][idx] if idx < len(t["raw"]) else {}
            start, end = f.get("line"), f.get("line_end")
            fn = ""
            if isinstance(start, int) and t["spans"]:
                cand = [(e - s, n) for s, e, n in t["spans"] if s <= start <= e]
                if cand:
                    fn = min(cand)[1]  # innerste umschliessende Funktion
            rows.append({
                "contract_id": t["contract_id"],
                "contract_file": t["contract_file"],
                "tool": "gptscan",
                "provider": meta.get("provider"),
                "model": meta.get("model"),
                "category_raw": name,
                "mwe": tx.get("mwe") or (name.split(":")[0] if ":" in name else None),
                "gptscan_code": raw.get("code") or tx.get("gptscan_code"),
                "category_defi_logic": bool(tx.get("defi_logic")),
                # Leer, wenn findings.yaml kein redliches Mapping kennt.
                "dasp10": tx.get("dasp10", ""),
                "swc": tx.get("swc", ""),
                "classification": tx.get("classification", ""),
                "function": fn,
                "function_source": t["source_origin"],
                "lines": {"start": start, "end": end},
                # Unter --main zaehlen die Zeilen in der REDUZIERTEN Datei.
                "lines_refer_to": t["source_origin"],
                "severity": f.get("severity"),
                "description": raw.get("description") or f.get("message", "").split("\n")[0],
                "recommendation": raw.get("recommendation", ""),
                # GPTScan gibt keinen Konfidenzwert aus (output.json kennt nur
                # code/severity/title/description/recommendation/affectedFiles).
                # Nicht erfinden -- null, und im summary.md benannt.
                "confidence": None,
                "run_id": t["run_id"],
                "timestamp": ts,
                # AP5: the task's run was cut short by the deadline/net --
                # fewer findings than a full run, appended so the existing
                # column order (and comparisons against eval/) stays intact.
                "timeout_hit": t["timeout_hit"],
                "timeout_stage": t["timeout_stage"],
            })
    return rows


# --------------------------------------------------------------------------- #
# Ausgaben
# --------------------------------------------------------------------------- #

def build_meta(run_id: str, tasks: list[dict], rows: list[dict],
               params: dict, merged: list[str]) -> dict:
    """Der Inhalt von run_meta.json: Laufparameter, SHA1 der Tool-Dateien,
    Zaehlungen je Quelle und Zustand, Laufzeit, Tokens, Kosten, Fehlerliste."""
    costs = [t["meta"].get("estimated_cost") for t in tasks
             if isinstance(t["meta"].get("estimated_cost"), (int, float))]
    durs = [t["duration"] for t in tasks if isinstance(t["duration"], (int, float))]
    errs = [{"contract": t["contract_id"], "exit_code": t["exit_code"],
             "errors": t["errors"], "fails": t["fails"], "degraded": t["degraded"]}
            for t in tasks if t["errors"] or t["fails"] or t["degraded"]]
    return {
        "run_id": run_id,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generator": "analysis_tools/gptscan_eval.py",
        "merged_runs": merged,
        "run_parameters": params,
        "tool_state": {
            "config_yaml": params.get("tool_yaml_sha1"),
            "findings_yaml": params.get("findings_yaml_sha1"),
            "parser_py": params.get("parser_sha1"),
            "entrypoint_sh": params.get("entrypoint_sha1"),
            "main_contract_py": params.get("main_contract_sha1"),
            "taxonomy_source": "smartbugs/tools/gptscan/findings.yaml",
        },
        "contracts": len(tasks),
        "contracts_main_reduced": sum(1 for t in tasks if t["source_origin"] == "main-reduziert"),
        "contracts_source_full": sum(1 for t in tasks if t["source_origin"] == "voll"),
        "contracts_source_unknown": sum(1 for t in tasks if t["source_origin"] == "unbekannt"),
        "findings_total": len(rows),
        "contracts_with_findings": len({r["contract_id"] for r in rows}),
        "runtime": {
            "wallclock_seconds": params.get("wallclock_seconds"),
            "task_seconds_sum": round(sum(durs), 1),
            "task_seconds_median": round(statistics.median(durs), 1) if durs else None,
            "task_seconds_max": round(max(durs), 1) if durs else None,
        },
        "tokens": {
            "prompt": sum(t["meta"].get("token_sent") or 0 for t in tasks),
            "completion": sum(t["meta"].get("token_received") or 0 for t in tasks),
            "llm_calls": sum(t["meta"].get("llm_calls") or 0 for t in tasks),
        },
        "cost_usd": {
            "sum": round(sum(costs), 5), "n": len(costs),
            "median": round(statistics.median(costs), 5) if costs else None,
            "max": round(max(costs), 5) if costs else None,
        },
        "states": {
            "tasks_with_errors": sum(1 for t in tasks if t["errors"]),
            "tasks_with_fails": sum(1 for t in tasks if t["fails"]),
            "tasks_degraded": sum(1 for t in tasks if t["degraded"]),
            "tasks_clean_no_findings": sum(1 for t in tasks
                                           if not t["findings"] and not t["fails"] and not t["degraded"]),
        },
        "error_list": errs,
    }


def write_summary(path: pathlib.Path, run_id: str, tasks: list[dict],
                  rows: list[dict], m: dict, tax: dict) -> None:
    """summary.md schreiben: Eckdaten, Zustaende, Findings je Kategorie,
    Severity und Contract, Contracts ohne Findings, Vorbehalte zu den Feldern.
    *m* ist das Ergebnis von build_meta."""
    by_cat = collections.Counter(r["category_raw"] for r in rows)
    by_con = collections.Counter(r["contract_id"] for r in rows)
    by_sev = collections.Counter(r["severity"] for r in rows)
    n = len(tasks)
    degraded = [t["contract_id"] for t in tasks if t["degraded"]]
    failed = [t["contract_id"] for t in tasks if t["fails"]]
    nofind = [t["contract_id"] for t in tasks
              if not t["findings"] and not t["fails"] and not t["degraded"]]
    # AP5: tasks whose run was cut short by the deadline/net. They stay
    # counted in every total above -- excluding them would be the same
    # measurement error with the opposite sign.
    timedout = [t["contract_id"] for t in tasks if t["timeout_hit"]]

    L = [
        f"# GPTScan-Lauf `{run_id}` -- Auswertung", "",
        f"Erzeugt {m['generated_utc']} von `analysis_tools/gptscan_eval.py`.",
        "Rohergebnisse: `" + (m["run_parameters"].get("results_dir") or "-") + "` (unveraendert).",
        "", "## Eckdaten", "",
        "| | |", "|---|---|",
        f"| Contracts | {n} |",
        f"| Findings | {len(rows)} auf {m['contracts_with_findings']} Contracts |",
        f"| Provider / Modell | {m['run_parameters'].get('provider')} / {m['run_parameters'].get('model')} |",
        f"| MAIN | {m['run_parameters'].get('main')} |",
        f"| processes / timeout / mem-limit | {m['run_parameters'].get('processes')} / "
        f"{m['run_parameters'].get('timeout_sec')} s / {m['run_parameters'].get('mem_limit')} |",
        f"| Kosten | ${m['cost_usd']['sum']:.4f} (Median ${m['cost_usd']['median'] or 0:.5f}, "
        f"max ${m['cost_usd']['max'] or 0:.5f}) |",
        f"| Tokens | {m['tokens']['prompt']:.0f} prompt / {m['tokens']['completion']:.0f} completion, "
        f"{m['tokens']['llm_calls']} LLM-Calls |",
        f"| Laufzeit | Wanduhr {m['runtime']['wallclock_seconds']} s, Task-Summe "
        f"{m['runtime']['task_seconds_sum']} s, Median {m['runtime']['task_seconds_median']} s, "
        f"max {m['runtime']['task_seconds_max']} s |",
        "",
        "Der Timeout wirkt seit AP5 im Container (Bremse bei GPTScan, Netz als "
        "letzte Stufe); Docker bleibt als aeusserer Fallback bestehen.",
        "", "## Zustaende", "",
        "Begriffe nach `docs/BA-ERRORS-VS-FAILS.md`.", "",
        "| Zustand | Anzahl | Bedeutung |", "|---|---|---|",
        f"| findings | {len(rows)} | Verdachtsfall ueber den Contract |",
        f"| Tasks mit errors | {m['states']['tasks_with_errors']} | Werkzeug hat das Problem "
        "bemerkt, abgefangen und weitergearbeitet |",
        f"| Tasks mit fails | {m['states']['tasks_with_fails']} | Werkzeug ausgehebelt, "
        "kein Ergebnis zustande gekommen |",
        f"| Contract nicht uebersetzt (degraded) | {m['states']['tasks_degraded']} | "
        "Compilat gescheitert -> ein Lauf ohne Findings ist hier UNBESTIMMT, nicht sauber |",
        f"| ohne Findings, sauber | {m['states']['tasks_clean_no_findings']} | uebersetzt, "
        "vollstaendig gelaufen, nichts gemeldet |",
        "",
        f"Davon Teillaeufe (Timeout): {len(timedout)} von {n}. Ein durch die AP5-Deadline "
        "vorzeitig beendeter Lauf liefert weniger Findings als ein Volllauf; er bleibt "
        "dennoch in allen Zahlen oben mitgezaehlt, siehe `sb_timeout` in "
        "`docs/BA-AP5-TIMEOUT-DESIGN.md`.",
        "",
        f"**Fehlerquote** (Tasks mit fails / alle Tasks): {m['states']['tasks_with_fails']}/{n} = "
        f"{100*m['states']['tasks_with_fails']/n:.1f} %.",
        f"**Errorquote** (Tasks mit errors / alle Tasks): {m['states']['tasks_with_errors']}/{n} = "
        f"{100*m['states']['tasks_with_errors']/n:.1f} %.",
        "",
    ]
    if failed:
        L += ["Tasks mit fails: " + ", ".join(f"`{c}`" for c in failed), ""]
    if m["merged_runs"]:
        sub = [t["contract_id"] for t in tasks if t["run_id"] != run_id]
        L += [
            "> **Zusammengefuehrter Blick.** Die Zahlen oben schliessen den Nachlauf "
            + ", ".join(f"`{r}`" for r in m["merged_runs"]) + " ein. Im Hauptlauf "
            f"`{run_id}` selbst scheiterten "
            + ", ".join(f"`{c}`" for c in (m["run_parameters"].get("exit_127") or []))
            + " mit Exit 127: ihr Dateiname benennt keinen im File enthaltenen Contract, "
            "`--main` hat also nichts, worauf es reduzieren koennte. SmartBugs fuehrt das "
            "als fail mit Klartext (`sb/parse_utils.py`), nicht als 'keine Findings'. "
            "Ersetzt wurden dadurch: " + (", ".join(f"`{c}`" for c in sub) or "keine")
            + " -- diese Contracts sind OHNE `--main` analysiert und in der Spalte "
            "`function_source` als `voll` erkennbar. Der Hauptlauf allein hat damit "
            f"{len(m['run_parameters'].get('exit_127') or [])} fails; hier stehen 0, weil "
            "der Nachlauf sie aufgeloest hat.", "",
        ]
    if degraded:
        L += ["Nicht uebersetzt (nie als 'keine Findings' zaehlen): "
              + ", ".join(f"`{c}`" for c in degraded), ""]
    if timedout:
        L += ["Teillaeufe (Timeout, zaehlen regulaer mit): "
              + ", ".join(f"`{c}`" for c in timedout), ""]

    L += ["## Findings je Kategorie", "",
          "`category_defi_logic` = die Regel hat in SWC/DASP kein redliches Gegenstueck "
          "(8 von 10, so in `findings.yaml` begruendet).", "",
          "| MWE-Regel | Anzahl | Contracts | DeFi-Logik | DASP-10 | SWC |",
          "|---|---:|---:|---|---|---|"]
    for cat, cnt in by_cat.most_common():
        tx = tax.get(cat, {})
        cons = len({r["contract_id"] for r in rows if r["category_raw"] == cat})
        L.append(f"| {cat} | {cnt} | {cons} | {'ja' if tx.get('defi_logic') else 'nein'} | "
                 f"{tx.get('dasp10') or '--'} | {tx.get('swc') or '--'} |")
    stumm = [c for c in tax if c not in by_cat]
    L += ["", f"Regeln ohne Treffer in diesem Lauf: {len(stumm)} von {len(tax)}"]
    if stumm:
        L += ["", *[f"- {c}" for c in sorted(stumm)]]

    L += ["", "### Severity", "",
          "| Severity | Findings |", "|---|---:|"]
    for s, c in by_sev.most_common():
        L.append(f"| {s or '--'} | {c} |")

    L += ["", "## Findings je Contract", "",
          f"{len(by_con)} von {n} Contracts tragen mindestens ein Finding.", "",
          "| Contract | Findings | Regeln |", "|---|---:|---|"]
    for c, cnt in by_con.most_common():
        regeln = sorted({r["mwe"] for r in rows if r["contract_id"] == c if r["mwe"]})
        L.append(f"| `{c}` | {cnt} | {', '.join(regeln)} |")

    L += ["", "## Contracts ohne Findings", "",
          f"{len(nofind)} Contracts sind uebersetzt, vollstaendig gelaufen und melden nichts. "
          f"Getrennt davon: {len(degraded)} nicht uebersetzt (unbestimmt) und {len(failed)} fails.",
          ""]
    if nofind:
        L += [", ".join(f"`{c}`" for c in sorted(nofind)), ""]

    L += ["## Vorbehalte zu den Feldern in findings.jsonl", "",
          "- `confidence` ist immer `null`. GPTScans `output.json` kennt nur "
          "`code`, `severity`, `title`, `description`, `recommendation`, `affectedFiles` "
          "-- einen Konfidenzwert gibt das Werkzeug nicht aus. Das Feld bleibt leer, "
          "statt einen Wert zu erfinden.",
          "- `function` ist heuristisch aus dem analysierten Quelltext bestimmt "
          "(Deklarationskopf + Klammerzaehlung), nicht von GPTScan geliefert. "
          "Wo die Zuordnung nicht greift, bleibt das Feld leer.",
          f"- `lines` bezieht sich auf die Datei, die GPTScan tatsaechlich gesehen hat: "
          f"{m['contracts_main_reduced']} Contracts main-reduziert, "
          f"{m['contracts_source_full']} voll, {m['contracts_source_unknown']} unbestimmt. "
          "Das Feld `lines_refer_to` haelt das je Finding fest. Zeilennummern aus einem "
          "MAIN-Lauf sind mit denen eines Laufs ohne MAIN NICHT vergleichbar.",
          "- `dasp10` bleibt leer, wo `findings.yaml` kein redliches Mapping kennt. "
          "Die dort unter `related` vermerkten Naeherungen werden bewusst NICHT eingesetzt.",
          ""]
    path.write_text("\n".join(L), encoding="utf-8")


def write_comparison(path: pathlib.Path, run_id: str, base_id: str,
                     rows: list[dict], brows: list[dict],
                     tasks: list[dict], btasks: list[dict]) -> dict:
    """Vergleich auf (Contract, MWE-Regel). Zeilennummern taugen dafuer nicht:
    unter --main zaehlen sie in der reduzierten Datei."""
    def key(r):
        """Vergleichsschluessel eines Findings: (Contract, MWE-Regel)."""
        return (r["contract_id"], r["mwe"])

    # Nur Contracts vergleichen, die in BEIDEN Laeufen einen Task haben. Sonst
    # zaehlte jeder im neuen Lauf gar nicht gefahrene Contract als
    # "verschwunden" -- das waere kein Reproduzierbarkeitsbefund, sondern ein
    # Artefakt der Laufgroesse.
    shared = {t["contract_id"] for t in tasks} & {t["contract_id"] for t in btasks}
    rows = [r for r in rows if r["contract_id"] in shared]
    brows = [r for r in brows if r["contract_id"] in shared]

    new_c = collections.Counter(key(r) for r in rows)
    old_c = collections.Counter(key(r) for r in brows)
    inter = new_c & old_c
    matched = sum(inter.values())
    added = new_c - old_c
    gone = old_c - new_c

    n_new, n_old = sum(new_c.values()), sum(old_c.values())
    cs_new = {r["contract_id"] for r in rows}
    cs_old = {r["contract_id"] for r in brows}
    common = sorted(shared)

    stats = {
        "baseline": base_id,
        "findings_new": n_new, "findings_baseline": n_old,
        "matched": matched,
        "added": sum(added.values()), "disappeared": sum(gone.values()),
        "share_baseline_reproduced": round(matched / n_old, 4) if n_old else None,
        "share_new_already_known": round(matched / n_new, 4) if n_new else None,
        "jaccard_pairs": round(len(set(new_c) & set(old_c)) / len(set(new_c) | set(old_c)), 4)
                         if (new_c or old_c) else None,
        "contracts_compared": len(common),
        "contracts_with_findings_new": len(cs_new),
        "contracts_with_findings_baseline": len(cs_old),
        "contracts_agree": len([c for c in common if (c in cs_new) == (c in cs_old)]),
    }

    L = [
        f"# `{run_id}` gegen `{base_id}`", "",
        "Verglichen wird auf dem Paar **(Contract, MWE-Regel)**, nicht auf Zeilennummern: "
        "unter `--main` zaehlen GPTScans Zeilen in der reduzierten Datei und sind mit denen "
        "eines Laufs ohne `--main` nicht vergleichbar.", "",
        "Beide Laeufe bleiben erhalten. Roh: `smartbugs/results/gptscan/<runid>/`.", "",
        "## Bilanz", "",
        "| | |", "|---|---:|",
        f"| Findings neu (`{run_id}`) | {n_new} |",
        f"| Findings Referenz (`{base_id}`) | {n_old} |",
        f"| deckungsgleich | {matched} |",
        f"| neu hinzugekommen | {sum(added.values())} |",
        f"| verschwunden | {sum(gone.values())} |",
        f"| verglichene Contracts | {len(common)} |",
        f"| Contracts mit Findings (neu / Referenz) | {len(cs_new)} / {len(cs_old)} |",
        "", "## Reproduzierbarkeit (AP4)", "",
        f"- Anteil der Referenz-Findings, die wieder auftauchen: "
        f"**{100*matched/n_old:.1f} %** ({matched}/{n_old})" if n_old else "- Referenz leer",
        f"- Anteil der neuen Findings, die schon vorher da waren: "
        f"**{100*matched/n_new:.1f} %** ({matched}/{n_new})" if n_new else "- Lauf leer",
        f"- Jaccard ueber (Contract, Regel)-Paare: {stats['jaccard_pairs']}",
        f"- Contracts mit gleichem Befund-Ja/Nein: {stats['contracts_agree']}/{len(common)}",
        "",
        "Der dokumentierte Referenzbefund lautet: bei Wiederholung trotz `temperature=0` "
        "waren nur 74 % der Findings identisch. Die Zahlen oben sind mit dieser Angabe nur "
        "dann vergleichbar, wenn dort dieselbe Zaehlweise zugrunde lag -- die Definition "
        "steht hier ausdruecklich dabei, damit der Vergleich nachpruefbar bleibt. Dieser "
        "Lauf unterscheidet sich von der Referenz zusaetzlich durch `--main`, ist also "
        "keine reine Wiederholung.", "",
    ]
    if added:
        L += ["## Neu hinzugekommen", "", "| Contract | Regel | Anzahl |", "|---|---|---:|"]
        L += [f"| `{c}` | {r} | {n} |" for (c, r), n in sorted(added.items())]
        L += [""]
    if gone:
        L += ["## Verschwunden", "", "| Contract | Regel | Anzahl |", "|---|---|---:|"]
        L += [f"| `{c}` | {r} | {n} |" for (c, r), n in sorted(gone.items())]
        L += [""]
    path.write_text("\n".join(L), encoding="utf-8")
    return stats


def write_readme(entries: list[dict], others: list[tuple] = ()) -> None:
    """eval/README.md neu schreiben.

    *entries* sind die GPTScan-Laeufe fuer die Tabelle (run_id, main, dry,
    contracts, findings, cost, zweck); *others* die uebrigen Auswertungen als
    Tupel (Ordner, Werkzeug, Contracts, Findings), auf die nur verwiesen wird.
    """
    L = [
        "# eval/ -- Auswertungen der aufgezeichneten Laeufe", "",
        "Hier liegen ausschliesslich ABGELEITETE Daten. Die Rohergebnisse stehen unter",
        "`smartbugs/results/<werkzeug>/<runid>/` und werden von den Skripten nur gelesen,",
        "nie veraendert oder geloescht. Alt und Neu bleiben beide erhalten.", "",
        "Diese Datei wird von `analysis_tools/gptscan_eval.py` fortgeschrieben; sie",
        "fuehrt die GPTScan-Laeufe im Detail und die uebrigen Auswertungen als",
        "Verweis. **Was jeder Ordner enthaelt, steht in seiner eigenen `README.md`.**",
        "",
        "> **Von den Rohergebnissen sind je Task `result.json` und `smartbugs.json`",
        "> versioniert** (seit 25.09.2026; `smartbugs/.gitignore`). Logs, Archive und",
        "> SARIF liegen im Release-Zip des Repositorys (README, \"Wo die Ergebnisse",
        "> liegen\"). Die Ordner unter `eval/` sind die daraus abgeleiteten",
        "> Auswertungen. Zum Nachfahren eines Laufs:",
        "> `.\\run_full_v2.ps1 -Mode full -MainFallback` (Parameter und Commit stehen in",
        "> `run_params.json`); bitgleiche Ergebnisse sind dabei nicht zu erwarten, siehe die",
        "> Reproduzierbarkeitszahlen im Vergleichsdokument.", "",
        "## Wie ein Ordner hier entsteht", "",
        "1. `run_full_v2.ps1` faehrt den Lauf und legt `eval/<runid>/run_params.json` ab",
        "   (Aufrufparameter, Versionen, SHA1 der Tool-Dateien, Git-Commit).",
        "2. `analysis_tools/gptscan_eval.py <runid>` liest die Rohergebnisse und erzeugt",
        "   `findings.jsonl`, `run_meta.json`, `summary.md` und den Vergleich gegen einen",
        "   Altlauf.", "",
        "Das SWC/DASP-Mapping wird nirgends hier dupliziert, sondern bei jedem Lauf aus",
        "`smartbugs/tools/gptscan/findings.yaml` gelesen. 8 der 10 MWE-Regeln sind dort",
        "bewusst als `BUSINESS-LOGIC (no SWC/DASP)` gefuehrt; nur MWE-205 (SWC-114/DASP-7)",
        "und MWE-207 (DASP-2) haben ein redliches Gegenstueck. `dasp10` bleibt sonst leer.", "",
        "## Laeufe", "",
        "Kosten in Klammern sind SIMULIERT: im Dry-Run wird kein API-Call abgesetzt,",
        "GPTScan schaetzt den Betrag nur. Gemessen an den Live-Laeufen liegt diese",
        "Schaetzung ueber den tatsaechlichen Kosten: Dry $0,3838 gegen $0,3638 im",
        "Live-Lauf mit MAIN und $0,2769 im Referenzlauf ohne MAIN, also 6 % bzw. 39 %",
        "darueber.", "",
        "| Ordner | Rohergebnis | MAIN | Contracts | Findings | Kosten | Zweck |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for e in entries:
        cost = f"({e['cost']:.4f})" if e["dry"] else f"${e['cost']:.4f}"
        L.append(f"| `eval/{e['run_id']}/` | `smartbugs/results/gptscan/{e['run_id']}/` | "
                 f"{'ja' if e['main'] else 'nein'} | {e['contracts']} | {e['findings']} | "
                 f"{cost} | {e['zweck']} |")
    if others:
        L += [
            "", "## Weitere Auswertungen in diesem Verzeichnis", "",
            "Erzeugt von `analysis_tools/build_eval.py` (LLMSmartAudit-Laeufe) bzw.",
            "`analysis_tools/curated_eval.py` (curated-Hauptlauf, alle drei Werkzeuge).",
            "Sie tragen ein eigenes `run_meta.json`-Schema und stehen deshalb nicht in",
            "der Tabelle oben.", "",
            "| Ordner | Werkzeug | Contracts | Findings |",
            "|---|---|---:|---:|",
        ]
        for name, tool, contracts, findings in others:
            L.append("| [`eval/%s/`](%s/README.md) | %s | %s | %s |"
                     % (name, name, tool or "-",
                        "-" if contracts is None else contracts,
                        "-" if findings is None else findings))
        L += [
            "",
            "Dazu kommen `eval/per_contract/` (eine Zeile je Contract, "
            "`analysis_tools/per_contract_stats.py`), `eval/slither_mwefixed_v2/` "
            "(Slither auf dem DeFi-Korpus, Export von `sb.results2csv`) und "
            "`eval/_runlogs/` (Konsolenprotokolle der Massenlaeufe) -- alle mit "
            "eigener `README.md`. Welcher der Laeufe unter `smartbugs/results/` "
            "wozu diente und wo er ausgewertet ist, steht in `eval/LAUFREGISTER.md`.",
        ]
    L += [
        "", "## Verhaeltnis zu den Altlaeufen", "",
        "Alle GPTScan-Laeufe unter `smartbugs/results/gptscan/` vor dem 15.08.2026 sind",
        "ohne `--main` entstanden -- nachpruefbar am Docker-Entrypoint in der jeweiligen",
        "`smartbugs.json`, der dort auf `'0'` endet. Der Volllauf mit `--main` vom",
        "15.08.2026 ist der erste seiner Art; der Vergleich Alt gegen Neu ist damit ein",
        "Vergleich MAIN=0 gegen MAIN=1 auf demselben Korpus, Image und Modell.", "",
        "Referenzlauf fuer den Vergleich ist `curated_mwefixed_live`",
        "(96 Contracts, 77 Findings auf 40 Contracts, $0.2769).", "",
        "## Zustaende", "",
        "Nach `docs/BA-ERRORS-VS-FAILS.md`:", "",
        "- **findings** -- Verdachtsfall ueber den Contract.",
        "- **errors** -- das Werkzeug hat ein Problem bemerkt, abgefangen und weitergearbeitet.",
        "- **fails** -- das Werkzeug wurde ausgehebelt, ein Ergebnis kam nicht zustande.",
        "- **nicht uebersetzt** -- das Compilat ist gescheitert. GPTScan faengt das ab und",
        "  endet trotzdem mit Exit-Code 0; der Parser markiert es als Info",
        "  `analysis degraded`. Solche Contracts werden NIE als 'keine Findings' gezaehlt,",
        "  ihr Ergebnis ist unbestimmt.", "",
    ]
    (EVAL / "README.md").write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------- #

def main() -> int:
    """Kommandozeile: Lauf einlesen, Nachlaeufe einmischen, findings.jsonl,
    run_meta.json, summary.md und den Vergleich schreiben, eval/README.md
    fortschreiben. Rueckgabe 0; 2, wenn der Lauf fehlt."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runid")
    ap.add_argument("--baseline", default="curated_mwefixed_live")
    ap.add_argument("--merge-run", action="append", default=[],
                    help="weiteren Lauf einbeziehen, z.B. den _nomain-Nachlauf")
    ap.add_argument("--no-compare", action="store_true")
    args = ap.parse_args()

    python = sys.executable
    rundir = RESULTS / args.runid
    if not rundir.is_dir():
        print(f"Lauf nicht gefunden: {rundir}", file=sys.stderr)
        return 2

    tax = load_taxonomy()
    tasks = read_run(rundir, tax, python, args.runid)
    merged = []
    for extra in args.merge_run:
        d = RESULTS / extra
        if not d.is_dir():
            print(f"WARNUNG: --merge-run {extra} nicht gefunden, uebersprungen", file=sys.stderr)
            continue
        have = {t["contract_id"] for t in tasks if not t["fails"]}
        for t in read_run(d, tax, python, extra):
            # Der Nachlauf ersetzt genau die Faelle, die im Hauptlauf scheiterten.
            tasks = [x for x in tasks if not (x["contract_id"] == t["contract_id"] and x["fails"])]
            if t["contract_id"] not in have:
                tasks.append(t)
        merged.append(extra)
    tasks.sort(key=lambda t: t["contract_id"])

    rows = finding_rows(tasks, tax)

    evaldir = EVAL / args.runid
    evaldir.mkdir(parents=True, exist_ok=True)
    params = {}
    pf = evaldir / "run_params.json"
    if pf.exists():
        try:
            params = json.loads(pf.read_text(encoding="utf-8-sig"))
        except ValueError:
            params = {}
    if not params and tasks:
        # Kein run_params.json (Lauf vor Einfuehrung des Protokolls, oder das
        # Skript kam nicht bis dorthin). Was sich aus den Rohergebnissen selbst
        # belegen laesst, wird abgeleitet; alles andere bleibt ausdruecklich
        # unbekannt statt geraten.
        t0 = tasks[0]
        entry = ""
        sbj = REPO / t0["task_dir"] / "smartbugs.json"
        try:
            entry = (json.loads(sbj.read_text(encoding="utf-8"))
                     .get("docker", {}) or {}).get("entrypoint", "") or ""
        except (OSError, ValueError):
            pass
        parts = entry.split("'")
        params = {
            "source": "aus den Rohergebnissen abgeleitet, kein run_params.json vorhanden",
            "run_id": args.runid,
            "main": t0["main"],
            "provider": t0["meta"].get("provider"),
            "model": t0["meta"].get("model"),
            "dry_run": bool(t0["meta"].get("dry_run")),
            "timeout_sec": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None,
            "processes": None,
            "mem_limit": None,
            "docker_image": "smartbugs/gptscan:1.0",
            "results_dir": f"smartbugs/results/gptscan/{args.runid}",
        }

    with (evaldir / "findings.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    m = build_meta(args.runid, tasks, rows, params, merged)

    if not args.no_compare:
        bdir = RESULTS / args.baseline
        if bdir.is_dir():
            btasks = read_run(bdir, tax, python, args.baseline)
            brows = finding_rows(btasks, tax)
            m["comparison"] = write_comparison(
                evaldir / f"comparison_{args.baseline}.md",
                args.runid, args.baseline, rows, brows, tasks, btasks)
        else:
            print(f"WARNUNG: Referenzlauf {bdir} fehlt, Vergleich uebersprungen", file=sys.stderr)

    (evaldir / "run_meta.json").write_text(json.dumps(m, indent=1, ensure_ascii=False),
                                           encoding="utf-8")
    write_summary(evaldir / "summary.md", args.runid, tasks, rows, m, tax)

    # eval/README.md ueber alle vorhandenen Auswertungen fortschreiben
    entries = []
    others = []
    for d in sorted(EVAL.iterdir()):
        rm = d / "run_meta.json"
        if not d.is_dir() or not rm.exists():
            continue
        try:
            e = json.loads(rm.read_text(encoding="utf-8"))
        except ValueError:
            continue
        # Unter eval/ liegen inzwischen auch Auswertungen, die build_eval.py und
        # curated_eval.py erzeugt haben. Sie tragen ein anderes run_meta-Schema
        # (kein run_parameters, cost_usd_estimated statt cost_usd) und gehoeren
        # nicht in die GPTScan-Tabelle. Frueher lief dieses Skript an ihnen in
        # einen KeyError.
        if "run_parameters" not in e or not isinstance(e.get("cost_usd"), dict):
            # Das Werkzeug steht entweder direkt im Meta (curated_eval.py) oder
            # laesst sich aus dem Pfad der Taxonomie ablesen (build_eval.py).
            tool = e.get("tool") or ""
            if not tool:
                mt = re.search(r"tools/([^/]+)/findings\.yaml", e.get("taxonomy") or "")
                tool = mt.group(1) if mt else "-"
            others.append((d.name, tool, e.get("contracts"), e.get("findings_total")))
            continue
        p = e.get("run_parameters", {})
        dry = bool(p.get("dry_run"))
        zweck = {"dry": "Pipelinetest, 0 API-Calls", "smoke": "Live-Stichprobe",
                 "full": "Volllauf"}.get(p.get("mode"))
        if not zweck:
            zweck = "Pipelinetest, 0 API-Calls" if dry else "Live-Lauf"
        if e["run_id"] == args.baseline:
            zweck = "Referenzlauf ohne MAIN, Baseline der Vergleiche"
        if e.get("merged_runs"):
            zweck += " (inkl. Nachlauf " + ", ".join(e["merged_runs"]) + ")"
        entries.append({
            "run_id": e["run_id"], "main": p.get("main"), "dry": dry,
            "contracts": e["contracts"], "findings": e["findings_total"],
            "cost": e["cost_usd"]["sum"], "zweck": zweck,
        })
    write_readme(entries, others)

    print(f"Contracts:        {m['contracts']}"
          f"  (main-reduziert {m['contracts_main_reduced']},"
          f" voll {m['contracts_source_full']}, unbestimmt {m['contracts_source_unknown']})")
    print(f"Findings:         {m['findings_total']} auf {m['contracts_with_findings']} Contracts")
    print(f"Kosten:           ${m['cost_usd']['sum']:.4f}")
    print(f"errors / fails:   {m['states']['tasks_with_errors']} / {m['states']['tasks_with_fails']}"
          f"   nicht uebersetzt: {m['states']['tasks_degraded']}")
    if "comparison" in m:
        c = m["comparison"]
        print(f"gegen {c['baseline']}: {c['matched']} gleich, {c['added']} neu, "
              f"{c['disappeared']} verschwunden "
              f"({100*(c['share_baseline_reproduced'] or 0):.1f} % der Referenz reproduziert)")
    print(f"geschrieben: {evaldir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
