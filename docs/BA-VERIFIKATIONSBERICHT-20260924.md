# Zweitprüfung des Repositorys, Stand 24.09.2026

Geprüfter Stand: `main` bei `7562bde` (Push vom 21.09.2026). Die Prüfung las
das Repository vollständig, führte alle Auswertungsskripte und Tests aus,
rechnete jede Zahl der Dokumentation gegen die Rohdaten unter
`smartbugs/results/` nach und verglich die Fremdbäume per Datei-Hash mit den
echten Upstream-Ständen. Danach wurden die Befunde in thematisch getrennten
Commits behoben; Abschnitt 3 nennt zu jedem Befund den Commit. Der erste
Verifikationsbericht vom 02.08.2026 ([`BA-VERIFIKATIONSBERICHT.md`](BA-VERIFIKATIONSBERICHT.md))
bleibt als datierter Stand stehen und trägt einen Nachtrag.

**Maßstab wie beim ersten Bericht:** Jede Behauptung wurde mit dem Ziel
geprüft, sie zu widerlegen. Eingestellte Arbeitspakete (AP2, AP4, AP7) und das
im Repository nicht prüfbare AP8 zählen nicht als Mangel. Prüfskripte und
Zwischenausgaben lagen in einem temporären Arbeitsverzeichnis außerhalb des
Repositorys; die verwendeten Befehle stehen bei jedem Punkt.

---

## 1. Was ausgeführt wurde

| Prüfung | Ergebnis am 24.09.2026, vor den Korrekturen |
|---|---|
| `python -m pytest tests -q` | 230 passed |
| `python analysis_tools/parser_audit.py` | 48 Läufe, 1 272 Tasks, 2 417 Rohmeldungen, 0 Lücken; Markdown identisch mit `docs/parser-audit-nachher.md` |
| `python analysis_tools/secret_scan.py --all` | 1 224 Dateien, kein Fund, 1 nicht gescannt (das 20-MB-Jar) |
| `python analysis_tools/errors_fails_report.py` | identisch mit `docs/errors-fails.md` |
| `python evaluate_curated.py --suffix v1_20260705` | identisch mit `eval/curated_v1_20260705__metriken.md` |
| `curated_eval.py`, `build_eval.py`, `gptscan_eval.py`, `per_contract_stats.py` mit umgeleiteter Ausgabe | alle `findings.jsonl`, `run_meta.json`, `summary.md` und CSVs reproduzieren feldgleich; Abweichungen nur in zwei von Hand ergänzten READMEs (K3) |
| Klone von `smartbugs@7ddaf6c`, `GPTScan@29a1747`, `LLMSmartAuditTool@c507fe4`, Hash-Vergleich | Eigenanteil-Zählungen 515/3/254, 38/7/19 und 212/9/14 bestätigt; in `smartbugs/sb/` weichen genau `docker.py` und `tools.py` ab |
| Mutationsprobe in einer Kopie der Testsuite | 12 Mutationen, 10 von mindestens einem Test erkannt (M4) |
| Inventar `smartbugs/results/` | 48 Läufe, 1 272 Tasks, 6 401 Dateien, 1 085 889 921 Byte |
| Prüfung relativer Markdown-Links | 54 Dateien, 0 tote Links |

Die Prüfung selbst setzte keinen LLM-Aufruf ab. Erst nach dem Bericht wurden
mit ausdrücklicher Freigabe drei Läufe gestartet (Abschnitt 4).

---

## 2. Was standgehalten hat

