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
| SmartBugs | `7ddaf6c` (`main`) = `v2.1.1-7-g7ddaf6c` |

> **Zum SmartBugs-Stand.** Frühere Fassungen dieses Dokuments nannten hier den
> Tag `v2.1.1` (= `01c0e66`). Das ist nicht der Stand, auf dem dieser Baum
> aufsetzt: Geklont wurde `main` sieben Commits später, bei `7ddaf6c`. Weil
> Upstream die Versionszeichenkette erst mit dem achten Commit auf `2.1.2`
> hochgesetzt hat, steht in `pyproject.toml` und `sb/cfg.py` weiterhin
> `2.1.1` — daher die frühere Verwechslung. Der Unterschied ist nicht
> kosmetisch: Vergleicht man gegen den Tag statt gegen `7ddaf6c`, erscheinen
> zehn Upstream-Commits (u. a. die auf 100 % Coverage aufgestockten
> `tests/unit/`-Dateien, `poetry.lock`, `install/setup-venv.sh`,
> `README.md`) fälschlich als eigene Eingriffe. Alle Zahlen unten sind gegen
> `7ddaf6c` gerechnet. Nachvollziehbar mit:
>
> ```
> git clone https://github.com/smartbugs/smartbugs.git up-sb
> git -C up-sb checkout 7ddaf6c
> ```

| Fremdkomponente | Upstream | Lizenz |
|---|---|---|
| SmartBugs | <https://github.com/smartbugs/smartbugs> | Apache-2.0 laut `smartbugs/LICENSE`, MIT laut `smartbugs/pyproject.toml` — Widerspruch im Upstream, beides permissiv |
| GPTScan | <https://github.com/GPTScan/GPTScan> | **AGPL-3.0** |
| LLMSmartAuditTool | <https://github.com/LLMAudit/LLMSmartAuditTool> | Apache-2.0 |

> Hinweis: `smartbugs/tools/llmsmartaudit/config.yaml` nannte ursprünglich
> `https://github.com/LLMSmartAudit/LLMSmartAuditTool` als `origin`. Diese URL
> existiert nicht; der korrekte Ort ist `LLMAudit/LLMSmartAuditTool`. Korrigiert.

---

## 1. Eigener Code

### Neu angelegte Verzeichnisse im Repo-Root

| Pfad | Inhalt |
|---|---|
| `analysis_tools/` | Auswertungswerkzeuge: Parser-Audit, Errors/Fails-Report, Rohlog-Zugriff, Redaktion, CSV-Vergleich |
| `tests/` | pytest-Regressionstests beider Parser und, seit AP5, der Timeout-Mechanik (Deadline-Wächter, Zwischenstand, Entrypoint-Marken) samt Fixtures aus echten Altläufen und synthetischem Material |
| `corpus_tools/` | Rekonstruktion des `mwevariety`-Korpus (`build_fixed.py`), Laufanalyse (`analyze_run.py`), Korpuskopie mit Hauptcontract-Namen für `--main` (`make_main_corpus.py`, seit 24.09.2026) |
| `testing_tools/` | *(AP5)* Lokaler, OpenAI-kompatibler Prüfstand-Endpunkt (`fake_llm_endpoint.py`), der Timeout-Pfade ohne echte API-Kosten und deterministisch auslösbar macht |
| `docs/` | Ausarbeitungen, Protokolle, Berichte |
| `run_curated.ps1` | Massenlauf-Runner über den curated-Datensatz |
| `evaluate_curated.py` | Recall/Precision/F1 gegen die Ground Truth |
| `requirements-dev.txt` | Host-Abhängigkeiten für `analysis_tools/`, `tests/`, `corpus_tools/` (seit 24.09.2026) |
| `.github/workflows/tests.yml` | CI: Testsuite und Secret-Scan bei jedem Push (seit 24.09.2026) |

### SmartBugs-Tool-Integrationen (eigene Ergänzungen im Fremdbaum)

`smartbugs/tools/gptscan/` und `smartbugs/tools/llmsmartaudit/` sind vollständig
selbst geschrieben. Ursprünglich je vier Dateien nach dem SmartBugs-Schema,
inzwischen je sechs — zwei sind später hinzugekommen und stehen unten separat;
bei LLMSmartAudit seit dem 24.09.2026 dazu `mapping.md`:

| Datei | Aufgabe |
|---|---|
| `config.yaml` | Image, `output: /output.json`, **`network: bridge`** (SmartBugs setzt Tool-Container sonst auf `network: none`, was jeden API-Aufruf stillschweigend bricht), `env:`-Allowlist, Entrypoint; bei GPTScan seit AP5 zusätzlich `GPTSCAN_BASE_URL`/`GPTSCAN_API_KEY` in der Allowlist, damit ein frei wählbarer Endpunkt (z. B. der lokale Prüfstand) aus einem SmartBugs-Lauf heraus erreichbar ist |
| `scripts/do_solidity.sh` | Entrypoint im Container: Quellordner vorbereiten, Provider/Modell aus der Umgebung wählen, Tool starten, Metadatenzeile ausgeben, `/output.json` garantieren; bei LLMSmartAudit seit 24.09.2026 ein Modell-Wächter: leeres `LLM_MODEL` beendet den Task mit Exit 2 und Platzhalterreport, bevor das Werkzeug startet |
| `parser.py` | `parse(exit_code, log, output) -> (findings, infos, errors, fails)` |
| `findings.yaml` | Finding-Name → SWC/DASP-Klassifikation, Severity, Beschreibung |
| `mapping.md` (nur LLMSmartAudit) | Begründung je Detektor, warum er seine SWC/DASP-Klassifikation trägt, mit Beleg aus dem Prompt und der Regel, wann eine DASP-Nummer vergeben wird; durch `tests/test_llmsa_mapping_doc.py` an `findings.yaml` gebunden |
| `scripts/main_contract.py` | *(AP6)* Reduziert eine Solidity-Datei bei `MAIN=1` auf den Hauptcontract, weil weder GPTScan noch LLMSmartAudit eine eigene Contract-Auswahl anbietet |
| `scripts/mark_timeout.py` | *(AP5)* Stempelt den Marker `sb_timeout` auf einen Report, wenn das Netz (90 % von `TIMEOUT`) den Lauf von außen beendet hat, bevor das Werkzeug selbst dazu kam |

Seit dem 24.09.2026 kommt ein drittes Verzeichnis dazu,
`smartbugs/tools/slither-0.11.3-glibc/`. Es ist keine neue Integration, sondern
eine Kopie von `tools/slither-0.11.3` mit anderem Image: `config.yaml`
(Image-Tag und Begründung), `Dockerfile` (`python:3.12-slim-bookworm` mit
`slither-analyzer==0.11.3`) und `scripts/do_solidity.sh` (ohne die
`PYTHONPATH`-Zeile des Upstream-Images) sind eigene Dateien; `findings.yaml`
und `parser.py` sind unveränderte Kopien aus dem Upstream-Verzeichnis und
bleiben dessen Code. Grund: `BA-BETRIEB.md`, Fallstrick 10.

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
| `LLMSmartAuditTool-main/.../Dockerfile.smartbugs`, `.dockerignore` | Containerisierung für SmartBugs; seit 24.09.2026 ohne eingebranntes `LLM_MODEL` (Gegenstück zum Wächter im Entrypoint) |
| `LLMSmartAuditTool-main/.../docs/coverage.md` | Welche Detektor-Kategorien `SmartContractTA` tatsächlich prüft |

> **Zur Abgrenzung:** Von den 19 gegenüber dem Upstream neuen Dateien im
> GPTScan-Baum sind 11 eigener Code bzw. eigene Dokumentation (die Tabelle
> oben). Die übrigen 8 liegen unter `GPTScan/reports/` und sind **generierte
> Auswertungen eigener Läufe** (CSV/HTML/PDF/Markdown), kein Werkzeugcode. Sie
> werden hier ausgewiesen, weil sie in der Dateizählung als „neu" erscheinen.

---

## 2. Änderungen an Fremdcode

### 2.1 SmartBugs — 2 inhaltlich geänderte Dateien in `sb/`, dazu `.gitignore`

Gegen den Upstream-Stand `7ddaf6c` unterscheiden sich in `sb/` genau **zwei**
Dateien: `docker.py` (37 Code-Zeilen) und `tools.py` (2 Code-Zeilen). Sie
bilden zusammen den Mechanismus zur Schlüsselübergabe. Hinzu kommt eine
Korrektur an `smartbugs/.gitignore`. Mehr ist es nicht; der vollständige
Hash-Abgleich über alle 777 getrackten Dateien unter `smartbugs/` ergibt:

