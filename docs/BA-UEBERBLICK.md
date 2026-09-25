# Die Arbeit im Überblick

Bachelorarbeit **„KI-gestützte Smart-Contract-Scanner im SmartBugs-Framework“**,
Alex Hofer und Alex Unterleitner, TU Wien, Betreuer Gernot Salzer.
**Dieses Repository ist die Abgabe.** Eine gesonderte schriftliche Ausarbeitung
gibt es nicht; was die Arbeit fragt, wie sie misst und was sie findet, steht in
den Dokumenten, dem Code und den Auswertungen dieses Repositorys.

Dieses Dokument erzählt die Arbeit in einem Stück: Fragestellung, Gegenstand,
Daten, Vorgehen, Ergebnisse, Einordnung, Grenzen, Fazit. Es enthält keine
Zahl, die nicht auch in einer der verlinkten Quellen steht; wer eine Angabe
nachprüfen will, folgt dem Verweis. Stand: 25.09.2026, nach den letzten
Messläufen vom 24.09.2026.

---

## 1. Worum es geht

Statische Analysatoren wie Slither finden Schwachstellen in Smart Contracts an
Code-Mustern: Reentrancy, ungeprüfte Low-Level-Aufrufe, Zeitstempel als
Zufallsquelle. Was sie nicht finden können, sind Fehler in der *Absicht* eines
Contracts, etwa ein Liquidity-Pool, der den Preis eines Tokens aus einem
manipulierbaren Spotwert ableitet. Zwei jüngere Werkzeuge setzen dafür große
Sprachmodelle ein: **GPTScan** koppelt ein LLM mit einer statischen
Bestätigungsstufe und sucht zehn DeFi-Logik-Szenarien; **LLMSmartAudit** lässt
mehrere LLM-Rollen den Quelltext gegen 41 Detektor-Prompts prüfen.

**SmartBugs** ist das etablierte Rahmenwerk, um Analysewerkzeuge für Smart
Contracts vergleichbar zu betreiben: je Contract ein Docker-Container, passender
Compiler, Timeout, einheitliches Ergebnisformat, Parser je Werkzeug. LLM-gestützte
Werkzeuge enthielt es nicht. Sie brauchen Dinge, die SmartBugs bisher nicht
vorsah: einen API-Schlüssel zur Laufzeit, Netzzugang aus dem Container, eine
Modellwahl, und sie kosten Geld pro Aufruf.

**Fragestellung.** Was leisten die beiden LLM-gestützten Scanner, wenn man sie
als reguläre SmartBugs-Werkzeuge betreibt, gemessen an einem klassischen
statischen Analysator? Im Einzelnen:

1. **Integration.** Lassen sich GPTScan und LLMSmartAudit so in SmartBugs
   einbinden, dass sie sich wie jedes andere Werkzeug aufrufen, auswerten und
   vergleichen lassen, und was fehlt SmartBugs dafür?
2. **Erkennungsleistung auf dem Standard-Benchmark.** Wie schneiden sie auf
   `smartbugs-curated` ab, je DASP-Kategorie, in Recall und Precision, verglichen
   mit Slither 0.11.3?
3. **Verhalten auf der Zieldomäne.** Was liefern sie auf realen DeFi-Contracts,
   für die GPTScan gebaut ist und für die es keine Ground Truth gibt?
4. **Betrieb.** Was kosten sie an Geld und Zeit, wie robust laufen sie durch,
   und wie stabil sind ihre Ergebnisse von Lauf zu Lauf?
5. **Grenzen.** Was misst dieser Vergleich, und was misst er nicht?

Der Eigenanteil der Arbeit ist die Integration beider Scanner in SmartBugs
(Parser, Konfiguration, Entrypoints, Findings-Zuordnung, Docker-Images), die
dafür nötigen Eingriffe in SmartBugs selbst, die Rekonstruktion eines
kompilierbaren DeFi-Korpus, die Messläufe und die Auswertung
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)).

---

## 2. Untersuchungsgegenstand