Alle Kennzahlen der Auswertung reproduzieren aus den Rohdaten: Recall,
Precision und F1 je Kategorie; 16 Contracts mit LLM-Aufruf, 72 Aufrufe und
$0,0098 für GPTScan auf curated; 1 124 und 2 154 Findings für LLMSmartAudit und
Slither; 1 763 unklassifizierte Slither-Findings mit 57 High und 60 Medium; 37
Kontext-Abbrüche im DeFi-Lauf; 74 GPTScan-Findings auf 37 Contracts mit MAIN;
längster Task 922 s; Jaccard 805 gemeinsame Paare, 61,4 % und 60,5 %, 7
identische Detektorsätze; 20 von 27 identische GPTScan-Ergebnisse; alle Zahlen
des Timeout-Nachweises in Protokoll 4.5; Korpus-Reparatur 33/50/13, 1 279
Dateien, 49 Contests, 96 von 96 übersetzbar; 41 Detektoren in `findings.yaml`
und `ChatChainConfig.json`; die drei Slither-Detektoren ohne Klassifikation.
Der Secret-Scan über den ganzen Baum ist sauber, die Redaktion in `sb/docker.py`
wirkt (Mutationsprobe: 2 bzw. 5 Tests rot, wenn man sie entfernt).

---

## 3. Befunde und Erledigung

### 3.1 Falsch

| Nr. | Stelle (Stand `7562bde`) | Befund | Korrektur | Commit |
|---|---|---|---|---|
| F1 | `LICENSE:59` | Patches in `smartbugs/sb/`: `docker.py, tools.py, solidity.py, analysis.py, io.py` | nur `docker.py` und `tools.py`, dazu `.gitignore`; eigene Dateien in den Fremdbäumen zugeordnet (M7) | `603d511` |
| F2 | `BA-EIGENANTEIL.md:462-467` | „nur die Blöcke 1–7 und 10“, „Blöcke 8 und 9“, „Regex-Korrektur“ | sieben Blöcke in `docker.py` und `tools.py`; die Regex-Korrektur ist Upstream-Arbeit | `603d511` |
| F2b | dieselbe Datei `:48`, `:184`, `:286` | „(nicht ganz vollständig noch)“, „vier inhaltlich geänderten“, „übrigen 18 Dateien“ | Überschrift bereinigt, zwei Dateien, 22 übrige (`git ls-files smartbugs/sb` = 24) | `603d511` |
| F3 | `BA-BETREUERGESPRAECH-AUFGABEN.md:345` | „21 (7 · 9 · 5 SmartBugs)“ | 18 (7 · 9 · 2, dazu `.gitignore`) | `603d511` |
| F3b | dieselbe Datei `:343-344`, `:348`, `:351` | 6 121 Zeilen, ~31 600 Wörter, 4 in LaTeX, 19 Läufe, 168 Tests | 13 881 Zeilen (davon 3 485 Tests), rund 65 000 Wörter in 27 handgeschriebenen Dokumenten, kein LaTeX, 48 Läufe, aktuelle Testzahl; Zählweise steht jetzt unter der Tabelle | `603d511`, Testzahl im Abschlusscommit |
| F4 | `BA-BETRIEB.md:41` | GPTScan „Median ~$0,0009“ je Contract | curated_v1: Mittel $0,00007, Median $0 (127 von 143 ohne LLM-Aufruf); DeFi-Korpus: Median $0,0013, Mittel $0,0029, Maximum $0,020 | `e227c4b` |
| F4b | `BA-BETRIEB.md:3` | „aus den 19 durchgeführten Läufen (Stand 2026-08-02)“ | 48 Läufe, Stand 24.09.2026 | `e227c4b` |
| F5 | `BA-WERKZEUGE-IM-VERGLEICH.md:401`, `:218` | „171-mal so teuer“, „drei Größenordnungen“ | rund 250-mal ($2,44 gegen $0,0098), „mehr als zwei Größenordnungen“ | `e227c4b` |
| F6 | `BA-DURCHFUEHRUNGSPROTOKOLL.md:95`, `BA-GPTSCAN-VERGLEICH.md:27` | Laufzeit `curated_mwe_20260706` „13:22 min“ | 13:17 (SmartBugs-Meldung), Task-Spanne 13:10 | `e227c4b` |
| F7 | `BA-TESTLAUF-AUSWERTUNG.md` | Zahlen des DeFi-Laufs vor dem Nachlauf vom 15.09. (55 Contracts, 2 481 Aufrufe, ≈ $8,00), ohne Stand-Vermerk | Kasten „Stand 18.08.2026, wird nicht nachgeführt“ mit den aktuellen Zahlen (59, 437, 2 624, 90 206 s, ≈ $8,37); README führt das Dokument als datiert | `bfa30f7` |
| F7b | dieselbe Datei, `run_full_v2_llmsa.ps1:31` | „AP5 offen“ | seit 18.08.2026 erledigt, Verweis auf Protokoll 4.5 | `bfa30f7` |
| F8 | `GPTScan/docs/SMARTBUGS_INTEGRATION.md:54-56`, `:86` | Allowlist „fixed“ in `docker.py` mit fünf Namen; Provider „deepseek or openai“ | Allowlist steht in `config.yaml` (`env:`, sieben Namen), `sb/tools.py` und `sb/docker.py` Block 2 und 5; `custom`, `GPTSCAN_BASE_URL`, `GPTSCAN_API_KEY` ergänzt | `08082d8` |
| F9 | `README.md:256-258`, `:345`; `BA-WERKZEUGE-IM-VERGLEICH.md:121-127`; `run_retry_llmsa.ps1:20-24` | `LLM_CONTEXT_TOKENS` als Stellschraube der Kontextgrenze; „weil die DeepSeek-API nicht mehr annimmt“; „38 Tasks“ | Zwei Grenzen benannt: Agentengrenze fest 65 536 in `camel/utils.py` (bis 24.09.), Completion-Budget aus der Variablen; kein API-Fehler, werkzeuginterner Abbruch bei 76 456 Token; 37 Tasks | `08082d8`, `8a53d79` |
| F10 | `BA-DURCHFUEHRUNGSPROTOKOLL.md:385` | Limitation 2: „Slither: 1 854“, „zwei Zusatz-Mappings“ | 1 763 seit Nachtrag 4.6, fünf Mappings; Tabelle 4.1 trägt einen Stand-Vermerk | `bfa30f7` |
| F11 | `README.md:75` | „6 297 Dateien, 1,08 GB“ | 6 401 Dateien, 1,09 GB (Stand 24.09., vor den neuen Läufen); Endstand im Abschlusscommit | `e227c4b` |
| F12 | `BA-AUFGABEN-UND-STATUS.md:156`, `:176` | „72 Commits (Stand 21.09.2026)“ | 83 am Abend des 21.09.2026 | `e227c4b` |
| F13 | Protokoll 4.1 gegen `WERKZEUGE` 4.1 und `GPTSCAN-VERGLEICH` | „3:19 min“ neben „3,2 min“ ohne Erklärung | beide Größen benannt: SmartBugs-Meldung gegen Task-Spanne (193 s, 10 929 s, 76 s) | `e227c4b` |
| F14 | `BA-VERIFIKATIONSBERICHT.md` 3.1, 6 | „fünf geänderte Dateien“, Vergleichsstand `v2.1.1` | Nachtrag vom 24.09.2026 im Dokument; README führt es als datierten Bericht | `bfa30f7` |
| F15 | `analysis_tools/redact_results.py:9` | Redaktion in `sb/docker.py:159-163` | Verweis auf Block `BA MODIFICATION 5` statt Zeilennummern | `e227c4b` |

