# GPTScan im Direktvergleich: Warum „0 %" und trotzdem treffsicher

**Zwei Contract-Läufe gegenübergestellt** · Auszug zur Bachelorarbeit
**Durchführung:** 05.–06.07.2026

GPTScan wurde in *zwei* getrennten Läufen über *zwei* unterschiedliche
Contract-Mengen evaluiert. Auf dem einen Datensatz erreicht das Werkzeug
**0 % Recall**, auf dem anderen liefert es **verwertbare Treffer**. Dieses
Dokument stellt ausschließlich diese Differenz dar und erklärt ihre Ursache.
Beide Läufe nutzten dieselbe Konfiguration (SmartBugs-Integration, DeepSeek
`deepseek-v4-flash`, `--processes 4`); der einzige Unterschied ist der
Contract-Korpus.

---

## 1. Die Gegenüberstellung auf einen Blick

| | **Lauf A — curated** | **Lauf B — mwevariety** |
|---|---|---|
| Korpus | smartbugs-curated | GPTScans Benchmark-Umfeld |
| Contracts | 143 (klassische SWC/DASP) | 96 (DeFi-Logik) |
| Contracts mit Findings | 6 roh / **0 themengerecht** | **7** |
| Findings gesamt | 6 (alle MWE-207) | **11** (alle Severity *high*) |
| Recall vs. Ground Truth | **0 %** \* | **treffsicher** † |
| Vorfilter passiert | nur 16 / 143 | Korpus ist bereits Zieldomäne |
| Static-Bestätigung | aktiv (kompilierbar) | überwiegend inaktiv (degradiert) |
| Kosten / Laufzeit | $0.01 / 3:19 min | $0.046 / 13:17 min |

\* *by design*, siehe Abschnitt 2. † Ohne vendorte Ground Truth →
deskriptiv/qualitativ statt Recall-Zahl, siehe Abschnitt 3.

**Kernaussage:** Die 0 % sind *kein* Werkzeugfehler, sondern die korrekte Antwort
auf einen Datensatz außerhalb von GPTScans Zuständigkeit. Sobald das Werkzeug auf
seiner Zieldomäne läuft, produziert es einschlägige Findings.

## 2. Warum GPTScan auf „curated" 0 % erreicht

GPTScan bildet nicht die klassischen Schwachstellenklassen ab, sondern
**10 DeFi-Logik-Szenarien** (`MWE-200` … `MWE-209`) — etwa manipulierbare
Preis-Orakel, LP-Token-Bewertung oder fehlerhafte Reward-Berechnung. Der Datensatz
`smartbugs-curated` annotiert dagegen genau *diese* Szenarien *nicht*: seine zehn
DASP-Kategorien sind Reentrancy, Arithmetik, Access Control,
`unchecked_low_level_calls` usw. Es gibt schlicht keine Überschneidung zwischen
dem, was GPTScan sucht, und dem, was curated labelt.

**Stufe 1 — Keyword-/Szenario-Vorfilter.**
Nur **16 von 143** Contracts enthielten überhaupt Schlüsselbegriffe eines
DeFi-Szenarios und lösten damit einen LLM-Aufruf aus. Die übrigen 127 werden ohne
LLM-Aufruf verworfen — für sie *kann* definitionsgemäß kein Finding entstehen.

**Stufe 2 — LLM und statische Bestätigung.**
Aus den 16 Kandidaten resultierten **6 Findings, alle vom Typ `MWE-207`**. Diese
lagen auf Real-World-Contracts, deren *Primär*-Label im curated-Ground-Truth ein
*anderes* war. Gegen die Single-Label-Ground-Truth gemessen zählen sie daher nicht
als Treffer → Recall 0 %.

**Die Static-Stufe arbeitete bestimmungsgemäß.**
Alle 4 Review-Kandidaten wurden am Quellcode geprüft. Die statische
Bestätigungsstufe lief und verwarf **5 LLM-Kandidaten korrekt** als False
Positives — also gewolltes Präzisions-Filtering, kein Datenproblem.

**Fazit Lauf A:** 0 % ist die *erwartete* Zahl. Ein Werkzeug für DeFi-Logik auf
einem Datensatz klassischer SWC-Bugs kann per Konstruktion nichts Themengerechtes
finden.

## 3. Warum GPTScan auf „mwevariety" Findings liefert

`mwevariety` besteht aus **96 DeFi-Contracts aus GPTScans eigenem
Benchmark-Umfeld** — also exakt der Contract-Art (Liquidity Pools, Preis-Orakel,
LP-Token, NFT-Approvals), für die die Szenario-Regeln entworfen wurden. Hier
passieren die Contracts den Vorfilter, und die Muster der `MWE`-Regeln greifen.