| Werkzeug | Art | Rolle | Was es meldet |
|---|---|---|---|
| **GPTScan** | LLM + leichte Programmanalyse; 10 Regeln `MWE-200` bis `MWE-209` für DeFi-Logik | Prüfling | Regel, Funktion, Zeilenbereich, Begründung; keine Confidence |
| **LLMSmartAudit** | Multi-Agenten-Pipeline auf ChatDev/CAMEL; 41 Detektor-Prompts; kompiliert nie | Prüfling | Detektorname und Begründungstext; **keine** Zeilennummern, keine Severity |
| **Slither 0.11.3** | statische Analyse, rund hundert Detektoren, deterministisch | Referenz | Detektor, Contract, Funktion, Zeilen, Impact, Confidence |

Rahmen ist **SmartBugs 2.1.1** (Upstream-Commit `7ddaf6c`), unter
`smartbugs/` mitgeführt. LLM-Backend aller aufgezeichneten Läufe ist DeepSeek
mit dem Modell `deepseek-v4-flash`, gewählt aus Kostengründen; Anbieter und
Modell sind zur Laufzeit wählbar ([`../README.md`](../README.md), Abschnitt
„Modell wählen und wechseln“). Architektur und Aufruf der drei Werkzeuge:
[`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), Abschnitte 1
bis 3; die Kette vom Runner bis zur Auswertung als Diagramm:
[`BA-WERKZEUGKETTE.md`](BA-WERKZEUGKETTE.md).

---

## 3. Daten

Zwei Korpora, die **Unterschiedliches messen**:

| | `smartbugs-curated` | `mwevariety_fixed` |
|---|---|---|
| Umfang | 143 Contract-Dateien | 96 Contracts |
| Herkunft | [smartbugs/smartbugs-curated](https://github.com/smartbugs/smartbugs-curated), Commit `230e649` (16.06.2024) | aus GPTScans eigenem Benchmark-Umfeld (Web3Bugs-Contests), in dieser Arbeit rekonstruiert |
| Ground Truth | ja: je Datei **eine** Primärschwachstelle aus den DASP-Top-10 (`vulnerabilities.json` im Datensatz) | **nein** |
| Was sich messen lässt | Recall, Precision, F1 je Kategorie | nur beschreiben: Findings, Abdeckung, Kosten, Ausfälle |
| Solidity | 0.4 (142 Dateien), 0.5 (eine) | 0.6 (18), 0.7 (8), 0.8 (70); geflattet mit vollständigem Import-Closure |
| Im Repository | nein; `run_curated.ps1` klont und pinnt den Stand | ja, `smartbugs/samples/gptscan/mwevariety_fixed/` |

Der zweite Korpus musste erst brauchbar gemacht werden: Im ursprünglichen
Zustand kompilierte 1 von 96 Dateien, GPTScans statische Bestätigungsstufe war
damit inaktiv und das Werkzeug auf einen reinen Prompt-Scanner reduziert. Die
Rekonstruktion aus den Originalquellen bringt alle 96 zum Übersetzen
([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md), Werkzeuge in
[`../corpus_tools/README.md`](../corpus_tools/README.md)).

Zwei Eigenheiten des ersten Korpus, die die Zahlen prägen: Er labelt je Datei
genau eine Schwachstelle, ein zutreffender Zweitbefund zählt als False
Positive. Und er führt dieselbe Datei
`0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` unter zwei Kategorien, weshalb
143 Dateien nicht 143 Contracts sind.

---

## 4. Vorgehen

### 4.1 Integration in SmartBugs

Je Werkzeug ein Verzeichnis nach dem SmartBugs-Schema
(`smartbugs/tools/gptscan/`, `smartbugs/tools/llmsmartaudit/`): `config.yaml`
(Image, Netz, Entrypoint), `findings.yaml` (Zuordnung jedes Finding-Namens zu
SWC/DASP und Severity), `parser.py` (Rohausgabe zu `findings`, `infos`,
`errors`, `fails`) und `scripts/do_solidity.sh` (Entrypoint im Container).
Dazu je ein eigenes Docker-Image; das LLMSmartAudit-Image wurde von 5,13 GB
auf 587 MB verkleinert, indem das für die Analyse nicht gebrauchte
Evaluationsverzeichnis des Upstreams entfällt.

Was SmartBugs dafür fehlte und ergänzt wurde (sieben Blöcke in `sb/tools.py`
und `sb/docker.py`, als `BA MODIFICATION` markiert): ein Feld `env:` in der
Werkzeugkonfiguration, über das nur benannte, auf dem Host gesetzte
Umgebungsvariablen in den Container gelangen, und die **Redaktion** dieser
Werte, bevor SmartBugs die Container-Argumente in `smartbugs.json` schreibt.
Ohne beides müsste der API-Schlüssel ins Image oder stünde im Klartext in jedem
Ergebnisordner. Dazu `network: bridge` für die beiden LLM-Werkzeuge, weil
SmartBugs Tool-Container sonst ohne Netz startet. Begründung und Alternativen:
[`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), Abschnitt 2.1 und 2.5.

