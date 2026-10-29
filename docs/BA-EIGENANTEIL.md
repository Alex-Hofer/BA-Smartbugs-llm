# Eigenanteil und Änderungen an Fremdcode

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Dieses Repository enthält drei fremde Codebasen (SmartBugs, GPTScan,
LLMSmartAuditTool) und unseren Eigenanteil. Hier steht, welche Datei wohin
gehört und — wo wir fremden Code verändert haben — **was** wir geändert haben
und **warum**.

Die Aufstellung ist nicht geschätzt, sondern per Datei-Hash gegen die
Upstream-Stände abgeglichen. Gezählt wird nur, was git **trackt**.

| Komponente | Upstream | Verglichener Stand | Lizenz |
|---|---|---|---|
| SmartBugs | <https://github.com/smartbugs/smartbugs> | `7ddaf6c` (`main`, = `v2.1.1-7-g7ddaf6c`) | Apache-2.0 laut `LICENSE`, MIT laut `pyproject.toml` — Widerspruch im Upstream, beides permissiv |
| GPTScan | <https://github.com/GPTScan/GPTScan> | `29a1747` (`main`) | **AGPL-3.0** |
| LLMSmartAuditTool | <https://github.com/LLMAudit/LLMSmartAuditTool> | `c507fe4` (`main`) | Apache-2.0 |

> **Warum `7ddaf6c` und nicht der Tag `v2.1.1`?** Wir haben `main` sieben
> Commits nach dem Tag geklont. Die Versionszeichenkette steht dort noch auf
> `2.1.1`, daher die frühere Verwechslung. Gegen den Tag verglichen erschienen
> zehn Upstream-Commits (u. a. Tests mit 100 % Coverage, `poetry.lock`,
> `README.md`) fälschlich als unsere Eingriffe. Alle Zahlen unten sind gegen
> `7ddaf6c` gerechnet:
>
> ```
> git clone https://github.com/smartbugs/smartbugs.git up-sb
> git -C up-sb checkout 7ddaf6c
> ```

Nebenbei korrigiert: `smartbugs/tools/llmsmartaudit/config.yaml` nannte als
`origin` `LLMSmartAudit/LLMSmartAuditTool`; richtig ist `LLMAudit/LLMSmartAuditTool`.

---

## 1. Eigener Code

### Verzeichnisse im Repo-Root

| Pfad | Inhalt |
|---|---|
| `analysis_tools/` | Generatoren der `eval/`-Ordner (`curated_eval.py`, `build_eval.py`, `gptscan_eval.py`, `per_contract_stats.py`), Nachrechnung ohne Rohdaten (`metrics_from_eval.py`), Parser-Audit, errors/fails-Report, Schwärzung, CSV-Vergleich, Secret-Scan ([`analysis_tools/README.md`](../analysis_tools/README.md)) |
| `tests/` | Regressionstests beider Parser und der Timeout-Mechanik, mit Fixtures aus echten Läufen |
| `corpus_tools/` | Rekonstruktion des DeFi-Korpus (`build_fixed.py`), Laufanalyse, Korpuskopie für `--main` |
| `testing_tools/` | lokaler, OpenAI-kompatibler Prüfstand (`fake_llm_endpoint.py`, AP5) |
| `docs/`, `eval/` | Dokumentation und Auswertungen |
| `run_curated.ps1` u. a. | Runner für Massenläufe |
| `evaluate_curated.py` | Recall/Precision/F1 gegen die Ground Truth |
| `requirements-dev.txt`, `.github/workflows/tests.yml` | Host-Abhängigkeiten; CI mit Tests und Secret-Scan bei jedem Push |

### SmartBugs-Integrationen

`smartbugs/tools/gptscan/` und `smartbugs/tools/llmsmartaudit/` haben wir
komplett selbst geschrieben:

| Datei | Aufgabe |
|---|---|
| `config.yaml` | Image, `output: /output.json`, **`network: bridge`** (sonst kein API-Zugang), `env:`-Allowlist, Entrypoint |
| `scripts/do_solidity.sh` | Entrypoint: Quelle vorbereiten, Provider/Modell wählen, Werkzeug starten, Metadaten ausgeben, `/output.json` garantieren; bei LLMSmartAudit Abbruch mit Exit 2, wenn `LLM_MODEL` fehlt |
| `parser.py` | `parse(exit_code, log, output) -> (findings, infos, errors, fails)` |
| `findings.yaml` | Finding-Name → SWC/DASP, Severity, Beschreibung |
| `scripts/main_contract.py` | reduziert eine Datei bei `MAIN=1` auf den Hauptcontract (AP6) |
| `scripts/mark_timeout.py` | setzt `sb_timeout`, wenn das Netz den Lauf beendet hat (AP5) |
| `mapping.md` (nur LLMSmartAudit) | Begründung je Detektor für seine SWC/DASP-Klasse, per Test an `findings.yaml` gebunden |

Dazu kommt `smartbugs/tools/slither-0.11.3-glibc/`: keine neue Integration,
sondern `tools/slither-0.11.3` mit anderem Image. Eigen sind `config.yaml`,
`Dockerfile` (`python:3.12-slim-bookworm`, `slither-analyzer==0.11.3`) und
`scripts/do_solidity.sh`; `findings.yaml` und `parser.py` sind unveränderte
Upstream-Kopien. Grund: [`BA-BETRIEB.md`](BA-BETRIEB.md), Fallstrick 10.

### Eigener Code in den Fremdbäumen

| Datei | Aufgabe |
|---|---|
| `GPTScan/src/llm_backend.py` | Provider-/Modellwahl, Preise, Kostenschätzung, Dry-Run, Budget- und Deadline-Wächter, Endpunkt für Provider `custom` |
| `GPTScan/src/report_md.py` | Markdown-Report |
| `GPTScan/Dockerfile`, `requirements-docker.txt`, `.dockerignore`, `.env.example` | Container ohne eingebackenen Schlüssel |
| `GPTScan/taxonomy/findings.yaml`, `taxonomy/mapping.md` | MWE-Regeln → SWC/DASP mit Begründung |
| `GPTScan/docs/SMARTBUGS_INTEGRATION.md`, `scripts/*.py` | Integrationsdoku, Hilfsskripte |
| `LLMSmartAuditTool-main/.../chatdev/audit_report.py` | sammelt die Ergebnisse aller 41 Detektorphasen und schreibt nach **jeder Phase** einen Zwischenstand (für den Timeout-Fall) |
| `LLMSmartAuditTool-main/.../Dockerfile.smartbugs`, `.dockerignore` | Container für SmartBugs, ohne eingebranntes Modell |
| `LLMSmartAuditTool-main/.../docs/coverage.md` | welche Detektoren `SmartContractTA` tatsächlich prüft |

Von den 19 neuen Dateien im GPTScan-Baum sind 11 eigener Code oder eigene
Doku; die übrigen 8 unter `GPTScan/reports/` sind generierte Auswertungen
eigener Läufe.

---

## 2. Änderungen an Fremdcode

### 2.1 SmartBugs: zwei Dateien in `sb/`, dazu `.gitignore`

Gegen `7ddaf6c` unterscheiden sich in `sb/` genau **zwei** Dateien:
`docker.py` (37 Code-Zeilen) und `tools.py` (2 Code-Zeilen). Dazu kommt eine
Korrektur an `smartbugs/.gitignore`. Hash-Abgleich über alle 3 780 getrackten
Dateien unter `smartbugs/` (Stand 25.09.2026):

| | Dateien |
|---|---:|
| unverändert gegenüber `7ddaf6c` | 516 |
| geändert (`sb/docker.py`, `sb/tools.py`, `.gitignore`) | 3 |
| neu: eigene Tool-Integrationen (inkl. glibc-Slither-Konfiguration) | 16 |
| neu: unveränderte Kopien aus `tools/slither-0.11.3/` | 2 |
| neu: Korpus-Dateien (fremde Contracts) | 241 |
| neu: Rohdaten der Messläufe (`result.json`, `smartbugs.json`) | 3 002 |

