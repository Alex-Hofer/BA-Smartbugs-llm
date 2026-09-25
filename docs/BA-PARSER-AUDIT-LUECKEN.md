# Der Ausnahme-Defekt im LLMSmartAudit-Parser

Wie am 21.09.2026 zehn Lücken im Parser-Audit sichtbar wurden, woran sie lagen
und wie sie geschlossen wurden. Stand 21.09.2026: **1 272 Tasks, 2 417 Rohmeldungen,
0 Lücken**; nach den Läufen vom 24.09.2026 sind es 1 501 Tasks, 2 555 Rohmeldungen,
weiterhin 0 Lücken — siehe [`parser-audit-nachher.md`](parser-audit-nachher.md).

---

## 1. Wie die Lücken sichtbar wurden

Bis zum 20.09.2026 meldete das Audit 0 Lücken. Das war keine Messung, sondern
eine Eigenschaft des Detektor-Katalogs.

Ein `TRACEBACK`-Signal entstand nur, wenn ein Log-Record **beides** enthielt:
die Zeichenkette `Traceback (most recent call last)` *und* die abschließende
`Modul.Fehler: Meldung`-Zeile. Lag die Abschlusszeile in einem eigenen Record,
sah der Katalog sie nicht — und meldete folgerichtig keine Lücke, ganz gleich,
was der Parser mit ihr gemacht hatte. Betroffen waren **132 Records in 89
Tasks**; von 92 Tasks, deren Parser-Ausgabe eine Ausnahme nennt, erzeugte das
Audit bei **46** überhaupt kein Ausnahme-Signal.

Der Detektor `_ORPHAN_EXC` in `analysis_tools/parser_audit.py` schließt diese
Stelle. Er greift nur, wenn ein Record **mit** der Ausnahme beginnt: ein
Ausnahmename mitten in Prosa oder in einer Finding-Beschreibung zählt nicht,
sonst erfände das Audit Lücken. Beide Richtungen sind in
`tests/test_parser_audit_orphan_exception.py` festgehalten.

Mit dem schärferen Katalog stieg die Zahl der erkannten Rohmeldungen von 2 289
auf 2 417 — und es erschienen **10 Lücken**, alle im Lauf `llmsa_mwefixed_v2`.

> Ein Audit, das nie etwas findet, belegt seine eigene Schärfe nicht. Erst der
> strengere Katalog machte die Aussage prüfbar.

## 2. Woran sie lagen

Alle zehn hatten dieselbe Ursache, und sie liegt nicht im eigenen Parser,
sondern im Zusammenspiel zweier Fremdkomponenten.

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

## 3. Wie sie geschlossen wurden

Die Reparatur liegt in `smartbugs/tools/llmsmartaudit/parser.py`
(`_repair_exception_fails`), **nicht** in `sb/parse_utils.py`. Upstream bleibt
damit unangetastet — das in `BA-EIGENANTEIL.md` ausgewiesene Prinzip hält, die
Korrektur wandert mit `python -m sb.reparse` auf alle Altläufe und berührt
keines der übrigen 30+ SmartBugs-Werkzeuge.

Zwei Regeln:

1. Ein `fails`-Eintrag, dessen Text eine Zeile der Token-Buchhaltung ist, wird
   verworfen. Die betroffenen Präfixe sind namentlich aufgezählt, nicht per
   Faustregel erkannt — ein Muster, das „alles, was wie eine Statuszeile
   aussieht" abdeckt, verschluckte auch echte Ausnahmen.
2. Jede Abschlusszeile am Zeilenanfang wird aufgenommen. Zeilen der
   Token-Buchhaltung *innerhalb* eines Tracebacks werden übersprungen, statt
   die Suche zu beenden.

Abgesichert durch `tests/test_llmsa_exception_repair.py` (8 Tests), darunter
zwei, die den Eingriff gegen die naheliegenden Fehlschläge festnageln: dass
ein in Prosa genannter Ausnahmename **kein** Fehlschlag wird, und dass die
Reparatur tatsächlich in `parse()` verdrahtet ist und nicht bloß definiert.

## 4. Was sich dadurch geändert hat — und was nicht

Nach `python -m sb.reparse --sarif --processes 4 results` über alle damals 48 Läufe (heute 51, unverändert 0 Lücken):

| | vorher | nachher |
|---|---|---|
| Lücken im Parser-Audit | 10 | **0** |
| erkannte Rohmeldungen | 2 417 | 2 417 |
| Tasks mit geänderten `fails` | — | 10 von 266 |
| Tasks mit geändertem **Zustand** | — | **0** |
| Recall / Precision / F1 | 97/30/45 · 67/45/54 | **unverändert** |
| Errors/Fails-Bilanz (Summen) | 1272/780/486/98/… | **unverändert** |
| Findings in `eval/` | 437 | **437, inhaltlich identisch** |

**Null Zustandsänderungen** ist der entscheidende Wert: Alle zehn Tasks galten
schon vorher als gescheitert. Die Reparatur ersetzt den *Text* der
Fehlermeldung, nicht das Urteil über den Task. Deshalb bewegt sich keine Zahl
der Arbeit; was sich ändert, ist allein die Diagnosetiefe.

Der Katalog erfasst Log-Records der Stufen ERROR und CRITICAL. WARNING-Records
wie `Cannot find functionB or same` (`5_Pools.sol` und `70_VaderPoolV2.sol`
im Lauf `curated_mwefixed_live`) liegen weiterhin außerhalb; „0 Lücken“ gilt
relativ zu diesem Katalog (`BA-VERIFIKATIONSBERICHT.md` 3.2).

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

Damit ist dieser Nachlauf erstmals **aus den Daten heraus** begründet. Bisher
stand dort nur, er habe „vier Tasks ersetzt, die der Hauptlauf nicht
entschieden hatte" — und ein Nachlauf über genau vier Contracts sieht ohne
Begründung nach Auswahl nach Ergebnis aus. Jetzt steht in `run_meta.json`, was
tatsächlich geschah: eine Störung der Infrastruktur, die mit Contract,
Werkzeug und Modell nichts zu tun hat. Die 37 Kontext-Überschreitungen sind
deshalb bewusst **nicht** wiederholt worden — sie sind inhaltlich, nicht
technisch.

Der zentrale Befund des Laufs bleibt unberührt: Die vier gelten als
`no_output`, nicht als `context_exceeded`, und waren nie in die 37
eingerechnet (55 + 4 + 37 = 96).

## 6. Was davon Upstream betrifft

Der Defekt ist keine Eigenheit dieses Aufbaus. `sb/parse_utils.py::exceptions`
unterstellt, dass zwischen Traceback-Kopf und Abschlusszeile ausschließlich
eingerückte Rahmen stehen. Jedes Werkzeug, das nebenher auf denselben Strom
protokolliert, bricht diese Annahme — und SmartBugs meldet dann eine beliebige
Statuszeile als Ausnahme, ohne dass es auffällt.

Eine upstream-taugliche Fassung müsste die letzte passende Abschlusszeile
wählen statt der ersten nicht eingerückten Zeile. Das ist der naheliegendste
eigene Beitrag an SmartBugs neben dem `env:`-Mechanismus; hier wurde er
bewusst nur im eigenen Tool-Parser umgesetzt, um den Messaufbau nicht an einer
fremden Stelle zu verändern.