Zwei Anforderungen aus dem Betreuergespräch sind umgesetzt
([`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md)):
Der SmartBugs-**Timeout** wird ins Werkzeug durchgereicht, so dass ein Lauf bei
70 % der Frist keine neuen LLM-Aufrufe mehr absetzt und bei 90 % beendet wird,
mit dem bis dahin Ermittelten als gekennzeichnetem Teilergebnis
([`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md)); und der
SmartBugs-Parameter **`MAIN`** reduziert eine Datei auf den Contract, nach dem
sie benannt ist, weil keines der beiden Werkzeuge eine eigene Contract-Auswahl
kennt.

### 4.2 Messläufe

Jeder Lauf hat eine `runid`; SmartBugs legt je Contract ein Task-Verzeichnis
mit `smartbugs.json` (Aufrufparameter), `result.json` (geparste Ergebnisse)
und dem Rohlog an. Alle Läufe wurden über PowerShell-Runner gestartet
(`run_curated.ps1`, `run_full_v2.ps1`, `run_full_v2_llmsa.ps1`,
`run_retry_llmsa.ps1`), sequenziell je Werkzeug, mit zwei bis vier parallelen
Containern und, wo das Werkzeug selbst keine Kostenbremse hat, einem
Kostendeckel im Runner. Die Hauptläufe:

| `runid` | Werkzeug(e) | Korpus | Datum | Tasks |
|---|---|---|---|---:|
| `curated_v1_20260705` | GPTScan, LLMSmartAudit, Slither | curated | 05./06.07.2026 | 3 × 143 |
| `curated_mwefixed_live` | GPTScan | mwevariety_fixed | 21.07.2026 | 96 |
| `gptscan_mwefixed_v2_main` | GPTScan mit `MAIN` | mwevariety_fixed | 15.08.2026 | 96 |
| `llmsa_curated_v2` | LLMSmartAudit | curated | 15.08.2026 | 143 |
| `llmsa_mwefixed_v2` (+ `_retry`) | LLMSmartAudit | mwevariety_fixed | 16.08. und 15.09.2026 | 96 |
| `slither_mwefixed_v1`, `_v2` | Slither (Upstream- und glibc-Image) | mwevariety_fixed | 24.09.2026 | 2 × 96 |
| `llmsa_mwefixed_v2_ctx1m` | LLMSmartAudit, Kontextgrenze 1 Mio. Token | die 37 Kontext-Contracts | 24.09.2026 | 37 |

Insgesamt liegen 51 Läufe mit 1 501 Tasks vor, darunter Probe-, Trocken- und
Prüfläufe ([`../README.md`](../README.md), „Wo die Ergebnisse liegen“;
Protokoll: [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md)).
Die Rohergebnisse sind git-ignoriert (2,68 GB); versioniert sind die
abgeleiteten Auswertungen unter [`../eval/`](../eval/README.md).

### 4.3 Wie gemessen wird

