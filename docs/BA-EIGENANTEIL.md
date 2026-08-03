# Eigenanteil und Änderungen an Fremdcode

Dieses Repository enthält drei fremde Codebasen (SmartBugs, GPTScan,
LLMSmartAuditTool) und den Eigenanteil dieser Bachelorarbeit. Dieses Dokument
sagt, welche Datei zu welcher Kategorie gehört — und wo eigener Code fremden
verändert, **was** geändert wurde und **warum**.

Die Aufstellung ist nicht geschätzt, sondern per Datei-Hash gegen die
Upstream-Stände abgeglichen. Gezählt wird ausschließlich, was git in diesem
Repository **trackt** — ignorierte oder ungetrackte Dateien erreichen den Leser
nicht und gehören daher in keine der Kategorien. Verglichene Upstream-Stände:

| Komponente | Stand |
|---|---|
| GPTScan | `29a1747` (`main`) |
| LLMSmartAuditTool | `c507fe4` (`main`) |
| SmartBugs | Tag `v2.1.1` = `01c0e66` |

| Fremdkomponente | Upstream | Lizenz |
|---|---|---|
| SmartBugs | <https://github.com/smartbugs/smartbugs> | Apache-2.0 laut `smartbugs/LICENSE`, MIT laut `smartbugs/pyproject.toml` — Widerspruch im Upstream, beides permissiv |
| GPTScan | <https://github.com/GPTScan/GPTScan> | **AGPL-3.0** |
| LLMSmartAuditTool | <https://github.com/LLMAudit/LLMSmartAuditTool> | Apache-2.0 |

> Hinweis: `smartbugs/tools/llmsmartaudit/config.yaml` nannte ursprünglich
> `https://github.com/LLMSmartAudit/LLMSmartAuditTool` als `origin`. Diese URL
> existiert nicht; der korrekte Ort ist `LLMAudit/LLMSmartAuditTool`. Korrigiert.

---

## 1. Eigener Code (nicht ganz vollständig noch)

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

> **Zur Abgrenzung:** Von den 21 gegenüber dem Upstream neuen Dateien im
> GPTScan-Baum sind 11 eigener Code bzw. eigene Dokumentation (die Tabelle
> oben). Die übrigen 10 liegen unter `GPTScan/reports/` und sind **generierte
> Auswertungen eigener Läufe** (CSV/HTML/PDF/Markdown), kein Werkzeugcode. Sie
> werden hier ausgewiesen, weil sie in der Dateizählung als „neu" erscheinen.

---

## 2. Änderungen an Fremdcode

### 2.1 SmartBugs — 5 geänderte Dateien in `sb/`, dazu `.gitignore`

Gegen den Upstream-Tag `v2.1.1` unterscheiden sich fünf Dateien in `sb/`. Zwei
davon bilden zusammen den Mechanismus zur Schlüsselübergabe; drei sind kleinere
Eingriffe. Hinzu kommt eine Korrektur an `smartbugs/.gitignore` (unten).

#### Der Schlüssel-Mechanismus (zwei Dateien, funktional untrennbar)

**`smartbugs/sb/tools.py`** (`FIELDS`, `class Tool`)

*Was:* Das Feld `env` wird in das `FIELDS`-Tupel und in die `Tool`-Dataclass
aufgenommen — eine kommaseparierte Liste von Namen von Host-Umgebungsvariablen.

*Warum:* SmartBugs liest nur Felder aus einer `config.yaml`, die in `FIELDS`
stehen. Ohne diesen Patch würde das `env:` in `tools/gptscan/config.yaml` und
`tools/llmsmartaudit/config.yaml` schlicht ignoriert, und der Patch in
`docker.py` liefe ins Leere.

**`smartbugs/sb/docker.py`** (`__docker_args` und `execute`)

*Was:* Zwei Ergänzungen. Erstens werden die unter `env:` aufgelisteten
Host-Umgebungsvariablen in den Container durchgereicht. Zweitens werden
dieselben Werte unmittelbar vor der Rückgabe durch `<redacted>` ersetzt.

*Warum:* SmartBugs reicht keine Umgebungsvariablen in Tool-Container durch. Für
zwei LLM-gestützte Werkzeuge gibt es damit keinen Weg, den API-Schlüssel zur
Laufzeit zu übergeben, ohne ihn ins Image zu backen — was ihn in jeder Kopie
des Images verewigen würde. Die zweite Ergänzung ist nötig, weil die
Docker-Argumente wörtlich in jede `results/**/smartbugs.json` geschrieben
werden; ohne sie steht der Schlüssel im Klartext in den Messdaten. Beide
Stellen sind im Quelltext kommentiert.

