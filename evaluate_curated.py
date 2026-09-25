#!/usr/bin/env python3
"""Vergleicht die SmartBugs-Ergebnisse der KI-Scanner (gptscan, llmsmartaudit)
mit der Ground Truth des smartbugs-curated-Datensatzes.

Metrik: Contract-Level-Recall pro Kategorie — ein gelabelter Contract gilt als
erkannt, wenn das Tool mindestens ein Finding meldet, dessen DASP-Klassifikation
(aus tools/<tool>/findings.yaml) auf die gelabelte Kategorie abbildet.

Findings ohne SWC/DASP-Klassifikation (GPTScans Business-Logic-MWEs, LLMSAs
logic/DeFi- und code-quality-Detektoren) sind hier bewusst NICHT abbildbar und
werden separat als "unmapped" gezaehlt — fuer GPTScan ist geringer Recall auf
diesem Datensatz erwartbar (Scope: DeFi-Logik, nicht klassische SWC-Klassen).

Definition der Kennzahlen (alle auf Contract-Ebene, je Kategorie)
----------------------------------------------------------------
  contracts : Contracts, die in der Ground Truth mit dieser Kategorie gelabelt sind
  detected  : davon jene, fuer die das Tool mindestens ein auf diese Kategorie
              abbildbares Finding meldet
  flagged   : ALLE Contracts, fuer die das Tool diese Kategorie meldet — auch
              die ohne entsprechendes Label
  Recall    = detected / contracts
  Precision = detected / flagged
  F1        = harmonisches Mittel

Zwei Eigenheiten, die bei der Interpretation zu beachten sind:

* Mehrfachmeldungen desselben Contracts zaehlen einmal. Bei hoher Finding-Dichte
  (LLMSmartAudit: Mittel 7,9 Findings je Contract) ist Contract-Level-Recall
  daher wohlwollend — ein Tool, das viel meldet, trifft haeufiger zufaellig.
* Zeilengenau laesst sich nicht auswerten, weil LLMSmartAudit grundsaetzlich
  keine Zeilennummern emittiert (siehe tools/llmsmartaudit/parser.py).

Diese Auswertung liest ausschliesslich das Feld ``findings`` aus jeder
``result.json``. Errors und Fails werden hier NICHT betrachtet — dafuer ist
``analysis_tools/errors_fails_report.py`` zustaendig. Das ist der Grund, warum
die Parser-Reparatur vom 2026-08-02 die Zahlen unten nicht veraendert hat
(Beleg: docs/parser-fix-vorher-nachher.md).

Achtung bei der Interpretation: ein Contract ohne Findings ist nur dann
unauffaellig, wenn er auch uebersetzt werden konnte. Fuer den Hauptlauf
curated_v1_20260705 trifft das auf alle 143 Contracts zu; in anderen Laeufen
nicht (siehe docs/errors-fails.md, Spalte "nicht uebersetzt").

Ground Truth ist smartbugs-curated auf Commit 230e649 (16.06.2024);
run_curated.ps1 klont und pinnt genau diesen Stand.

Aufruf (aus dem Repo-Root; System-Python und SmartBugs-venv gehen beide,
sofern PyYAML installiert ist):
  python evaluate_curated.py --suffix v1_20260705
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

# Konservatives Zusatz-Mapping fuer Detektoren, deren findings.yaml-Eintrag
# KEINE Klassifikation traegt, deren DASP-Zuordnung aber kanonisch ist. In der
# BA als methodische Ergaenzung dokumentiert (BA-DURCHFUEHRUNGSPROTOKOLL.md,
# Fehler #9 und Nachtrag vom 20.09.2026).
#
# timestamp = SWC-116/DASP-8, weak-prng = SWC-120/DASP-6.
#
# Die drei unchecked-*-Detektoren kamen am 20.09.2026 dazu. SWC-104 heisst
# "Unchecked Call Return Value"; genau das finden sie. Klassifiziert waren in
# findings.yaml statt dessen nur low-level-calls (severity informational, meldet
# lediglich, DASS ein Low-Level-Call vorkommt) und unused-return -- die beiden
# schwaecheren Stellvertreter. Die Luecke traf ausgerechnet die groesste
# curated-Kategorie und liess die statische Baseline schlechter aussehen, als
# sie ist:
#   unchecked-lowlevel  54 Findings, severity medium
#   unchecked-send      34 Findings, severity medium
#   unchecked-transfer   3 Findings, severity high
EXTRA_MAPPING = {
    "slither-0.11.3": {
        "timestamp": "time_manipulation",
        "weak-prng": "bad_randomness",
        "unchecked-lowlevel": "unchecked_low_level_calls",
        "unchecked-send": "unchecked_low_level_calls",
        "unchecked-transfer": "unchecked_low_level_calls",
    },
}

# DASP-Top-10 -> Ordner-/Labelnamen des curated-Datensatzes
DASP_TO_CATEGORY = {
    1: "reentrancy",
    2: "access_control",
    3: "arithmetic",
    4: "unchecked_low_level_calls",
    5: "denial_of_service",
    6: "bad_randomness",
    7: "front_running",
    8: "time_manipulation",
    9: "short_addresses",
    10: "other",
}


def load_mapping(findings_yaml: Path, tool: str) -> dict:
    """Finding-Name -> curated-Kategorie (oder None, wenn keine DASP-Zuordnung)."""
    data = yaml.safe_load(findings_yaml.read_text(encoding="utf-8"))
    mapping = {}
    for name, entry in (data or {}).items():
        cls = (entry or {}).get("classification") or ""
        m = re.search(r"DASP-(\d+)", cls)
        mapping[name] = DASP_TO_CATEGORY.get(int(m.group(1))) if m else None
    for name, cat in EXTRA_MAPPING.get(tool, {}).items():
        if not mapping.get(name):
            mapping[name] = cat
    return mapping


def rates(contracts: int, detected: int, flagged: int):
    """Recall, Precision und F1 aus den drei Zaehlern einer Kategorie.

    ``None`` steht fuer "nicht definiert": Recall ohne gelabelte Contracts,
    Precision ohne geflaggte Contracts, F1 sobald eines von beiden fehlt oder
    beide 0 sind.
    """
    rec = detected / contracts if contracts else None
    prec = detected / flagged if flagged else None
    f1 = (2 * prec * rec / (prec + rec)
          if prec is not None and rec is not None and (prec + rec) else None)
    return rec, prec, f1


def evaluate_tool(tool: str, contracts: dict, resroot: Path, mapping: dict):
    """Zaehlt einen Lauf eines Werkzeugs gegen die Ground Truth aus.

    ``contracts`` bildet ``(kategorie-ordner, dateiname)`` auf die gelabelten
    Kategorien ab, ``resroot`` ist das Laufverzeichnis
    ``smartbugs/results/<tool>/curated_<suffix>``, ``mapping`` der Finding-Name
    zu curated-Kategorie (``load_mapping``).

    Rueckgabe: ``(per_cat, totals, densities, detail_rows)`` -- je Kategorie die
    Zaehler ``contracts``/``detected``/``flagged`` nach der Definition im
    Modulkopf, die Summen ueber den Lauf, die Findingzahl je ausgewertetem
    Contract und eine Zeile je Contract fuer die Detail-CSV. Contracts ohne
    ``result.json`` zaehlen als ``missing`` und nie als "nichts gefunden".
    """
    per_cat = defaultdict(lambda: {"contracts": 0, "detected": 0, "flagged": 0})
    totals = {"results": 0, "missing": 0, "findings": 0, "mapped": 0,
              "unmapped": 0, "extra_cat": 0}
    densities = []
    detail_rows = []

    for (folder, fname), labeled in sorted(contracts.items()):
        result_json = resroot / folder / fname / "result.json"
        for cat in labeled:
            per_cat[cat]["contracts"] += 1
        if not result_json.exists():
            totals["missing"] += 1
            continue
        totals["results"] += 1
        data = json.loads(result_json.read_text(encoding="utf-8"))
        findings = data.get("findings", [])
        totals["findings"] += len(findings)
        found_cats = set()
        for f in findings:
            cat = mapping.get(f.get("name"))
            if cat:
                totals["mapped"] += 1
                found_cats.add(cat)
            else:
                totals["unmapped"] += 1
        hit = False
        for cat in labeled:
            if cat in found_cats:
                per_cat[cat]["detected"] += 1
                hit = True
        for cat in found_cats:
            per_cat[cat]["flagged"] += 1
        totals["extra_cat"] += len(found_cats - set(labeled))
        densities.append(len(findings))
        detail_rows.append({
            "tool": tool, "category": folder, "contract": fname,
            "labeled": ";".join(labeled), "detected": int(hit),
            "n_findings": len(findings),
            "mapped_categories": ";".join(sorted(found_cats)),
        })
    return per_cat, totals, densities, detail_rows


def main() -> None:
    """Vergleicht je Werkzeug alle Ergebnisse eines Laufs mit der Ground Truth.

    Ablauf: Ground Truth laden -> je Werkzeug das findings.yaml-Mapping
    aufbauen -> jede result.json des Laufs lesen -> Findings auf
    curated-Kategorien abbilden -> je Kategorie Recall/Precision/F1 ausgeben.
    Fehlende result.json werden als ``missing`` gezaehlt und nicht als
    "nichts gefunden" gewertet.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".", help="BA-Repo-Root")
    ap.add_argument("--suffix", required=True, help="RunIdSuffix des Massenlaufs")
    ap.add_argument("--tools", nargs="+", default=["gptscan", "llmsmartaudit"])
    ap.add_argument("--csv", action="store_true",
                    help="Detail-CSV evaluation_curated_<suffix>.csv schreiben")
    args = ap.parse_args()
    repo = Path(args.repo)

    ground_truth = json.loads(
        (repo / "smartbugs-curated" / "vulnerabilities.json").read_text(encoding="utf-8")
    )
    # (kategorie-ordner, dateiname) -> gelabelte Kategorien
    contracts = {}
    for entry in ground_truth:
        p = Path(entry["path"])
        contracts[(p.parts[1], p.name)] = sorted({v["category"] for v in entry["vulnerabilities"]})

    detail_rows = []
    for tool in args.tools:
        mapping = load_mapping(repo / "smartbugs" / "tools" / tool / "findings.yaml", tool)
        resroot = repo / "smartbugs" / "results" / tool / f"curated_{args.suffix}"
        per_cat, totals, densities, rows = evaluate_tool(tool, contracts, resroot, mapping)
        detail_rows.extend(rows)

        print(f"\n## {tool} (curated_{args.suffix})")
        print(f"{'Kategorie':<28}{'Contracts':>10}{'Erkannt':>9}{'Recall':>9}"
              f"{'Geflaggt':>10}{'Precision':>11}{'F1':>7}")
        sum_c = sum_d = sum_f = 0
        for cat in sorted(per_cat):
            c, d, fl = (per_cat[cat]["contracts"], per_cat[cat]["detected"],
                        per_cat[cat]["flagged"])
            sum_c, sum_d, sum_f = sum_c + c, sum_d + d, sum_f + fl
            rec, prec, f1 = rates(c, d, fl)
            fmt = lambda v: f"{v:>.0%}" if v is not None else "-"
            print(f"{cat:<28}{c:>10}{d:>9}{fmt(rec):>9}{fl:>10}"
                  f"{fmt(prec):>11}{fmt(f1):>7}")
        rec = sum_d / sum_c if sum_c else 0
        prec = sum_d / sum_f if sum_f else None
        f1 = (2 * prec * rec / (prec + rec)
              if prec is not None and (prec + rec) else None)
        fmt = lambda v: f"{v:>.0%}" if v is not None else "-"
        print(f"{'GESAMT':<28}{sum_c:>10}{sum_d:>9}{fmt(rec):>9}{sum_f:>10}"
              f"{fmt(prec):>11}{fmt(f1):>7}")
        if densities:
            dens = sorted(densities)
            print(f"Finding-Dichte je Contract: Mittel "
                  f"{sum(dens) / len(dens):.1f}, Median {dens[len(dens) // 2]}, "
                  f"Max {dens[-1]}, Contracts ohne Findings: {dens.count(0)}")
        print(f"result.json: {totals['results']} (fehlend: {totals['missing']}) | "
              f"Findings: {totals['findings']} (DASP-mapped: {totals['mapped']}, "
              f"unmapped: {totals['unmapped']}) | Findings ausserhalb des Labels: "
              f"{totals['extra_cat']} Kategorie-Treffer")

    if args.csv and detail_rows:
        out = repo / f"evaluation_curated_{args.suffix}.csv"
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(detail_rows[0].keys()))
            writer.writeheader()
            writer.writerows(detail_rows)
        print(f"\nDetail-CSV: {out}")


if __name__ == "__main__":
    main()
