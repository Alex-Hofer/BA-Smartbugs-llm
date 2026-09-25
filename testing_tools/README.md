# testing_tools/ — lokaler LLM-Prüfstand

Eigener Code dieser Arbeit. `fake_llm_endpoint.py` ist eine absichtlich
langsame, OpenAI-kompatible Attrappe eines Chat-Completions-Endpunkts. Sie
antwortet auf jede Anfrage mit derselben festen Antwort, nach einer
einstellbaren Verzögerung, und kostet nichts.

Wozu: Die Timeout-Mechanik (Arbeitspaket AP5, `docs/BA-AP5-ABSCHLUSSBERICHT.md`)
lässt sich gegen einen echten Anbieter nicht wiederholbar prüfen; Antwortzeiten
schwanken, und jeder Versuch kostet Geld. Gegen den Prüfstand lassen sich
Bremse (70 % der Frist) und Netz (90 %) gezielt auslösen. Dieselbe Attrappe
dient dem Modell-Wächter des LLMSmartAudit-Entrypoints als Gegenprobe.

## Aufruf

```powershell
python testing_tools\fake_llm_endpoint.py --port 8000 --delay 5
```

Optionen: `--host` (Standard `127.0.0.1`), `--port`, `--delay` (Sekunden je
Antwort), `--reply` (Antworttext). Aus einem SmartBugs-Lauf heraus erreicht man
den Prüfstand über den Provider `custom` und die Adresse
`http://host.docker.internal:8000/v1`; das vollständige Beispiel steht in der
README unter „Beispiel 3 — Test ohne Kosten gegen den lokalen Prüfstand“. Die
Umleitung ist auf den Provider `custom` beschränkt, ein bezahltes Backend lässt
sich nicht per Umgebungsvariable umlenken.

## Was der Prüfstand nicht ist

* Kein Modell: Die Antwort ist konstant und inhaltlich bedeutungslos. Findings,
  die ein Werkzeug daraus ableitet, sagen nichts über einen Contract.
* Kein Ersatz für einen Dry-Run: GPTScan hat mit `GPTSCAN_DRY_RUN=1` einen
  eigenen Modus ohne Netz; LLMSmartAudit hat keinen, dafür ist der Prüfstand der
  einzige kostenlose Weg.

Tests: `tests/test_fake_llm_endpoint.py` startet den Endpunkt und prüft
Antwortformat und Verzögerung; die Entrypoint-Tests unter `tests/` brauchen
ihn nicht, sie prüfen die Timeout-Marken mit Stubs.
