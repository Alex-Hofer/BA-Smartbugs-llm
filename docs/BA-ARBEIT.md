# KI-gestützte Smart-Contract-Scanner im SmartBugs-Framework

**Technical Report zur Bachelorarbeit**
Alex Hofer und Alex Unterleitner · TU Wien · Betreuer: Gernot Salzer und Monika di Angelo ·
Messzeitraum Juli bis September 2026

---

## Kurzfassung

Wir integrierten die LLM-gestützten Schwachstellenscanner **GPTScan** und
**LLMSmartAudit** als reguläre Werkzeuge in **SmartBugs 2.1.1** und
evaluierten sie gegen den statischen Analysator **Slither 0.11.3**. Für den
Betrieb fehlten dem Rahmenwerk drei Funktionen, die wir ergänzten: die
Weitergabe von Umgebungsvariablen (API-Schlüssel) in den Container, deren
Schwärzung in den Ergebnisdateien und ein robustes Aufräumen der
Task-Verzeichnisse unter Windows.

Auf dem Standard-Benchmark `smartbugs-curated` (143 Dateien) erreichte
LLMSmartAudit einen Recall von 97 % bei 30 % Precision (F1 45 %), Slither 67 %
bei 45 % (F1 54 %). GPTScan erzielte 0 %, da der Datensatz keine der
DeFi-Logikfehler enthält, auf die seine zehn Regeln ausgelegt sind. Auf 96
realen DeFi-Contracts, die wir zunächst kompilierbar machen mussten, meldete
GPTScan 77 Findings auf 40 Contracts bei Kosten von 0,28 USD. Slither meldete
dort 7 096 überwiegend stilistische Findings. LLMSmartAudit scheiterte auf 37
Contracts an einer fest im Werkzeug hinterlegten Kontextgrenze. Nach deren
Anhebung wurden alle 37 vollständig analysiert. LLMSmartAudit war rund 250-mal
so teuer wie GPTScan und rund 140-mal so langsam wie Slither. Beide
LLM-Werkzeuge liefern bei Wiederholung nicht dieselben Ergebnisse.

---

## 1. Einleitung und Fragestellung

Statische Analysatoren wie Slither erkennen Schwachstellen anhand von
Code-Mustern, etwa einen externen Aufruf vor einer Zustandsänderung, einen
ungeprüften Rückgabewert oder einen Zeitstempel als Zufallsquelle. Fehler in
der *Absicht* eines Contracts erkennen sie dagegen nicht. Ein Beispiel ist
ein Liquidity-Pool, der den Wert eines Tokens aus einem Spotpreis ableitet, den
ein Angreifer im selben Block manipulieren kann. Der Code ist dabei syntaktisch
korrekt. Die Schwachstelle liegt im ökonomischen Modell. Neuere Werkzeuge
setzen für solche Fehler große Sprachmodelle ein. Deren Nutzen lässt sich nur
im Vergleich mit einer etablierten Referenz einordnen. Als Referenz eignet sich
Slither, weil es bis auf einen Detektor deterministisch arbeitet, nichts kostet
und nach wenigen Sekunden fertig ist. Im Vergleich mit Slither zeigt sich, was
ein LLM-Werkzeug zusätzlich findet und welche Nachteile es bei Kosten, Laufzeit
und Reproduzierbarkeit mit sich bringt.

Ein LLM-Werkzeug stellt Anforderungen, die SmartBugs bislang nicht vorsah:
einen API-Schlüssel zur Laufzeit, Netzzugang aus dem Container und eine
Modellwahl. Zudem verursacht jeder Aufruf Kosten, und die Ergebnisse sind nicht
deterministisch. Daraus ergibt sich unsere Leitfrage: **Was leisten
LLM-gestützte Schwachstellenscanner für Smart Contracts, wenn man sie als
reguläre SmartBugs-Werkzeuge betreibt, gemessen an einem klassischen
statischen Analysator?**

Wir gliedern sie in vier Teilfragen. Erstens, ob sich GPTScan und
LLMSmartAudit so integrieren lassen, dass sie wie jedes andere Werkzeug
aufgerufen, ausgewertet und verglichen werden können, und was SmartBugs dafür
fehlt. Zweitens, wie beide auf `smartbugs-curated` je DASP-Kategorie in Recall
und Precision gegenüber Slither abschneiden. Drittens, was sie auf realen
DeFi-Contracts liefern, für die GPTScan entwickelt wurde und für die keine
Ground Truth existiert. Viertens, welche Kosten und Laufzeiten sie verursachen,
wie robust sie laufen und wie stabil ihre Ergebnisse über wiederholte Läufe
sind.

---

## 2. Untersuchte Werkzeuge

**GPTScan** kombiniert ein Sprachmodell mit leichtgewichtiger
Programmanalyse. Das LLM identifiziert Kandidaten anhand von zehn
DeFi-Szenarien (`MWE-200` bis `MWE-209`), von denen acht kein Gegenstück in SWC
oder DASP haben. Anschließend bestätigt eine statische Analyse die Kandidaten
am kompilierten Contract. Ohne erfolgreiche Kompilierung entfällt diese
Bestätigungsstufe, und das Werkzeug arbeitet als reiner Prompt-Scanner.

**LLMSmartAudit** ist eine Multi-Agenten-Pipeline auf Basis von ChatDev/CAMEL.
Mehrere LLM-Rollen prüfen den Quelltext nacheinander gegen 41 Detektor-Prompts
(Modus `SmartContractTA`, die Upstream-Dokumentation nennt 40). Das Werkzeug
kompiliert nie und liefert weder Zeilennummern noch eine eigene
Severity-Einschätzung.

