# tests/ — Regressionstests

```powershell
python -m pytest tests -q
```

Die Suite braucht kein Docker, keinen API-Schlüssel und keine Rohdaten unter
`smartbugs/results/`: Die Fixtures unter `tests/fixtures/` sind unveränderte
Ausschnitte echter Läufe, ihre Herkunft steht in `tests/fixtures/MANIFEST.json`.
Fälle, die in den aufgezeichneten Läufen nie auftraten (Timeout, leeres Archiv,
kaputtes JSON), sind synthetisch gebaut und tragen `synthetic` im Testnamen.
Dieselbe Suite läuft bei jedem Push als GitHub-Actions-Workflow
(`.github/workflows/tests.yml`). `tests/conftest.py` beschreibt, wie die
Parser geladen und die Fixtures aufgebaut werden.

## Welche Testdatei was prüft

| Testdatei | Geprüfter Code |
|---|---|
| `test_gptscan_parser.py` | `smartbugs/tools/gptscan/parser.py`: Findings, Zustände, Timeout-Marker, Kostenbremse, defekte Eingaben |
| `test_llmsmartaudit_parser.py`, `test_llmsa_exception_repair.py` | `smartbugs/tools/llmsmartaudit/parser.py`: Findings, Exit-Codes, Kontextgrenze, Teilberichte, Ausnahme-Reparatur |
| `test_entrypoint_timeout.py`, `test_entrypoint_main.py`, `test_entrypoint_model_guard.py` | beide `scripts/do_solidity.sh`: Timeout-Marken (AP5), `MAIN`-Verdrahtung (AP6), Modell-Wächter |
| `test_main_contract.py` | `scripts/main_contract.py` (Reduktion auf den Hauptcontract) und die Byte-Identität beider Kopien |
| `test_gptscan_deadline.py` | `GPTScan/src/llm_backend.py`: Deadline-Wächter, Endpunkt-Override, Kostenschätzung |
| `test_audit_report_partial.py` | `LLMSmartAuditTool-main/.../chatdev/audit_report.py`: Zwischenstand nach jeder Phase |
| `test_llmsa_context_limit.py` | `camel/utils.py`: Agentengrenze über `LLM_CONTEXT_TOKENS` |
| `test_docker_env_redaction.py`, `test_docker_cleanup.py` | die Eingriffe in `smartbugs/sb/docker.py`: Weitergabe und Redaktion der Umgebungsvariablen, Aufräumen mit Wiederholung |
| `test_build_eval.py`, `test_curated_eval.py`, `test_evaluate_curated.py`, `test_per_contract_stats.py`, `test_parser_audit.py`, `test_parser_audit_orphan_exception.py` | die Auswertungsskripte in `analysis_tools/` und `evaluate_curated.py`, darunter die Recall-/Precision-Zählung gegen synthetische Bäume |
| `test_metrics_from_eval.py` | `analysis_tools/metrics_from_eval.py`: Nachrechnung von Recall und Precision allein aus den versionierten `eval/`-Dateien, für alle drei Werkzeuge des curated-Laufs gegen `run_meta.json` |
| `test_tool_copies.py` | Byte-Identität der kopierten Werkzeugdateien: beide `mark_timeout.py`, `parser.py` und `findings.yaml` im Slither-glibc-Verzeichnis gegen das Upstream-Verzeichnis |
| `test_fake_llm_endpoint.py` | `testing_tools/fake_llm_endpoint.py` |
| `test_docs_links.py`, `test_docs_numbers.py`, `test_llmsa_mapping_doc.py` | die Dokumentation: relative Links, Tabelle 4.1 gegen `run_meta.json`, `mapping.md` gegen `findings.yaml` |

## Was nicht getestet ist

Ohne eigenen Test sind `analysis_tools/gptscan_eval.py`, `gptscan_run_stats.py`,
`errors_fails_report.py`, `compare_csv.py`, `redact_results.py`,
`secret_scan.py` und `rawlog.py`, die Skripte unter `corpus_tools/`, die vier
PowerShell-Runner, `scripts/mark_timeout.py` (in den Entrypoint-Tests nur
bereitgestellt, nicht ausgeführt), der Entrypoint, das Dockerfile und die
`config.yaml` im Slither-glibc-Verzeichnis, die beiden `config.yaml` der
KI-Integrationen, die `findings.yaml` von GPTScan (die von LLMSmartAudit prüft
`test_llmsa_mapping_doc.py` gegen `mapping.md`), `GPTScan/src/report_md.py`, die Hilfsskripte
`GPTScan/scripts/aggregate_smartbugs.py` und `prettify_sol.py`, die
Dockerfiles, der pre-commit-Hook und der CI-Workflow. Ihre Ausgaben sind
stattdessen über die eingecheckten Berichte nachprüfbar: `docs/errors-fails.md`,
`docs/parser-audit-nachher.md` und die Ordner unter `eval/` entstehen aus genau
diesen Skripten und reproduzieren bis auf den Zeitstempel
(`docs/BA-VERIFIKATIONSBERICHT-20260924.md`, Abschnitt 1; zuletzt am
25.09.2026 für alle Generatoren nachvollzogen).
