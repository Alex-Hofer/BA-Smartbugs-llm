# Demonstrationslauf GPTScan + LLMSmartAudit

Datum: 2026-08-02. Zweck: Funktionsnachweis der Werkzeugkette an zwei
Contract-Sätzen, mit sichtbarem inhaltlichem Kontrast. **Kein neuer Messwert
für die Bachelorarbeit** — dafür ist die Stichprobe zu klein und die
Werkzeugausgabe zu wenig deterministisch (siehe Abschnitt 8).

Bedienung der Werkzeuge: `BA-WERKZEUG-BEDIENUNG.md`.

> **Datierter Bericht (02./03.08.2026), nicht nachgeführt.** Die fünf
> Demoläufe stehen mit ihrem Zweck in `eval/LAUFREGISTER.md`. Das damals
> verwendete LLMSmartAudit-Image trug noch das eingebrannte Modell und das
> 5,13-GB-Evaluationsverzeichnis; seit dem 24.09.2026 gilt beides nicht mehr
> (`BA-BETRIEB.md`, Fallstrick 2; `BA-EIGENANTEIL.md` 2.4). Lokale Pfade des
> Erhebungsrechners in den zitierten Konsolenausgaben sind zu `<repo>`
> beziehungsweise `<benutzer>` gekürzt.

Die im Text genannten Bilanzdateien `docs/errors-fails-demo_*.md` und `.csv`
sind git-ignoriert (`.gitignore`) und liegen nur im Arbeitsbaum des
Erhebungsrechners; ihr Inhalt ist in den Abschnitten 5 und 7 wiedergegeben.
Die Dateilisten `demolauf_satz*.sbd` im Wurzelverzeichnis sind versioniert.

---

## 1. Was gelaufen ist

| Satz | Datensatz | Contracts | Werkzeuge |
|---|---|---:|---|
| A | `smartbugs-curated\dataset` (SWC/DASP, mit Ground Truth) | 5 | GPTScan, LLMSmartAudit |
| B | `smartbugs\samples\gptscan\mwevariety_fixed` (DeFi, Web3Bugs) | 5 | GPTScan, LLMSmartAudit |

Die Contracts wurden gezielt ausgewählt, nicht zufällig gezogen. Für Satz A je
einer aus einer anderen Ground-Truth-Kategorie, und zwar nur solche, die im
Altlauf `curated_v1_20260705` nachweislich übersetzt und ohne Errors oder Fails
durchgelaufen waren — damit ein Nullergebnis aussagekräftig ist und nicht bloß
ein Übersetzungsunfall. Für Satz B die fünf Contracts, die im Altlauf
`curated_mwefixed_live` Findings lieferten und zusammen die breiteste
MWE-Abdeckung ergaben.

Die Auswahl wurde über zwei `.sbd`-Dateilisten im Repository-Wurzelverzeichnis
umgesetzt (`demolauf_satzA.sbd`, `demolauf_satzB.sbd`). Grund: `-FilePattern`
nimmt genau ein Glob-Muster, und Pythons `glob` kennt keine
Klammer-Alternativen. SmartBugs unterstützt Dateilisten von Haus aus
(`sb/smartbugs.py::collect_files`).

---

## 2. Ein Blocker, der den Lauf zunächst vollständig verhinderte

Der erste Durchgang — ein kostenloser Dry-Run zur Pipeline-Prüfung — lieferte
**null Ergebnisse**: 0 von 5 Tasks, keine einzige `result.json`. Der Runner
meldete dabei `ExitCode=0` und keinerlei Fehler. Ohne den vorgeschalteten
Dry-Run wäre das erst nach dem bezahlten Lauf aufgefallen.

Alle vier Worker-Prozesse starben mit derselben Ausnahme:

```
Process SpawnProcess-1:
Traceback (most recent call last):
  File "...\multiprocessing\process.py", line 313, in _bootstrap
    self.run()
  File "...\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "...\smartbugs\sb\analysis.py", line 184, in analyser
    duration = execute(task)
  File "...\smartbugs\sb\analysis.py", line 99, in execute
    exit_code, tool_log, tool_output, sb_bin_log, docker_args = sb.docker.execute(task)
  File "...\smartbugs\sb\docker.py", line 157, in execute
    shutil.rmtree(sbdir)
  File "...\shutil.py", line 790, in rmtree
    return _rmtree_unsafe(path, onexc)
  File "...\shutil.py", line 621, in _rmtree_unsafe
    onexc(os.rmdir, fullname, err)
  File "...\shutil.py", line 617, in _rmtree_unsafe
    os.rmdir(fullname)
PermissionError: [WinError 5] Zugriff verweigert: 'C:\\Users\\<benutzer>\\AppData\\Local\\Temp\\tmp34q1mbcp\\bin'
```

### Ursache

SmartBugs legt je Task ein Temp-Verzeichnis an, kopiert den Contract und die
Hilfsskripte samt `solc` hinein, mountet es in den Container und löscht es im
`finally`-Block von `sb.docker.execute` wieder. Unter Docker Desktop ist das
Handle auf die gerade im Container ausgeführten Dateien zu diesem Zeitpunkt
noch offen; `os.rmdir` auf das bereits geleerte `bin` scheitert mit
`WinError 5`.

Belege:

