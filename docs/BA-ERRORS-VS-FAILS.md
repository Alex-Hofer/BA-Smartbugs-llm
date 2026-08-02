# Errors und Fails in SmartBugs: Semantik und Herleitung

SmartBugs schreibt in jede `result.json` vier Gruppen: `findings`, `infos`,
`errors` und `fails`. Die beiden letzten werden oft in einen Topf geworfen. Sie
bedeuten Verschiedenes, und für die Auswertung dieses Benchmarks ist der
Unterschied entscheidend. Dieses Dokument leitet die Trennung aus dem Code her,
statt sie zu behaupten.

## Die Quelle: `errors_fails()`

Maßgeblich ist `smartbugs/sb/parse_utils.py:66-90`. Der Kommentar dort im
Original benennt die Absicht:

```python
errors = set()  # errors detected and handled by the tool
fails  = set()  # exceptions not caught by the tool, or outside events leading to abortion
```

Daraus die Definition, die in dieser Arbeit durchgehend verwendet wird:

| Klasse | Bedeutung |
|---|---|
| **error** | Das Werkzeug hat das Problem bemerkt, behandelt und weitergearbeitet. Das Ergebnis existiert, ist aber möglicherweise unvollständig. |
| **fail** | Eine Exception ist dem Werkzeug entkommen, oder der Lauf wurde von außen abgebrochen. Das Ergebnis ist nicht zustande gekommen. |

Eine dritte, oft übersehene Eigenschaft: **beides sind Mengen** (`set`). Zwei
identische Meldungen in einem Task erscheinen nur einmal. Die Spalten
`errors`/`fails` in `results2csv` zählen also *verschiedene Meldungen*, nicht
*Vorkommen*.

## Was `errors_fails()` konkret einordnet

### Nach Exit-Code

`parse_utils.py:71-85`:

| Exit-Code | Klasse | Meldung |
|---|---|---|
| `None` | fail | `DOCKER_TIMEOUT` — SmartBugs hat den Container abgebrochen |
| `0` | — | nichts |
| `127` | fail | Dateiname passte zu keinem Contract (Option `main`) |
| `125`, `126`, `137`, `139`, `143` | fail | `DOCKER_*` aus der Tabelle `DOCKER_CODES` (`parse_utils.py:8-15`), u. a. `DOCKER_KILL_OOM` und `DOCKER_SEGV` |
| `128`–`192` | fail | `DOCKER_RECEIVED_SIGNAL_<n>` |
| alles andere | **error** | `EXIT_CODE_<n>` |

Der letzte Fall ist die wichtige Feinheit: ein beliebiger Exit-Code ungleich
null gilt als *error*, nicht als *fail*. Die Begründung steht als Kommentar im
Upstream-Code (`parse_utils.py:84`): ein Werkzeug darf einen Exit-Code als
Ergebniskanal benutzen. Genau das tut slither — es liefert 255, sobald es etwas
gefunden hat. `smartbugs/tools/slither-0.11.3/parser.py:126` verwirft den Code
deshalb ausdrücklich:

```python
errors.discard("EXIT_CODE_255")  # this code seems to be returned in any case
```

Das erklärt die 140 Tasks im slither-Lauf, die trotz Exit-Code 255 als sauber
gelten. Es ist kein Fehler, sondern gewollt.

### Nach Log-Inhalt

`parse_utils.py:86-89` ergänzt anschließend:

```python
if log:
    fails.update(exceptions(log))
elif log_expected and not fails:
    fails.add("execution failed")
```

`exceptions()` (`parse_utils.py:40-54`) erkennt

* Python-Tracebacks — eine Zeile, die auf `Traceback (most recent call last):`
  **endet**, danach gilt die erste *nicht eingerückte* Zeile als die Exception;
* Shell-Abbrüche (`Segmentation fault`, `Killed`), Java-Exceptions und
  Rust-Panics über die Muster in `parse_utils.py:32-37`.

Alles, was `exceptions()` findet, landet in **fails**. Die Annahme dahinter: ein
Traceback im Log heißt, die Exception ist entkommen.

## Warum GPTScan diese Annahme bricht

GPTScan loggt über `rich`. Das rendert jeden Log-Record als hart umbrochenen,
auf Konsolenbreite aufgefüllten Block und setzt rechtsbündig eine
`quelle.py:ZEILE`-Marke an die erste Zeile:

```
[07:13:59] Traceback (most recent call last):                       tasks.py:177
             File
           "/usr/local/lib/python3.10/site-packages/crytic_compile/
           platform/solc.py", line 575, in _run_solc
```

Für `exceptions()` ist das unsichtbar: Die erste Zeile *endet* nicht auf
`Traceback (most recent call last):`, und jede Folgezeile ist eingerückt, so
dass die Abbruchbedingung nie greift.

