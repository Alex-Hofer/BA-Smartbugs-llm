"""Tests fuer evaluate_curated.py: die Contract-Level-Zaehlung gegen die Ground Truth.

Bisher war aus dieser Datei nur ``load_mapping`` getestet; die Recall- und
Precision-Rechnung lief ausschliesslich in ``main()`` gegen die echten,
git-ignorierten Rohdaten und die geklonte Ground Truth. Eine vertauschte Formel
waere unbemerkt geblieben. Hier laeuft dieselbe Rechnung gegen einen
synthetischen Ergebnisbaum, in dem jede Zahl von Hand nachzurechnen ist.

Die Zaehlweise steht im Modulkopf von ``evaluate_curated.py``: ein gelabelter
Contract gilt als erkannt, wenn mindestens ein Finding auf die gelabelte
Kategorie abbildet; ``flagged`` zaehlt alle Contracts, fuer die eine Kategorie
gemeldet wurde, auch die ohne passendes Label.
"""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import evaluate_curated as ec  # noqa: E402


def write_result(root, folder, fname, names):
    """Legt ``<root>/<folder>/<fname>/result.json`` mit Findings der Namen ``names`` an."""
    d = root / folder / fname
    d.mkdir(parents=True)
    d.joinpath("result.json").write_text(
        json.dumps({"findings": [{"name": n} for n in names]}), encoding="utf-8")


def test_rates_follow_the_definitions_in_the_module_header():
    rec, prec, f1 = ec.rates(1, 1, 2)
    assert (rec, prec) == (1.0, 0.5)
    assert f1 == pytest.approx(2 / 3)
    # Ohne gelabelte Contracts kein Recall, ohne geflaggte keine Precision.
    assert ec.rates(0, 0, 0) == (None, None, None)
    assert ec.rates(2, 0, 0) == (0.0, None, None)
    # Beide Raten 0: F1 ist nicht definiert, keine Division durch 0.
    assert ec.rates(2, 0, 3) == (0.0, 0.0, None)


def test_detected_requires_a_finding_in_the_labelled_category(tmp_path):
    contracts = {
        ("access_control", "b.sol"): ["access_control"],
        ("arithmetic", "c.sol"): ["arithmetic"],
        ("reentrancy", "a.sol"): ["reentrancy"],
    }
    mapping = {"reent": "reentrancy", "unmapped": None}
    write_result(tmp_path, "reentrancy", "a.sol", ["reent", "unmapped"])   # Treffer
    write_result(tmp_path, "access_control", "b.sol", ["reent"])           # falsche Kategorie
    # c.sol bekommt keine result.json: fehlend, nicht "sauber".

    per_cat, totals, densities, rows = ec.evaluate_tool("t", contracts, tmp_path, mapping)

    assert per_cat["reentrancy"] == {"contracts": 1, "detected": 1, "flagged": 2}
    assert per_cat["access_control"] == {"contracts": 1, "detected": 0, "flagged": 0}
    assert per_cat["arithmetic"] == {"contracts": 1, "detected": 0, "flagged": 0}
    assert totals == {"results": 2, "missing": 1, "findings": 3, "mapped": 2,
                      "unmapped": 1, "extra_cat": 1}
    assert densities == [1, 2]  # in Schluesselreihenfolge: b.sol, dann a.sol
    assert ec.rates(1, 1, 2)[:2] == (1.0, 0.5)  # Recall 100 %, Precision 50 %

    by_contract = {r["contract"]: r for r in rows}
    assert set(by_contract) == {"a.sol", "b.sol"}
    assert by_contract["a.sol"]["detected"] == 1
    assert by_contract["a.sol"]["mapped_categories"] == "reentrancy"
    assert by_contract["b.sol"]["detected"] == 0
    assert by_contract["b.sol"]["mapped_categories"] == "reentrancy"


def test_swapped_formula_would_be_caught():
    """Recall teilt durch gelabelte, Precision durch geflaggte Contracts.

    Mit 1 gelabelten, 1 erkannten und 4 geflaggten Contracts unterscheiden
    sich die beiden Groessen deutlich; eine Vertauschung faellt auf.
    """
    rec, prec, _ = ec.rates(1, 1, 4)
    assert rec == 1.0
    assert prec == 0.25


def test_main_end_to_end_on_a_synthetic_repo(tmp_path, capsys, monkeypatch):
    """Ground Truth, findings.yaml und Ergebnisbaum wie im echten Repository angeordnet."""
    repo = tmp_path
    (repo / "smartbugs-curated").mkdir()
    (repo / "smartbugs-curated" / "vulnerabilities.json").write_text(json.dumps([
        {"path": "dataset/reentrancy/a.sol", "vulnerabilities": [{"category": "reentrancy"}]},
        {"path": "dataset/access_control/b.sol", "vulnerabilities": [{"category": "access_control"}]},
    ]), encoding="utf-8")
    tooldir = repo / "smartbugs" / "tools" / "gptscan"
    tooldir.mkdir(parents=True)
    (tooldir / "findings.yaml").write_text(
        "reent:\n  classification: SWC-107 / DASP-1\n  severity: high\n", encoding="utf-8")
    root = repo / "smartbugs" / "results" / "gptscan" / "curated_x"
    write_result(root, "reentrancy", "a.sol", ["reent"])
    write_result(root, "access_control", "b.sol", ["reent"])

    monkeypatch.setattr(sys, "argv", ["evaluate_curated.py", "--repo", str(repo),
                                      "--suffix", "x", "--tools", "gptscan", "--csv"])
    ec.main()
    out = capsys.readouterr().out

    gesamt = next(l for l in out.splitlines() if l.startswith("GESAMT"))
    # Contracts, Erkannt, Recall, Geflaggt, Precision, F1
    assert gesamt.split() == ["GESAMT", "2", "1", "50%", "2", "50%", "50%"]
    reent = next(l for l in out.splitlines() if l.startswith("reentrancy"))
    assert reent.split() == ["reentrancy", "1", "1", "100%", "2", "50%", "67%"]
    assert "result.json: 2 (fehlend: 0)" in out

    csv_path = repo / "evaluation_curated_x.csv"
    assert csv_path.exists()
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "tool,category,contract,labeled,detected,n_findings,mapped_categories"
    assert len(lines) == 3
