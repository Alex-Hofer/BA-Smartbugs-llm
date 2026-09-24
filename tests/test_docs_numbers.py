"""Die Kennzahlen der Tabelle 4.1 in ``docs/BA-WERKZEUGE-IM-VERGLEICH.md``
muessen mit ``eval/curated_v1_20260705__<werkzeug>/run_meta.json``
uebereinstimmen.

Die Tabelle wird von Hand gepflegt, ``run_meta.json`` erzeugt
``analysis_tools/curated_eval.py`` aus den Rohdaten. Weicht beides voneinander
ab, ist entweder die Tabelle veraltet oder die Auswertung hat sich bewegt --
beides soll auffallen, bevor es jemand liest.
"""

import json
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(REPO_ROOT, "docs", "BA-WERKZEUGE-IM-VERGLEICH.md")
RUN = "curated_v1_20260705"
TOOLS = ("gptscan", "llmsmartaudit", "slither-0.11.3")   # Spaltenreihenfolge der Tabelle


def _pct(v):
    return round(100 * (v or 0))


ROWS = {
    "Findings gesamt": lambda m: m["findings_total"],
    "davon DASP-zugeordnet": lambda m: m["findings_dasp_mapped"],
    "Recall": lambda m: _pct(m["metrics_contract_level"]["GESAMT"]["recall"]),
    "Precision": lambda m: _pct(m["metrics_contract_level"]["GESAMT"]["precision"]),
    "LLM-Aufrufe": lambda m: (m["tokens"] or {}).get("llm_calls", 0),
    "Kosten gesamt": lambda m: m["cost_usd"],
}


def section_41():
    with open(DOC, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("### 4.1"))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("### 4.2"))
    return lines[start:end]


def table_row(label):
    for line in section_41():
        cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == label:
            return cells[1:4]
    raise AssertionError("Zeile %r fehlt in Tabelle 4.1" % label)


def number(cell):
    for ch in (" ", " ", "\xa0", " ", "$", "%"):
        cell = cell.replace(ch, "")
    return float(cell.replace(",", "."))


def run_meta(tool):
    path = os.path.join(REPO_ROOT, "eval", "%s__%s" % (RUN, tool), "run_meta.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.mark.parametrize("label", sorted(ROWS))
def test_table_41_matches_run_meta(label):
    cells = table_row(label)
    assert len(cells) == 3, cells
    for tool, cell in zip(TOOLS, cells):
        expected = ROWS[label](run_meta(tool))
        assert number(cell) == pytest.approx(expected, abs=0.005), (tool, label, cell, expected)
