# Die drei Werkzeuge im Vergleich

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Was GPTScan, LLMSmartAudit und Slither tun, wie wir sie unter SmartBugs
aufrufen und was unsere Messungen über sie sagen. Alle Zahlen haben wir gegen
die Rohergebnisse unter `smartbugs/results/` geprüft; die Quelle steht jeweils
dabei.

**Vorweg:** Die beiden Korpora messen Unterschiedliches. `smartbugs-curated`
labelt klassische SWC/DASP-Schwachstellen, `mwevariety_fixed` besteht aus
DeFi-Contracts ohne Referenzstand — und nur der zweite ist GPTScans
Zieldomäne. Wer GPTScans 0 % Recall auf curated neben LLMSmartAudits 97 %
stellt, vergleicht nicht zwei Werkzeuge, sondern ein Werkzeug mit einer Frage,
für die es nicht gebaut ist (Abschnitt 5).

---

## 1. GPTScan

### Architektur

GPTScan koppelt ein LLM mit leichter Programmanalyse. Es sucht nicht nach
Code-Mustern, sondern nach **10 DeFi-Logik-Szenarien**, den Regeln `MWE-200`
bis `MWE-209` (etwa „Insecure LP Token Value Calculation“, „No Slippage Limit
Check“, „Approval Not Revoked“). Jede Regel besteht aus einem *Szenario* (wonach
in der Funktion gesucht wird) und einer *Eigenschaft* (welche Bedingung sie
verdächtig macht).

Die Pipeline hat vier Stufen; ihre Zwischenstände schreibt der Entrypoint als
Zeile `GPTSCAN_META` ins `result.log`:

| Stufe | Feld in `GPTSCAN_META` | Was passiert |
|---|---|---|
| Vorfilter | `*_after_filter` | Schlüsselbegriffe je Szenario; ohne Treffer kein LLM-Aufruf |
| Szenario-Abgleich | `*_after_step_1` | LLM entscheidet, ob das Szenario zutrifft |
| Eigenschafts-Prüfung | `*_after_step_2` | LLM prüft die verdächtige Bedingung |
| Statische Bestätigung | `*_after_static`, `vul_before_static`, `vul_after_static` | Daten-/Kontrollfluss am **kompilierten** Contract; verwirft, was sich nicht erhärten lässt |

Die vierte Stufe schützt die Präzision und **braucht ein Compilat**. Fehlt es,
läuft GPTScan im LLM-only-Modus weiter; der Parser markiert das als
`analysis degraded`, und „keine Findings“ heißt dann „unbestimmt“, nicht
„sauber“. Genau das war der Anlass für die Korpus-Reparatur
([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md)).

### Ein- und Ausgabe

Eingabe ist ein **Verzeichnis** mit genau einer `.sol`-Datei; GPTScan hat keine
Contract-Auswahl und berichtet über alles, was dort kompiliert. Ausgabe ist
`/output.json` (`version`, `success`, `message`, `results`) plus
`/output.json.metadata.json` mit Token, Kosten und Stufenzahlen. Je Finding:
Regel, Funktionsname, Zeilenbereich, Severity (immer `high`), Begründung,
Empfehlung — keine Confidence.

### Aufruf im Container

```
'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN' '$MAIN'
```

`smartbugs/tools/gptscan/scripts/do_solidity.sh`:

1. legt den von SmartBugs gelieferten `solc` über `$BIN` in den `PATH`;
2. reduziert bei `MAIN=1` die Quelle per `main_contract.py --verify-compile`
   auf den namensgleichen Contract und stellt die Vollquelle wieder her, wenn
   die Reduktion nicht mehr kompiliert (Exit 127: kein Contract dieses Namens);
3. teilt den Timeout in **Bremse bei 70 %** (`SB_DEADLINE_EPOCH`, GPTScan stellt
   LLM-Aufrufe ein) und **Netz bei 90 %** (`timeout -s TERM`); der Rest bleibt
   fürs Bergen (AP5);
4. kopiert die Quelle nach `/work/input` — GPTScan liefert still leere
   Ausgaben, wenn der Pfad Wörter wie `external`, `openzeppelin`, `uniswap`
   oder `test` enthält;