> **Markierung im Quelltext.** Sämtliche eigenen Eingriffe in den vier
> inhaltlich geänderten SmartBugs-Dateien sind in nummerierte Marker
> eingefasst — `# --- BA MODIFICATION <n>: BEGIN ---` bis
> `# --- BA MODIFICATION <n>: END ---`. `grep -rn "BA MODIFICATION" smartbugs/sb`
> listet alle auf; ein Kopfkommentar in `docker.py` erklärt die Konvention.
>
> | Datei | Blöcke |
> |---|---:|
> | `sb/docker.py` | 5 |
> | `sb/tools.py` | 2 |
> | `sb/analysis.py` | 2 |
> | `sb/solidity.py` | 1 |
>
> Wo ein Block Upstream-Code **ersetzt** statt nur ergänzt, steht die ersetzte
> Fassung wörtlich als Kommentar im Block, eingeleitet mit „restore it to undo
> this block". Das Rückgängigmachen ist damit rein mechanisch: Block löschen,
> zitierte Zeilen einsetzen.
>
> Nachgeprüft: Ein Skript entfernt alle zehn Blöcke, setzt die zitierten Zeilen
> ein und vergleicht mit dem Upstream `v2.1.1` — alle vier Dateien stimmen
> danach überein (bis auf Leerzeilen) und übersetzen weiterhin. Es ist also
> weder eigener Code unmarkiert geblieben noch fremder versehentlich
> mitmarkiert.

#### Aufräumen der Task-Verzeichnisse unter Windows (dieselbe Datei)

**`smartbugs/sb/docker.py`** (`rmtree_retry`, aufgerufen in `execute`)

*Was:* Das abschließende `shutil.rmtree(sbdir)` im `finally`-Block von
`execute` ist durch `rmtree_retry` ersetzt — dasselbe Löschen, aber mit
Wiederholung und kurzem Backoff. Bleibt das Verzeichnis dauerhaft gesperrt,
wird das über `sb.debug.log` gemeldet, statt eine Ausnahme zu werfen.

*Warum:* SmartBugs mountet je Task ein Temp-Verzeichnis in den Container und
löscht es unmittelbar nach `container.remove()`. Unter Docker Desktop ist das
Handle auf die gerade im Container ausgeführten Dateien dann noch offen;
`os.rmdir` auf das bereits geleerte `bin` scheitert mit `WinError 5`. Der
entstehende `PermissionError` ist kein `SmartBugsError` und wird deshalb von
der Wiederholungsschleife in `sb/analysis.py` nicht aufgefangen: Er entkommt
aus dem `finally`-Block und beendet den Worker-Prozess, **bevor**
`result.json`, `result.log` und `smartbugs.json` geschrieben werden. Der
Hauptprozess bemerkt nichts und endet mit Status 0 — der Ergebnisverlust ist
vollständig und lautlos. Beobachtet am 2026-08-02 mit Docker Desktop Server
29.0.1, reproduzierbar in allen vier Worker-Prozessen; hergeleitet und belegt
in `BA-DEMOLAUF-ERGEBNIS.md`, Abschnitt 2.

Abgesichert durch `tests/test_docker_cleanup.py` (normaler Fall,
vorübergehende Sperre, dauerhafte Sperre).

#### Zwei kleinere Eingriffe und ein Formatter-Artefakt

| Datei | Was | Warum |
|---|---|---|
| `sb/solidity.py` | `CONTRACT_NAMES`: `([A-Za-z0-9_]*)` → `([a-zA-Z$_][a-zA-Z0-9$_]*)` | Das Upstream-Muster akzeptiert einen mit einer Ziffer beginnenden Namen und kennt `$` nicht, das in Solidity-Bezeichnern zulässig ist. Betrifft, welche Contract-Namen SmartBugs in einer Datei findet |
| `sb/analysis.py` | `os.makedirs(task.rdir)` in `try/except` gekapselt; das `time.sleep` zwischen den Wiederholungen aus dem Schleifenrumpf in den `except`-Zweig verschoben | Schlägt `makedirs` fehl, greift die unmittelbar folgende `isdir`-Prüfung und wirft SmartBugs' eigenen `SmartBugsError` mit klarer Meldung statt eines rohen `OSError`. Die Verschiebung des `sleep` ist eine Umstellung ohne Verhaltensänderung |
| `sb/io.py` | `return(x)` → `return x`, ein Kommentar-Leerzeichen | **Kein eigener Eingriff, sondern ein Formatter-Artefakt** — siehe Hinweis unter der Tabelle |
| `smartbugs/.gitignore` | Muster `results*` an das Verzeichnis der Datei geankert: `/results*` | Ohne Anker traf das Muster jeden Pfad, der mit „results" beginnt — und schloss damit **sechs Upstream-Dateien** von der Versionierung aus (siehe unten). `smartbugs/results/` bleibt unverändert ignoriert |