**Contract-Level, je DASP-Kategorie.** Ein gelabelter Contract gilt als
erkannt, wenn das Werkzeug mindestens ein Finding meldet, dessen
DASP-Klassifikation auf die gelabelte Kategorie abbildet. Recall ist der Anteil
erkannter Contracts je Kategorie; Precision der Anteil der Contracts, die das
Werkzeug mit dieser Kategorie geflaggt hat und die tatsächlich so gelabelt sind.
Die Klassifikation kommt aus der `findings.yaml` des Werkzeugs; für Slither
kommen fünf dokumentierte Zusatz-Zuordnungen hinzu (`timestamp`, `weak-prng`,
drei `unchecked-*`-Detektoren). **Findings ohne DASP-Nummer fallen aus der
Rechnung**, sie sind deshalb nicht belanglos, sondern nur nicht gegen die
Ground Truth messbar. Zu jeder Precision steht die **Basisrate** (Anteil der
Contracts mit diesem Label), zu jedem Recall ein 95-%-Wilson-Intervall.
Zwei Skripte rechnen dasselbe: `evaluate_curated.py` auf der Konsole,
`analysis_tools/curated_eval.py` in die versionierten Ordner
([`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md)).

**Zustände statt Nullen.** Ein Task ohne Finding ist nicht automatisch „sauber“.
Die Auswertung unterscheidet `findings`, `clean`, `degraded` (GPTScan ohne
Compilat), `context_exceeded` (LLMSmartAudit am Kontextfenster abgebrochen) und
`failed`; `errors` und `fails` sind aus dem SmartBugs-Code hergeleitet
([`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md)). Ein Parser-Audit prüft, dass
keine Rohmeldung im Parser verlorengeht; die Reparatur eines solchen Verlusts
(1 368 Rohmeldungen) ist dokumentiert
([`BA-PARSER-AUDIT-LUECKEN.md`](BA-PARSER-AUDIT-LUECKEN.md),
[`parser-fix-vorher-nachher.md`](parser-fix-vorher-nachher.md)).

**Qualitative Stichproben** am Quellcode ergänzen die Zahlen dort, wo die
Ground Truth nicht trägt (Protokoll, Abschnitte 4.2 und 4.3); ihre Einzelurteile
wurden nicht archiviert, nur die Summen.

---

## 5. Ergebnisse

### 5.1 `smartbugs-curated`, 143 Contracts, Lauf `curated_v1_20260705`

| | GPTScan | LLMSmartAudit | Slither 0.11.3 |
|---|---:|---:|---:|
| Contracts mit Ergebnis | 143 | 143 | 140 |
| Findings gesamt, davon DASP-zugeordnet | 6 / 6 | 1 124 / 656 | 2 154 / 391 |
| Recall | 0 % | **97 %** | 67 % |
| Precision | 0 % | 30 % | **45 %** |
| F1 | – | 45 % | **54 %** |
| LLM-Aufrufe | 72 | 6 174 | 0 |
| Kosten gesamt | $0,0098 | $2,44 | $0 |
| Rechenzeit je Contract | 5,0 s | 299,2 s | 2,1 s |
| Tasks mit `fails` | 0 | 0 | 3 |

Quelle: `eval/curated_v1_20260705__<werkzeug>/run_meta.json`; je Kategorie mit
Basisrate und Intervall in
[`../eval/curated_v1_20260705__metriken.md`](../eval/curated_v1_20260705__metriken.md);
Diskussion in [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), 4.1.

Drei Beobachtungen: LLMSmartAudit findet fast alles und meldet fast alles
(7,9 Findings je Contract, kein Contract ohne Meldung; die zwei verfehlten
Kategorien `other` und `short_addresses` haben unter den 41 Detektoren kein
Gegenstück). Slither meldet am meisten, ist auf den klassischen Kategorien aber
am präzisesten und hat den besten F1. GPTScan löste auf 16 der 143 Contracts
überhaupt einen LLM-Aufruf aus; die übrigen verwarf sein Vorfilter mangels
DeFi-Schlüsselwörtern.

### 5.2 `mwevariety_fixed`, 96 DeFi-Contracts, keine Ground Truth

