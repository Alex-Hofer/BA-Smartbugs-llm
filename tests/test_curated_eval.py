"""Regressionstests fuer analysis_tools/curated_eval.py.

Das Skript traegt den curated-Hauptlauf je Werkzeug nach ``eval/`` zusammen.
Es rechnet dabei nichts Neues aus, aber es liest an vier Stellen etwas aus
Rohdaten heraus, an denen ein stiller Fehler die versionierten Zahlen
verfaelschen wuerde:

* **Die Stellung der Entrypoint-Argumente.** Timeout und MAIN stehen an fester
  Position in ``docker.entrypoint``, und Slither hat ein Argument weniger als
  die beiden KI-Werkzeuge. Greift man daneben, landet ein Pfad im Feld ``main``
  und ``timeout_s`` bleibt leer -- beides faellt nicht auf, weil die Werte nur
  im ``run_meta.json`` stehen.
* **Der Zustand eines Tasks.** Ein Contract, der nicht uebersetzt wurde oder den
  Kontext gesprengt hat, darf nie als ``clean`` gelten. Sonst zaehlt ein nie
  analysierter Contract als unauffaellig.
* **Die Zaehlweise von Recall und Precision.** Sie muss der von
  ``evaluate_curated.py`` entsprechen, sonst weichen die versionierten Tabellen
  von der Konsolenausgabe ab, auf die sie sich berufen.
* **Felder, die ein Werkzeug nicht meldet.** Sie muessen ``null`` bleiben, und
  die Severity aus ``findings.yaml`` darf nie in der Spalte des Werkzeugurteils
  landen.

Alle Faelle hier sind ``synthetic``: ``smartbugs/results/`` ist git-ignoriert,
ein Test, der es braeuchte, schluege in einem frischen Klon aus dem falschen
Grund fehl.
"""

import importlib.util
import json
import os

import pytest

import conftest  # noqa: F401  -- legt REPO_ROOT und smartbugs/ auf sys.path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    path = os.path.join(REPO_ROOT, "analysis_tools", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ce = load("curated_eval")


# --------------------------------------------------------------------------- #
# Hilfen
# --------------------------------------------------------------------------- #

