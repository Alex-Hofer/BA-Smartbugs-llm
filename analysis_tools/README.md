# analysis_tools/ — Auswertungswerkzeuge

Eigener Code dieser Arbeit (kein SmartBugs-Upstream). Alle Skripte lesen die
Rohergebnisse unter `smartbugs/results/<werkzeug>/<runid>/` und schreiben
abgeleitete Dateien nach `eval/` oder `docs/`; keines setzt einen LLM- oder
Docker-Aufruf ab. Einzige schreibende Ausnahme auf den Rohdaten ist
`redact_results.py`, das API-Schlüssel aus alten Task-Logs entfernt.

Voraussetzungen: System-Python 3.11 oder neuer mit `pyyaml` und `pytest`
(`python -m pip install -r requirements-dev.txt`, siehe README „Umgebung
anlegen“). Aufruf immer aus dem Repository-Wurzelverzeichnis.

## Die Skripte

| Skript | Wozu | Liest | Schreibt | Aufruf |
|---|---|---|---|---|
| `curated_eval.py` | Auswertung des curated-Hauptlaufs für alle drei Werkzeuge: Findings, Zustände, Recall/Precision/F1 je DASP-Kategorie mit Basisrate und Wilson-Intervall | `smartbugs/results/<tool>/curated_v1_20260705/`, `smartbugs-curated/vulnerabilities.json`, `smartbugs/tools/<tool>/findings.yaml` | `eval/curated_v1_20260705__<tool>/` (`findings.jsonl`, `run_meta.json`, `summary.md`, `README.md`), `eval/curated_v1_20260705__metriken.md` | `python analysis_tools\curated_eval.py` |
| `build_eval.py` | Auswertung eines LLMSmartAudit-Laufs: Findings mit DASP-Zuordnung, Zustände (auch `context_exceeded`), Token, Kosten, Laufparameter aus `smartbugs.json` und Runner-Protokoll | `smartbugs/results/llmsmartaudit/<runid>/`, `eval/_runlogs/*.log` | `eval/<runid>/` | `python analysis_tools\build_eval.py <runid> [--merge-run <runid>]` |
| `gptscan_eval.py` | Auswertung eines GPTScan-Laufs samt Vergleich gegen den Referenzlauf `curated_mwefixed_live`; schreibt außerdem `eval/README.md` neu | `smartbugs/results/gptscan/<runid>/`, `eval/<runid>/run_params.json` (falls vorhanden) | `eval/<runid>/`, `eval/README.md` | `python analysis_tools\gptscan_eval.py <runid> [--merge-run <runid>] [--no-compare]` |
| `metrics_from_eval.py` | Recall/Precision/F1 je Kategorie **ohne Rohdaten**, allein aus `findings.jsonl` und der per_contract-Tabelle eines Ordners; `--check` vergleicht mit `run_meta.json` | `eval/<ordner>/findings.jsonl`, `eval/per_contract/<ordner>.csv` | Konsole | `python analysis_tools\metrics_from_eval.py eval\curated_v1_20260705__llmsmartaudit --check` |
| `per_contract_stats.py` | eine Zeile je Contract (Zustand, Findings, Laufzeit, Token, Kosten, GPTScan-Stufen bzw. LLMSmartAudit-Phasen) | Rohergebnisse eines Laufs | `eval/per_contract/<runid>__<tool>.csv` (+ `__phases.csv` bei LLMSmartAudit) | `python analysis_tools\per_contract_stats.py <tool> <runid> [--merge-run <runid>] [--out-dir <pfad>]` |
| `gptscan_run_stats.py` | Token-, Kosten- und Laufzeitkennzahlen eines GPTScan-Laufs aus den `GPTSCAN_META`-Zeilen, für die Runner | `result.log` je Task | Konsole | `python analysis_tools\gptscan_run_stats.py <runid>` |
| `errors_fails_report.py` | Bilanz `errors` gegen `fails` je Lauf und Werkzeug, mit jeder Meldung im Wortlaut | `result.json` aller Läufe | `docs/errors-fails.md`, `docs/errors-fails.csv` | `python analysis_tools\errors_fails_report.py --md docs\errors-fails.md --csv docs\errors-fails.csv` |
| `parser_audit.py` | prüft, ob Rohsignal (Tracebacks, Fehlerzeilen, Marker) auf dem Weg vom Container in `result.json` verlorengeht | `result.log`, `result.tar`, `result.json` aller Läufe | `docs/parser-audit-nachher.md` (und `.csv`, git-ignoriert) | `python analysis_tools\parser_audit.py` |
| `compare_csv.py` | Vorher/Nachher-Vergleich zweier `sb.results2csv`-Exporte, etwa vor und nach einer Parser-Änderung | zwei CSV-Dateien | Konsole (`docs/parser-fix-vorher-nachher.md` ist eine solche Ausgabe) | `python analysis_tools\compare_csv.py <vorher.csv> <nachher.csv>` |
| `redact_results.py` | entfernt API-Schlüssel aus Task-Logs, die vor der Redaktion in `sb/docker.py` entstanden sind; verweigert, wenn sich mehr als der Schlüsselwert ändern würde | Task-Logs | dieselben Task-Logs | `python analysis_tools\redact_results.py` (siehe Kopfkommentar) |
| `secret_scan.py` | verhindert, dass ein Schlüssel in einen Commit gelangt; läuft als pre-commit-Hook und in der CI | gestagte Dateien oder der ganze Arbeitsbaum, Archive entpackt | Exit-Code, Fundstellen ohne Wert | `python analysis_tools\secret_scan.py [--all] [--install]` |
| `rawlog.py` | gemeinsame Lesefunktionen für `result.log`, `result.tar` und `rich`-formatierte Logs; wird von `parser_audit.py`, `errors_fails_report.py` und `redact_results.py` importiert | – | – | Bibliothek, kein eigener Aufruf |
| `__init__.py` | macht das Verzeichnis importierbar; Modultabelle im Docstring | – | – | – |