Zusätzlich bei der Umsetzung gefunden: `smartbugs/uv.lock` ist 52 Byte groß
und enthält keinen Paketeintrag; `BA-EIGENANTEIL.md` behauptete, die Datei
schreibe „die tatsächlich installierten Versionen fest“. Korrigiert in
`6557e9f`; ob die Datei bleibt, entscheiden die Autoren.

### 3.2 Kaputt

| Nr. | Befund | Korrektur | Commit |
|---|---|---|---|
| K1 | `run_full_v2_llmsa.ps1` und `run_retry_llmsa.ps1` verlangten `smartbugs\venv`, alle Dokumente und die beiden anderen Runner `smartbugs\.venv`; beide Skripte brachen in der dokumentierten Umgebung sofort ab | Pfad angeglichen, Herkunft im Kopfkommentar vermerkt | `6913bc6` |
| K2 | `core.hooksPath` und `core.longpaths` waren in diesem Clone nicht gesetzt; der Secret-Scan-Hook war inaktiv | lokal gesetzt (kein Commit); jeder Clone muss das nach `BA-BETRIEB.md` 7 selbst tun | – |
| K3 | `eval/curated_v1_20260705__gptscan/README.md` und `__slither-0.11.3/README.md` enthielten Sätze, die der Generator nicht schrieb; der dokumentierte Aufruf hätte sie überschrieben | Sätze in `curated_eval.py::write_readme` übernommen, Zahlen darin berechnet; `eval/` regeneriert, Zahlenartefakte unverändert | `4520f3b` |
| K4 | Kein Befehl im Repository legte `smartbugs/.venv` an oder installierte `pyyaml`/`pytest` für das System-Python | README-Abschnitt „Umgebung anlegen“, `requirements-dev.txt`, Verweise in BETRIEB 7 und BEDIENUNG 1; der Weg wurde in einer frischen venv nachvollzogen | `6557e9f` |
| K5 | Docker lief bei der Prüfung nicht | Am 24.09. lief Docker: Images `smartbugs/gptscan:1.0` 2,14 GB, `smartbugs/llmsmartaudit:1.0` 587 MB, `smartbugs/slither:0.11.3` 490 MB vorhanden; das LLMSmartAudit-Image wurde nach `8a53d79` neu gebaut (ID `7c111aa6b366`, vorher `e72f37d07212`) | – |