5. ruft `main.py -s /work/input -o /output.json --provider … --format json`;
6. normalisiert die Exit-Codes 137/143 auf 124, damit ein gewollter Timeout in
   **errors** landet und nicht in **fails**;
7. sorgt dafür, dass `/output.json` existiert, notfalls als Platzhalter mit
   `success: false`.

## 2. LLMSmartAudit

### Architektur

LLMSmartAudit ist eine **Multi-Agenten-Pipeline** auf ChatDev/CAMEL. Fünf Rollen
(CEO, Counselor, Security Analyst, Solidity Programming Expert, Security
Testing Engineer) führen ein Gespräch über den Quelltext. **Kompiliert wird
nie**; das Werkzeug liest Solidity als Text.

Im Modus `SmartContractTA` hat die Kette drei Abschnitte
(`CompanyConfig/SmartContractTA/ChatChainConfig.json`):

1. **`ContractAnalysis`** — eine Runde mit Reflexion: Wozu dient der Contract?
2. **`CodeReview`** — **41 Detektor-Prompts**, je eine Runde, von
   `ArithmeticDetector` und `ReentrancyDetector` über
   `PriceManipulationDetector` bis `DoSDetector`.
3. **`TestBugsSummary`** — Zusammenfassung.

Der Detektorkatalog ist die Taxonomie:
`smartbugs/tools/llmsmartaudit/findings.yaml` führt genau diese 41 Einträge mit
Severity und, wo vorhanden, SWC/DASP-Klasse.

### Ein- und Ausgabe

Eingabe ist **eine Quelldatei** (`--task-file`). Ausgabe ist
`WareHouse/<NAME>_<ORG>_<timestamp>/<NAME>_audit_report.json`, das der
Entrypoint nach `/output.json` kopiert (`categories_total`,
`categories_checked`, `checked[]`, `summary`, `findings[]`). Je Finding gibt es
nur Detektorname und Begründung — **keine** Funktion, Zeilennummer, Severity
oder Confidence. Die Severity in unseren Auswertungen (`severity_doc`) ist der
Katalogwert aus `findings.yaml`, kein Urteil des Modells.

### Kontextgrenze

Zwei Grenzen wirken unabhängig voneinander:

1. **Agentengrenze.** `camel/utils.py:get_model_token_limit` liefert für
   `ModelType.DEEPSEEK_CHAT` fest 65 536; `run.py` setzt diesen Typ für jeden
   Provider `deepseek`. `chat_agent.py` zählt vor jedem Aufruf die Token der
   wachsenden Konversation und bricht an der Grenze mit
   `max_tokens_exceeded_by_camel` ab — das ist der Abbruch der 37 Contracts im
   DeFi-Lauf (`30_Vault.sol`: 76 456 Token). In allen aufgezeichneten
   Hauptläufen änderte `LLM_CONTEXT_TOKENS` daran nichts, weil die Variable nur
   für Provider `custom` galt. Seit dem 24.09.2026 gilt sie auch für
   `DEEPSEEK_CHAT` (Default weiterhin 65 536).
2. **Completion-Budget.** `camel/model_backend.py:_context_limit` fällt für
   unbekannte Modell-IDs auf `LLM_CONTEXT_TOKENS` zurück (Default 16 384); alle
   unsere Läufe setzen 65 536. Ohne diesen Wert fiele das Budget großer Prompts
   auf 1 Token.

Ein abgebrochener Contract ist **nicht analysiert**; der Parser führt ihn als
`context_exceeded`. Im Log steht kein API-Fehler, sondern der werkzeuginterne
Abbruch. DeepSeek nennt für `deepseek-v4-flash` ein Kontextfenster von 1 Mio.
Token (api-docs.deepseek.com, abgerufen 24.09.2026); die 65 536 stammen also
aus der Zeit von `deepseek-chat`. Der Nachlauf mit
`LLM_CONTEXT_TOKENS=1000000` bestätigt das: Alle 37 Contracts liefen durch
(4.2).

### Aufruf im Container

Gleicher Entrypoint-Vertrag wie bei GPTScan;
`smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh`:

1. reduziert bei `MAIN=1` per `main_contract.py` — **ohne** Compile-Prüfung,
   weil das Image kein `solc` hat;
