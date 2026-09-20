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
| `tests/` | pytest-Regressionstests beider Parser und, seit AP5, der Timeout-Mechanik (Deadline-Wächter, Zwischenstand, Entrypoint-Marken) samt Fixtures aus echten Altläufen und synthetischem Material |
| `corpus_tools/` | Rekonstruktion des `mwevariety`-Korpus (`build_fixed.py`), Laufanalyse (`analyze_run.py`) |
| `testing_tools/` | *(AP5)* Lokaler, OpenAI-kompatibler Prüfstand-Endpunkt (`fake_llm_endpoint.py`), der Timeout-Pfade ohne echte API-Kosten und deterministisch auslösbar macht |
| `docs/` | Ausarbeitungen, Protokolle, Berichte |
| `run_curated.ps1` | Massenlauf-Runner über den curated-Datensatz |
| `evaluate_curated.py` | Recall/Precision/F1 gegen die Ground Truth |

### SmartBugs-Tool-Integrationen (eigene Ergänzungen im Fremdbaum)

`smartbugs/tools/gptscan/` und `smartbugs/tools/llmsmartaudit/` sind vollständig
selbst geschrieben. Ursprünglich je vier Dateien nach dem SmartBugs-Schema,
inzwischen je sechs — zwei sind später hinzugekommen und stehen unten separat:

| Datei | Aufgabe |
|---|---|
| `config.yaml` | Image, `output: /output.json`, **`network: bridge`** (SmartBugs setzt Tool-Container sonst auf `network: none`, was jeden API-Aufruf stillschweigend bricht), `env:`-Allowlist, Entrypoint; bei GPTScan seit AP5 zusätzlich `GPTSCAN_BASE_URL`/`GPTSCAN_API_KEY` in der Allowlist, damit ein frei wählbarer Endpunkt (z. B. der lokale Prüfstand) aus einem SmartBugs-Lauf heraus erreichbar ist |
| `scripts/do_solidity.sh` | Entrypoint im Container: Quellordner vorbereiten, Provider/Modell aus der Umgebung wählen, Tool starten, Metadatenzeile ausgeben, `/output.json` garantieren |
| `parser.py` | `parse(exit_code, log, output) -> (findings, infos, errors, fails)` |
| `findings.yaml` | Finding-Name → SWC/DASP-Klassifikation, Severity, Beschreibung |
| `scripts/main_contract.py` | *(AP6)* Reduziert eine Solidity-Datei bei `MAIN=1` auf den Hauptcontract, weil weder GPTScan noch LLMSmartAudit eine eigene Contract-Auswahl anbietet |
| `scripts/mark_timeout.py` | *(AP5)* Stempelt den Marker `sb_timeout` auf einen Report, wenn das Netz (90 % von `TIMEOUT`) den Lauf von außen beendet hat, bevor das Werkzeug selbst dazu kam |

### Eigener Code innerhalb der Fremdbäume

| Datei | Aufgabe |
|---|---|
| `GPTScan/src/llm_backend.py` | Provider-/Modell-Abstraktion, Preise, Kostenschätzung, `--dry-run`, Budget-Wächter, seit AP5 zusätzlich: `deadline_exceeded()` (Deadline-Wächter, das Gegenstück zum Budget-Wächter) und Endpunkt-Override für den Provider `custom` (`GPTSCAN_BASE_URL`), über den der lokale Prüfstand angesprochen wird |
| `GPTScan/src/report_md.py` | Markdown-Reportformatter (`--format md\|both`) |
| `GPTScan/Dockerfile`, `requirements-docker.txt`, `.dockerignore`, `.env.example` | Containerisierung ohne eingebackenen Schlüssel |
| `GPTScan/taxonomy/findings.yaml`, `taxonomy/mapping.md` | Abbildung der 10 MWE-Detektoren auf SWC/DASP mit Begründung |
| `GPTScan/docs/SMARTBUGS_INTEGRATION.md` | Integrationsdokumentation |
| `GPTScan/scripts/aggregate_smartbugs.py`, `prettify_sol.py` | Hilfsskripte |
| `LLMSmartAuditTool-main/.../chatdev/audit_report.py` | Sammelt die Ergebnisse aller 41 Detektor-Phasen und rendert einen standardisierten Report; seit AP5 zusätzlich: schreibt den Report **nach jeder einzelnen Phase** atomar als Zwischenstand (`categories_checked`/`categories_total`), damit der Entrypoint bei einem harten Timeout-Abbruch etwas zu bergen hat |
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
30+ SmartBugs-Werkzeuge berührt. Das gilt auch für AP5 (Timeout durchreichen):
Der gesamte Mechanismus liegt in den eigenen Entrypoints und Parsern der beiden
KI-Scanner, `sb/docker.py`s äußerer Docker-Timeout bleibt unverändert die letzte
Instanz.