### 3.3 Fehlt

| Nr. | Befund | Erledigung | Commit |
|---|---|---|---|
| M1 | Keine Slither-Baseline auf dem DeFi-Korpus | Lauf `slither_mwefixed_v1` am 24.09.2026, Abschnitt 4.1; 45 von 96 Contracts ohne Ergebnis aus einem Werkzeugketten-Grund (Fallstrick 10) | `dc8516f` |
| M2 | ANTLR-Frage seit 02.08. offen | Protokoll Nachtrag 4.7 und Limitation 9: 87 von 143 Tasks mit Grammatik-Ablehnungen, alle Solidity 0.4, `functions` im Median ein Viertel der Deklarationen; Vorbehalt in `WERKZEUGE` 5 und `GPTSCAN-VERGLEICH` 2 | `dc8516f` |
| M3 | WARNING-Records außerhalb des Parser-Audit-Katalogs | in `BA-PARSER-AUDIT-LUECKEN.md` 4 benannt (`Cannot find functionB`, zwei Tasks); Katalog nicht erweitert | `bfa30f7` |
| M4 | Kein Test verlangte, dass ein Treffer die gelabelte Kategorie trifft; Zeilennummern des GPTScan-Parsers ungetestet | zwei Tests; dazu Link-Test über alle Dokumente und Abgleich der Tabelle 4.1 mit `run_meta.json` | `4520f3b`, `7acb55a` |
| M5 | Rohdaten von `llmsa_curated_v2` fehlen | unverändert; die Dateien liegen beim zweiten Verfasser (`eval/_runlogs/README.md`) | offen |
| M6 | Formulierungen aus einem Arbeitsprozess in `BA-VERIFIKATIONSBERICHT.md:8,11` | neutral formuliert | `bfa30f7` |
| M7 | `LICENSE` ordnete eigene Dateien in den Fremdbäumen nicht zu | Zuordnung ergänzt: eigene Dateien im LLMSmartAudit-Baum unter MIT, eigene Dateien im GPTScan-Baum als Teil des bearbeiteten GPTScan unter AGPL-3.0. **Diese Zuordnung ist ein Vorschlag, den die Autoren bestätigen müssen.** | `603d511` |
| M8 | Was der Fließtext braucht | Slither-Spalte für den DeFi-Korpus ergänzt (4.2); Wanduhr-Begriffe benannt; Spannen an Einzelzahlen weiterhin nur in 4.4; keine Abbildung im Repository | teils |

### 3.4 Angreifbar