| | GPTScan (`curated_mwefixed_live`) | GPTScan mit `MAIN` (`gptscan_mwefixed_v2_main`) | LLMSmartAudit (`llmsa_mwefixed_v2`) | Slither, glibc-Image (`slither_mwefixed_v2`) |
|---|---:|---:|---:|---:|
| Contracts analysiert | 96 | 96 | **59** | 95 |
| nicht analysiert, Grund | – | – | 37, Kontextfenster überschritten | 1, Compilerfehler |
| Contracts mit Findings | 40 | 37 | 59 | 94 |
| Findings gesamt | 77 | 74 | 437 | 7 096 |
| Kosten | $0,28 | $0,36 | ≈ $8,37 | $0 |
| Wanduhr | 36,7 min | 50,9 min | – | 2,8 min |

Quelle: `eval/per_contract/*.csv`, `eval/gptscan_mwefixed_v2_main/run_meta.json`,
`eval/llmsa_mwefixed_v2/run_meta.json`; Tabelle mit allen Zeilen in
[`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), 4.2.

Der wichtigste Befund steht in der ersten Zeile: **LLMSmartAudit kam auf 37 der
96 Contracts (38,5 %) zu keinem Ergebnis**, weil die Konversation seiner Agenten
die Grenze von 65 536 Token überschritt. Die Grenze erwies sich als Konstante
im Werkzeug, nicht als Grenze des Modells: Ein Nachlauf über genau diese 37
Contracts mit angehobener Grenze (`llmsa_mwefixed_v2_ctx1m`, 24.09.2026)
analysierte alle 37 vollständig, 317 Findings, 5,55 USD abgebucht. Die Zahlen
des Hauptlaufs bleiben unverändert stehen, weil der Nachlauf auf einem anderen
Modellstand lief ([`../eval/llmsa_mwefixed_v2_ctx1m/`](../eval/llmsa_mwefixed_v2_ctx1m/README.md)).

GPTScan liefert auf seiner Zieldomäne 77 Findings aus acht seiner zehn Regeln,
alle durch die statische Stufe bestätigt, für 28 Cent. Slither meldet im Median
55 Findings je Contract, überwiegend Stilhinweise (`too-many-digits`,
`naming-convention`). Ohne Ground Truth ist das ein Mengen-, kein
Qualitätsvergleich.

### 5.3 Kosten, Zeit, Robustheit

Auf curated ist LLMSmartAudit rund 250-mal so teuer wie GPTScan ($2,44 gegen
$0,0098 für dieselben 143 Contracts) und rund 140-mal so langsam wie Slither;
auf dem DeFi-Korpus kostet es je analysiertem Contract 49-mal so viel wie
GPTScan ($0,142 gegen $0,0029). Alle LLM-Aufrufe der Arbeit zusammen liegen in
der Größenordnung von 20 bis 23 USD, je nach Schätzgrundlage
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md) 4.4,
[`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md) 4.2
und 4.3, [`BA-BETRIEB.md`](BA-BETRIEB.md) 3).

Robustheit: LLMSmartAudit lief auf curated ohne einen einzigen `error` oder
`fail` durch; sein Problem ist die Kontextgrenze, nicht die Stabilität. GPTScan
verliert ohne Compilat seinen Präzisionsschutz (`degraded`), und seine
Grammatik lehnte in 87 der 143 curated-Tasks Teile des Solidity-0.4-Quelltexts
ab. Slither stürzte in 3 von 143 Tasks im IR-Generator ab
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), 4.3;
[`errors-fails.md`](errors-fails.md)).

### 5.4 Reproduzierbarkeit

Beide LLM-Werkzeuge sind nicht deterministisch, auch bei `temperature=0`:

| | Messung | Ergebnis |
|---|---|---|
| GPTScan | 27 Contracts, zwei Läufe | 20 von 27 (74 %) mit identischem Finding-Satz |
| GPTScan | 96 Contracts, `gptscan_mwefixed_v2_main` gegen `curated_mwefixed_live` | 75,3 % der Referenz-Findings reproduziert (vermischt mit dem Effekt von `MAIN`) |
| LLMSmartAudit | 143 Contracts, `curated_v1_20260705` gegen `llmsa_curated_v2` | Jaccard über (Contract, Detektor)-Paare 61,4 %, über alle 142 Contracts 60,5 %; identischer Detektor-Satz bei 7 von 141 Contracts |
| Slither | – | deterministisch |

