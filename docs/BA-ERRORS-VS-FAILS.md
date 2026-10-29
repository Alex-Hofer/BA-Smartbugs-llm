# Errors und Fails in SmartBugs: Bedeutung und Herleitung

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

SmartBugs schreibt in jede `result.json` vier Gruppen: `findings`, `infos`,
`errors` und `fails`. Die letzten beiden werden oft in einen Topf geworfen,
bedeuten aber Verschiedenes — und für unsere Auswertung ist der Unterschied
entscheidend. Deshalb leiten wir ihn aus dem Code her.

## Begriffe

Ein Scanner stellt keinen Fehler fest, er äußert einen Verdacht. Wir halten das
sprachlich auseinander:

| Wer spricht | Wort | Beispiel |
|---|---|---|
| ein **Werkzeug** über einen Contract | **Finding**, Verdachtsfall, Kandidat | „GPTScan meldet 77 Findings auf 40 Contracts“ |
| **Ground Truth oder Literatur** | Schwachstelle, Fehler | „curated labelt eine Schwachstelle je Contract“ |
| die **Ausführung** eines Werkzeugs | Fehler | „solc bricht mit einem Compile-Fehler ab“ |

Erst der Abgleich mit der Ground Truth macht ein Finding zum True oder False
Positive. Um die dritte Zeile — Fehler des *Werkzeugs*, nicht des Contracts —
geht es im Rest dieses Dokuments.

Die Feldnamen `findings`, `infos`, `errors` und `fails` lassen wir unverändert;
sonst wäre unsere Ausgabe nicht mehr mit SmartBugs kompatibel. Deshalb heißt
auch `analysis_tools/errors_fails_report.py` so.

## Die Quelle: `errors_fails()`

Maßgeblich ist `smartbugs/sb/parse_utils.py:66-90`. Der Kommentar im Original:

```python
errors = set()  # errors detected and handled by the tool
fails  = set()  # exceptions not caught by the tool, or outside events leading to abortion
```

| Klasse | Bedeutung |
|---|---|
| **error** | Das Werkzeug hat das Problem bemerkt, behandelt und weitergearbeitet. Ein Ergebnis existiert, ist aber womöglich unvollständig. |
| **fail** | Eine Exception ist entkommen, oder der Lauf wurde von außen abgebrochen. Ein Ergebnis gibt es nicht. |

Beides sind **Mengen**: Zwei gleiche Meldungen in einem Task zählen einmal. Die
Spalten in `results2csv` zählen also *verschiedene Meldungen*, nicht
*Vorkommen*.

### Einordnung nach Exit-Code (`parse_utils.py:71-85`)

| Exit-Code | Klasse | Meldung |
|---|---|---|
| `None` | fail | `DOCKER_TIMEOUT` — SmartBugs hat den Container abgebrochen |
| `0` | — | nichts |
| `127` | fail | Dateiname passt zu keinem Contract (Option `main`) |
| `125`, `126`, `137`, `139`, `143` | fail | `DOCKER_*`, u. a. `DOCKER_KILL_OOM`, `DOCKER_SEGV` |
| `128`–`192` | fail | `DOCKER_RECEIVED_SIGNAL_<n>` |
| alles andere | **error** | `EXIT_CODE_<n>` |

Wichtig ist die letzte Zeile: Ein beliebiger Exit-Code ≠ 0 ist ein *error*, kein
*fail*, weil ein Werkzeug den Exit-Code als Ergebniskanal nutzen darf
(Kommentar in `parse_utils.py:84`). Slither tut genau das und liefert 255,
sobald es etwas findet; sein Parser verwirft den Code deshalb
(`errors.discard("EXIT_CODE_255")`). Daher gelten die 140 Slither-Tasks mit
Exit 255 als sauber.

### Einordnung nach Log-Inhalt (`parse_utils.py:86-89`)

```python
if log:
    fails.update(exceptions(log))
elif log_expected and not fails:
    fails.add("execution failed")
```

`exceptions()` erkennt Python-Tracebacks (eine Zeile, die auf
`Traceback (most recent call last):` **endet**; danach gilt die erste *nicht
eingerückte* Zeile als Exception), außerdem Shell-Abbrüche, Java-Exceptions und
Rust-Panics. Alles davon landet in **fails** — die Annahme: Ein Traceback im Log
heißt, die Exception ist entkommen.

## Warum GPTScan diese Annahme bricht