2. rechnet Bremse und Netz wie GPTScan (ein Test hält beide Entrypoints
   deckungsgleich). Die **Bremse ist hier folgenlos**, weil LLMSmartAudit
   `SB_DEADLINE_EPOCH` nicht liest; wirksam ist nur das Netz;
3. setzt bei aktivem Timeout `SB_PARTIAL_REPORT`; `audit_report.record()`
   schreibt dorthin nach **jeder Detektorphase** einen Zwischenstand;
4. ruft `run.py --config SmartContractTA --org smartbugs --name sb_<basename>
   --provider … --task-file …`;
5. kopiert danach den Endbericht nach `/output.json` — oder den geborgenen
   Zwischenstand, wenn das Netz zugeschlagen hat;
6. schreibt sonst einen Bericht mit `categories_checked: 0` und
   `error: "no report produced"` und erzwingt Exit ≠ 0.

## 3. Slither 0.11.3 als Referenz

Slither ist ein klassischer statischer Analysator: kompilieren,
Zwischendarstellung bauen, rund hundert Detektoren darauf laufen lassen. Kein
LLM, kein Netz (`network: none`), keine Kosten, bis auf einen Detektor
deterministisch (4.4). Seine Findings tragen Detektor, Contract, Funktion,
Zeilenbereich, `impact` und `confidence`.

Wir nutzen das fertige SmartBugs-Werkzeug **unverändert**
(`smartbugs/tools/slither-0.11.3/`, Image `smartbugs/slither:0.11.3`). Es ist
die Referenz, nicht der Prüfling. Für den DeFi-Korpus kam am 24.09.2026
`smartbugs/tools/slither-0.11.3-glibc/` dazu: gleiche Version, gleicher Parser,
gleiche `findings.yaml`, aber ein glibc-basiertes Image, weil die
solc-Binaries 0.7.6 und 0.8.1 bis 0.8.12 im Alpine-Image nicht starten
([`BA-BETRIEB.md`](BA-BETRIEB.md), Fallstrick 10). Der curated-Lauf bleibt beim
Upstream-Image; Solidity 0.4 ist nicht betroffen.

---

## 4. Gegenüberstellung anhand unserer Messdaten

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
| Tasks mit `errors` / `fails` | 2 / 0 | 0 / 0 | 3 / 3 |
| Container-Zeit gesamt | 712,9 s | 42 792,5 s | 298,8 s |
| Median je Contract | 3,1 s | 264,1 s | 1,9 s |
| Wanduhr (4 Prozesse) | 3,2 min | 182,1 min | 1,3 min |
| LLM-Aufrufe | 72 | 6 174 | 0 |
| Token (prompt / completion) | 25 580 / 22 302 | 12 554 710 / 3 517 916 | – |
| Kosten gesamt | $0,0098 | $2,44 | $0 |
| **Kosten je Contract** | **$0,0001** | **$0,0171** | **$0** |
| **Zeit je Contract** | **5,0 s** | **299,2 s** | **2,1 s** |

Die Wanduhr rechnen wir aus den Zeitstempeln der `smartbugs.json` (erster
Task-Start bis letztes Task-Ende). SmartBugs selbst meldet etwas mehr, weil
Start und Aufräumen mitzählen (3:19 min, 3:02:15 h, 1:24 min); diese Werte
nennt das Durchführungsprotokoll.