**Slither 0.11.3** dient als statische Referenz. Es kompiliert den Contract,
erzeugt eine Zwischendarstellung und wendet darauf Detektoren an. Die
SmartBugs-Integration kennt 102 Finding-Namen. Slither benötigt weder Netz noch
API-Schlüssel. Wir verwendeten es unverändert.

Als Rahmenwerk verwenden wir SmartBugs 2.1.1. Als LLM-Backend diente in allen
Läufen DeepSeek `deepseek-v4-flash`, gewählt aus Kostengründen.

---

## 3. Umsetzung

Für beide LLM-Werkzeuge erstellten wir vollständige SmartBugs-Integrationen.
Dazu gehören eine Konfiguration mit Image, Netzfreigabe und erlaubten
Umgebungsvariablen, eine Taxonomie, die jedem Finding-Namen eine SWC- und
DASP-Klasse sowie eine Severity zuordnet, ein Parser, ein Entrypoint und je ein
eigenes Docker-Image. Das LLMSmartAudit-Image verkleinerten wir von 5,13 GB auf
587 MB. Anbieter und Modell sind zur Laufzeit wählbar und nicht im Image
festgelegt.

SmartBugs selbst erweiterten wir an zwei Stellen. Eine neue
Konfigurationsoption reicht ausschließlich benannte Host-Variablen in den
Container weiter, und deren Werte werden geschwärzt, bevor SmartBugs die
Aufrufparameter speichert. Ohne diese Erweiterung müsste der API-Schlüssel im
Image liegen oder stünde im Klartext in jedem Ergebnisordner. Zusätzlich räumt
SmartBugs die Task-Verzeichnisse nun mit Wiederholungen auf, weil unter Docker
Desktop für Windows sonst Ergebnisse unbemerkt verloren gingen. Alle übrigen
Dateien des Rahmenwerks sind byteidentisch zum Upstream.

GPTScan meldete Kompilierfehler ursprünglich nur im Log, während die
Ergebnisdatei einen fehlerfreien Lauf auswies. Ein von uns entwickeltes
Parser-Audit fand über die damals 930 Tasks 1 368 von 1 464 Rohmeldungen nicht
im Parser-Output wieder. Nach der Reparatur fehlen 0 von inzwischen 2 555
Rohmeldungen.

Für die DeFi-Evaluation rekonstruierten wir einen kompilierbaren Korpus aus den
Originalquellen. Den Timeout von SmartBugs, der für beide Werkzeuge bisher nur
als harter Abbruch des Containers wirkte, reicht der Entrypoint nun in das
Werkzeug weiter. Bei 70 % der Frist stellt GPTScan neue LLM-Aufrufe ein und
lässt seine Pipeline regulär auslaufen. Bei 90 % beendet ein
`timeout`-Kommando den Prozess, und der Entrypoint sichert den Zwischenstand,
den LLMSmartAudit nach jeder Detektorphase schreibt. Beide Pfade kennzeichnen
das Teilergebnis mit einem eigenen Marker. Da keines der Werkzeuge eine
Contract-Auswahl kennt, reduziert ein zusätzlicher Parameter `MAIN` die
Eingabedatei auf den Contract, nach dem sie benannt ist.

Abgesichert ist die Umsetzung durch Auswertungsskripte, PowerShell-Runner,
einen lokalen LLM-Prüfstand für kostenfreie Tests sowie 276 Regressionstests,
die ohne Docker und API-Schlüssel gegen aufgezeichnete Rohdaten laufen und bei
jedem Push ausgeführt werden.

---

## 4. Methodik

### 4.1 Datensätze

Wir verwenden zwei Korpora mit unterschiedlicher Aussagekraft. Für
**`smartbugs-curated`** liegt eine Ground Truth mit genau einer
DASP-Primärschwachstelle je Datei vor. Hier **messen** wir Recall, Precision
und F1. Der Korpus **`mwevariety_fixed`** umfasst 96 reale DeFi-Contracts aus
49 Audit-Wettbewerben des Web3Bugs-Benchmarks und hat keine Ground Truth. Hier
**beschreiben** wir Findings, Abdeckung, Kosten und Ausfälle. Wir brauchen
beide Korpora: Nur der erste erlaubt Kennzahlen gegen eine Ground Truth, und
nur der zweite enthält die DeFi-Logikfehler, für die GPTScan entwickelt wurde.

Im Ausgangszustand war der DeFi-Korpus unbrauchbar, denn nur 1 von 96 Dateien
kompilierte. GPTScans statische Bestätigung lief deshalb nie. Wir ordneten jede
Datei per Byte-Abgleich ihrem Original zu (33 identisch, 50 als exakter Präfix
eines abgeschnittenen Originals, 13 über den gemeinsamen Dateikopf), betteten
1 279 Abhängigkeiten ein, flatteten alle 96 Dateien und übersetzten sie mit
`solc`. In GPTScans eigener Werkzeugkette scheitert nur `58_UniV3Vault.sol`
weiterhin. Diese Datei führen wir als *degradiert*.

Zwei Eigenheiten von `smartbugs-curated` beeinflussen alle Kennzahlen. Ein
zutreffender Zweitbefund zählt als False Positive, weil jede Datei nur ein
Label hat. Außerdem liegt eine Datei unter zwei Kategorien, sodass 143 Dateien
nicht 143 verschiedenen Contracts entsprechen.

### 4.2 Messläufe

Alle Läufe führten wir sequenziell je Werkzeug mit zwei bis vier parallelen
Containern aus. Der Timeout je Task betrug 600 s (Slither), 1 800 s (GPTScan)
und 3 600 bis 7 200 s (LLMSmartAudit). Da LLMSmartAudit keine eigene
Kostenbremse besitzt, begrenzen die Runner die Kosten je Lauf.

