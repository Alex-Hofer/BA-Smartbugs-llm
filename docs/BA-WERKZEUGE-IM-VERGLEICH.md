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

Zwei Grenzen wirken getrennt voneinander.

1. **Agentengrenze.** `camel/utils.py:get_model_token_limit` liefert für
   `ModelType.DEEPSEEK_CHAT` fest 65 536; `run.py` setzt diesen Typ für jeden
   Provider `deepseek`. `chat_agent.py` zählt die Token der wachsenden
   Konversation vor jedem Aufruf und bricht ab, wenn sie die Grenze erreichen,
   Meldung `max_tokens_exceeded_by_camel`. Das ist der Abbruch der 37
   Contracts im DeFi-Lauf (`30_Vault.sol`: 76 456 Token). In allen
   aufgezeichneten Läufen änderte `LLM_CONTEXT_TOKENS` an dieser Grenze
   nichts; die Variable wirkte in `camel/utils.py` nur für Provider `custom`.
   Seit dem 24.09.2026 liest `camel/utils.py` sie auch für `DEEPSEEK_CHAT`
   (Default weiterhin 65 536), Läufe mit einem danach gebauten Image können die
   Grenze anheben.
2. **Completion-Budget.** `camel/model_backend.py:_context_limit` schlägt für
   Modell-IDs ohne Eintrag in `num_max_token_map` auf `LLM_CONTEXT_TOKENS`
   zurück (Default 16 384); alle Läufe dieser Arbeit setzen 65 536. Ohne den
   Wert fiele das Completion-Budget großer Prompts auf 1 Token.

Der Contract wurde beim Abbruch **nicht analysiert**; der Parser führt diesen
Zustand getrennt als `context_exceeded`. Das Log zeigt keinen API-Fehler,
sondern den werkzeuginternen Abbruch. Die Anbieterdokumentation nennt für
`deepseek-v4-flash` ein Kontextfenster von 1M Token (api-docs.deepseek.com,
abgerufen 24.09.2026); die 65 536 sind also allein die Konstante des
Werkzeugs, die aus der Zeit von `deepseek-chat` stammt. Der Nachlauf vom
24.09.2026 mit `LLM_CONTEXT_TOKENS=1000000` bestätigt das: Alle 37 Contracts
liefen vollständig durch (Abschnitt 4.2, `eval/llmsa_mwefixed_v2_ctx1m/`).

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
Für den DeFi-Korpus kam am 24.09.2026 ein zweites Werkzeugverzeichnis dazu,
`smartbugs/tools/slither-0.11.3-glibc/`: dieselbe Slither-Version, derselbe
Parser, dieselbe `findings.yaml`, aber ein eigenes, glibc-basiertes Image
(`smartbugs/slither:0.11.3-glibc`, Dockerfile im Verzeichnis), weil die
solc-Binaries 0.7.6 und 0.8.1 bis 0.8.12 im Alpine-Image des Upstreams nicht
starten (`BA-BETRIEB.md`, Fallstrick 10). Der curated-Lauf bleibt beim
Upstream-Image; Solidity 0.4 ist nicht betroffen.

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
| davon DASP-zugeordnet | 6 | 656 | 391 |
| Findings je Contract (Mittel) | 0,04 | 7,9 | 15,1 |
| Recall | 0 % | **97 %** | 67 % |
| Precision | 0 % | 30 % | **45 %** |
| F1 | – | 45 % | **54 %** |
| Tasks mit `errors` | 2 | 0 | 3 |
| Tasks mit `fails` | 0 | 0 | 3 |
| Container-Zeit gesamt | 712,9 s | 42 792,5 s | 298,8 s |
| Median je Contract | 3,1 s | 264,1 s | 1,9 s |
| Wanduhr, erster Task-Start bis letztes Task-Ende (4 Prozesse) | 3,2 min | 182,1 min | 1,3 min |
| LLM-Aufrufe | 72 | 6 174 | 0 |
| Token (prompt / completion) | 25 580 / 22 302 | 12 554 710 / 3 517 916 | – |
| Kosten gesamt | $0,0098 | $2,44 | $0 |
| **Kosten je Contract** | **$0,0001** | **$0,0171** | **$0** |
| **Zeit je Contract** | **5,0 s** | **299,2 s** | **2,1 s** |