Recall, Precision und F1 je Kategorie, mit Basisrate und 95-%-Wilson-Intervall:
[`eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md).
Sechs der zehn Kategorien haben höchstens acht Contracts; ihre Intervalle sind
32 bis 79 Prozentpunkte breit — 100 % Recall bei vier Contracts heißt nur
„zwischen 51 % und 100 %“.

**Was auffällt:**

- *LLMSmartAudit findet fast alles und meldet fast alles.* 97 % Recall bei 7,9
  Findings je Contract, kein Contract ohne Meldung. Bei dieser Dichte ist
  Contract-Level-Recall wohlwollend. Die zwei verfehlten Kategorien (`other`,
  `short_addresses`) haben keinen passenden Detektor — eine Grenze der
  Taxonomie, kein Erkennungsfehler.
- *Slither meldet am meisten und ist trotzdem am präzisesten.* Von 2 154
  Findings sind nur 391 DASP-zugeordnet; die übrigen 1 763 sind überwiegend
  Informational- und Optimization-Hinweise (1 480), dazu 166 Low, 60 Medium, 57
  High. Mit F1 54 % ist Slither hier das stärkste Werkzeug — auf genau den
  Klassen, für die es gebaut ist.
- *Der Kostenunterschied umfasst mehr als zwei Größenordnungen:* $0,0171 gegen
  $0,0001 je Contract. Slither ist rund 140-mal so schnell wie LLMSmartAudit
  und kostenlos.

### 4.2 `mwevariety_fixed` — GPTScans Zieldomäne

96 DeFi-Contracts, keine Ground Truth. Quellen:
`eval/per_contract/curated_mwefixed_live__gptscan.csv`,
`eval/gptscan_mwefixed_v2_main/run_meta.json`,
`eval/llmsa_mwefixed_v2/run_meta.json`,
`eval/per_contract/slither_mwefixed_v2__slither-0.11.3-glibc.csv`.

| | GPTScan | GPTScan + `MAIN` | LLMSmartAudit | Slither (glibc) | LLMSmartAudit, 37 Kontext-Contracts, Grenze 1 Mio. |
|---|---:|---:|---:|---:|---:|
| Lauf | `curated_mwefixed_live` | `gptscan_mwefixed_v2_main` | `llmsa_mwefixed_v2` | `slither_mwefixed_v2` | `llmsa_mwefixed_v2_ctx1m` |
| Contracts | 96 | 96 | 96 | 96 | 37 |
| **davon analysiert** | **96** | **96** | **59** | **95** | **37** |
| Kontext überschritten | – | – | **37** | – | 0 |
| Compilerfehler (`Stack too deep`) | – | – | – | **1** | – |
| Contracts mit Findings | 40 | 37 | 59 | 94 | 37 |
| Findings gesamt | 77 | 74 | 437 | 7 096 | 317 |
| verschiedene Regeln/Kategorien | 8 von 10 | – | 34 von 41 | 48 Detektoren | 34 von 41 |
| Kosten | $0,2769 | $0,3638 | ≈ $8,37 | $0 | $5,55 abgebucht ($11,42 geschätzt) |
| Wanduhr | 36,7 min | 50,9 min | – | 2,8 min | 5,0 h in zwei Teilen |
| Container-Zeit gesamt | 8 217,2 s | 11 771,7 s | 90 206,2 s | 646,6 s | 35 027,9 s |
| Kosten je **analysiertem** Contract | $0,0029 | $0,0038 | $0,142 | $0 | $0,15 |

**Entscheidend ist die Zeile „davon analysiert“.** GPTScan kam auf allen 96
Contracts zu einem Ergebnis, LLMSmartAudit auf 59 — **37 Contracts (38,5 %)
sprengten die Kontextgrenze**; auf curated war es 1 von 143. Der Grund: Die
geflatteten DeFi-Contracts tragen ihre kompletten Importe und sind ein
Vielfaches größer. Im Mittel gingen 20 900 Prompt-Token in jeden der 2 624
Aufrufe.

**Slither als statische Baseline** (`slither_mwefixed_v2`, 24.09.2026,
glibc-Image, 4 Prozesse, 2:48 min) analysierte 95 von 96 Contracts. Der Rest,
`58_UniV3Vault.sol`, scheitert am Compiler (`Stack too deep when compiling
inline assembly`): Der Korpusbau hatte ihn nur mit `--optimize` übersetzt,
Slither ruft solc ohne Optimierer auf. Der Vorlauf mit dem Upstream-Image
(`slither_mwefixed_v1`) erreichte nur 51 Contracts, weil die passenden
solc-Binaries im Alpine-Image nicht starten; für diese 51 sind beide Läufe bis
auf `encode-packed-collision` (4.4) identisch. Die 7 096 Findings verteilen sich
auf 4 858 Informational, 112 Optimization, 1 254 Low, 748 Medium und 124 High;
am häufigsten sind `too-many-digits` (2 020) und `naming-convention` (1 886).
Im Median meldet Slither 55 Findings je Contract (0 bis 349), GPTScan 0 (0 bis
6, mit `MAIN` 0 bis 7). Ohne Ground Truth ist das ein Mengen-, kein
Qualitätsvergleich.

**Die 37 Kontext-Contracts mit angehobener Grenze** (`llmsa_mwefixed_v2_ctx1m`,
24.09.2026, zwei Prozesse): alle 37 durch alle 41 Detektoren, 317 Findings (2
bis 19 je Contract, Median 9), 1 625 Aufrufe mit im Mittel 61 700 Prompt-Token,
Median 954 s je Contract. Der 38,5-%-Ausfall ist damit eine Eigenschaft der
Konstante im Werkzeug, nicht des Modells. Wir mischen den Nachlauf nicht in den
Hauptlauf, weil er auf einem anderen Modellstand lief (DeepSeek-V4.1-Flash
hinter demselben Namen); Auswertung in
[`eval/llmsa_mwefixed_v2_ctx1m/`](../eval/llmsa_mwefixed_v2_ctx1m/README.md).

Absolute Findingzahlen zwischen den Spalten zu vergleichen wäre falsch: 437 zu
77 heißt auch 59 zu 96 Contracts und 41 breite Detektoren zu 10 engen Regeln.

### 4.3 Fehlerbilder

`errors` heißt: Das Werkzeug hat ein Problem bemerkt und weitergearbeitet.
`fails` heißt: Ein Ergebnis kam nicht zustande. Herleitung in
[`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md), Bilanz über alle Läufe in
[`errors-fails.md`](errors-fails.md).

