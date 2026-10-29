# Der Ausnahme-Defekt im LLMSmartAudit-Parser

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Am 21.09.2026 zeigte unser Parser-Audit plötzlich zehn Lücken. Hier steht,
woran das lag und wie wir sie geschlossen haben. Heute: 1 501 Tasks, 2 555
Rohmeldungen, **0 Lücken** ([`parser-audit-nachher.md`](parser-audit-nachher.md)).

---

## 1. Wie die Lücken sichtbar wurden

Bis zum 20.09.2026 meldete das Audit 0 Lücken — das war aber keine Messung,
sondern eine Schwäche des Detektor-Katalogs. Ein `TRACEBACK`-Signal entstand
nur, wenn ein Log-Record **beides** enthielt: `Traceback (most recent call last)`
*und* die Abschlusszeile `Modul.Fehler: Meldung`. Stand die Abschlusszeile in
einem eigenen Record, sah das Audit sie nicht. Betroffen waren **132 Records in
89 Tasks**; bei 46 von 92 Tasks mit Ausnahme im Parser-Output gab es gar kein
Ausnahme-Signal.

Der neue Detektor `_ORPHAN_EXC` in `analysis_tools/parser_audit.py` schließt
das. Er greift nur, wenn ein Record **mit** der Ausnahme beginnt — ein
Ausnahmename mitten in einer Finding-Beschreibung zählt nicht, sonst erfände
das Audit Lücken (beide Richtungen in
`tests/test_parser_audit_orphan_exception.py`). Mit dem schärferen Katalog
stieg die Zahl der erkannten Rohmeldungen von 2 289 auf 2 417, und es
erschienen **10 Lücken**, alle im Lauf `llmsa_mwefixed_v2`.

> Ein Audit, das nie etwas findet, belegt seine eigene Schärfe nicht.

## 2. Woran sie lagen

Alle zehn hatten dieselbe Ursache — nicht in unserem Parser, sondern im
Zusammenspiel zweier fremder Komponenten.

`sb/parse_utils.py::exceptions` nimmt nach einer Traceback-Kopfzeile die
**erste nicht eingerückte Zeile** als Ausnahme. LLMSmartAudit schreibt seine
Token-Buchhaltung in denselben Ausgabestrom, und diese Zeilen sind ebenfalls
nicht eingerückt:

```
2040: Traceback (most recent call last):
2041:   File "/app/run.py", line ...              <- eingerueckt, uebersprungen
2044: num_prompt_tokens (before adjustment): 22878   <- als "die Ausnahme" genommen
2045: gap_between_send_receive: 60
 ...
2076: openai.APIStatusError: Error code: 402 - Insufficient Balance   <- die Ursache
```

Nach Zeile 2044 setzt die Schleife `traceback = False` und erreicht Zeile 2076
nie. In `result.json` stand deshalb `exception (num_prompt_tokens: 22878)`
statt der Ursache.

Zwei Klassen, keine dritte:

* **Sechs Kontextfenster-Abbrüche** — `RuntimeError: error in
  ChatAgentResponse … termination_reasons: ['max_tokens_exceeded_by_camel']`.
  Die bekannte Grenze des Werkzeugs bei großen Contracts.
* **Vier abgewiesene API-Aufrufe** — `openai.APIStatusError: Error code: 402 —
  Insufficient Balance`. Das DeepSeek-Guthaben war während des Laufs
  aufgebraucht.

In allen zehn Fällen markierte der Parser den Task korrekt als gescheitert.
Verloren ging nicht *dass* etwas schieflief, sondern **woran**.

## 3. Wie wir sie geschlossen haben

Die Reparatur liegt in `smartbugs/tools/llmsmartaudit/parser.py`
(`_repair_exception_fails`), **nicht** in `sb/parse_utils.py`. So bleibt
SmartBugs unangetastet ([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)), die Korrektur
wandert per `python -m sb.reparse` auf alle Altläufe und berührt kein anderes
Werkzeug. Zwei Regeln:

1. Ein `fails`-Eintrag, der eine Zeile der Token-Buchhaltung ist, wird
   verworfen. Die Präfixe sind namentlich aufgezählt — ein Muster für „alles,
   was wie eine Statuszeile aussieht“ würde auch echte Ausnahmen schlucken.
2. Jede Abschlusszeile am Zeilenanfang wird aufgenommen; Buchhaltungszeilen
   *innerhalb* eines Tracebacks werden übersprungen, statt die Suche zu beenden.

Abgesichert durch `tests/test_llmsa_exception_repair.py` (8 Tests), u. a.: Ein
in Prosa genannter Ausnahmename wird **kein** Fehlschlag, und die Reparatur ist
tatsächlich in `parse()` verdrahtet.

## 4. Was sich geändert hat — und was nicht

Nach `python -m sb.reparse --sarif --processes 4 results` über alle damals 48
Läufe:

| | vorher | nachher |
|---|---|---|
| Lücken im Parser-Audit | 10 | **0** |
| erkannte Rohmeldungen | 2 417 | 2 417 |
| Tasks mit geänderten `fails` | — | 10 von 266 |
| Tasks mit geändertem **Zustand** | — | **0** |
| Recall / Precision / F1 | 97/30/45 · 67/45/54 | **unverändert** |
| Errors/Fails-Bilanz (Summen) | 1272/780/486/98/… | **unverändert** |
| Findings in `eval/` | 437 | **437, inhaltlich identisch** |

Entscheidend sind die **null Zustandsänderungen**: Alle zehn Tasks galten schon
vorher als gescheitert. Die Reparatur ändert den *Text* der Meldung, nicht das
Urteil über den Task — keine Zahl der Arbeit bewegt sich, nur die Diagnose wird
genauer.

Der Katalog erfasst Records der Stufen ERROR und CRITICAL. WARNING-Records wie
`Cannot find functionB or same` (`5_Pools.sol`, `70_VaderPoolV2.sol`) liegen
außerhalb; „0 Lücken“ gilt relativ zu diesem Katalog
([`BA-VERIFIKATIONSBERICHT.md`](BA-VERIFIKATIONSBERICHT.md) 3.2).

Vorher und nachher, an einem Beispiel:

```
30_Vault.sol
  vorher : exception (String length: 109412)
  nachher: exception (RuntimeError: ... 'max_tokens_exceeded_by_camel' ...)
```

## 5. Der inhaltliche Gewinn

Die vier 402er sind genau die vier Contracts, die der Nachlauf
`llmsa_mwefixed_v2_retry` am 15.09.2026 wiederholt hat: `12_Witch`,
`25_CompositeMultiOracle`, `43_DelegatedStaking`, `62_Locke`.

Damit ist dieser Nachlauf erstmals **aus den Daten** begründet. Ohne Begründung
sieht ein Nachlauf über genau vier Contracts nach Auswahl nach Ergebnis aus;
jetzt steht in `run_meta.json`, was geschah: eine Störung der Infrastruktur,
unabhängig von Contract, Werkzeug und Modell. Die 37 Kontext-Überschreitungen
haben wir deshalb bewusst **nicht** im selben Lauf wiederholt — sie sind
inhaltlich, nicht technisch.

Der zentrale Befund des Laufs bleibt unberührt: Die vier gelten als
`no_output`, nicht als `context_exceeded`, und waren nie in die 37
eingerechnet (55 + 4 + 37 = 96).

## 6. Was davon Upstream betrifft

Der Defekt ist keine Eigenheit unseres Aufbaus. `sb/parse_utils.py::exceptions`
unterstellt, dass zwischen Traceback-Kopf und Abschlusszeile nur eingerückte
Zeilen stehen. Jedes Werkzeug, das nebenher in denselben Strom schreibt, bricht
diese Annahme, und SmartBugs meldet dann unbemerkt eine Statuszeile als
Ausnahme. Eine Upstream-Fassung müsste die letzte passende Abschlusszeile
nehmen statt der ersten nicht eingerückten. Wir haben das bewusst nur im
eigenen Parser umgesetzt, um den Messaufbau nicht an fremder Stelle zu
verändern — als Beitrag an SmartBugs wäre es der nächste naheliegende Schritt.