Zwischen den beiden LLMSmartAudit-Läufen liegen sechs Wochen; der Rückgang ist
einseitig, ein Modellwechsel hinter demselben Namen ist nicht auszuschließen.
Die Zahl ist eine Obergrenze für die Stabilität
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), 4.4;
[`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md), 4).

---

## 6. Einordnung

**Die Zahl, die am meisten täuscht: GPTScans 0 % auf curated.** Der Datensatz
enthält keine DeFi-Logik; die zehn Regeln des Werkzeugs suchen nichts anderes.
Auf seiner Zieldomäne meldet dasselbe Werkzeug 77 static-bestätigte Findings.
Eine Rangfolge aus 0 % gegen 97 % vergliche nicht zwei Werkzeuge, sondern ein
Werkzeug mit der Frage, für die es nicht gebaut wurde.

**Die zweite: LLMSmartAudits Precision von 30 % ist eine Untergrenze.** Der
Datensatz kennt nur ein Label je Datei, 468 der 1 124 Findings tragen keine
DASP-Nummer, und Stichproben der „falschen“ Treffer ergaben 15 plausibel,
4 generisch, 0 falsch von 19. Umgekehrt ist der Recall von 97 % eine
Obergrenze: Wer acht Findings je Contract meldet, trifft auf Contract-Ebene
häufiger zufällig. Je Kategorie ist die Precision gegen die Basisrate zu lesen;
bei `access_control` liegen 19 % nur knapp über den 13 %, die Raten brächte.

**Wofür welches Werkzeug taugt.** Slither für alles syntaktisch Erkennbare,
deterministisch, kostenlos, in Sekunden; es hat keinen Begriff von
beabsichtigtem Verhalten. GPTScan für genau die zehn DeFi-Szenarien, billig
und skalierend, aber nur so gut wie sein Compilat. LLMSmartAudit als breitestes
Werkzeug mit 41 Detektoren, auf kleinen Contracts nahezu vollständig, aber
teuer, langsam, ohne Zeilennummern und auf großen DeFi-Contracts an der
Kontextgrenze gescheitert, bis diese angehoben wurde
([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md), 5;
[`BA-GPTSCAN-VERGLEICH.md`](BA-GPTSCAN-VERGLEICH.md)).

---

## 7. Grenzen

1. **Single-Label-Ground-Truth.** Zweitbefunde zählen als False Positive;
   Precision-Werte sind Untergrenzen.
2. **Nur DASP-zugeordnete Findings zählen.** Bei Slither sind das 391 von
   2 154, bei LLMSmartAudit 656 von 1 124. Die Zuordnung der 41 Detektoren ist
   je Detektor begründet, zwei Grenzfälle sind ausgewiesen
   ([`../smartbugs/tools/llmsmartaudit/mapping.md`](../smartbugs/tools/llmsmartaudit/mapping.md)).
3. **Contract-Level, nicht zeilengenau**, weil LLMSmartAudit keine
   Zeilennummern liefert.
4. **Keine Ground Truth auf dem DeFi-Korpus.** Dort wird beschrieben, nicht
   gemessen.
5. **Ein Lauf ist keine Verteilung.** Die Streuung ist je LLM-Werkzeug aus zwei
   Läufen beziffert; Konfidenzintervalle über Läufe sind daraus nicht
   ableitbar.
6. **Ein Modell, ein Anbieter.** Alle Messungen mit `deepseek-v4-flash`; ein
   stärkeres Modell ist ohne Code-Änderung einsetzbar, aber nicht gemessen.
7. **Severity ist kein Urteil des Modells.** Bei beiden LLM-Werkzeugen stammt
   sie aus der `findings.yaml`.
8. **Timeout-Nachweis an je einem Contract.** Er zeigt, dass ein Teillauf nichts
   erfindet, nicht, wie viel er im Mittel verpasst.
9. **Grammatik-Ablehnungen.** GPTScans Vorfilter sah in 87 der 143
   curated-Tasks nur einen Teil des Quelltexts; die Begründung „kein
   Schlüsselwort“ ist nur für die 56 vollständig geparsten Tasks belegt.
10. **Die Rohdaten eines Laufs fehlen.** `llmsa_curated_v2` existiert nur noch
    als abgeleitete Auswertung; er trägt allein zur Streuungsangabe bei.
11. **Nicht untersucht:** ob die Integration die Werkzeuge gegenüber ihrem
    Originalzustand verändert (Integrationstreue), ob ein Verbund aus GPTScan
    und Slither mehr findet als LLMSmartAudit allein, und eine systematische
    Wiederholungsmessung über mehr als zwei Läufe.

Vollständige Liste: [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Abschnitt 5, und [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
„Was dieser Vergleich nicht zeigt“.

---

## 8. Fazit

Zu den fünf Fragen aus Abschnitt 1:

1. **Integration:** Beide Scanner laufen als reguläre SmartBugs-Werkzeuge, mit
   Parser, Taxonomie, Timeout und `MAIN`. SmartBugs fehlten dafür zwei Dinge,
   die Weitergabe von Umgebungsvariablen an den Container und ihre Redaktion im
   Ergebnis; beide sind als Pull Requests an das SmartBugs-Projekt vorbereitet.
2. **Standard-Benchmark:** LLMSmartAudit erreicht 97 % Recall bei 30 %
   Precision, Slither 67 % bei 45 % und den besten F1; GPTScan meldet nichts
   Themengerechtes, weil der Datensatz seine Domäne nicht enthält.
3. **Zieldomäne:** GPTScan liefert dort 77 bestätigte Findings auf 40 von 96
   Contracts; LLMSmartAudit scheiterte auf 37 von 96 an einer Konstante im
   Werkzeug und analysiert mit angehobener Grenze alle.
4. **Betrieb:** Der Kostenunterschied zwischen den beiden LLM-Werkzeugen
   beträgt mehr als zwei Größenordnungen; Slither ist kostenlos und rund 140-mal
   schneller als LLMSmartAudit. Von Lauf zu Lauf stimmen bei GPTScan 74 % der
   Contracts überein, bei LLMSmartAudit 61 % der Finding-Paare.
5. **Grenzen:** Die Metrik ist wohlwollend zum Werkzeug, das viel meldet, und
   streng zum Werkzeug, das außerhalb der Taxonomie meldet. Die wahren Werte
   liegen näher beieinander, als die Tabelle nahelegt.

Das praktische Ergebnis über die Zahlen hinaus: LLM-gestützte Scanner lassen
sich in einen Rahmen wie SmartBugs einbinden, aber der Rahmen muss dafür
Schlüssel, Netz, Kosten und Nichtdeterminismus als Erstklassiges behandeln.
Diese Arbeit zeigt an zwei Werkzeugen, was das im Einzelnen heißt.

---

## 9. Offen geblieben

* Aus dem Betreuergespräch: AP2 (Integrationstreue), AP4 (systematische
  Reproduzierbarkeitsmessung), AP7 (Meta-Findings-Dokument) und AP8
  ([`BA-BETREUERGESPRAECH-AUFGABEN.md`](BA-BETREUERGESPRAECH-AUFGABEN.md)).
* Die beiden Pull Requests an `smartbugs/smartbugs` sind vorbereitet, aber noch
  nicht eingereicht ([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), 2.5).
* `58_UniV3Vault.sol` in der Slither-Baseline (Compilerfehler ohne
  `--optimize`), die zwei Grenzfälle der DASP-Zuordnung, die verlorenen Rohdaten
  von `llmsa_curated_v2`
  ([`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md), 5).

