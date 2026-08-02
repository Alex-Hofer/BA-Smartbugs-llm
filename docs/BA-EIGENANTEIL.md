# Eigenanteil und Änderungen an Fremdcode

Dieses Repository enthält drei fremde Codebasen (SmartBugs, GPTScan,
LLMSmartAuditTool) und den Eigenanteil dieser Bachelorarbeit. Dieses Dokument
sagt, welche Datei zu welcher Kategorie gehört — und wo eigener Code fremden
verändert, **was** geändert wurde und **warum**.

Die Aufstellung ist nicht geschätzt, sondern per Datei-Hash gegen die
Upstream-Stände abgeglichen (Stand 2026-08-02):

| Fremdkomponente | Upstream | Lizenz |
|---|---|---|
| SmartBugs | <https://github.com/smartbugs/smartbugs> | Apache-2.0 laut `smartbugs/LICENSE`, MIT laut `smartbugs/pyproject.toml` — Widerspruch im Upstream, beides permissiv |
| GPTScan | <https://github.com/GPTScan/GPTScan> | **AGPL-3.0** |
| LLMSmartAuditTool | <https://github.com/LLMAudit/LLMSmartAuditTool> | Apache-2.0 |

> Hinweis: `smartbugs/tools/llmsmartaudit/config.yaml` nannte ursprünglich
> `https://github.com/LLMSmartAudit/LLMSmartAuditTool` als `origin`. Diese URL
> existiert nicht; der korrekte Ort ist `LLMAudit/LLMSmartAuditTool`. Korrigiert.

---

## 1. Vollständig eigener Code

### Neu angelegte Verzeichnisse im Repo-Root

| Pfad | Inhalt |
|---|---|
| `analysis_tools/` | Auswertungswerkzeuge: Parser-Audit, Errors/Fails-Report, Rohlog-Zugriff, Redaktion, CSV-Vergleich |
| `tests/` | pytest-Regressionstests beider Parser samt Fixtures aus echten Altläufen |
| `corpus_tools/` | Rekonstruktion des `mwevariety`-Korpus (`build_fixed.py`), Laufanalyse (`analyze_run.py`) |
| `docs/` | Ausarbeitungen, Protokolle, Berichte |
| `run_curated.ps1` | Massenlauf-Runner über den curated-Datensatz |
| `evaluate_curated.py` | Recall/Precision/F1 gegen die Ground Truth |

### SmartBugs-Tool-Integrationen (eigene Ergänzungen im Fremdbaum)

`smartbugs/tools/gptscan/` und `smartbugs/tools/llmsmartaudit/` sind vollständig
selbst geschrieben, je vier Dateien nach dem SmartBugs-Schema:

| Datei | Aufgabe |
|---|---|
| `config.yaml` | Image, `output: /output.json`, **`network: bridge`** (SmartBugs setzt Tool-Container sonst auf `network: none`, was jeden API-Aufruf stillschweigend bricht), `env:`-Allowlist, Entrypoint |
| `scripts/do_solidity.sh` | Entrypoint im Container: Quellordner vorbereiten, Provider/Modell aus der Umgebung wählen, Tool starten, Metadatenzeile ausgeben, `/output.json` garantieren |
| `parser.py` | `parse(exit_code, log, output) -> (findings, infos, errors, fails)` |
| `findings.yaml` | Finding-Name → SWC/DASP-Klassifikation, Severity, Beschreibung |

### Eigener Code innerhalb der Fremdbäume

| Datei | Aufgabe |
|---|---|
| `GPTScan/src/llm_backend.py` | Provider-/Modell-Abstraktion, Preise, Kostenschätzung, `--dry-run`, Budget-Wächter |
| `GPTScan/src/report_md.py` | Markdown-Reportformatter (`--format md\|both`) |
| `GPTScan/Dockerfile`, `requirements-docker.txt`, `.dockerignore`, `.env.example` | Containerisierung ohne eingebackenen Schlüssel |
| `GPTScan/taxonomy/findings.yaml`, `taxonomy/mapping.md` | Abbildung der 10 MWE-Detektoren auf SWC/DASP mit Begründung |
| `GPTScan/docs/SMARTBUGS_INTEGRATION.md` | Integrationsdokumentation |
| `GPTScan/scripts/aggregate_smartbugs.py`, `prettify_sol.py` | Hilfsskripte |
| `LLMSmartAuditTool-main/.../chatdev/audit_report.py` | Sammelt die Ergebnisse aller 41 Detektor-Phasen und rendert einen standardisierten Report |
| `LLMSmartAuditTool-main/.../Dockerfile.smartbugs`, `.dockerignore` | Containerisierung für SmartBugs |
| `LLMSmartAuditTool-main/.../docs/coverage.md` | Welche Detektor-Kategorien `SmartContractTA` tatsächlich prüft |