* Die acht zurückgebliebenen Temp-Verzeichnisse enthielten jeweils ein
  **leeres** `bin\` — der Inhalt war gelöscht, nur das Verzeichnis blieb.
* Dieselben Verzeichnisse ließen sich Minuten später ohne Weiteres entfernen.

Der Schaden entsteht durch die Fehlerbehandlung eine Ebene höher:
`sb/analysis.py:96` wiederholt Docker-Probleme nur für `sb.errors.SmartBugsError`.
`PermissionError` fällt nicht darunter, entkommt aus dem `finally`-Block und
beendet den Worker-Prozess — **bevor** `result.json`, `result.log` und
`smartbugs.json` geschrieben werden (`sb/analysis.py:110-131`). Der
Hauptprozess bemerkt davon nichts und meldet Erfolg. Der Ergebnisverlust ist
also vollständig und lautlos.

### Behebung

Neu in `sb/docker.py`: `rmtree_retry` wiederholt das Löschen mit kurzem
Backoff. Ein Verzeichnis, das dauerhaft gesperrt bleibt, wird über
`sb.debug.log` gemeldet und liegen gelassen, statt eine Ausnahme zu werfen —
ein Aufräum-Problem darf eine bereits fertige Analyse nie verwerfen.

Abgesichert durch `tests/test_docker_cleanup.py` (drei Tests: normaler Fall,
vorübergehende Sperre, dauerhafte Sperre). Testsuite gesamt: 44 bestanden.

Verifikation an der ursprünglichen Reproduktion: derselbe Dry-Run lieferte
danach 5 von 5 Tasks und 5 `result.json`.

> **Einordnung.** Das ist eine Änderung an SmartBugs-Fremdcode und gehört als
> solche in `BA-EIGENANTEIL.md`. Die 19 Altläufe sind davon nicht berührt —
> sie liefen vor dem Auftreten des Problems und sind unverändert. Warum es
> jetzt auftritt und im Juli nicht, ist nicht abschließend geklärt; die
> naheliegende Erklärung ist ein zwischenzeitliches Update von Docker Desktop
> (aktuell Server 29.0.1). Der Fix ist reine Robustheit und ändert an der
> Analyse selbst nichts.

---

## 3. Befehle

Alle Läufe schreiben in **neue** Ergebnisordner; keine Altdaten wurden berührt.

```powershell
# Satz A, GPTScan
.\run_curated.ps1 -Tool gptscan -SkipClone -RunIdSuffix demo_swc `
  -FilePattern '..\smartbugs-curated\dataset:..\demolauf_satzA.sbd'

# Satz B, GPTScan
.\run_curated.ps1 -Tool gptscan -SkipClone -RunIdSuffix demo_defi `
  -FilePattern 'samples\gptscan\mwevariety_fixed:..\demolauf_satzB.sbd'

# LLMSmartAudit, Kostenprobe an einem Contract
.\run_curated.ps1 -Tool llmsmartaudit -SkipClone -RunIdSuffix demo_kostenprobe `
  -FilePattern 'samples\gptscan\mwevariety_fixed:20_Synth.sol'

# LLMSmartAudit, Satz A und die vier verbliebenen aus Satz B
.\run_curated.ps1 -Tool llmsmartaudit -SkipClone -RunIdSuffix demo_swc_llm `
  -FilePattern '..\smartbugs-curated\dataset:..\demolauf_satzA.sbd'
.\run_curated.ps1 -Tool llmsmartaudit -SkipClone -RunIdSuffix demo_defi_llm `
  -FilePattern 'samples\gptscan\mwevariety_fixed:..\demolauf_satzB_rest.sbd'
```

Auswertung im Anschluss:

```powershell
python analysis_tools\parser_audit.py smartbugs\results\<tool>\<lauf>
python analysis_tools\errors_fails_report.py smartbugs\results\<tool>\<lauf>
python evaluate_curated.py --suffix demo_swc     --tools gptscan
python evaluate_curated.py --suffix demo_swc_llm --tools llmsmartaudit
```

Der Runner wurde dabei als Kindprozess gestartet und dessen Ausgabe per
`cmd /c "... > datei 2>&1"` protokolliert. Grund: `run_curated.ps1` schreibt
mit `Out-Host` direkt an die Konsole, sodass `Tee-Object` nichts sieht; und
eine Umleitung im selben PowerShell-5.1-Prozess erzeugt aus nativem stderr
ErrorRecords, die den Runner (`ErrorActionPreference = Stop`) abbrechen. Genau
das ist im ersten Versuch passiert.

---

## 4. Ergebnis GPTScan

### Satz A — SWC/DASP-Contracts

| Contract | Findings | Errors | Fails | LLM-Calls | Kosten |
|---|---:|---:|---:|---:|---:|
| `access_control/FibonacciBalance.sol` | 0 | 0 | 0 | 0 | $0,0000 |
| `arithmetic/integer_overflow_1.sol` | 0 | 0 | 0 | 0 | $0,0000 |
| `bad_randomness/guess_the_random_number.sol` | 0 | 0 | 0 | 0 | $0,0000 |
| `denial_of_service/dos_address.sol` | 0 | 0 | 0 | 0 | $0,0000 |
| `time_manipulation/ether_lotto.sol` | 0 | 0 | 0 | 0 | $0,0000 |
| **Summe** | **0** | **0** | **0** | **0** | **$0,0000** |

Laufzeit gesamt: 39 s. Alle fünf Contracts wurden übersetzt, keine
Compile-Failures, keine Timeouts.

Jeder der fünf Tasks protokolliert in `result.json` die Info-Zeile:

```
GPTScan run: backend=deepseek/deepseek-v4-flash, llm_calls=0, est_cost_usd=0.0000
```

Das ist der eigentliche Befund: **`llm_calls=0`**. GPTScan hat kein einziges
Mal das Modell gefragt. Es hat die Contracts in seiner vorgelagerten Stufe
verworfen, weil keine Funktion zu einem seiner zehn MWE-Szenarien passt. Die
Null ist also kein „nichts gefunden", sondern ein „gar nicht erst gesucht" —
und sie belegt zugleich, dass es sich um einen echten Live-Lauf handelte
(Backend und Modell stehen in derselben Zeile), nicht um einen Dry-Run.

### Satz B — DeFi-Contracts

| Contract | Findings | Errors | Fails | LLM-Calls | Laufzeit | Kosten |
|---|---:|---:|---:|---:|---:|---:|
| `20_Synth.sol` | 4 | 6 | 0 | 65 | 692,5 s | $0,0236 |
| `29_HybridPool.sol` | 3 | 6 | 0 | 28 | 391,0 s | $0,0107 |
| `5_DAO.sol` | 5 | 0 | 0 | 36 | 431,8 s | $0,0138 |
| `5_Pools.sol` | 4 | 5 | 0 | 28 | 412,6 s | $0,0142 |
| `70_VaderPoolV2.sol` | 5 | 0 | 0 | 36 | 288,8 s | $0,0102 |
| **Summe** | **21** | **17** | **0** | **193** | **2216,6 s** | **$0,0725** |

Wanduhrzeit des Laufs: 16:25 min (bei `--processes 4`). Keine
Compile-Failures, keine Timeouts, **keine Fails**.

Getroffene MWE-Regeln — sechs verschiedene:

