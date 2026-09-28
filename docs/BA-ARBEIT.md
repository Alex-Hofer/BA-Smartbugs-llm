# KI-gestützte Smart-Contract-Scanner im SmartBugs-Framework

Bachelorarbeit von Alex Hofer und Alex Unterleitner, TU Wien, Betreuer Gernot
Salzer. Beide Verfasser haben zu gleichen Teilen beigetragen; eine Aufteilung
nach Personen wird nicht ausgewiesen. **Dieses Repository ist die Abgabe.**
Eine gesonderte schriftliche Ausarbeitung gibt es nicht.

Dieses Dokument erzählt die Arbeit in einem Stück: Motivation, Fragestellung,
Vorgehen, Ergebnisse, Diskussion, Grenzen, Fazit. Es ersetzt kein
Detaildokument, sondern führt am Ende in der richtigen Reihenfolge dorthin.
Jede Zahl trägt ihre Quelle: die versionierten Auswertungen unter `eval/`
(`run_meta.json`, `findings.jsonl`, die Tabellen unter `eval/per_contract/`)
oder das Dokument, das bei ihr genannt ist. Verweise sind relativ zu `docs/`.
Stand: 25.09.2026, nach den letzten Messläufen vom 24.09.2026.

---

## 0. Kurzfassung

Zwei LLM-gestützte Analysewerkzeuge für Solidity-Contracts, GPTScan und
LLMSmartAudit, wurden als reguläre Werkzeuge in das Rahmenwerk SmartBugs 2.1.1
eingebunden und gegen den statischen Analysator Slither 0.11.3 gemessen: auf
`smartbugs-curated` (143 gelabelte Contracts, Ground Truth nach DASP-Top-10)
und auf einem in dieser Arbeit rekonstruierten Korpus von 96 realen
DeFi-Contracts ohne Ground Truth. Gefragt war, ob sich solche Werkzeuge unter
SmartBugs betreiben lassen und was dem Rahmenwerk dafür fehlt, wie sie gegen
die statische Referenz abschneiden, was sie auf ihrer Zieldomäne liefern und
was sie an Geld, Zeit und Stabilität kosten.

Die Integration gelingt; SmartBugs fehlten die Weitergabe von
Umgebungsvariablen in den Container, deren Redaktion im Ergebnis und ein
robustes Aufräumen unter Windows (sieben markierte Eingriffe, als zwei Pull
Requests vorbereitet). Auf `smartbugs-curated` erreicht LLMSmartAudit 97 %
Recall bei 30 % Precision (F1 45 %), Slither 67 % bei 45 % (F1 54 %), GPTScan
0 %, weil der Datensatz die DeFi-Logik nicht enthält, für die seine zehn Regeln
gebaut sind (Vorbehalte in Abschnitt 6). Auf den DeFi-Contracts meldet GPTScan
77 Findings auf 40 Contracts für 28 Cent; LLMSmartAudit scheiterte auf 37 von
96 an einer Kontextgrenze, die sich als Konstante im Werkzeug erwies; Slither
meldet 7 096 überwiegend stilistische Findings. Nach den aus Token gerechneten
Kosten ist LLMSmartAudit rund 250-mal so teuer wie GPTScan, und es ist rund
140-mal so langsam wie Slither; beide LLM-Werkzeuge sind nicht deterministisch.

Fazit: LLM-gestützte Scanner lassen sich in SmartBugs betreiben, wenn der
Rahmen Schlüssel, Netz, Kosten, Timeout und Nichtdeterminismus behandelt.
Slither bleibt für syntaktisch Erkennbares das präziseste Werkzeug. GPTScan
deckt eng und billig zehn DeFi-Szenarien ab. LLMSmartAudit findet auf kleinen
Contracts fast alles Gelabelte, aber teuer, ohne Zeilennummern und mit einer
Precision, die die Ground Truth nur nach unten abschätzt.

---

## 1. Motivation und Kontext

Statische Analysatoren wie Slither finden Schwachstellen in Smart Contracts an
Code-Mustern: einen externen Aufruf vor der Zustandsänderung, einen
ungeprüften Rückgabewert, einen Zeitstempel als Zufallsquelle. Was sie nicht
finden können, sind Fehler in der Absicht eines Contracts, etwa einen
Liquidity-Pool, der den Wert eines Tokens aus einem im selben Block
manipulierbaren Spotpreis ableitet. Der Code ist dann syntaktisch fehlerfrei
und tut, was dort steht; ausnutzbar ist das ökonomische Modell dahinter
([`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md), Abschnitt 5).

Zwei jüngere Werkzeuge setzen dafür große Sprachmodelle ein, mit verschiedenem
Ansatz. GPTScan koppelt ein LLM mit leichter Programmanalyse und sucht zehn
DeFi-Logik-Szenarien, die es anschließend statisch am kompilierten Contract
bestätigt. LLMSmartAudit lässt mehrere LLM-Rollen den Quelltext gegen einen
Katalog von Detektor-Prompts prüfen und kompiliert nie. Beide sind als
Forschungsprototypen veröffentlicht ([`../GPTScan/README.md`](../GPTScan/README.md),
[`../LLMSmartAuditTool-main/LLMSmartAuditTool-main/README.md`](../LLMSmartAuditTool-main/LLMSmartAuditTool-main/README.md)).

Ein Vergleich gegen statische Analyse ist die Voraussetzung dafür, den Nutzen
der LLM-Werkzeuge einzuordnen: Slither ist (bis auf einen Detektor, Abschnitt
5.4) deterministisch, kostenlos, läuft in
Sekunden und ist die etablierte Referenz für die klassischen
Schwachstellenklassen. Erst neben ihm wird sichtbar, was ein LLM zusätzlich
findet, was es an Geld und Zeit kostet und was es an Reproduzierbarkeit
aufgibt ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
Abschnitt 3).

SmartBugs ist das Rahmenwerk, das genau solche Vergleiche ermöglicht: eine
einheitliche Kommandozeile für 25 Analysewerkzeuge, je Contract ein
Docker-Container, automatische Bereitstellung des passenden Compilers, Timeout,
Parser je Werkzeug, standardisiertes Ergebnisformat und SARIF-Ausgabe
([`../smartbugs/README.md`](../smartbugs/README.md)). Es stammt aus der
Arbeitsgruppe des Betreuers. Ein LLM-gestütztes Werkzeug enthielt es nicht,
und ein solches Werkzeug braucht Dinge, die SmartBugs nicht vorsah: einen
API-Schlüssel zur Laufzeit, Netzzugang aus dem Container, eine Modellwahl, und
es kostet Geld pro Aufruf und liefert bei Wiederholung nicht dasselbe
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Abschnitte 2.1 und 2.5). Was es
heißt, zwei solche Werkzeuge trotzdem als reguläre SmartBugs-Werkzeuge zu
betreiben und zu vergleichen, ist der Gegenstand dieser Arbeit.

---

## 2. Forschungsfrage

Die Fragestellung wurde vor der Durchführung nicht schriftlich festgehalten;
kein Dokument aus der Durchführungszeit formuliert sie ausdrücklich. Die
Arbeitspakete des Betreuergesprächs
([`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md)) und
das Vorgehen im Durchführungsprotokoll
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Abschnitt 1)
legen fest, was getan wurde. Die folgende Formulierung leitet die Frage aus
dem ab, was tatsächlich gemessen wurde; die Verfasser haben sie am 25.09.2026
als ihre Fragestellung bestätigt.

**Was leisten LLM-gestützte Schwachstellenscanner für Smart Contracts, wenn
man sie als reguläre Werkzeuge unter SmartBugs betreibt, gemessen an einem
klassischen statischen Analysator?** Im Einzelnen:

1. **Integration.** Lassen sich GPTScan und LLMSmartAudit so in SmartBugs
   einbinden, dass sie sich wie jedes andere Werkzeug aufrufen, auswerten und
   vergleichen lassen, und was fehlt SmartBugs dafür?
2. **Erkennungsleistung auf dem Standard-Benchmark.** Wie schneiden beide auf
   `smartbugs-curated` ab, je DASP-Kategorie in Recall und Precision auf
   Contract-Ebene, verglichen mit Slither 0.11.3?
3. **Verhalten auf der Zieldomäne.** Was liefern beide auf realen
   DeFi-Contracts, für die GPTScan gebaut ist und für die es keine Ground
   Truth gibt, und wie verhält sich Slither dort?
4. **Betrieb.** Was kosten sie an Geld und Zeit, wie robust laufen sie durch,
   und wie stabil sind ihre Ergebnisse von Lauf zu Lauf?