---

## 2. Änderungen an Fremdcode

### 2.1 SmartBugs — genau eine Änderung

**`smartbugs/sb/docker.py`** (`__docker_args` und `execute`)

*Was:* Zwei Ergänzungen. Erstens werden Host-Umgebungsvariablen, die die
`config.yaml` des Werkzeugs unter `env:` auflistet, in den Container
durchgereicht. Zweitens werden dieselben Werte unmittelbar vor der Rückgabe
durch `<redacted>` ersetzt.

*Warum:* SmartBugs reicht keine Umgebungsvariablen in Tool-Container durch. Für
zwei LLM-gestützte Werkzeuge gibt es damit keinen Weg, den API-Schlüssel zur
Laufzeit zu übergeben, ohne ihn ins Image zu backen — was ihn in jeder Kopie
des Images verewigen würde. Die zweite Ergänzung ist nötig, weil die
Docker-Argumente wörtlich in jede `results/**/smartbugs.json` geschrieben
werden; ohne sie steht der Schlüssel im Klartext in den Messdaten. Beide
Stellen sind im Quelltext kommentiert.

*Nicht geändert:* Alles andere in `smartbugs/sb/`. Insbesondere
`parse_utils.py`, `parsing.py`, `results2csv.py` und `reparse.py` sind
unverändert — die Parser-Reparatur (siehe `docs/BA-ERRORS-VS-FAILS.md`) findet
ausschließlich in den eigenen Tool-Parsern statt, damit sie sich per
`python -m sb.reparse` auf Altläufe anwenden lässt und kein anderes der
30+ SmartBugs-Werkzeuge berührt.

### 2.2 GPTScan — 7 geänderte Dateien

38 Dateien sind unverändert, 22 neu (siehe oben), 7 geändert:

| Datei | Was | Warum |
|---|---|---|
| `src/tasks.py` | CLI-Optionen `--provider`, `--model`, `--dry-run`, `--format`; `-k/--gptkey` von *required* auf optional; `.env`-Laden über `python-dotenv` | GPTScan war fest auf OpenAI verdrahtet und verlangte den Schlüssel als Kommandozeilenargument — unter SmartBugs weder wählbar noch sicher übergebbar |
| `src/analyze_pipeline.py` | `ask_with_timeout()` zur zentralen Messstelle umgebaut: Token-/Call-Zählung, Budget-Wächter, `--dry-run`-Kurzschluss | Ohne eine einzige Messstelle gibt es keine belastbare Kostenaussage; die Zählung muss im Elternprozess liegen, damit sie unabhängig von der Multiprocessing-Startmethode funktioniert |
| `src/chatgpt_api.py` | Modellwahl und SDK-Konfiguration an `llm_backend` delegiert; Zähler für ausgeführte und wegen Budget übersprungene Calls | Die Modell-IDs `gpt-3.5-turbo`/`gpt-4` waren hart kodiert |
| `src/config.py` | `PROVIDERS`-Tabelle (Endpunkt, Schlüssel-Variable, Modell-Tiers, Preise), Budget-Grenzen | Provider und Preise gehören an eine Stelle, nicht verstreut in den Aufrufcode |
| `src/rich_utils.py` | Ein vergessenes `breakpoint()` entfernt und durch sichere Darstellung ersetzt | Der Debug-Haltepunkt blockiert jeden Lauf ohne Terminal — im Container also jeden Lauf |
| `requirements.txt` | `python-dotenv==1.0.1` ergänzt | Für das `.env`-Laden in `tasks.py` |
| `README.md` | Abschnitt zur Provider-/Modellwahl | Dokumentation der obigen Änderungen |

> **Lizenzhinweis:** GPTScan steht unter AGPL-3.0. Die obigen Änderungen sind
> Bearbeitungen im Sinne der Lizenz und bleiben AGPL-3.0, unabhängig von der
> MIT-Lizenz des übrigen Eigenanteils.

### 2.3 LLMSmartAuditTool — 9 geänderte Dateien