| Regel | Contracts |
|---|---|
| MWE-200 Insecure LP Token Value Calculation | 20_Synth (2×), 29_HybridPool (2×), 70_VaderPoolV2 (2×) |
| MWE-201 Insecure Vote Calculation | 5_DAO (5×) |
| MWE-203 Approval Not Revoked | 70_VaderPoolV2 |
| MWE-205 Front Running | 20_Synth, 5_Pools |
| MWE-206 No Slippage Limit Check | 20_Synth, 5_Pools (3×), 70_VaderPoolV2 (2×) |
| MWE-207 Unauthorized Transfer | 29_HybridPool |

Alle Findings tragen `severity: high` und nennen Datei, Start- und Endzeile,
Beschreibung, Empfehlung und den internen GPTScan-Code. Beispiel aus
`5_DAO.sol`:

```json
{
  "filename": "5_DAO.sol",
  "line": 228,
  "line_end": 241,
  "name": "MWE-201: Insecure Vote Calculation",
  "severity": "high",
  "message": "Calculating vote amount can be manipulated to cause flashloan attacks.\nRecommendation: In vote calculation, add a check for tokens that may come from a flash loan.\nGPTScan code: insecure-vote-calculation"
}
```

### Der Kontrast in einem Satz

Dasselbe Werkzeug, dieselbe Konfiguration, dasselbe Modell: auf fünf klassischen
SWC-Contracts **0 Findings bei 0 Modellaufrufen und $0,00**, auf fünf
DeFi-Contracts **21 Findings aus sechs verschiedenen Regeln bei 193
Modellaufrufen und $0,07**.

---

## 5. Errors in Satz B — im Wortlaut

17 Errors auf drei Contracts, dabei **null Fails**: GPTScan hat die Probleme
jeweils bemerkt, behandelt und weitergearbeitet. Die Meldungen stehen hier
unverändert so, wie der Parser sie ausgibt (einschließlich der vom Werkzeug
selbst gekürzten Tracebacks).

**`20_Synth.sol`** (6):

```
ERROR    tasks: Current File: /work/input/20_Synth.sol, current function: _burn, current vul: price-manipulation
ERROR    tasks: Current File: /work/input/20_Synth.sol, current function: _getAddedBaseAmount, current vul: price-manipulation
ERROR    tasks: Current File: /work/input/20_Synth.sol, current function: removeForMember, current vul: price-manipulation
ERROR    tasks: Static analysis failed: Invalid args
ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation
ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation
```

**`29_HybridPool.sol`** (6):

```
ERROR    tasks: Current File: /work/input/29_HybridPool.sol, current function: _burn, current vul: price-manipulation
ERROR    tasks: Current File: /work/input/29_HybridPool.sol, current function: burn, current vul: price-manipulation
ERROR    tasks: Static analysis failed: Invalid args
ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 232, in si ... lyze_pipeline.py" , line 87, in ask_with_timeout raise TimeoutError("Timeout") TimeoutError: Timeout
ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation
TimeoutError: Timeout
```

**`5_Pools.sol`** (5):

```
ERROR    tasks: Current File: /work/input/5_Pools.sol, current function: burnSynth, current vul: price-manipulation
ERROR    tasks: Current File: /work/input/5_Pools.sol, current function: mintSynth, current vul: price-manipulation
ERROR    tasks: Current File: /work/input/5_Pools.sol, current function: syncSynth, current vul: price-manipulation
ERROR    tasks: Static analysis failed: Invalid args
ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation
```

Einordnung, ausdrücklich getrennt vom Wortlaut:

* `Static analysis failed: Invalid args` und die `Current File: ...`-Zeilen
  gehören zusammen. Sie treten immer gemeinsam auf und markieren Funktionen,
  bei denen GPTScans statische Bestätigungsstufe einen LLM-Kandidaten nicht
  prüfen konnte. Die betroffenen Kandidaten fallen damit heraus — die Contracts
  liefern trotzdem Findings.
* `validate_description` ist eine interne Plausibilitätsprüfung von GPTScan
  gegen die Modellantwort. Sie schlägt an, wenn das Modell eine Variable
  beschreibt, die so nicht auffindbar ist. Auch das ist bestimmungsgemäßes
  Verwerfen, kein Absturz.
* `TimeoutError: Timeout` in `29_HybridPool.sol` betrifft **einen einzelnen
  Modellaufruf** innerhalb des Tasks, nicht den Task. Der Task lief mit
  Exit-Code 0 zu Ende und lieferte drei Findings.

Zusätzlich meldet der Runner **4 Review-Kandidaten**: Contracts, bei denen die
statische Stufe LLM-Kandidaten verworfen hat. Laut `result.json` ist das
durchweg das bestimmungsgemäße False-Positive-Filtering:

```
static confirmation filtered LLM candidates: 8 before, 4 after (intended behaviour)   20_Synth.sol
static confirmation filtered LLM candidates: 5 before, 4 after (intended behaviour)   29_HybridPool.sol
static confirmation filtered LLM candidates: 8 before, 5 after (intended behaviour)   5_Pools.sol
static confirmation filtered LLM candidates: 10 before, 5 after (intended behaviour)  70_VaderPoolV2.sol
```

### Nebenbefund: der WARNING-Blindfleck ist reproduziert

`70_VaderPoolV2.sol` enthält in `result.log`:

```
[08/02/26 18:59:38] WARNING  utils: Cannot find functionB or same   utils.py:177
                             function
```

In `result.json` desselben Tasks stehen **0 Errors**. Damit ist der in
`BA-VERIFIKATIONSBERICHT.md`, Abschnitt 3.2, beschriebene Blindfleck im neuen
Lauf bestätigt: Der Parser übernimmt diese WARNING-Zeile nicht.

Zwei Beobachtungen zur Nachprüfbarkeit:

* Die Meldung ist von Rich über **zwei Zeilen umbrochen**. Ein Suchmuster über
  den vollständigen Satz `Cannot find functionB or same function` findet sie
  nicht. Wer den Befund nachprüft, muss nach `Cannot find function` suchen.
* Bei `5_Pools.sol` — dem zweiten im Auftrag genannten Contract — trat die
  Meldung diesmal **nicht** auf.

---

## 6. Ergebnis LLMSmartAudit

Das Werkzeug lief in drei Aufrufen: zuerst eine Kostenprobe an einem Contract
(um vor dem Rest abschätzen zu können, worauf man sich einlässt), dann Satz A,
dann die vier verbliebenen aus Satz B. `20_Synth.sol` liegt deshalb in einem
eigenen Ergebnisordner, gehört inhaltlich aber zu Satz B.