| Werkzeug | Fehlerbild | Auswirkung |
|---|---|---|
| GPTScan | `Static analysis failed: Invalid args` — in `curated_mwefixed_live` bei 35 von 96 Contracts, 80 Kandidaten (77 zu `MWE-200`); meist besteht die LLM-Antwort auf den Static-Prompt eine Validierungsregel nicht (`tasks.py`, `validate_description`), dreimal ist sie kein JSON | Kandidat gilt als nicht bestätigt und entfällt. Kostet Recall, nicht Precision; wie viele echte Findings darunter waren, haben wir nicht untersucht |
| GPTScan | `InvalidCompilation` | degradiert auf LLM-only, Ergebnis unbestimmt |
| GPTScan | Exit 127 bei `MAIN=1` (kein Contract dieses Namens) | `fails`; Nachlauf ohne `MAIN` nötig |
| LLMSmartAudit | `max_tokens_exceeded_by_camel` | Contract **nicht analysiert**, darf nie als sauber zählen |
| LLMSmartAudit | `no report produced` | wohlgeformter Leerbericht, Exit ≠ 0 |
| Slither | `AssertionError` im IR-Generator, `NotConstant` | 3 von 143 Tasks; `--continue-on-errors` fängt sie ab |

Bemerkenswert: **LLMSmartAudit hatte auf curated weder `errors` noch `fails`.**
Sein Problem ist nicht die Robustheit, sondern die Kontextgrenze bei großen
Contracts.

### 4.4 Reproduzierbarkeit

Beide LLM-Werkzeuge sind nicht deterministisch, auch bei `temperature=0`.

**GPTScan:**