212 Dateien sind unverändert, 9 geändert:

| Datei | Was | Warum |
|---|---|---|
| `run.py` | Provider-/Modellwahl über `--provider`/`--model`, `--task-file`; Abbruch mit klarer Meldung statt stillem Fallback | Das Werkzeug war auf OpenAI festgelegt und las die Aufgabe interaktiv |
| `camel/model_backend.py` | `_resolve_model_id()` (Modell-ID aus `LLM_MODEL_ID` statt aus dem Enum), DeepSeek-Obergrenze von 8192 Completion-Tokens, Kontextfenster-Fallback | Das `ModelType`-Enum ist fest; ohne Entkopplung ist kein Modell wählbar, das nicht im Enum steht |
| `camel/typing.py` | `ModelType.DEEPSEEK_CHAT` und `ModelType.CUSTOM`; tiktoken-Encoding-Abbildung für Nicht-OpenAI-Modelle | `tiktoken` kennt nur OpenAI-Modelle und wirft sonst beim Token-Schätzen |
| `camel/utils.py` | Kontextfenster für die neuen Modelltypen (DeepSeek 65536, `CUSTOM` über `LLM_CONTEXT_TOKENS`) | Ohne Eintrag greift kein Truncation-Schutz |
| `chatdev/chat_chain.py` | Ruft `audit_report.reset()` zu Laufbeginn und `write_markdown()` am Ende auf | Anbindung des eigenen Report-Sammlers |
| `chatdev/phase.py` | Ruft `audit_report.record()` am Ende jeder Phase; reicht `model_type` an zwei Stellen durch | Jede Detektor-Phase überschreibt `env_dict['ideas']`, sodass ohne diesen Abgriff nur das Ergebnis des **letzten** Detektors überlebt |
| `chatdev/statistics.py` | DeepSeek-Preise in die Kostentabelle | Sonst werden DeepSeek-Läufe mit 0 bepreist |
| `CompanyConfig/SmartContractTA/ChatChainConfig.json` | Rolle „Security Testing Engineer" ergänzt | — |
| `requirements.txt` | `httpx<0.28` gepinnt | `openai 1.3.3` übergibt `proxies=` an `httpx.Client`; der Parameter ist in httpx 0.28 entfernt, der Aufruf schlägt sonst beim Import fehl |

### 2.4 Nicht als Änderung zählt

* `LLMSmartAuditTool-main/.../misc/*.png`: Im Upstream haben drei Dateinamen ein
  führendes Leerzeichen (`misc/ WordCloud.png`). Beim Bezug als ZIP-Archiv
  entfällt es. Inhaltlich identisch.
* `LLMSmartAuditTool-main/.../evaluation/` (27.662 Dateien, 3,7 GB) wurde
  **entfernt**. Zur Laufzeit nirgends referenziert — der Entrypoint startet
  `run.py --config SmartContractTA` aus `/app`. Das Image schrumpft dadurch von
  5,13 GB auf 590 MB. Extern gesichert, siehe `README.md`.
* `LLMSmartAuditTool-main/.../WareHouse/VaultDS*`: Reste eigener
  Integrationstests vom 2026-06-30. Bis auf einen Beispielreport entfernt;
  ebenfalls extern gesichert und über den Initial-Commit `f85946e` weiterhin
  aus der Historie herstellbar.
* `GPTScan/src/jars/*.jar` (19,9 MB + 18,9 MB): fremde Binärartefakte **ohne
  Bauanleitung im Repo** (kein `pom.xml`/`build.gradle`, nur zwei `.java`-Dateien
  im ganzen Baum). Sie werden zur Laufzeit per `java -jar` aufgerufen
  (`GPTScan/src/analyze_pipeline.py:529`,
  `GPTScan/src/antlr4helper/callgraph.py:145`) und sind nicht regenerierbar,
  bleiben also unangetastet.

---

## 3. Abgleich reproduzieren

```bash
git clone --depth 1 https://github.com/GPTScan/GPTScan.git /tmp/up-gptscan
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/LLMAudit/LLMSmartAuditTool.git /tmp/up-llmsa
git -C /tmp/up-llmsa sparse-checkout set --no-cone '/*' '!/evaluation'

diff -r -q --exclude=.git GPTScan /tmp/up-gptscan
diff -r -q --exclude=.git LLMSmartAuditTool-main/LLMSmartAuditTool-main /tmp/up-llmsa
```
