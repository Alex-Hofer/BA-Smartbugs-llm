# KI-Scanner im SmartBugs-Framework — Auswertung der jüngsten Testläufe

**Werkzeuge:** GPTScan · LLMSmartAudit (llmaudit)
**Korpus:** `mwevariety_fixed`, 96 DeFi-Contracts
**Modell (beide):** deepseek / deepseek-v4-flash
**Läufe:** `gptscan_mwefixed_v2_main` (2026-08-15) · `llmsa_mwefixed_v2` (2026-08-16)
**Belege:** `eval/gptscan_mwefixed_v2_main/summary.md`, `eval/llmsa_mwefixed_v2/summary.md`

---

## 1. Was ist passiert? (Vorgehen)

**Ausgangslage.** Beide Werkzeuge sind in SmartBugs als Docker-Integration
eingebunden und wurden über denselben, zuvor rekonstruierten Korpus von 96
Contracts geschickt (`mwevariety_fixed`: 96/96 nativ kompilierbar). Ziel war ein
Volllauf beider Scanner mit gesetztem **MAIN-Parameter**, um Findings, Kosten,
Laufzeit und Fehlerverhalten unter Realbedingungen zu erheben.

### GPTScan-Lauf (`gptscan_mwefixed_v2_main`)

- 96 Contracts, Provider deepseek/deepseek-v4-flash, **MAIN = True**.
- Konfiguration: 4 parallele Prozesse, Docker-Timeout 1800 s, Mem-Limit 4 g.
- Auswertung automatisiert über `analysis_tools/gptscan_eval.py`; Rohergebnisse
  unverändert belassen.
- Besonderheit im Vorgehen: Drei Contracts scheiterten im Hauptlauf mit
  **Exit 127** (Dateiname benennt keinen im File enthaltenen Contract → `--main`
  hat kein Reduktionsziel). Sie wurden in einem **Nachlauf ohne MAIN** aufgelöst
  und sind in der Spalte `function_source` als „voll" erkennbar.

### LLMSmartAudit-Lauf (`llmsa_mwefixed_v2`)

- 96 Contracts, Modus **SmartContractTA** (fest in `scripts/do_solidity.sh`),
  **MAIN = 0**.
- Deutlich rechenintensiver: 2.481 LLM-Aufrufe, Summe der Task-Laufzeit
  ≈ 88.440 s (≈ 24,6 h).
- **Besonderheit / Störung dieses Laufs — Token- bzw. Kontextlimit erreicht:**
  Bei **37 von 96 Contracts (38,5 %)** wurde der Kontext überschritten; diese
  Contracts wurden **nie analysiert**. Dazu kamen 4 Contracts ohne Report.
  Effektiv liegt nur für **55 Contracts (57,3 %)** ein Analyseergebnis vor. Diese
  Deckelung ist die zentrale Einschränkung des Laufs und wird in den Ergebnissen
  konsequent getrennt ausgewiesen.

### Relabeling / einheitliche Zustandssemantik

Beide Läufe wurden nach derselben, aus dem SmartBugs-Quelltext hergeleiteten
Terminologie ausgewertet (`docs/BA-ERRORS-VS-FAILS.md`):

- **Finding** – das Werkzeug äußert einen Verdacht über den Contract (noch kein
  True/False Positive).
- **Error** – das Werkzeug hat ein Problem bemerkt, abgefangen und
  weitergearbeitet; ein (evtl. unvollständiges) Ergebnis liegt vor.
- **Failure/Fail** – eine Exception ist entkommen oder der Lauf wurde
  abgebrochen; **kein** Ergebnis.

---

## 2. Was war das Outcome? (Ergebnisse)

### 2.1 GPTScan — `gptscan_mwefixed_v2_main`