| Nr. | Punkt | Stand nach dem 24.09.2026 |
|---|---|---|
| A1 | GPTScans 0 % auf curated hängt auch am Parser, nicht nur am Vorfilter | quantifiziert (Nachtrag 4.7); die Aussage „127 ohne Schlüsselwort“ ist nur für 56 vollständig geparste Tasks belegt |
| A2 | Die Kontextgrenze 65 536 war eine selbst gesetzte Konstante | Anbieterdokumentation nennt für `deepseek-v4-flash` 1M Token; die Grenze ist seit `8a53d79` über `LLM_CONTEXT_TOKENS` einstellbar; Nachlauf über die 37 Contracts in Abschnitt 4.2 |
| A3 | DASP-Zuordnung der 41 LLMSmartAudit-Detektoren ohne Begründung je Detektor; keine Regel, wann nachgemappt wird | offen; Basisrate je Kategorie steht jetzt neben der Precision (`metriken.md`) |
| A4 | Kosten je analysiertem Contract vergleicht 96 mit 59 Contracts | Tabelle 4.2 benennt es; unverändert |
| A5 | Zwei Läufe sind keine Streuung; keine Einzelzahl trägt eine Spanne | Wilson-Intervalle für den Recall je Kategorie ergänzt (`4520f3b`); Lauf-zu-Lauf-Spannen weiterhin nur in 4.4 |
| A6 | Timeout-Nachweis auf je einem Contract | unverändert, steht als Limitation 7 |
| A7 | Dieselben Kennzahlen in mindestens neun Dokumenten | README trennt jetzt lebende von datierten Dokumenten; ein Test vergleicht Tabelle 4.1 mit `run_meta.json`; die Mehrfachpflege bleibt |

### 3.5 Weitere Befunde

| Nr. | Befund | Erledigung | Commit |
|---|---|---|---|
| N1 | Ground Truth ungepinnt: `run_curated.ps1` klonte `smartbugs-curated` ohne Commit; der lokale Clone steht auf `230e649` (16.06.2024), nirgends dokumentiert | Clone gepinnt, Warnung bei Abweichung; Stand in README, `evaluate_curated.py`, `run_meta.json` (`ground_truth_commit`) und `metriken.md` | `6913bc6`, `6557e9f`, `4520f3b` |
| N2 | `VERSION` beider Parser stand auf „2026/08/02“ trotz Änderungen am 17.08. und 21.09.; SmartBugs schreibt den Wert in jede `result.json` | Stempel auf das Datum der letzten Änderung, Konvention als Kommentar, alle Läufe neu geparst (Zahlen unverändert) | `040216a` |
| N3 | Qualitative Stichproben (19, 10, 6 und 4 Urteile) ohne Liste im Repository | offen; braucht die Notizen der Autoren | offen |
| N4 | Beide Allowlists reichen `OPENAI_API_KEY` auch bei Provider `deepseek` in den Container | die Runner entfernen vor dem Start die Schlüssel, die der Anbieter nicht braucht | `6913bc6` |

---

## 4. Neue Messungen vom 24.09.2026

### 4.1 Slither auf `mwevariety_fixed` (`slither_mwefixed_v1`, kostenlos)

96 Tasks, `--timeout 600`, 4 Prozesse, 8:46 min. 51 Contracts analysiert (50
mit Findings, einer ohne), 4 319 Findings aus 46 Detektoren, nach Impact 3 268
Informational, 50 Optimization, 581 Low, 358 Medium, 62 High. 45 Contracts
blieben ohne Ergebnis, weil die von SmartBugs bereitgestellten solc-Binaries
0.7.6 und 0.8.1 bis 0.8.12 gegen glibc gelinkt sind und im Alpine-basierten
Slither-Image nicht starten (nachgestellt im Container; `BA-BETRIEB.md`
Fallstrick 10, Protokoll 4.8, `WERKZEUGE` 4.2). Die Baseline-Lücke ist damit
zur Hälfte geschlossen; der Rest braucht ein glibc-basiertes Slither-Image
oder statisch gelinkte Compiler.

### 4.2 LLMSmartAudit über die 37 Kontext-Contracts mit angehobener Grenze (`llmsa_mwefixed_v2_ctx1m`)