| Lauf | Werkzeug | Korpus | Zeitraum | Tasks |
|---|---|---|---|---:|
| `curated_v1_20260705` | GPTScan, LLMSmartAudit, Slither | curated | Juli 2026 | 3 × 143 |
| `curated_mwefixed_live` | GPTScan | DeFi | Juli 2026 | 96 |
| `gptscan_mwefixed_v2_main` (+ `_nomain`) | GPTScan mit `MAIN` | DeFi | August 2026 | 96 + 3 |
| `llmsa_curated_v2` | LLMSmartAudit | curated | August 2026 | 143 |
| `llmsa_mwefixed_v2` (+ `_retry`) | LLMSmartAudit | DeFi | August/September 2026 | 96 + 4 |
| `slither_mwefixed_v1`, `_v2` | Slither (Upstream- und glibc-Image) | DeFi | September 2026 | 2 × 96 |
| `llmsa_mwefixed_v2_ctx1m` | LLMSmartAudit, Kontextgrenze 1 Mio. Token | 37 DeFi-Contracts | September 2026 | 37 |

Die vier Nachlauf-Tasks von `llmsa_mwefixed_v2` waren im Hauptlauf an
erschöpftem API-Guthaben gescheitert. Der Nachlauf mit angehobener
Kontextgrenze lief auf einem neueren Modellstand als die übrigen
LLMSmartAudit-Läufe. Insgesamt umfasst die Arbeit 50 Laufverzeichnisse mit
1 501 Tasks, einschließlich Vorphasen-, Trocken- und Nachweisläufen. Vom
curated-Wiederholungslauf von LLMSmartAudit ist nur noch die abgeleitete
Auswertung vorhanden, die Rohdaten fehlen.

### 4.3 Auswertung

Die Auswertung erfolgt auf Contract-Ebene je DASP-Kategorie. Ein gelabelter
Contract gilt als erkannt, wenn das Werkzeug mindestens ein Finding meldet,
dessen DASP-Klasse der gelabelten Kategorie entspricht. Der Recall gibt an,
welchen Anteil der Contracts einer Kategorie ein Werkzeug erkannt hat. Die
Precision gibt an, welcher Anteil der Contracts, für die ein Werkzeug eine
Kategorie meldet, tatsächlich mit dieser Kategorie gelabelt ist. Als
Vergleichswert zur Precision nennen wir die Basisrate. Das ist die Precision
eines Werkzeugs, das die Kategorie für jeden Contract meldet. Zu jedem Recall
geben wir außerdem ein 95-%-Wilson-Intervall an.

Welcher DASP-Kategorie ein Finding angehört, legt die Taxonomie des jeweiligen
Werkzeugs fest. Das ist eine Tabelle, die jedem Finding-Namen eine Klasse
zuordnet. Bei Slither tragen fünf Detektoren im Upstream keine Klasse, obwohl
ihr Name eine SWC-Klasse nennt (`timestamp`, `weak-prng` und drei
`unchecked-*`-Detektoren). Für diese fünf ergänzten wir die Zuordnung. Die
Taxonomien der LLM-Werkzeuge veränderten wir nicht. Findings ohne DASP-Klasse
zählen weder für Recall noch für Precision. Das betrifft bei GPTScan 0 von 6,
bei LLMSmartAudit 468 von 1 124 und bei Slither 1 763 von 2 154 Findings.

Ein Contract ohne Findings gilt nur dann als sauber, wenn er tatsächlich
analysiert wurde. Wir unterscheiden deshalb fünf Ergebnisarten: *Findings*,
*sauber*, *degradiert* (GPTScan ohne Kompilat), *Kontext überschritten*
(LLMSmartAudit bricht ab, der Contract wird nie analysiert) und *gescheitert*.
Drei unabhängige Skripte berechnen dieselben Kennzahlen, und ein Parser-Audit
prüft für jeden Lauf, dass keine Rohmeldung verloren geht. Wo die Ground Truth
nicht ausreicht, prüften wir zusätzlich Stichproben direkt am Quellcode.

---

## 5. Ergebnisse

### 5.1 `smartbugs-curated` (143 Dateien)

| | GPTScan | LLMSmartAudit | Slither 0.11.3 |
|---|---:|---:|---:|
| Contracts mit Ergebnis | 143 | 143 | 140 |
| Contracts mit Findings | 6 | 143 | 140 |
| Findings gesamt / davon DASP-zugeordnet | 6 / 6 | 1 124 / 656 | 2 154 / 391 |
| erkannte Contracts (von 143) | 0 | 138 | 96 |
| geflaggte (Contract, Kategorie)-Paare | 6 | 464 | 214 |
| **Recall** | 0 % | **97 %** | 67 % |
| **Precision** | 0 % | 30 % | **45 %** |
| **F1** | – | 45 % | **54 %** |
| LLM-Aufrufe | 72 | 6 174 | 0 |
| Token (Prompt / Completion) | 25 580 / 22 302 | 12 554 710 / 3 517 916 | – |
| Kosten gesamt | $0,0098 | ≈ $2,44 (aus Token geschätzt) | $0 |
| Container-Zeit gesamt | 712,9 s | 42 792,5 s | 298,8 s |
| Wanduhr (erster Task-Start bis letztes Task-Ende) | 3,2 min | 182,1 min | 1,3 min |
| Tasks mit `errors` / `fails` | 2 / 0 | 0 / 0 | 3 / 3 |