| Regel | Beschreibung | Findings |
|---|---|---:|
| `MWE-200` | Insecure LP Token Value Calculation | 6 |
| `MWE-207` | Unauthorized Transfer | 2 |
| `MWE-209` | Wrong Order for Interest or ExchangeRate | 2 |
| `MWE-203` | Approval Not Revoked | 1 |
| **Gesamt** (auf 7 Contracts, alle Severity *high*) | | **11** |

Im Kontrast dazu: 0 themengerechte Findings auf curated.

**Warum gerade diese Contracts?** Weil ihre Logik die von GPTScan gesuchten
Angriffsmuster tatsächlich enthält. Zwei am Quellcode verifizierte Beispiele aus
der qualitativen Stichprobe:

* **`slot0`-Spotpreis als Flashloan-Vektor** — LP-Token-/Preisbewertung stützt
  sich auf einen unmittelbar manipulierbaren Spotpreis (klassischer
  `MWE-200`-Fall).
* **Nie zurückgesetzte NFT-Approval** — eine erteilte Freigabe bleibt dauerhaft
  bestehen und eröffnet einen späteren Missbrauch.

Qualitative Bewertung der 6 gezogenen Findings: **4 plausibel, 1 generisch,
1 falsch**. GPTScan trifft auf seiner Zieldomäne also nicht nur *irgendetwas*,
sondern überwiegend inhaltlich Nachvollziehbares.

## 4. Einschränkungen des mwevariety-Laufs

Damit der Vergleich nicht überinterpretiert wird, gehören folgende Caveats
zwingend dazu:

1. **Keine vendorte Ground Truth.** Für mwevariety existiert kein annotierter
   Referenzstand → es gibt bewusst *keine* Recall/Precision-Zahl, nur eine
   deskriptive und qualitative Auswertung.
2. **Degradierter LLM-only-Modus.** 95 von 96 Contracts waren einzeln extrahiert
   und nicht kompilierbar (`InvalidCompilation`); GPTScans statische
   Bestätigungsstufe — der Präzisions-Schutz — lief daher überwiegend *nicht*. Die
   Findings entstammen fast ausschließlich der LLM-Stufe. Dieser Defekt wurde
   später behoben, siehe [`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md).
3. **Nicht-Determinismus.** Ein Wiederholungslauf über dieselben 27 Contracts
   ergab nur **74 % identische Ergebnisse** (3 Findings verschwunden, 2 neu,
   2 verändert) — *trotz* `temperature=0`. Zentrale Limitation LLM-basierter
   Scanner.

## 5. Exkurs: Was sind DeFi-Logik-Szenarien?

### Logik-Schwachstellen im Allgemeinen

Klassische Schwachstellen (die SWC/DASP-Klassen aus Abschnitt 2) sind *generische
Code-Defekte*: Reentrancy, Integer-Overflow, ein nicht geprüfter
`call`-Rückgabewert. Sie hängen nicht davon ab, *was* der Contract wirtschaftlich
tun soll — ein Overflow ist ein Overflow, egal ob im Token oder im Spiel. Solche
Muster lassen sich syntaktisch erkennen, weshalb statische Analysewerkzeuge wie
Slither hier stark sind.

Eine **Logik-Schwachstelle** liegt dagegen *eine Ebene höher*: Der Code ist
technisch fehlerfrei und tut exakt das, was dort steht — aber dieses beabsichtigte
Verhalten ist *ökonomisch ausnutzbar*. Es gibt keinen „kaputten" Befehl, den man
markieren könnte; der Fehler steckt in der *Absicht* bzw. im Finanzmodell des
Contracts. Beispiel: Ein Preis wird völlig korrekt berechnet — nur aus einer
Quelle, die ein Angreifer im selben Block manipulieren kann.

### Warum gerade DeFi, und warum ein LLM?

DeFi-Contracts (Decentralized Finance — Swaps, Kreditvergabe, Staking, Liquidity
Pools, LP-Token) bewegen unmittelbar Werte. Ihre typischen Fehler sind deshalb
**contract-spezifisch und semantisch**: Um sie zu erkennen, muss man verstehen,
*was* der Contract erreichen will und *wie* sein ökonomisches Modell funktioniert
— nicht bloß, welche Opcodes vorkommen. Genau das können rein statische Werkzeuge
nicht, weil ihnen jeder Begriff von „beabsichtigtem" Verhalten fehlt. Deshalb
koppelt GPTScan ein **LLM** (das Absicht aus Code, Bezeichnern und Kommentaren
erschließt) mit einer **statischen Bestätigungsstufe** (die den LLM-Verdacht am
Datenfluss gegenprüft und False Positives verwirft).

### Die „10 Szenarien" konkret

Die GPTScan-Autoren haben aus realen Audit-Reports **zehn wiederkehrende,
maschinell prüfbare Logik-Fehlermuster** destilliert. Jedes davon ist als
*Szenario* („wonach in der Funktion gesucht wird") plus *Eigenschaft* („welche
Bedingung es verdächtig macht") formuliert; in dieser Integration tragen sie die
Kennungen `MWE-200` … `MWE-209`. Repräsentative Vertreter dieses Katalogs:

* **Manipulierbare Preisbildung** — ein Spot-/Momentanpreis oder `balanceOf` dient
  direkt als Orakel und lässt sich per Flashloan verzerren. (GPTScans Regel
  `MWE-200` „Insecure LP Token Value Calculation".)
* **Riskante Erst-Einzahlung** — der erste Einzahler in einen Vault kann das
  Verhältnis von Anteilen zu Guthaben verzerren („Share-Inflation").
* **Fehlender Slippage-/Front-Running-Schutz** — ein Tausch akzeptiert jeden
  Ausführungspreis und ist damit sandwich-bar.
* **Fehlerhafte Reward-/Zins-/Accounting-Berechnung** — Belohnungen, Zinsen oder
  Guthaben werden in falscher Reihenfolge oder mit falscher Basis verrechnet.
* **Approval-Missbrauch** — eine erteilte Token-Freigabe wird nie zurückgesetzt
  und bleibt dauerhaft ausnutzbar.

**Namensherkunft.** Die Regelnamen stammen unmittelbar aus GPTScans eigener
Ausgabe (dem `name`-Feld jedes Findings), sind also belegt und nicht
rekonstruiert: `MWE-200` Insecure LP Token Value Calculation, `MWE-203` Approval
Not Revoked, `MWE-207` Unauthorized Transfer, `MWE-209` Wrong Order for Interest
or ExchangeRate. Weitere Regeln desselben Katalogs treten im erweiterten Lauf über
den reparierten Korpus auf — u. a. `MWE-201` Insecure Vote Calculation, `MWE-202`
Insecure Token Buying Behavior, `MWE-205` Front Running und `MWE-206` No Slippage
Limit Check (siehe [`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md)).

