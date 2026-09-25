"""Tests fuer analysis_tools/metrics_from_eval.py: Kennzahlen aus versionierten Dateien.

Der wichtigste Test braucht keine Fixtures: Er rechnet Recall, Precision und F1
fuer die drei curated-Ordner unter eval/ aus findings.jsonl und der
per_contract-Tabelle nach und vergleicht mit den Werten, die curated_eval.py
aus den git-ignorierten Rohdaten in run_meta.json geschrieben hat. Weichen sie
ab, ist entweder die Nachrechnung falsch oder eine der versionierten Dateien
passt nicht mehr zu den anderen.
"""

import csv
import importlib.util
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "analysis_tools", "metrics_from_eval.py")
EVAL = os.path.join(REPO_ROOT, "eval")

spec = importlib.util.spec_from_file_location("metrics_from_eval", SCRIPT)
mfe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mfe)

CURATED = ("curated_v1_20260705__gptscan", "curated_v1_20260705__llmsmartaudit",
           "curated_v1_20260705__slither-0.11.3")


@pytest.mark.parametrize("folder", CURATED)
def test_versioned_files_reproduce_run_meta(folder):
    """Ohne Rohdaten dieselben Zaehler wie curated_eval.py mit Rohdaten."""
    fdir = os.path.join(EVAL, folder)
    pop = mfe.load_population(mfe.pathlib.Path(EVAL, "per_contract", folder + ".csv"))
    m = mfe.metrics(pop, mfe.load_findings(mfe.pathlib.Path(fdir, "findings.jsonl")))
    with open(os.path.join(fdir, "run_meta.json"), encoding="utf-8") as fh:
        run_meta = json.load(fh)
    assert mfe.check_against_run_meta(m, run_meta) == []
    assert m["_outside"] == 0
    assert m["GESAMT"]["contracts"] == 143


def test_cli_check_passes_for_llmsmartaudit(capsys):
    rc = mfe.main(["eval/curated_v1_20260705__llmsmartaudit", "--check"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "| **GESAMT** | **143** | **138** | **97 %** | **464** | **30 %** | **45 %** |" in out
    assert "Stimmt mit metrics_contract_level" in out


def test_second_run_uses_the_population_of_the_first(capsys):
    """llmsa_curated_v2 hat keine eigene per_contract-Tabelle (Rohdaten verloren)."""
    rc = mfe.main(["eval/llmsa_curated_v2",
                   "--population", "eval/per_contract/curated_v1_20260705__llmsmartaudit.csv"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "| **GESAMT** | **143** | **137** | **96 %** | **434** | **32 %** | **47 %** |" in out


def test_missing_population_is_reported(capsys):
    rc = mfe.main(["eval/llmsa_curated_v2"])
    assert rc == 2
    assert "Grundgesamtheit" in capsys.readouterr().err


def _write_population(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["task_dir", "contract_id"])
        w.writeheader()
        w.writerows(rows)


def test_synthetic_counts_and_mismatch_detection(tmp_path):
    """Erkannt nur bei passender Kategorie; ein vertauschter Zaehler faellt bei --check auf."""
    pop_csv = tmp_path / "pop.csv"
    _write_population(pop_csv, [
        {"task_dir": "reentrancy/a.sol", "contract_id": "a"},
        {"task_dir": "reentrancy/b.sol", "contract_id": "b"},
        {"task_dir": "access_control/c.sol", "contract_id": "c"},
    ])
    findings = [
        {"label_dir": "reentrancy", "contract_id": "a", "dasp_category": "reentrancy"},
        {"label_dir": "reentrancy", "contract_id": "a", "dasp_category": None},        # unmapped
        {"contract_file": "access_control\\c.sol", "contract_id": "c", "dasp10": "DASP-1"},  # build_eval-Form
        {"label_dir": "reentrancy", "contract_id": "zz", "dasp_category": "reentrancy"},   # ausserhalb
    ]
    m = mfe.metrics(mfe.load_population(pop_csv), findings)
    assert m["reentrancy"]["contracts"] == 2
    assert m["reentrancy"]["detected"] == 1          # nur a; b hat kein Finding
    assert m["reentrancy"]["flagged"] == 2           # a und c
    assert m["access_control"] == {"contracts": 1, "detected": 0, "flagged": 0,
                                   "recall": 0.0, "precision": None, "f1": None}
    assert m["GESAMT"]["recall"] == pytest.approx(1 / 3)
    assert m["GESAMT"]["precision"] == pytest.approx(1 / 2)
    assert m["_outside"] == 1

    ok = {"metrics_contract_level": {k: v for k, v in m.items() if k != "_outside"}}
    assert mfe.check_against_run_meta(m, ok) == []
    swapped = json.loads(json.dumps(ok))
    r = swapped["metrics_contract_level"]["reentrancy"]
    r["detected"], r["flagged"] = r["flagged"], r["detected"]   # 2/1 statt 1/2
    problems = mfe.check_against_run_meta(m, swapped)
    assert any(p.startswith("reentrancy.detected") for p in problems)
    assert any(p.startswith("reentrancy.flagged") for p in problems)
