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

**LLMSmartAudit pro Kategorie.** Die Spalte *Contracts* nennt, wie viele Contracts
die Ground Truth mit dieser Kategorie labelt; Recall und Precision beziehen sich
darauf.

| Kategorie | Contracts | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| unchecked_low_level_calls | 52 | 100 % | 79 % | 88 % |
| reentrancy | 31 | 100 % | 43 % | 60 % |
| bad_randomness | 8 | 88 % | 44 % | 58 % |
| time_manipulation | 5 | 100 % | 26 % | 42 % |
| arithmetic | 15 | 100 % | 20 % | 33 % |
| access_control | 18 | 100 % | 19 % | 32 % |
| front_running | 4 | 100 % | 9 % | 16 % |
| denial_of_service | 6 | 100 % | 8 % | 14 % |
| other | 3 | 0 % | – | – |
| short_addresses | 1 | 0 % | – | – |
| **Gesamt** | **143** | **97 %** | **30 %** | **45 %** |

Finding-Dichte: Ø 7,9/Contract (Median 7, Max 18); **kein Contract blieb ohne Findings**.

**Slither pro Kategorie** (Auszug): reentrancy 94/74/83 · unchecked_low_level_calls 88/59/71 · time_manipulation 100/21/34 · arithmetic und front_running 0 % (keine passenden Detektoren). 1 854 der 2 154 Slither-Findings (86,1 %) haben weder in SmartBugs' `findings.yaml` noch über die beiden Zusatz-Mappings (Fehler #9) eine DASP-Zuordnung und gehen deshalb nicht in Recall und Precision ein (Abschnitt 5, Punkt 2). Keine Zuordnung heißt nicht belanglos: Nach der Impact-Stufe des jeweiligen Detektors sind 1 480 davon Informational oder Optimization, 166 Low, 148 Medium und 60 High.

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

### 4.5 AP5 — Nachweis des Timeout-Verhaltens (18.08.2026)

Bis AP5 hatte SmartBugs' `--timeout` für die beiden LLM-Werkzeuge keine Wirkung
außer dem harten Containerabbruch: ein abgelaufener Lauf landete als
`DOCKER_TERM` in **fails** (Werkzeug ausgehebelt) und hinterließ kein Ergebnis.
AP5 verteilt den übergebenen Timeout auf drei Marken — **Bremse 70 %**,
**Netz 90 %**, Rest für die Bergung — und lässt einen beherrschten Timeout in
**errors** statt in **fails** landen. Dieser Abschnitt belegt das an echten
Container-Läufen. Beide Images waren zuvor neu gebaut
(`smartbugs/gptscan:1.0` 2,14 GB; `smartbugs/llmsmartaudit:1.0` **586 MB** —
der Neubau bestätigt damit die in `BA-EIGENANTEIL.md` geführte Reduktion von
5,13 GB am aktuellen Dockerfile). Testsuite vor den Läufen: 108 grün.

**Zwei verschiedene Zusagen, die nicht vermengt werden dürfen:** Bei **GPTScan**
ist der wertschöpfende Pfad die **Bremse** — das Werkzeug stellt LLM-Aufrufe ein
und läuft freiwillig aus. Greift bei GPTScan erst das **Netz**, wird **kein**
Teilergebnis gerettet; der Entrypoint legt nur einen wohlgeformten
Platzhalterreport an, den der Parser ehrlich als `success=false` ausweist. Das
Bergen eines Zwischenstands ist **LLMSmartAudits** Mechanismus (Snapshot nach
jeder Detektorphase), und dort ist das Netz die einzige Stufe, weil
LLMSmartAudit `SB_DEADLINE_EPOCH` nicht liest.

#### 4.5.1 Kostenloser Durchgang gegen den Prüfstand

`testing_tools/fake_llm_endpoint.py` (OpenAI-kompatible Attrappe mit
einstellbarer Antwortverzögerung), Contracts aus
`smartbugs/samples/gptscan/mwevariety_fixed/`, jeweils eigene Ergebnisbäume.