### Satz A — SWC/DASP-Contracts

| Contract | Findings | Errors | Fails | Laufzeit |
|---|---:|---:|---:|---:|
| `access_control/FibonacciBalance.sol` | 13 | 0 | 0 | 993,5 s |
| `arithmetic/integer_overflow_1.sol` | 5 | 0 | 0 | 382,8 s |
| `bad_randomness/guess_the_random_number.sol` | 5 | 0 | 0 | 510,9 s |
| `denial_of_service/dos_address.sol` | 5 | 0 | 0 | 446,9 s |
| `time_manipulation/ether_lotto.sol` | 5 | 0 | 0 | 777,8 s |
| **Summe** | **33** | **0** | **0** | **3111,9 s** |

Wanduhrzeit 16:39 min bei `--processes 4`. Alle fünf Tasks meldeten
`categories checked: 41/41`.

**Die Ground Truth wurde in allen fünf Fällen getroffen** — nicht nur in der
Summe, sondern jeweils beim richtigen Contract:

| Contract | Ground-Truth-Kategorie | passendes Finding | Schwere |
|---|---|---|---|
| `FibonacciBalance.sol` | access_control | Missing Access Control / Authorization; Missing onlyOwner Modifier; Unprotected Ownership Change | high |
| `integer_overflow_1.sol` | arithmetic | Integer Overflow / Underflow | high |
| `guess_the_random_number.sol` | bad_randomness | Predictable / Weak Randomness | medium |
| `dos_address.sol` | denial_of_service | Denial of Service; Gas-Limit / Unbounded Operation | medium |
| `ether_lotto.sol` | time_manipulation | Timestamp Dependence | low |

Dazu kommt allerdings erheblicher Beifang: `FibonacciBalance.sol` liefert 13
Findings, von denen drei die Ground-Truth-Kategorie treffen. Ob die übrigen
zehn zutreffen, wurde hier **nicht** geprüft — dafür gibt es keine Referenz.
Bemerkenswert außerdem, dass die eigentliche Schwachstelle von
`ether_lotto.sol` nur als `low` eingestuft wird.

Verteilung über alle 33 Findings — 9× high, 20× medium, 4× low:

```
 5  Missing Withdrawal Function (locked funds)
 4  Transaction Order Dependence (front-running)
 2  Integer Overflow / Underflow
 2  Gas-Limit / Unbounded Operation
 2  Price Manipulation (centralized pricing)
 2  Missing Access Control / Authorization
 2  Lack of Input Validation
 2  Denial of Service
 2  Timestamp Dependence
 2  Predictable / Weak Randomness
 1  Reentrancy
 1  Storage/Memory Data Inconsistency
 1  Missing onlyOwner Modifier
 1  Unprotected Ownership Change
 1  Centralization Risk
 1  Uninitialized Return Variable
 1  Strict Balance Equality (this.balance ==)
 1  Missing Fallback Function (rejected/locked ether)
```

#### Gegenprobe mit `evaluate_curated.py`

Satz A ist der einzige Teil des Demolaufs mit Ground Truth, lässt sich also
beziffern statt nur behaupten. Für GPTScan (`--suffix demo_swc`) ist das
Ergebnis über alle zehn Kategorien 0 erkannt, 0 geflaggt — konsistent mit
`llm_calls=0`. Für LLMSmartAudit (`--suffix demo_swc_llm`):

```
Kategorie                    Contracts  Erkannt   Recall  Geflaggt  Precision     F1
access_control                      18        1       6%         2        50%    10%
arithmetic                          15        1       7%         2        50%    12%
bad_randomness                       8        1      12%         2        50%    20%
denial_of_service                    6        1      17%         2        50%    25%
front_running                        4        0       0%         4         0%      -
other                                3        0       0%         0          -      -
reentrancy                          31        0       0%         1         0%      -
short_addresses                      1        0       0%         0          -      -
time_manipulation                    5        1      20%         2        50%    29%
unchecked_low_level_calls           52        0       0%         0          -      -
GESAMT                             143        5       3%        15        33%     6%
Finding-Dichte je Contract: Mittel 6.6, Median 5, Max 13, Contracts ohne Findings: 0
result.json: 5 (fehlend: 138) | Findings: 33 (DASP-mapped: 20, unmapped: 13) | Findings ausserhalb des Labels: 10 Kategorie-Treffer
```

**Diese Tabelle ist nur teilweise lesbar, und zwar aus einem Grund, der in der
letzten Zeile steht: `result.json: 5 (fehlend: 138)`.** Das Skript rechnet
immer gegen die vollen 143 Contracts des Datensatzes. Recall, Precision und F1
beziehen sich daher auf 143 Contracts, von denen 138 nie analysiert wurden —
diese Prozentwerte sagen über den Demolauf nichts aus.

Aussagekräftig sind zwei andere Angaben:

* **Spalte `Erkannt`: 1 in jeder der fünf Kategorien, die überhaupt vertreten
  waren.** Das ist die unabhängige Bestätigung der Tabelle oben — jeder der
  fünf Contracts wurde in seiner Ground-Truth-Kategorie erkannt.
* **`DASP-mapped: 20, unmapped: 13`.** Von 33 Findings lassen sich 20 auf eine
  DASP-Klasse abbilden; 13 sind Kategorien, für die der Datensatz kein Label
  kennt (Centralization Risk, Missing Withdrawal Function und ähnliche). Sie
  sind deshalb weder richtig noch falsch — sie sind unprüfbar.

Ein Detail verdient Beachtung: `front_running` wurde bei **vier** Contracts
geflaggt, von denen **keiner** so gelabelt ist (Precision 0%). Der Detektor
„Transaction Order Dependence" meldet also auf vier von fünf Contracts an,
unabhängig davon, worum es geht. Bei den vier zutreffenden Kategorien liegt die
Precision jeweils bei 50%: ein richtiger Treffer, ein zusätzlicher Contract,
der dieses Label nicht trägt.

### Satz B — DeFi-Contracts

