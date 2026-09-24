"""``smartbugs/tools/llmsmartaudit/mapping.md`` begruendet die Zuordnung der
41 LLMSmartAudit-Detektoren zu SWC/DASP. Die Begruendung darf der
maschinenlesbaren ``findings.yaml`` nicht davonlaufen: Jede Detektorzeile der
beiden Tabellen muss einen Eintrag in ``findings.yaml`` haben und dieselbe
Klassifikation tragen, und die im Text genannte Zaehlung (wie viele Detektoren
eine DASP-Nummer tragen) muss zur ``DASP_RE`` der Auswertung passen.
"""

import os
import re

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_DIR = os.path.join(REPO_ROOT, "smartbugs", "tools", "llmsmartaudit")
FINDINGS = os.path.join(TOOL_DIR, "findings.yaml")
MAPPING = os.path.join(TOOL_DIR, "mapping.md")

DASP_RE = re.compile(r"\bDASP-(\d+)\b")   # wie analysis_tools/curated_eval.py
ROW = re.compile(r"^\| `(?P<detector>\w+Detector)` \| (?P<name>[^|]+?) \| `(?P<cls>[^`]+)` \|")


@pytest.fixture(scope="module")
def findings():
    with open(FINDINGS, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return {entry["detector"]: (name, entry["classification"]) for name, entry in data.items()}


@pytest.fixture(scope="module")
def mapping_text():
    with open(MAPPING, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def mapping_rows(mapping_text):
    rows = {}
    for line in mapping_text.splitlines():
        m = ROW.match(line)
        if m:
            assert m.group("detector") not in rows, "Detektor doppelt: %s" % m.group("detector")
            rows[m.group("detector")] = (m.group("name").strip(), m.group("cls"))
    return rows


def test_findings_yaml_has_41_detectors(findings):
    assert len(findings) == 41


def test_every_detector_is_documented_exactly_once(findings, mapping_rows):
    assert set(mapping_rows) == set(findings)


def test_classification_matches_findings_yaml(findings, mapping_rows):
    for detector, (name, cls) in mapping_rows.items():
        yaml_name, yaml_cls = findings[detector]
        assert name == yaml_name, (detector, name, yaml_name)
        assert cls == yaml_cls, (detector, cls, yaml_cls)


def test_documented_counts_match_dasp_regex(findings, mapping_text, mapping_rows):
    with_dasp = {d for d, (_, cls) in findings.items() if DASP_RE.search(cls)}
    n = len(with_dasp)
    assert "%d der 41 Detektoren eine DASP-Nummer, %d keine" % (n, 41 - n) in mapping_text
    # Die erste Tabelle enthaelt genau die Detektoren mit DASP-Nummer, die zweite den Rest.
    first, second = mapping_text.split("## Die 26 Detektoren ohne DASP-Nummer", 1)
    in_first = {m.group("detector") for m in map(ROW.match, first.splitlines()) if m}
    in_second = {m.group("detector") for m in map(ROW.match, second.splitlines()) if m}
    assert in_first == with_dasp
    assert in_second == set(findings) - with_dasp
