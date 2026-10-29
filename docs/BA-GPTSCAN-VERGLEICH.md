# GPTScan: warum „0 %“ und trotzdem treffsicher

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Auf `smartbugs-curated` erreicht GPTScan **0 % Recall**, auf DeFi-Contracts
liefert es **verwertbare Treffer** — bei gleicher Konfiguration (SmartBugs,
DeepSeek `deepseek-v4-flash`, 4 Prozesse). Hier geht es nur um diesen
Unterschied und seine Ursache. Die Läufe A und B stammen vom 05./06.07.2026,
Lauf C vom 21.07.2026.

---

## 1. Auf einen Blick

| | **A — curated** | **B — DeFi, unrepariert** | **C — DeFi, repariert** |
|---|---|---|---|
| Lauf | `curated_v1_20260705` | `curated_mwe_20260706` | `curated_mwefixed_live` |
| Contracts | 143 (SWC/DASP) | 96 (DeFi-Logik) | 96 (dieselben, kompilierbar) |
| Contracts mit Findings | 6 / **0 themengerecht** | 7 | **40** |
| Findings | 6 (alle `MWE-207`) | 11 | **77** (8 von 10 Regeln) |
| Recall gegen Ground Truth | **0 %** | keine Ground Truth | keine Ground Truth |
| Statische Bestätigung | aktiv | fast nie (kein Compilat) | aktiv (95 von 96) |
| Kosten / Laufzeit | $0,01 / 3:19 min | $0,046 / 13:17 min | $0,28 / 36:45 min |

**Kernaussage:** Die 0 % sind kein Werkzeugfehler, sondern die richtige
Antwort auf einen Datensatz außerhalb von GPTScans Zuständigkeit. Auf seiner
Zieldomäne liefert es einschlägige Findings — und sobald die Pipeline
vollständig läuft (Lauf C), deutlich mehr.

## 2. Warum 0 % auf curated

GPTScan sucht nicht nach klassischen Schwachstellenklassen, sondern nach **10
DeFi-Logik-Szenarien** (`MWE-200` … `MWE-209`): manipulierbare Preis-Orakel,
LP-Token-Bewertung, fehlerhafte Reward-Berechnung. `smartbugs-curated` labelt
genau diese Szenarien *nicht* — seine Kategorien sind Reentrancy, Arithmetik,
Access Control, `unchecked_low_level_calls` usw. Es gibt keine Überschneidung.

**Vorfilter.** Nur **16 von 143** Contracts enthielten Schlüsselbegriffe eines
DeFi-Szenarios und lösten einen LLM-Aufruf aus; für die übrigen 127 *kann* kein
Finding entstehen. Einschränkung: Bei 87 Contracts (Solidity 0.4) lehnte
GPTScans ANTLR-Grammatik Teile des Codes ab, vor allem `constant`-Konstrukte,
und sah im Median nur ein Viertel der Funktionen
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), Nachtrag
4.7). Ob dort ein Schlüsselwort fehlte oder nie gesehen wurde, lässt sich nicht
trennen — die Schlussfolgerung bleibt, die Zahl 127 ist unscharf.

**LLM und statische Bestätigung.** Aus den 16 Kandidaten wurden **6 Findings,
alle `MWE-207`**, auf Contracts mit anderem Primärlabel. Gegen die
Single-Label-Ground-Truth zählen sie nicht. Die statische Stufe arbeitete wie
vorgesehen: Wir haben alle 4 Review-Kandidaten am Quellcode geprüft; sie
verwarf **5 LLM-Kandidaten zu Recht** als False Positives.

## 3. Warum Findings auf dem DeFi-Korpus

Der Korpus besteht aus **96 DeFi-Contracts aus GPTScans eigenem
Benchmark-Umfeld** (Web3Bugs) — genau die Art Contract (Liquidity Pools,
Orakel, LP-Token, NFT-Approvals), für die die Regeln gebaut sind. Hier
passieren die Contracts den Vorfilter, und die Regeln greifen.

Im unreparierten Lauf B:

| Regel | Beschreibung | Findings |
|---|---|---:|
| `MWE-200` | Insecure LP Token Value Calculation | 6 |
| `MWE-207` | Unauthorized Transfer | 2 |
| `MWE-209` | Wrong Order for Interest or ExchangeRate | 2 |
| `MWE-203` | Approval Not Revoked | 1 |
| **Gesamt** (7 Contracts, alle *high*) | | **11** |

Zwei am Quellcode bestätigte Beispiele:

* **`slot0`-Spotpreis als Flashloan-Vektor** — die Preisbewertung stützt sich
  auf einen im selben Block manipulierbaren Spotpreis (klassisch `MWE-200`).
* **Nie zurückgesetzte NFT-Approval** — eine Freigabe bleibt dauerhaft und
  ermöglicht späteren Missbrauch.

Unsere Bewertung von 6 gezogenen Findings: **4 plausibel, 1 generisch,
1 falsch.**