Die Wanduhr ist aus den Zeitstempeln der `smartbugs.json` gerechnet (erster
Task-Start bis letztes Task-Ende: 3:13 min, 3:02:09 h, 1:16 min). SmartBugs
selbst meldet am Ende jedes Laufs eine etwas längere Zeit, weil Start und
Aufräumen mitzählen: 3:19 min, 3:02:15 h und 1:24 min
(`smartbugs/results/logs/<runid>.log`). Das Durchführungsprotokoll nennt in
Tabelle 4.1 die SmartBugs-Meldung.

Recall, Precision und F1 je DASP-Kategorie stehen in
[`eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md),
seit dem 24.09.2026 mit Basisrate und Wilson-Intervall (95 %) für den Recall.
Sechs der zehn Kategorien haben acht oder weniger Contracts; ihre Intervalle
sind breiter als 40 Prozentpunkte, ein Recall von 100 % bei vier Contracts
heißt nur „zwischen 51 % und 100 %“.

**Drei Dinge fallen auf.**

*LLMSmartAudit findet fast alles und meldet fast alles.* 97 % Recall bei 7,9
Findings je Contract; kein einziger Contract blieb ohne Meldung. Bei dieser
Dichte ist Contract-Level-Recall wohlwollend — wer genug meldet, trifft
häufiger zufällig. Die beiden verfehlten Kategorien (`other`,
`short_addresses`) haben unter den 41 Detektoren kein Gegenstück; das ist eine
Taxonomie-Grenze, kein Detektionsfehler.

*Slither meldet am meisten und ist trotzdem am präzisesten.* 2 154 Findings,
aber nur 391 mit DASP-Zuordnung. Die übrigen 1 763 (81,8 %) sind überwiegend
Informational- und Optimization-Hinweise (1 480), dazu 166 Low, 60 Medium und
57 High. Mit F1 54 % ist Slither auf diesem Korpus das stärkste der drei
Werkzeuge — auf genau den Schwachstellenklassen, für die es gebaut ist.

*Der Kostenunterschied ist mehr als zwei Größenordnungen.* $0,0171 gegen $0,0001 je
Contract, und 299,2 s gegen 2,1 s Rechenzeit je Contract. Slither ist rund
140-mal so schnell wie LLMSmartAudit und kostenlos.

### 4.2 `mwevariety_fixed` — GPTScans Zieldomäne

96 DeFi-Contracts, keine Ground Truth. Quelle:
`eval/per_contract/curated_mwefixed_live__gptscan.csv`,
`eval/gptscan_mwefixed_v2_main/run_meta.json`,
`eval/llmsa_mwefixed_v2/run_meta.json`,
`eval/per_contract/slither_mwefixed_v2__slither-0.11.3-glibc.csv`
(Vorlauf mit dem Upstream-Image: `slither_mwefixed_v1__slither-0.11.3.csv`).

| | GPTScan (`curated_mwefixed_live`) | GPTScan (`gptscan_mwefixed_v2_main`, MAIN) | LLMSmartAudit (`llmsa_mwefixed_v2`) | Slither 0.11.3 (`slither_mwefixed_v2`, glibc-Image) | LLMSmartAudit (`llmsa_mwefixed_v2_ctx1m`, nur die 37 Kontext-Contracts) |
|---|---:|---:|---:|---:|---:|
| Contracts | 96 | 96 | 96 | 96 | 37 |
| **davon überhaupt analysiert** | **96** | **96** | **59** | **95** | **37** |
| Kontext überschritten | – | – | **37** | – | 0 |
| Compiler-Fehler (`Stack too deep`) | – | – | – | **1** | – |
| Contracts mit Findings | 40 | 37 | 59 | 94 | 37 |
| Findings gesamt | 77 | 74 | 437 | 7 096 | 317 |
| verschiedene Regeln/Kategorien | 8 von 10 | – | 34 von 41 | 48 Detektoren | 34 von 41 |
| Kosten | $0,2769 | $0,3638 | ≈ $8,37 | $0 | $5,55 abgebucht (geschätzt $11,42) |
| Wanduhr | 36,7 min | 50,9 min | – | 2,8 min | 5,0 h in zwei Teilen |
| Container-Zeit gesamt | 8 217,2 s | 11 771,7 s | 90 206,2 s | 646,6 s | 35 027,9 s |
| Kosten je **analysiertem** Contract | $0,0029 | $0,0038 | $0,142 | $0 | $0,15 |

**Der entscheidende Unterschied steht in der zweiten Zeile.** GPTScan kam auf
allen 96 Contracts zu einem Ergebnis, LLMSmartAudit auf 59 — **37 Contracts
(38,5 %) sprengten die Kontextgrenze und wurden nie analysiert.** Auf curated
war es genau 1 von 143. Der Grund ist der Korpus: Die geflatteten DeFi-Contracts
tragen ihren vollständigen Import-Closure und sind um ein Vielfaches größer. Im
Mittel gingen 20 900 Prompt-Token in jeden der 2 624 Aufrufe.

**Slither als statische Baseline auf demselben Korpus** (Lauf
`slither_mwefixed_v2` vom 24.09.2026, glibc-Image, `--timeout 600`, 4 Prozesse,
2:48 min Wanduhr) kam auf 95 der 96 Contracts zu einem Ergebnis: 94 mit
Findings, einer ohne. Der eine Rest, `58_UniV3Vault.sol` (`pragma` 0.8.9),
scheitert am Compiler selbst: solc meldet `Stack too deep when compiling
inline assembly`; der Korpusbau hatte diese Datei nur mit `--optimize`
übersetzt bekommen, Slither ruft solc ohne Optimierer auf. Ein erster Lauf am
selben Tag mit dem Upstream-Image (`slither_mwefixed_v1`) hatte nur 51 der 96
Contracts erreicht: SmartBugs reicht den zur `pragma` passenden Compiler als
`$BIN/solc` in den Container, das Upstream-Image ist Alpine Linux, und die
solc-Binaries 0.7.6 und 0.8.1 bis 0.8.12 sind gegen glibc gelinkt und dort
nicht startbar (`BA-BETRIEB.md`, Fallstrick 10). Das eigene glibc-Image
(Abschnitt 3) behebt das; für die 51 in beiden Läufen analysierten Contracts
sind Findingzahl und Detektorverteilung in v1 und v2 identisch, Slither ist
deterministisch. Die 7 096 Findings verteilen sich nach Slithers Impact-Stufe
auf 4 858 Informational, 112 Optimization, 1 254 Low, 748 Medium und
124 High; die häufigsten Detektoren sind `too-many-digits` (2 020) und
`naming-convention` (1 886), also Stilhinweise. Im Median meldet Slither 55
Findings je analysiertem Contract (Spanne 0 bis 349), GPTScan auf denselben
96 Contracts 0 bis 2. Ohne Ground Truth bleibt das ein Mengen-, kein
Qualitätsvergleich.

**Die 37 Kontext-Contracts mit angehobener Grenze** (Nachlauf
`llmsa_mwefixed_v2_ctx1m`, 24.09.2026, `LLM_CONTEXT_TOKENS=1000000`, Image
vom selben Tag, zwei Prozesse): Alle 37 liefen durch alle 41 Detektoren, kein
Abbruch, 317 Findings (2 bis 19 je Contract, Median 9), 1 625 LLM-Aufrufe mit
im Mittel 61 700 Prompt-Token je Aufruf, Median 954 s je Contract. Der
38,5-Prozent-Befund des Hauptlaufs ist damit eine Eigenschaft der Konstante
65 536 im Werkzeug, nicht des Modells. Die Zahlen des Hauptlaufs bleiben
unverändert stehen; der Nachlauf lief auf einem anderen Modellstand
(DeepSeek-V4.1-Flash hinter demselben Namen) und wird nicht eingemischt.
Auswertung in [`eval/llmsa_mwefixed_v2_ctx1m/`](../eval/llmsa_mwefixed_v2_ctx1m/README.md).

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

**Für LLMSmartAudit lässt sie sich seit dem 20.09.2026 beziffern.** Es gibt zwei
vollständige Läufe über dieselben 143 curated-Contracts: `curated_v1_20260705`
(05.07.2026) und `llmsa_curated_v2` (15.08.2026), beide mit
`deepseek/deepseek-v4-flash`. Verglichen über die 141 Contracts, für die beide
mindestens ein Finding melden:

| | |
|---|---:|
| Findings gesamt | 1 124 gegen 1 028 |
| Paare (Contract, Detektor) in beiden Läufen | 805 |
| nur im ersten Lauf | 291 |
| nur im zweiten Lauf | 216 |
| Übereinstimmung (Jaccard), über die 141 Contracts mit Findings in beiden Läufen | **61,4 %** |
| Übereinstimmung (Jaccard), über alle 142 Contracts mit Findings in mindestens einem Lauf | **60,5 %** |
| Contracts mit **identischem** Detektor-Satz | **7 von 141 = 5,0 %** |

> **Welche der beiden Zahlen gilt.** Die 61,4 % lassen einen Contract außen vor
> — `0x663e4229…`, mit 18 Detektoren in Lauf 1 und **keinem** Finding in Lauf 2,
> weil der Lauf dort am Kontextfenster scheiterte. Das ist kein Zufallsrauschen,
> sondern ein systematischer Ausfall, und ihn auszuschließen schmeichelt der
> Übereinstimmung. Über alle 142 Contracts gerechnet sinkt der Jaccard auf
> 60,5 % (805 von 1 330 Paaren). Der Unterschied ist klein, die Richtung aber
> eindeutig: 61,4 % ist die **Obergrenze**. Umgekehrt ist der Ausschluss nicht
> willkürlich — ein Contract ohne jedes Finding trägt zur Frage, wie stabil die
> *Detektor-Auswahl* ist, nichts bei. Beide Zahlen stehen hier, damit die
> Entscheidung nachvollziehbar bleibt.

Das ist deutlich instabiler als GPTScan. Dort stimmten 74 % der Contracts im
Finding-Satz überein, hier 5 %. Der Grund liegt in der Finding-Dichte: Bei
durchschnittlich acht Detektoren je Contract muss nur einer von acht kippen,
damit der Satz nicht mehr identisch ist — die Jaccard-Zahl von 61,4 % ist das
fairere Maß.

**Vier Vorbehalte, ohne die die Zahl nicht zu gebrauchen ist.**

1. Die beiden Läufe unterscheiden sich nicht nur zufällig: Timeout 5 400 s gegen
   3 600 s, vier gegen drei Prozesse. Beides betrifft den Inhalt nicht — in
   keinem der Läufe trat ein Timeout auf —, aber sauber isoliert ist der
   Nicht-Determinismus damit nicht.
2. Der Parser wurde dazwischen repariert (02.08.2026). Das erklärt den
   Unterschied **nicht**: `docs/parser-fix-vorher-nachher.md` weist nach, dass
   die Spalte `findings` für jeden einzelnen Task unverändert blieb.
3. Zwischen den Läufen liegen sechs Wochen. Dass der Anbieter das Modell hinter
   demselben Namen verändert hat, lässt sich nicht ausschließen — und der
   Rückgang ist auffällig einseitig: In fast jeder Detektorkategorie meldet der
   spätere Lauf weniger (Integer Overflow 73 → 54 Contracts, Lack of Input
   Validation 105 → 87, Reentrancy 70 → 56). Zufallsstreuung wäre symmetrisch.
   Die Zahl ist deshalb eine **Obergrenze für die Stabilität**, nicht eine
   Messung reiner Sampling-Varianz.
4. Die Rohergebnisse von `llmsa_curated_v2` existieren nicht mehr (Stand
   24.09.2026; der Co-Autor hat sie nicht mehr). Seine Seite des Vergleichs ist
   allein über die abgeleitete `findings.jsonl` belegt. Deren Treue zum
   Rohmaterial wurde am 21.09.2026, als die Rohdaten noch vorlagen, auf dem
   Rechner des Co-Autors gegengeprüft: 143 Task-Ordner, Summe der Findings
   1 028 — identisch mit der `findings.jsonl`. Ein erneuter Reparse oder eine
   Wiederholung von `build_eval.py` ist für diesen Lauf nicht mehr möglich.

Slither ist deterministisch.

---

## 5. Einordnung: Wofür ist welches Werkzeug brauchbar?

### Die Zahl, die am meisten täuscht

**GPTScans 0 % Recall auf curated ist kein Werkzeugbefund.** Von 143 Contracts
lösten 16 überhaupt einen LLM-Aufruf aus; die übrigen 127 verwarf der Vorfilter,
weil kein DeFi-Szenario-Schlüsselwort vorkam. Für sie *kann* definitionsgemäß
kein Finding entstehen. Die 6 Findings, die am Ende herauskamen, lagen auf
Contracts, deren Primärlabel ein anderes war — gegen eine
Single-Label-Ground-Truth gemessen zählen sie nicht.

Ein Vorbehalt kommt hinzu: In 87 der 143 Tasks lehnte GPTScans Grammatik Teile
der Solidity-0.4-Quelltexte ab und zählte im Median nur ein Viertel der
deklarierten Funktionen; der Vorfilter sah dort weniger, als im Contract steht
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Nachtrag
4.7). An den 0 % ändert das nichts, an der Begründung „kein Schlüsselwort“ für
alle 127 Contracts schon.

Dasselbe Werkzeug auf seiner Zieldomäne: 77 Findings auf 40 von 96 Contracts,
acht verschiedene Regeln, alle static-bestätigt, für $0,28. Der Unterschied ist
nicht das Werkzeug, sondern die Frage.

### Die zweite Zahl, die täuscht

**LLMSmartAudits Precision von 30 % ist eine Untergrenze, keine Messung.** Drei
Dinge drücken sie systematisch:

1. curated labelt genau *eine* Primärschwachstelle je Contract. Ein zutreffender
   Sekundärbefund zählt als False Positive.
2. 468 der 1 124 Findings tragen keine DASP-Klassifikation und fallen ganz aus
   der Rechnung. Welche der 41 Detektoren eine DASP-Nummer tragen, nach
   welcher Regel und mit welchem Beleg im Prompt, steht seit dem 24.09.2026 in
   [`smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md);
   dort auch die zwei Zuordnungen auf der Kippe (`Centralization Risk` mit
   DASP-2, `Incorrect Constructor Name` ohne) und was ihre Änderung an den
   30 % bewegen würde (30,9 % beziehungsweise 29,5 %).
