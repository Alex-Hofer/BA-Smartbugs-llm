# Die zehn Lücken im Parser-Audit

Einordnung der Lücken, die `analysis_tools/parser_audit.py` seit dem
21.09.2026 meldet. Stand: 48 Läufe, 1 272 Tasks, 2 417 Rohmeldungen, **10
Lücken** — alle im Lauf `llmsa_mwefixed_v2`, alle vom Signaltyp `TRACEBACK`.

Der Bericht selbst steht in
[`parser-audit-nachher.md`](parser-audit-nachher.md) und wird erzeugt, nicht
geschrieben. Dieses Dokument sagt, was dort steht und was es bedeutet.

---

## 1. Warum die Zahl von 0 auf 10 gestiegen ist

Bis zum 20.09.2026 meldete das Audit **0 Lücken**. Das war keine Messung,
sondern eine Eigenschaft des Detektor-Katalogs.

Ein `TRACEBACK`-Signal entstand nur, wenn ein Log-Record **beides** enthielt:
die Zeichenkette `Traceback (most recent call last)` *und* die abschließende
`Modul.Fehler: Meldung`-Zeile. LLMSmartAudit schreibt über `rich`, und dessen
Konsole trennt beides gelegentlich in zwei Records. Landet die Abschlusszeile
allein in einem eigenen Record, sah der alte Katalog sie nicht — und meldete
folgerichtig keine Lücke, ganz gleich, was der Parser mit ihr gemacht hätte.

Auf dem heutigen Bestand betrifft das **132 Records in 89 Tasks**. Von den 92
Tasks, deren Parser-Ausgabe eine Ausnahme nennt, erzeugte das Audit bei **46**
überhaupt kein Ausnahme-Signal, sondern nur `EXIT_NONZERO` und `OUTPUT_ERROR`.

Der neue Detektor `_ORPHAN_EXC` schließt diese Stelle. Er greift bewusst nur,
wenn der Record **mit** der Ausnahme beginnt: ein Ausnahmename mitten in Prosa
oder in einer Finding-Beschreibung zählt nicht als Meldung dieser Ausnahme.
Abgesichert durch `tests/test_parser_audit_orphan_exception.py`.

> **Die ehrliche Lesart.** Die alte Null sagte „der Katalog hat nichts
> gefunden", nicht „der Parser verliert nichts". Erst der schärfere Katalog
> macht die Aussage prüfbar — und er findet etwas. Ein Audit, das nie etwas
> findet, belegt seine eigene Schärfe nicht.

## 2. Was in den zehn Fällen tatsächlich passiert

In **allen zehn** Fällen markiert der Parser den Task korrekt als gescheitert.
Verloren geht nicht *dass* etwas schieflief, sondern **woran**. Der Parser
greift eine benachbarte Zeile auf statt die Abschlusszeile der Ausnahme.

| Contract | Ursache laut Rohlog | Parser meldet stattdessen |
|---|---|---|
| `106_NFTLoanFacilitator.sol` | `max_tokens_exceeded_by_camel` | `num_max_completion_tokens (before adjustment): 43146` |
| `12_Witch.sol` | **HTTP 402 Insufficient Balance** | `num_prompt_tokens: 22878`, `tenacity.RetryError` |
| `25_CompositeMultiOracle.sol` | **HTTP 402 Insufficient Balance** | `String length: 31828`, `tenacity.RetryError` |
| `30_Vault.sol` | `max_tokens_exceeded_by_camel` | `String length: 109412` |
| `43_DelegatedStaking.sol` | **HTTP 402 Insufficient Balance** | `String length: 92678`, `tenacity.RetryError` |
| `62_Locke.sol` | **HTTP 402 Insufficient Balance** | `num_max_token: 65536`, `tenacity.RetryError` |
| `69_NFTXStakingZap.sol` | `max_tokens_exceeded_by_camel` | `num_max_completion_tokens (after adjustment): 5410` |
| `74_TimeswapPair.sol` | `max_tokens_exceeded_by_camel` | `num_max_completion_tokens (after adjustment): 8192` |
| `75_XDEFIDistribution.sol` | `max_tokens_exceeded_by_camel` | `String length: 142562` |
| `78_FlashGovernanceArbiter.sol` | `max_tokens_exceeded_by_camel` | `String length: 173170` |

Zwei Klassen, keine dritte:

* **Sechs Kontextfenster-Abbrüche.** `RuntimeError: error in
  ChatAgentResponse … termination_reasons: ['max_tokens_exceeded_by_camel']`.
  Das ist die bekannte Grenze des Werkzeugs bei großen Contracts und in der
  Arbeit bereits als solche beschrieben. Der Parser meldet eine der
  Token-Zählzeilen aus derselben Fehlerausgabe — inhaltlich verwandt, aber
  nicht die Ursache.

* **Vier abgebrochene API-Aufrufe wegen erschöpftem Guthaben.**
  `openai.APIStatusError: Error code: 402 — Insufficient Balance`. Der Parser
  reicht nur die Hülle `tenacity.RetryError` weiter, in der die eigentliche
  Ursache als Text eines `Future`-Objekts steckt.

## 3. Was das für die Auswertung heißt

**Für die Kennzahlen: nichts.** Recall, Precision und F1 werden ausschließlich
auf `curated_v1_20260705` gerechnet, nicht auf `llmsa_mwefixed_v2`.

**Für den Lauf selbst: die vier 402er sind bereits aufgelöst.** Sie sind genau
die vier Contracts, die der Nachlauf `llmsa_mwefixed_v2_retry` am 15.09.2026
wiederholt hat — `12_Witch`, `25_CompositeMultiOracle`, `43_DelegatedStaking`,
`62_Locke`. Nach dem Auffüllen des Guthabens lieferten alle vier ein Ergebnis;
ihre Findings stecken in der zusammengeführten `findings.jsonl`. Die Bilanz des
Laufs geht damit auf:

```
55 Contracts mit Findings im Hauptlauf
+ 4 aus dem Nachlauf            = 59 mit Findings
+ 37 Kontext ueberschritten      = 96
```

Der zentrale Befund des Laufs — 37 von 96 Contracts sprengen das
Kontextfenster — ist davon **unberührt**. Die vier Guthaben-Fälle werden von
`build_eval.task_state` als `no_output` geführt, nicht als
`context_exceeded`; sie sind nie in die 37 eingerechnet worden.

**Was neu ist, ist die Begründung des Nachlaufs.** Bisher stand dort, er habe
„vier Tasks ersetzt, die der Hauptlauf nicht entschieden hatte". Das ist
richtig, aber unscharf — und ein Nachlauf über genau vier Contracts sieht ohne
Begründung nach Auswahl nach Ergebnis aus. Die Ursache ist eine
Infrastruktur-Störung, kein unliebsames Ergebnis: Das Guthaben war
aufgebraucht, vier Contracts liefen deshalb in HTTP 402. Genau das ließ sich
bis zum 21.09.2026 nicht belegen, weil der Parser nur die Hülle
`tenacity.RetryError` weiterreicht und das Audit die Abschlusszeile nicht sah.
Nachgetragen in
[`../eval/llmsa_mwefixed_v2/README.md`](../eval/llmsa_mwefixed_v2/README.md).

## 4. Warum die Lücken nicht geschlossen wurden

Die Ausnahme-Extraktion liegt in `sb/parse_utils.py`, also in fremdem
Upstream-Code. `BA-EIGENANTEIL.md` weist ausdrücklich aus, dass dieser Teil
**unverändert** bleibt: die Parser-Reparatur dieser Arbeit findet
ausschließlich in den eigenen Tool-Parsern statt, damit sie sich per
`python -m sb.reparse` auf Altläufe anwenden lässt und keines der übrigen
30+ SmartBugs-Werkzeuge berührt.

Die Lücken ließen sich im eigenen LLMSmartAudit-Parser schließen, indem er
verwaiste Abschluss-Records selbst einsammelt. Das erfordert einen `reparse`
über alle Läufe und verschiebt die Errors/Fails-Bilanz in
[`errors-fails.md`](errors-fails.md). Diese Änderung ist **bewusst nicht mehr
vorgenommen** worden: Sie ist kein Fehler des Messaufbaus, sondern eine
Verbesserung der Diagnosetiefe, und sie so kurz vor Abschluss einzuziehen
hieße, sämtliche Rohdaten noch einmal anzufassen. Die zehn Fälle sind
stattdessen hier vollständig benannt und eingeordnet — was sie für die
Auswertung gleichwertig verwertbar macht.

Für eine Fortführung der Arbeit ist es der naheliegendste nächste Schritt.