```
$ diff -r -q --exclude=.git smartbugs/sb up-sb/sb
Files smartbugs/sb/docker.py and up-sb/sb/docker.py differ
Files smartbugs/sb/tools.py and up-sb/sb/tools.py differ
```

> **`sb/analysis.py`, `sb/solidity.py` und `sb/io.py` sind kein Eigenanteil.**
> Frühere Fassungen führten dort Eingriffe auf. Die Änderungen stammen aber vom
> Upstream selbst (`921f9b5`, `89c16bb`) und lagen nur gegen den falschen
> Vergleichsstand als „unsere“ vor. Unsere reinen Kommentarblöcke darin haben
> wir am 21.09.2026 entfernt; die Dateien sind byteidentisch zum Upstream.

#### Der Schlüssel-Mechanismus

**`sb/tools.py`** — `env` kommt ins `FIELDS`-Tupel (Block 1) und als
Typangabe in die Klasse `Tool` (Block 2). SmartBugs akzeptiert in einer
`config.yaml` nur Felder aus `FIELDS`; ohne Block 1 bricht es beim Laden
unserer Integrationen ab:

```
SmartBugsError: Tool gptscan/solidity: extra field(s) env
```

(nachgeprüft am 28.09.2026; frühere Fassungen behaupteten fälschlich, das Feld
würde still ignoriert). Block 2 ist nur die Typangabe und zur Laufzeit ohne
Wirkung.

**`sb/docker.py`** — reicht die unter `env:` gelisteten Host-Variablen in den
Container und ersetzt dieselben Werte vor der Rückgabe durch `<redacted>`.
Ohne Ersteres müsste der Schlüssel ins Image (und stünde in jeder Kopie);
ohne Letzteres stünde er im Klartext in jeder `results/**/smartbugs.json`.

*Abgesichert durch* `tests/test_docker_env_redaction.py` (6 Tests): nur
deklarierte **und** gesetzte Variablen werden weitergereicht, Werte werden
geschwärzt, Namen bleiben — und der Container bekommt trotzdem den **echten**
Wert. Letzteres ist der wichtigste Test: Eine zu früh angesetzte Schwärzung
bestünde die Schlüssel-Prüfung und würde jede Analyse still unbrauchbar
machen. Mutationsprobe (21.09.2026): ohne Schwärzung 2 rote Tests, ohne
Weitergabe 5, Schwärzung vor dem Lauf 2.

> **Markierung im Quelltext.** Alle Eingriffe stehen zwischen
> `# --- BA MODIFICATION <n>: BEGIN ---` und `... END ---`
> (`grep -rn "BA MODIFICATION" smartbugs/sb`): 5 Blöcke in `docker.py`, 2 in
> `tools.py`. Wo ein Block Upstream-Code ersetzt, steht der Originalcode als
> Kommentar daneben („restore it to undo this block“). Gegen `7ddaf6c`
> geprüft: Blöcke raus, Originalzeilen rein, und beide Dateien stimmen mit dem
> Upstream überein. Einzige Ausnahme: ein Kopfkommentar in `docker.py`, der die
> Konvention erklärt — eigener Text außerhalb der Blöcke, ohne Wirkung auf das
> Verhalten.

#### Aufräumen der Task-Verzeichnisse unter Windows

**`sb/docker.py`** — `shutil.rmtree(sbdir)` im `finally` von `execute` ist
durch `rmtree_retry` ersetzt: dasselbe Löschen mit Wiederholung und kurzem
Backoff; bleibt das Verzeichnis gesperrt, wird das geloggt statt geworfen.