| Werkzeug | Contract | `--timeout` | Bremse/Netz | Verzögerung | Ergebnis |
|---|---|---|---|---|---|
| GPTScan | `5_Router.sol` | 300 s | 210 / 270 s | 10 s | `stage=brake`, Exit 0, 232 s, 21 Calls, 7 unterdrückt |
| GPTScan | `71_IndexTemplate.sol` | 300 s | 210 / 270 s | 10 s | **kein Marker** — Lauf mit 211,8 s vollständig |
| GPTScan | `5_Router.sol` | 60 s | 42 / 54 s | 60 s | `stage=net`, Exit **124**, 69,5 s |
| GPTScan | `5_Vether.sol` | 60 s | 42 / 54 s | 45 s | kein Marker — Contract setzt 0 LLM-Aufrufe ab |
| LLMSmartAudit | `5_Vether.sol`, `45_CreditLimitByMedian.sol` | 300 s | 210 / 270 s | 10 s | `stage=net`, Exit 124, 286 s, **24/41** Kategorien geborgen |

In **allen** Läufen war `fails` leer und der Timeout stand als `TIMEOUT_BRAKE`
bzw. `TIMEOUT_NET` in `errors` — das eigentliche Ziel des Arbeitspakets. Die
Normalisierung ist belegt: BusyBox meldet 143, SmartBugs sieht 124.

Zwei ungeplante, aber aussagekräftige Negativkontrollen fielen dabei an:
`71_IndexTemplate.sol` lief 1,8 s **nach** der Bremse vollständig durch und
trägt korrekt **keinen** Marker (Markerfreiheit heißt: der Lauf war
vollständig); `5_Vether.sol` passiert unter GPTScan keinen Feature-Word-Filter,
setzt null LLM-Aufrufe ab und ist als Timeout-Sonde untauglich.

**Reproduzierbarkeitsauflage:** Prüfstands-Verzögerung und `--timeout` müssen
aufeinander abgestimmt sein. Die naheliegende Kombination 30 s Verzögerung bei
`--timeout 60` liefert für LLMSmartAudit `categories_checked = 0`, also genau
den Zustand, den der Parser (zu Recht) als „Contract nicht analysiert" wertet.

Zusätzlich an echten Containern geprüft, dass **`TIMEOUT=0` nichts ändert**: Der
Entrypoint erhält `'0'`, die Zeile `SB_TIMEOUT_BUDGET` fehlt im Log, es wird kein
Marker gesetzt, LLMSmartAudit meldet 41/41 und schreibt keinen Zwischenstand
(GPTScan 17,4 s gegen 17,2 s mit Timeout). Die 19 Altmessungen bleiben
vergleichbar.

#### 4.5.2 Scharfer Lauf (DeepSeek `deepseek-v4-flash`)

Je Werkzeug ein Contract, jeweils als Voll- **und** Teillauf; die Timeouts sind
aus der zuvor gemessenen Volllaufzeit abgeleitet (nicht geraten).

| Werkzeug | Contract | Lauf | `--timeout` | Dauer | Ergebnis |
|---|---|---|---|---|---|
| LLMSmartAudit | `5_Vether.sol` | voll | — | 719,9 s | 41/41 Kategorien, **9 Findings** |
| LLMSmartAudit | `5_Vether.sol` | teil | 400 s (280/360) | 376,5 s | `stage=net`, Exit 124, **23/41**, 5 Findings |
| GPTScan | `5_Router.sol` | voll | — | 172,2 s | 39 Calls, **2 Findings**, $0,0067 |
| GPTScan | `5_Router.sol` | teil | 120 s (84/108) | 99,9 s | `stage=brake`, Exit 0, 24 Calls, 26 unterdrückt, 0 Findings, $0,0031 |

`fails` war in allen vier Läufen leer.

#### 4.5.3 Hat das Teilergebnis Substanz? (Teilmengen-Nachweis)

Ein Teilergebnis, das Findings **erfindet**, wäre schlimmer als gar keines.
Geprüft wurden deshalb zwei Eigenschaften:

* **Test A (Mechanismus):** Stammt jedes Finding des Teillaufs aus einem
  Detektor, der tatsächlich gelaufen ist? — **Ja, ohne Ausnahme.**
* **Test B (Teilmenge):** Sind die Findings des Teillaufs eine Teilmenge derer
  des Volllaufs? — **Ja.**

LLMSmartAudit, `5_Vether.sol`: Der Teillauf deckt exakt die **ersten 23**
Detektoren der Kette ab (echtes Präfix) und meldet 5 Findings — TOD (#5),
WithdrawalFunction (#13), LackAuthorization (#14), MissingOnlyOwner (#19),
PrecisionLoss (#21) — sämtlich auch im Volllauf enthalten (dort 9 Findings,
die weiteren 4 liegen auf den Positionen #22, #27, #38, #40). Der Teillauf hat
**nichts erfunden**.

Ehrlich zu benennen ist die Gegenrichtung: RedundantConditional (#22) lag im
abgedeckten Bereich, feuerte im Volllauf, im Teillauf jedoch nicht. Ein
Teillauf kann also ein Finding **verpassen**, das der Volllauf hatte — Folge des
bereits in 5.3 dokumentierten Nicht-Determinismus, nicht des Timeout-Mechanismus.
Die Zusage lautet „keine erfundenen Findings", nicht „identische Findings".

GPTScan, `5_Router.sol`: Der Teillauf meldet 0 Findings, ist damit trivial
Teilmenge der 2 Findings des Volllaufs. Die Metadaten zeigen aber einen Effekt,
der ausdrücklich festgehalten gehört: **`vul_before_static` steigt von 6
(Volllauf) auf 13 (Teillauf)**. Ursache ist `llm_backend.dry_sentinel` — nach
der Bremse liefert es für unterdrückte Aufrufe *bejahende* Platzhalter
(`"yes"` bzw. eine All-yes-Auswahl), weil es ursprünglich für `--dry-run`
geschrieben wurde, wo ein Oberschranken-Durchlauf gewollt ist. Die
Kandidatenliste wird dadurch künstlich aufgebläht. Dass daraus **kein**
erfundenes Finding wurde, liegt an zwei nachgelagerten Sicherungen: die
statische Bestätigungsstufe verwarf alle 13 Kandidaten
(`vul_after_static = 0`), und für die Static-Prompts liefert derselbe Sentinel
`"{}"`, womit keine bestätigende Nebenbedingung entsteht. Der Schutz war also
vorhanden, aber als **Nebeneffekt** und nicht als ausgesprochene Zusage.

**Diese Zahlen sind vor der Korrektur gemessen.** Der Deadline-Pfad gibt seither
einen eigenen, neutralen Platzhalter zurück (`llm_backend.deadline_sentinel`,
ausnahmslos `"{}"`), den alle drei Auswertungsstellen als „keine Angabe" lesen:
die Mehrfachauswahl als leere Menge, die Ja/Nein-Bestätigung als Nein, die
Static-Prompts unverändert. Die Wirkung ist nachgemessen und nicht nur
argumentiert — siehe **4.5.6**.

Bemerkenswert ist zudem, dass GPTScans Teillauf **beide** echten Findings
verlor: Die Bremse kostet hier nicht nur Vollständigkeit, sondern kann das
Ergebnis auf null reduzieren, weil die statische Bestätigung ohne die
zugehörigen LLM-Antworten nichts mehr bestätigen kann.

#### 4.5.4 Preis des Zwischenstands

Der Bezugswert „rund 76 s je Contract" ist **wall-clock durch Contractzahl bei
`--processes 4`** (10 935 s / 143) und damit keine Bearbeitungszeit je Contract.
Aus den 143 `smartbugs.json` des Referenzlaufs ergibt sich die tatsächliche
Verteilung: **Mittelwert 299,2 s, Median 264,1 s, Spanne 150,8–923,2 s**. Der
hier gemessene Volllauf (719,9 s für `5_Vether.sol`) liegt innerhalb dieser
Spanne; ein Vergleich gegen die 76 s wäre irreführend.

Die 41 zusätzlichen Schreibvorgänge wurden direkt vermessen (41 `record()`
-Aufrufe, 20 Wiederholungen, Median): **0,07 ms ohne** Snapshot gegen
**56,40 ms mit** Snapshot, also **56,3 ms Aufschlag für einen ganzen Contract**
— **0,019 %** des Referenzmittels von 299,2 s. Damit ist der Aufschlag weit
unterhalb der Wahrnehmungsschwelle und weit unterhalb der geforderten „paar
Prozent". Hinzu kommt: Der Flush ist ohnehin auf „nur wenn `SB_PARTIAL_REPORT`
gesetzt ist" beschränkt, und diese Variable setzt der Entrypoint ausschließlich
bei `TIMEOUT > 0`. Bei den 19 Altmessungen findet also **kein einziger**
zusätzlicher Schreibvorgang statt.

#### 4.5.5 Kosten und Artefakte

Kosten des scharfen Laufs: GPTScan **$0,0098** (vom Werkzeug selbst gerechnet:
$0,0067 voll + $0,0031 teil). LLMSmartAudit protokolliert keine Tokenzahlen;
abgeschätzt über Contractgröße × Aufrufzahl zu DeepSeek-v4-flash-Preisen
(0,14 / 0,28 USD je 1 M Token) ergeben sich **≈ $0,033**. **Gesamt ≈ $0,04.**
GPTScans Budget-Wächter (`MAX_COST_USD = 0.5` je Contract) wurde nicht
ausgelöst (`budget_exceeded = null`).

Ergebnisbäume (lokal, git-ignoriert), keine Altmessung berührt:
`smartbugs/results/{gptscan,llmsmartaudit}/ap5_{free_brake,free_net,free_notimeout,live_full,live_partial}/`;
die Wiederholungsläufe aus 4.5.6 unter
`ap5_{verify_brake,verify_net,verify_notimeout,verify2_full,verify2_part}/`.

#### 4.5.6 Gegenprobe nach der Korrektur des Platzhalters

Die Korrektur aus 4.5.3 greift in den Deadline-Pfad ein, also genau in das, was
4.5.1 und 4.5.2 gemessen haben. Beide Abschnitte wurden deshalb wiederholt.

**Voraussetzung, die dabei zuerst auffiel:** Das gptscan-Image **backt GPTScans
Quelltext ein** (`COPY . /opt/gptscan`), war aber vor der Korrektur gebaut. Ohne
Neubau wäre die Änderung im Repository gewesen und in keinem Lauf wirksam. Nach
dem Neubau im Image nachgesehen: `llm_backend.py` enthält `deadline_sentinel`,
`analyze_pipeline.py` ruft ihn im Deadline-Zweig, Budget-Zweig und `--dry-run`
rufen weiterhin `dry_sentinel`. Die Entrypoints sind über `bin: scripts`
**gemountet** und die Parser laufen auf dem Host — beide brauchen keinen Neubau.

**Prüfstand (kostenlos), alle vier Fälle bestanden:**

| Fall | Parameter | Ergebnis |
|---|---|---|
| GPTScan, Bremse | `--timeout 300`, 10 s Verzögerung | Exit 0, 231,8 s, `TIMEOUT_BRAKE`, `fails` leer |
| GPTScan, Netz | `--timeout 60`, 60 s Verzögerung | Exit **124**, 69,5 s, `TIMEOUT_NET`, `sb_timeout` in `output.json` |
| LLMSmartAudit, Netz | `--timeout 300`, 10 s Verzögerung | Exit **124**, 285,6 s, **24/41** geborgen, `timestamp: partial` |
| GPTScan, kein `--timeout` | Kontrolle | Exit 0, 17,8 s, keine `SB_TIMEOUT_BUDGET`-Zeile, kein Marker |

Der Bremsen-Lauf ist mit dem Altlauf aus 4.5.1 **identisch parametriert** und
damit direkt vergleichbar. Der Prüfstand antwortet auf jede Anfrage mit dem
Literal `"yes"`, was für die Mehrfachauswahl-Stufe kein gültiges JSON ist — ein
*echter* Aufruf kann dort also gar keinen Kandidaten erzeugen. Jeder Kandidat des
Altlaufs stammte folglich aus dem bejahenden Platzhalter:

| Kennzahl | vor der Korrektur | nach der Korrektur |
|---|---|---|
| LLM-Aufrufe | 21 | 21 |
| `used_time` | 215,14 s | 215,20 s |
| unterdrückte Aufrufe | 7 | 2 |
| `functions_after_step_1` | 3 | **0** |
| `vul_before_static` | 2 | **0** |

Der Rückgang von 7 auf 2 unterdrückte Aufrufe hat dieselbe Ursache: Jeder
erfundene All-yes-Eintrag zog eine weitere Ja/Nein-Frage nach sich, die ebenfalls
unterdrückt und mitgezählt wurde.

**Scharfer Lauf (DeepSeek `deepseek-v4-flash`), `5_Router.sol`:**

| | Volllauf | Teillauf (`--timeout 120`) |
|---|---|---|
| vor der Korrektur (4.5.2) | 172,2 s, 39 Aufrufe, 2 Findings, $0,0067 | 99,9 s, `brake`, 24 Aufrufe, 26 unterdrückt, 0 Findings, $0,0031 |
| `vul_before_static` | 6 | **13** |
| nach der Korrektur | 233,4 s, 44 Aufrufe, 2 Findings, $0,0091 | 99,8 s, `brake`, 23 Aufrufe, 13 unterdrückt, 0 Findings, $0,0033 |
| `vul_before_static` | 7 | **5** |

Das ist die Aussage, um die es geht: **Vor der Korrektur war die Kandidatenliste
des Teillaufs größer als die des Volllaufs (13 gegen 6) — nach der Korrektur ist
sie kleiner (5 gegen 7).** Ein Teillauf kann seither nur noch weniger vorschlagen
als ein Volllauf, nie mehr. Beide Volllaufergebnisse nennen dieselben zwei
Findings (MWE-200, MWE-206); der reguläre Pfad ist also unverändert. `fails` war
in allen Läufen leer, `budget_exceeded` überall `null`.

Die Schwankung zwischen den beiden Vollläufen (39 gegen 44 Aufrufe, 6 gegen 7
Kandidaten, 172 s gegen 233 s) ist der in 5.3 dokumentierte Nicht-Determinismus,
nicht eine Wirkung der Korrektur.

Kosten der Gegenprobe: **$0,0124** (Volllauf $0,0091 + Teillauf $0,0033), vom
Werkzeug selbst gerechnet. Die Prüfstands-Läufe kosten nichts.

**Nach der Zusammenführung mit `main` noch einmal gegengeprüft.** Der
LLMSmartAudit-Parser hat parallel eine zweite Prüfung bekommen (Kontextfenster,
`_context_state`), die bei jedem Parse mitläuft. Da Parser auf dem Host laufen,
gilt das auch rückwirkend für die oben aufgezeichneten Läufe. Alle drei echten
Timeout-Läufe wurden deshalb mit dem zusammengeführten Parser neu ausgewertet:
**derselbe `TIMEOUT_`-Eintrag, `fails` weiterhin leer, kein Eintrag verloren oder
hinzugekommen.** Einzige Änderung ist eine zusätzliche Info-Zeile beim
LLMSmartAudit-Lauf (`context window: 65536 tokens, smallest completion budget:
61588`) — das ist die neue Prüfung, die meldet, dass das Budget reichlich war.

**Nicht wiederholt:** der scharfe LLMSmartAudit-Lauf aus 4.5.2/4.5.3. Die
Korrektur betrifft ausschließlich GPTScan-Quelltext; LLMSmartAudits Image ist
neuer als die letzte Änderung an seinem eingebackenen Code, sein Netz-Pfad ist
oben kostenlos verifiziert, und ein Wiederholungslauf hätte rund $0,03 und
18 Minuten gekostet, ohne eine berührte Codezeile zu prüfen. Der
Teilmengen-Nachweis aus 4.5.3 bleibt damit die Messung vom 18.08.2026.

## 5. Methodische Limitationen

1. **Single-Label-Ground-Truth:** curated annotiert eine Primär-Schwachstelle pro Contract; echte Sekundär-Befunde zählen als False Positives → Precision-Werte sind Untergrenzen.
2. **DASP-only-Mapping:** Findings ohne DASP-Klassifikation (LLMSA: 468; Slither: 1 854) fließen nicht in Recall/Precision ein; zwei kanonische Zusatz-Mappings wurden dokumentiert ergänzt (Fehler #9).
3. **Nicht-Determinismus:** 74 % Lauf-zu-Lauf-Übereinstimmung bei GPTScan (4.3); LLMSA-Ergebnisse sind ebenfalls nicht deterministisch (nicht separat quantifiziert).
4. **Degradierte Static-Stufe:** Auf mwevariety war GPTScans Präzisions-Schutzmechanismus mangels kompilierbarer Dateien überwiegend inaktiv.
5. **Severity-Werte** beider LLM-Tools sind Kategorie-Defaults (4.2) — severity-gewichtete Metriken wären irreführend.
6. **Contract-Level-Metrik:** Bei hoher Finding-Dichte (LLMSA Ø 7,9) ist Contract-Level-Recall wohlwollend; Zeilen-genaue Auswertung war nicht möglich, da LLMSA keine Zeilennummern emittiert.
7. **Reichweite des Timeout-Nachweises (4.5):** Der Teilmengen-Nachweis stützt sich auf je einen Contract pro Werkzeug (Kostenrahmen). Er zeigt, dass der Teillauf nichts erfindet — er quantifiziert nicht, wie viel ein Teillauf im Mittel verpasst. Bei GPTScan fiel das Teilergebnis im gemessenen Fall sogar auf null Findings.
8. **`evaluate_curated.py` kennt den Timeout-Marker nicht:** Die Auswertung liest ausschließlich das Feld `findings` aus jeder `result.json` (siehe Kopfkommentar der Datei) und betrachtet weder `errors`/`fails` noch `degraded` — ein legitim unvollständiger, aber sauber geparster Teillauf (`sb_timeout`, seit AP5) ginge dort wie ein Volllauf in Recall und Precision ein. Bewusste Arbeitsteilung, kein Codefehler; für die AP5-Messläufe (4.5.1) ohne Wirkung, da sie nicht durch `evaluate_curated.py` liefen.

## 6. Artefakte & Reproduktion

| Artefakt | Pfad |
|---|---|
| Massentest-Skript | `run_curated.ps1` (Repo-Root; Prechecks, sequenzielle Läufe, Manifeste, Kosten-Summe) |
| Auswertung | `evaluate_curated.py` (Recall/Precision/F1 pro DASP-Kategorie, Detail-CSV) |
| Ergebnisse | `smartbugs/results/{gptscan,llmsmartaudit,slither-0.11.3}/curated_v1_20260705/` · `smartbugs/results/gptscan/curated_mwe_20260706/` (lokal, git-ignoriert) |
| Manifeste/CSVs | `smartbugs/results/curated_*_v1_20260705.csv` · `evaluation_curated_v1_20260705.csv` · `curated_results.csv` |
| Tool-Integration | `smartbugs/tools/{gptscan,llmsmartaudit}/{config.yaml,findings.yaml,parser.py,scripts/}` |

Reproduktion: `.\run_curated.ps1` (Volllauf beide Tools) bzw. `-Tool gptscan|llmsmartaudit`, danach `smartbugs\.venv\Scripts\python.exe evaluate_curated.py --suffix <RunIdSuffix> --csv`. Voraussetzungen: Docker Desktop, lokal gebaute Images, `DEEPSEEK_API_KEY` in `GPTScan/.env`.