### 2.2 GPTScan — 7 geänderte Dateien

Von den 66 getrackten Dateien sind 38 unverändert, 21 neu (siehe oben) und
7 geändert; die Summe ergibt genau die 66:

| Datei | Was | Warum |
|---|---|---|
| `src/tasks.py` | CLI-Optionen `--provider`, `--model`, `--dry-run`, `--format`; `-k/--gptkey` von *required* auf optional; `.env`-Laden über `python-dotenv`; **seit AP5:** Marker `sb_timeout` sowie `llm_calls_skipped_deadline`/`deadline_exceeded` in `/output.json.metadata.json` | GPTScan war fest auf OpenAI verdrahtet und verlangte den Schlüssel als Kommandozeilenargument — unter SmartBugs weder wählbar noch sicher übergebbar. Der Marker ist nötig, weil der Parser sonst nicht unterscheiden kann, ob ein Lauf vollständig war |
| `src/analyze_pipeline.py` | `ask_with_timeout()` zur zentralen Messstelle umgebaut: Token-/Call-Zählung, Budget-Wächter, `--dry-run`-Kurzschluss; **seit AP5:** Deadline-Wächter davor geschaltet, das Gegenstück zum Budget-Wächter | Ohne eine einzige Messstelle gibt es keine belastbare Kostenaussage; die Zählung muss im Elternprozess liegen, damit sie unabhängig von der Multiprocessing-Startmethode funktioniert. Derselbe Grund gilt für den Deadline-Wächter — er muss unabhängig vom Startverfahren zuverlässig greifen |
| `src/chatgpt_api.py` | Modellwahl und SDK-Konfiguration an `llm_backend` delegiert; Zähler für ausgeführte und wegen Budget übersprungene Calls; **seit AP5:** Zähler `num_calls_skipped_deadline` und Grund-Variable `deadline_exceeded_reason` | Die Modell-IDs `gpt-3.5-turbo`/`gpt-4` waren hart kodiert. Die neuen Felder folgen exakt dem Muster der Budget-Bookkeeping, damit die Metadaten sagen können, *warum* ein Lauf früh endete |
| `src/config.py` | `PROVIDERS`-Tabelle (Endpunkt, Schlüssel-Variable, Modell-Tiers, Preise), Budget-Grenzen; **seit AP5:** dritter Eintrag `custom` mit Preisen `0.0` | Provider und Preise gehören an eine Stelle, nicht verstreut in den Aufrufcode. `custom` macht den lokalen Prüfstand (`testing_tools/fake_llm_endpoint.py`) adressierbar, ohne einen realen, kostenpflichtigen Provider umleiten zu können |
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
  `run.py --config SmartContractTA` aus `/app`. Ein aus dem heutigen Repo-Stand
  gebautes Image misst dadurch 590 MB statt 5,13 GB. Extern gesichert, siehe
  `README.md`.

  > **Präzisierung.** Die 590 MB gelten für ein *neu gebautes* Image
  > (`llmsmartaudit-fromrepo:verify`, daneben `llmsmartaudit-reduced:verify`
  > mit 586 MB). Der Tag, den `tools/llmsmartaudit/config.yaml` referenziert
  > und mit dem sämtliche Läufe dieser Arbeit durchgeführt wurden, ist
  > `smartbugs/llmsmartaudit:1.0` — und der ist lokal **weiterhin 5,13 GB
  > groß**, weil die Verkleinerung nie in diesen Tag übernommen wurde. Die
  > Ersparnis ist also gebaut und belegt, aber nicht in Benutzung. Auf die
  > Messergebnisse hat das keinen Einfluss: Der Unterschied ist ausschließlich
  > der ungenutzte `evaluation/`-Ordner.
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

