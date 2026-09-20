# Die drei Werkzeuge im Vergleich

Was GPTScan, LLMSmartAudit und Slither tun, wie sie unter SmartBugs aufgerufen
werden und was die eigenen Messungen über sie sagen. Alle Zahlen sind gegen die
Rohergebnisse unter `smartbugs/results/` geprüft; die Quelle steht jeweils
dabei.

**Eine Vorbemerkung, ohne die der Rest irreführend wäre.** Die beiden Korpora
messen Unterschiedliches. `smartbugs-curated` labelt klassische
SWC/DASP-Schwachstellen, `mwevariety_fixed` besteht aus DeFi-Contracts ohne
annotierten Referenzstand. GPTScans Zieldomäne ist die zweite Menge, nicht die
erste. Eine Tabelle, die GPTScans 0 % Recall auf curated neben LLMSmartAudits
97 % stellt und daraus eine Rangfolge ableitet, vergleicht nicht zwei Werkzeuge,
sondern ein Werkzeug mit der Frage, für die es nicht gebaut wurde. Abschnitt 5
nimmt das auseinander.

---

## 1. GPTScan

### Architektur

GPTScan koppelt ein LLM mit leichter Programmanalyse. Es sucht nicht nach
Code-Mustern, sondern nach **10 DeFi-Logik-Szenarien** — den Regeln `MWE-200`
bis `MWE-209`, etwa „Insecure LP Token Value Calculation", „No Slippage Limit
Check" oder „Approval Not Revoked". Jede Regel ist als *Szenario* („wonach in
der Funktion gesucht wird") plus *Eigenschaft* („welche Bedingung sie verdächtig
macht") formuliert.

Die Pipeline arbeitet in vier Stufen; ihre Zwischenstände stehen in der Zeile
`GPTSCAN_META`, die der Entrypoint aus `/output.json.metadata.json` ins
`result.log` schreibt:

| Stufe | Feld in `GPTSCAN_META` | Was passiert |
|---|---|---|
| Vorfilter | `*_after_filter` | Schlüsselbegriffe je Szenario; ohne Treffer kein LLM-Aufruf |
| Szenario-Abgleich | `*_after_step_1` | das LLM entscheidet, ob das Szenario zutrifft |
| Eigenschafts-Prüfung | `*_after_step_2` | das LLM prüft die verdächtige Bedingung |
| Statische Bestätigung | `*_after_static`, `vul_before_static`, `vul_after_static` | Daten-/Kontrollfluss am **kompilierten** Contract; verwirft, was sich nicht erhärten lässt |

Die vierte Stufe ist der Präzisionsschutz und **setzt eine erfolgreiche
Kompilierung voraus**. Scheitert sie, läuft GPTScan im degradierten
LLM-only-Modus weiter; der Parser markiert das als Info `analysis degraded`, und
ein Ergebnis „keine Findings" ist dann unbestimmt, nicht sauber. Genau dieser
Zustand war der Anlass für die Korpus-Reparatur
([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md)).

### Ein- und Ausgabe

Eingabe ist ein **Verzeichnis** mit genau einer `.sol`-Datei — GPTScan hat keine
Contract-Auswahl, `src/tasks.py::simple_cli` berichtet über alles, was im
übergebenen Verzeichnis kompiliert. Ausgabe ist `/output.json` im Format
`{"version", "success", "message", "results"}`, dazu
`/output.json.metadata.json` mit Token, Kosten und Stufenzahlen.

Gemeldet wird je Finding: Regel (`MWE-…`), Funktionsname, Zeilenbereich,
Severity (durchgehend `high`), Begründung und Empfehlung. **Nicht** gemeldet
wird eine Confidence.

### Aufruf im Container

```
'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN' '$MAIN'
```

`smartbugs/tools/gptscan/scripts/do_solidity.sh` tut der Reihe nach:

1. legt den von SmartBugs mitgelieferten `solc` über `$BIN` in den `PATH`
   (`solc: yes` in der `config.yaml`);
2. reduziert bei `MAIN=1` die Quelle über `main_contract.py` auf den Contract,
   nach dem die Datei benannt ist — mit `--verify-compile`, und stellt die
   Vollquelle wieder her, wenn die Reduktion nicht mehr kompiliert. Exit 127
   heißt: kein Contract dieses Namens;
3. teilt den Timeout in **Bremse 70 %** (als `SB_DEADLINE_EPOCH`; GPTScan stellt
   dann LLM-Aufrufe ein und läuft freiwillig aus) und **Netz 90 %** (`timeout
   -s TERM`), der Rest bleibt fürs Bergen (AP5);
4. kopiert die Quelle nach `/work/input` — GPTScan liefert stillschweigend leere
   Ausgaben, wenn der Pfad Wörter wie `external`, `openzeppelin`, `uniswap`,
   `test` enthält;
5. ruft `main.py -s /work/input -o /output.json --provider … --format json`;
6. normalisiert die Timeout-Codes 137/143 auf 124, damit ein gewollter Timeout
   in SmartBugs' **errors** landet und nicht in **fails**;
7. garantiert, dass `/output.json` existiert, notfalls als wohlgeformter
   Platzhalter mit `success: false`.

## 2. LLMSmartAudit

### Architektur

LLMSmartAudit ist eine **Multi-Agenten-Pipeline** auf ChatDev/CAMEL. Fünf Rollen
— Chief Executive Officer, Counselor, Security Analyst, Solidity Programming
Expert, Security Testing Engineer — führen ein geführtes Gespräch über den
Quelltext. Es wird **nie kompiliert**; das Werkzeug liest Solidity als Text.

Im hier verwendeten Modus `SmartContractTA` besteht die Kette aus drei
Abschnitten (`CompanyConfig/SmartContractTA/ChatChainConfig.json`):

1. **`ContractAnalysis`** — eine Runde mit Reflexion: Wozu dient der Contract?
2. **`CodeReview`** — eine zusammengesetzte Phase aus **41 Detektor-Prompts**,
   je einer Runde ohne Reflexion. Von `ArithmeticDetector` und
   `ReentrancyDetector` über `PriceManipulationDetector` und
   `FlashLoanDetector` bis `DoSDetector`.
3. **`TestBugsSummary`** — die Zusammenfassung.

Der Detektorkatalog ist die Taxonomie: `smartbugs/tools/llmsmartaudit/findings.yaml`
führt genau diese 41 Einträge mit Severity und, wo vorhanden, SWC/DASP-Klassifikation.

### Ein- und Ausgabe

Eingabe ist **eine Quelldatei** (`--task-file`). Ausgabe ist
`WareHouse/<NAME>_<ORG>_<timestamp>/<NAME>_audit_report.json`, das der Entrypoint
nach `/output.json` kopiert. Es enthält `categories_total`, `categories_checked`,
`checked[]`, `summary` und `findings[]`.

Gemeldet wird je Finding: Detektorname und Begründungstext. **Nicht** gemeldet
werden Funktionsname, Zeilennummern, Severity und Confidence — sie bleiben in
allen Exporten `null`. Die Severity in den Auswertungen (`severity_doc`) ist der
Default aus `findings.yaml` und je Detektorname konstant; sie ist **kein** Urteil
des Modells.

### Kontextgrenze

`camel/model_backend.py` schlägt für Modell-IDs ohne Eintrag in
`num_max_token_map` auf `LLM_CONTEXT_TOKENS` zurück (Default 16 384); alle Läufe
dieser Arbeit setzen 65 536. Reicht das nicht, bricht ein Agent mit
`max_tokens_exceeded_by_camel` ab — der Contract wurde dann **nicht analysiert**.
Der Parser führt diesen Zustand getrennt als `context_exceeded`.

### Aufruf im Container

Derselbe Entrypoint-Vertrag wie bei GPTScan:

```
'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN' '$MAIN'
```

`smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh`:

1. reduziert bei `MAIN=1` über `main_contract.py` — hier **ohne**
   Compile-Prüfung, weil das Image kein `solc` hat und das Werkzeug ohnehin
   nicht kompiliert;
2. rechnet Bremse und Netz mit derselben Arithmetik wie GPTScan aus (ein Test
   hält beide Entrypoints deckungsgleich). Die **Bremse ist hier folgenlos**:
   LLMSmartAudit liest `SB_DEADLINE_EPOCH` nicht. Wirksam ist nur das Netz;
3. setzt `SB_PARTIAL_REPORT`, sobald ein Timeout im Spiel ist. `audit_report.record()`
   schreibt dorthin nach **jeder abgeschlossenen Detektorphase** einen
   Zwischenstand;
4. ruft `run.py --config SmartContractTA --org smartbugs --name sb_<basename>
   --provider … --task-file …`;
5. kopiert nach dem Lauf den Endbericht nach `/output.json` — oder, wenn das Netz
   zuschlug, den geborgenen Zwischenstand;
6. schreibt sonst einen wohlgeformten Bericht mit `categories_checked: 0` und
   `error: "no report produced"` und erzwingt einen Exit-Code ≠ 0, damit der
   Fehlschlag sichtbar bleibt.

## 3. Slither 0.11.3 als Referenzpunkt

Slither ist ein klassischer statischer Analysator: er kompiliert den Contract,
baut eine Zwischendarstellung und lässt darauf rund hundert Detektoren laufen.
Kein LLM, kein Netzzugang (`network: none`), keine Kosten, deterministisch.

Slither kommt als fertiges SmartBugs-Werkzeug und wurde in dieser Arbeit **nicht
verändert** — `smartbugs/tools/slither-0.11.3/` ist unangetastet, das Image
`smartbugs/slither:0.11.3` stammt von Docker Hub. Es ist die Referenz, an der
sich die beiden KI-Werkzeuge messen lassen müssen, nicht selbst ein Prüfling.

Seine Findings tragen Detektorname, Contract, Funktion, Zeilenbereich, `impact`
und `confidence`.

---

## 4. Gegenüberstellung anhand der eigenen Messdaten

### 4.1 `smartbugs-curated`, Lauf `curated_v1_20260705`

143 gelabelte Contracts, alle drei Werkzeuge im selben Lauf.
Quelle: `eval/curated_v1_20260705__<werkzeug>/run_meta.json`.

| | GPTScan | LLMSmartAudit | Slither 0.11.3 |
|---|---:|---:|---:|
| Contracts mit Ergebnis | 143 | 143 | 140 |
| Contracts mit Findings | 6 | 143 | 140 |
| Findings gesamt | 6 | 1 124 | 2 154 |
| davon DASP-zugeordnet | 6 | 656 | 300 |
| Findings je Contract (Mittel) | 0,04 | 7,9 | 15,1 |
| Recall | 0 % | **97 %** | 64 % |
| Precision | 0 % | 30 % | **45 %** |
| F1 | – | 45 % | **52 %** |
| Tasks mit `errors` | 2 | 0 | 3 |
| Tasks mit `fails` | 0 | 0 | 3 |
| Container-Zeit gesamt | 712,9 s | 42 792,5 s | 298,8 s |
| Median je Contract | 3,1 s | 264,1 s | 1,9 s |
| Wanduhr (4 Prozesse) | 3,2 min | 182,1 min | 1,3 min |
| LLM-Aufrufe | 72 | 6 174 | 0 |
| Token (prompt / completion) | 25 580 / 22 302 | 12 554 710 / 3 517 916 | – |
| Kosten gesamt | $0,0098 | $2,44 | $0 |
| **Kosten je Contract** | **$0,0001** | **$0,0171** | **$0** |
| **Zeit je Contract** | **5,0 s** | **299,2 s** | **2,1 s** |

Recall, Precision und F1 je DASP-Kategorie stehen in
[`eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md).

**Drei Dinge fallen auf.**

*LLMSmartAudit findet fast alles und meldet fast alles.* 97 % Recall bei 7,9
Findings je Contract; kein einziger Contract blieb ohne Meldung. Bei dieser
Dichte ist Contract-Level-Recall wohlwollend — wer genug meldet, trifft
häufiger zufällig. Die beiden verfehlten Kategorien (`other`,
`short_addresses`) haben unter den 41 Detektoren kein Gegenstück; das ist eine
Taxonomie-Grenze, kein Detektionsfehler.

*Slither ist dreimal so teuer in der Findingzahl und trotzdem präziser.* 2 154
Findings, aber nur 300 mit DASP-Zuordnung. Die übrigen 1 854 (86,1 %) sind
überwiegend Informational- und Optimization-Hinweise (1 480), dazu 166 Low,
148 Medium und 60 High.

*Der Kostenunterschied ist drei Größenordnungen.* $0,0171 gegen $0,0001 je
Contract, und 299,2 s gegen 2,1 s Rechenzeit je Contract. Slither ist rund
140-mal so schnell wie LLMSmartAudit und kostenlos.

### 4.2 `mwevariety_fixed` — GPTScans Zieldomäne

96 DeFi-Contracts, keine Ground Truth. Quelle:
`eval/per_contract/curated_mwefixed_live__gptscan.csv`,
`eval/gptscan_mwefixed_v2_main/run_meta.json`,
`eval/llmsa_mwefixed_v2/run_meta.json`.

| | GPTScan (`curated_mwefixed_live`) | GPTScan (`gptscan_mwefixed_v2_main`, MAIN) | LLMSmartAudit (`llmsa_mwefixed_v2`) |
|---|---:|---:|---:|
| Contracts | 96 | 96 | 96 |
| **davon überhaupt analysiert** | **96** | **96** | **59** |
| Kontext überschritten | – | – | **37** |
| Contracts mit Findings | 40 | 37 | 59 |
| Findings gesamt | 77 | 74 | 437 |
| verschiedene Regeln/Kategorien | 8 von 10 | – | 34 von 41 |
| Kosten | $0,2769 | $0,3638 | ≈ $8,37 |
| Wanduhr | 36,7 min | 50,9 min | – |
| Container-Zeit gesamt | 8 217,2 s | 11 771,7 s | 90 206,2 s |
| Kosten je **analysiertem** Contract | $0,0029 | $0,0038 | $0,142 |

**Der entscheidende Unterschied steht in der zweiten Zeile.** GPTScan kam auf
allen 96 Contracts zu einem Ergebnis, LLMSmartAudit auf 59 — **37 Contracts
(38,5 %) sprengten die Kontextgrenze und wurden nie analysiert.** Auf curated
war es genau 1 von 143. Der Grund ist der Korpus: Die geflatteten DeFi-Contracts
tragen ihren vollständigen Import-Closure und sind um ein Vielfaches größer. Im
Mittel gingen 20 900 Prompt-Token in jeden der 2 624 Aufrufe.

Absolute Findingzahlen zwischen diesen beiden Spalten zu vergleichen, wäre
deshalb falsch: 437 zu 77 ist auch ein Vergleich von 59 zu 96 Contracts und von
41 breiten Detektoren zu 10 engen DeFi-Regeln.

### 4.3 Fehlerbilder

`errors` heißt: das Werkzeug hat ein Problem bemerkt, abgefangen und
weitergearbeitet. `fails` heißt: es wurde ausgehebelt, ein Ergebnis kam nicht
zustande. Die Herleitung aus `smartbugs/sb/parse_utils.py` steht in
[`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md); die Bilanz über alle Läufe in
[`errors-fails.md`](errors-fails.md).

| Werkzeug | typisches Fehlerbild | Auswirkung |
|---|---|---|
| GPTScan | `Static analysis failed: Invalid args` — die statische Stufe stürzt ab; auf `mwevariety_fixed` bei 35 von 96 Contracts | Findings entstehen, aber ungefiltert: der Präzisionsschutz fehlt |
| GPTScan | `InvalidCompilation` — Contract nicht übersetzbar | Lauf degradiert auf LLM-only, Ergebnis unbestimmt |
| GPTScan | Exit 127 bei `MAIN=1` — Dateiname passt zu keinem Contract | Task als `fails`; Nachlauf ohne MAIN nötig |
| LLMSmartAudit | `max_tokens_exceeded_by_camel` | Contract **nicht analysiert**; darf nie als sauber zählen |
| LLMSmartAudit | `no report produced` | wohlgeformter Leerbericht, Exit ≠ 0 |
| Slither | `AssertionError` im IR-Generator, `NotConstant` | 3 von 143 Tasks (2,1 %); `--continue-on-errors` fängt sie ab |

Bemerkenswert an der curated-Bilanz: **LLMSmartAudit hatte dort weder `errors`
noch `fails`** — ausgerechnet das Werkzeug mit der höchsten Laufzeit lief am
glattesten durch. Sein Problem ist nicht die Robustheit, sondern die
Kontextgrenze, und die schlägt erst bei großen Contracts zu.

### 4.4 Reproduzierbarkeit

Beide KI-Werkzeuge sind nicht deterministisch, auch bei `temperature=0`.
Gemessen wurde das bisher nur für GPTScan:

* 27 Contracts, zwei Läufe: **20 von 27 (74 %)** mit identischem Finding-Satz
  ([`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md), Abschnitt 4).
* 96 Contracts, `gptscan_mwefixed_v2_main` gegen `curated_mwefixed_live`:
  **75,3 %** der Referenz-Findings reproduziert
  (`eval/gptscan_mwefixed_v2_main/comparison_curated_mwefixed_live.md`). Dieser
  Wert vermischt allerdings zwei Ursachen, weil der zweite Lauf zusätzlich
  `MAIN` gesetzt hatte.

Für LLMSmartAudit wurde die Streuung nicht separat quantifiziert. Slither ist
deterministisch.

---

## 5. Einordnung: Wofür ist welches Werkzeug brauchbar?

### Die Zahl, die am meisten täuscht

**GPTScans 0 % Recall auf curated ist kein Werkzeugbefund.** Von 143 Contracts
lösten 16 überhaupt einen LLM-Aufruf aus; die übrigen 127 verwarf der Vorfilter,
weil kein DeFi-Szenario-Schlüsselwort vorkam. Für sie *kann* definitionsgemäß
kein Finding entstehen. Die 6 Findings, die am Ende herauskamen, lagen auf
Contracts, deren Primärlabel ein anderes war — gegen eine
Single-Label-Ground-Truth gemessen zählen sie nicht.

Dasselbe Werkzeug auf seiner Zieldomäne: 77 Findings auf 40 von 96 Contracts,
acht verschiedene Regeln, alle static-bestätigt, für $0,28. Der Unterschied ist
nicht das Werkzeug, sondern die Frage.

### Die zweite Zahl, die täuscht

**LLMSmartAudits Precision von 30 % ist eine Untergrenze, keine Messung.** Drei
Dinge drücken sie systematisch:

1. curated labelt genau *eine* Primärschwachstelle je Contract. Ein zutreffender
   Sekundärbefund zählt als False Positive.
2. 468 der 1 124 Findings tragen keine DASP-Klassifikation und fallen ganz aus
   der Rechnung.
3. Stichproben am Quellcode ergaben 15 plausibel / 4 generisch / 0 falsch bei
   19 geprüften Extra-Kategorie-Treffern
   ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
   Abschnitt 4.2).

Umgekehrt ist der Recall von 97 % eine **Obergrenze**: Bei 7,9 Findings je
Contract und Contract-Level-Zählung ist ein Zufallstreffer billig zu haben.
Beides zusammen heißt: Die wahren Werte liegen näher beieinander, als die
Tabelle nahelegt.

### Wofür welches Werkzeug taugt

**Slither** ist die erste Wahl für alles, was syntaktisch erkennbar ist, und die
einzige Wahl, wenn Determinismus, Nulltarif und Sekundenlaufzeit zählen. Auf
klassischen Schwachstellen ist es das präziseste der drei (F1 52 %). Es hat
keinen Begriff von beabsichtigtem Verhalten und kann Logikfehler deshalb
prinzipiell nicht finden.

**GPTScan** taugt für genau das, wofür es gebaut ist: die zehn
DeFi-Logik-Szenarien. Es ist erstaunlich billig ($0,0029 je analysiertem
DeFi-Contract) und schnell, weil der Vorfilter den Großteil der Arbeit gar nicht
erst entstehen lässt. Es skaliert auf große Contracts, weil es funktionsweise
arbeitet. Der Preis dafür ist eine enge Zuständigkeit — außerhalb der zehn
Regeln meldet es nichts —, und seine Präzision hängt daran, dass der Contract
kompiliert. Ohne Compilat fällt der Schutzmechanismus weg, und das ist der Fall,
in dem man seinen Zahlen am wenigsten trauen darf.

**LLMSmartAudit** ist das breiteste der drei: 41 Detektoren, die auch Dinge
abdecken, für die es keine DASP-Kategorie gibt (fehlende Withdrawal-Funktion,
Zentralisierungsrisiko, Präzisionsverlust). Auf kleinen Contracts findet es
nahezu alles Gelabelte. Der Preis ist hoch und dreifach: auf curated 171-mal so teuer
je Contract wie GPTScan und rund 140-mal so langsam wie Slither, auf dem
DeFi-Korpus immer noch 49-mal so teuer je analysiertem Contract; und auf realen
DeFi-Contracts scheitert es an der Kontextgrenze — bei 38,5 % des
DeFi-Korpus kam gar kein Ergebnis zustande. Dazu kommt, dass es weder
Zeilennummern noch Severity meldet: Jedes Finding muss von Hand am Quelltext
verortet werden.

### Was dieser Vergleich nicht zeigt

1. **Keine Aussage über die Erkennungsleistung auf DeFi-Logik.** Für
   `mwevariety_fixed` gibt es keine Ground Truth; dort lässt sich nur
   beschreiben, nicht messen.
2. **Keine Aussage über einen Werkzeug-Verbund.** Ob GPTScan und Slither
   zusammen mehr finden als LLMSmartAudit allein, wurde nicht untersucht.
3. **Ein Lauf ist keine Verteilung.** Bei 74 % Lauf-zu-Lauf-Übereinstimmung
   sind alle Findingzahlen der KI-Werkzeuge Stichproben aus einer Streuung, die
   nicht quantifiziert ist.
4. **Nur ein Modell.** Alle Messungen liefen mit `deepseek-v4-flash`, dem
   billigen Tier. Ob ein stärkeres Modell die Bilanz verschiebt, ist offen — der
   Wechsel wäre nach `README.md`, Abschnitt „Modell wählen und wechseln", ohne
   Code-Änderung möglich.
5. **Contract-Level, nicht zeilengenau.** Eine zeilengenaue Auswertung ist nicht
   möglich, solange LLMSmartAudit keine Zeilennummern emittiert.