LLMSmartAudit erkannte in sieben der zehn Kategorien alle gelabelten Contracts
(Recall 100 %) und bei `bad_randomness` 7 von 8 (88 %). Die Kategorien `other`
und `short_addresses` erkannte es gar nicht, weil es dafür keinen passenden
Detektor hat. Seine Precision lag zwischen 79 % bei `unchecked_low_level_calls`
(Basisrate 36 %) und 8 % bei `denial_of_service` (Basisrate 4 %). Bei
`access_control` lag sie mit 19 % nur knapp über der Basisrate von 13 %.

Slither erzielte gute Werte bei `reentrancy` (Recall 94 %, Precision 74 %) und
bei `unchecked_low_level_calls` (Recall 98 %, Precision 58 %). Für `arithmetic`
und `front_running` hat es keine passenden Detektoren. Ohne die drei ergänzten
`unchecked-*`-Zuordnungen hätte Slither einen Recall von 64 %, eine Precision
von 45 % und einen F1-Wert von 52 % erreicht.

GPTScan stellte nur für 16 der 143 Contracts überhaupt eine LLM-Anfrage. Seine
sechs Findings lagen alle auf Contracts mit einem anderen Primärlabel. Sechs
Kategorien umfassen höchstens acht Contracts, ihre Recall-Intervalle sind
deshalb 32 bis 79 Prozentpunkte breit.

Slither stürzte in drei Tasks im IR-Generator ab, und GPTScan meldete in zwei
Tasks behandelte Fehler. LLMSmartAudit lief ohne Fehler durch. Im
Wiederholungslauf überschritt bei ihm ein Contract das Kontextfenster.

### 5.2 DeFi-Korpus `mwevariety_fixed` (96 Contracts, ohne Ground Truth)

| | GPTScan | GPTScan mit `MAIN` | LLMSmartAudit | Slither (glibc-Image) | LLMSmartAudit, Grenze angehoben |
|---|---:|---:|---:|---:|---:|
| Contracts | 96 | 96 | 96 | 96 | 37 |
| davon analysiert | 96 | 96 | **59** | 95 | 37 |
| nicht analysiert (Grund) | – | – | 37 (Kontextfenster) | 1 (Compilerfehler) | – |
| ohne Kompilat (degradiert) | 1 | 1 | – | – | – |
| Contracts mit Findings | 40 | 37 | 59 | 94 | 37 |
| Findings gesamt | 77 | 74 | 437 | 7 096 | 317 |
| verschiedene Regeln / Kategorien | 8 von 10 | – | 34 von 41 | 48 Detektoren | 34 von 41 |
| LLM-Aufrufe | 1 614 | 1 518 | 2 624 | 0 | 1 625 |
| Kosten | $0,2769 | $0,3638 | ≈ $8,37 (geschätzt) | $0 | $5,55 abgebucht ($11,42 geschätzt) |
| Container-Zeit gesamt | 8 217 s | 11 772 s | 90 206 s | 647 s | 35 028 s |
| Wanduhr | 36,7 min | 50,9 min (53,5 min mit Nachlauf) | nicht ausgewiesen | 2,8 min | 5,0 h in zwei Teilen |

GPTScan lieferte auf seiner Zieldomäne 77 Findings aus acht seiner zehn Regeln,
44 davon zu `MWE-200` (Insecure LP Token Value Calculation). Auf 56 Contracts
übergab die LLM-Stufe Kandidaten an die statische Bestätigung, die auf 39
davon mindestens einen Kandidaten verwarf. Auf 35 Contracts endete die
statische Prüfung einzelner Kandidaten mit einer Ausnahme, insgesamt bei 80
Kandidaten (77 zu `MWE-200`, 3 zu `MWE-207`). Meist lag das daran, dass die
LLM-Antwort eine Validierungsregel nicht erfüllte. GPTScan verwirft solche
Kandidaten. Das kostet Recall, nicht Precision: Jedes der 77 gemeldeten
Findings hat die statische Prüfung bestanden. Mit `MAIN` wurden 41 der 96
Dateien auf ihren Hauptcontract reduziert. Drei Dateien enthielten keinen
Contract mit dem Namen der Datei. Diese drei analysierten wir deshalb in einem
Nachlauf ohne `MAIN`.

LLMSmartAudit lieferte für 37 der 96 Contracts (38,5 %) kein Ergebnis, weil die
Agenten-Konversation 65 536 Token überschritt. Diese Grenze ist eine im
Werkzeugcode hinterlegte Konstante aus der Zeit eines älteren Modells. Der
Anbieter nennt für das verwendete Modell ein Kontextfenster von 1 Mio. Token.
Ein Nachlauf über genau diese 37 Contracts mit angehobener Grenze analysierte
alle vollständig. Er ergab 317 Findings bei im Mittel 61 700 Prompt-Token je
Aufruf (Hauptlauf: 20 900). Die abgebuchten Kosten betrugen 5,55 USD. Wegen
des abweichenden Modellstands weisen wir Haupt- und Nachlauf getrennt aus.

Slither erreichte mit dem Upstream-Image nur 51 der 96 Contracts, weil mehrere
solc-Versionen im Alpine-basierten Image nicht starten. Mit einem eigenen
glibc-Image analysierte Slither 95 von 96 Contracts und meldete 7 096 Findings
aus 48 Detektoren (4 858 Informational, 112 Optimization, 1 254 Low,
748 Medium, 124 High), im Median 55 je Contract (GPTScan: 0). Am häufigsten
waren die Stilhinweise `too-many-digits` (2 020) und `naming-convention`
(1 886). Den verbleibenden Contract konnte bereits der Compiler nicht übersetzen
(Fehler `Stack too deep`). Da es für den DeFi-Korpus keine Ground Truth gibt,
lässt sich hier nur die Anzahl der Findings vergleichen. Ob die Findings
zutreffen, zeigen diese Zahlen nicht.

