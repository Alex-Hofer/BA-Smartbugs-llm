# Durchführungsprotokoll: Evaluation der LLM-gestützten Scanner

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

| | |
|---|---|
| **Zeitraum** | Kern 05./06.07.2026; Nachträge 4.5 bis 4.9 bis 24.09.2026 |
| **Umgebung** | Windows 11, Docker Desktop (Linux-Engine), SmartBugs 2.1.1 (Python 3.13, venv), DeepSeek `deepseek-v4-flash` |
| **Werkzeuge** | GPTScan (LLM + statische Bestätigung, Regeln `MWE-200`…`209`), LLMSmartAudit (ChatDev/CAMEL, 41 Detektor-Prompts), Slither 0.11.3 (statische Baseline) |
| **Datensätze** | [smartbugs-curated](https://github.com/smartbugs/smartbugs-curated) (143 Contracts, 10 DASP-Kategorien, ein Label je Datei); `smartbugs/samples/gptscan/mwevariety` (96 DeFi-Contracts, ohne Ground Truth) |

---

## 1. Vorgehen

Wir sind in Stufen vorgegangen und haben vor jedem kostenpflichtigen Schritt
eine Prüfung eingebaut:

1. **Setup:** Images prüfen und bauen, Schlüssel-Handling verifizieren.
2. **Smoke-Test „dry“** ($0): Pipeline und Parser ohne echte API-Aufrufe.
3. **Gate-Review:** alle Ergebnisse von Schritt 2 unabhängig gegengeprüft —
   erst danach echte API-Aufrufe.
4. **Smoke-Test „live“:** beide Werkzeuge auf 3 Contracts.
5. **Analysen:** Parser- und SARIF-Prüfung, Rate-Limits, Laufzeit, Kosten.
6. **Automatisierung:** `run_curated.ps1` geschrieben, geprüft, im Trockenlauf
   getestet.
7. **Massenläufe:** GPTScan und LLMSmartAudit über curated (143), Slither (143),
   GPTScan über mwevariety (96).
8. **Auswertung:** `evaluate_curated.py` (Recall/Precision/F1 je
   DASP-Kategorie, Contract-Level) plus Stichproben am Quellcode.

Alle Läufe liefen über unsere SmartBugs-Integration, also in Docker, mit
einheitlicher Ausgabe (result.json, SARIF) und geschwärztem Schlüssel.

## 2. Setup-Besonderheiten

- **LLMSmartAudit-Image** direkt aus git HEAD gebaut, ohne Checkout (wegen
  Windows-Pfadlängen):
  `git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main | docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -`
- **Schlüssel** nur lokal in `GPTScan/.env` (git-ignoriert); SmartBugs reicht
  ihn zur Laufzeit in den Container und schwärzt ihn vor dem Speichern.
- **Netz:** SmartBugs isoliert Container (`network: none`); nur die beiden
  LLM-Werkzeuge haben per `network: bridge` API-Zugang.

## 3. Fehler, Diagnosen und Lösungen (chronologisch)

| # | Problem | Symptom | Diagnose | Lösung |
|---|---|---|---|---|
| 1 | Abgeschaltetes Modell im LLMSmartAudit-Image | jeder Lauf wäre mit HTTP 400 gescheitert | Stub-Experiment: Der Modellname geht wörtlich an die API, die nur noch `deepseek-v4-pro/flash` kennt; das eingebrannte `deepseek-chat` ist abgeschaltet | `LLM_MODEL=deepseek-v4-flash` auf dem Host setzen; seit 24.09.2026 Pflichtprüfung im Entrypoint |
| 2 | Kein Offline-/Stub-Modus bei LLMSmartAudit | „Stub“-Lauf erzeugte echte, abgelehnte API-Aufrufe | `run.py` bildet `--model` bei `deepseek` nie auf das interne StubModel ab | dokumentiert; Trockenläufe nur mit GPTScan (`GPTSCAN_DRY_RUN=1`) |
| 3 | Kaputte Test-Samples | `_chk/20_Pool.sol`: solc `extraneous input '<EOF>'` | ab Zeile 22 keine Zeilenumbrüche, ein `//`-Kommentar verschluckt den Rest; 4 von 6 `_chk`-Dateien betroffen | Ersatz `74_TimeswapPair.sol` (hatte trotzdem einen echten solc-Fehler; GPTScan fiel sauber auf LLM-only zurück) |
| 4 | **Stilles Scheitern bei GPTScan** | Compile-Fehler nur im `result.log`; `result.json` mit `errors=[]` und 0 Findings — nicht von „sauber“ zu unterscheiden | an zwei Fällen verifiziert; drei Zustände (sauber / nicht kompiliert / degradiert) | zunächst Manifeste aus den Logs; Parser-Fix am 02.08.2026 ([`parser-fix-vorher-nachher.md`](parser-fix-vorher-nachher.md), [`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md)) |
| 5 | PowerShell 5.1 und stderr | `docker info *> $null` warf `NativeCommandError` | PS 5.1 macht aus umgeleitetem stderr ErrorRecords | Umleitung über `cmd /c` |
| 6 | Exit-Code im Skript falsch | „ExitCode=Welcome to SmartBugs…“ | PowerShell-Funktionen geben die ganze Pipeline zurück | sb-Ausgabe per `\| Out-Host`, nur `$LASTEXITCODE` zurückgeben |
| 7 | Fehlalarm im Degradations-Manifest | Trockenlauf meldete intakten Contract als degradiert | im Trockenlauf läuft die statische Stufe nie | `dry_run`-Abfrage im Manifest |
| 8 | Manifest meldete zu viel | ~48 % der Contracts als „degradiert“ | `vul_before_static > vul_after_static` ist GPTScans gewollter Filter | umbenannt in „Review-Kandidaten“ (manuelle Prüfung, kein Ausschluss) |
| 9 | DASP-Lücken bei Slither | `time_manipulation`-Recall fälschlich 0 % | `timestamp` und `weak-prng` tragen in `findings.yaml` keine Klasse | dokumentiertes Zusatz-Mapping (timestamp → DASP-8, weak-prng → DASP-6) |
| 10 | DASP-Lücken bei LLMSmartAudit | 4 der 5 verpassten Contracts | `other` (SWC-109) und `short_addresses` haben keinen passenden Detektor | als Grenze der Taxonomie dokumentiert; 3 nicht zugeordnete Findings trafen sogar die Primärschwachstelle |
| 11 | Slither-Abstürze | 3 von 143 Tasks mit `EXIT_CODE_1` | 2× `AssertionError` im IR-Generator (`x.call.value(v)("")`), 1× `NotConstant` (`Request[2**64]`) | als Grenzfälle dokumentiert; `--continue-on-errors` fing sie ab |
| 12 | mwevariety kaum kompilierbar | 95/96 `InvalidCompilation`, 22/96 Python-Crashes | Einzeldateien ohne Importe; Crashes sind Folgefehler | dokumentiert; später repariert ([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md)) |
| 13 | Schlüssel im Klartext in Altergebnissen | 62 lokale Ergebnisdateien früherer Läufe | Schwärzung kam erst mit der SmartBugs-Integration; nie im Git, nie veröffentlicht | alle neuen Läufe geschwärzt geprüft; Schlüssel tauschen und Altdaten säubern vor jeder Weitergabe |

## 4. Ergebnisse

### 4.1 smartbugs-curated (143 Contracts, Contract-Level)

Stand 06.07.2026. Slither steht seit dem 20.09.2026 bei 67 / 45 / 54 (Nachtrag 4.6).

| Werkzeug | Recall | Precision | F1 | Findings (DASP-zugeordnet) | Kosten | Laufzeit |
|---|---|---|---|---|---|---|
| Slither 0.11.3 | 64 % | 45 % | 52 % | 2 154 (300) | $0 | 1:24 min |
| LLMSmartAudit | **97 %** | 30 % | 45 % | 1 124 (656) | $2,44 | 3:02 h |
| GPTScan | 0 %* | – | – | 6 (6) | $0,01 | 3:19 min |

\* GPTScan zielt nur auf DeFi-Logik, nicht auf die klassischen Klassen des
Datensatzes. 16 von 143 Contracts passierten den Vorfilter; die 6 Findings
(alle `MWE-207`) lagen auf Contracts mit anderem Label.

Laufzeit = SmartBugs-Meldung „Analysis completed in“; die Spanne vom ersten
Task-Start zum letzten Task-Ende ist etwas kürzer
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md) 4.1).

**LLMSmartAudit je Kategorie** (*Contracts* = so viele sind mit der Kategorie
gelabelt):

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

Im Mittel 7,9 Findings je Contract (Median 7, Maximum 18); **kein Contract
blieb ohne Finding**.

**Slither je Kategorie** (Auszug, Stand 06.07.): reentrancy 94/74/83,
unchecked_low_level_calls 88/59/71, time_manipulation 100/21/34, arithmetic und
front_running 0 % (keine passenden Detektoren). 1 854 der 2 154 Findings
(86,1 %) hatten keine DASP-Zuordnung — davon 1 480 Informational/Optimization,
166 Low, 148 Medium, 60 High. Seit Nachtrag 4.6: 1 763 ohne Zuordnung, davon
60 Medium und 57 High.

### 4.2 Stichproben am Quellcode

- **Verpasste Contracts (LLMSmartAudit):** 4 von 5 liegen an der Taxonomie
  (Fehler #10), nur einer ist ein echter Fehlgriff (`smart_billions.sol`, der
  PredictableRand-Detektor feuerte nicht). Auf demselben Contract verwarf auch
  GPTScans statische Stufe 2 Kandidaten.
- **„False Positives“ (LLMSmartAudit):** 19 Treffer in fremden Kategorien →
  **15 plausibel, 4 generisch, 0 falsch**; 10 nicht zugeordnete → 8 plausibel,
  2 generisch. Die gemessenen 30 % Precision unterschätzen also deutlich.
- **Severity:** über alle 1 124 Findings je Detektor zu 100 % konstant — ein
  Katalogwert, kein Urteil des Modells.
- **GPTScan-Review-Kandidaten:** alle 4 geprüft; die statische Stufe verwarf 5
  LLM-Kandidaten zu Recht.
- Die Einzelurteile der Stichproben (19, 10, 6 und 4 Findings) haben wir nicht
  archiviert, nur die Summen.

### 4.3 GPTScan auf mwevariety (96 DeFi-Contracts, unrepariert)

- **11 Findings auf 7 Contracts** (alle high): `MWE-200` ×6, `MWE-207` ×2,
  `MWE-209` ×2, `MWE-203` ×1.
- Stichprobe (6 Findings): **4 plausibel** (u. a. `slot0`-Spotpreis als
  Flashloan-Vektor, nie zurückgesetzte NFT-Approval), 1 generisch, 1 falsch.
- **Wiederholung** über 27 Contracts: nur **74 % identisch** (3 Findings weg,
  2 neu, 2 verändert) — trotz `temperature=0`.
- $0,046, 13:17 min, 257 LLM-Aufrufe, keine Rate-Limits. Keine Ground Truth,
  also nur beschreibend.

### 4.4 Betrieb und Robustheit

- **Keine Rate-Limits** über rund 6 640 API-Aufrufe (6 174 LLMSmartAudit
  curated, 129 Smoke, 257 + 72 + 9 GPTScan); kein Retry wurde je ausgelöst.
- Bewährte Parameter: `--processes 4`, Timeouts 1 800 s (GPTScan) / 5 400 s
  (LLMSmartAudit), Läufe nacheinander, `LLM_CONTEXT_TOKENS=65536`.
- **Kosten der Läufe vom 05./06.07.2026: ≈ $2,55** (Smoke $0,06, GPTScan
  curated $0,01, LLMSmartAudit curated $2,44, mwevariety $0,05). Das ist nicht
  die Summe der ganzen Arbeit: Mit den späteren Volläufen, dem Nachlauf und den
  abgebrochenen Läufen kommen rund 23 USD zusammen
  ([`BA-ARBEIT.md`](BA-ARBEIT.md) 5.3).

### 4.5 AP5 — Nachweis des Timeout-Verhaltens (18.08.2026)

Vor AP5 war `--timeout` für beide LLM-Werkzeuge nur ein harter
Containerabbruch: Der Lauf landete in **fails** und hinterließ nichts. AP5
teilt den Timeout in drei Marken — **Bremse 70 %**, **Netz 90 %**, Rest fürs
Bergen — und lässt einen beherrschten Timeout in **errors** landen. Beide
Images waren vorher neu gebaut (GPTScan 2,14 GB, LLMSmartAudit **586 MB**);
Testsuite: 108 grün.

**Zwei verschiedene Zusagen:** Bei **GPTScan** zählt die **Bremse** — es
stellt LLM-Aufrufe ein und läuft aus; greift erst das Netz, bleibt nur ein
Platzhalterreport (`success=false`). Bei **LLMSmartAudit** ist das **Netz** die
einzige Stufe, und der Entrypoint birgt den Zwischenstand nach der letzten
Detektorphase.

#### 4.5.1 Kostenlos gegen den Prüfstand

`testing_tools/fake_llm_endpoint.py` (OpenAI-kompatibel, einstellbare
Verzögerung), Contracts aus `mwevariety_fixed/`:

| Werkzeug | Contract | `--timeout` | Bremse/Netz | Verzögerung | Ergebnis |
|---|---|---|---|---|---|
| GPTScan | `5_Router.sol` | 300 s | 210 / 270 s | 10 s | `stage=brake`, Exit 0, 232 s, 21 Aufrufe, 7 unterdrückt |
| GPTScan | `71_IndexTemplate.sol` | 300 s | 210 / 270 s | 10 s | **kein Marker** — nach 211,8 s vollständig |
| GPTScan | `5_Router.sol` | 60 s | 42 / 54 s | 60 s | `stage=net`, Exit **124**, 69,5 s |
| GPTScan | `5_Vether.sol` | 60 s | 42 / 54 s | 45 s | kein Marker — 0 LLM-Aufrufe |
| LLMSmartAudit | `5_Vether.sol`, `45_CreditLimitByMedian.sol` | 300 s | 210 / 270 s | 10 s | `stage=net`, Exit 124, 286 s, **24/41** Kategorien geborgen |

In **allen** Läufen war `fails` leer, der Timeout stand als `TIMEOUT_BRAKE`
bzw. `TIMEOUT_NET` in `errors`. BusyBox meldet 143, SmartBugs sieht 124.

Zwei ungeplante Negativkontrollen: `71_IndexTemplate.sol` lief 1,8 s **nach**
der Bremse vollständig durch und trägt richtigerweise **keinen** Marker;
`5_Vether.sol` passiert GPTScans Vorfilter nicht und taugt nicht als Sonde.

Wichtig für Wiederholungen: Verzögerung und Timeout müssen zusammenpassen. 30 s
Verzögerung bei `--timeout 60` ergibt für LLMSmartAudit `categories_checked =
0` — genau der Zustand, den der Parser zu Recht als „nicht analysiert“ wertet.

Außerdem geprüft: **`TIMEOUT=0` ändert nichts** — kein `SB_TIMEOUT_BUDGET` im
Log, kein Marker, LLMSmartAudit 41/41 ohne Zwischenstand (GPTScan 17,4 s gegen
17,2 s). Die Altmessungen bleiben vergleichbar.

#### 4.5.2 Scharfer Lauf (`deepseek-v4-flash`)

Je Werkzeug ein Contract, als Voll- und Teillauf; die Timeouts haben wir aus
der gemessenen Volllaufzeit abgeleitet.

| Werkzeug | Contract | Lauf | `--timeout` | Dauer | Ergebnis |
|---|---|---|---|---|---|
| LLMSmartAudit | `5_Vether.sol` | voll | — | 719,9 s | 41/41, **9 Findings** |
| LLMSmartAudit | `5_Vether.sol` | teil | 400 s (280/360) | 376,5 s | `stage=net`, Exit 124, **23/41**, 5 Findings |
| GPTScan | `5_Router.sol` | voll | — | 172,2 s | 39 Aufrufe, **2 Findings**, $0,0067 |
| GPTScan | `5_Router.sol` | teil | 120 s (84/108) | 99,9 s | `stage=brake`, Exit 0, 24 Aufrufe, 26 unterdrückt, 0 Findings, $0,0031 |

`fails` war in allen vier Läufen leer.

#### 4.5.3 Hat das Teilergebnis Substanz?

Ein Teilergebnis, das Findings **erfindet**, wäre schlimmer als keines. Geprüft:

* **Test A:** Stammt jedes Finding des Teillaufs aus einem Detektor, der
  tatsächlich lief? — **Ja.**
* **Test B:** Sind die Findings des Teillaufs eine Teilmenge des Volllaufs? —
  **Ja.**

**LLMSmartAudit**, `5_Vether.sol`: Der Teillauf deckt genau die **ersten 23**
Detektoren ab und meldet 5 Findings (TOD #5, WithdrawalFunction #13,
LackAuthorization #14, MissingOnlyOwner #19, PrecisionLoss #21) — alle auch im
Volllauf (dort 9; die übrigen 4 auf #22, #27, #38, #40). Nichts erfunden.
Umgekehrt feuerte RedundantConditional (#22) im Volllauf, im Teillauf nicht —
ein Teillauf kann also etwas **verpassen**; das ist Nichtdeterminismus, nicht der
Timeout-Mechanismus. Die Zusage lautet „nichts erfunden“, nicht „identisch“.

**GPTScan**, `5_Router.sol`: 0 Findings, also trivial eine Teilmenge. Aber
**`vul_before_static` stieg von 6 (voll) auf 13 (teil)**. Ursache war
`llm_backend.dry_sentinel`: Nach der Bremse lieferte es für unterdrückte
Aufrufe *bejahende* Platzhalter, weil es für `--dry-run` geschrieben war. Dass
daraus kein Finding wurde, lag nur an nachgelagerten Sicherungen (die statische
Stufe verwarf alle 13; für Static-Prompts lieferte der Platzhalter `"{}"`).
Seitdem gibt der Deadline-Pfad einen eigenen, neutralen Platzhalter zurück
(`deadline_sentinel`, immer `"{}"`) — nachgemessen in 4.5.6. Außerdem verlor
GPTScans Teillauf **beide** echten Findings: Ohne die LLM-Antworten kann die
statische Stufe nichts bestätigen, das Ergebnis kann auf null fallen.

#### 4.5.4 Was der Zwischenstand kostet

Die 41 zusätzlichen Schreibvorgänge (`record()`, 20 Wiederholungen, Median)
kosten **56,3 ms je Contract** — **0,019 %** der mittleren Laufzeit von 299,2 s
(Median 264,1 s, Spanne 150,8–923,2 s aus den 143 `smartbugs.json` des
Referenzlaufs). Geschrieben wird außerdem nur, wenn `SB_PARTIAL_REPORT` gesetzt
ist, also nur bei `TIMEOUT > 0` — die Altmessungen betrifft es nicht.

#### 4.5.5 Kosten und Ablage

GPTScan $0,0098 (vom Werkzeug gerechnet), LLMSmartAudit ≈ $0,033 (geschätzt
aus Contractgröße × Aufrufen zu 0,14 / 0,28 USD je Mio. Token), **gesamt
≈ $0,04**. GPTScans Budget-Wächter griff nicht. Ergebnisse unter
`smartbugs/results/{gptscan,llmsmartaudit}/ap5_{free_brake,free_net,free_notimeout,live_full,live_partial}/`,
die Wiederholungen aus 4.5.6 unter
`ap5_{verify_brake,verify_net,verify_notimeout,verify2_full,verify2_part}/`.

#### 4.5.6 Gegenprobe nach der Korrektur

Die Korrektur aus 4.5.3 trifft genau den gemessenen Pfad, also haben wir 4.5.1
und 4.5.2 wiederholt. Dabei fiel zuerst auf: Das GPTScan-Image **backt den
Quelltext ein** — ohne Neubau wäre die Änderung nirgends wirksam gewesen. Nach
dem Neubau im Image geprüft: `deadline_sentinel` ist da und wird im
Deadline-Zweig gerufen. Entrypoints (gemountet) und Parser (Host) brauchen
keinen Neubau.

**Prüfstand — alle vier Fälle bestanden:**

| Fall | Parameter | Ergebnis |
|---|---|---|
| GPTScan, Bremse | `--timeout 300`, 10 s | Exit 0, 231,8 s, `TIMEOUT_BRAKE`, `fails` leer |
| GPTScan, Netz | `--timeout 60`, 60 s | Exit **124**, 69,5 s, `TIMEOUT_NET`, `sb_timeout` gesetzt |
| LLMSmartAudit, Netz | `--timeout 300`, 10 s | Exit **124**, 285,6 s, **24/41** geborgen |
| GPTScan, ohne `--timeout` | Kontrolle | Exit 0, 17,8 s, kein Marker |

Der Prüfstand antwortet immer `"yes"`, was für die Mehrfachauswahl kein
gültiges JSON ist — jeder Kandidat im Altlauf stammte also aus dem bejahenden
Platzhalter:

| Kennzahl | vorher | nachher |
|---|---|---|
| LLM-Aufrufe | 21 | 21 |
| unterdrückte Aufrufe | 7 | 2 |
| `functions_after_step_1` | 3 | **0** |
| `vul_before_static` | 2 | **0** |

**Scharf, `5_Router.sol`:**

| | Volllauf | Teillauf (`--timeout 120`) |
|---|---|---|
| vorher | 172,2 s, 39 Aufrufe, 2 Findings, `vul_before_static` 6 | 99,9 s, 24 Aufrufe, 0 Findings, `vul_before_static` **13** |
| nachher | 233,4 s, 44 Aufrufe, 2 Findings, `vul_before_static` 7 | 99,8 s, 23 Aufrufe, 0 Findings, `vul_before_static` **5** |

**Vorher war die Kandidatenliste des Teillaufs größer als die des Volllaufs (13
gegen 6), nachher kleiner (5 gegen 7).** Ein Teillauf kann seitdem nur weniger
vorschlagen, nie mehr. Beide Volläufe melden dieselben zwei Findings
(`MWE-200`, `MWE-206`); die Unterschiede zwischen ihnen sind Nichtdeterminismus.
Kosten der Gegenprobe $0,0124; Prüfstandsläufe kostenlos.

Nach dem Zusammenführen mit `main` (neue Kontextprüfung im
LLMSmartAudit-Parser) haben wir die drei echten Timeout-Läufe neu ausgewertet:
gleicher `TIMEOUT_`-Eintrag, `fails` leer, nur eine zusätzliche Info-Zeile zum
Kontextbudget. Den scharfen LLMSmartAudit-Lauf haben wir **nicht** wiederholt:
Die Korrektur betrifft nur GPTScan-Code, der Netz-Pfad ist kostenlos
nachgeprüft, und ein Lauf hätte $0,03 und 18 Minuten gekostet, ohne eine
geänderte Zeile zu testen.

### 4.6 Nachtrag (20.09.2026): drei Slither-Detektoren ergänzt

Die Zahlen in 4.1 bleiben als Stand der Durchführung stehen. In
`smartbugs/tools/slither-0.11.3/findings.yaml` tragen die drei Detektoren für
**ungeprüfte Rückgabewerte** keine Klasse, während zwei schwächere auf
SWC-104/DASP-4 abgebildet sind:

| Detektor | Findings | Severity | Klasse |
|---|---:|---|---|
| `low-level-calls` (meldet nur, *dass* ein Low-Level-Call vorkommt) | 91 | informational | SWC-104, DASP-4 |
| `unused-return` | 1 | medium | SWC-104, DASP-4 |
| `unchecked-lowlevel` | 54 | medium | — |
| `unchecked-send` | 34 | medium | — |
| `unchecked-transfer` | 3 | high | — |

SWC-104 heißt „Unchecked Call Return Value“ — genau das melden die drei. Die
Lücke traf die größte Kategorie (`unchecked_low_level_calls`, 52 Contracts) und
ließ die Baseline schlechter aussehen, als sie ist. Wir haben die drei
deshalb ins Zusatz-Mapping aufgenommen:

| | vorher | nachher |
|---|---|---|
| `unchecked_low_level_calls` (R/P/F1) | 88 / 59 / 71 | **98 / 58 / 73** |
| Slither gesamt | 64 / 45 / 52 | **67 / 45 / 54** |
| erkannte Contracts | 91 | 96 |
| DASP-zugeordnete Findings | 300 | 391 |
| ohne Zuordnung | 1 854 (86,1 %) | 1 763 (81,8 %) |

Die Precision bleibt bei 45 % — eine Korrektur der Untererfassung, kein neuer
Maßstab. Die Taxonomien der LLM-Werkzeuge haben wir nicht angefasst.

### 4.7 Nachtrag (24.09.2026): Grammatik-Ablehnungen bei GPTScan

GPTScan liest den Code mit einem ANTLR-Parser, zählt daraus Funktionen
(`GPTSCAN_META`, Feld `functions`) und wendet darauf den Vorfilter an. In **87
der 143** curated-Tasks lehnte dieser Parser Teile des Codes ab (`mismatched
input`, `extraneous input`, `missing`; 1 773 Meldungen, Median 5 je Task). Alle
87 sind Solidity 0.4; am häufigsten scheitert `constant` (95× `extraneous
input`, 70× `missing 'constant'`). Von den 56 Tasks ohne Ablehnung sind 55
ebenfalls 0.4 — es kommt auf die Konstrukte an, nicht auf die Version.

Die Folge zeigt sich an der Funktionszählung: In 86 der 87 Tasks liegt
`functions` unter der Zahl der Deklarationen im Code (Median 25 %), bei den
übrigen in 35 von 56 (Median 45 %). Beispiele: `BECToken.sol` — 11 Meldungen,
4 von 24 Funktionen, kein LLM-Aufruf; `parity_wallet_bug_1.sol` — 274
Meldungen, 14 von 38. Von den 87 Tasks lösten 6 einen LLM-Aufruf aus (7 %), von
den 56 anderen 10 (18 %).

**Belegt** ist, dass der Vorfilter bei einem Teil der 127 verworfenen Contracts
weniger sah, als im Code steht. **Nicht belegt** ist, dass vollständiges Parsen
Findings gebracht hätte — die Regeln zielen auf DeFi-Logik, die curated nicht
labelt. Einen Nachlauf mit vollständigem Parsen haben wir nicht gefahren. Auf
dem DeFi-Korpus (0.6 bis 0.8) tritt das Problem nicht auf.

### 4.8 Nachtrag (24.09.2026): Slither auf `mwevariety_fixed`

Erster Versuch `slither_mwefixed_v1` (`--timeout 600`, 4 Prozesse, 8:46 min):
nur 51 von 96 Contracts analysiert (4 319 Findings, 46 Detektoren). Ursache:
Die solc-Binaries 0.7.6 und 0.8.1 bis 0.8.12 sind gegen glibc gelinkt und
starten im Alpine-Image nicht ([`BA-BETRIEB.md`](BA-BETRIEB.md), Fallstrick 10).

Mit eigenem glibc-Image (`smartbugs/tools/slither-0.11.3-glibc/`, gleiche
Version, gleicher Parser) lief `slither_mwefixed_v2` (2:48 min, 646,6 s
Container-Zeit) auf 95 von 96 Contracts: 94 mit Findings, 7 096 Findings aus 48
Detektoren (4 858 Informational, 112 Optimization, 1 254 Low, 748 Medium, 124
High). Für die 51 schon in v1 analysierten Contracts identisch. Der letzte,
`58_UniV3Vault.sol`, scheitert an `Stack too deep` (nur mit `--optimize`
übersetzbar, Slither ruft solc ohne). Auswertung in
`eval/per_contract/slither_mwefixed_v{1,2}__*.csv`.

### 4.9 Nachtrag (24.09.2026): die 37 Kontext-Contracts

`llmsa_mwefixed_v2` führte 37 von 96 Contracts als „Kontext überschritten“.
Ursache war die Konstante 65 536 in `camel/utils.py`; das Modell kann laut
Anbieter 1 Mio. Token. Seit dem 24.09.2026 ist die Grenze über
`LLM_CONTEXT_TOKENS` einstellbar. Der Nachlauf `llmsa_mwefixed_v2_ctx1m` über
genau diese 37 (`LLM_CONTEXT_TOKENS=1000000`, `LLM_MAX_COMPLETION_TOKENS=32768`,
Timeout 7 200 s, 2 Prozesse): **37 von 37 vollständig**, 317 Findings aus 34
Kategorien, 1 625 Aufrufe, 100,3 Mio. Prompt-Token (im Mittel 61 700 je Aufruf
gegen 20 900 im Hauptlauf), 35 028 s Container-Zeit, Median 954 s je Contract,
**5,55 USD abgebucht** (geschätzt 11,42). Der Lauf entstand in zwei Teilen (26
und 11 Contracts), weil der Runner an einer Dateisperre abbrach und ein
Ersatz-Kostenwächter bei geschätzten 8 USD stoppte — ohne Einfluss auf die
Ergebnisse. Vorbehalt: Der Anbieter bedient den Modellnamen seit September
2026 mit DeepSeek-V4.1-Flash; deshalb mischen wir den Nachlauf nicht in den
Hauptlauf. Auswertung in `eval/llmsa_mwefixed_v2_ctx1m/`.

## 5. Methodische Grenzen

1. **Ein Label je Datei:** Richtige Zweitbefunde zählen als False Positive —
   Precision ist eine Untergrenze.
2. **Nur DASP-zugeordnete Findings zählen:** LLMSmartAudit 468 und Slither
   1 763 Findings fallen heraus. Fünf Zusatz-Mappings für Slither sind
   dokumentiert (Fehler #9, Nachtrag 4.6); die LLMSmartAudit-Zuordnung ist je
   Detektor in `smartbugs/tools/llmsmartaudit/mapping.md` begründet.
3. **Nichtdeterminismus:** GPTScan 74 % (4.3); LLMSmartAudit 61,4 % Jaccard
   ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md) 4.4).
4. **Degradierte statische Stufe** auf dem unreparierten mwevariety.
5. **Severity** beider LLM-Werkzeuge ist ein Katalogwert (4.2) —
   severity-gewichtete Kennzahlen wären irreführend.
6. **Contract-Level:** Bei 7,9 Findings je Contract ist der Recall
   wohlwollend; zeilengenau geht nicht, weil LLMSmartAudit keine Zeilen liefert.
7. **Timeout-Nachweis an je einem Contract:** zeigt, dass ein Teillauf nichts
   erfindet, nicht, wie viel er im Mittel verpasst. Bei GPTScan fiel das
   Teilergebnis auf null.
8. **`evaluate_curated.py` kennt `sb_timeout` nicht:** Es liest nur `findings`;
   ein Teillauf ginge wie ein Volllauf in die Kennzahlen ein. Für die
   ausgewerteten Läufe ohne Folge, weil keiner einen Timeout hatte.
9. **Grammatik-Ablehnungen bei Solidity 0.4 (4.7):** Die Begründung „kein
   Schlüsselwort“ für GPTScans 0 % ist nur für die 56 vollständig geparsten
   Tasks belegt.

## 6. Artefakte und Reproduktion

| Artefakt | Pfad |
|---|---|
| Massenlauf | `run_curated.ps1` (Prechecks, sequenzielle Läufe, Manifeste, Kostensumme) |
| Auswertung | `evaluate_curated.py` (Recall/Precision/F1 je DASP-Kategorie, Detail-CSV) |
| Ergebnisse | `smartbugs/results/{gptscan,llmsmartaudit,slither-0.11.3}/curated_v1_20260705/`, `smartbugs/results/gptscan/curated_mwe_20260706/` (je Task `result.json` und `smartbugs.json` im Git, Logs im Release-Zip) |
| Manifeste/CSVs | `smartbugs/results/curated_*_v1_20260705.csv`, `evaluation_curated_v1_20260705.csv`, `curated_results.csv` |
| Integration | `smartbugs/tools/{gptscan,llmsmartaudit}/` |

Reproduktion: `.\run_curated.ps1` (oder `-Tool gptscan|llmsmartaudit`), danach
`smartbugs\.venv\Scripts\python.exe evaluate_curated.py --suffix <RunIdSuffix> --csv`.
Voraussetzungen: Docker Desktop, lokal gebaute Images, `DEEPSEEK_API_KEY` in
`GPTScan/.env`.