**Abgrenzung.** Ausdrücklich nicht untersucht werden: ob die Integration die
Werkzeuge gegenüber ihrem Originalzustand verändert (Integrationstreue,
Arbeitspaket AP2); eine systematische Wiederholungsmessung über mehr als zwei
Läufe (AP4); ob ein Verbund aus GPTScan und Slither mehr findet als
LLMSmartAudit allein; andere Modelle oder Anbieter als DeepSeek
`deepseek-v4-flash`; eine zeilengenaue Auswertung; eine Ground Truth für den
DeFi-Korpus; severity-gewichtete Kennzahlen; und ein verallgemeinerndes
Dokument mit Anforderungen an LLM-Analysewerkzeuge (AP7). Die
Arbeitspakete AP2, AP4 und AP7 sind im Betreuerdokument als offen geführt
([`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md),
Abschnitt 1; [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
„Was dieser Vergleich nicht zeigt“).

---

## 3. Ausgangslage

**GPTScan** beschreibt sich als Werkzeug, das ChatGPT zur Erkennung von
Logik-Schwachstellen einsetzt; die zugehörige Veröffentlichung ist Sun et al.,
„GPTScan: Detecting Logic Vulnerabilities in Smart Contracts by Combining GPT
with Program Analysis“, ICSE 2024. Es wurde vom Upstream auf den Datensätzen
Web3Bugs, DefiHacks und Top200 evaluiert und steht unter AGPL-3.0
([`../GPTScan/README.md`](../GPTScan/README.md)). Das Werkzeug bringt genau
zehn Regeln mit, `MWE-200` bis `MWE-209`, jede als Szenario plus statische
Bestätigungsprüfung formuliert; acht davon haben in den Registern SWC und DASP
kein Gegenstück ([`../GPTScan/taxonomy/mapping.md`](../GPTScan/taxonomy/mapping.md)).
Unter SmartBugs läuft es mit `network: bridge` und einem lokal gebauten Image
([`../smartbugs/tools/gptscan/config.yaml`](../smartbugs/tools/gptscan/config.yaml)).

**LLMSmartAudit** ist eine Multi-Agenten-Pipeline auf ChatDev/CAMEL: Rollen wie
Security Analyst und Solidity Programming Expert führen ein geführtes Gespräch
über den Quelltext, in zwei Modi namens `SmartContractBA` und
`SmartContractTA`; die Veröffentlichung ist Wei et
al., „LLM-SmartAudit: Advanced Smart Contract Vulnerability Detection“, arXiv
2410.09381, Lizenz Apache-2.0 ([`../LLMSmartAuditTool-main/LLMSmartAuditTool-main/README.md`](../LLMSmartAuditTool-main/LLMSmartAuditTool-main/README.md)).
Diese Arbeit verwendet den Modus `SmartContractTA` mit 41 Detektor-Prompts;
die Upstream-README listet 40 davon, die Konfiguration des Werkzeugs und die
`findings.yaml` der Integration führen 41
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Abschnitt 2;
[`../smartbugs/tools/llmsmartaudit/config.yaml`](../smartbugs/tools/llmsmartaudit/config.yaml)).

**Slither 0.11.3** ist ein statischer Analysator für Solidity in Python, der
den Contract kompiliert, eine Zwischendarstellung baut und darauf eine Reihe
von Detektoren laufen lässt ([`../smartbugs/tools/slither-0.11.3/config.yaml`](../smartbugs/tools/slither-0.11.3/config.yaml));
die `findings.yaml` der SmartBugs-Integration kennt 102 Finding-Namen. Es ist
Teil der SmartBugs-Auslieferung, sein Image kommt von Docker Hub, es läuft
ohne Netz und wurde in dieser Arbeit nicht verändert
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Abschnitt 3).

**SmartBugs** ist eine erweiterbare Plattform mit einheitlicher Schnittstelle
zu Werkzeugen, die Ethereum-Programme auf Schwachstellen prüfen, beschrieben
in di Angelo, Durieux, Ferreira, Salzer, „SmartBugs 2.0: An Execution Framework
for Weakness Detection in Ethereum Smart Contracts“, ASE 2023. Ein neues
Werkzeug braucht ein Docker-Image, wenige Zeilen Konfiguration und ein kleines
Parser-Skript ([`../smartbugs/README.md`](../smartbugs/README.md)). Verwendet
wird Version 2.1.1 auf dem Upstream-Commit `7ddaf6c`, unter `smartbugs/`
mitgeführt; warum genau dieser Stand und nicht der Tag `v2.1.1`, steht in
[`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Kopf.

**smartbugs-curated** ist der zu SmartBugs gehörende Datensatz verwundbarer
Solidity-Contracts, geordnet nach der DASP-Taxonomie, mit annotierten
Schwachstellenzeilen je Datei; eine frühere Fassung diente der Studie von neun
Analysewerkzeugen auf der ICSE 2020
([Upstream-README](https://github.com/smartbugs/smartbugs-curated)). Verwendet
wird der Stand `230e649` vom 16.06.2024 mit 143 Dateien; `vulnerabilities.json`
labelt je Datei eine Primärschwachstelle. Der Datensatz liegt nicht im
Repository, `run_curated.ps1` klont und pinnt ihn
([`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md),
Kopf; [`../README.md`](../README.md)).

**DASP-Top-10 und SWC** sind zwei Klassifikationsschemata für
Smart-Contract-Schwachstellen (dasp.co, swcregistry.io; beide in
[`../GPTScan/taxonomy/mapping.md`](../GPTScan/taxonomy/mapping.md) genannt).
`smartbugs-curated` labelt nach DASP; die `findings.yaml` jedes Werkzeugs
ordnet jedem Finding-Namen eine SWC- und, wo möglich, eine DASP-Klasse zu.
Nur DASP-zugeordnete Findings gehen in Recall und Precision ein.

---

## 4. Vorgehen

### 4.1 Aufbau

SmartBugs ist der Rahmen, die Werkzeuge sind Container. Je Werkzeug gibt es
ein Verzeichnis nach dem SmartBugs-Schema (`smartbugs/tools/gptscan/`,
`smartbugs/tools/llmsmartaudit/`): `config.yaml` (Image, Netz, Entrypoint,
Allowlist der Umgebungsvariablen), `findings.yaml` (Zuordnung jedes
Finding-Namens zu SWC/DASP und Severity), `parser.py` (Rohausgabe zu
`findings`, `infos`, `errors`, `fails`) und `scripts/do_solidity.sh` als
Entrypoint im Container. Dazu je ein eigenes Docker-Image; das
LLMSmartAudit-Image wurde von 5,13 GB auf 587 MB verkleinert, indem das für
die Analyse nicht gebrauchte Evaluationsverzeichnis des Upstreams entfällt
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Abschnitte 1 und 2.4).

LLM-Backend aller aufgezeichneten Läufe ist DeepSeek mit dem Modell
`deepseek-v4-flash`, aus Kostengründen gewählt; Anbieter und Modell sind zur
Laufzeit über Umgebungsvariablen wählbar, nichts steckt im Image
([`../README.md`](../README.md), „Modell wählen und wechseln“).

Was SmartBugs dafür fehlte und ergänzt wurde: ein Feld `env:` in der
Werkzeugkonfiguration, über das nur benannte, auf dem Host gesetzte
Umgebungsvariablen in den Container gelangen, und die Redaktion dieser Werte,
bevor SmartBugs die Container-Argumente in `smartbugs.json` schreibt. Ohne
beides müsste der API-Schlüssel ins Image oder stünde im Klartext in jedem
Ergebnisordner. Dazu ein Aufräumen der Task-Verzeichnisse mit Wiederholung,
weil unter Docker Desktop auf Windows sonst Ergebnisse lautlos verloren
gingen. Das sind sieben Blöcke in `sb/docker.py` und `sb/tools.py`, im
Quelltext als `BA MODIFICATION` markiert; alle übrigen Dateien unter
`smartbugs/sb/` sind byteidentisch zum Upstream
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Abschnitt 2.1).

### 4.2 Zwei Datensätze, und warum zwei

| | `smartbugs-curated` | `mwevariety_fixed` |
|---|---|---|
| Umfang | 143 Dateien | 96 Contracts |
| Herkunft | [smartbugs/smartbugs-curated](https://github.com/smartbugs/smartbugs-curated), Commit `230e649` | Web3Bugs, eine Sammlung realer DeFi-Contracts aus Audit-Wettbewerben, die das GPTScan-Paper als Benchmark verwendet; 96 Dateien aus 49 Wettbewerben, in dieser Arbeit rekonstruiert ([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md), Abschnitt 3) |
| Ground Truth | ja, eine Primärschwachstelle je Datei aus den DASP-Top-10 | nein |
| Was sich messen lässt | Recall, Precision, F1 je Kategorie | nur beschreiben: Findings, Abdeckung, Kosten, Ausfälle |
| Solidity | 0.4 (142 Dateien), 0.5 (eine) | 0.6 (18), 0.7 (8), 0.8 (70), geflattet mit vollständigem Import-Closure |
| Im Repository | nein, wird geklont | ja, `smartbugs/samples/gptscan/mwevariety_fixed/` |

Auf dem ersten Korpus wird gemessen, auf dem zweiten beschrieben. Ohne den
zweiten wäre GPTScan nur auf einem Datensatz gemessen, der seine Domäne nicht
enthält; ohne den ersten gäbe es keine Zahl gegen eine Ground Truth. Der zweite
Korpus musste erst brauchbar gemacht werden: Im ursprünglichen Zustand
kompilierte 1 von 96 Dateien, GPTScans statische Bestätigungsstufe war damit
inaktiv und das Werkzeug auf einen reinen Prompt-Scanner reduziert. Die
Rekonstruktion aus den Originalquellen ordnet jede Datei ihrem Original per
Byte-Abgleich zu (33 Dateien identisch, 50 als exakter Präfix eines
abgeschnittenen Originals, 13 über den gemeinsamen Dateikopf), bettet 1 279
Abhängigkeiten ein und bringt alle 96 nativ mit `solc` zum Übersetzen; in
GPTScans eigener Werkzeugkette scheitert `58_UniV3Vault.sol` weiterhin am
Compilat und wird im Ergebnis als degradiert geführt
([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md), Abschnitte 4 und 7;
Werkzeuge in [`../corpus_tools/README.md`](../corpus_tools/README.md)).

Zwei Eigenheiten des ersten Korpus prägen die Zahlen: Er labelt je Datei genau
eine Schwachstelle, ein zutreffender Zweitbefund zählt als False Positive. Und
er führt dieselbe Datei `0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol`
unter zwei Kategorien, weshalb 143 Dateien nicht 143 Contracts sind
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Abschnitt 5,
Punkt 6).

### 4.3 Messläufe

Jeder Lauf hat eine `runid`; SmartBugs legt je Contract ein Task-Verzeichnis
mit `smartbugs.json` (Aufrufparameter), `result.json` (geparste Ergebnisse),
`result.log` und `result.tar` an. Alle Läufe wurden über die vier
PowerShell-Runner gestartet, sequenziell je Werkzeug, mit zwei bis vier
parallelen Containern und einem Timeout je Task von 600 s (Slither), 1 800 s
(GPTScan) und 3 600 bis 7 200 s (LLMSmartAudit, je nach Lauf). LLMSmartAudit
hat keine eigene Kostenbremse, deshalb setzen die Runner einen Kostendeckel
([`BA-BETRIEB.md`](BA-BETRIEB.md), Abschnitte 2 und 3; die Parameter jedes
Laufs stehen im Block `invocation` seiner `run_meta.json`). Die Läufe, die in
die Ergebnisse eingehen:

| `runid` | Werkzeug(e) | Korpus | Datum | Tasks | Modell |
|---|---|---|---|---:|---|
| `curated_v1_20260705` | GPTScan, LLMSmartAudit, Slither | curated | 05./06.07.2026 | 3 × 143 | `deepseek-v4-flash` |
| `curated_mwefixed_live` | GPTScan | mwevariety_fixed | 21.07.2026 | 96 | `deepseek-v4-flash` |
| `gptscan_mwefixed_v2_main` (+ `_nomain`) | GPTScan mit `MAIN` | mwevariety_fixed | 15.08.2026 | 96 + 3 | `deepseek-v4-flash` |
| `llmsa_curated_v2` | LLMSmartAudit | curated | 15./16.08.2026 | 143 | `deepseek-v4-flash` |
| `llmsa_mwefixed_v2` (+ `_retry`: vier Tasks, die im Hauptlauf am erschöpften API-Guthaben gescheitert waren) | LLMSmartAudit | mwevariety_fixed | 16.08. und 15.09.2026 | 96 + 4 | `deepseek-v4-flash` |
| `slither_mwefixed_v1`, `_v2` | Slither, Upstream- und glibc-Image | mwevariety_fixed | 24.09.2026 | 2 × 96 | – |
| `llmsa_mwefixed_v2_ctx1m` | LLMSmartAudit, Kontextgrenze 1 Mio. Token | die 37 Kontext-Contracts | 24.09.2026 | 37 | `deepseek-v4-flash` (der Anbieter bedient den Namen seit September 2026 mit DeepSeek-V4.1-Flash) |

Insgesamt liegen 50 Laufverzeichnisse mit 1 501 Tasks vor (51 `runid`-Werte,
weil ein Verzeichnis zwei enthält), darunter Vorphasen-, Trocken-, Stichproben-,
Demonstrations- und Timeout-Nachweisläufe; welches Verzeichnis wozu diente und
wo es ausgewertet ist, steht in [`../eval/LAUFREGISTER.md`](../eval/LAUFREGISTER.md).
Von den Rohergebnissen sind je Task `result.json` und `smartbugs.json`
versioniert; Logs und Archive liegen als Zip an einem GitHub-Release des
Repositorys ([`../README.md`](../README.md), „Wo die Ergebnisse liegen“). Ein
Lauf ist nur noch als abgeleitete Auswertung vorhanden: `llmsa_curated_v2`
wurde auf dem Rechner des Co-Autors gefahren, seine Rohdaten existieren seit
dem 24.09.2026 nicht mehr ([`../eval/llmsa_curated_v2/README.md`](../eval/llmsa_curated_v2/README.md)).

### 4.4 Auswertung

**Contract-Level, je DASP-Kategorie.** Ein gelabelter Contract gilt als
erkannt, wenn das Werkzeug mindestens ein Finding meldet, dessen
DASP-Klassifikation auf die gelabelte Kategorie abbildet. Recall ist der Anteil
erkannter Contracts je Kategorie; Precision der Anteil der Contracts, die das
Werkzeug mit dieser Kategorie geflaggt hat und die tatsächlich so gelabelt
sind. Die Klassifikation kommt aus der `findings.yaml` des Werkzeugs; für
Slither kommen fünf dokumentierte Zusatzzuordnungen hinzu (`timestamp`,
`weak-prng`, drei `unchecked-*`-Detektoren), die letzten drei seit dem
20.09.2026 ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Nachtrag 4.6). Die Regel dafür: ergänzt wurden nur Slither-Detektoren, die in
der `findings.yaml` des SmartBugs-Upstreams keine Klassifikation tragen,
obwohl ihr Name eine SWC-Klasse benennt; die Taxonomien der beiden
LLM-Werkzeuge wurden nicht nachgebessert, ihre Zuordnungen sind je Detektor
begründet, und zwei Grenzfälle sind ausgewiesen, ohne sie zu ändern
([`../smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md)).
Zu jeder Precision steht die Basisrate, also die Precision eines
Werkzeugs, das die Kategorie auf jedem Contract meldet; zu jedem Recall ein
95-%-Wilson-Intervall. Zwei Skripte rechnen dasselbe, `evaluate_curated.py`
auf der Konsole und `analysis_tools/curated_eval.py` in die versionierten
Ordner; ein drittes, `analysis_tools/metrics_from_eval.py`, rechnet die
Kennzahlen allein aus den versionierten Dateien nach
([`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md);
[`../analysis_tools/README.md`](../analysis_tools/README.md)).

**Was aus der Wertung fällt, und warum.** Findings ohne DASP-Nummer gehen
nicht in Recall und Precision ein: bei GPTScan auf curated keines von 6, bei
LLMSmartAudit 468 von 1 124, bei Slither 1 763 von 2 154. Sie sind nicht
belanglos, sondern nur nicht gegen eine DASP-Ground-Truth messbar. Die
Zuordnung der 41 LLMSmartAudit-Detektoren ist je Detektor am Prompt begründet,
mit zwei ausgewiesenen Grenzfällen ([`../smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md)).
Ebenso fällt heraus, was kein Ergebnis ist: Die Auswertung unterscheidet die
Zustände `findings`, `clean`, `degraded` (GPTScan ohne Compilat, Ergebnis
unbestimmt), `context_exceeded` (LLMSmartAudit am Kontextfenster abgebrochen,
Contract nie analysiert) und `failed`; `errors` und `fails` sind aus dem
SmartBugs-Code hergeleitet ([`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md)).
Ein Parser-Audit prüft für jeden Lauf, dass keine Rohmeldung im Parser
verlorengeht ([`parser-audit-nachher.md`](parser-audit-nachher.md)).

**Qualitative Stichproben** am Quellcode ergänzen die Zahlen dort, wo die
Ground Truth nicht trägt; ihre Einzelurteile wurden nicht archiviert, nur die
Summen ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Abschnitte 4.2 und 4.3).

### 4.5 Eigene Beiträge

- **Integration** beider Scanner in SmartBugs: Konfiguration, Taxonomie,
  Parser, Entrypoints, Docker-Images, Modell- und Anbieterwahl zur Laufzeit,
  dazu die sieben Eingriffe in SmartBugs selbst und ein eigenes
  glibc-Werkzeugverzeichnis für Slither auf dem DeFi-Korpus
  ([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)).
- **Parser und Parser-Audit.** Im Ausgangszustand meldete GPTScan
  Compile-Fehler nur im Log; `result.json` zeigte `errors=[]` und war von
  „sauber“ nicht zu unterscheiden. Ein Audit über die damals 930 Tasks fand
  1 368 von 1 464 Rohmeldungen (Fehler-, Warn- und Traceback-Zeilen der
  Werkzeuge im `result.log`) im Parser-Output nicht wieder; nach der
  Reparatur vom 02.08.2026 sind es 0 von heute 2 555
  ([`parser-audit-vorher.md`](parser-audit-vorher.md),
  [`parser-audit-nachher.md`](parser-audit-nachher.md),
  [`parser-fix-vorher-nachher.md`](parser-fix-vorher-nachher.md)); ein zweiter
  Defekt im Zusammenspiel mit LLMSmartAudit ist in
  [`BA-PARSER-AUDIT-LUECKEN.md`](BA-PARSER-AUDIT-LUECKEN.md) beschrieben.
- **Korpus-Reparatur** des DeFi-Korpus (Abschnitt 4.2).
- **Timeout ins Werkzeug durchreichen (AP5).** SmartBugs' `--timeout` wirkte
  für beide Werkzeuge nur als harter Containerabbruch. Seit dem 18.08.2026
  rechnet der Entrypoint aus dem Timeout drei Marken: bei 70 % setzt GPTScan
  keine neuen LLM-Aufrufe mehr ab und lässt seine Pipeline zu Ende laufen, bei
  90 % beendet ein `timeout`-Kommando als Sicherheitsnetz den Werkzeugprozess,
  und der Entrypoint birgt den Zwischenstand, den LLMSmartAudit nach jeder
  Detektorphase schreibt; beide Wege tragen den Marker `sb_timeout`
  ([`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md)).
- **`MAIN`-Parameter (AP6).** Keines der Werkzeuge kennt eine Contract-Auswahl;
  bei `MAIN=1` reduziert `main_contract.py` die Datei auf den Contract, nach
  dem sie benannt ist ([`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md), AP6).
- **Auswertungsskripte** unter `analysis_tools/`, `evaluate_curated.py`, die
  Runner, ein lokaler LLM-Prüfstand für kostenlose Tests und 276
  Regressionstests, die ohne Docker und Schlüssel gegen aufgezeichnete Rohdaten
  laufen und bei jedem Push ausgeführt werden; insgesamt 15 907 Zeilen eigener
  Code ([`../tests/README.md`](../tests/README.md);
  [`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md),
  Abschnitt 4.1).

---

## 5. Ergebnisse

### 5.1 `smartbugs-curated`, 143 Contracts, Lauf `curated_v1_20260705`

Quelle: `eval/curated_v1_20260705__<werkzeug>/run_meta.json`; je Kategorie mit
Basisrate und Intervall in
[`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md).

| | GPTScan | LLMSmartAudit | Slither 0.11.3 |
|---|---:|---:|---:|
| Contracts mit Ergebnis | 143 | 143 | 140 |
| Contracts mit Findings | 6 | 143 | 140 |
| Findings gesamt, davon DASP-zugeordnet | 6 / 6 | 1 124 / 656 | 2 154 / 391 |
| erkannte Contracts (von 143) | 0 | 138 | 96 |
| geflaggte (Contract, Kategorie)-Paare | 6 | 464 | 214 |
| Recall | 0 % | **97 %** | 67 % |
| Precision | 0 % | 30 % | **45 %** |
| F1 | – | 45 % | **54 %** |
| LLM-Aufrufe | 72 | 6 174 | 0 |
| Token (Prompt / Completion) | 25 580 / 22 302 | 12 554 710 / 3 517 916 | – |
| Kosten gesamt | $0,0098 (vom Werkzeug aus Token gerechnet) | ≈ $2,44 (aus Token gerechnet, keine Abbuchung belegt) | $0 |
| Container-Zeit gesamt | 712,9 s | 42 792,5 s | 298,8 s |
| Wanduhr, erster Task-Start bis letztes Task-Ende | 3,2 min | 182,1 min | 1,3 min |
| Tasks mit `errors` / `fails` | 2 / 0 | 0 / 0 | 3 / 3 |

Slither steht seit dem 20.09.2026 bei 67 / 45 / 54; ältere Dokumente nennen
64 / 45 / 52, den Stand vor der Ergänzung der drei `unchecked-*`-Detektoren im
Zusatz-Mapping ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Nachtrag 4.6).

Je Kategorie: LLMSmartAudit erreicht 100 % Recall in sieben der zehn
Kategorien und 88 % bei `bad_randomness` (7 von 8); die zwei verfehlten,
`other` und `short_addresses`, haben unter den 41 Detektoren kein Gegenstück. Seine Precision reicht von 79 % bei
`unchecked_low_level_calls` (Basisrate 36 %) bis 8 % bei `denial_of_service`
(Basisrate 4 %). Slither ist bei `reentrancy` (Recall 94 %, Precision 74 %)
und `unchecked_low_level_calls` (98 %, 58 %) stark und hat bei `arithmetic`
und `front_running` keine passenden Detektoren (0 %). GPTScan löste auf 16 der
143 Contracts überhaupt einen LLM-Aufruf aus; seine 6 Findings, alle zur Regel
`MWE-207` (Unauthorized Transfer), liegen auf Contracts mit anderem
Primärlabel. Sechs der zehn Kategorien haben
acht oder weniger Contracts; ihre Recall-Intervalle sind je nach Werkzeug
zwischen 32 und 79 Prozentpunkte breit
([`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md)).

Ausfälle: Slither stürzte in 3 von 143 Tasks im IR-Generator ab (`fails`);
GPTScan meldete in 2 Tasks `errors`; LLMSmartAudit lief ohne `error` und `fail`
durch, ein Contract überschritt jedoch im zweiten Lauf das Kontextfenster
([`errors-fails.md`](errors-fails.md);
[`../eval/llmsa_curated_v2/README.md`](../eval/llmsa_curated_v2/README.md)).

### 5.2 `mwevariety_fixed`, 96 DeFi-Contracts, keine Ground Truth

Quelle: `eval/curated_mwefixed_live/run_meta.json`,
`eval/gptscan_mwefixed_v2_main/run_meta.json`,
`eval/llmsa_mwefixed_v2/run_meta.json`, `eval/llmsa_mwefixed_v2_ctx1m/run_meta.json`,
[`../eval/slither_mwefixed_v2/README.md`](../eval/slither_mwefixed_v2/README.md).

| | GPTScan (`curated_mwefixed_live`) | GPTScan mit `MAIN` (`gptscan_mwefixed_v2_main`) | LLMSmartAudit (`llmsa_mwefixed_v2` mit `_retry`) | Slither, glibc-Image (`slither_mwefixed_v2`) | LLMSmartAudit, Grenze angehoben (`llmsa_mwefixed_v2_ctx1m`) |
|---|---:|---:|---:|---:|---:|
| Contracts | 96 | 96 | 96 | 96 | 37 |
| davon analysiert | 96 | 96 | **59** | 95 | 37 |
| nicht analysiert, Grund | – | – | 37, Kontextfenster überschritten | 1, Compilerfehler | – |
| davon ohne Compilat (degradiert, Ergebnis unbestimmt) | 1 | 1 | – | – | – |
| Contracts mit Findings | 40 | 37 | 59 | 94 | 37 |
| Findings gesamt | 77 | 74 | 437 | 7 096 | 317 |
| verschiedene Regeln / Kategorien | 8 von 10 | – | 34 von 41 | 48 Detektoren | 34 von 41 |
| LLM-Aufrufe | 1 614 | 1 518 | 2 624 | 0 | 1 625 |
| Kosten | $0,2769 | $0,3638 | ≈ $8,37 (geschätzt) | $0 | $5,55 abgebucht ($11,42 geschätzt) |
| Container-Zeit gesamt | 8 217 s | 11 772 s | 90 206 s | 647 s | 35 028 s |
| Wanduhr | 36,7 min | 50,9 min (Hauptlauf; mit dem Nachlauf `_nomain` 53,5 min) | nicht ausgewiesen (Hauptlauf und Nachlauf an verschiedenen Tagen) | 2,8 min | 5,0 h in zwei Teilen |

**GPTScan** liefert auf seiner Zieldomäne 77 Findings aus acht seiner zehn
Regeln, 44 davon `MWE-200` (Insecure LP Token Value Calculation), für 28 Cent
([`../eval/curated_mwefixed_live/README.md`](../eval/curated_mwefixed_live/README.md)).
Auf 56 der 96 Contracts übergab die LLM-Stufe Kandidaten an die statische
Bestätigung, und auf 39 dieser 56 verwarf sie mindestens einen Kandidaten
([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md), Abschnitt 9). Auf 35 der
96 Contracts endete die statische Prüfung einzelner Kandidaten mit einer
Ausnahme (`Static analysis failed: Invalid args`), insgesamt 80
Kandidatenprüfungen, davon 77 zur Regel `MWE-200` und 3 zu `MWE-207` (dass
77 auch die Zahl der gemeldeten Findings ist, ist Zufall); meist hatte die
Antwort des LLM auf den Static-Prompt eine Validierungsregel nicht passiert.
GPTScan wertet einen
solchen Kandidaten als nicht bestätigt und verwirft ihn
(`GPTScan/src/tasks.py`). Die Abbrüche kosten deshalb Recall, nicht Precision:
Jedes der 77 gemeldeten Findings hat eine bestandene statische Prüfung hinter
sich; wie viele echte Findings unter den 80 verworfenen Kandidaten waren, ist
nicht untersucht (`eval/curated_mwefixed_live/run_meta.json`, `error_list`;
[`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Abschnitt 4.3).
Der Lauf mit `MAIN` reduzierte 41 der 96 Dateien auf ihren Hauptcontract; bei
drei passte der Dateiname zu keinem Contract (Exit 127), sie wurden ohne `MAIN`
nachgefahren und eingemischt.

**LLMSmartAudit** kam auf 37 der 96 Contracts (38,5 %) zu keinem Ergebnis, weil
die Konversation seiner Agenten die Grenze von 65 536 Token überschritt. Die
Grenze erwies sich als Konstante im Werkzeug (`camel/utils.py`), nicht als
Grenze des Modells, für das der Anbieter 1 Mio. Token nennt. Ein Nachlauf über
genau diese 37 Contracts mit angehobener Grenze analysierte alle 37
vollständig, 317 Findings, im Mittel 61 700 Prompt-Token je Aufruf gegen
20 900 im Hauptlauf, 5,55 USD abgebucht. Die Zahlen des Hauptlaufs bleiben
unverändert stehen, weil der Nachlauf auf einem anderen Modellstand lief
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Nachtrag 4.9;
[`../eval/llmsa_mwefixed_v2_ctx1m/README.md`](../eval/llmsa_mwefixed_v2_ctx1m/README.md)).

**Slither** erreichte mit dem Upstream-Image zunächst nur 51 der 96 Contracts,
weil die von SmartBugs bereitgestellten solc-Binaries 0.7.6 und 0.8.1 bis
0.8.12 im Alpine-Image nicht starten; mit einem eigenen glibc-Image sind es
95 von 96, mit 7 096 Findings aus 48 Detektoren (4 858 Informational, 112
Optimization, 1 254 Low, 748 Medium, 124 High), im Median 55 je Contract, die
häufigsten `too-many-digits` und `naming-convention`. Der letzte Contract,
`58_UniV3Vault.sol`, scheitert am Compiler (`Stack too deep`), nicht am
Werkzeug ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Nachtrag 4.8; [`BA-BETRIEB.md`](BA-BETRIEB.md), Fallstrick 10). Ohne Ground
Truth ist das ein Mengen-, kein Qualitätsvergleich.

### 5.3 Kosten, Zeit, Robustheit

Je Contract auf curated kostet LLMSmartAudit $0,0171 und braucht 299,2 s
Rechenzeit, GPTScan $0,00007 und 5,0 s, Slither nichts und 2,1 s (die Summen
aus 5.1 geteilt durch 143 Tasks; Slithers drei gescheiterte Tasks zählen mit).
Aus den Gesamtsummen gerechnet ist LLMSmartAudit rund 250-mal so teuer wie
GPTScan ($2,44 gegen $0,0098, beides aus Token gerechnet) und rund 140-mal so
langsam wie Slither (42 792,5 s gegen 298,8 s); auf dem DeFi-Korpus kostet es
je analysiertem Contract 49-mal so viel wie GPTScan ($0,142 gegen $0,0029,
59 gegen 96 Contracts) ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
Abschnitte 4.1 und 4.2).

Die LLM-Aufrufe der gesamten Arbeit, aus den dokumentierten Einzelposten
summiert:

| Posten | Betrag (USD) | Quelle |
|---|---:|---|
| Smoke-Tests 05.07.2026, beide Werkzeuge | ≈ 0,06 | Protokoll 4.4 |
| `curated_v1_20260705`, GPTScan | 0,0098 | `run_meta.json` |
| `curated_v1_20260705`, LLMSmartAudit | 2,44 (aus Token gerechnet) | `run_meta.json` |
| `curated_mwe_20260706`, unreparierter Korpus | 0,046 | [`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md), Nachprüfung |
| `curated_mwefixed_live` | 0,2769 | `run_meta.json` |
| GPTScan-Demolauf 02.08.2026 | 0,0725 | [`BA-DEMOLAUF-ERGEBNIS.md`](BA-DEMOLAUF-ERGEBNIS.md) |
| `gptscan_mwefixed_v2_smoke`, `_smoke2`, `_main` | 0,4087 | `run_meta.json` |
| `llmsa_curated_v2` | ≈ 5,16 (geschätzt) | `run_meta.json` |
| `llmsa_mwefixed_v2` mit Nachlauf | ≈ 8,37 (geschätzt) | `run_meta.json` |
| Timeout-Nachweis AP5, scharfe Läufe | ≈ 0,05 | Protokoll 4.5.5, 4.5.6 |
| `llmsa_mwefixed_v2_ctx1m` | 5,55 abgebucht | [`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md), 4.2 |
| zwei abgebrochene Läufe am 24.09.2026 | 0,62 abgebucht | ebenda, 4.3 |
| **Summe** | **rund 23** | |

Für die LLMSmartAudit-Demoläufe und die Live-Stichprobe `llmsa_smoke_curated`
gibt es keine Kostenzahl. Die Beträge der LLMSmartAudit-Volläufe sind aus Token
mit festen Sätzen geschätzt; das einzige belegte Paar aus Schätzung und
Abbuchung liegt um den Faktor 2,06 auseinander, weil der Anbieter einen
Cache-Rabatt gewährt ([`BA-BETRIEB.md`](BA-BETRIEB.md), Abschnitt 3). Die
Summe ist also eine Größenordnung, keine Abrechnung.

Robustheit: LLMSmartAudit lief auf curated ohne `error` oder `fail` durch; sein
Problem ist die Kontextgrenze, nicht die Stabilität. GPTScan verliert ohne
Compilat seine statische Bestätigungsstufe, und seine Grammatik lehnte in 87
der 143 curated-Tasks Teile des Solidity-0.4-Quelltexts ab und zählte dort im
Median nur ein Viertel der deklarierten Funktionen
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Nachtrag 4.7).
Über rund 6 640 API-Aufrufe der Läufe vom 05./06.07.2026 trat kein Rate-Limit
auf (ebenda, 4.4).

### 5.4 Reproduzierbarkeit

Beide LLM-Werkzeuge sind nicht deterministisch, auch bei `temperature=0`:

| | Messung | Ergebnis |
|---|---|---|
| GPTScan | 27 Contracts, zwei Läufe über den unreparierten Korpus, also im degradierten Modus ohne statische Stufe | 20 von 27 (74 %) mit identischem Finding-Satz |
| GPTScan | 96 Contracts des reparierten Korpus, `gptscan_mwefixed_v2_main` gegen `curated_mwefixed_live` | 58 von 77 Referenz-Findings reproduziert (75,3 %); vermischt mit dem Effekt von `MAIN` |
| LLMSmartAudit | 143 Contracts, `curated_v1_20260705` gegen `llmsa_curated_v2`, Schlüssel `contract_id` | 805 gemeinsame (Contract, Detektor)-Paare; Jaccard 61,4 % über die 141 Contracts mit Findings in beiden Läufen, 60,5 % über die 142 mit Findings in mindestens einem (der Unterschied ist der Contract, der im zweiten Lauf am Kontextfenster scheiterte); identischer Detektor-Satz bei 7 von 141 |
| Slither | 51 Contracts in `slither_mwefixed_v1` und `_v2` | identisch |
| Slither | Nachmessung 28.09.2026: beide Korpora vollständig, je unter Windows und Linux | alle Detektoren identisch bis auf `encode-packed-collision`, der bei einzelnen Contracts um ein Finding schwankt (ohne DASP-Zuordnung, Kennzahlen unberührt) |

Quellen: [`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md), Abschnitt 4;
[`../eval/gptscan_mwefixed_v2_main/comparison_curated_mwefixed_live.md`](../eval/gptscan_mwefixed_v2_main/comparison_curated_mwefixed_live.md);
[`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Abschnitt 4.4.
Auf die Kennzahlen gegen die Ground Truth schlägt das Rauschen kaum durch: Der
zweite LLMSmartAudit-Lauf kommt auf 96 % Recall, 32 % Precision und 47 % F1
gegenüber 97 / 30 / 45 im ersten
([`../eval/llmsa_curated_v2/README.md`](../eval/llmsa_curated_v2/README.md)).
Im Aufwand unterscheiden sich die beiden Läufe deutlich: Bei 6 126 gegen 6 174
Aufrufen erzeugte der zweite 11,2 Mio. Completion-Token gegenüber 3,5 Mio. und
brauchte 114 091,5 s Container-Zeit gegenüber 42 792,5 s (mit drei statt vier
Prozessen); die Ursache ist nicht untersucht
(`eval/llmsa_curated_v2/run_meta.json`).

### 5.5 Integration, Timeout, `MAIN`

Beide Scanner laufen als reguläre SmartBugs-Werkzeuge; alle Läufe dieser
Arbeit sind mit `python -m sb` beziehungsweise den Runnern entstanden, die
Ergebnisse liegen im SmartBugs-Layout und lassen sich mit `sb.reparse` und
`sb.results2csv` weiterverarbeiten. Die sieben Eingriffe in SmartBugs sind als
zwei Änderungen auf dem aktuellen Upstream-Stand vorbereitet, mit Tests und
100 % Abdeckung, aber noch nicht eingereicht
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Abschnitt 2.5).

Der Timeout-Mechanismus ist an echten Containern belegt: Gegen einen
absichtlich langsamen lokalen Endpunkt und gegen die DeepSeek-API landete ein
ablaufender Lauf in allen Fällen als `TIMEOUT_BRAKE` oder `TIMEOUT_NET` in
`errors`, nie in `fails`; LLMSmartAudit barg 23 beziehungsweise 24 von 41
Detektorphasen, und jedes Finding eines Teillaufs war auch im Volllauf
enthalten. Bei GPTScan fiel das Teilergebnis im gemessenen Fall auf null
Findings, weil die statische Bestätigung ohne die zugehörigen LLM-Antworten
nichts mehr bestätigen konnte; ein Platzhalter, der nach der Bremse bejahende
Antworten lieferte, wurde dabei gefunden und korrigiert
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Abschnitt 4.5).

`MAIN` reduzierte im GPTScan-Volllauf 41 von 96 Dateien. Für LLMSmartAudit
brachte es auf den zwei geprüften Kontext-Contracts nichts: Die geflatteten
Dateien behielten 12 von 13 beziehungsweise 19 von 19 Definitionen, weil der
Hauptcontract fast alles transitiv referenziert, und brachen wie im Hauptlauf
am Kontextfenster ab ([`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md),
Abschnitt 4.3).

---

## 6. Diskussion

**Die Zahl, die am meisten täuscht: GPTScans 0 % auf curated.** Der Datensatz
enthält keine DeFi-Logik; die zehn Regeln des Werkzeugs suchen nichts anderes.
Von 143 Contracts lösten 16 überhaupt einen LLM-Aufruf aus, die übrigen verwarf
der Vorfilter, wobei die Begründung „kein Schlüsselwort“ nur für die 56
vollständig geparsten Tasks belegt ist; in 87 Tasks sah der Vorfilter wegen
der Grammatik-Ablehnungen nur einen Teil der Funktionen. Auf seiner Zieldomäne
meldet dasselbe Werkzeug 77 Findings. Eine Rangfolge aus 0 % gegen 97 %
vergliche nicht zwei Werkzeuge, sondern ein Werkzeug mit der Frage, für die es
nicht gebaut wurde ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
Abschnitt 5; [`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md)).

**Die zweite: LLMSmartAudits 30 % Precision sind eine Untergrenze, seine 97 %
Recall eine Obergrenze.** Der Datensatz kennt nur ein Label je Datei, 468 der
1 124 Findings tragen keine DASP-Nummer, und eine Stichprobe von 19 „falschen“
Treffern ergab 15 plausibel, 4 generisch, 0 falsch. Umgekehrt ist der Recall
wohlwollend: Ein Werkzeug, das im Mittel 7,9 Findings je Contract meldet und
auf Contract-Ebene gewertet wird, trifft die gelabelte Kategorie häufiger auch
zufällig. Je Kategorie ist die Precision gegen die Basisrate zu lesen: Bei
`access_control` liegen 19 % nur knapp über den 13 %, die Raten brächte; bei
`unchecked_low_level_calls` stehen 79 % einer Basisrate von 36 % gegenüber.
Die wahren Werte der drei Werkzeuge liegen näher beieinander, als die Tabelle
in 5.1 nahelegt ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
Abschnitt 5; [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Abschnitt 4.2).

**Warum der Vergleich zwischen den Korpora nicht symmetrisch ist.** Die 143
curated-Dateien sind kleine Solidity-0.4-Contracts mit Ground Truth; die 96
DeFi-Contracts sind geflattete Solidity-0.6- bis 0.8-Dateien mit vollständigem
Import-Closure, um ein Vielfaches größer und ohne Referenzstand. Im Mittel
gingen 20 900 Prompt-Token in jeden LLMSmartAudit-Aufruf auf dem DeFi-Korpus.
Absolute Findingzahlen zwischen den Spalten in 5.2 zu vergleichen, hieße 59
gegen 96 Contracts und 41 breite Detektoren gegen 10 enge Regeln zu
vergleichen. Auf curated misst die Arbeit, auf dem DeFi-Korpus beschreibt sie;
was auf dem einen gilt, überträgt sich nicht auf den anderen
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Vorbemerkung
und Abschnitt 4.2).

**Was Werkzeug- und was Modelleigenschaft ist.** Die Kontextgrenze von 65 536
Token war eine Konstante in LLMSmartAudits Code aus der Zeit eines älteren
Modells; das Modell selbst verarbeitet ein Vielfaches, wie der Nachlauf zeigt.
Die Grammatik-Ablehnungen bei Solidity 0.4 sind eine Eigenschaft von GPTScans
ANTLR-Parser. Die Severity beider LLM-Werkzeuge stammt aus der `findings.yaml`
der Integration, nicht aus einem Urteil des Modells. Die Ausfälle der
Slither-Baseline mit dem Upstream-Image lagen an der Werkzeugkette (glibc gegen
musl), nicht an Slither. Modelleigenschaften sind dagegen der
Nichtdeterminismus und der einseitige Rückgang der LLMSmartAudit-Findings
zwischen Juli und August, der einen Modellwechsel hinter demselben Namen nahelegt;
die 61,4 % sind deshalb eine Obergrenze für die Stabilität, keine Messung
reiner Streuung ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
Abschnitte 2 und 4.4).

**Was der Timeout-Befund gezeigt hat.** Keines der beiden Werkzeuge kennt einen
Timeout für den Lauf; GPTScan hat eine Frist je LLM-Aufruf, LLMSmartAudit
keine. Ob sich ein Teilergebnis retten lässt, hängt daran, ob ein Werkzeug
inkrementell festhält oder erst am Schluss zusammenführt: LLMSmartAudit hält
nach jeder Phase einen Zwischenstand, GPTScan führt erst am Ende zusammen und
muss deshalb seine Pipeline ohne neue LLM-Aufrufe zu Ende laufen lassen.
Dieselbe Anforderung erzwang zwei verschiedene Lösungen, und ein Teillauf kann
zwar nichts erfinden, aber bei GPTScan auf null fallen
([`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md), Abschnitt 2).

**Was der Kontext-Befund gezeigt hat.** Ein Ausfall von 38,5 % auf realen
Contracts war kein Modell-, sondern ein Werkzeugbefund, und er blieb so lange
unsichtbar, wie der Parser einen abgebrochenen Task nicht von einem sauberen
unterschied. Die Unterscheidung `context_exceeded` gegen `clean` ist deshalb
Teil der Messmethode, nicht Kosmetik. Dass der Nachlauf mit angehobener Grenze
nicht in den Hauptlauf eingemischt wird, ist der Preis dafür, dass der Anbieter
das Modell hinter dem Namen tauscht ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Nachtrag 4.9).

**Was daraus für LLM-gestützte Analysewerkzeuge folgt.** Die Arbeit hat an zwei
Werkzeugen dieselben Lücken gefunden: kein Lauf-Timeout, keine Kostenbremse
(LLMSmartAudit), kein Offline-Modus, stilles Scheitern statt Fehlermeldung,
Severity als Katalogdefault, keine Zeilennummern, ein fest im Image
eingebranntes Modell, das vom Anbieter abgeschaltet wurde. Ein Rahmen wie
SmartBugs muss dafür Schlüssel, Netz, Kosten und Nichtdeterminismus als feste
Bestandteile seines Vertrags mit dem Werkzeug behandeln. Das Material dazu ist gesammelt, ein verallgemeinerndes
Dokument nicht geschrieben ([`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md), AP7).

---

## 7. Limitationen

1. **Single-Label-Ground-Truth.** Zweitbefunde zählen als False Positive;
   Precision-Werte sind Untergrenzen.
2. **Nur DASP-zugeordnete Findings zählen.** Bei Slither 391 von 2 154, bei
   LLMSmartAudit 656 von 1 124; zwei Zuordnungen der LLMSmartAudit-Detektoren
   stehen auf der Kippe und bewegen die Precision um rund einen Prozentpunkt
   ([`../smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md)).
3. **Contract-Level, nicht zeilengenau**, weil LLMSmartAudit keine
   Zeilennummern liefert.
4. **Keine Ground Truth auf dem DeFi-Korpus.** Dort wird beschrieben, nicht
   gemessen.
5. **Zwei Läufe sind keine Verteilung.** Die Streuung ist je LLM-Werkzeug aus
   zwei Läufen beziffert, die sich zudem in Timeout, Prozesszahl und
   Parser-Stand unterscheiden; Konfidenzintervalle über Läufe sind daraus nicht
   ableitbar.
6. **Ein Modell, ein Anbieter.** Alle Messungen mit `deepseek-v4-flash`; ein
   anderes Modell ist ohne Code-Änderung einsetzbar, aber nicht gemessen.
7. **Severity ist kein Urteil des Modells**, sondern der Default aus der
   `findings.yaml`.
8. **Timeout-Nachweis an je einem Contract.** Er zeigt, dass ein Teillauf
   nichts erfindet, nicht, wie viel er im Mittel verpasst. `evaluate_curated.py`
   kennt den Marker `sb_timeout` nicht und würde einen Teillauf wie einen
   Volllauf werten; für die ausgewerteten Läufe ohne Folge, weil keiner einen
   Timeout hatte ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
   Abschnitt 5, Punkt 8).