- 27 Contracts, zwei Läufe: **20 von 27 (74 %)** mit identischem Finding-Satz
  ([`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md), 4).
- 96 Contracts, `gptscan_mwefixed_v2_main` gegen `curated_mwefixed_live`:
  **75,3 %** der Referenz-Findings reproduziert
  (`eval/gptscan_mwefixed_v2_main/comparison_curated_mwefixed_live.md`) —
  vermischt mit dem Effekt von `MAIN`.

**LLMSmartAudit**, zwei vollständige Läufe über dieselben 143 Contracts
(`curated_v1_20260705` vom 05.07. und `llmsa_curated_v2` vom 15.08.2026, beide
`deepseek-v4-flash`):

| | |
|---|---:|
| Findings gesamt | 1 124 gegen 1 028 |
| Paare (Contract, Detektor) in beiden Läufen | 805 |
| nur im ersten / nur im zweiten Lauf | 291 / 216 |
| Jaccard über die 141 Contracts mit Findings in beiden Läufen | **61,4 %** |
| Jaccard über alle 142 Contracts mit Findings in mindestens einem Lauf | **60,5 %** |
| Contracts mit **identischem** Detektor-Satz | **7 von 141 (5,0 %)** |

Die 61,4 % lassen `0x663e4229…` außen vor: 18 Detektoren im ersten Lauf,
keiner im zweiten, weil dieser am Kontextfenster scheiterte. Das ist ein
systematischer Ausfall, kein Rauschen; ihn auszuschließen schmeichelt der
Übereinstimmung, daher ist 61,4 % die **Obergrenze**. Für die Frage, wie stabil
die *Detektor-Auswahl* ist, trägt ein Contract ohne Finding aber nichts bei —
deshalb nennen wir beide Zahlen. Schlüssel ist `contract_id`; mit dem
eindeutigen Schlüssel (`label_dir`, `contract_id`) ergeben sich 61,2 % und
60,4 % — an der Aussage ändert das nichts.

Gegenüber GPTScan (74 % identisch) wirkt LLMSmartAudit mit 5 % sehr instabil.
Das liegt an der Dichte: Bei rund acht Detektoren je Contract genügt ein
kippender, damit der Satz nicht mehr identisch ist. Jaccard ist das fairere
Maß. Auf die Kennzahlen schlägt das Rauschen kaum durch: Der zweite Lauf kommt
auf 96 % / 32 % / 47 % statt 97 % / 30 % / 45 %
([`eval/llmsa_curated_v2/README.md`](../eval/llmsa_curated_v2/README.md)).

**Vorbehalte:**

1. Die Läufe unterscheiden sich auch in Timeout (5 400 s gegen 3 600 s) und
   Prozesszahl (vier gegen drei). In keinem trat ein Timeout auf, sauber
   isoliert ist der Nichtdeterminismus damit aber nicht.
2. Die Parser-Reparatur dazwischen (02.08.2026) erklärt den Unterschied nicht:
   Die Spalte `findings` blieb für jeden Task gleich
   ([`parser-fix-vorher-nachher.md`](parser-fix-vorher-nachher.md)).
3. Zwischen den Läufen liegen sechs Wochen, und der Rückgang ist einseitig: In
   fast jeder Kategorie meldet der spätere Lauf weniger (Integer Overflow
   73 → 54 Contracts, Lack of Input Validation 105 → 87, Reentrancy 70 → 56).
   Zufall wäre symmetrisch; ein Modellwechsel hinter demselben Namen liegt
   nahe. Die Zahl ist eine **Obergrenze für die Stabilität**.
4. Die Rohdaten von `llmsa_curated_v2` gibt es nicht mehr (Stand 24.09.2026).
   Am 21.09.2026 haben wir die abgeleitete `findings.jsonl` noch gegen sie
   geprüft (143 Task-Ordner, 1 028 Findings, identisch); ein erneuter Reparse
   ist nicht mehr möglich.

**Slither ist bis auf einen Detektor deterministisch.** Am 28.09.2026 haben wir
beide Messläufe je unter Windows und Linux wiederholt und Contract für Contract
mit den versionierten `result.json` verglichen: curated 143 bzw. 142 von 143
identisch, DeFi 96 von 96. Die einzigen Abweichungen kommen von
`encode-packed-collision`, der bei einzelnen Contracts mal ein Finding mehr,
mal weniger meldet (`62_Locke.sol` in fünf Wiederholungen 67, 68, 68, 67, 67).
Der Detektor hat keine DASP-Zuordnung; Recall und Precision bleiben gleich,
nur die Gesamtzahl eines Laufs kann um einzelne Findings schwanken.

---

## 5. Einordnung: Wofür taugt welches Werkzeug?

### Die Zahl, die am meisten täuscht

**GPTScans 0 % auf curated ist kein Werkzeugbefund.** Nur 16 von 143
Contracts lösten überhaupt einen LLM-Aufruf aus; die übrigen 127 verwarf der
Vorfilter. Die 6 Findings lagen auf Contracts mit anderem Primärlabel und
zählen gegen eine Single-Label-Ground-Truth nicht. Einschränkung: In 87 Tasks
lehnte GPTScans Grammatik Teile des Solidity-0.4-Codes ab und sah im Median nur
ein Viertel der Funktionen
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Nachtrag 4.7)
— an den 0 % ändert das nichts, an der Begründung „kein Schlüsselwort“ für alle
127 schon. Auf seiner Zieldomäne liefert dasselbe Werkzeug 77 statisch
bestätigte Findings auf 40 Contracts für $0,28.

### Die zweite Zahl, die täuscht

**LLMSmartAudits 30 % Precision sind eine Untergrenze.** Drei Dinge drücken sie:

1. curated labelt eine Schwachstelle je Datei; ein richtiger Zweitbefund zählt
   als False Positive.
2. 468 der 1 124 Findings haben keine DASP-Nummer und fallen heraus. Welcher
   Detektor welche Nummer trägt und warum, steht in
   [`mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md) — samt den zwei
   Grenzfällen (`Centralization Risk`, `Incorrect Constructor Name`), die die
   Precision auf 30,9 % bzw. 29,5 % verschieben würden.
3. Unsere Stichprobe von 19 Extra-Kategorie-Treffern: 15 plausibel, 4
   generisch, 0 falsch
   ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), 4.2).