Erschwerend kommt hinzu, dass GPTScan ein gescheitertes Compilat **abfängt**:
Ohne Falcon-IR wird die Static-Bestätigungsstufe übersprungen, der Lauf endet
mit Exit-Code 0, und `output.json` enthält `{"success": true, "results": []}`.
Vor der Parser-Überarbeitung vom 2026-08-02 war ein nicht übersetzbarer Contract
damit von einem sauberen nicht zu unterscheiden — über alle 19 Läufe betraf das
**246 Tasks**, entsprechend **98 verschiedenen Contracts in 9 Läufen**. Der
Hauptlauf `curated_v1_20260705` (143 Contracts) ist davon **nicht** betroffen:
dort ist kein einziges Compilat gescheitert.

### Die Auflösung

`smartbugs/tools/gptscan/parser.py` entzerrt die `rich`-Umbrüche und benutzt das
Rendering selbst als Unterscheidungsmerkmal:

| Traceback im Log | Klasse | Begründung |
|---|---|---|
| `rich`-gerendert (Zeitstempel bzw. Quellmarke vorhanden) | **error** | GPTScans eigener Logger hat es geschrieben, also hat GPTScan es abgefangen |
| roh auf stderr | **fail** | dem Prozess entkommen; bleibt bei `errors_fails()` |

Das Kriterium ist nicht erfunden, sondern am Material abgelesen: die 44 Tasks
mit Exit-Code 1 tragen ihr Traceback roh auf stderr, während jedes abgefangene
Compile-Problem durch den `rich`-Logger läuft.

## Was ausdrücklich *kein* Fehler ist

Drei Beobachtungen sehen nach Defekten aus und sind keine. Weder das Audit
(`analysis_tools/parser_audit.py`) noch die Parser werten sie als Fehler:

1. **`vul_before_static > vul_after_static`** in `GPTSCAN_META`. Das ist
   GPTScans Static-Bestätigungsstufe, die LLM-Kandidaten verwirft — der
   bestimmungsgemäße False-Positive-Filter. Er greift bei etwa der Hälfte aller
   Live-Contracts. Der Parser macht ihn als `info` sichtbar, damit er nicht mit
   einem Defekt verwechselt wird.
2. **Reine solc-Warnungen** in den `CryticCompile`-Records. Warnungen halten die
   Analyse nicht auf. Umgekehrt gilt allerdings *nicht*, dass eine Warnung
   harmlos wäre: mit `--combined-json` schreibt älteres solc Warnungen nach
   stdout, was das JSON zerstört und crytic-compile abbrechen lässt. Ob das
   Compilat gescheitert ist, entscheidet daher die geworfene Exception, nicht
   das Wort „Warning".
3. **slithers Exit-Code 255** (siehe oben).

## Ursache und Folgefehler

Ein gescheitertes Compilat zieht eine Kette von Folgefehlern nach sich: ohne
Falcon-IR laufen die Codepfade der Static-Stufe ins Leere und werfen
`TypeError: 'NoneType' object is not subscriptable` oder
`UnboundLocalError: local variable 'match_flag' referenced before assignment`.
Diese Meldungen sind irreführend — sie benennen ein Symptom, nicht die Ursache.

**Sie werden trotzdem unverändert ausgegeben.** Kein Filtern, kein Umschreiben.
Die Einordnung geschieht in einer eigenen Spalte, die
`analysis_tools/errors_fails_report.py` erzeugt:

| Klassifikation | Bedeutung |
|---|---|
| `root_cause` | Die Meldung benennt das Compilat selbst |
| `consequence` | Jede andere Meldung in einem Task, dessen Compilat gescheitert ist |
| `independent` | Der Contract wurde übersetzt; die Meldung steht für sich |

Die Grundlage dafür liefert der Parser als `info`:
„GPTScan analysis degraded: the contract did not compile, so the static
confirmation stage never ran. Any 'no findings' result for this contract is
inconclusive, not clean."

## Konsequenz für die Auswertung

Ein Task ohne Findings ist nur dann *sauber*, wenn er auch weder Errors noch
Fails trägt **und** sein Contract übersetzt wurde. Die Spalte
*nicht übersetzt* in `docs/errors-fails.md` weist diese Tasks getrennt aus.
`evaluate_curated.py` wertet ausschließlich die Spalte `findings` aus und bleibt
von der Trennung unberührt — die Recall/Precision-Werte des Hauptlaufs
`curated_v1_20260705` haben sich durch die Parser-Überarbeitung nicht geändert
(Beleg: `docs/parser-fix-vorher-nachher.md`).

## Werkzeuge

```powershell
# Bilanz über alle Läufe, als Markdown und CSV
python analysis_tools\errors_fails_report.py --md docs\errors-fails.md --csv docs\errors-fails.csv

# Nur ein Lauf
python analysis_tools\errors_fails_report.py smartbugs\results\gptscan\curated_mwefixed_live

# Prüfen, dass kein Rohsignal im Parser verlorengeht
python analysis_tools\parser_audit.py
```

`run_curated.ps1` ruft den Report am Ende jedes Massenlaufs automatisch auf.