| Kennzahl | Wert |
|---|---|
| Findings | **74** auf **37** Contracts |
| Tasks mit Errors | 31 / 96 (**32,3 %**) |
| Tasks mit Fails | **0** |
| Nicht übersetzt (unbestimmt, ≠ „clean") | 1 (`58_UniV3Vault`) |
| Ohne Findings, sauber | 58 |
| Kosten | **$0,3638** (Median $0,00135, max $0,02639) |
| Tokens / Calls | 736.374 prompt / 930.986 completion · 1.518 Calls |
| Laufzeit | Wanduhr 3.055 s · Task-Summe 11.771,7 s · max 922,2 s |

- Dominierende Regel: **MWE-200 (Insecure LP Token Value Calculation): 41
  Findings auf 25 Contracts.** 8 der 10 MWE-Regeln zählen zu „DeFi-Logik" ohne
  redliches SWC/DASP-Gegenstück; 2 Regeln (MWE-204, MWE-208) ohne Treffer.
- Alle 74 Findings tragen Severity **high** — das ist ein Kategorie-Default des
  Detektors, kein Einzelfallurteil.
- **Wichtiger Vorbehalt:** Der Timeout wird derzeit **nur von Docker**
  durchgesetzt, nicht vom Werkzeug selbst (offener Punkt AP5).

### 2.2 LLMSmartAudit — `llmsa_mwefixed_v2`

| Zustand | Contracts | Anteil |
|---|---|---|
| Findings gemeldet | 55 | 57,3 % |
| **Kontext überschritten – NICHT analysiert** | **37** | **38,5 %** |
| kein Report | 4 | 4,2 % |

| Aufwand | Wert |
|---|---|
| LLM-Calls | 2.481 |
| Prompt-Tokens | 52.824.882 |
| Completion-Tokens | 8.662.310 |
| Kosten (geschätzt) | ≈ **$8,00** — das Werkzeug meldet $0,0000 (keine Preistabelle für `deepseek-v4-flash`); maßgeblich bleibt die DeepSeek-Rechnung |
| Summe Task-Laufzeit | 88.440 s (≈ 24,6 h) |

- Auf den 55 analysierten Contracts wurden Findings breit gestreut gemeldet;
  häufigste Kategorien: **Centralization Risk (43)**, **Precision Loss /
  Integer-Division Truncation (30)**, **Missing Access Control (24)**, **Single
  External Oracle Dependency (24)**. Contracts mit den meisten Findings:
  `5_Vader` (16), `5_Pools` (15), `5_DAO` (14).
- **Interpretationsregel (kritisch):** Die 37 „Kontext überschritten"-Contracts
  sind **kein** Ergebnis. Sie dürfen weder als „clean" gezählt noch in eine
  Precision-Rechnung aufgenommen werden.
- LLMSmartAudit liefert **keine Positionsangaben** (`function`, `lines`,
  `severity`, `confidence` sind `null`) — es liest Quelltext als Text.

### 2.3 Gegenüberstellung

| | GPTScan | LLMSmartAudit |
|---|---|---|
| Analysierbare Contracts | 95/96 (1 nicht übersetzt) | **55/96** (37 Kontext-Overflow, 4 ohne Report) |
| Findings | 74 (fokussiert, DeFi-Regeln) | breit, allgemeine Solidity-Mängel |
| Kosten | $0,36 | ≈ $8,00 (geschätzt) |
| Laufzeit-Summe | ≈ 3,3 h | ≈ 24,6 h |
| Zeilennummern | ja | nein |
| Zentrale Störung | Static-Stufe/Timeout (AP5) | **Token-/Kontextlimit auf 38,5 % der Contracts** |

**Kernaussage:** GPTScan ist fokussiert, günstig und schnell, deckt aber nur
DeFi-Logik ab. LLMSmartAudit meldet breiter, ist aber um ~Faktor 22 teurer,
langsamer — und der Lauf ist durch das **erreichte Token-/Kontextlimit nur
eingeschränkt aussagekräftig**, weil über ein Drittel des Korpus gar nicht
analysiert wurde.

---

## 3. Offene Präzisierung

Das Token-Problem erscheint in den Daten als *pro-Contract-Kontextüberschreitung*
(37 Contracts). Falls zusätzlich ein **globaler Quota-/Budget-Stopp** vorlag
(API-Guthaben erschöpft, Lauf vorzeitig abgebrochen), ist dieser mit
Zeitpunkt/Log getrennt zu dokumentieren.