GPTScan loggt über `rich`, das jeden Eintrag hart umbricht und rechts eine
`quelle.py:ZEILE`-Marke anhängt:

```
[07:13:59] Traceback (most recent call last):                       tasks.py:177
             File
           "/usr/local/lib/python3.10/site-packages/crytic_compile/
           platform/solc.py", line 575, in _run_solc
```

Für `exceptions()` ist das unsichtbar: Die Zeile endet nicht auf
`Traceback (most recent call last):`, und alle Folgezeilen sind eingerückt.

Dazu kommt: GPTScan **fängt** ein gescheitertes Compilat ab, überspringt die
statische Stufe, endet mit Exit 0 und schreibt `{"success": true, "results": []}`.
Vor unserer Parser-Überarbeitung (02.08.2026) war ein nicht übersetzbarer
Contract damit von einem sauberen nicht zu unterscheiden — betroffen waren
**246 Tasks** (98 Contracts in 9 Läufen). Der Hauptlauf `curated_v1_20260705`
nicht: Dort ist kein Compilat gescheitert.

### Unsere Lösung

`smartbugs/tools/gptscan/parser.py` setzt die `rich`-Umbrüche wieder zusammen
und nutzt das Rendering als Merkmal:

| Traceback im Log | Klasse | Begründung |
|---|---|---|
| von `rich` gerendert (Zeitstempel bzw. Quellmarke) | **error** | GPTScans eigener Logger hat ihn geschrieben, also abgefangen |
| roh auf stderr | **fail** | dem Prozess entkommen |

Das Kriterium haben wir am Material abgelesen: Die 44 Tasks mit Exit 1 tragen
ihren Traceback roh auf stderr, jedes abgefangene Compile-Problem läuft durch
`rich`.

## Was *kein* Fehler ist

1. **`vul_before_static > vul_after_static`** in `GPTSCAN_META` — GPTScans
   gewollter False-Positive-Filter, bei etwa der Hälfte der Contracts aktiv. Der
   Parser zeigt ihn als `info`.
2. **Reine solc-Warnungen.** Sie halten die Analyse nicht auf. Aber Vorsicht:
   Älteres solc schreibt mit `--combined-json` Warnungen nach stdout, was das
   JSON zerstört. Ob das Compilat gescheitert ist, entscheidet deshalb die
   geworfene Exception, nicht das Wort „Warning“.
3. **Slithers Exit-Code 255** (siehe oben).

## Ursache und Folgefehler

Ein gescheitertes Compilat zieht Folgefehler nach sich, etwa
`TypeError: 'NoneType' object is not subscriptable` oder
`UnboundLocalError: local variable 'match_flag' referenced before assignment`.
Sie benennen das Symptom, nicht die Ursache. **Wir geben sie trotzdem
unverändert aus** und ordnen sie nur in einer eigenen Spalte von
`errors_fails_report.py` ein:

| Klassifikation | Bedeutung |
|---|---|
| `root_cause` | Meldung betrifft das Compilat selbst |
| `consequence` | jede andere Meldung in einem Task mit gescheitertem Compilat |
| `independent` | Contract wurde übersetzt; die Meldung steht für sich |

Grundlage ist der `info`-Eintrag des Parsers: „GPTScan analysis degraded: the
contract did not compile, so the static confirmation stage never ran. Any 'no
findings' result for this contract is inconclusive, not clean.“

## Folge für die Auswertung

Ein Task ohne Findings ist nur dann *sauber*, wenn er weder errors noch fails
trägt **und** sein Contract übersetzt wurde; die Spalte *nicht übersetzt* in
[`errors-fails.md`](errors-fails.md) weist diese Tasks getrennt aus.
`evaluate_curated.py` wertet nur `findings` aus — Recall und Precision von
`curated_v1_20260705` haben sich durch die Parser-Überarbeitung nicht geändert
([`parser-fix-vorher-nachher.md`](parser-fix-vorher-nachher.md)).

## Werkzeuge

```powershell
# Bilanz über alle Läufe
python analysis_tools\errors_fails_report.py --md docs\errors-fails.md --csv docs\errors-fails.csv

# ein einzelner Lauf
python analysis_tools\errors_fails_report.py smartbugs\results\gptscan\curated_mwefixed_live

# geht Rohsignal im Parser verloren?
python analysis_tools\parser_audit.py
```

`run_curated.ps1` ruft den Report nach jedem Massenlauf selbst auf.