---

## 10. Eigenanteil und Fremdanteil

| Eigen | Fremd, unverändert | Fremd, verändert |
|---|---|---|
| `smartbugs/tools/gptscan/`, `smartbugs/tools/llmsmartaudit/`, `smartbugs/tools/slither-0.11.3-glibc/` (Dockerfile, Konfiguration, Entrypoint) | `smartbugs/` außer den genannten Stellen | 2 Dateien in `smartbugs/sb/` (7 Blöcke `BA MODIFICATION`) |
| `analysis_tools/`, `corpus_tools/`, `testing_tools/`, `tests/`, `evaluate_curated.py`, die vier Runner, `docs/`, `eval/` | `smartbugs-curated` (geklont, nicht im Repository) | 7 Dateien in `GPTScan/`, 9 in `LLMSmartAuditTool-main/` |
| eigene Dateien in den Fremdbäumen, u. a. `GPTScan/src/llm_backend.py`, `GPTScan/Dockerfile`, `LLMSmartAuditTool-main/.../chatdev/audit_report.py`, `Dockerfile.smartbugs` | | |

Jede geänderte Fremddatei ist per Datei-Hash gegen den Upstream-Stand belegt,
mit *was* und *warum* ([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)). Lizenz: MIT
für den Eigenanteil; GPTScan steht unter AGPL-3.0, weshalb die geänderten
Images nicht veröffentlicht werden ([`../LICENSE`](../LICENSE)).