### 5.3 Kosten, Laufzeit und Robustheit

Je Contract auf `smartbugs-curated` kostete LLMSmartAudit $0,0171 bei 299,2 s
Rechenzeit, GPTScan $0,00007 bei 5,0 s und Slither nichts bei 2,1 s.
LLMSmartAudit war damit rund **250-mal so teuer** wie GPTScan ($2,44 gegenüber
$0,0098) und rund **140-mal so langsam** wie Slither (42 792,5 s gegenüber
298,8 s). Auf dem DeFi-Korpus kostete es je analysiertem Contract 49-mal so viel
wie GPTScan ($0,142 gegenüber $0,0029 bei 59 gegenüber 96 Contracts).

Alle LLM-Aufrufe der Arbeit summierten sich auf **rund 23 USD**:

| Posten | USD |
|---|---:|
| Smoke-Tests, beide Werkzeuge | ≈ 0,06 |
| GPTScan, curated-Hauptlauf | 0,0098 |
| LLMSmartAudit, curated-Hauptlauf | 2,44 (aus Token geschätzt) |
| GPTScan, unreparierter DeFi-Korpus | 0,046 |
| GPTScan, reparierter DeFi-Korpus | 0,2769 |
| GPTScan, Demonstrationslauf | 0,0725 |
| GPTScan, Läufe mit `MAIN` inkl. Vorläufe | 0,4087 |
| LLMSmartAudit, curated-Wiederholungslauf | ≈ 5,16 (geschätzt) |
| LLMSmartAudit, DeFi-Korpus mit Nachlauf | ≈ 8,37 (geschätzt) |
| Timeout-Nachweis | ≈ 0,05 |
| LLMSmartAudit, Kontextgrenze angehoben | 5,55 (abgebucht) |
| zwei abgebrochene Läufe | 0,62 (abgebucht) |
| **Summe** | **rund 23** |

Ohne Kompilat entfällt bei GPTScan die statische Prüfung. Außerdem konnte
GPTScans Parser in 87 der 143 curated-Tasks Teile des Solidity-0.4-Quelltexts
nicht verarbeiten und erfasste dort im Median nur ein Viertel der Funktionen.
Bei rund 6 640 API-Aufrufen trat kein Rate-Limit auf.

### 5.4 Reproduzierbarkeit

Beide LLM-Werkzeuge sind auch bei `temperature=0` nicht deterministisch:

| Werkzeug | Vergleich | Ergebnis |
|---|---|---|
| GPTScan | 27 Contracts, zwei Läufe auf dem unreparierten Korpus (ohne statische Stufe) | 20 von 27 (74 %) mit identischem Finding-Satz |
| GPTScan | 96 Contracts des reparierten Korpus, Lauf mit `MAIN` gegen Referenzlauf | 58 von 77 Findings reproduziert (75,3 %), überlagert vom Effekt von `MAIN` |
| LLMSmartAudit | 143 curated-Contracts, zwei vollständige Läufe | 805 gemeinsame (Contract, Detektor)-Paare, 291 nur im ersten, 216 nur im zweiten Lauf. Jaccard 61,4 % (141 Contracts mit Findings in beiden Läufen) bzw. 60,5 % (142 mit Findings in mindestens einem). Identischer Detektor-Satz bei 7 von 141 |
| Slither | 51 DeFi-Contracts, Upstream- gegen glibc-Image | identisch |
| Slither | beide Korpora, je unter Windows und Linux wiederholt | identisch bis auf `encode-packed-collision`, der bei einzelnen Contracts um ein Finding schwankt (ohne DASP-Klasse, Kennzahlen unberührt) |

Auf die Kennzahlen gegen die Ground Truth wirkte sich die Streuung kaum aus.
Der zweite LLMSmartAudit-Lauf erreichte 96 % Recall, 32 % Precision und 47 % F1
gegenüber 97 / 30 / 45 % im ersten. Im Aufwand unterschieden sich die Läufe
dagegen deutlich. Bei 6 126 gegenüber 6 174 Aufrufen erzeugte der zweite Lauf
11,2 Mio. statt 3,5 Mio. Completion-Token und benötigte 114 091,5 s statt
42 792,5 s Container-Zeit (bei drei statt vier parallelen Prozessen). Die
Ursache untersuchten wir nicht.

### 5.5 Integration, Timeout und `MAIN`

Alle Läufe dieser Arbeit führten wir über SmartBugs aus. Die Ergebnisse liegen
im Standardformat des Rahmenwerks vor und lassen sich mit dessen Werkzeugen neu
parsen und tabellieren. Den Timeout-Mechanismus wiesen wir an echten Containern
nach, sowohl gegen einen absichtlich langsamen lokalen Endpunkt als auch gegen
die DeepSeek-API. Ein ablaufender Lauf wurde in allen Fällen als behandelter
Fehler (`errors`) und nie als Abbruch (`fails`) verbucht. LLMSmartAudit sicherte
23 bzw. 24 von 41 Detektorphasen, und jedes Finding eines Teillaufs war auch im
Volllauf enthalten. Bei GPTScan enthielt das Teilergebnis im gemessenen Fall
keine Findings, weil die statische Bestätigung ohne die zugehörigen
LLM-Antworten nichts bestätigen konnte. Dabei entdeckten und korrigierten wir
einen Platzhalter, der nach Erreichen der Zeitgrenze bejahende Antworten
lieferte.