Je Kategorie muss man die Precision gegen die Basisrate lesen: bei
`unchecked_low_level_calls` 79 % gegen 36 %, bei `access_control` nur 19 %
gegen 13 % — kaum besser als Raten. Umgekehrt ist der Recall von 97 % eine
**Obergrenze**, weil bei 7,9 Findings je Contract ein Zufallstreffer billig
ist. Die wahren Werte liegen näher beieinander, als die Tabelle nahelegt.

### Wofür welches Werkzeug taugt

**Slither** ist erste Wahl für alles, was sich am Code-Muster erkennen lässt,
und einzige Wahl, wenn Determinismus, null Kosten und Sekunden zählen. Auf
klassischen Schwachstellen ist es das präziseste (F1 54 %). Logikfehler kann es
prinzipiell nicht finden.

**GPTScan** taugt für seine zehn DeFi-Szenarien — und dafür ist es erstaunlich
billig ($0,0029 je DeFi-Contract) und schnell, weil der Vorfilter die meiste
Arbeit gar nicht entstehen lässt. Es arbeitet funktionsweise und skaliert
deshalb auf große Contracts. Der Preis: Außerhalb der zehn Regeln meldet es
nichts, und ohne Compilat fehlt der Präzisionsschutz.

**LLMSmartAudit** ist das breiteste: 41 Detektoren, auch für Dinge ohne
DASP-Kategorie (fehlende Withdrawal-Funktion, Zentralisierungsrisiko,
Präzisionsverlust). Auf kleinen Contracts findet es fast alles Gelabelte. Dafür
ist es rund 250-mal so teuer wie GPTScan und 140-mal so langsam wie Slither,
scheitert auf realen DeFi-Contracts an der Kontextgrenze und liefert weder
Zeilennummern noch Severity — jedes Finding muss man von Hand im Code suchen.

### Was dieser Vergleich nicht zeigt

1. **Keine Erkennungsleistung auf DeFi-Logik** — ohne Ground Truth lässt sich
   dort nur beschreiben.
2. **Keinen Werkzeug-Verbund** — ob GPTScan und Slither zusammen mehr finden
   als LLMSmartAudit, haben wir nicht untersucht.
3. **Keine Verteilung** — die Streuung beruht je LLM-Werkzeug auf zwei Läufen;
   daraus folgen weder Standardabweichung noch Konfidenzintervall.
4. **Nur ein Modell** (`deepseek-v4-flash`, das günstige Tier). Ein stärkeres
   Modell ließe sich ohne Code-Änderung einsetzen (`README.md`, „Modell wählen
   und wechseln“).
5. **Nicht zeilengenau**, solange LLMSmartAudit keine Zeilennummern liefert.
6. **143 Dateien sind nicht 143 Contracts.**
   `0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` liegt unter `reentrancy`
   und unter `unchecked_low_level_calls`, wird also zweimal analysiert und
   gewertet. „Single-Label“ gilt je Datei, nicht je Contract; eindeutig ist
   erst `(label_dir, contract_id)`. Auf die Kennzahlen wirkt sich das kaum aus.