---

## 11. Nachprüfen

**Ohne die Rohdaten**, allein aus dem Repository: Alle Kennzahlen dieses
Dokuments stehen in den versionierten Auswertungen unter `eval/`
(`run_meta.json`, `findings.jsonl`, `summary.md`) und lassen sich dort
nachlesen; jede `README.md` dort sagt, was man aus dem Ordner schließen darf
und was nicht. Recall und Precision lassen sich aus diesen Dateien allein
nachrechnen: `python analysis_tools\metrics_from_eval.py
eval\curated_v1_20260705__llmsmartaudit --check` bildet die Kennzahlen aus
`findings.jsonl` und der per_contract-Tabelle und vergleicht sie mit
`run_meta.json`. Die Testsuite (`python -m pytest tests -q`) läuft ohne Docker
und ohne Schlüssel gegen aufgezeichnete Rohdaten; sie enthält Tests, die die
Tabellen der Dokumentation gegen `run_meta.json` prüfen und diese Nachrechnung
für alle drei Werkzeuge des curated-Laufs ausführen.

**Mit den Rohdaten** (2,68 GB unter `smartbugs/results/`, bei den Verfassern):
`python analysis_tools/curated_eval.py` erzeugt die `eval/`-Ordner des
curated-Laufs neu, `python analysis_tools/parser_audit.py` den Lückenbericht,
`python analysis_tools/errors_fails_report.py` die Errors/Fails-Bilanz; alle
drei reproduzieren die eingecheckten Dateien bis auf den Zeitstempel.

**Neue Läufe** brauchen Docker, die lokal gebauten Images und einen
API-Schlüssel; Anleitung in [`../README.md`](../README.md) und
[`BA-BETRIEB.md`](BA-BETRIEB.md). Bitgleiche LLM-Ergebnisse sind nicht zu
erwarten (Abschnitt 5.4).

---

## 12. Verlauf

| Wann | Was |
|---|---|
| bis Juli 2026 | Integration beider Werkzeuge, erste Läufe; Hauptlauf `curated_v1_20260705` (05./06.07.); Korpus-Reparatur und GPTScan-Referenzlauf `curated_mwefixed_live` (21.07.) |
| 02.08.2026 | Neugründung des Repositorys ohne das 3,7-GB-Evaluationsverzeichnis; Parser-Audit und -Reparatur; Errors/Fails-Semantik; Demonstrationslauf |
| 15./16.08.2026 | LLMSmartAudit-Volläufe über beide Korpora; GPTScan-Volllauf mit `MAIN` |
| 17./18.08.2026 | Timeout-Durchreichung (AP5) mit Prüfstand und Nachweisläufen |
| 15.09.2026 | Nachlauf über vier unentschiedene DeFi-Contracts |
| 20./21.09.2026 | Ausbaustufe: Modellwahl zur Laufzeit, Slither-Mapping, Streuung von LLMSmartAudit beziffert |
| 24./25.09.2026 | Zweitprüfung des Repositorys; Slither-Baseline auf dem DeFi-Korpus; Kontextgrenze einstellbar und Nachlauf über die 37 Contracts; Pull Requests vorbereitet |

Die datierten Berichte zu diesen Schritten stehen in der README unter
„Dokumentation“.