Voraussetzung war `8a53d79`: `camel/utils.py` liest die Agentengrenze aus
`LLM_CONTEXT_TOKENS` (Default 65 536), das Image wurde daraus neu gebaut.
Lauf mit `LLM_CONTEXT_TOKENS=1000000`, `LLM_MAX_COMPLETION_TOKENS=32768`,
4 Prozessen, Timeout 7 200 s je Task und Kostendeckel 8 USD über
`run_retry_llmsa.ps1`. Der Modellname `deepseek-v4-flash` wird vom Anbieter
seit September 2026 auf DeepSeek-V4.1-Flash geleitet; die Ergebnisse sind
deshalb mit einem anderen Modellstand entstanden als der Hauptlauf vom
16.08.2026.

*Ergebnis: wird nach Abschluss des Laufs ergänzt.*

### 4.3 LLMSmartAudit mit MAIN über dieselben 37 Contracts (`llmsa_mwefixed_v2_main37`)

Gegenprobe mit der alten Grenze 65 536: Reduziert der Entrypoint die Datei auf
den Hauptcontract (`scripts/main_contract.py`), passen die Contracts dann in
das Fenster? Dafür wurde mit `corpus_tools/make_main_corpus.py` eine Kopie des
Korpus angelegt, in der jede Datei nach ihrem Hauptcontract heißt (SmartBugs
verlangt das für `--main`), und `run_retry_llmsa.ps1` um `-Corpus` und `-Main`
erweitert. 3 Prozesse, Kostendeckel 3 USD.

*Ergebnis: wird nach Abschluss des Laufs ergänzt.*

---

## 5. Offen und Empfehlungen

1. **Rohdaten von `llmsa_curated_v2`** vom zweiten Verfasser übernehmen und mit
   `build_eval.py` gegen `eval/llmsa_curated_v2/findings.jsonl` prüfen (M5).
2. **Stichprobenliste** der qualitativen Urteile anlegen oder im Protokoll 4.2
   vermerken, dass die Einzelurteile nicht archiviert wurden (N3).
3. **Lizenzzuordnung** der eigenen Dateien in den Fremdbäumen bestätigen (M7).
4. **`smartbugs/uv.lock`** entfernen oder durch eine echte Festschreibung
   ersetzen; die Datei pinnt nichts.
5. **Slither-Baseline vervollständigen:** glibc-basiertes Slither-Image oder
   statische solc-Builds für 0.7.6 bis 0.8.12, dann die 45 Contracts nachfahren.
6. **DASP-Zuordnung der LLMSmartAudit-Detektoren** je Detektor begründen, wie
   `GPTScan/taxonomy/mapping.md` es für GPTScan tut (A3).
7. **Betrieb:** Image-ID je Lauf in `run_params.json` aller Runner; `ENV
   LLM_MODEL` mit Wächter im LLMSmartAudit-Entrypoint; eine CI, die `pytest`,
   `secret_scan.py --all` und den Link-Test ausführt.
8. **Für den Fließtext:** mindestens eine Abbildung der Werkzeugkette
   (SmartBugs, Container, Entrypoint, Parser, Auswertung); das Repository
   enthält keine.

---

## 6. Fazit

Die Messdaten und Auswertungen reproduzieren vollständig aus den Rohdaten;
daran hat die Zweitprüfung nichts geändert. Die Dokumentation widersprach sich
an fünfzehn Stellen, zwei Runner liefen in der dokumentierten Umgebung nicht,
und zwei Sachfragen berührten die Interpretation der beiden Hauptergebnisse.
Beide sind jetzt beantwortet: Die Grammatik-Ablehnungen betreffen 87 der 143
curated-Contracts und schwächen die Begründung „kein Schlüsselwort“, nicht das
Ergebnis 0 %; die Kontextgrenze von 65 536 war eine Konstante des Werkzeugs,
nicht des Anbieters, und ist seit dem 24.09.2026 einstellbar. Offen bleiben
die Rohdaten eines Laufs, die Liste der Stichprobenurteile, die Bestätigung
der Lizenzzuordnung und die zweite Hälfte der Slither-Baseline.