def write_task(root, category, contract, entrypoint, result, image="smartbugs/x:1.0"):
    """Ein Taskverzeichnis so anlegen, wie SmartBugs es hinterlaesst."""
    d = os.path.join(root, category, contract) if category else os.path.join(root, contract)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "smartbugs.json"), "w", encoding="utf-8") as fh:
        json.dump({"filename": os.path.join(category, contract),
                   "docker": {"entrypoint": entrypoint, "image": image,
                              "network": "bridge"},
                   "result": {"start": 1.0, "duration": 2.0, "exit_code": 0}}, fh)
    with open(os.path.join(d, "result.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    return d


GPTSCAN_ENTRY = ("'/sb/bin/do_solidity.sh' '/sb/x.sol' '1800' '/sb/bin' '0'")
SLITHER_ENTRY = ("'/sb/bin/do_solidity.sh' '/sb/x.sol' '600' '/sb/bin'")


# --------------------------------------------------------------------------- #
# Entrypoint-Argumente
# --------------------------------------------------------------------------- #

def test_timeout_and_main_are_read_from_their_own_positions_synthetic(tmp_path, monkeypatch):
    """Timeout ist das dritte Argument, MAIN das fuenfte -- nicht das dritte/siebte.

    Die naheliegende Zerlegung mit ``split("'")`` zaehlt die Trennzeichen mit und
    liefert an denselben Indizes den Dateinamen und das BIN-Verzeichnis.
    """
    run = tmp_path / "results" / "gptscan" / "curated_v1"
    write_task(str(run), "reentrancy", "a.sol", GPTSCAN_ENTRY,
               {"findings": [], "errors": [], "fails": [], "infos": []})
    monkeypatch.setattr(ce, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(ce, "ground_truth", lambda: {})

    task = ce.read_run("gptscan", "curated_v1")[0]
    assert task["timeout_s"] == 1800
    assert task["main"] == "0"


def test_slither_has_no_main_argument_and_main_stays_none_synthetic(tmp_path, monkeypatch):
    """Slithers Entrypoint kennt kein $MAIN; das Feld darf nicht geraten werden."""
    run = tmp_path / "results" / "slither-0.11.3" / "curated_v1"
    write_task(str(run), "reentrancy", "a.sol", SLITHER_ENTRY,
               {"findings": [], "errors": [], "fails": [], "infos": []})
    monkeypatch.setattr(ce, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(ce, "ground_truth", lambda: {})

    task = ce.read_run("slither-0.11.3", "curated_v1")[0]
    assert task["timeout_s"] == 600
    assert task["main"] is None


def test_tasks_are_found_below_the_category_folders_synthetic(tmp_path, monkeypatch):
    """Der curated-Lauf ist nach DASP-Kategorie sortiert, nicht flach.

    ``build_eval.read_run`` sucht mit ``*/`` und faende hier nur die
    Kategorieordner. Deshalb sucht dieses Skript in der Tiefe.
    """
    run = tmp_path / "results" / "gptscan" / "curated_v1"
    for cat, name in (("reentrancy", "a.sol"), ("arithmetic", "b.sol")):
        write_task(str(run), cat, name, GPTSCAN_ENTRY,
                   {"findings": [], "errors": [], "fails": [], "infos": []})
    monkeypatch.setattr(ce, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(ce, "ground_truth", lambda: {})

    tasks = ce.read_run("gptscan", "curated_v1")
    assert len(tasks) == 2
    assert {t["label_dir"] for t in tasks} == {"reentrancy", "arithmetic"}
    assert {t["contract_id"] for t in tasks} == {"a", "b"}


# --------------------------------------------------------------------------- #
# Zustaende
# --------------------------------------------------------------------------- #

def test_a_contract_that_did_not_compile_is_never_clean_synthetic():
    """``analysis degraded`` schlaegt den leeren Findingliste-Fall."""
    task = {"findings": [], "errors": [], "fails": [],
            "infos": ["GPTScan analysis degraded: the contract did not compile"]}
    assert ce.state_of("gptscan", task) == "degraded"


def test_an_empty_finding_list_without_a_marker_is_clean_synthetic():
    task = {"findings": [], "errors": [], "fails": [], "infos": []}
    assert ce.state_of("gptscan", task) == "clean"


def test_a_failed_task_outranks_a_degradation_marker_synthetic():
    task = {"findings": [], "errors": [], "fails": ["no tar archive"],
            "infos": ["GPTScan analysis degraded: the contract did not compile"]}
    assert ce.state_of("gptscan", task) == "failed"


def test_llmsmartaudit_uses_the_shared_state_rule_synthetic():
    """Der Kontextabbruch kommt aus build_eval und wird nicht nachgebaut."""
    task = {"findings": [], "errors": ["context window exceeded: the agent aborted"],
            "fails": [], "infos": []}
    assert ce.state_of("llmsmartaudit", task) == "context_exceeded"
    assert ce.state_of("llmsmartaudit", task) != "clean"


# --------------------------------------------------------------------------- #
# Kennzahlen
# --------------------------------------------------------------------------- #

def _task(labels, names):
    return {"labels": labels, "findings": [{"name": n} for n in names]}


def test_recall_counts_a_contract_once_however_often_it_is_flagged_synthetic():
    """Contract-Level: Mehrfachmeldungen desselben Contracts zaehlen einmal."""
    mapping = {"det_a": "reentrancy"}
    tasks = [_task(["reentrancy"], ["det_a", "det_a", "det_a"])]
    m = ce.metrics(tasks, mapping)
    assert m["reentrancy"]["detected"] == 1
    assert m["reentrancy"]["flagged"] == 1
    assert m["GESAMT"]["recall"] == 1.0


def test_findings_without_a_dasp_mapping_change_neither_recall_nor_precision_synthetic():
    mapping = {"det_a": "reentrancy", "det_ohne": None}
    ohne = ce.metrics([_task(["reentrancy"], ["det_a"])], mapping)
    mit = ce.metrics([_task(["reentrancy"], ["det_a", "det_ohne"])], mapping)
    assert ohne["GESAMT"] == mit["GESAMT"]


def test_a_category_that_was_never_flagged_has_no_precision_synthetic():
    """Keine Meldung heisst unbekannte Precision, nicht 0 %."""
    m = ce.metrics([_task(["other"], [])], {"det_a": "reentrancy"})
    assert m["other"]["recall"] == 0.0
    assert m["other"]["precision"] is None
    assert m["other"]["f1"] is None


def test_precision_counts_a_flag_on_an_unlabelled_contract_synthetic():
    """Eine Meldung ausserhalb des Labels druckt die Precision -- so ist sie definiert."""
    mapping = {"det_a": "reentrancy"}
    tasks = [_task(["reentrancy"], ["det_a"]), _task(["arithmetic"], ["det_a"])]
    m = ce.metrics(tasks, mapping)
    assert m["reentrancy"]["detected"] == 1
    assert m["reentrancy"]["flagged"] == 2
    assert m["reentrancy"]["precision"] == 0.5


def test_recall_requires_a_finding_in_the_labelled_category_synthetic():
    """Ein Treffer in einer anderen Kategorie erkennt das Label nicht.

    Mutationsprobe vom 24.09.2026: zaehlte jeder beliebige Treffer als
    erkannt, blieb die Suite gruen. Dieser Fall schliesst die Luecke.
    """
    mapping = {"det_ac": "access_control"}
    m = ce.metrics([_task(["reentrancy"], ["det_ac"])], mapping)
    assert m["reentrancy"]["detected"] == 0
    assert m["reentrancy"]["recall"] == 0.0
    assert m["access_control"]["flagged"] == 1
    assert m["access_control"]["detected"] == 0
    assert m["GESAMT"]["recall"] == 0.0


def test_wilson_interval_matches_the_textbook_value():
    """4 von 4 ergibt 0,51 bis 1,00; ohne Beobachtung gibt es kein Intervall."""
    assert ce.wilson(4, 4) == (0.51, 1.0)
    assert ce.wilson(0, 0) is None
    lo, hi = ce.wilson(50, 100)
    assert 0.40 < lo < 0.41 and 0.59 < hi < 0.60


def test_base_rate_is_the_share_of_labelled_contracts_synthetic():
    """Basisrate = Contracts mit Label / alle Contracts des Laufs."""
    mapping = {"det_a": "reentrancy"}
    tasks = [_task(["reentrancy"], ["det_a"]), _task(["arithmetic"], []),
             _task(["arithmetic"], []), _task(["reentrancy"], [])]
    m = ce.metrics(tasks, mapping)
    assert m["reentrancy"]["prevalence"] == 0.5
    assert m["arithmetic"]["prevalence"] == 0.5
    assert m["reentrancy"]["recall_ci95"] == ce.wilson(1, 2)
    assert m["GESAMT"]["prevalence"] is None


def test_the_unchecked_detectors_are_mapped_to_dasp_4():
    """Sonst zaehlt die groesste curated-Kategorie einen Teil ihrer Treffer nicht.

    SWC-104 heisst "Unchecked Call Return Value". In Slithers findings.yaml
    tragen genau die Detektoren, die das finden, keine Klassifikation --
    klassifiziert sind statt dessen `low-level-calls` (severity informational,
    meldet nur die Verwendung) und `unused-return`. Das Zusatz-Mapping in
    evaluate_curated.py schliesst die Luecke; dieser Test haelt sie geschlossen.
    """
    mapping = ce.evaluate_curated.load_mapping(
        ce.REPO / "smartbugs" / "tools" / "slither-0.11.3" / "findings.yaml",
        "slither-0.11.3")
    for detector in ("unchecked-lowlevel", "unchecked-send", "unchecked-transfer"):
        assert mapping[detector] == "unchecked_low_level_calls", detector
    # Der Anlass des Mappings: der schwaechere Stellvertreter war schon zugeordnet.
    assert mapping["low-level-calls"] == "unchecked_low_level_calls"
    # Die beiden aelteren Ergaenzungen bleiben unberuehrt.
    assert mapping["timestamp"] == "time_manipulation"
    assert mapping["weak-prng"] == "bad_randomness"


def test_the_mapping_comes_from_evaluate_curated_not_from_a_copy():
    """Eine eigene Kopie der DASP-Zuordnung liefe irgendwann auseinander."""
    import inspect
    assert ce.evaluate_curated.load_mapping is not None
    params = list(inspect.signature(ce.evaluate_curated.load_mapping).parameters)
    assert params == ["findings_yaml", "tool"]
    assert ce.evaluate_curated.DASP_TO_CATEGORY[1] == "reentrancy"


# --------------------------------------------------------------------------- #
# Findingzeilen
# --------------------------------------------------------------------------- #

def test_fields_the_tool_does_not_emit_stay_null_synthetic():
    """LLMSmartAudit meldet weder Position noch Severity -- eine 0 waere gelogen."""
    tasks = [{"contract_id": "a", "contract_file": "reentrancy/a.sol",
              "label_dir": "reentrancy", "labels": ["reentrancy"], "run_id": "r",
              "infos": ["LLMSmartAudit run: backend=deepseek/deepseek-v4-flash"],
              "findings": [{"name": "Reentrancy", "description": "..."}]}]
    tax = {"Reentrancy": {"severity": "high", "classification": "SWC-107, DASP-1"}}
    rows = ce.finding_rows("llmsmartaudit", tasks, tax, {"Reentrancy": "reentrancy"}, "t")

    row = rows[0]
    assert row["function"] is None and row["lines"] is None
    assert row["severity"] is None, "Severity des Werkzeugs, nicht die aus findings.yaml"
    assert row["severity_doc"] == "high"
    assert row["dasp10"] == "DASP-1"
    assert (row["provider"], row["model"]) == ("deepseek", "deepseek-v4-flash")


def test_slither_impact_lands_in_the_severity_column_synthetic():
    """Slither nennt seinen Schweregrad ``impact``; er ist ein echtes Urteil."""
    tasks = [{"contract_id": "a", "contract_file": "reentrancy/a.sol",
              "label_dir": "reentrancy", "labels": ["reentrancy"], "run_id": "r",
              "infos": [],
              "findings": [{"name": "reentrancy-eth", "impact": "High",
                            "confidence": "Medium", "line": 5, "line_end": 9,
                            "function": "withdraw", "message": "..."}]}]
    tax = {"reentrancy-eth": {"severity": "high", "classification": "SWC-107, DASP-1"}}
    rows = ce.finding_rows("slither-0.11.3", tasks, tax, {"reentrancy-eth": "reentrancy"}, "t")

    row = rows[0]
    assert row["severity"] == "High"
    assert row["confidence"] == "Medium"
    assert row["lines"] == {"start": 5, "end": 9}
    assert row["provider"] is None and row["model"] is None


def test_an_unknown_finding_name_keeps_its_raw_name_and_stays_unmapped_synthetic():
    """Ein Detektor ohne Eintrag darf nicht verschwinden -- er zaehlt als unmapped."""
    tasks = [{"contract_id": "a", "contract_file": "other/a.sol", "label_dir": "other",
              "labels": ["other"], "run_id": "r", "infos": [],
              "findings": [{"name": "neuer-detektor"}]}]
    rows = ce.finding_rows("slither-0.11.3", tasks, {}, {}, "t")

    assert len(rows) == 1
    assert rows[0]["category_raw"] == "neuer-detektor"
    assert rows[0]["dasp10"] == "" and rows[0]["dasp_category"] == ""
    assert rows[0]["severity_doc"] is None


# --------------------------------------------------------------------------- #
# Darstellung
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value,expected", [(None, "–"), (0.0, "0 %"), (1.0, "100 %")])
def test_a_missing_rate_is_a_dash_and_not_zero_percent(value, expected):
    assert ce.pct(value) == expected


def test_thousands_are_grouped_the_way_the_rest_of_the_repo_writes_them():
    assert ce.num(1124) == "1 124"
    assert ce.num(6) == "6"


# --------------------------------------------------------------------------- #
# Ground Truth fehlt
# --------------------------------------------------------------------------- #

def test_missing_ground_truth_aborts_instead_of_writing_empty_metrics_synthetic(tmp_path, monkeypatch):
    """Ohne smartbugs-curated/vulnerabilities.json bricht die Auswertung ab.

    In einem frischen Klon fehlt der git-ignorierte Datensatz. Liefe das Skript
    trotzdem durch, ueberschriebe es die versionierten eval/-Dateien mit
    Recall "-" und leeren Labels, ohne dass jemand es bemerkt.
    """
    monkeypatch.setattr(ce, "REPO", tmp_path)
    with pytest.raises(SystemExit) as exc:
        ce.ground_truth()
    assert "smartbugs-curated" in str(exc.value)
    assert "230e649" in str(exc.value)