**Quelle aller Zahlen:** Durchführungsprotokoll der Tool-Evaluation
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md)), Abschnitte 4.1
und 4.3 sowie Fehler #12; Rohdaten unter
`smartbugs/results/gptscan/{curated_v1_20260705, curated_mwe_20260706}`.

---

## Nachprüfung am Repository (20.09.2026)

Diese Fassung ersetzt die frühere `.tex`/`.pdf`-Ausarbeitung gleichen Namens sowie
deren Vorfassung `BA_OnlyGPTScan.pdf`. Alle Kennzahlen wurden gegen die
Rohergebnisse gegengeprüft; präzisiert wurde dabei nur, *woran* eine Zahl
gemessen ist — die Werte selbst sind unverändert.

| Angabe | Beleg | Ergebnis |
|---|---|---|
| Lauf A: 143 Tasks, 6 Findings, alle MWE-207 | alle `result.json` in `smartbugs/results/gptscan/curated_v1_20260705/` | bestätigt |
| Lauf A: $0.01 / 3:19 min / 72 LLM-Calls | `GPTSCAN_META` je `result.log` ($0,0098; 72 Calls) und `smartbugs.json` (3,22 min Task-Spanne; SmartBugs meldet 3:19) | bestätigt |
| Lauf A: 16 / 143 passierten den Vorfilter | `GPTSCAN_META`, Feld `llm_calls` > 0 bei genau 16 Contracts | bestätigt — gemeint ist der Keyword-Vorfilter, nach dem *ersten* LLM-Schritt bleiben 12 Contracts übrig |
| Lauf A: 4 Review-Kandidaten, 5 verworfene LLM-Kandidaten | `GPTSCAN_META`: Summe `vul_before_static` = 11, `vul_after_static` = 6, Verwurf bei 4 Contracts | bestätigt |
| Lauf B: 11 Findings auf 7 Contracts, Regelverteilung 6/2/2/1 | alle `result.json` in `smartbugs/results/gptscan/curated_mwe_20260706/` | bestätigt |
| Lauf B: $0.046 / 257 LLM-Calls | `GPTSCAN_META` je `result.log` ($0,0461; 257 Calls) | bestätigt |
| 74 % Lauf-zu-Lauf-Übereinstimmung | `mwevar_live` (27 Contracts) gegen dieselben 27 aus `curated_mwe_20260706` | bestätigt — 20 von 27 Contracts mit identischem Finding-Satz (74,1 %); die Einheit ist der **Contract**, nicht das einzelne Finding |