`MAIN` reduzierte im GPTScan-Volllauf 41 von 96 Dateien. Für LLMSmartAudit
half der Parameter bei den beiden geprüften Contracts nicht, die am
Kontextfenster gescheitert waren. Ihre geflatteten Dateien behielten 12 von 13
bzw. 19 von 19 Definitionen, weil der Hauptcontract fast alles transitiv
referenziert. Beide scheiterten deshalb erneut am Kontextfenster.

---

## 6. Diskussion

GPTScans Recall von 0 % auf `smartbugs-curated` ist leicht misszuverstehen.
Der Datensatz enthält keine DeFi-Logik, und genau darauf zielen die zehn Regeln
des Werkzeugs. Von 143 Contracts lösten nur 16 eine LLM-Anfrage aus, die
übrigen 127 verwarf der Vorfilter. Dass ihnen das passende Schlüsselwort
fehlte, ist allerdings nur für die 56 vollständig geparsten Tasks belegt. Auf
seiner Zieldomäne meldete dasselbe Werkzeug 77 statisch bestätigte Findings.
Der Vergleich von 0 % mit 97 % sagt daher wenig über GPTScan aus, weil der
Datensatz nicht zu seinem Einsatzzweck passt.

LLMSmartAudits Precision von 30 % ist als Untergrenze zu lesen, sein Recall von
97 % als Obergrenze. Für die Precision als Untergrenze sprechen drei Gründe:
Der Datensatz kennt nur ein Label je Datei, 468 der 1 124 Findings tragen keine
DASP-Klasse, und eine Stichprobe von 19 vermeintlich falschen Treffern ergab
15 plausible, 4 generische und keinen falschen Befund. Für den Recall als
Obergrenze spricht, dass ein Werkzeug, das im Mittel 7,9 Findings je Contract
meldet, die gelabelte Kategorie auf Contract-Ebene häufig auch zufällig trifft.
Die tatsächlichen Leistungen der drei Werkzeuge liegen daher näher beieinander,
als die Kennzahlen nahelegen. Die Metrik des Standard-Benchmarks begünstigt
Werkzeuge, die viel melden, und benachteiligt Werkzeuge, deren Befunde
außerhalb der Taxonomie liegen. Absolute Findingzahlen auf dem DeFi-Korpus
vergleichen wir bewusst nicht. LLMSmartAudit analysierte dort nur 59 der 96
Contracts und arbeitet mit 41 breiten Detektoren, GPTScan mit 10 engen Regeln.

Werkzeug- und Modelleigenschaften sind leicht zu verwechseln. Auf Werkzeug und
Umgebung gehen folgende Effekte zurück: Die Kontextgrenze war eine Konstante im
Code, die Grammatik-Ablehnungen kommen von GPTScans Parser, die Severity beider
LLM-Werkzeuge stammt aus der Taxonomie der Integration, und Slithers Ausfälle
lagen an der C-Bibliothek des Images. Auf das Modell gehen dagegen der
Nichtdeterminismus und der einseitige Rückgang der LLMSmartAudit-Findings
zwischen den beiden curated-Läufen zurück (etwa Integer Overflow von 73 auf 54
Contracts, Reentrancy von 70 auf 56). Dieser Rückgang deutet auf einen
Modellwechsel hinter demselben Namen hin. Die gemessene Übereinstimmung von
61,4 % ist deshalb keine Messung reiner Streuung. Wir lesen sie als Obergrenze
für die Stabilität.

Ob sich ein Teilergebnis retten lässt, hängt von der Architektur des Werkzeugs
ab. LLMSmartAudit sichert nach jeder Phase einen Zwischenstand. GPTScan führt
die Ergebnisse erst am Ende zusammen und muss seine Pipeline deshalb ohne neue
LLM-Aufrufe auslaufen lassen. Dieselbe Anforderung erforderte also zwei
verschiedene Lösungen. Der Ausfall von 38,5 % auf dem DeFi-Korpus zeigt
außerdem, dass die Auswertung „nicht analysiert“ und „nichts gefunden“ trennen
muss. Solange der Parser beides nicht unterschied, blieb der Ausfall
unsichtbar.

Beide LLM-Werkzeuge weisen dieselben Lücken auf: kein Timeout für den
Gesamtlauf, keine Kostenbremse (LLMSmartAudit), kein Offline-Modus, stilles
Scheitern statt Fehlermeldung, Severity als Katalogwert, keine Zeilennummern
und ein fest eingebautes Modell, das der Anbieter inzwischen abgeschaltet hat.
Ein Rahmenwerk, das solche Werkzeuge vergleichbar betreiben will, muss
API-Schlüssel, Netzzugang, Kosten, Laufzeitgrenzen und Nichtdeterminismus
explizit behandeln.

---

## 7. Erfahrungen aus der Durchführung

Den größten Aufwand verursachten Fehler, die keinen Absturz auslösten und die
Ergebnisse unbemerkt verfälschten. Dazu gehörten der nicht kompilierbare
Korpus, auf dem GPTScan scheinbar erfolgreich lief, der Parser, der
abgebrochene Tasks nicht von sauberen unterschied, die Kontextgrenze, die wir
zunächst dem Modell zuschrieben, und das unter Docker Desktop still
fehlschlagende Aufräumen. Seither prüft ein Parser-Audit jeden Lauf auf
verlorene Rohmeldungen.

