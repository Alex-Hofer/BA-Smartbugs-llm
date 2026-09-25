#!/usr/bin/env python3
"""Recall, Precision und F1 allein aus den versionierten Dateien unter eval/.

Wozu: Die Rohergebnisse unter smartbugs/results/ sind git-ignoriert, und die
Ground Truth (smartbugs-curated/) wird geklont, nicht mitgefuehrt. Wer nur das
Repository hat, kann mit diesem Skript trotzdem nachrechnen, ob die Kennzahlen
in eval/curated_v1_20260705__metriken.md und in den run_meta.json stimmen --
aus zwei Dateien, die beide versioniert sind:

    eval/<ordner>/findings.jsonl              eine Zeile je Finding, mit Label
                                              des Contracts und DASP-Zuordnung
    eval/per_contract/<runid>__<tool>.csv     eine Zeile je Task, also auch die
                                              Contracts OHNE Finding (die
                                              Grundgesamtheit je Kategorie)

Zaehlweise wie evaluate_curated.py (Kopf dort): Contract-Level, ein Contract
gilt als erkannt, wenn mindestens ein Finding auf seine gelabelte Kategorie
abbildet; ``flagged`` zaehlt alle Contracts, fuer die eine Kategorie gemeldet
wurde. Findings ohne DASP-Zuordnung gehen nicht ein.

Die Label kommen aus den Dateien selbst: ``label_dir`` (curated_eval.py) oder
der erste Pfadteil von ``contract_file`` (build_eval.py) -- das ist der
Kategorienordner von smartbugs-curated, der je Datei genau ein Label traegt.
Die externe vulnerabilities.json wird nicht gebraucht; dass beide dasselbe
sagen, wurde am 25.09.2026 gegen den Clone auf 230e649 geprueft.

Aufruf (aus dem Repository-Wurzelverzeichnis):

    python analysis_tools/metrics_from_eval.py eval/curated_v1_20260705__llmsmartaudit
    python analysis_tools/metrics_from_eval.py eval/curated_v1_20260705__slither-0.11.3 --check
    python analysis_tools/metrics_from_eval.py eval/llmsa_curated_v2 \
        --population eval/per_contract/curated_v1_20260705__llmsmartaudit.csv

``--population`` ist noetig, wenn der Ordner keine eigene per_contract-Tabelle
hat (llmsa_curated_v2: Rohdaten verloren; derselbe Korpus wie curated_v1).
``--check`` vergleicht mit ``metrics_contract_level`` in run_meta.json und
endet mit Exit-Code 1, wenn eine Zahl abweicht. Ausgabe ist eine
Markdown-Tabelle; das Skript liest nur.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from evaluate_curated import DASP_TO_CATEGORY, rates  # noqa: E402

DASP_RE = re.compile(r"DASP-(\d+)")


def load_population(csv_path: pathlib.Path) -> dict[tuple[str, str], list[str]]:
    """``(kategorie-ordner, contract_id) -> [label]`` aus einer per_contract-CSV.

    ``task_dir`` hat dort die Form ``<kategorie-ordner>/<datei>``; der Ordner ist
    das Label der Datei in smartbugs-curated.
    """
    pop = {}
    with csv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            task_dir = row["task_dir"].replace("\\", "/")
            label_dir = task_dir.split("/")[0]
            pop[(label_dir, row["contract_id"])] = [label_dir]
    return pop


def load_findings(jsonl_path: pathlib.Path) -> list[dict]:
    """Alle Zeilen einer findings.jsonl als Liste von Dicts."""
    with jsonl_path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def category_of(row: dict) -> str | None:
    """curated-Kategorie eines Findings oder None, wenn es keine DASP-Zuordnung hat."""
    cat = row.get("dasp_category")
    if cat:
        return cat
    m = DASP_RE.search(str(row.get("dasp10") or ""))
    return DASP_TO_CATEGORY.get(int(m.group(1))) if m else None


def key_of(row: dict) -> tuple[str, str]:
    """``(kategorie-ordner, contract_id)`` eines Findings."""
    label_dir = row.get("label_dir")
    if not label_dir:
        label_dir = str(row.get("contract_file") or "").replace("\\", "/").split("/")[0]
    return (label_dir, row["contract_id"])


def metrics(population: dict, findings: list[dict]) -> dict:
    """Zaehler und Raten je Kategorie plus ``GESAMT``, Schema wie run_meta.json.

    Findings zu Contracts ausserhalb der Grundgesamtheit werden ignoriert und
    gezaehlt (Schluessel ``_outside``), damit ein falsch gewaehlter
    ``--population``-Pfad auffaellt.
    """
    per = {}
    for _key, labels in population.items():
        for c in labels:
            per.setdefault(c, {"contracts": 0, "detected": 0, "flagged": 0})["contracts"] += 1
    found: dict[tuple[str, str], set] = {}
    outside = 0
    for row in findings:
        cat = category_of(row)
        if not cat:
            continue
        k = key_of(row)
        if k not in population:
            outside += 1
            continue
        found.setdefault(k, set()).add(cat)
    for k, cats in found.items():
        for c in population[k]:
            if c in cats:
                per[c]["detected"] += 1
        for c in cats:
            per.setdefault(c, {"contracts": 0, "detected": 0, "flagged": 0})["flagged"] += 1
    out = {}
    for cat in sorted(per):
        v = per[cat]
        rec, prec, f1 = rates(v["contracts"], v["detected"], v["flagged"])
        out[cat] = dict(v, recall=rec, precision=prec, f1=f1)
    c = sum(v["contracts"] for v in per.values())
    d = sum(v["detected"] for v in per.values())
    fl = sum(v["flagged"] for v in per.values())
    rec, prec, f1 = rates(c, d, fl)
    out["GESAMT"] = {"contracts": c, "detected": d, "flagged": fl,
                     "recall": rec, "precision": prec, "f1": f1}
    out["_outside"] = outside
    return out


def render(m: dict, title: str) -> str:
    """Markdown-Tabelle im Format von eval/curated_v1_20260705__metriken.md."""
    pct = lambda v: ("%d %%" % round(100 * v)) if v is not None else "–"
    L = ["## %s" % title, "",
         "| Kategorie | Contracts | Erkannt | Recall | Geflaggt | Precision | F1 |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for cat in sorted(k for k in m if k not in ("GESAMT", "_outside")):
        v = m[cat]
        L.append("| %s | %d | %d | %s | %d | %s | %s |" % (
            cat, v["contracts"], v["detected"], pct(v["recall"]), v["flagged"],
            pct(v["precision"]), pct(v["f1"])))
    v = m["GESAMT"]
    L.append("| **GESAMT** | **%d** | **%d** | **%s** | **%d** | **%s** | **%s** |" % (
        v["contracts"], v["detected"], pct(v["recall"]), v["flagged"],
        pct(v["precision"]), pct(v["f1"])))
    if m.get("_outside"):
        L += ["", "%d Findings gehoeren zu Contracts ausserhalb der Grundgesamtheit "
              "und wurden ignoriert." % m["_outside"]]
    return "\n".join(L)


def check_against_run_meta(m: dict, run_meta: dict) -> list[str]:
    """Abweichungen von ``metrics_contract_level`` in run_meta.json, leer wenn gleich."""
    ref = run_meta.get("metrics_contract_level") or {}
    problems = []
    for cat, v in ref.items():
        mine = m.get(cat)
        if mine is None:
            problems.append("%s: fehlt in der Nachrechnung" % cat)
            continue
        for f in ("contracts", "detected", "flagged"):
            if mine[f] != v[f]:
                problems.append("%s.%s: %s statt %s" % (cat, f, mine[f], v[f]))
        for f in ("recall", "precision", "f1"):
            a, b = mine.get(f), v.get(f)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9):
                problems.append("%s.%s: %s statt %s" % (cat, f, a, b))
    for cat in m:
        if cat not in ref and cat not in ("_outside",):
            problems.append("%s: nicht in run_meta.json" % cat)
    return problems


def main(argv=None) -> int:
    """Kommandozeile: Ordner unter eval/ auswerten, Tabelle drucken, optional pruefen."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="Ordner unter eval/ mit findings.jsonl")
    ap.add_argument("--population",
                    help="per_contract-CSV mit allen Tasks des Laufs; Standard: "
                         "eval/per_contract/<ordnername>.csv")
    ap.add_argument("--check", action="store_true",
                    help="mit metrics_contract_level in run_meta.json vergleichen")
    args = ap.parse_args(argv)

    folder = pathlib.Path(args.folder)
    if not folder.is_absolute():
        folder = REPO / folder
    findings_path = folder / "findings.jsonl"
    if not findings_path.exists():
        print("keine findings.jsonl in %s" % folder, file=sys.stderr)
        return 2
    pop_path = pathlib.Path(args.population) if args.population \
        else REPO / "eval" / "per_contract" / (folder.name + ".csv")
    if not pop_path.is_absolute():
        pop_path = REPO / pop_path
    if not pop_path.exists():
        print("keine Grundgesamtheit: %s fehlt; --population angeben" % pop_path,
              file=sys.stderr)
        return 2

    m = metrics(load_population(pop_path), load_findings(findings_path))
    print(render(m, "%s (Grundgesamtheit: %s)" % (folder.name, pop_path.name)))

    if args.check:
        rm_path = folder / "run_meta.json"
        if not rm_path.exists():
            print("--check: keine run_meta.json in %s" % folder, file=sys.stderr)
            return 2
        problems = check_against_run_meta(m, json.loads(rm_path.read_text(encoding="utf-8")))
        if problems:
            print("\nAbweichungen von run_meta.json:")
            for p in problems:
                print("  " + p)
            return 1
        print("\nStimmt mit metrics_contract_level in run_meta.json ueberein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