9. **Grammatik-Ablehnungen.** GPTScans Vorfilter sah in 87 der 143
   curated-Tasks nur einen Teil des Quelltexts; ein Nachlauf mit vollständigem
   Parsen wurde nicht durchgeführt.
10. **Verworfene Kandidaten auf dem DeFi-Korpus.** Auf 35 der 96 Contracts
    endete die statische Prüfung von zusammen 80 GPTScan-Kandidaten mit einer
    Ausnahme; sie gelten als nicht bestätigt und fehlen im Ergebnis. Wie viele
    echte Findings darunter waren, ist nicht untersucht; die 77 Findings sind
    eine Untergrenze dessen, was die zehn Regeln auf diesem Korpus treffen
    (Abschnitt 5.2).
11. **Rohdaten fehlen teilweise.** `llmsa_curated_v2` existiert nur noch als
    abgeleitete Auswertung; von allen übrigen Läufen sind `result.json` und
    `smartbugs.json` versioniert, Logs und Archive liegen außerhalb des Git
    im Release-Zip. Die Einzelurteile der qualitativen Stichproben wurden
    nicht archiviert.
12. **Kosten sind teils geschätzt.** Für die LLMSmartAudit-Volläufe liegt keine
    Abbuchung vor, für die Demo- und Stichprobenläufe keine Zahl (Abschnitt 5.3).