Die Auswertungen unter `eval/` sind bis auf Zeitstempel reproduzierbar: Ein
erneuter Lauf von `curated_eval.py`, `errors_fails_report.py` und
`parser_audit.py` erzeugt die eingecheckten Dateien inhaltsgleich
(`docs/BA-VERIFIKATIONSBERICHT-20260924.md`, Abschnitt 1).

## Wo die Zählweise steht

* Recall, Precision, F1 (Contract-Level, je DASP-Kategorie): Kopf von
  `evaluate_curated.py` im Wurzelverzeichnis; `curated_eval.py` rechnet
  identisch und wird darauf getestet (`tests/test_curated_eval.py`,
  `tests/test_evaluate_curated.py`).
* Zustände (`findings`, `clean`, `degraded`, `context_exceeded`, `failed`) und
  die Trennung `errors` gegen `fails`: `docs/BA-ERRORS-VS-FAILS.md`.
* DASP-Zuordnung je Finding-Name: `smartbugs/tools/<tool>/findings.yaml`, für
  LLMSmartAudit begründet in `smartbugs/tools/llmsmartaudit/mapping.md`; fünf
  Zusatz-Zuordnungen für Slither in `evaluate_curated.py` (`EXTRA_MAPPING`).

## Tests

`python -m pytest tests -q` prüft `build_eval.py`, `curated_eval.py`,
`per_contract_stats.py` und `parser_audit.py` gegen aufgezeichnete Rohdaten
unter `tests/fixtures/`. Ohne Test sind `gptscan_eval.py`,
`gptscan_run_stats.py`, `errors_fails_report.py`, `compare_csv.py`,
`redact_results.py`, `secret_scan.py` und `rawlog.py`; ihre Ausgaben sind
stattdessen über die eingecheckten Berichte nachprüfbar (`tests/README.md`).