| Contract | Findings | Errors | Fails | Laufzeit |
|---|---:|---:|---:|---:|
| `20_Synth.sol` (Kostenprobe) | 11 | 0 | 0 | 1970,6 s |
| `29_HybridPool.sol` | 5 | 0 | 0 | 1791,9 s |
| `5_DAO.sol` | 14 | 0 | 0 | 1374,7 s |
| `5_Pools.sol` | 11 | 0 | 0 | 1589,1 s |
| `70_VaderPoolV2.sol` | 8 | 0 | 0 | 1725,2 s |
| **Summe** | **49** | **0** | **0** | **8451,5 s** |

Wanduhrzeit 32:54 min (Kostenprobe, ein Task allein) plus 29:55 min (die
restlichen vier parallel). Auch hier durchweg `categories checked: 41/41`.

Die Klassen sind dieselbe Art wie in Satz A — allgemeine Solidity-Befunde, keine
Findings zur DeFi-Logik im Sinne der MWE-Regeln:

```
 4  Centralization Risk                     2  Unnecessary Boolean Comparison
 3  Redundant Conditional Check             2  Inconsistent Base Tokens on Migration
 3  Missing Access Control / Authorization  1  Unprotected Ownership Change
 3  Missing onlyOwner Modifier              1  Inconsistent State Initialization Order
 2  Integer Overflow / Underflow            1  Lack of Input Validation
 2  Unchecked External Call                 1  Denial of Service
 2  Unchecked Low-level Call                1  Authorization via tx.origin
 2  Reentrancy                              1  Gas-Limit / Unbounded Operation
 2  Transaction Order Dependence            1  Storage/Memory Data Inconsistency
 2  Timestamp Dependence                    1  Uninitialized Return Variable
                                            1  Precision Loss / Integer-Division Truncation
```

### Drei Eigenschaften, die für die Auswertung zählen

* **Keine Errors, keine Fails, keine Compile-Failures** in allen zehn Tasks.
  `errors_fails_report.py` und `parser_audit.py` melden über die drei Läufe
  10 Tasks, 10 clean, 0 Signale, 0 Gaps.
* **Keine Zeilennummern.** Jedes Finding trägt `line: None`. Die Fundstelle
  steht allenfalls im Fließtext der Meldung. GPTScan liefert dagegen `line` und
  `line_end`.
* **Keine Kostendaten.** Das Werkzeug gibt weder Token- noch Preisangaben aus.
  Das `result.log` von `20_Synth.sol` umfasst 9.191.466 Bytes in 88.535 Zeilen
  — vollständiges Multi-Agent-Transkript, aber keine Abrechnungszeile. Eine
  Kostenaussage ist deshalb nur indirekt möglich (siehe Abschnitt 8).

### Gesamtbilanz beider Werkzeuge

| | GPTScan | LLMSmartAudit |
|---|---:|---:|
| Findings Satz A | **0** | **33** |
| Findings Satz B | **21** | **49** |
| Errors / Fails | 17 / 0 | 0 / 0 |
| LLM-Aufrufe | 193 | nicht ausgewiesen |
| Kosten | $0,0725 | nicht ausgewiesen |
| Wanduhrzeit | 17:04 min | 79:28 min |
| Zeilennummern | ja | nein |

---

## 7. Konsolenausgaben im Wortlaut

Vollständig, ungekürzt und unverändert. `WRAP:`-Zeilen stammen vom
Protokoll-Wrapper, nicht von SmartBugs.

### 7.1 GPTScan, Satz A

```
WRAP: Satz=A Tool=gptscan Suffix=demo_swc Pattern=..\smartbugs-curated\dataset:..\demolauf_satzA.sbd
[20:53:57] Prechecks...
[20:53:58] DEEPSEEK_API_KEY geladen (Laenge 35). Wert wird nicht ausgegeben.
[20:53:58] Clone uebersprungen (-SkipClone). FilePattern: ..\smartbugs-curated\dataset:..\demolauf_satzA.sbd
[20:53:58] Starte GPTScan (processes=4, timeout=1800s, runid=curated_gptscan_demo_swc)...
Welcome to SmartBugs 2.1.1!
Collecting files ...
5 files to analyse
Assembling tasks ...
5 tasks to execute
Starting task 1/5: gptscan and access_control/FibonacciBalance.sol
Starting task 2/5: gptscan and denial_of_service/dos_address.sol
Starting task 3/5: gptscan and arithmetic/integer_overflow_1.sol
Starting task 4/5: gptscan and bad_randomness/guess_the_random_number.sol
1/5 completed, ETC 0:24:04
Starting task 5/5: gptscan and time_manipulation/ether_lotto.sol
2/5 completed, ETC 0:15:05
3/5 completed, ETC 0:08:38
4/5 completed, ETC 0:03:47
5/5 completed, ETC 0:00:00
Analysis completed in 0:00:39.
[20:54:41] GPTScan beendet, ExitCode=0 (Log: smartbugs\results\logs\curated_gptscan_demo_swc.log)
[20:54:41] Scanne GPTScan-Logs auf Compile-Fehler/Degradation...
[20:54:41] GPTScan-Bilanz: 5 Tasks | 0 Compile-Failures/Timeouts (curated_compile_failures_demo_swc.csv) | 0 Review-Kandidaten (curated_review_candidates_demo_swc.csv) | Kosten gesamt ~$0,0000
[20:54:41] Auswertung: Compile-Failures/Timeouts zaehlen NICHT als 'clean' (result.json dort still-unvollstaendig).
[20:54:41] Review-Kandidaten sind KEIN Automatik-Ausschluss: Kandidaten-Verwurf durch die Static-Stufe ist meist GPTScans normales False-Positive-Filtering - nur manuell nachpruefen.
[20:54:41] gptscan: 5 result.json unter <repo>\smartbugs\results\gptscan\curated_demo_swc
[20:54:41] Errors/Fails-Bilanz:
tool/run                                        tasks  clean err.tasks fail.tasks  errors  fails no-compile
-----------------------------------------------------------------------------------------------------------
gptscan/curated_gptscan_demo_swc                    5      5         0          0       0      0          0
-----------------------------------------------------------------------------------------------------------
TOTAL                                               5      5         0          0       0      0          0
Markdown: <repo>\docs\errors-fails-demo_swc.md
[20:54:41] Spalte 'nicht uebersetzt': dort ist ein leeres Finding-Ergebnis unbestimmt, NICHT sauber.
[20:54:41] CSV-Auswertung: cd smartbugs; .venv\Scripts\python.exe -m sb.results2csv results\gptscan\curated_demo_swc results\llmsmartaudit\curated_demo_swc > ..\curated_results.csv
[20:54:41] Parser-Vollstaendigkeit pruefen: python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_demo_swc
[20:54:41] Fertig.
WRAP: ExitCode=0
```