Nach der Korpus-Reparatur ([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md))
lief in Lauf C die statische Stufe auf 56 Contracts mit Kandidaten und verwarf
auf 39 davon mindestens einen; übrig blieben 77 Findings
([`../eval/curated_mwefixed_live/README.md`](../eval/curated_mwefixed_live/README.md)).
Diese Zahlen nennen [`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md)
4.2 und [`BA-ARBEIT.md`](BA-ARBEIT.md) 5.2. Der Sprung von 11 auf 77 heißt
nicht, dass das Werkzeug besser wurde, sondern dass seine Pipeline zum ersten
Mal vollständig lief.

## 4. Einschränkungen

1. **Keine Ground Truth** für den DeFi-Korpus — also bewusst keine
   Recall-/Precision-Zahl, nur Beschreibung und Stichproben.
2. **Lauf B lief degradiert.** 95 von 96 Contracts waren nicht kompilierbar;
   die Findings stammen fast nur aus der LLM-Stufe. Erst Lauf C hat die
   statische Stufe.
3. **Nichtdeterminismus.** Ein Wiederholungslauf über 27 Contracts des
   unreparierten Korpus ergab **20 von 27 (74 %)** mit identischem Finding-Satz
   (3 Findings weg, 2 neu, 2 verändert) — trotz `temperature=0`. Auf dem
   reparierten Korpus gibt es nur den Vergleich `gptscan_mwefixed_v2_main` gegen
   Lauf C: 58 von 77 Findings wiedergefunden (75,3 %), vermischt mit dem Effekt
   von `MAIN`
   ([`comparison_curated_mwefixed_live.md`](../eval/gptscan_mwefixed_v2_main/comparison_curated_mwefixed_live.md)).

## 5. Exkurs: Was sind DeFi-Logik-Schwachstellen?

**Klassische Schwachstellen** (die SWC/DASP-Klassen) sind generische
Code-Defekte: Reentrancy, Integer-Overflow, ungeprüfter `call`-Rückgabewert.
Sie hängen nicht davon ab, was der Contract wirtschaftlich tun soll, und lassen
sich syntaktisch erkennen — daher ist Slither hier stark.

Eine **Logik-Schwachstelle** liegt eine Ebene höher: Der Code tut genau, was
dort steht, aber dieses Verhalten ist *ökonomisch ausnutzbar*. Es gibt keinen
„kaputten“ Befehl; der Fehler steckt im Finanzmodell. Beispiel: Ein Preis wird
korrekt berechnet — nur aus einer Quelle, die ein Angreifer im selben Block
manipulieren kann.

**Warum ein LLM?** DeFi-Contracts (Swaps, Kredite, Staking, Liquidity Pools)
bewegen direkt Geld. Ihre Fehler zu erkennen heißt zu verstehen, *was* der
Contract erreichen will. Statischen Werkzeugen fehlt jeder Begriff von
beabsichtigtem Verhalten. GPTScan koppelt deshalb ein LLM, das die Absicht aus
Code, Namen und Kommentaren erschließt, mit einer statischen Stufe, die den
Verdacht am Datenfluss gegenprüft.

**Die zehn Szenarien** haben die GPTScan-Autoren aus realen Audit-Reports
destilliert; jedes besteht aus *Szenario* und *Eigenschaft*. Typische Vertreter:

* **Manipulierbare Preisbildung** — Spotpreis oder `balanceOf` als Orakel,
  per Flashloan verzerrbar (`MWE-200`).
* **Riskante Erst-Einzahlung** — der erste Einzahler verzerrt das Verhältnis
  von Anteilen zu Guthaben („Share-Inflation“).
* **Fehlender Slippage-Schutz** — ein Tausch akzeptiert jeden Preis und ist
  sandwich-bar (`MWE-206`).
* **Falsche Reward-/Zinsberechnung** — falsche Reihenfolge oder Basis
  (`MWE-209`).
* **Approval-Missbrauch** — eine Freigabe wird nie zurückgesetzt (`MWE-203`).

Die Regelnamen stammen direkt aus GPTScans Ausgabe (Feld `name`). Im
reparierten Korpus treten außerdem u. a. `MWE-201` (Insecure Vote
Calculation), `MWE-202` (Insecure Token Buying Behavior) und `MWE-205` (Front
Running) auf.

---

## Belege

Zahlen aus [`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md)
(4.1, 4.3, Fehler #12) und den Rohdaten unter
`smartbugs/results/gptscan/{curated_v1_20260705, curated_mwe_20260706}`. Am
20.09.2026 haben wir alle Angaben gegen die Rohergebnisse geprüft:

| Angabe | Beleg | Ergebnis |
|---|---|---|
| A: 143 Tasks, 6 Findings, alle `MWE-207` | alle `result.json` | bestätigt |
| A: $0,0098, 72 Aufrufe, 3:19 min | `GPTSCAN_META`, `smartbugs.json` | bestätigt |
| A: 16 von 143 nach dem Vorfilter | `llm_calls > 0` bei genau 16 Contracts | bestätigt; nach dem ersten LLM-Schritt bleiben 12 |
| A: 4 Review-Kandidaten, 5 verworfen | Summe `vul_before_static` = 11, `vul_after_static` = 6 | bestätigt |
| B: 11 Findings auf 7 Contracts, 6/2/2/1 | alle `result.json` | bestätigt |
| B: $0,0461, 257 Aufrufe | `GPTSCAN_META` | bestätigt |
| 74 % Übereinstimmung | `mwevar_live` gegen dieselben 27 aus Lauf B | bestätigt; Einheit ist der Contract, nicht das Finding |

Dieses Dokument ersetzt die frühere `.tex`/`.pdf`-Fassung gleichen Namens und
`BA_OnlyGPTScan.pdf`.
