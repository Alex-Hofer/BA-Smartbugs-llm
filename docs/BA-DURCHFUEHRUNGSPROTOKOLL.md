# Durchführungsprotokoll: Evaluation KI-gestützter Smart-Contract-Scanner

**Zeitraum:** 05.–06.07.2026 · **Umgebung:** Windows 11, Docker Desktop (Linux-Engine), SmartBugs 2.1.1 (Python 3.13, venv), LLM-Backend DeepSeek `deepseek-v4-flash`
**Evaluierte Tools:** GPTScan (LLM + statische Bestätigung, 10 DeFi-Logik-Regeln MWE-200..209) · LLMSmartAudit (ChatDev/CAMEL-Multi-Agent-Pipeline, 41 Detektor-Prompts) · Slither 0.11.3 (statische Baseline)
**Datensätze:** [smartbugs-curated](https://github.com/smartbugs/smartbugs-curated) (143 Contracts, 10 DASP-Kategorien, Single-Label-Ground-Truth) · `smartbugs/samples/gptscan/mwevariety` (96 DeFi-Contracts aus GPTScans eigenem Benchmark-Umfeld, ohne vendorte Ground Truth)

---

## 1. Vorgehen (Überblick)

Mehrstufiger, gate-gesicherter Testlauf, dann Massenevaluation:

1. **Phase 0 — Setup:** Docker-Images prüfen/bauen, API-Key-Handling verifizieren.
2. **Phase 1 — Smoke-Test „dry"** ($0): Pipeline/Parser-Test ohne echte API-Calls.
3. **Gate-Review** (adversarial): unabhängige Verifikation aller Phase-1-Ergebnisse als Go/No-Go vor kostenpflichtigen Live-Calls.
4. **Phase 2 — Smoke-Test „live":** beide Tools auf 3 Contracts mit echten API-Calls.
5. **Phase 3 — Analysen:** Parser-/SARIF-Validierung, Rate-Limit-/Timing-/Kosten-Forensik.
6. **Phase 4 — Automatisierung:** Massentest-Skript `run_curated.ps1` (geschrieben, reviewed, per Trockentest verifiziert).
7. **Massenläufe:** GPTScan + LLMSmartAudit über curated (143), Slither-Baseline (143), GPTScan über mwevariety (96).
8. **Auswertung:** quantitativ (`evaluate_curated.py`: Recall/Precision/F1 pro DASP-Kategorie, Contract-Level) + qualitative Stichproben am Quellcode.

Alle Läufe erfolgten über die SmartBugs-Integration (`smartbugs/tools/{gptscan,llmsmartaudit}/`), d. h. dockerisiert, mit standardisierten Ausgaben (result.json + SARIF) und Key-Redaction in den persistierten Metadaten.

## 2. Setup-Besonderheiten

- **LLMSmartAudit-Image** (`smartbugs/llmsmartaudit:1.0`) wurde ohne Working-Tree-Checkout direkt aus git HEAD gebaut (Windows-Langpfad-Problematik):
  `git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main | docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -`
- **API-Key-Handling:** Key liegt ausschließlich lokal (`GPTScan/.env`, git-ignoriert); SmartBugs forwarded ihn zur Laufzeit als Env-Variable in den Container und ersetzt ihn vor dem Persistieren durch `<redacted>` (verifiziert in allen neuen Läufen).
- **Netzwerk:** SmartBugs isoliert Tool-Container standardmäßig (`network: none`); die beiden LLM-Tools nutzen den dokumentierten Opt-in `network: bridge` (nur diese Container haben API-Zugriff).

## 3. Fehler, Diagnosen und Behebungen (chronologisch)

| # | Problem | Symptom | Diagnose | Behebung |
|---|---|---|---|---|
| 1 | Totes LLM-Modell im LLMSA-Image | Jeder Lauf wäre mit HTTP 400 gescheitert | Stub-Experiment (`LLM_MODEL=STUB`) zeigte: der Modellname geht verbatim an die DeepSeek-API; deren Fehlermeldung nannte nur noch `deepseek-v4-pro/flash` als gültig — das im Image eingebrannte `deepseek-chat` ist abgeschaltet. Code-Analyse (run.py/model_backend.py) bestätigte den Datenfluss | Host-seitig `LLM_MODEL=deepseek-v4-flash` setzen (überschreibt Image-ENV); kein Rebuild nötig |
| 2 | Kein Offline-/Stub-Modus bei LLMSA | „Stub"-Testlauf erzeugte echte (abgelehnte) API-Roundtrips | `run.py` mappt `--model` unter provider=deepseek nie auf das interne StubModel | Akzeptiert & dokumentiert; Dry-Testing nur über GPTScans `GPTSCAN_DRY_RUN=1` |
| 3 | Korrupte Test-Samples | `_chk/20_Pool.sol`: solc `extraneous input '<EOF>'` | Ab Z. 22 fehlen alle Zeilenumbrüche → `//`-Kommentar verschluckt den Restvertrag; 4 von 6 `_chk`-Dateien betroffen (Ein-Zeilen-Blobs) | Für den Smoke-Test Austausch gegen `74_TimeswapPair.sol` (wohlgeformt; hatte dennoch einen echten solc-Fehler Z. 51 → GPTScan degradierte nachweislich graceful auf LLM-only) |
| 4 | **Silent Failure bei GPTScan** | Compile-Fehler erscheinen NUR im result.log; result.json zeigt `errors=[]`, 0 Findings — ununterscheidbar von „sauber, nichts gefunden" | Verifiziert an zwei Fällen; drei ununterscheidbare Zustände identifiziert (sauber / compile-failed / degradiert) | Massentest-Skript erzeugt Post-Run-Manifeste aus den Logs (`curated_compile_failures_*.csv`, `curated_review_candidates_*.csv`); Parser-Fix als Empfehlung dokumentiert |
| 5 | PowerShell-5.1-Falle: stderr-Umleitung | `docker info *> $null` warf `NativeCommandError` (Docker-WARNING auf stderr + `$ErrorActionPreference='Stop'`) | PS 5.1 wandelt umgeleitete native stderr-Zeilen in ErrorRecords | Umleitung an `cmd /c` delegiert |
| 6 | Exit-Code-Capture-Bug im Skript | „ExitCode=Welcome to SmartBugs…" | PowerShell-Funktionen geben den gesamten Pipeline-Output zurück, nicht nur `return`-Werte | sb-Ausgabe via `\| Out-Host` zur Konsole; nur `$LASTEXITCODE` zurückgeben |
| 7 | Fehlalarm im Degradations-Manifest (Dry-Run) | Dry-Testlauf flaggte intakten Contract als „degradiert" | Im Dry-Run läuft die Static-Bestätigung nie → Signatur dort bedeutungslos | `dry_run`-Guard in der Manifest-Logik |
| 8 | Manifest-Übermeldung (Review) | „Degraded"-Signatur hätte ~48 % der Live-Contracts geflaggt | `vul_before_static > vul_after_static` ist GPTScans **bestimmungsgemäßes** False-Positive-Filtering, kein Defekt | Umbenennung in „Review-Kandidaten" (manuelle Nachprüfung, kein Automatik-Ausschluss); Log-Meldungen entsprechend präzisiert |
| 9 | DASP-Mapping-Lücken (Slither) | `time_manipulation`-Recall fälschlich 0 % | Slithers `timestamp`- und `weak-prng`-Detektoren tragen in SmartBugs' findings.yaml keine Klassifikation | Konservatives, dokumentiertes Zusatz-Mapping in `evaluate_curated.py` (timestamp→DASP-8, weak-prng→DASP-6) |
| 10 | DASP-Mapping-Lücken (LLMSA) | 4 der 5 verpassten Contracts | curated-Kategorien „other" (= uninitialized storage pointer, SWC-109) und „short_addresses" haben kein Gegenstück unter den 41 Detektoren bzw. im DASP-Schema | Als Taxonomie-Limitation dokumentiert (kein Tool-Fehler); 3 unmapped Findings waren sogar korrekte Primär-Vuln-Treffer |
| 11 | Slither-Engine-Crashes | 3/143 Tasks (2,1 %) mit `EXIT_CODE_1` | 2× `AssertionError` im IR-Generator (Legacy-Muster `(bool success, ) = x.call.value(v)("")`), 1× `NotConstant` (`Request[2**64]`) — keine solc-Probleme | Als Tool-Grenzfälle dokumentiert; `--continue-on-errors` fing sie sauber ab |
| 12 | mwevariety-Korpus großteils nicht kompilierbar | 95/96 „InvalidCompilation"; 22/96 Tool-interne Python-Crashes (TypeError/UnboundLocalError) | Einzeln extrahierte Benchmark-Dateien ohne Import-/Dependency-Baum; die Crashes sind Folgefehler der fehlgeschlagenen Kompilierung | Dokumentiert: GPTScan lief dort überwiegend im degradierten LLM-only-Modus (statische Bestätigung inaktiv); leere Fehler-results wurden korrekt erzeugt |
| 13 | Klartext-Key in Alt-Ergebnissen | 62 lokale Ergebnisdateien früherer Läufe enthielten den API-Key | Redaction wurde erst mit der SmartBugs-Integration eingeführt; Alt-Läufe davor betroffen. Nie git-getrackt, nie veröffentlicht | Verifiziert, dass alle neuen Läufe redigieren; Key-Rotation + Scrubbing vor jeder Weitergabe der results als Auflage dokumentiert |

## 4. Ergebnisse

### 4.1 smartbugs-curated (143 Contracts, Contract-Level, DASP-Mapping)

| Tool | Recall | Precision | F1 | Findings (DASP-mapped) | Kosten | Laufzeit |
|---|---|---|---|---|---|---|
| Slither 0.11.3 | 64 % | 45 % | 52 % | 2 154 (300) | $0 | 1:24 min |
| LLMSmartAudit | **97 %** | 30 % | 45 % | 1 124 (656) | $2.44 | 3:02 h |
| GPTScan | 0 %* | – | – | 6 (6) | $0.01 | 3:19 min |

\* by design: GPTScan adressiert ausschließlich DeFi-Logik-Schwachstellen, nicht die klassischen SWC-Klassen des Datensatzes. Nur 16/143 Contracts passierten den Keyword-Vorfilter; die 6 Findings (alle MWE-207) lagen auf real-world Contracts mit anderem Primär-Label.

**LLMSmartAudit pro Kategorie** (Recall / Precision / F1): unchecked_low_level_calls 100/79/88 · reentrancy 100/43/60 · bad_randomness 88/44/58 · time_manipulation 100/26/42 · arithmetic 100/20/33 · access_control 100/19/32 · front_running 100/9/16 · denial_of_service 100/8/14 · other 0/–/– · short_addresses 0/–/–. Finding-Dichte: Ø 7,9/Contract (Median 7, Max 18); **kein Contract blieb ohne Findings**.

**Slither pro Kategorie** (Auszug): reentrancy 94/74/83 · unchecked_low_level_calls 88/59/71 · time_manipulation 100/21/34 · arithmetic und front_running 0 % (keine passenden Detektoren). 89,5 % der 2 154 Slither-Findings sind Stil-/Info-Meldungen ohne DASP-Kategorie.

### 4.2 Qualitative Einordnung (Stichproben am Quellcode verifiziert)

- **LLMSA-Misses:** 4 von 5 sind Taxonomie-Artefakte (Fehler #10), nur 1 echter Detektions-Fehler (`smart_billions.sol`, PredictableRand-Detektor feuerte nicht). Bemerkenswert: Auf demselben Contract verwarf auch GPTScans Static-Stufe 2 LLM-Kandidaten.
- **LLMSA-„False Positives":** Stichprobe 19 Extra-Kategorie-Treffer → **15 plausibel / 4 generisch / 0 falsch**; Stichprobe 10 unmapped → 8 plausibel / 2 generisch. Die gemessene Precision (30 %) unterschätzt die tatsächliche deutlich, weil curated nur EINE Primär-Schwachstelle pro Contract labelt und das DASP-Mapping standardkonforme SWC-Findings ohne DASP-Nummer verwirft.
- **Severity-Caveat:** Über alle 1 124 LLMSA-Findings ist die Severity je Detektorname zu 100 % konstant → dokumentations-zugewiesene Kategorie-Defaults, keine Einzelfall-Urteile des Modells.
- **GPTScan-Review-Kandidaten (curated):** Alle 4 geprüft — die Static-Stufe lief und verwarf 5 LLM-Kandidaten bestimmungsgemäß (False-Positive-Filtering, kein Datenproblem).

### 4.3 GPTScan auf Zieldomäne (mwevariety, 96 DeFi-Contracts)

- **11 Findings auf 7 Contracts** (alle high): MWE-200 „Insecure LP Token Value" ×6, MWE-207 ×2, MWE-209 ×2, MWE-203 ×1 — im Kontrast zu 0 themengerechten Findings auf curated.
- Qualitative Stichprobe (6 Findings): **4 plausibel** (u. a. `slot0`-Spotpreis als Flashloan-Vektor, nie zurückgesetzte NFT-Approval), 1 generisch, 1 falsch.
- **Reproduzierbarkeit:** Vergleich mit einem früheren Live-Lauf über dieselben 27 Contracts: nur **74 % identische Ergebnisse** (3 Findings verschwunden, 2 neu, 2 verändert) — trotz `temperature=0`. Zentrale Limitation LLM-basierter Scanner.
- Kosten $0.046, Laufzeit 13:22 min, 257 LLM-Calls, keine Rate-Limits. Caveats des Korpus siehe Fehler #12; keine vendorte Ground Truth → deskriptive + qualitative Auswertung.

### 4.4 Betriebs-/Robustheitsdaten

- **Keine Rate-Limits** über ~6 640 DeepSeek-API-Calls gesamt (6 174 LLMSA-curated + 129 LLMSA-Smoke + 257 + 72 + 9 GPTScan); keine Retries nötig (LLMSA nutzt tenacity-Backoff, GPTScan fixe 30-s-Retries — beides wurde nie ausgelöst).
- Validierte Parameter: `--processes 4`; Timeouts 1 800 s (GPTScan) / 5 400 s (LLMSA); Läufe sequenziell; `LLM_CONTEXT_TOKENS=65536` als Versicherung.
- **Gesamtkosten aller Experimente: ≈ $2.55** (Smoke $0.06 + curated GPTScan $0.01 + curated LLMSA $2.44 + mwevariety $0.05); Slither $0. Alle Kostenwerte aus den Token-Zahlen der Logs bzw. GPTScans eigenem Kosten-Estimator nachgerechnet.

## 5. Methodische Limitationen

1. **Single-Label-Ground-Truth:** curated annotiert eine Primär-Schwachstelle pro Contract; echte Sekundär-Befunde zählen als False Positives → Precision-Werte sind Untergrenzen.
2. **DASP-only-Mapping:** Findings ohne DASP-Klassifikation (LLMSA: 468; Slither: 1 854) fließen nicht in Recall/Precision ein; zwei kanonische Zusatz-Mappings wurden dokumentiert ergänzt (Fehler #9).
3. **Nicht-Determinismus:** 74 % Lauf-zu-Lauf-Übereinstimmung bei GPTScan (4.3); LLMSA-Ergebnisse sind ebenfalls nicht deterministisch (nicht separat quantifiziert).
4. **Degradierte Static-Stufe:** Auf mwevariety war GPTScans Präzisions-Schutzmechanismus mangels kompilierbarer Dateien überwiegend inaktiv.
5. **Severity-Werte** beider LLM-Tools sind Kategorie-Defaults (4.2) — severity-gewichtete Metriken wären irreführend.
6. **Contract-Level-Metrik:** Bei hoher Finding-Dichte (LLMSA Ø 7,9) ist Contract-Level-Recall wohlwollend; Zeilen-genaue Auswertung war nicht möglich, da LLMSA keine Zeilennummern emittiert.

## 6. Artefakte & Reproduktion

| Artefakt | Pfad |
|---|---|
| Massentest-Skript | `run_curated.ps1` (Repo-Root; Prechecks, sequenzielle Läufe, Manifeste, Kosten-Summe) |
| Auswertung | `evaluate_curated.py` (Recall/Precision/F1 pro DASP-Kategorie, Detail-CSV) |
| Ergebnisse | `smartbugs/results/{gptscan,llmsmartaudit,slither-0.11.3}/curated_v1_20260705/` · `smartbugs/results/gptscan/curated_mwe_20260706/` (lokal, git-ignoriert) |
| Manifeste/CSVs | `smartbugs/results/curated_*_v1_20260705.csv` · `evaluation_curated_v1_20260705.csv` · `curated_results.csv` |
| Tool-Integration | `smartbugs/tools/{gptscan,llmsmartaudit}/{config.yaml,findings.yaml,parser.py,scripts/}` |

Reproduktion: `.\run_curated.ps1` (Volllauf beide Tools) bzw. `-Tool gptscan|llmsmartaudit`, danach `smartbugs\.venv\Scripts\python.exe evaluate_curated.py --suffix <RunIdSuffix> --csv`. Voraussetzungen: Docker Desktop, lokal gebaute Images, `DEEPSEEK_API_KEY` in `GPTScan/.env`.

> Hinweis: Die Durchführung erfolgte KI-gestützt über ein Multi-Agent-Setup; Architektur und Erfahrungen dazu sind separat dokumentiert in `docs/BA-AGENT-WORKFLOW.md`.