*Warum:* Unter Docker Desktop ist das Handle auf das gemountete Verzeichnis
nach `container.remove()` noch offen, `os.rmdir` scheitert mit `WinError 5`.
Der `PermissionError` ist kein `SmartBugsError`, entkommt dem `finally` und
beendet den Worker, **bevor** `result.json`, `result.log` und `smartbugs.json`
geschrieben sind. Der Hauptprozess endet trotzdem mit Status 0 — der Verlust
ist vollständig und lautlos. Beobachtet am 02.08.2026 mit Docker Desktop
29.0.1 in allen vier Workern ([`BA-DEMOLAUF-ERGEBNIS.md`](BA-DEMOLAUF-ERGEBNIS.md),
2); abgesichert durch `tests/test_docker_cleanup.py`.

#### `.gitignore`

Das Muster `results*` traf ohne Anker jeden Pfad, der mit „results“ beginnt,
und schloss damit sechs Upstream-Dateien von der Versionierung aus — darunter
`sb/results2csv.py`, ohne das der in der SmartBugs-README beschriebene Ablauf
in einem frischen Klon nicht funktionierte. Seit dem 25.09.2026 heißt das
Muster `/results/**` mit Ausnahmen: Je Task sind `result.json` und
`smartbugs.json` versioniert, und auch der Wrapper `smartbugs/results2csv` ist
wieder dabei. Alle zurückgewonnenen Dateien sind byteidentisch zum Upstream.

Eine leere `uv.lock` (52 Byte, ohne Paketeintrag) haben wir am 24.09.2026
entfernt; die Abhängigkeiten definiert `pyproject.toml`.

#### Was wir in SmartBugs nicht angefasst haben

