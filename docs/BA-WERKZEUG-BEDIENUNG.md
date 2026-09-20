# Bedienung der beiden KI-Scanner: GPTScan und LLMSmartAudit

Diese Anleitung beschreibt, wie die beiden LLM-gestützten Scanner in diesem
Repository tatsächlich bedient werden — so, dass ein Dritter die Läufe
nachvollziehen kann. Sie beschreibt den Ist-Zustand, keinen Sollzustand.

Beide Werkzeuge werden **nicht** direkt aufgerufen, sondern über
[SmartBugs](https://github.com/smartbugs/smartbugs) als Rahmenwerk. SmartBugs
startet je Contract einen Docker-Container, sammelt dessen Ausgabe ein und
schreibt sie in einen Ergebnisordner.

---

## 1. Voraussetzungen

| Voraussetzung | Prüfen mit | Erwartung |
|---|---|---|
| Docker Desktop läuft | `cmd /c "docker info --format ""{{.ServerVersion}}"""` | Versionsnummer, z. B. `29.0.1` |
| Image GPTScan | `cmd /c "docker images"` \| `Select-String gptscan` | `smartbugs/gptscan:1.0` |
| Image LLMSmartAudit | dito mit `llmsmartaudit` | `smartbugs/llmsmartaudit:1.0` |
| API-Schlüssel | `Test-Path GPTScan\.env` | `True` |
| SmartBugs-venv | `Test-Path smartbugs\.venv\Scripts\python.exe` | `True` |

> Die stderr-Umleitung wird bewusst an `cmd /c` delegiert. PowerShell 5.1
> wandelt umgeleitete native stderr-Zeilen in ErrorRecords um, und Docker
> schreibt Warnungen auf stderr.

### Images bauen, falls sie fehlen

```powershell
# GPTScan
docker build -t smartbugs/gptscan:1.0 .\GPTScan

# LLMSmartAudit (Git Bash, nicht PowerShell)
git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main |
  docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -
```

### API-Schlüssel

Der Schlüssel steht in `GPTScan\.env` (git-ignoriert) als
`DEEPSEEK_API_KEY=...`. `run_curated.ps1` liest ihn von dort, setzt ihn als
Host-Umgebungsvariable und entfernt ihn am Ende wieder. Der Wert wird nie
ausgegeben; in `smartbugs.json` wird er durch `<redacted>` ersetzt
(`sb/docker.py`, Ende von `execute`).

### Zwei Python-Umgebungen

| Zweck | Interpreter |
|---|---|
| alles, was `sb.*` importiert (SmartBugs selbst, `sb.results2csv`, `sb.reparse`) | `smartbugs\.venv\Scripts\python.exe` |
| `analysis_tools\`, `tests\`, `evaluate_curated.py` | System-`python` |

Die venv hat kein `pytest`; das System-Python hat kein Docker-SDK. Das ist kein
Versehen, sondern die Aufgabenteilung.

---

## 2. Modellwahl — der wichtigste Fallstrick

**`LLM_MODEL=deepseek-v4-flash` ist für LLMSmartAudit Pflicht.** Das im Image
eingebrannte `deepseek-chat` ist beim Anbieter abgeschaltet; jeder Lauf ohne
diese Variable scheitert mit HTTP 400 (siehe `BA-DURCHFUEHRUNGSPROTOKOLL`,
Fehler #1). `run_curated.ps1` setzt sie selbst — beim direkten `sb`-Aufruf muss
man daran denken.

Für GPTScan gilt das Gegenstück über `GPTSCAN_PROVIDER` und `GPTSCAN_MODEL`.

Seit dem 20.09.2026 nehmen alle vier Runner die Wahl als Parameter entgegen:
`-Provider`, `-Model`, `-BaseUrl`, bei LLMSmartAudit zusätzlich `-ContextTokens`
und `-MaxCompletionTokens`; `run_curated.ps1` außerdem `-GptscanModel` und
`-LlmModel`. Die Vorgabewerte sind `deepseek` und `deepseek-v4-flash`, also die
Werte aller aufgezeichneten Läufe. Beispiele in `README.md`, Abschnitt
„Modell wählen und wechseln".

Die Werkzeuge lesen ihre Konfiguration ausschließlich aus
Host-Umgebungsvariablen, die in `smartbugs\tools\<tool>\config.yaml` unter
`env:` **einzeln freigeschaltet** sein müssen:

| Werkzeug | freigeschaltete Variablen |
|---|---|
| gptscan | `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `GPTSCAN_PROVIDER`, `GPTSCAN_MODEL`, `GPTSCAN_DRY_RUN`, `GPTSCAN_BASE_URL`, `GPTSCAN_API_KEY` |
| llmsmartaudit | `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_CONTEXT_TOKENS`, `LLM_MAX_COMPLETION_TOKENS` |

Eine Variable, die dort nicht steht, erreicht den Container nicht — auch wenn
sie auf dem Host gesetzt ist. Weitergereicht wird nur, was tatsächlich gesetzt
ist (`sb/docker.py::__docker_args`).

Ebenfalls in der `config.yaml` und ebenfalls wesentlich: **`network: bridge`**.
SmartBugs gibt Werkzeug-Containern standardmäßig `network: none`. Ohne diese
Zeile scheitert jeder API-Aufruf beider Werkzeuge — lautlos, als wäre nichts zu
finden gewesen.

---

## 3. Aufruf über `run_curated.ps1`

Der Runner ist der bequeme Weg. Er erledigt Prechecks, Schlüsselverwaltung,
Modellwahl, beide Werkzeugläufe (bewusst nacheinander) und die Auswertung.

```powershell
.\run_curated.ps1 [-Tool gptscan|llmsmartaudit|both] [-Processes N]
                  [-FilePattern 'ROOT:GLOB'] [-GptscanDry] [-SkipClone]
                  [-RunIdSuffix SUFFIX]
```

| Parameter | Bedeutung | Default |
|---|---|---|
| `-Tool` | Welches Werkzeug. `both` = erst GPTScan, dann LLMSmartAudit | `both` |
| `-Processes` | Parallele SmartBugs-Tasks | `4` |
| `-FilePattern` | Was analysiert wird, Format `ROOT:GLOB` (genau **ein** Doppelpunkt, also kein Laufwerksbuchstabe) | `..\smartbugs-curated\dataset:**/*.sol` |
| `-GptscanDry` | GPTScan ohne API-Aufrufe ($0). LLMSmartAudit wird dann übersprungen — es hat keinen Dry-Modus | aus |
| `-SkipClone` | Klonen von `smartbugs-curated` überspringen | aus |
| `-RunIdSuffix` | Ergebnisordner `results\<tool>\curated_<suffix>\` | Zeitstempel |

Fest verdrahtet, nicht über Parameter erreichbar: `--json --sarif`,
`--continue-on-errors`, Timeout 1800 s (GPTScan) bzw. 5400 s (LLMSmartAudit).

Beispiele:

```powershell
# Pipeline-Test ohne Kosten
.\run_curated.ps1 -Tool gptscan -GptscanDry -SkipClone `
  -FilePattern 'samples:gptscan/Vault.sol'

# Ein einzelner DeFi-Contract, live
.\run_curated.ps1 -Tool gptscan -SkipClone -RunIdSuffix demo `
  -FilePattern 'samples\gptscan\mwevariety_fixed:20_Synth.sol'
```

### Mehrere ausgewählte Dateien: `.sbd`-Listen

`-FilePattern` nimmt genau ein Glob-Muster, und SmartBugs benutzt Pythons
`glob` — das kennt **keine** Klammer-Alternativen wie `{a,b}`. Wer eine
gezielte Auswahl statt „alles" oder „eine Datei" braucht, nutzt eine
`.sbd`-Datei: eine Textdatei mit einem Pfad je Zeile
(`sb/smartbugs.py::collect_files`).

```
access_control/FibonacciBalance.sol
arithmetic/integer_overflow_1.sol
```

Aufruf — die Liste wird relativ zum **Arbeitsverzeichnis** gesucht
(`smartbugs\`), ihre Zeilen dagegen relativ zu `ROOT` aufgelöst:

```powershell
.\run_curated.ps1 -Tool gptscan -SkipClone -RunIdSuffix demo_swc `
  -FilePattern '..\smartbugs-curated\dataset:..\demolauf_satzA.sbd'
```

Der Pfad einer Zeile bestimmt zugleich den Ergebnispfad (`${RELDIR}`). Für den
`smartbugs-curated`-Datensatz muss die Kategorie deshalb Teil der Zeile sein,
sonst findet `evaluate_curated.py` die Ground Truth nicht mehr.

---

## 4. Aufruf direkt über `sb`

Ohne Runner — dann sind Schlüssel und Modellwahl Handarbeit:

```powershell
$env:DEEPSEEK_API_KEY = '...'          # nicht ins Terminal-Log geraten lassen
$env:GPTSCAN_PROVIDER = 'deepseek'
$env:GPTSCAN_MODEL    = 'deepseek-v4-flash'

Push-Location smartbugs
& '.\.venv\Scripts\python.exe' -m sb `
    -t gptscan `
    -f '..\smartbugs-curated\dataset:**/*.sol' `
    --json --sarif `
    --timeout 1800 `
    --processes 4 `
    --continue-on-errors `
    --results 'results/${TOOL}/mein_lauf/${RELDIR}/${FILENAME}' `
    --runid mein_lauf
Pop-Location
```

Für LLMSmartAudit stattdessen:

```powershell
$env:LLM_PROVIDER       = 'deepseek'
$env:LLM_MODEL          = 'deepseek-v4-flash'   # Pflicht, siehe Abschnitt 2
$env:LLM_CONTEXT_TOKENS = '65536'
# ... -t llmsmartaudit --timeout 5400
```

Die wichtigsten `sb`-Optionen:

| Option | Bedeutung |
|---|---|
| `-t, --tools` | Werkzeuge (mehrere möglich) |
| `-f, --files` | Muster, mehrere möglich; `DIR:` als Präfix für Suche relativ zu `DIR` |
| `--processes N` | Parallelität (Default 1) |
| `--timeout N` | Sekunden **je Task**. LLMSmartAudit braucht ≥ 3600 |
| `--continue-on-errors` | Tasks mit Kompositionsfehlern überspringen statt abbrechen |
| `--json` / `--sarif` | Ausgabe parsen und `result.json` / zusätzlich `result.sarif` schreiben |
| `--results DIR` | Ergebnispfad-Vorlage mit `${TOOL}`, `${RUNID}`, `${RELDIR}`, `${FILENAME}` |
| `--runid ID` | Name des Laufs; bestimmt auch `results\logs\<ID>.log` |
| `--overwrite` | Vorhandene Ergebnisse löschen und neu rechnen |
| `--main` | Nur den Contract analysieren, der wie die Datei heißt |
| `--quiet`, `--debug` | Konsolenausgabe unterdrücken bzw. erweitern |

Die Vorlagen-Variablen in `--results` müssen in **einfachen**
Anführungszeichen stehen, sonst expandiert PowerShell `${TOOL}` selbst zu einer
leeren Zeichenkette.

Ohne `--overwrite` werden vorhandene Task-Ordner nicht neu berechnet. Ein
neuer `--runid` bzw. `-RunIdSuffix` ist deshalb der sichere Weg zu einem
frischen Lauf, ohne alte Ergebnisse zu gefährden.

---

## 5. Wo die Ergebnisse landen

```
smartbugs\results\<tool>\<lauf>\<RELDIR>\<contract>.sol\
        result.log       result.tar       smartbugs.json
        result.json      result.sarif
smartbugs\results\logs\<runid>.log
```

Je Task fünf Dateien:

| Datei | Inhalt | wofür |
|---|---|---|
| `result.log` | **Rohe** stdout/stderr des Containers, Zeile für Zeile | Die Wahrheit. Alles andere ist daraus abgeleitet |
| `result.tar` | Die vom Werkzeug geschriebene Ergebnisdatei (`/output.json`), als Archiv eingesammelt | Der strukturierte Werkzeugbericht |
| `smartbugs.json` | SmartBugs' eigene Sicht: Task, Zeiten, Exit-Code, Docker-Argumente (Schlüssel `<redacted>`) | Laufzeit, Exit-Code, Reproduktion |
| `result.json` | Ergebnis des SmartBugs-Parsers: `findings`, `infos`, `errors`, `fails` | Die auswertbare Form |
| `result.sarif` | Dieselben Findings im SARIF-Format | Werkzeugübergreifende Weiterverarbeitung |

Reihenfolge beim Lesen eines auffälligen Tasks: erst `result.log`, dann
`smartbugs.json` (Exit-Code), dann `result.json`. Wer mit `result.json`
anfängt, sieht nur, was der Parser durchgelassen hat.

`errors` und `fails` bedeuten nicht dasselbe: `error` heißt, das Werkzeug hat
ein Problem bemerkt, behandelt und weitergearbeitet; `fail` heißt, eine
Ausnahme ist entkommen oder der Lauf wurde abgebrochen. Hergeleitet aus
`sb/parse_utils.py::errors_fails`, ausführlich in `BA-ERRORS-VS-FAILS.md`.

---

## 6. Auswertung

```powershell
# Errors/Fails je Lauf und Werkzeug, mit Meldung im Wortlaut
python analysis_tools\errors_fails_report.py smartbugs\results\<tool>\<lauf> `
    --md bericht.md --csv bericht.csv

# Prüfen, dass keine Rohmeldung aus result.log im Parser verlorengeht
python analysis_tools\parser_audit.py smartbugs\results\<tool>\<lauf>

# Nur mit Ground Truth sinnvoll (smartbugs-curated).
# --suffix ist PFLICHT und meint den RunIdSuffix, nicht den Ordnernamen.
python evaluate_curated.py --suffix v1_20260705 --tools gptscan llmsmartaudit --csv

# Tabellarische Gesamtsicht
Push-Location smartbugs
& '.\.venv\Scripts\python.exe' -m sb.results2csv results\gptscan\<lauf> > ..\ergebnis.csv
Pop-Location
```

> **Vorsicht bei `evaluate_curated.py` und Teilläufen.** Das Skript rechnet
> immer gegen die vollen 143 Contracts der Ground Truth. Wurden nur fünf
> analysiert, meldet es `result.json: 5 (fehlend: 138)`, und alle Recall-,
> Precision- und F1-Werte beziehen sich trotzdem auf 143 — sie sind dann
> **nicht** interpretierbar. Aussagekräftig bleibt in diesem Fall nur die
> Spalte `Erkannt` (wie viele der gelabelten Contracts das Werkzeug traf) und
> die Zeile darunter mit `DASP-mapped` / `unmapped`.

`run_curated.ps1` ruft `errors_fails_report.py` am Ende selbst auf und legt
zusätzlich zwei Manifeste unter `smartbugs\results\` ab:

* `curated_compile_failures_<suffix>.csv` — Contracts mit Compile-Fehler oder
  Timeout. Dort ist ein leeres Finding-Ergebnis **unbestimmt, nicht sauber**.
* `curated_review_candidates_<suffix>.csv` — Contracts, bei denen GPTScans
  statische Stufe LLM-Kandidaten verworfen hat. Das ist meist das
  bestimmungsgemäße False-Positive-Filtering, **kein** Ausschlussgrund.

> `python -m sb.reparse` nur mit `--sarif` aufrufen. Ohne diese Option löscht
> es vorhandene SARIF-Dateien ersatzlos.

---

## 7. Fallstricke

**Werkzeuge**

* `network: bridge` in der `config.yaml` ist zwingend — sonst kein API-Zugang.
* `env:`-Allowlist: Nicht gelistete Variablen erreichen den Container nie.
* LLMSmartAudit braucht `--timeout` ≥ 3600 s (gemessener Median 264 s je
  Contract, Maximum 923 s) und hat **keine** Kostenbremse. GPTScan hat eine.
* LLMSmartAudit weist **keine** Kosten aus. GPTScan schreibt eine Zeile
  `GPTSCAN_META {...}` mit `estimated_cost` in `result.log`.

**Windows / Docker**

* SmartBugs legt je Task ein Temp-Verzeichnis an, mountet es in den Container
  und löscht es danach. Docker Desktop hält den Mount kurz nach dem Entfernen
  des Containers noch, sodass das Löschen mit `WinError 5` scheitern kann.
  `sb/docker.py::rmtree_retry` wiederholt das Löschen deshalb. Ohne diese
  Wiederholung stirbt der Worker-Prozess, **bevor** Ergebnisse geschrieben
  werden — bei Exit-Code 0 und ohne Fehlermeldung. Siehe
  `BA-DEMOLAUF-ERGEBNIS.md`, Abschnitt 2.

**PowerShell 5.1**

* Kein `&&` / `||` → `A; if ($?) { B }`.
* Umgeleitetes natives stderr wird zu ErrorRecords. Umleitungen an `cmd /c`
  delegieren oder ganz vermeiden.
* `run_curated.ps1` schreibt die Werkzeugausgabe mit `Out-Host` direkt an die
  Konsole. `Tee-Object` bekommt davon nichts zu sehen — zum Protokollieren
  `Start-Transcript` verwenden oder den Runner als Kindprozess starten und
  dessen Ausgabe per `cmd /c "... > datei 2>&1"` umleiten.
* `>` schreibt ein BOM → beim Wiedereinlesen `encoding="utf-8-sig"`.
* `Select-Object -First N` beendet den Producer und liefert Exit-Code 255. Das
  ist kein Fehler des Befehls.

---

## 8. Timeout-Verhalten und Prüfstand (AP5)

Seit AP5 wirkt `--timeout` **innerhalb** des Containers, nicht mehr nur als
äußerer Docker-Abschuss. Der jeweilige Entrypoint rechnet aus dem übergebenen
`TIMEOUT` drei Marken: **Bremse** bei 70 % (als `SB_DEADLINE_EPOCH` exportiert;
nur **GPTScan** liest sie, stellt danach neue LLM-Aufrufe ein und läuft
regulär aus. **LLMSmartAudit liest `SB_DEADLINE_EPOCH` nicht** — der Export
ist dort absichtlich wirkungslos, exportiert nur, damit beide Entrypoints
dieselbe Marken-Rechnung teilen), **Netz** bei 90 % (`timeout` beendet den
Prozess hart, Exit-Code wird einheitlich auf 124 normalisiert — bei
LLMSmartAudit ist das die **einzige** wirksame Stufe; der Entrypoint birgt
danach den Zwischenstand, den `audit_report.record()` nach jeder
Detektor-Phase abgelegt hat), Rest fürs Aufräumen. `--timeout 0` bzw. kein
`--timeout` schaltet den Mechanismus vollständig ab — Verhalten wie vor AP5.

### Ein Teilergebnis erkennen

* `sb_timeout` auf oberster Ebene des Reports:
  `{"hit": true, "stage": "brake"|"net", "detail": "..."}`. Fehlt das Feld,
  war der Lauf vollständig.
* In `result.json`: ein Eintrag in `errors` mit Präfix `TIMEOUT_`
  (`TIMEOUT_BRAKE`/`TIMEOUT_NET`) — **nicht** in `fails`, da der Lauf
  absichtlich beendet wurde.
* Bei LLMSmartAudit zusätzlich `categories_checked < categories_total`
  (von 41) im Report. `categories_checked == 0` wird unabhängig vom
  Timeout-Marker als `errors` gemeldet, damit eine leere Findings-Liste nie
  als „sauber" gelesen wird.

### Prüfstand starten

Keines der beiden Werkzeuge kennt einen Offline-Modus (LLMSmartAudit schickt
selbst `LLM_MODEL=STUB` wörtlich an die API). Der lokale Ersatz-Endpunkt macht
den Timeout-Pfad trotzdem kostenlos und wiederholbar testbar:

```powershell
python -m testing_tools.fake_llm_endpoint --port 8099 --delay 30
```

Aus dem Container heraus ist der Host unter `host.docker.internal` erreichbar:

```powershell
$env:LLM_PROVIDER  = 'custom'
$env:LLM_BASE_URL  = 'http://host.docker.internal:8099'
# ... -t llmsmartaudit --timeout 60
```

```powershell
$env:GPTSCAN_PROVIDER  = 'custom'
$env:GPTSCAN_BASE_URL  = 'http://host.docker.internal:8099'
# ... -t gptscan --timeout 60
```

Beide `custom`-Provider sind mit Preis `0` hinterlegt, ein Lauf gegen den
Prüfstand kann also nicht versehentlich Kosten auslösen.

> **Nachgetragen (Commit `a2611ea`).** `LLM_BASE_URL` steht bereits in
> `smartbugs/tools/llmsmartaudit/config.yaml`s `env:`-Allowlist (Abschnitt 2)
> und erreicht den Container damit. `GPTSCAN_BASE_URL` fehlte zunächst in
> `smartbugs/tools/gptscan/config.yaml`s `env:`-Zeile; das ist behoben — sie
> führt inzwischen auch `GPTSCAN_BASE_URL` und `GPTSCAN_API_KEY`, ein `sb -t
> gptscan`-Lauf bekommt die Basis-URL damit in den Container gereicht.
> Getestet ist der Override auf Ebene von `GPTScan/src/llm_backend.py`
> (`tests/test_gptscan_deadline.py`). Weiter reicht der Nachweis auf dem Host
> nicht: `main.py` zieht über `analyze_pipeline`/`chatgpt_api` die Pakete
> `openai`, `tiktoken` und `rich`, die auf dem Host nicht installiert sind —
> ein direkter, nicht containerisierter Aufruf ist dort schlicht nicht
> lauffähig. Der durchgehende Pfad ist damit container-only; belegt ist er
> inzwischen durch den `sb -t gptscan`-Lauf gegen den Prüfstand in Abschnitt
> 4.5 von `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` (siehe unten).

Belegt ist der Mechanismus durch 32 eigene Tests in einer grünen Suite
(`python -m pytest tests/ -q`) und die Vorprüfung des `timeout`-Kommandos in
beiden Images (`docs/BA-AP5-VORPRUEFUNG.md`). Der Messlauf gegen einen echten,
tatsächlich ablaufenden Endpunkt ist erledigt (Commit `43c3f32`): siehe
Abschnitt 4.5 in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` — je ein Contract pro
Werkzeug, Nachweis dass ein Teillauf nichts erfindet, nicht wie viel er im
Mittel verpasst (dortige Limitation 7).