> **`sb/io.py` zählt nicht als Eigenanteil.** Die beiden Abweichungen sind
> exakt das, was `black` erzeugt — und `black` mit `line-length = 100` ist in
> SmartBugs' eigener `pyproject.toml` konfiguriert. Nachgeprüft: Lässt man
> `black --line-length 100` auf die Upstream-Fassung von `sb/io.py` los,
> entsteht **byte-identisch** die hier vorliegende Datei. Dieselbe Probe an
> `tools.py`, `solidity.py`, `analysis.py` und `docker.py` schlägt fehl — deren
> Änderungen sind inhaltlich und bleiben nach einem `black`-Lauf bestehen.
> `io.py` ist damit ein Nebenprodukt eines Formatter-Laufs, keine
> Programmierleistung, und wird hier nur der Vollständigkeit halber geführt.

Die sechs durch die `.gitignore`-Korrektur zurückgewonnenen Dateien sind
sämtlich **byte-identisch zum Upstream** und ab sofort versioniert:

| Datei | Bedeutung |
|---|---|
| `sb/results2csv.py` | Quelldatei. `README.md` schreibt `python -m sb.results2csv results` als Arbeitsschritt vor — in einem frischen Klon fehlte sie, der Ablauf war nicht durchführbar |
| `templates/results.sql` | SQL-Schema für die Ergebnisausgabe |
| `.github.off/results-ubuntu-{hx,rt,sol}.csv`, `.github.off/old/results-ubuntu.csv` | Referenzergebnisse der (upstream selbst deaktivierten) CI |

*Nicht geändert:* Die übrigen 18 Dateien in `smartbugs/sb/`. Insbesondere
`parse_utils.py`, `parsing.py`, `results2csv.py` und `reparse.py` sind
unverändert — die Parser-Reparatur (siehe `docs/BA-ERRORS-VS-FAILS.md`) findet
ausschließlich in den eigenen Tool-Parsern statt, damit sie sich per
`python -m sb.reparse` auf Altläufe anwenden lässt und kein anderes der
30+ SmartBugs-Werkzeuge berührt.

### 2.2 GPTScan — 7 geänderte Dateien

Von den 66 getrackten Dateien sind 38 unverändert, 21 neu (siehe oben) und
7 geändert; die Summe ergibt genau die 66:

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

Von den 235 getrackten Dateien sind 212 unverändert, 14 neu und 9 geändert;
die Summe ergibt genau die 235. Von den 14 neuen sind nur 4 eigener Code
(`chatdev/audit_report.py`, `Dockerfile.smartbugs`, `.dockerignore`,
`docs/coverage.md`); die übrigen 10 sind die drei umbenannten `misc/*.png`
und der aufbewahrte Beispielreport unter `WareHouse/VaultDS5_sb_20260630223101/`
(siehe 2.4):

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
git clone https://github.com/GPTScan/GPTScan.git /tmp/up-gptscan
git -C /tmp/up-gptscan checkout 29a1747

git clone --filter=blob:none --sparse \
    https://github.com/LLMAudit/LLMSmartAuditTool.git /tmp/up-llmsa
# ohne --sparse und den evaluation-Ausschluss werden 3,7 GB geladen
git -C /tmp/up-llmsa sparse-checkout set --no-cone '/*' '!/evaluation'
git -C /tmp/up-llmsa checkout c507fe4

git clone --depth 1 --branch v2.1.1 \
    https://github.com/smartbugs/smartbugs.git /tmp/up-smartbugs

diff -r -q --exclude=.git GPTScan /tmp/up-gptscan
diff -r -q --exclude=.git LLMSmartAuditTool-main/LLMSmartAuditTool-main /tmp/up-llmsa
diff -r -q --exclude=.git smartbugs/sb /tmp/up-smartbugs/sb
```

In Git Bash unter Windows braucht das sparse-checkout-Muster
`MSYS_NO_PATHCONV=1`, sonst wandelt MSYS das führende `/` in einen
Windows-Pfad um.

`diff -r` vergleicht den Arbeitsbaum und zeigt damit auch ungetrackte Dateien
an. Für die Zählung oben ist `git ls-files` maßgeblich.