Die übrigen 22 Dateien in `sb/`, insbesondere `parse_utils.py`, `parsing.py`
und `reparse.py`. Die Parser-Reparatur ([`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md))
liegt ausschließlich in unseren Tool-Parsern — so lässt sie sich per
`sb.reparse` auf Altläufe anwenden und berührt kein anderes Werkzeug. Dasselbe
gilt für AP5: Der Mechanismus liegt in unseren Entrypoints und Parsern, der
äußere Docker-Timeout bleibt die letzte Instanz. Auch den Ausnahme-Defekt in
`sb/parse_utils.py::exceptions` (LLMSmartAudits Token-Buchhaltung wurde als
Ausnahme gemeldet und verdeckte in vier Fällen ein leeres API-Guthaben) haben
wir im eigenen Parser behoben (`_repair_exception_fails`,
[`BA-PARSER-AUDIT-LUECKEN.md`](BA-PARSER-AUDIT-LUECKEN.md)).

### 2.2 GPTScan — 7 geänderte Dateien

Von 64 getrackten Dateien: 38 unverändert, 19 neu, 7 geändert.

| Datei | Was | Warum |
|---|---|---|
| `src/tasks.py` | Optionen `--provider`, `--model`, `--dry-run`, `--format`; Schlüssel optional statt Pflichtargument; `.env` über `python-dotenv`; Marker `sb_timeout` und Deadline-Felder in den Metadaten | GPTScan war fest auf OpenAI verdrahtet und wollte den Schlüssel auf der Kommandozeile. Der Marker sagt dem Parser, ob ein Lauf vollständig war |
| `src/analyze_pipeline.py` | `ask_with_timeout()` als zentrale Messstelle: Token-/Aufrufzählung, Budget- und Deadline-Wächter, Dry-Run | ohne eine Messstelle keine belastbare Kostenaussage; die Zählung muss im Elternprozess liegen |
| `src/chatgpt_api.py` | Modellwahl an `llm_backend` delegiert; Zähler für übersprungene Aufrufe (Budget, Deadline) | Modell-IDs waren hart kodiert; die Metadaten sollen sagen, *warum* ein Lauf früh endete |
| `src/config.py` | `PROVIDERS`-Tabelle, Budget-Grenzen, Provider `custom` mit Preis 0 | Provider und Preise an einer Stelle; `custom` macht den Prüfstand erreichbar, ohne einen bezahlten Provider umleiten zu können |
| `src/rich_utils.py` | vergessenes `breakpoint()` entfernt | blockiert jeden Lauf ohne Terminal, also jeden im Container |
| `requirements.txt` | `python-dotenv==1.0.1` | für `.env` |
| `README.md` | Abschnitt zur Modellwahl | Doku |

> Diese Änderungen bleiben AGPL-3.0, unabhängig von der MIT-Lizenz unseres
> übrigen Eigenanteils.

### 2.3 LLMSmartAuditTool — 9 geänderte Dateien

Von 235 getrackten Dateien: 212 unverändert, 14 neu (davon 4 eigener Code, die
übrigen sind drei umbenannte `misc/*.png` und ein aufbewahrter Beispielreport),
9 geändert.

| Datei | Was | Warum |
|---|---|---|
| `run.py` | `--provider`, `--model`, `--task-file`; klare Fehlermeldung statt stillem Fallback | war auf OpenAI festgelegt und las die Aufgabe interaktiv |
| `camel/model_backend.py` | Modell-ID aus `LLM_MODEL_ID` statt aus dem Enum; DeepSeek-Grenze 8 192 Completion-Token; Kontextfenster-Fallback | sonst ist kein Modell außerhalb des Enums wählbar |
| `camel/typing.py` | `ModelType.DEEPSEEK_CHAT`, `ModelType.CUSTOM`; tiktoken-Encoding für Nicht-OpenAI-Modelle | `tiktoken` wirft sonst beim Token-Schätzen |
| `camel/utils.py` | Kontextfenster für die neuen Typen; seit 24.09.2026 über `LLM_CONTEXT_TOKENS` einstellbar (Default 65 536) | ohne Eintrag kein Truncation-Schutz; die feste Grenze kostete 37 DeFi-Contracts |
| `chatdev/chat_chain.py` | `audit_report.reset()` am Anfang, `write_markdown()` am Ende | Anbindung unseres Report-Sammlers |
| `chatdev/phase.py` | `audit_report.record()` nach jeder Phase; `model_type` durchgereicht | jede Detektorphase überschreibt `env_dict['ideas']` — ohne Abgriff überlebt nur der **letzte** Detektor |
| `chatdev/statistics.py` | DeepSeek-Preise | sonst kosten DeepSeek-Läufe angeblich $0 |
| `CompanyConfig/SmartContractTA/ChatChainConfig.json` | Rolle „Security Testing Engineer“ ergänzt | — |
| `requirements.txt` | `httpx<0.28` | `openai 1.3.3` übergibt `proxies=`, das httpx 0.28 nicht mehr kennt |

### 2.4 Was nicht als Änderung zählt

* **`misc/*.png`:** Drei Dateinamen haben im Upstream ein führendes
  Leerzeichen, das beim ZIP-Bezug verloren geht. Inhalt identisch.
* **`evaluation/` entfernt** (27 662 Dateien, 3,7 GB). Zur Laufzeit nirgends
  benutzt. Das Image schrumpft dadurch von **5,13 GB auf 587 MB**; der Ordner
  ist extern gesichert. Der Image-Tag `smartbugs/llmsmartaudit:1.0` wurde am
  20.09.2026 und zweimal am 24.09.2026 neu gebaut (zuletzt `fe758cf6410c`,
  587 MB, ohne eingebranntes Modell); die früher genannten 586 und 590 MB sind
  Prüf-Builds vom 02.08.2026. Im Image liegt kein `evaluation/`, keine `.env`
  und kein Schlüssel. Unsere Messläufe entstanden noch mit dem 5,13-GB-Image;
  der Unterschied ist nur der ungenutzte Ordner. Seit dem 24.09.2026
  protokollieren die Runner die Image-ID jedes Laufs.
* **`WareHouse/VaultDS*`:** Reste eigener Tests vom 30.06.2026, bis auf einen
  Beispielreport entfernt, über den Initial-Commit `f85946e` wiederherstellbar.
* **`GPTScan/src/jars/*.jar`** (19,9 und 18,9 MB): fremde Binärdateien ohne
  Bauanleitung im Repo, zur Laufzeit per `java -jar` aufgerufen — unangetastet.

### 2.5 War der Eingriff nötig, und ging es anders?

Aufwand grob geschätzt: **klein** = eine Sitzung, **mittel** = mehrere Tage mit
Tests, **groß** = eigene Konstruktion mit laufender Pflege.

#### Die sieben Blöcke in `smartbugs/sb/`

| # | Block | Was | Ohne ihn | Anderer Weg, Aufwand | Upstream? |
|---|---|---|---|---|---|
| 1 | `docker.py` 1 | `import time` | — (trägt Block 3) | — | mit 3 |
| 2 | `docker.py` 2 | `env:`-Variablen in den Container | **kein** Weg, einen Schlüssel zur Laufzeit zu übergeben | Schlüssel ins Image (nicht rotierbar, landet in jeder Kopie) oder eigener Runner neben SmartBugs, der Parallelität, Timeout, Layout und SARIF nachbaut — **groß**, und Slither liefe nicht mehr im selben Rahmen | **ja**, der wichtigste Teil; rein additiv |
| 3 | `docker.py` 3 | `rmtree_retry()` | Windows-Läufe verlieren lautlos Ergebnisse | nicht aufräumen (füllt das Temp-Verzeichnis) oder Windows-Sonderpfad — **klein**, aber schlechter | **ja**, echter Upstream-Fehler |
| 4 | `docker.py` 4 | `rmtree_retry(sbdir)` statt `shutil.rmtree` | dito | dito | mit 3 |
| 5 | `docker.py` 5 | Werte durch `<redacted>` ersetzen | Schlüssel im Klartext in jeder `smartbugs.json` | nachträglich säubern (`redact_results.py`) — **mittel** und unterlegen: Bis dahin liegt der Schlüssel auf der Platte. Genau so entstanden die 62 betroffenen Altdateien | **ja**, untrennbar von 2 |
| 6 | `tools.py` 1 | `"env"` in `FIELDS` | SmartBugs lädt die Integrationen gar nicht | keiner | mit 2 |
| 7 | `tools.py` 2 | Typangabe `env: Optional[str]` | zur Laufzeit nichts | weglassen | mit 2 |

Sechs der sieben Blöcke sind alternativlos, wenn LLM-Werkzeuge überhaupt unter
SmartBugs laufen sollen; Block 7 gehört zu einer sauberen Fassung dazu.

#### Die Änderungen an GPTScan und LLMSmartAudit

| Bereich | Warum nötig | Anderer Weg | Einordnung |
|---|---|---|---|
| Provider-/Modellwahl | beide Werkzeuge fest auf OpenAI | Proxy, der Modell-IDs umschreibt — **mittel**, verfälscht aber Tokenzählung und Kosten | upstream-tauglich |
| `breakpoint()` entfernt | blockiert jeden Container-Lauf | keiner | upstream-tauglich, einzeilig |
| `httpx<0.28` | Import scheitert sonst | `openai` anheben — **mittel**, berührt Fremdcode | upstream-tauglich als Zwischenlösung |
| `audit_report.py` + Aufrufe | ohne ihn überlebt nur der letzte von 41 Detektoren | Phasenprotokolle nachträglich parsen — **groß** und brüchig | upstream-tauglich, wichtigste inhaltliche Korrektur |
| neue `ModelType`-Einträge, Kontextfenster | `tiktoken` wirft sonst; kein Truncation-Schutz | keiner, solange das Enum fest ist | Mechanismus upstream-tauglich, DeepSeek-Einträge nicht |
| DeepSeek-Preise | sonst $0 | Kosten außerhalb rechnen (tun wir ohnehin) | Eigenheit |
| AP5 (Marker, Deadline-Wächter, Zwischenstand je Phase) | `--timeout` war nur ein harter Abbruch ohne Ergebnis | Teilergebnisse aufgeben — kostet bei bis zu 7 200 s je Contract Stunden und bezahlte Token | Eigenheit dieses Aufbaus ([`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md)) |
| `evaluation/` entfernt | Repository sonst unhandhabbar | nur per `.dockerignore` ausschließen — löst nur das Image-Problem | Eigenheit, kein PR |

#### Pull Request an SmartBugs: eingereicht und übernommen

Ursprünglich wollten wir nur die sieben Blöcke einreichen und die
Werkzeugänderungen den Werkzeug-Repositories überlassen. Unser Betreuer hat am
10.10.2026 um mehr gebeten: beide Werkzeuge direkt in SmartBugs, als ein Pull
Request auf `develop`, bei dem unsere Beiträge sichtbar bleiben.

**Am 12.10.2026 eingereicht als
[smartbugs/smartbugs#222](https://github.com/smartbugs/smartbugs/pull/222), am
14.10.2026 in `develop` übernommen** (Basis Version 2.1.6; `sb/docker.py` und
`sb/tools.py` sind dort seit `7ddaf6c` unverändert). Fünf Commits ohne unsere
Markerkommentare, im Stil des Upstreams (Docstrings, Typannotationen,
`black`/`ruff`), jeder mit einem von uns als Autor und dem anderen als
Co-Autor:

| Commit | Inhalt | Blöcke | Tests |
|---|---|---|---|
| Forward selected host environment variables into tool containers | Feld `env:`, Weitergabe nur gesetzter Variablen, Schwärzung vor `smartbugs.json`; Eintrag im Tool-Template | 2, 5, 6, 7 | 8 neue |
| Retry removing a task's temporary directory instead of crashing the worker | `_remove_tempdir()` mit Wiederholung | 1, 3, 4 | 4 neue, eigene Datei |
| Add GPTScan as a SmartBugs tool | `tools/gptscan/` mit Entrypoint, `main_contract.py`, `mark_timeout.py`, Dockerfile | — | — |
| Add LLMSmartAudit as a SmartBugs tool | `tools/llmsmartaudit/`, dieselben Dateien | — | — |
| README | zwei Tabellenzeilen, Zähler 26 → 28, Fußnote zu Schlüssel, Modell, Netz, Kosten und Image-Bau | — | — |

Die Werkzeuge selbst liegen mit den Änderungen aus 2.2 und 2.3 als öffentliche
Forks unter [`Alex-Hofer/GPTScan`](https://github.com/Alex-Hofer/GPTScan/tree/smartbugs)
und [`Alex-Hofer/LLMSmartAuditTool`](https://github.com/Alex-Hofer/LLMSmartAuditTool/tree/smartbugs)
(Branch `smartbugs`, ohne `evaluation/`); die Dockerfiles im Pull Request bauen
aus dort gepinnten Commits. Nicht im Pull Request: Markerkommentare,
`mapping.md`, unsere Auswertungshilfen. Die beiden Werkzeuge stehen bewusst
nicht in `tools/all`, weil jeder Lauf Geld kostet.

Vor dem Einreichen geprüft: unter Linux 502 Tests bei 100 % Abdeckung
(Upstream: 490), `ruff` und `black` ohne Befund, `mypy` ohne neue Befunde;
unter Windows scheitern wie im Upstream 12 Tests an Pfadannahmen. Beide Images
haben wir aus den Dockerfiles des Pull Requests gebaut und durch SmartBugs
gefahren (GPTScan im Dry-Run, LLMSmartAudit gegen den Prüfstand); in
`smartbugs.json` stand nur `<redacted>`.

---

## 3. Abgleich selbst nachprüfen

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

In Git Bash `MSYS_NO_PATHCONV=1` voranstellen, sonst wird aus dem führenden `/`
im sparse-checkout-Muster ein Windows-Pfad. `diff -r` zeigt auch ungetrackte
Dateien; für die Zählung oben gilt `git ls-files`.