### 7.2 GPTScan, Satz B

```
WRAP: Satz=B Tool=gptscan Suffix=demo_defi Pattern=samples\gptscan\mwevariety_fixed:..\demolauf_satzB.sbd
[20:54:57] Prechecks...
[20:54:58] DEEPSEEK_API_KEY geladen (Laenge 35). Wert wird nicht ausgegeben.
[20:54:58] Clone uebersprungen (-SkipClone). FilePattern: samples\gptscan\mwevariety_fixed:..\demolauf_satzB.sbd
[20:54:58] Starte GPTScan (processes=4, timeout=1800s, runid=curated_gptscan_demo_defi)...
Welcome to SmartBugs 2.1.1!
Collecting files ...
5 files to analyse
Assembling tasks ...
5 tasks to execute
Starting task 1/5: gptscan and 70_VaderPoolV2.sol
Starting task 2/5: gptscan and 5_DAO.sol
Starting task 3/5: gptscan and 5_Pools.sol
Starting task 4/5: gptscan and 29_HybridPool.sol
1/5 completed, ETC 0:24:58
Starting task 5/5: gptscan and 20_Synth.sol
2/5 completed, ETC 0:16:25
3/5 completed, ETC 0:09:52
4/5 completed, ETC 0:04:33
5/5 completed, ETC 0:00:00
Analysis completed in 0:16:25.
[21:11:27] GPTScan beendet, ExitCode=0 (Log: smartbugs\results\logs\curated_gptscan_demo_defi.log)
[21:11:27] Scanne GPTScan-Logs auf Compile-Fehler/Degradation...
[21:11:27] GPTScan-Bilanz: 5 Tasks | 0 Compile-Failures/Timeouts (curated_compile_failures_demo_defi.csv) | 4 Review-Kandidaten (curated_review_candidates_demo_defi.csv) | Kosten gesamt ~$0,0725
[21:11:27] Auswertung: Compile-Failures/Timeouts zaehlen NICHT als 'clean' (result.json dort still-unvollstaendig).
[21:11:27] Review-Kandidaten sind KEIN Automatik-Ausschluss: Kandidaten-Verwurf durch die Static-Stufe ist meist GPTScans normales False-Positive-Filtering - nur manuell nachpruefen.
[21:11:27] gptscan: 5 result.json unter <repo>\smartbugs\results\gptscan\curated_demo_defi
[21:11:27] Errors/Fails-Bilanz:
tool/run                                        tasks  clean err.tasks fail.tasks  errors  fails no-compile
-----------------------------------------------------------------------------------------------------------
gptscan/curated_gptscan_demo_defi                   5      2         3          0      17      0          0
-----------------------------------------------------------------------------------------------------------
TOTAL                                               5      2         3          0      17      0          0

Distinct messages: 13 (0 fails, 13 errors)

  most widespread errors:
        3 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Static analysis failed: Invalid args
        3 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si
        1 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Current File: /work/input/20_Synth.sol, current function: _burn, current vul: price-
        1 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Current File: /work/input/20_Synth.sol, current function: _getAddedBaseAmount, curre
        1 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Current File: /work/input/20_Synth.sol, current function: removeForMember, current v
        1 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Current File: /work/input/29_HybridPool.sol, current function: _burn, current vul: p
        1 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Current File: /work/input/29_HybridPool.sol, current function: burn, current vul: pr
        1 contracts  [independent]  gptscan/curated_gptscan_demo_defi
           ERROR    tasks: Current File: /work/input/5_Pools.sol, current function: burnSynth, current vul: pri

CSV: <repo>\docs\errors-fails-demo_defi.csv
Markdown: <repo>\docs\errors-fails-demo_defi.md
[21:11:27] Spalte 'nicht uebersetzt': dort ist ein leeres Finding-Ergebnis unbestimmt, NICHT sauber.
[21:11:27] CSV-Auswertung: cd smartbugs; .venv\Scripts\python.exe -m sb.results2csv results\gptscan\curated_demo_defi results\llmsmartaudit\curated_demo_defi > ..\curated_results.csv
[21:11:27] Parser-Vollstaendigkeit pruefen: python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_demo_defi
[21:11:27] Fertig.
WRAP: ExitCode=0
```

### 7.3 LLMSmartAudit, Kostenprobe

```
WRAP: Satz=B Tool=llmsmartaudit Suffix=demo_kostenprobe Pattern=samples\gptscan\mwevariety_fixed:20_Synth.sol
[21:12:11] Prechecks...
[21:12:12] DEEPSEEK_API_KEY geladen (Laenge 35). Wert wird nicht ausgegeben.
[21:12:12] Clone uebersprungen (-SkipClone). FilePattern: samples\gptscan\mwevariety_fixed:20_Synth.sol
[21:12:12] Starte LLMSmartAudit (processes=4, timeout=5400s, runid=curated_llmsa_demo_kostenprobe)...
[21:12:12] ACHTUNG: keine Kostenbremse im Tool - erwartete Dauer ~3.5-4.5 h fuer 143 Contracts.
Welcome to SmartBugs 2.1.1!
Collecting files ...
1 files to analyse
Assembling tasks ...
1 tasks to execute
Starting task 1/1: llmsmartaudit and 20_Synth.sol
1/1 completed, ETC 0:00:00
Analysis completed in 0:32:54.
[21:45:10] LLMSmartAudit beendet, ExitCode=0 (Log: smartbugs\results\logs\curated_llmsa_demo_kostenprobe.log)
[21:45:10] llmsmartaudit: 1 result.json unter <repo>\smartbugs\results\llmsmartaudit\curated_demo_kostenprobe
[21:45:10] Errors/Fails-Bilanz:
tool/run                                        tasks  clean err.tasks fail.tasks  errors  fails no-compile
-----------------------------------------------------------------------------------------------------------
llmsmartaudit/curated_llmsa_demo_kostenprobe        1      1         0          0       0      0          0
-----------------------------------------------------------------------------------------------------------
TOTAL                                               1      1         0          0       0      0          0
Markdown: <repo>\docs\errors-fails-demo_kostenprobe.md
[21:45:10] Spalte 'nicht uebersetzt': dort ist ein leeres Finding-Ergebnis unbestimmt, NICHT sauber.
[21:45:10] CSV-Auswertung: cd smartbugs; .venv\Scripts\python.exe -m sb.results2csv results\gptscan\curated_demo_kostenprobe results\llmsmartaudit\curated_demo_kostenprobe > ..\curated_results.csv
[21:45:10] Parser-Vollstaendigkeit pruefen: python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_demo_kostenprobe
[21:45:10] Fertig.
WRAP: ExitCode=0
```