13. **Die Läufe sind nicht bitgleich reproduzierbar.** Neue Läufe brauchen
    Docker, lokal gebaute Images und einen Schlüssel, kosten Geld und liefern
    wegen des Nichtdeterminismus und möglicher Modellwechsel andere Findings.
14. **Nicht untersucht:** Integrationstreue gegenüber den Originalwerkzeugen,
    ein Werkzeug-Verbund, eine systematische Wiederholungsmessung; `MAIN` ist
    für LLMSmartAudit nur an zwei Contracts geprüft; die Slither-Baseline auf
    dem DeFi-Korpus fehlt für `58_UniV3Vault.sol`.
15. **143 Dateien sind nicht 143 Contracts** (Abschnitt 4.2).

Vollständige Herleitung: [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Abschnitt 5; [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
„Was dieser Vergleich nicht zeigt“;
[`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md),
Abschnitt 5.

---

## 8. Fazit und Ausblick

Zu den vier Fragen aus Abschnitt 2:

1. **Integration.** Beide Scanner laufen als reguläre SmartBugs-Werkzeuge mit
   Parser, Taxonomie, Timeout und `MAIN`. SmartBugs fehlten dafür die
   Weitergabe von Umgebungsvariablen an den Container und ihre Redaktion im
   Ergebnis, dazu ein robustes Aufräumen unter Windows; die sieben Eingriffe
   sind als zwei Pull Requests vorbereitet.
2. **Standard-Benchmark.** LLMSmartAudit erreicht 97 % Recall bei 30 %
   Precision, Slither 67 % bei 45 % und den besten F1; GPTScan meldet nichts
   Themengerechtes, weil der Datensatz seine Domäne nicht enthält.
3. **Zieldomäne.** GPTScan liefert dort 77 Findings auf 40 von 96 Contracts für
   28 Cent; LLMSmartAudit scheiterte auf 37 von 96 an einer Konstante im
   Werkzeug und analysiert mit angehobener Grenze alle; Slither meldet mit dem
   passenden Image auf 95 von 96 Contracts, überwiegend Stilhinweise.
4. **Betrieb.** Der Kostenunterschied zwischen den beiden LLM-Werkzeugen
   beträgt mehr als zwei Größenordnungen; Slither ist kostenlos und rund
   140-mal schneller als LLMSmartAudit. Von Lauf zu Lauf stimmen bei GPTScan
   74 % der Contracts überein (gemessen auf dem unreparierten Korpus, auf dem
   reparierten 75 % der Findings bei zusätzlich gesetztem `MAIN`), bei
   LLMSmartAudit 61 % der Finding-Paare; auf die Kennzahlen gegen die Ground
   Truth schlägt das kaum durch.

Das praktische Ergebnis über die Zahlen hinaus: LLM-gestützte Scanner lassen
sich in einen Rahmen wie SmartBugs einbinden, aber der Rahmen muss dafür
Schlüssel, Netz, Kosten, Timeout und Nichtdeterminismus behandeln, und die
Auswertung muss „nicht analysiert“ von „nichts gefunden“ trennen. Die Metrik
des Standard-Benchmarks ist wohlwollend zum Werkzeug, das viel meldet, und
streng zum Werkzeug, das außerhalb der Taxonomie meldet.

**Ausblick.** Als Nächstes sinnvoll wären: die beiden vorbereiteten Pull
Requests an `smartbugs/smartbugs` einreichen
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Abschnitt 2.5); der Nachweis der
Integrationstreue durch Läufe der Originalwerkzeuge außerhalb von SmartBugs
(AP2) und eine Wiederholungsmessung über mehrere Läufe (AP4); ein stärkeres
Modell, das ohne Code-Änderung einsetzbar ist; eine Ground Truth für den
DeFi-Korpus aus den Audit-Reports der Web3Bugs-Contests, aus denen er stammt;
die Frage, ob GPTScan und Slither zusammen LLMSmartAudit ersetzen; eine
Durchsicht der 80 auf dem DeFi-Korpus verworfenen GPTScan-Kandidaten am
Quelltext; und das verallgemeinernde Anforderungsdokument an LLM-Analysewerkzeuge (AP7), für
das das Material vorliegt.

---

## 9. Eigenleistung und Fremdanteil

| Eigen (Code, Dokumentation, Auswertungen) | Fremd, verändert | Fremd, unverändert |
|---|---|---|
| `analysis_tools/`, `corpus_tools/`, `testing_tools/`, `tests/`, `evaluate_curated.py`, die vier Runner, `docs/`, `eval/`, CI-Workflow | 2 Dateien in `smartbugs/sb/` (7 Blöcke `BA MODIFICATION`) und `smartbugs/.gitignore` | `smartbugs/` außer den genannten Stellen (516 Dateien byteidentisch zu `7ddaf6c`) |
| `smartbugs/tools/gptscan/`, `smartbugs/tools/llmsmartaudit/`; in `smartbugs/tools/slither-0.11.3-glibc/` Dockerfile, Konfiguration und Entrypoint | 7 Dateien in `GPTScan/` (Anbieter- und Modellwahl, Messstelle, Budget- und Deadline-Wächter, ein entferntes `breakpoint()`) | 38 Dateien in `GPTScan/`, 212 in `LLMSmartAuditTool-main/` |
| eigene Dateien in den Fremdbäumen: `GPTScan/src/llm_backend.py`, `report_md.py`, `Dockerfile`, `taxonomy/`; `LLMSmartAuditTool-main/.../chatdev/audit_report.py`, `Dockerfile.smartbugs` | 9 Dateien in `LLMSmartAuditTool-main/` (Anbieter- und Modellwahl, Kontextfenster, Report-Sammler, ein gepinntes `httpx`) | `smartbugs-curated` (geklont, nicht im Repository); die 241 Korpus-Dateien unter `smartbugs/samples/gptscan/` |

Jede geänderte Fremddatei ist per Datei-Hash gegen den Upstream-Stand belegt,
mit *was* und *warum*; das Evaluationsverzeichnis des LLMSmartAudit-Upstreams
(27 662 Dateien, 3,7 GB) wurde entfernt und extern gesichert
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)).

**Lizenzlage.** Der Eigenanteil steht unter der MIT-Lizenz; welche Pfade das
sind, zählt [`../LICENSE`](../LICENSE) auf. GPTScan steht unter AGPL-3.0, die
Änderungen daran und die eigenen Dateien in seinem Baum bleiben AGPL-3.0, und
die daraus gebauten Images werden deshalb nicht veröffentlicht. LLMSmartAudit
steht unter Apache-2.0, SmartBugs laut seiner Lizenzdatei unter Apache-2.0 und
laut `pyproject.toml` unter MIT; beides ist permissiv, der Widerspruch liegt im
Upstream.

---

## 10. Lesepfad

In dieser Reihenfolge, lebende Dokumente vor datierten Momentaufnahmen:

| Wenn Sie wissen wollen … | lesen Sie |
|---|---|
| worum es geht, was gemessen wurde, was herauskam und was das bedeutet | dieses Dokument |
| wie die drei Werkzeuge arbeiten und wie sie im Detail abschneiden, mit Diskussion | [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), das Ergebnis- und Diskussionskapitel |
| Recall, Precision und F1 je Kategorie, mit Basisrate und Intervall | [`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md) |
| was aus einem einzelnen Lauf geschlossen werden darf und was nicht | die `README.md` im jeweiligen Ordner unter [`../eval/`](../eval/README.md); alle Läufe in [`../eval/LAUFREGISTER.md`](../eval/LAUFREGISTER.md) |
| warum GPTScan auf curated 0 % erreicht und trotzdem brauchbar ist | [`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md) |
| wie der DeFi-Korpus entstand und warum er repariert werden musste | [`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md) |
| warum ein Detektor seine DASP-Nummer trägt oder nicht | [`../smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md), [`../GPTScan/taxonomy/mapping.md`](../GPTScan/taxonomy/mapping.md) |
| was ein Finding von einem `error` und einem `fail` unterscheidet | [`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md) |
| welcher Code eigen ist, welcher fremd, und jede Änderung an Fremdcode | [`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), [`../LICENSE`](../LICENSE) |
| wie die Messungen abliefen, mit Fehlern, Diagnosen und datierten Nachträgen | [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md) |
| wie der Timeout ins Werkzeug kommt und was belegt ist | [`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md) (datiert, 18.08.2026); Diagramme in [`BA-WERKZEUGKETTE.md`](BA-WERKZEUGKETTE.md) |
| welche Arbeitspakete der Betreuer gestellt hat und welche erledigt sind | [`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md) |
| wie man einen Lauf selbst startet, was er kostet und wo es hakt | [`../README.md`](../README.md) ab „Voraussetzungen“, dann [`BA-BETRIEB.md`](BA-BETRIEB.md) und [`BA-WERKZEUG-BEDIENUNG.md`](BA-WERKZEUG-BEDIENUNG.md) |
| wie geprüft wurde, dass Zahlen und Dokumente stimmen | [`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md) (datiert, 24./25.09.2026); Erstprüfung [`BA-VERIFIKATIONSBERICHT.md`](BA-VERIFIKATIONSBERICHT.md) (datiert, 02.08.2026) |
| wie die Arbeit zwischenzeitlich stand | datierte Momentaufnahmen, in der `README.md` unter „Dokumentation“ als solche geführt: [`BA-TESTLAUF-AUSWERTUNG.md`](BA-TESTLAUF-AUSWERTUNG.md), [`BA-DEMOLAUF-ERGEBNIS.md`](BA-DEMOLAUF-ERGEBNIS.md), [`BA-AUFGABEN-UND-STATUS.md`](BA-AUFGABEN-UND-STATUS.md), [`BA-ARBEITSBERICHT-20260802.md`](BA-ARBEITSBERICHT-20260802.md), [`Update_Bericht.md`](Update_Bericht.md) |

**Nachprüfen ohne Rohdaten:** `python analysis_tools\metrics_from_eval.py
eval\curated_v1_20260705__llmsmartaudit --check` rechnet Recall und Precision
aus `findings.jsonl` und der per_contract-Tabelle nach und vergleicht sie mit
`run_meta.json`; `python -m pytest tests -q` führt dieselbe Nachrechnung für
alle drei Werkzeuge und prüft die Tabellen der Dokumentation gegen
`run_meta.json`. **Mit den Rohdaten** (Release-Zip nach `smartbugs/`
entpackt) erzeugen `curated_eval.py`, `parser_audit.py` und
`errors_fails_report.py` die versionierten Auswertungen bis auf den
Zeitstempel identisch neu ([`../README.md`](../README.md), „Auswerten“).

---

## Anhang: Verlauf

| Wann | Was |
|---|---|
| Juli 2026 | Integration beider Werkzeuge, Vorphasen- und Smoke-Läufe (ab 01.07.); Hauptlauf `curated_v1_20260705` (05./06.07.); GPTScan über den unreparierten DeFi-Korpus (06.07.); Korpus-Reparatur und Referenzlauf `curated_mwefixed_live` (21.07.) |
| 02./03.08.2026 | Neugründung des Repositorys ohne das 3,7-GB-Evaluationsverzeichnis; Parser-Audit und Parser-Reparatur; Herleitung der `errors`/`fails`-Semantik; Demonstrationslauf |
| 15./16.08.2026 | GPTScan-Volllauf mit `MAIN`; LLMSmartAudit-Volläufe über beide Korpora |
| 17./18.08.2026 | Timeout-Durchreichung (AP5) mit Prüfstand und Nachweisläufen |
| 15.09.2026 | Nachlauf über vier DeFi-Contracts, deren Tasks im Hauptlauf am erschöpften API-Guthaben gescheitert waren |
| 20./21.09.2026 | Modellwahl zur Laufzeit; drei Slither-Detektoren im Zusatz-Mapping; Streuung von LLMSmartAudit beziffert |
| 24./25.09.2026 | Zweitprüfung des Repositorys; Slither-Baseline auf dem DeFi-Korpus; Kontextgrenze einstellbar und Nachlauf über die 37 Contracts; Pull Requests vorbereitet; Rohdaten versioniert und als Release abgelegt |

Daten der Läufe: [`../eval/LAUFREGISTER.md`](../eval/LAUFREGISTER.md); die
datierten Berichte zu den einzelnen Schritten stehen in der
[`../README.md`](../README.md) unter „Dokumentation“.