Weitere Hindernisse betrafen Betrieb und Infrastruktur. Vor Einführung der
Schwärzung stand der API-Schlüssel in 62 lokalen Ergebnisdateien früherer
Läufe im Klartext (nie im Repository). Ein Volllauf scheiterte teilweise an
erschöpftem API-Guthaben, woraufhin wir Kostendeckel in den Runnern
einführten. Das Modell war ursprünglich im Image festgelegt, und der Anbieter
schaltete es ab. Jeder Modellwechsel erforderte damals einen Neubau des Images.
Heute sind Anbieter und Modell zur Laufzeit wählbar. Das LLMSmartAudit-Upstream
brachte ein Evaluationsverzeichnis mit 27 662 Dateien (3,7 GB) mit, das für die
Analyse nicht benötigt wird und das wir entfernten. Die Rohdaten eines Laufs,
der nur auf einem unserer Rechner lag, gingen verloren. Seither versionieren
wir die Ergebnisdateien jedes Tasks.

Rückblickend würden wir drei Dinge anders machen. Windows als Hauptplattform
bremste uns häufiger als erwartet (Pfadlängen, verlorene Ausführungsrechte,
Zeilenenden). Ein früher Gegentest unter Linux hätte viele dieser Probleme
sofort gezeigt. Ein lokaler Prüfstand, der einen LLM-Endpunkt nachbildet, hätte
von Beginn an kostenpflichtige Testläufe gegen die echte API ersetzen können.
Außerdem floss der größte Teil der Arbeitszeit in Integration, Fehlersuche und
Absicherung. Diesen Aufwand unterschätzten wir bei der Planung.

---

## 8. Grenzen der Aussagen

Die Precision-Werte sind Untergrenzen, da `smartbugs-curated` nur ein Label je
Datei vergibt und nur DASP-zugeordnete Findings gewertet werden (bei Slither
391 von 2 154, bei LLMSmartAudit 656 von 1 124). Zwei grenzwertige
Detektorzuordnungen von LLMSmartAudit verschieben dessen Precision um etwa
einen Prozentpunkt. Die Auswertung erfolgt auf Contract-Ebene, weil
LLMSmartAudit keine Zeilennummern liefert. Die Severity ist ein Katalogwert und
kein Urteil des Modells. Auf dem DeFi-Korpus fehlt eine
Ground Truth, dort beschreiben wir nur. Für GPTScan sind zwei Effekte nicht
ausgemessen: der nur teilweise geparste Quelltext in 87 curated-Tasks und die
80 auf dem DeFi-Korpus verworfenen Kandidaten. Die 77 Findings sind daher eine
Untergrenze.

Die Streuung beruht je LLM-Werkzeug auf nur zwei Läufen, die sich zudem in
Timeout, Prozesszahl und Parser-Stand unterscheiden. Konfidenzintervalle über
Läufe lassen sich daraus nicht ableiten. Alle Messungen nutzten ein einziges
Modell eines Anbieters. Der Timeout-Nachweis stützt sich auf je einen Contract
pro Werkzeug. Er zeigt, dass ein Teillauf keine Findings erfindet. Wie viele
Findings ein Teillauf im Mittel verpasst, zeigt er nicht. Die Rohdaten eines
Laufs, die Einzelurteile der qualitativen Stichproben und Abbuchungen für die
LLMSmartAudit-Volläufe liegen nicht vor. Neue Läufe sind nicht bitgleich
reproduzierbar. Sie benötigen Docker, lokal gebaute Images und einen
API-Schlüssel, verursachen Kosten und liefern aufgrund des Nichtdeterminismus
andere Findings.

---

## 9. Fazit und Ausblick

Alle vier Teilfragen lassen sich beantworten. LLM-Scanner sind als reguläre
SmartBugs-Werkzeuge betreibbar, sobald das Rahmenwerk Umgebungsvariablen
weiterreicht und schwärzt. Auf dem Standard-Benchmark führte LLMSmartAudit im
Recall, Slither in Precision und F1. Auf der Zieldomäne zeigte GPTScan, dass
seine 0 % auf `smartbugs-curated` am Datensatz liegen. LLMSmartAudit
analysierte dort erst nach Anhebung einer werkzeuginternen Grenze alle
Contracts. Im Betrieb lagen zwischen den Kosten der beiden LLM-Werkzeuge mehr
als zwei Größenordnungen. Ihre Ergebnisse streuen von Lauf zu Lauf erheblich,
die Kennzahlen gegen die Ground Truth ändern sich dadurch aber kaum.

Slither bleibt für syntaktisch erkennbare Schwachstellen das präziseste
Werkzeug. GPTScan deckt zehn DeFi-Szenarien eng und kostengünstig ab.
LLMSmartAudit findet auf kleinen Contracts nahezu alle gelabelten
Schwachstellen, ist aber teuer und liefert keine Zeilennummern. Seine Precision
lässt sich mit der vorhandenen Ground Truth nur nach unten abschätzen.

Für weitere Arbeiten sehen wir mehrere Ansatzpunkte. Ein Vergleich mit den
Originalwerkzeugen außerhalb von SmartBugs würde belegen, dass die Integration
ihr Verhalten nicht verändert. Wiederholungsmessungen über mehr als zwei Läufe
würden die Streuung genauer bestimmen. Ein stärkeres Modell lässt sich ohne
Codeänderung einsetzen. Aus den Audit-Reports der zugrunde liegenden
Wettbewerbe ließe sich eine Ground Truth für den DeFi-Korpus ableiten. Offen ist
außerdem, ob GPTScan und Slither gemeinsam LLMSmartAudit ersetzen können.
Schließlich sollten die 80 verworfenen GPTScan-Kandidaten manuell durchgesehen
werden.

---

## 10. Reproduktion

Voraussetzungen sind Windows 11 mit PowerShell, Docker Desktop sowie Python
3.10+ für SmartBugs und 3.11+ für Auswertung und Tests. Die Images der beiden
LLM-Werkzeuge und, für den DeFi-Korpus, das glibc-Image für Slither müssen
lokal gebaut werden.