### 7.4 LLMSmartAudit, Satz A

```
WRAP: Satz=A Tool=llmsmartaudit Suffix=demo_swc_llm Pattern=..\smartbugs-curated\dataset:..\demolauf_satzA.sbd
[00:55:30] Prechecks...
[00:55:31] DEEPSEEK_API_KEY geladen (Laenge 35). Wert wird nicht ausgegeben.
[00:55:31] Clone uebersprungen (-SkipClone). FilePattern: ..\smartbugs-curated\dataset:..\demolauf_satzA.sbd
[00:55:31] Starte LLMSmartAudit (processes=4, timeout=5400s, runid=curated_llmsa_demo_swc_llm)...
[00:55:31] ACHTUNG: keine Kostenbremse im Tool - erwartete Dauer ~3.5-4.5 h fuer 143 Contracts.
Welcome to SmartBugs 2.1.1!
Collecting files ...
5 files to analyse
Assembling tasks ...
5 tasks to execute
Starting task 1/5: llmsmartaudit and denial_of_service/dos_address.sol
Starting task 2/5: llmsmartaudit and arithmetic/integer_overflow_1.sol
Starting task 3/5: llmsmartaudit and access_control/FibonacciBalance.sol
Starting task 4/5: llmsmartaudit and time_manipulation/ether_lotto.sol
1/5 completed, ETC 1:13:17
Starting task 5/5: llmsmartaudit and bad_randomness/guess_the_random_number.sol
2/5 completed, ETC 0:46:44
3/5 completed, ETC 0:27:38
4/5 completed, ETC 0:12:21
5/5 completed, ETC 0:00:00
Analysis completed in 0:16:39.
[01:12:14] LLMSmartAudit beendet, ExitCode=0 (Log: smartbugs\results\logs\curated_llmsa_demo_swc_llm.log)
[01:12:14] llmsmartaudit: 5 result.json unter <repo>\smartbugs\results\llmsmartaudit\curated_demo_swc_llm
[01:12:14] Errors/Fails-Bilanz:
tool/run                                        tasks  clean err.tasks fail.tasks  errors  fails no-compile
-----------------------------------------------------------------------------------------------------------
llmsmartaudit/curated_llmsa_demo_swc_llm            5      5         0          0       0      0          0
-----------------------------------------------------------------------------------------------------------
TOTAL                                               5      5         0          0       0      0          0
Markdown: <repo>\docs\errors-fails-demo_swc_llm.md
[01:12:15] Spalte 'nicht uebersetzt': dort ist ein leeres Finding-Ergebnis unbestimmt, NICHT sauber.
[01:12:15] CSV-Auswertung: cd smartbugs; .venv\Scripts\python.exe -m sb.results2csv results\gptscan\curated_demo_swc_llm results\llmsmartaudit\curated_demo_swc_llm > ..\curated_results.csv
[01:12:15] Parser-Vollstaendigkeit pruefen: python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_demo_swc_llm
[01:12:15] Fertig.
WRAP: ExitCode=0
```

### 7.5 LLMSmartAudit, Satz B (die vier verbliebenen)

```
WRAP: Satz=B Tool=llmsmartaudit Suffix=demo_defi_llm Pattern=samples\gptscan\mwevariety_fixed:..\demolauf_satzB_rest.sbd
[01:12:16] Prechecks...
[01:12:16] DEEPSEEK_API_KEY geladen (Laenge 35). Wert wird nicht ausgegeben.
[01:12:16] Clone uebersprungen (-SkipClone). FilePattern: samples\gptscan\mwevariety_fixed:..\demolauf_satzB_rest.sbd
[01:12:16] Starte LLMSmartAudit (processes=4, timeout=5400s, runid=curated_llmsa_demo_defi_llm)...
[01:12:16] ACHTUNG: keine Kostenbremse im Tool - erwartete Dauer ~3.5-4.5 h fuer 143 Contracts.
Welcome to SmartBugs 2.1.1!
Collecting files ...
4 files to analyse
Assembling tasks ...
4 tasks to execute
Starting task 1/4: llmsmartaudit and 29_HybridPool.sol
Starting task 2/4: llmsmartaudit and 5_DAO.sol
Starting task 3/4: llmsmartaudit and 70_VaderPoolV2.sol
Starting task 4/4: llmsmartaudit and 5_Pools.sol
1/4 completed, ETC 0:57:26
2/4 completed, ETC 0:34:07
3/4 completed, ETC 0:15:39
4/4 completed, ETC 0:00:00
Analysis completed in 0:29:55.
[01:42:15] LLMSmartAudit beendet, ExitCode=0 (Log: smartbugs\results\logs\curated_llmsa_demo_defi_llm.log)
[01:42:15] llmsmartaudit: 4 result.json unter <repo>\smartbugs\results\llmsmartaudit\curated_demo_defi_llm
[01:42:15] Errors/Fails-Bilanz:
tool/run                                        tasks  clean err.tasks fail.tasks  errors  fails no-compile
-----------------------------------------------------------------------------------------------------------
llmsmartaudit/curated_llmsa_demo_defi_llm           4      4         0          0       0      0          0
-----------------------------------------------------------------------------------------------------------
TOTAL                                               4      4         0          0       0      0          0
Markdown: <repo>\docs\errors-fails-demo_defi_llm.md
[01:42:15] Spalte 'nicht uebersetzt': dort ist ein leeres Finding-Ergebnis unbestimmt, NICHT sauber.
[01:42:15] CSV-Auswertung: cd smartbugs; .venv\Scripts\python.exe -m sb.results2csv results\gptscan\curated_demo_defi_llm results\llmsmartaudit\curated_demo_defi_llm > ..\curated_results.csv
[01:42:15] Parser-Vollstaendigkeit pruefen: python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_demo_defi_llm
[01:42:15] Fertig.
WRAP: ExitCode=0
```

### 7.6 Nachgelagerte Prüfungen