### 2.5 War der Eingriff nötig, ging es anders, und was hätte das gekostet?

Die Abschnitte 2.1 bis 2.3 sagen, **was** geändert wurde und **warum**. Dieser
Abschnitt beantwortet die drei Fragen, die dort offenblieben: Gäbe es einen
anderen Weg, wie groß wäre er, und welche Eingriffe wären Kandidaten für einen
späteren Pull Request an `smartbugs/smartbugs`?

Maßstab für „Aufwand" ist grob geschätzte Arbeit, nicht Codezeilen: **klein** =
eine Sitzung, **mittel** = mehrere Tage mit neuen Tests, **groß** = eigene
Konstruktion mit laufender Pflege.

#### Die zehn markierten Blöcke in `smartbugs/sb/`

| # | Datei, Block | Was | Ohne den Eingriff geht nicht | Anderer Weg | Aufwand des anderen Wegs | Upstream-tauglich? |
|---|---|---|---|---|---|---|
| 1 | `docker.py` 1 | `import time` | nichts für sich — trägt Block 3 | entfällt | — | mit Block 3 |
| 2 | `docker.py` 2 | Host-Variablen der `env:`-Allowlist in den Container reichen | **kein** Weg, einen API-Schlüssel zur Laufzeit zu übergeben | Schlüssel ins Image backen; oder SmartBugs umgehen und die Container selbst starten | **groß.** Ein eingebackener Schlüssel wandert in jede Kopie des Images und lässt sich nicht rotieren, ohne neu zu bauen — für ein Repository, das der Betreuer klont, nicht vertretbar. Ein eigener Runner neben SmartBugs bedeutet, Task-Sammlung, Parallelität, Timeout, Ergebnis-Layout und SARIF-Ausgabe nachzubauen: genau das, wofür SmartBugs da ist, und der Vergleich mit Slither wäre kein Vergleich im selben Rahmen mehr | **ja** — der stärkste PR-Kandidat. LLM-gestützte Werkzeuge sind für SmartBugs neu; ohne diesen Mechanismus kann das Projekt keines davon aufnehmen. Der Eingriff ist rein additiv und für alle vorhandenen Werkzeuge folgenlos |
| 3 | `docker.py` 3 | `rmtree_retry()` — Löschen mit Wiederholung | Läufe unter Windows verlieren lautlos Ergebnisse | Aufräumen ganz auslassen und die Temp-Verzeichnisse dem System überlassen; oder nur unter Windows anders verfahren | **klein**, aber schlechter: Nicht-Aufräumen füllt bei 1 169 Tasks das Temp-Verzeichnis, und ein Windows-Sonderpfad ist genau dieselbe Änderung mit einer zusätzlichen Fallunterscheidung | **ja.** Ein echter Upstream-Fehler, kein Eigenheit dieses Aufbaus: Der `PermissionError` entkommt aus dem `finally`-Block, bevor die Ergebnisdateien geschrieben sind, und der Hauptprozess endet mit Status 0. Reproduziert am 02.08.2026 mit Docker Desktop 29.0.1, belegt in `BA-DEMOLAUF-ERGEBNIS.md`, abgesichert durch `tests/test_docker_cleanup.py` |
| 4 | `docker.py` 4 | ersetzt `shutil.rmtree(sbdir)` durch `rmtree_retry(sbdir)` | dito | dito | — | mit Block 3 |
| 5 | `docker.py` 5 | ersetzt die durchgereichten Werte vor der Rückgabe durch `<redacted>` | der Schlüssel stünde im Klartext in jeder `results/**/smartbugs.json` | nachträglich säubern (`analysis_tools/redact_results.py` tut genau das für Altläufe) | **mittel** und grundsätzlich unterlegen: Zwischen Schreiben und Säubern liegt ein Zeitfenster, in dem der Schlüssel auf der Platte steht. Genau daran lagen die 62 betroffenen Altdateien (Protokoll, Fehler #13) | **ja**, gehört untrennbar zu Block 2. Ein Durchreichen ohne Redaktion wäre eine Sicherheitslücke, die das Projekt sich nicht einhandeln will |
| 6 | `tools.py` 1 | `"env"` in `FIELDS` | `env:` in der `config.yaml` wird ignoriert, Block 2 läuft ins Leere | keiner — `FIELDS` ist die Allowlist, die SmartBugs aus einer `config.yaml` liest | — | mit Block 2 |
| 7 | `tools.py` 2 | Feld `env: Optional[str]` in der `Tool`-Dataclass | dito | keiner | — | mit Block 2 |
| 8 | `analysis.py` 1 | `os.makedirs(task.rdir)` in `try/except` | nichts Hartes. Ohne den Block kommt statt SmartBugs' eigener Fehlermeldung ein roher `OSError` | Eingriff weglassen und die schlechtere Meldung hinnehmen | **null** | **eher ja**, aber unbedeutend. Reine Diagnosequalität, kein Verhaltensunterschied im Erfolgsfall |
| 9 | `analysis.py` 2 | `time.sleep` aus dem Schleifenrumpf in den `except`-Zweig | nichts. **Verhaltensgleich** — der Erfolgspfad verlässt die Schleife ohnehin per `break` | Eingriff weglassen | **null** | **nein.** Kosmetik. Gehört in keinen PR, weil er einen Reviewer Zeit kostet, ohne etwas zu ändern. Rückblickend wäre es besser gewesen, ihn gar nicht erst vorzunehmen |
| 10 | `solidity.py` 1 | `CONTRACT_NAMES`: `([A-Za-z0-9_]*)` → `([a-zA-Z$_][a-zA-Z0-9$_]*)` | Contract-Namen mit `$` werden nicht gefunden; Namen, die mit einer Ziffer beginnen, fälschlich akzeptiert | keiner innerhalb von SmartBugs — das Muster ist die einzige Stelle, an der Contract-Namen erkannt werden | — | **ja.** Eine schlichte Korrektur gegen die Solidity-Grammatik, unabhängig von dieser Arbeit. Betrifft alle Werkzeuge, die `--main` benutzen |

**Zusammengefasst.** Von zehn Blöcken sind fünf (2, 5, 6, 7 und zusammen 1/3/4)
alternativlos, wenn man LLM-gestützte Werkzeuge überhaupt unter SmartBugs
betreiben will. Zwei (8, 9) hätte man auch lassen können; Block 9 ist reine
Kosmetik und der einzige, den man rückblickend nicht wieder so machen würde.
Block 10 ist eine Fehlerkorrektur, die mit dieser Arbeit nichts zu tun hat.

#### Die Änderungen an GPTScan und LLMSmartAudit

Hier ist die Lage anders: Das sind **keine** Upstream-Kandidaten im selben Sinn.
Ein Teil davon ist allgemein nützlich, ein Teil ist reine Anpassung an diesen
Aufbau.

| Bereich | Warum nötig | Anderer Weg und sein Aufwand | Einordnung |
|---|---|---|---|
| **Provider-/Modellwahl** (`GPTScan/src/{tasks,config,chatgpt_api}.py`, `LLMSmartAudit/{run.py, camel/*}`) | Beide Werkzeuge waren fest auf OpenAI verdrahtet, die Modell-IDs hart kodiert. Ohne Entkopplung wäre der gesamte Vergleich an OpenAI-Preise gebunden gewesen | Einen Proxy vor die API setzen, der die Modell-ID umschreibt. **Mittel** — und er verfälscht die Messung: Tokenzählung und Kostenschätzung der Werkzeuge liefen dann gegen den Proxy, nicht gegen den echten Endpunkt | **Upstream-tauglich.** Ein Werkzeug, das nur einen Anbieter kennt, ist für jeden eine Einschränkung. Für GPTScan ist das der naheliegendste eigene PR |
| **`src/rich_utils.py`: vergessenes `breakpoint()`** | Der Haltepunkt blockiert jeden Lauf ohne Terminal, also jeden Lauf im Container | keiner | **Upstream-tauglich**, offensichtlicher Fehler, einzeilige Korrektur |
| **`requirements.txt`: `httpx<0.28`** | `openai 1.3.3` übergibt `proxies=` an `httpx.Client`; der Parameter ist ab httpx 0.28 entfernt, der Import scheitert | `openai` anheben statt `httpx` deckeln. **Mittel** — die `openai`-1.x-API hat sich dazwischen mehrfach geändert, das hätte Aufrufstellen im Fremdcode berührt | **Upstream-tauglich**, aber als Zwischenlösung deklariert |
| **`chatdev/audit_report.py` (neu) plus die Aufrufe in `chat_chain.py` und `phase.py`** | Jede Detektorphase überschreibt `env_dict['ideas']`. Ohne diesen Abgriff überlebt **nur das Ergebnis des letzten** der 41 Detektoren — 40 Ergebnisse gehen verloren | Die 41 Phasenprotokolle aus `WareHouse/` nachträglich parsen. **Groß** und brüchig: Man rekonstruierte aus Gesprächsprotokollen, was das Werkzeug selbst schon strukturiert hatte, und jede Änderung an den Prompts bräche den Parser | **Upstream-tauglich und die wichtigste inhaltliche Korrektur an diesem Werkzeug.** Ohne sie meldet LLMSmartAudit strukturell zu wenig |
| **`camel/typing.py`, `camel/utils.py`: neue `ModelType`-Einträge und Kontextfenster** | `tiktoken` kennt nur OpenAI-Modelle und wirft beim Token-Schätzen; ohne Kontextfenster-Eintrag greift kein Truncation-Schutz | keiner, solange die Modellwahl über das feste Enum läuft | **Teilweise.** Der Mechanismus (Entkopplung vom Enum) gehört upstream; die konkreten DeepSeek-Einträge sind Eigenheit dieses Aufbaus |
| **`chatdev/statistics.py`: DeepSeek-Preise** | Sonst werden DeepSeek-Läufe mit $0,0000 bepreist | Kosten außerhalb rechnen — genau das tun `build_eval.py` und `curated_eval.py` bereits, weil die Tabelle `deepseek-v4-flash` weiterhin nicht kennt | **Eigenheit.** Eine Preistabelle im Werkzeug veraltet zwangsläufig; upstream gehörte eher ein Mechanismus als eine Zeile |
| **AP5-Ergänzungen in beiden Werkzeugen** (`sb_timeout`-Marker, Deadline-Wächter, Snapshot je Phase) | SmartBugs' `--timeout` wirkte für beide Werkzeuge nur als harter Containerabbruch: Der Lauf landete in **fails** und hinterließ nichts | Beim Containerabbruch bleiben und Teilergebnisse aufgeben. **Null Aufwand**, aber bei Laufzeiten bis 7 200 s je Contract verliert man damit Stunden Rechenzeit und bezahlte Token | **Eigenheit dieses Aufbaus.** Der Mechanismus hängt an SmartBugs' Timeout-Vertrag; ein PR gehörte, wenn überhaupt, zu SmartBugs und nicht zu den Werkzeugen. Entwurf und Nachweis in `docs/BA-AP5-TIMEOUT-DESIGN.md` und `docs/BA-AP5-ABSCHLUSSBERICHT.md` |
| **Entfernen von `evaluation/`** (27 662 Dateien, 3,7 GB) | Zur Laufzeit nirgends referenziert; das Repository bliebe sonst unhandhabbar | Den Ordner behalten und nur per `.dockerignore` aus dem Image halten. **Klein** — löst aber nur das Image-Problem, nicht die Repository-Größe | **Eigenheit, kein PR.** Extern gesichert, siehe 2.4 |

#### Was daraus für einen späteren Pull Request folgt

Ein PR an `smartbugs/smartbugs` sollte **nur** die Blöcke 1–7 und 10 enthalten,
also den `env:`-Mechanismus samt Redaktion, das robuste Aufräumen und die
Regex-Korrektur. Blöcke 8 und 9 gehören nicht hinein: Block 8 ist
Diagnosekosmetik, Block 9 ändert nichts. Alles andere sind Änderungen an den
beiden Werkzeugen und gehörte, wenn überhaupt, in PRs an deren eigene
Repositories.

**Angelegt ist davon bisher nichts** — kein Branch, kein Fork, kein PR. Dieser
Abschnitt ist die Vorarbeit, nicht der Vollzug.

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
