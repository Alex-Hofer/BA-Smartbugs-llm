# Bedienung der LLM-Scanner GPTScan und LLMSmartAudit

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

So bedienen wir die beiden Scanner in diesem Repository, beschrieben so, dass
man unsere Läufe nachvollziehen kann. Wir rufen sie **nicht** direkt auf,
sondern über [SmartBugs](https://github.com/smartbugs/smartbugs): Je Contract
startet ein Docker-Container, SmartBugs sammelt die Ausgabe ein und schreibt
sie in einen Ergebnisordner.

---

## 1. Voraussetzungen

| Voraussetzung | Prüfen mit | Erwartung |
|---|---|---|
| Docker Desktop läuft | `cmd /c "docker info --format ""{{.ServerVersion}}"""` | Versionsnummer |
| Image GPTScan | `cmd /c "docker images"` \| `Select-String gptscan` | `smartbugs/gptscan:1.0` |
| Image LLMSmartAudit | dito mit `llmsmartaudit` | `smartbugs/llmsmartaudit:1.0` |
| Image Slither glibc (nur DeFi-Korpus) | dito mit `slither` | `smartbugs/slither:0.11.3-glibc` ([`BA-BETRIEB.md`](BA-BETRIEB.md), Fallstrick 10) |
| API-Schlüssel | `Test-Path GPTScan\.env` | `True` |
| SmartBugs-venv | `Test-Path smartbugs\.venv\Scripts\python.exe` | `True` |

Fehlt etwas: README, „Umgebung anlegen“ und „Images bauen“. Docker-Befehle
laufen über `cmd /c`, weil PowerShell 5.1 umgeleitetes stderr in ErrorRecords
verwandelt und Docker Warnungen auf stderr schreibt.

**API-Schlüssel.** Er steht in `GPTScan\.env` (git-ignoriert) als
`DEEPSEEK_API_KEY=...`. `run_curated.ps1` setzt ihn für die Dauer des Laufs als
Host-Variable; in `smartbugs.json` steht nur `<redacted>`.

**Zwei Python-Umgebungen.** Alles, was `sb.*` importiert (SmartBugs,
`sb.results2csv`, `sb.reparse`), läuft in `smartbugs\.venv`; `analysis_tools\`,
`tests\` und `evaluate_curated.py` laufen im System-Python. Die venv hat kein
`pytest`, das System-Python kein Docker-SDK — das ist so gewollt.

---

## 2. Modellwahl — der wichtigste Fallstrick

**`LLM_MODEL=deepseek-v4-flash` ist für LLMSmartAudit Pflicht.** Das früher im
Image eingebrannte `deepseek-chat` hat der Anbieter abgeschaltet; ohne die
Variable bricht der Entrypoint seit dem 24.09.2026 sofort mit Exit 2 ab
([`BA-BETRIEB.md`](BA-BETRIEB.md), Fallstrick 2). `run_curated.ps1` setzt sie
selbst, beim direkten `sb`-Aufruf muss man daran denken. Für GPTScan gilt
dasselbe über `GPTSCAN_PROVIDER` und `GPTSCAN_MODEL`.

Alle vier Runner nehmen die Wahl als Parameter: `-Provider`, `-Model`,
`-BaseUrl`, bei LLMSmartAudit zusätzlich `-ContextTokens` und
`-MaxCompletionTokens`; `run_curated.ps1` außerdem `-GptscanModel` und
`-LlmModel`. Default ist `deepseek` / `deepseek-v4-flash` wie in allen unseren
Läufen (Beispiele: README, „Modell wählen und wechseln“).

In den Container gelangt nur, was in `smartbugs\tools\<tool>\config.yaml` unter
`env:` steht **und** auf dem Host gesetzt ist:

| Werkzeug | freigegebene Variablen |
|---|---|
| gptscan | `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `GPTSCAN_PROVIDER`, `GPTSCAN_MODEL`, `GPTSCAN_DRY_RUN`, `GPTSCAN_BASE_URL`, `GPTSCAN_API_KEY` |
| llmsmartaudit | `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_CONTEXT_TOKENS`, `LLM_MAX_COMPLETION_TOKENS` |

Ebenso wichtig: **`network: bridge`** in der `config.yaml`. SmartBugs gibt
Containern standardmäßig kein Netz — ohne die Zeile scheitert jeder API-Aufruf,
und zwar lautlos, als gäbe es nichts zu finden.

---

## 3. Aufruf über `run_curated.ps1`

Der bequeme Weg: Prechecks, Schlüssel, Modellwahl, beide Werkzeuge
nacheinander und die Auswertung in einem Aufruf.

```powershell
.\run_curated.ps1 [-Tool gptscan|llmsmartaudit|both] [-Processes N]
                  [-FilePattern 'ROOT:GLOB'] [-GptscanDry] [-SkipClone]
                  [-RunIdSuffix SUFFIX]
```

| Parameter | Bedeutung | Default |
|---|---|---|
| `-Tool` | Werkzeug; `both` = erst GPTScan, dann LLMSmartAudit | `both` |
| `-Processes` | parallele Tasks | `4` |
| `-FilePattern` | `ROOT:GLOB` mit genau **einem** Doppelpunkt (kein Laufwerksbuchstabe) | `..\smartbugs-curated\dataset:**/*.sol` |
| `-GptscanDry` | GPTScan ohne API-Aufrufe; LLMSmartAudit wird übersprungen | aus |
| `-SkipClone` | `smartbugs-curated` nicht klonen | aus |
| `-RunIdSuffix` | Ergebnisordner `results\<tool>\curated_<suffix>\` | Zeitstempel |

Fest eingestellt: `--json --sarif`, `--continue-on-errors`, Timeout 1800 s
(GPTScan) bzw. 5400 s (LLMSmartAudit).

```powershell
# Pipeline-Test ohne Kosten
.\run_curated.ps1 -Tool gptscan -GptscanDry -SkipClone `
  -FilePattern 'samples:gptscan/Vault.sol'

# ein einzelner DeFi-Contract, live
.\run_curated.ps1 -Tool gptscan -SkipClone -RunIdSuffix demo `
  -FilePattern 'samples\gptscan\mwevariety_fixed:20_Synth.sol'
```

### Mehrere ausgewählte Dateien: `.sbd`-Listen

SmartBugs nutzt Pythons `glob`, das keine Alternativen wie `{a,b}` kennt. Für
eine gezielte Auswahl gibt es `.sbd`-Dateien mit einem Pfad je Zeile:

```
access_control/FibonacciBalance.sol
arithmetic/integer_overflow_1.sol
```

```powershell
.\run_curated.ps1 -Tool gptscan -SkipClone -RunIdSuffix demo_swc `
  -FilePattern '..\smartbugs-curated\dataset:..\demolauf_satzA.sbd'
```

Die Liste selbst wird relativ zu `smartbugs\` gesucht, ihre Zeilen relativ zu
`ROOT`. Weil der Zeilenpfad auch den Ergebnispfad bestimmt, muss bei
`smartbugs-curated` die Kategorie in der Zeile stehen — sonst findet
`evaluate_curated.py` die Ground Truth nicht.

---

## 4. Aufruf direkt über `sb`

Ohne Runner sind Schlüssel und Modellwahl Handarbeit:

```powershell
$env:DEEPSEEK_API_KEY = '...'          # nicht ins Terminal-Log geraten lassen
$env:GPTSCAN_PROVIDER = 'deepseek'
$env:GPTSCAN_MODEL    = 'deepseek-v4-flash'

Push-Location smartbugs
& '.\.venv\Scripts\python.exe' -m sb `
    -t gptscan `
    -f '..\smartbugs-curated\dataset:**/*.sol' `
    --json --sarif --timeout 1800 --processes 4 --continue-on-errors `
    --results 'results/${TOOL}/mein_lauf/${RELDIR}/${FILENAME}' `
    --runid mein_lauf
Pop-Location
```

Für LLMSmartAudit stattdessen:

```powershell
$env:LLM_PROVIDER       = 'deepseek'
$env:LLM_MODEL          = 'deepseek-v4-flash'   # Pflicht
$env:LLM_CONTEXT_TOKENS = '65536'
# ... -t llmsmartaudit --timeout 5400
```

| Option | Bedeutung |
|---|---|
| `-t`, `-f` | Werkzeuge bzw. Dateimuster (`DIR:`-Präfix für Suche relativ zu `DIR`) |
| `--processes N` | Parallelität (Default 1) |
| `--timeout N` | Sekunden **je Task**; LLMSmartAudit braucht ≥ 3600 |
| `--continue-on-errors` | fehlerhafte Tasks überspringen statt abbrechen |
| `--json` / `--sarif` | `result.json` bzw. zusätzlich `result.sarif` schreiben |
| `--results DIR` | Pfadvorlage mit `${TOOL}`, `${RUNID}`, `${RELDIR}`, `${FILENAME}` |
| `--runid ID` | Name des Laufs, auch für `results\logs\<ID>.log` |
| `--overwrite` | vorhandene Ergebnisse neu rechnen |
| `--main` | nur den Contract analysieren, der wie die Datei heißt |

Die Vorlage in `--results` muss in **einfachen** Anführungszeichen stehen, sonst
macht PowerShell aus `${TOOL}` einen Leerstring. Ohne `--overwrite` rechnet
SmartBugs vorhandene Tasks nicht neu — ein neuer `--runid` ist der sichere Weg
zu einem frischen Lauf.

---

## 5. Wo die Ergebnisse landen

```
smartbugs\results\<tool>\<lauf>\<RELDIR>\<contract>.sol\
        result.log  result.tar  smartbugs.json  result.json  result.sarif
smartbugs\results\logs\<runid>.log
```

| Datei | Inhalt |
|---|---|
| `result.log` | **rohe** Ausgabe des Containers — die Wahrheit, alles andere ist abgeleitet |
| `result.tar` | die Ergebnisdatei des Werkzeugs (`/output.json`) als Archiv |
| `smartbugs.json` | SmartBugs' Sicht: Zeiten, Exit-Code, Docker-Argumente (Schlüssel geschwärzt) |
| `result.json` | geparstes Ergebnis: `findings`, `infos`, `errors`, `fails` |
| `result.sarif` | dieselben Findings als SARIF |

Bei einem auffälligen Task zuerst `result.log`, dann den Exit-Code in
`smartbugs.json`, erst dann `result.json` lesen — sonst sieht man nur, was der
Parser durchgelassen hat. `error` heißt: Problem bemerkt, weitergearbeitet;
`fail` heißt: Ausnahme entkommen oder Lauf abgebrochen
([`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md)).

---

## 6. Auswertung

```powershell
# errors/fails je Lauf, mit Meldung im Wortlaut
python analysis_tools\errors_fails_report.py smartbugs\results\<tool>\<lauf> `
    --md bericht.md --csv bericht.csv

# geht eine Rohmeldung aus result.log im Parser verloren?
python analysis_tools\parser_audit.py smartbugs\results\<tool>\<lauf>

# nur mit Ground Truth (smartbugs-curated); --suffix ist der RunIdSuffix
python evaluate_curated.py --suffix v1_20260705 --tools gptscan llmsmartaudit --csv

# Gesamttabelle; Kodierung ausdrücklich setzen (BA-BETRIEB.md, 6)
Push-Location smartbugs
& '.\.venv\Scripts\python.exe' -m sb.results2csv results\gptscan\<lauf> | Out-File -Encoding utf8 ..\ergebnis.csv
Pop-Location
```

> **Vorsicht bei Teilläufen:** `evaluate_curated.py` rechnet immer gegen alle
> 143 Contracts. Bei fünf analysierten Contracts sind Recall, Precision und F1
> nicht interpretierbar; aussagekräftig bleiben nur die Spalte `Erkannt` und
> die Zeile `DASP-mapped` / `unmapped`.

`run_curated.ps1` ruft `errors_fails_report.py` selbst auf und legt zwei
Manifeste an:

* `curated_compile_failures_<suffix>.csv` — Compile-Fehler oder Timeout; ein
  leeres Ergebnis ist dort **unbestimmt, nicht sauber**.
* `curated_review_candidates_<suffix>.csv` — Contracts, bei denen GPTScans
  statische Stufe Kandidaten verworfen hat; meist gewollte Filterung.

`python -m sb.reparse` nur mit `--sarif` aufrufen, sonst löscht es vorhandene
SARIF-Dateien.

---

## 7. Fallstricke

**Werkzeuge**

* Ohne `network: bridge` kein API-Zugang; ohne Eintrag in `env:` kommt keine
  Variable im Container an.
* LLMSmartAudit braucht `--timeout` ≥ 3600 s (Median 264 s, Maximum 923 s je
  Contract), hat **keine** Kostenbremse und weist keine Kosten aus. GPTScan hat
  eine Bremse und schreibt `estimated_cost` in die Zeile `GPTSCAN_META`.

**Windows / Docker**

* Docker Desktop hält den Mount eines Task-Verzeichnisses kurz nach dem Ende
  des Containers noch fest; das Löschen scheitert dann mit `WinError 5`. Ohne
  Wiederholung starb der Worker, **bevor** Ergebnisse geschrieben waren — bei
  Exit 0 und ohne Meldung. Deshalb wiederholt `sb/docker.py` das Löschen
  ([`BA-DEMOLAUF-ERGEBNIS.md`](BA-DEMOLAUF-ERGEBNIS.md), 2).

**PowerShell 5.1**

* Kein `&&` / `||` → `A; if ($?) { B }`.
* Umgeleitetes natives stderr wird zu ErrorRecords → an `cmd /c` delegieren.
* `run_curated.ps1` schreibt mit `Out-Host` direkt an die Konsole; `Tee-Object`
  sieht davon nichts. Zum Mitschneiden `Start-Transcript` nutzen.
* `>` schreibt ein BOM → beim Einlesen `encoding="utf-8-sig"`.
* `Select-Object -First N` liefert Exit 255, weil es den Producer beendet — kein
  Fehler.

---

## 8. Timeout und Prüfstand (AP5)

Regeln und Marken stehen in [`BA-BETRIEB.md`](BA-BETRIEB.md), Abschnitt 8;
Entwurf und Nachweis in [`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md).
Kurz: Bei 70 % von `--timeout` stellt GPTScan neue LLM-Aufrufe ein, bei 90 %
beendet `timeout` den Prozess (bei LLMSmartAudit die einzige wirksame Stufe),
danach birgt der Entrypoint den Zwischenstand. `--timeout 0` schaltet alles ab.

**Teilergebnis erkennen:** Feld `sb_timeout` im Report; `TIMEOUT_BRAKE` oder
`TIMEOUT_NET` in `errors` (nie in `fails`); bei LLMSmartAudit
`categories_checked < categories_total`.

**Prüfstand starten.** Ein lokaler Endpunkt antwortet absichtlich langsam und
macht den Timeout-Pfad kostenlos testbar:

```powershell
python -m testing_tools.fake_llm_endpoint --port 8099 --delay 30
```

```powershell
# LLMSmartAudit
$env:LLM_PROVIDER = 'custom'
$env:LLM_BASE_URL = 'http://host.docker.internal:8099'
# ... -t llmsmartaudit --timeout 60

# GPTScan
$env:GPTSCAN_PROVIDER = 'custom'
$env:GPTSCAN_BASE_URL = 'http://host.docker.internal:8099'
# ... -t gptscan --timeout 60
```

Beide `custom`-Provider haben Preis 0. Den GPTScan-Pfad kann man nur im
Container testen: `main.py` braucht `openai`, `tiktoken` und `rich`, die auf
dem Host nicht installiert sind. Belegt ist der Mechanismus durch 32 Tests, die
Vorprüfung in beiden Images ([`BA-AP5-VORPRUEFUNG.md`](BA-AP5-VORPRUEFUNG.md))
und scharfe Läufe gegen einen echten Endpunkt
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), 4.5).