```
===== parser_audit =====
tool/run                                       tasks  signals  GAPS  gap breakdown
--------------------------------------------------------------------------------------------------------------
llmsmartaudit/curated_llmsa_demo_defi_llm          4        0     0  -
llmsmartaudit/curated_llmsa_demo_kostenprobe       1        0     0  -
llmsmartaudit/curated_llmsa_demo_swc_llm           5        0     0  -
--------------------------------------------------------------------------------------------------------------
TOTAL                                             10        0     0

===== parser_audit, beide GPTScan-Laeufe =====
tool/run                                       tasks  signals  GAPS  gap breakdown
--------------------------------------------------------------------------------------------------------------
gptscan/curated_gptscan_demo_defi                  5       17     0  -
gptscan/curated_gptscan_demo_swc                   5        0     0  -
--------------------------------------------------------------------------------------------------------------
TOTAL                                             10       17     0
```

---

## 8. Was das Ergebnis heißt — und was nicht

### Was es zeigt

**Die Kette funktioniert.** 20 Tasks über zwei Werkzeuge und zwei Datensätze,
alle mit Exit-Code 0, kein einziger Fail, keine Compile-Failure, kein Timeout.
Alle vier bzw. fünf Ergebnisdateien je Task wurden geschrieben und ließen sich
auswerten.

**Der erwartete Kontrast ist eingetreten, und zwar deutlicher als formuliert.**
GPTScan findet auf den fünf SWC-Contracts nichts — aber der eigentliche Befund
ist `llm_calls=0`. Das Werkzeug hat dort **gar nicht erst gesucht**: seine
vorgelagerte Stufe fand keine Funktion, die zu einem der zehn MWE-Szenarien
passt, und verwarf die Contracts vor dem ersten Modellaufruf. Ein Nullergebnis
von GPTScan auf klassischen SWC-Schwachstellen ist deshalb keine Aussage über
diese Schwachstellen — es ist die Aussage, dass das Werkzeug für sie nicht
zuständig ist. Auf den DeFi-Contracts, für die es gebaut wurde, liefert
dasselbe Werkzeug 21 Findings aus sechs verschiedenen MWE-Regeln.

**LLMSmartAudit ist das Gegenstück.** Es findet auf beiden Sätzen etwas (33
bzw. 49), trifft in Satz A die Ground-Truth-Kategorie bei allen fünf
Contracts — aber es meldet in Satz B **nicht** die Findings zur DeFi-Logik, auf
die GPTScans MWE-Regeln zielen, sondern dieselbe Art allgemeiner
Solidity-Befunde wie in Satz A. Auf `20_Synth.sol`
überschneiden sich die beiden Werkzeuge praktisch nur bei Front-Running
(GPTScan: MWE-205, LLMSmartAudit: Transaction Order Dependence). Die Werkzeuge
konkurrieren also weniger, als sie einander ergänzen.

### Was es nicht zeigt

**Keine Messwerte.** Zehn Contracts sind keine Stichprobe. Die Zahlen in
diesem Bericht belegen Funktionsfähigkeit, nicht Erkennungsleistung.

**Keine Aussage über Richtigkeit.** Geprüft wurde, *dass* Findings entstehen
und *ob* sie die Ground-Truth-Kategorie treffen — nicht, ob sie zutreffen.
`FibonacciBalance.sol` liefert 13 Findings, von denen drei zur Ground Truth
gehören; die übrigen zehn sind ungeprüft. Falsch-Positiv-Raten lassen sich
hieraus nicht ableiten.

**Die Ausgabe ist nicht deterministisch.** Gegenüber dem Altlauf
`curated_mwefixed_live` wichen die Findings je Contract ab, bei gleichem
Werkzeug, gleichem Modell und gleicher Datei:

| Contract | Altlauf | dieser Lauf |
|---|---:|---:|
| `20_Synth.sol` | 6 | 4 |
| `5_Pools.sol` | 5 | 4 |
| `29_HybridPool.sol` | 4 | 3 |
| `5_DAO.sol` | 4 | 5 |
| `70_VaderPoolV2.sol` | 4 | 5 |

Auch die MWE-Regeln je Contract deckten sich nicht vollständig: bei
`5_Pools.sol` fehlte diesmal MWE-200. Wer Läufe vergleicht, vergleicht damit
immer auch Rauschen.

**Aufwand und Kosten wichen erheblich von den Altläufen ab.** GPTScan
brauchte 28–65 LLM-Aufrufe je DeFi-Contract statt eines Medians von 9,5, und
$0,0102–0,0236 statt $0,0013. LLMSmartAudit brauchte für `20_Synth.sol`
1970 s — mehr als das Doppelte des bisherigen Maximums von 923 s und das
7,5-Fache des Medians von 264 s. Ob das am Contract, am Modellverhalten oder
am Backend liegt, ist offen; für eine Kostenplanung heißt es, dass die
Erfahrungswerte der Altläufe keine verlässliche Untergrenze sind.

**Zu den Kosten von LLMSmartAudit lässt sich weiterhin nichts Belastbares
sagen.** Das Werkzeug weist keine aus. Die Angabe „~$1,5–3 für 143 Contracts"
in `run_curated.ps1` stammt aus dem Smoke-Test und ist eine Schätzung, keine
Messung.

**`parser_audit.py` meldet 0 Gaps — das ist schwächer, als es klingt.** Das
Werkzeug wertet nur `ERROR` und `CRITICAL` als Signal (`_LOG_ERROR`,
`_INTERESTING`); `WARNING` steht nicht in der Liste. Genau in dieser Lücke
liegt der in Abschnitt 5 reproduzierte Blindfleck bei `70_VaderPoolV2.sol`.
Die Null bedeutet also: keine der *gesuchten* Meldungen ging verloren.

### Der wichtigste Nebenertrag

Dass der Lauf überhaupt einen Blocker zutage gefördert hat (Abschnitt 2), ist
für die Arbeit wertvoller als die Findings selbst. Ein Fehler, der Ergebnisse
lautlos auf null setzt und dabei Exit-Code 0 meldet, ist die unangenehmste
Sorte: Ohne den vorgeschalteten kostenlosen Dry-Run wäre er erst nach dem
bezahlten Lauf aufgefallen — und in einem Volllauf über 143 Contracts wäre die
Fehlersuche ungleich teurer gewesen.