| | Dateien |
|---|---:|
| unverändert gegenüber `7ddaf6c` | 515 |
| geändert | 3 (`sb/docker.py`, `sb/tools.py`, `.gitignore`) |
| neu: eigene Tool-Integrationen | 16 (`tools/gptscan/`, `tools/llmsmartaudit/` samt `mapping.md`; dazu `config.yaml`, `Dockerfile`, `scripts/do_solidity.sh` in `tools/slither-0.11.3-glibc/`) |
| neu: unveränderte Kopien aus `tools/slither-0.11.3/` | 2 (`findings.yaml`, `parser.py` in `tools/slither-0.11.3-glibc/`) |
| neu: abgelegte Korpus-Dateien | 241 (`samples/gptscan/**.sol` — fremde Contracts, kein eigener Code) |

Summe: 515 + 3 + 16 + 2 + 241 = 777 (bis 24.09.2026 dazu eine leere `uv.lock`,
siehe Kasten unten). Nachprüfbar mit einem Befehl:

```
$ diff -r -q --exclude=.git smartbugs/sb up-sb/sb
Files smartbugs/sb/docker.py and up-sb/sb/docker.py differ
Files smartbugs/sb/tools.py and up-sb/sb/tools.py differ
```

> **Korrektur: `sb/analysis.py` und `sb/solidity.py` sind kein Eigenanteil.**
> Frühere Fassungen dieses Dokuments führten hier zwei „kleinere Eingriffe":
> die Kapselung von `os.makedirs(task.rdir)` in `try/except` samt Verschiebung
> des `time.sleep` in den `except`-Zweig (`analysis.py`) und die Erweiterung
> des `CONTRACT_NAMES`-Musters um `$` und um das Verbot einer führenden Ziffer
> (`solidity.py`). Beide Änderungen sind real vorhanden — aber sie stammen
> **nicht aus dieser Arbeit**. Upstream hat sie selbst vorgenommen, in
> `921f9b5` („add tests, push coverage to 100 %", 20.04.2026) und `89c16bb`
> („Fix parsing of Solidity names", 12.05.2026). Beide Commits liegen vor dem
> hier geklonten Stand `7ddaf6c` (20.05.2026) und damit auch vor dem ersten
> Commit dieses Repositorys (02.08.2026).
>
> Von hier stammten in den beiden Dateien allein die
> `BA MODIFICATION`-Kommentarblöcke — drei an der Zahl. Sie waren beim
> Vergleich gegen den Tag `v2.1.1` entstanden, also gegen den falschen Stand,
> und schrieben der Arbeit dadurch eine Leistung zu, die Upstream erbracht
> hat. **Sie wurden am 21.09.2026 entfernt.** Beide Dateien sind seitdem
> byte-identisch zum Upstream (siehe den `diff -r`-Beleg oben); an ihrem Code
> hat sich dabei nichts geändert, weil die Blöcke reiner Kommentar waren.
> Der Eigenanteil an SmartBugs besteht aus `sb/docker.py`, `sb/tools.py` und
> `.gitignore`.

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

*Abgesichert durch* `tests/test_docker_env_redaction.py` (6 Tests): Weitergabe
nur deklarierter **und** gesetzter Variablen, keine Weitergabe undeklarierter,
kein `environment`-Schlüssel für Werkzeuge ohne `env:`-Feld, Redaktion der
Werte in der Rückgabe, Erhalt der Variablennamen — und, als Gegenprobe, dass
der Container den **echten** Wert erhält. Der letzte Punkt ist der wichtigste:
Eine zu früh angesetzte Redaktion würde die Schlüssel-Prüfung bestehen und
trotzdem jede Analyse still unbrauchbar machen, weil sich das Werkzeug dann mit
der Zeichenkette `<redacted>` authentifizieren würde. Mutationsprobe am
21.09.2026: Entfernt man die Redaktion, werden 2 Tests rot; entfernt man die
Weitergabe, 5; redigiert man vor statt nach dem Lauf, 2.

> **Markierung im Quelltext.** Sämtliche eigenen Eingriffe in den beiden
> geänderten SmartBugs-Quelldateien sind in nummerierte Marker
> eingefasst — `# --- BA MODIFICATION <n>: BEGIN ---` bis
> `# --- BA MODIFICATION <n>: END ---`. `grep -rn "BA MODIFICATION" smartbugs/sb`
> listet alle auf; ein Kopfkommentar in `docker.py` erklärt die Konvention.
>
> | Datei | Blöcke | |
> |---|---:|---|
> | `sb/docker.py` | 5 | eigener Code |
> | `sb/tools.py` | 2 | eigener Code |
>
> Wo ein Block Upstream-Code **ersetzt** statt nur ergänzt, steht die ersetzte
> Fassung wörtlich als Kommentar im Block, eingeleitet mit „restore it to undo
> this block". Das Rückgängigmachen ist damit rein mechanisch: Block löschen,
> zitierte Zeilen einsetzen.
>
> Nachgeprüft gegen `7ddaf6c`: Entfernt man die sieben Blöcke aus `docker.py`
> und `tools.py` und setzt die zitierten Zeilen ein, stimmen beide Dateien mit
> dem Upstream überein (bis auf Leerzeilen) und übersetzen weiterhin. Die
> übrigen Dateien in `sb/` sind ohnehin byte-identisch.
>
> Eine Einschränkung: In `sb/docker.py` steht **außerhalb** der Blöcke ein
> Kopfkommentar von gut zwanzig Zeilen, der die Markierungskonvention erklärt.
> Er ist eigener Text in einer fremden Datei und bleibt bei einem Rückbau
> stehen. Die frühere Formulierung „weder eigener Code unmarkiert geblieben"
> traf für ihn nicht zu; er ändert kein Verhalten, ist aber hiermit
> ausgewiesen.

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

#### Ein kleinerer Eingriff

| Datei | Was | Warum |
|---|---|---|
| `smartbugs/.gitignore` | Muster `results*` an das Verzeichnis der Datei geankert: `/results*` | Ohne Anker traf das Muster jeden Pfad, der mit „results" beginnt — und schloss damit **sechs Upstream-Dateien** von der Versionierung aus (siehe unten). `smartbugs/results/` bleibt unverändert ignoriert |

> **Eine siebte Upstream-Datei ist weiterhin ausgeschlossen.** Der Anker
> `/results*` greift im Verzeichnis `smartbugs/` selbst und trifft dort neben
> `results/` auch den Bash-Wrapper `smartbugs/results2csv`:
>
> ```
> $ git check-ignore -v smartbugs/results2csv
> smartbugs/.gitignore:45:/results*   smartbugs/results2csv
> ```
>
> Die Datei liegt im Arbeitsbaum, erreicht aber keinen Commit und fehlt daher
> in einem frischen Klon. Folgenlos für den dokumentierten Ablauf: `README.md`
> schreibt `python -m sb.results2csv results` vor, und das Modul
> `sb/results2csv.py` ist versioniert. Betroffen ist allein der
> Kommandozeilen-Wrapper neben `smartbugs` und `reparse`.

> **`sb/io.py` ist kein Eigenanteil und steht deshalb nicht mehr in dieser
> Tabelle.** Frühere Fassungen führten die Datei mit den Abweichungen
> `return(x)` → `return x` und einem Kommentar-Leerzeichen und erklärten sie
> als Artefakt eines `black`-Laufs. Beides war ein Fehlschluss aus dem
> falschen Vergleichsstand: Gegen `7ddaf6c` ist `sb/io.py` **byte-identisch**
> zum Upstream. Die Umformatierung stammt von Upstream selbst, aus Commit
> `921f9b5` („add tests, push coverage to 100 %"), der zwischen dem Tag
> `v2.1.1` und dem hier geklonten Stand liegt.

> **`uv.lock` wurde am 24.09.2026 entfernt.** Die Datei war gegenüber dem
> Upstream neu, das Nebenprodukt eines `uv`-Aufrufs, und enthielt nur den Kopf
> (`version`, `revision`, `requires-python`), aber keinen einzigen
> Paketeintrag — 52 Byte. Sie legte also keine Versionen fest und machte die
> Umgebung nicht reproduzierbar; frühere Fassungen dieses Dokuments behaupteten
> das Gegenteil. Die Abhängigkeiten definiert `pyproject.toml`; die venv dieses
> Arbeitsbaums entstand mit `python -m venv` und `pip install -e .` (README,
> „Umgebung anlegen“). `poetry.lock` bleibt unverändert daneben stehen.

Die sechs durch die `.gitignore`-Korrektur zurückgewonnenen Dateien sind
sämtlich **byte-identisch zum Upstream** und ab sofort versioniert:

| Datei | Bedeutung |
|---|---|
| `sb/results2csv.py` | Quelldatei. `README.md` schreibt `python -m sb.results2csv results` als Arbeitsschritt vor — in einem frischen Klon fehlte sie, der Ablauf war nicht durchführbar |
| `templates/results.sql` | SQL-Schema für die Ergebnisausgabe |
| `.github.off/results-ubuntu-{hx,rt,sol}.csv`, `.github.off/old/results-ubuntu.csv` | Referenzergebnisse der (upstream selbst deaktivierten) CI |

*Nicht geändert:* Die übrigen 22 Dateien in `smartbugs/sb/`. Insbesondere
`parse_utils.py`, `parsing.py`, `results2csv.py` und `reparse.py` sind
unverändert — die Parser-Reparatur (siehe `docs/BA-ERRORS-VS-FAILS.md`) findet
ausschließlich in den eigenen Tool-Parsern statt, damit sie sich per
`python -m sb.reparse` auf Altläufe anwenden lässt und kein anderes der
30+ SmartBugs-Werkzeuge berührt. Das gilt auch für AP5 (Timeout durchreichen):
Der gesamte Mechanismus liegt in den eigenen Entrypoints und Parsern der beiden
KI-Scanner, `sb/docker.py`s äußerer Docker-Timeout bleibt unverändert die letzte
Instanz.

> **Der Ausnahme-Defekt vom 21.09.2026 ist nach derselben Regel behandelt.**
> `sb/parse_utils.py::exceptions` nimmt nach einer Traceback-Kopfzeile die
> erste nicht eingerückte Zeile als Ausnahme. LLMSmartAudit schreibt seine
> Token-Buchhaltung unindentiert in denselben Strom, sodass in zehn Tasks eine
> Buchungszeile als Ausnahme gemeldet wurde und die wirkliche Ursache — in
> vier Fällen ein erschöpftes API-Guthaben — nie in `result.json` ankam.
>
> Die Korrektur liegt in `smartbugs/tools/llmsmartaudit/parser.py`
> (`_repair_exception_fails`), nicht im Upstream. Sie ist damit eigener Code
> im eigenen Tool-Parser, wandert per `sb.reparse` auf alle Altläufe und
> berührt kein anderes Werkzeug. Abgesichert durch
> `tests/test_llmsa_exception_repair.py`. Die Herleitung, die Messung des
> Vorher/Nachher und die Frage, was davon upstream-tauglich wäre, stehen in
> [`BA-PARSER-AUDIT-LUECKEN.md`](BA-PARSER-AUDIT-LUECKEN.md).

### 2.2 GPTScan — 7 geänderte Dateien

Von den 64 getrackten Dateien sind 38 unverändert, 19 neu (siehe oben) und
7 geändert; die Summe ergibt genau die 64:

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
  gebautes Image misst dadurch **587 MB statt 5,13 GB**. Extern gesichert, siehe
  `README.md`.

  > **Stand 20.09.2026.** Der Tag, den `tools/llmsmartaudit/config.yaml`
  > referenziert, ist `smartbugs/llmsmartaudit:1.0`. Er wurde an diesem Tag aus
  > dem aktuellen Repo-Stand neu gebaut und misst **587 MB** (Docker-Angabe:
  > 587 MB Disk Usage, 164 MB Content Size). Die Verkleinerung ist damit nicht
  > mehr nur belegt, sondern auch in Benutzung.
  >
  > Frühere Fassungen dieses Abschnitts nannten hier 590 MB für ein separat
  > gebautes Prüf-Image und hielten fest, der eigentliche Tag sei „weiterhin
  > 5,13 GB groß". Das war bereits überholt: Abschnitt 4.5 des
  > Durchführungsprotokolls berichtet denselben Tag am 18.08.2026 mit 586 MB.
  >
  > **Die drei Zahlen 586 / 587 / 590 MB sind am 21.09.2026 restlos
  > aufgeklärt.** Es sind drei verschiedene Builds, die alle drei noch lokal
  > vorliegen:
  >
  > ```
  > smartbugs/llmsmartaudit:1.0     587MB   2026-09-20   <- der benutzte Tag
  > llmsmartaudit-fromrepo:verify   590MB   2026-08-02   <- Pruef-Build aus dem Repo
  > llmsmartaudit-reduced:verify    586MB   2026-08-02   <- Pruef-Build der Verkleinerung
  > ```
  >
  > Kein Widerspruch also, sondern drei Messpunkte über sieben Wochen, deren
  > Spanne von vier Megabyte auf aktualisierte pip-Abhängigkeiten zurückgeht.
  > Maßgeblich ist allein der erste: Er trägt den Tag, den
  > `tools/llmsmartaudit/config.yaml` referenziert.
  >
  > Beim selben Termin gegengeprüft: Im Image liegt **kein**
  > `evaluation/`-Verzeichnis (0 von 11 711 Einträgen), die Verkleinerung ist
  > also tatsächlich wirksam und nicht bloß behauptet. Das Image enthält weder
  > eine `.env`-Datei noch ein Schlüsselmuster.
  >
  > **Die aufgezeichneten Messläufe entstanden mit dem ursprünglichen,
  > 5,13 GB großen Image.** Auf ihre Ergebnisse hat der Neubau keinen Einfluss:
  > Der Unterschied ist ausschließlich der zur Laufzeit nie referenzierte
  > `evaluation/`-Ordner. Unter dem Tag liegt jetzt allerdings nicht mehr
  > bitgleich dasselbe Image, mit dem gemessen wurde.
  >
  > **Stand 24.09.2026.** Der Tag wurde an diesem Tag zweimal neu gebaut:
  > zuerst mit der über `LLM_CONTEXT_TOKENS` einstellbaren Agentengrenze in
  > `camel/utils.py` (ID `7c111aa6b366`, damit lief der Nachlauf
  > `llmsa_mwefixed_v2_ctx1m`), dann ohne eingebranntes `LLM_MODEL` und mit
  > dem Modell-Wächter im Entrypoint (ID `fe758cf6410c`, weiterhin 587 MB).
  > Die Runner protokollieren seit dem 24.09.2026 die Image-ID jedes Laufs,
  > damit sich diese Frage künftig aus dem Protokoll beantwortet.
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

#### Die sieben markierten Blöcke in `smartbugs/sb/`

| # | Datei, Block | Was | Ohne den Eingriff geht nicht | Anderer Weg | Aufwand des anderen Wegs | Upstream-tauglich? |
|---|---|---|---|---|---|---|
| 1 | `docker.py` 1 | `import time` | nichts für sich — trägt Block 3 | entfällt | — | mit Block 3 |
| 2 | `docker.py` 2 | Host-Variablen der `env:`-Allowlist in den Container reichen | **kein** Weg, einen API-Schlüssel zur Laufzeit zu übergeben | Schlüssel ins Image backen; oder SmartBugs umgehen und die Container selbst starten | **groß.** Ein eingebackener Schlüssel wandert in jede Kopie des Images und lässt sich nicht rotieren, ohne neu zu bauen — für ein Repository, das der Betreuer klont, nicht vertretbar. Ein eigener Runner neben SmartBugs bedeutet, Task-Sammlung, Parallelität, Timeout, Ergebnis-Layout und SARIF-Ausgabe nachzubauen: genau das, wofür SmartBugs da ist, und der Vergleich mit Slither wäre kein Vergleich im selben Rahmen mehr | **ja** — der stärkste PR-Kandidat. LLM-gestützte Werkzeuge sind für SmartBugs neu; ohne diesen Mechanismus kann das Projekt keines davon aufnehmen. Der Eingriff ist rein additiv und für alle vorhandenen Werkzeuge folgenlos |
| 3 | `docker.py` 3 | `rmtree_retry()` — Löschen mit Wiederholung | Läufe unter Windows verlieren lautlos Ergebnisse | Aufräumen ganz auslassen und die Temp-Verzeichnisse dem System überlassen; oder nur unter Windows anders verfahren | **klein**, aber schlechter: Nicht-Aufräumen füllt bei 1 169 Tasks das Temp-Verzeichnis, und ein Windows-Sonderpfad ist genau dieselbe Änderung mit einer zusätzlichen Fallunterscheidung | **ja.** Ein echter Upstream-Fehler, kein Eigenheit dieses Aufbaus: Der `PermissionError` entkommt aus dem `finally`-Block, bevor die Ergebnisdateien geschrieben sind, und der Hauptprozess endet mit Status 0. Reproduziert am 02.08.2026 mit Docker Desktop 29.0.1, belegt in `BA-DEMOLAUF-ERGEBNIS.md`, abgesichert durch `tests/test_docker_cleanup.py` |
| 4 | `docker.py` 4 | ersetzt `shutil.rmtree(sbdir)` durch `rmtree_retry(sbdir)` | dito | dito | — | mit Block 3 |
| 5 | `docker.py` 5 | ersetzt die durchgereichten Werte vor der Rückgabe durch `<redacted>` | der Schlüssel stünde im Klartext in jeder `results/**/smartbugs.json` | nachträglich säubern (`analysis_tools/redact_results.py` tut genau das für Altläufe) | **mittel** und grundsätzlich unterlegen: Zwischen Schreiben und Säubern liegt ein Zeitfenster, in dem der Schlüssel auf der Platte steht. Genau daran lagen die 62 betroffenen Altdateien (Protokoll, Fehler #13) | **ja**, gehört untrennbar zu Block 2. Ein Durchreichen ohne Redaktion wäre eine Sicherheitslücke, die das Projekt sich nicht einhandeln will |
| 6 | `tools.py` 1 | `"env"` in `FIELDS` | `env:` in der `config.yaml` wird ignoriert, Block 2 läuft ins Leere | keiner — `FIELDS` ist die Allowlist, die SmartBugs aus einer `config.yaml` liest | — | mit Block 2 |
| 7 | `tools.py` 2 | Feld `env: Optional[str]` in der `Tool`-Dataclass | dito | keiner | — | mit Block 2 |

**Zusammengefasst.** Alle sieben verbliebenen Blöcke sind alternativlos, wenn
man LLM-gestützte Werkzeuge überhaupt unter SmartBugs betreiben will: 2, 5, 6
und 7 tragen den Schlüssel-Mechanismus, 1/3/4 zusammen das Aufräumen unter
Windows. Es bleibt kein Eingriff übrig, den man ebenso gut hätte lassen
können.

> Drei weitere Blöcke standen bis zum 21.09.2026 in `analysis.py` (2) und
> `solidity.py` (1) und wurden hier mitbewertet. Sie waren gegenstandslos —
> der von ihnen beschriebene Code stammt vom Upstream — und sind entfernt;
> siehe den Kasten in Abschnitt 2.1.

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
| **`camel/typing.py`, `camel/utils.py`: neue `ModelType`-Einträge und Kontextfenster** | `tiktoken` kennt nur OpenAI-Modelle und wirft beim Token-Schätzen; ohne Kontextfenster-Eintrag greift kein Truncation-Schutz. Seit 24.09.2026 liest `get_model_token_limit` für `DEEPSEEK_CHAT` die Grenze aus `LLM_CONTEXT_TOKENS` (Default weiterhin 65 536, damit Altläufe vergleichbar bleiben); die Anbieterdokumentation nennt für `deepseek-v4-flash` 1M Token | keiner, solange die Modellwahl über das feste Enum läuft | **Teilweise.** Der Mechanismus (Entkopplung vom Enum) gehört upstream; die konkreten DeepSeek-Einträge sind Eigenheit dieses Aufbaus |
| **`chatdev/statistics.py`: DeepSeek-Preise** | Sonst werden DeepSeek-Läufe mit $0,0000 bepreist | Kosten außerhalb rechnen — genau das tun `build_eval.py` und `curated_eval.py` bereits, weil die Tabelle `deepseek-v4-flash` weiterhin nicht kennt | **Eigenheit.** Eine Preistabelle im Werkzeug veraltet zwangsläufig; upstream gehörte eher ein Mechanismus als eine Zeile |
| **AP5-Ergänzungen in beiden Werkzeugen** (`sb_timeout`-Marker, Deadline-Wächter, Snapshot je Phase) | SmartBugs' `--timeout` wirkte für beide Werkzeuge nur als harter Containerabbruch: Der Lauf landete in **fails** und hinterließ nichts | Beim Containerabbruch bleiben und Teilergebnisse aufgeben. **Null Aufwand**, aber bei Laufzeiten bis 7 200 s je Contract verliert man damit Stunden Rechenzeit und bezahlte Token | **Eigenheit dieses Aufbaus.** Der Mechanismus hängt an SmartBugs' Timeout-Vertrag; ein PR gehörte, wenn überhaupt, zu SmartBugs und nicht zu den Werkzeugen. Entwurf und Nachweis in `docs/BA-AP5-TIMEOUT-DESIGN.md` und `docs/BA-AP5-ABSCHLUSSBERICHT.md` |
| **Entfernen von `evaluation/`** (27 662 Dateien, 3,7 GB) | Zur Laufzeit nirgends referenziert; das Repository bliebe sonst unhandhabbar | Den Ordner behalten und nur per `.dockerignore` aus dem Image halten. **Klein** — löst aber nur das Image-Problem, nicht die Repository-Größe | **Eigenheit, kein PR.** Extern gesichert, siehe 2.4 |

#### Was daraus für einen Pull Request folgt, und was davon vorbereitet ist

Ein PR an `smartbugs/smartbugs` sollte **nur** die sieben Blöcke in
`docker.py` und `tools.py` enthalten, also den `env:`-Mechanismus samt
Redaktion und das robuste Aufräumen. Alles andere sind Änderungen an den
beiden Werkzeugen und gehörte, wenn überhaupt, in PRs an deren eigene
Repositories.

**Stand 25.09.2026: vorbereitet, noch nicht eingereicht.** Die sieben Blöcke
sind in zwei getrennte Änderungen auf dem aktuellen Upstream-Stand
(`smartbugs/smartbugs`, Version 2.1.6; `sb/docker.py` und `sb/tools.py` sind
dort seit `7ddaf6c` unverändert) übertragen, ohne die hiesigen Markerkommentare
und im Stil des Upstreams (Docstrings, Typannotationen, `black`/`ruff`):

| Branch | Inhalt | Blöcke | Tests |
|---|---|---|---|
| `feat/env-passthrough` | Feld `env:` in `config.yaml`, Weitergabe nur gesetzter Host-Variablen, Redaktion der Werte vor dem Schreiben nach `smartbugs.json`; Eintrag in `templates/tools/template/config.yaml` | 2, 5, 6, 7 | 8 neue |
| `fix/tempdir-cleanup-retry` | `_remove_tempdir()` mit Wiederholung statt `shutil.rmtree()` im `finally` von `execute()` | 1, 3, 4 | 4 neue |

Beide Branches bestehen die Upstream-Prüfungen: unter Linux 495 beziehungsweise
491 Tests bei 100 % Abdeckung (Upstream-Stand: 487), `ruff` ohne Befund,
`mypy` ohne neue Befunde, `black` ohne Änderung an den berührten Dateien.
Unter Windows scheitern im Upstream-Stand 12 Tests an Pfadannahmen; die
beiden Branches ändern daran nichts. Die Branches liegen in einem lokalen Klon
außerhalb dieses Repositorys, zusammen mit den PR-Beschreibungen; Fork, Push
und das Öffnen der PRs sind der Schritt, der noch aussteht und die Verfasser
als Absender braucht.

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

git clone https://github.com/smartbugs/smartbugs.git /tmp/up-smartbugs
git -C /tmp/up-smartbugs checkout 7ddaf6c

diff -r -q --exclude=.git GPTScan /tmp/up-gptscan
diff -r -q --exclude=.git LLMSmartAuditTool-main/LLMSmartAuditTool-main /tmp/up-llmsa
diff -r -q --exclude=.git smartbugs/sb /tmp/up-smartbugs/sb
```

In Git Bash unter Windows braucht das sparse-checkout-Muster
`MSYS_NO_PATHCONV=1`, sonst wandelt MSYS das führende `/` in einen
Windows-Pfad um.

`diff -r` vergleicht den Arbeitsbaum und zeigt damit auch ungetrackte Dateien
an. Für die Zählung oben ist `git ls-files` maßgeblich.