Die Kennzahlen lassen sich ohne Docker, API-Schlüssel und Kosten aus den
versionierten Auswertungen nachrechnen. Die Testsuite prüft dabei zusätzlich
die Tabellen der Dokumentation:

```powershell
python analysis_tools\metrics_from_eval.py eval\curated_v1_20260705__llmsmartaudit --check
python -m pytest tests -q
```

Ein neuer Lauf beginnt am besten mit einem kostenfreien Trockenlauf:

```powershell
.\run_curated.ps1 -Tool gptscan -GptscanDry -SkipClone -FilePattern 'samples:gptscan/Vault.sol'
.\run_curated.ps1        # Volllauf: beide LLM-Werkzeuge, 143 curated-Contracts
```

Für LLMSmartAudit muss `LLM_MODEL=deepseek-v4-flash` gesetzt sein. Das
Werkzeug besitzt keine eigene Kostenbremse. Ein curated-Volllauf dauerte bei
vier parallelen Prozessen gut drei Stunden.

---

## Eigenanteil und Lizenz

Eigener Code sind die Auswertungs-, Korpus- und Testwerkzeuge, die Runner, die
beiden SmartBugs-Integrationen, die Konfiguration des glibc-Slither-Images
sowie einzelne neue Dateien in den Werkzeugen (u. a. Modellanbindung,
Report-Sammler, Dockerfiles). Wir veränderten zwei Dateien von SmartBugs,
sieben von GPTScan und neun von LLMSmartAudit. Unverändert übernommen sind 516
Dateien von SmartBugs, 38 von GPTScan und 212 von LLMSmartAudit sowie die 241
fremden Contract-Dateien der Korpora. Jede Änderung ist per Datei-Hash gegen
den Upstream belegt. Der Eigenanteil steht unter MIT. Änderungen an GPTScan
bleiben AGPL-3.0, weshalb wir die daraus gebauten Images nicht veröffentlichen.
LLMSmartAudit (Apache-2.0) und SmartBugs sind permissiv lizenziert.

---

## Literatur

- M. di Angelo, T. Durieux, J. F. Ferreira, G. Salzer: SmartBugs 2.0: An
  Execution Framework for Weakness Detection in Ethereum Smart Contracts. In:
  Proceedings of the 38th IEEE/ACM International Conference on Automated
  Software Engineering (ASE 2023), S. 2102–2105, 2023.
- Y. Sun, D. Wu, Y. Xue, H. Liu, H. Wang, Z. Xu, X. Xie, Y. Liu: GPTScan:
  Detecting Logic Vulnerabilities in Smart Contracts by Combining GPT with
  Program Analysis. In: Proceedings of the 46th IEEE/ACM International
  Conference on Software Engineering (ICSE 2024), 2024.
  https://doi.org/10.1145/3597503.3639117
- Z. Wei, J. Sun, Z. Zhang, X. Zhang: LLM-SmartAudit: Advanced Smart Contract
  Vulnerability Detection. arXiv:2410.09381, 2024.

---

## Weiterführende Dokumentation

| Dokument | Inhalt |
|---|---|
| [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md) | Architektur der drei Werkzeuge, Detailergebnisse, Fehlerbilder |
| [`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md) | Recall, Precision und F1 je Kategorie mit Basisrate und Intervall |
| [`../eval/LAUFREGISTER.md`](../eval/LAUFREGISTER.md) | alle Laufverzeichnisse, je Lauf eine `README.md` unter [`../eval/`](../eval/README.md) |
| [`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md) | GPTScan auf curated und auf seiner Zieldomäne |
| [`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md) | Rekonstruktion des DeFi-Korpus |
| [`../smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md), [`../GPTScan/taxonomy/mapping.md`](../GPTScan/taxonomy/mapping.md) | Begründung der DASP-Zuordnungen |
| [`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md) | Semantik von `errors` und `fails` |
| [`BA-PARSER-AUDIT-LUECKEN.md`](BA-PARSER-AUDIT-LUECKEN.md), [`parser-fix-vorher-nachher.md`](parser-fix-vorher-nachher.md) | Parser-Audit und -Reparatur |
| [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md) | Ablauf der Messungen, Fehler und Nachträge |
| [`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md), [`BA-WERKZEUGKETTE.md`](BA-WERKZEUGKETTE.md) | Timeout-Mechanismus und Werkzeugkette |
| [`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), [`../LICENSE`](../LICENSE) | Eigen- und Fremdanteil, Lizenzen |
| [`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md) | Arbeitspakete und Stand |
| [`../README.md`](../README.md), [`BA-BETRIEB.md`](BA-BETRIEB.md), [`BA-WERKZEUG-BEDIENUNG.md`](BA-WERKZEUG-BEDIENUNG.md) | Einrichtung, Betrieb, Kosten, Fallstricke |
| [`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md), [`BA-VERIFIKATIONSBERICHT.md`](BA-VERIFIKATIONSBERICHT.md) | Prüfung der Zahlen und Dokumente |
| [`BA-TESTLAUF-AUSWERTUNG.md`](BA-TESTLAUF-AUSWERTUNG.md), [`BA-DEMOLAUF-ERGEBNIS.md`](BA-DEMOLAUF-ERGEBNIS.md), [`BA-AUFGABEN-UND-STATUS.md`](BA-AUFGABEN-UND-STATUS.md), [`BA-ARBEITSBERICHT-20260802.md`](BA-ARBEITSBERICHT-20260802.md), [`Update_Bericht.md`](Update_Bericht.md) | datierte Zwischenstände |