3. Stichproben am Quellcode ergaben 15 plausibel / 4 generisch / 0 falsch bei
   19 geprüften Extra-Kategorie-Treffern
   ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
   Abschnitt 4.2).

Gleichzeitig ist die Precision je Kategorie gegen ihre Basisrate zu lesen, also
gegen die Precision eines Werkzeugs, das die Kategorie auf jedem Contract
meldet. Bei `unchecked_low_level_calls` stehen 79 % Precision einer Basisrate
von 36 % gegenüber (52 von 143 Contracts tragen das Label), bei
`access_control` 19 % einer Basisrate von 13 %: Dort liegt LLMSmartAudit nur
knapp über dem Raten. Beide Spalten stehen je Kategorie in
[`eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md).

Umgekehrt ist der Recall von 97 % eine **Obergrenze**: Bei 7,9 Findings je
Contract und Contract-Level-Zählung ist ein Zufallstreffer billig zu haben.
Beides zusammen heißt: Die wahren Werte liegen näher beieinander, als die
Tabelle nahelegt.

### Wofür welches Werkzeug taugt

**Slither** ist die erste Wahl für alles, was syntaktisch erkennbar ist, und die
einzige Wahl, wenn Determinismus, Nulltarif und Sekundenlaufzeit zählen. Auf
klassischen Schwachstellen ist es das präziseste der drei (F1 54 %). Es hat
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
nahezu alles Gelabelte. Der Preis ist hoch und dreifach: auf curated rund
250-mal so teuer wie GPTScan ($2,44 gegen $0,0098 für dieselben 143
Contracts) und rund 140-mal so langsam wie Slither, auf dem
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
3. **Ein Lauf ist keine Verteilung.** Alle Findingzahlen der KI-Werkzeuge sind
   Stichproben aus einer Streuung. Diese ist für beide Werkzeuge beziffert —
   GPTScan 74 % Lauf-zu-Lauf-Übereinstimmung, LLMSmartAudit 61,4 % (Jaccard)
   bzw. 5 % identische Detektor-Sätze, siehe Abschnitt 4.4 —, beruht aber je
   Werkzeug auf nur **zwei** Läufen. Zwei Läufe ergeben eine Spannweite, keine
   Verteilung: Streuungsmaße wie Standardabweichung oder Konfidenzintervalle
   sind daraus nicht ableitbar. Slither ist als deterministisches Werkzeug
   nicht betroffen.
4. **Nur ein Modell.** Alle Messungen liefen mit `deepseek-v4-flash`, dem
   billigen Tier. Ob ein stärkeres Modell die Bilanz verschiebt, ist offen — der
   Wechsel wäre nach `README.md`, Abschnitt „Modell wählen und wechseln", ohne
   Code-Änderung möglich.
5. **Contract-Level, nicht zeilengenau.** Eine zeilengenaue Auswertung ist nicht
   möglich, solange LLMSmartAudit keine Zeilennummern emittiert.
6. **143 Dateien sind nicht 143 Contracts.** `smartbugs-curated` führt
   `0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` zweimal — einmal unter
   `reentrancy`, einmal unter `unchecked_low_level_calls`, je mit einem eigenen
   Label. Derselbe Contract wird also zweimal analysiert und zweimal gewertet.
   Das relativiert die Rede vom „Single-Label-Datensatz": Sie gilt je *Datei*,
   nicht je Contract. Auf die Kennzahlen wirkt es sich kaum aus (ein Contract von
   143), aber `contract_id` ist damit kein eindeutiger Schlüssel — eindeutig ist
   erst `(label_dir, contract_id)`.
