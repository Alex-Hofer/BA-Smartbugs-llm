# Update-Bericht zum Arbeitsstand

**Bachelorarbeit: KI-gestützte Smart-Contract-Scanner im SmartBugs-Framework**

| | |
|---|---|
| Berichtszeitraum | Juli 2026 (letzter Bericht) bis 3. August 2026 |
| Bezugsdokument | Kontextpapier zum Projektstand Juli 2026, abgeleitet aus dem Foliendeck `BA-Arbeitsfortschritt.pptx`; beides am 25.09.2026 beziehungsweise früher aus dem Repository entfernt, die Prioritäten stehen in Abschnitt 2 |
| Gegenstand | Commits `f85946e` … `a2be0f3` (10 Commits), Zweig `main`, auf `origin` gespiegelt |
| Verfasst am | 2026-08-03 |

> **Nachtrag 25.09.2026.** Datierter Bericht. Überholt sind: die Zählung der
> Eingriffe in SmartBugs (Abschnitte 6.3, 6.4 und 11) gegen den Tag `v2.1.1`;
> gegen den tatsächlich geklonten Stand `7ddaf6c` sind es 7 Blöcke in 2
> Dateien (`BA-EIGENANTEIL.md` 2.1). Von den offenen Punkten in Abschnitt 10
> sind erledigt: die ANTLR-Frage (`BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.7), die
> Evaluation des Hauptlaufs (`../eval/curated_v1_20260705__metriken.md`), der
> GPTScan-Massenlauf nach der Parser-Reparatur (`gptscan_mwefixed_v2_main`,
> 15.08.2026), die Kostenmessung für neue Läufe über den Kontostand
> (`BA-BETRIEB.md` 3) und der Eintrag zu Fehler #4 im Protokoll. Offen bleiben
> die Ursache des Static-Absturzes auf 35 von 96 Contracts, die Streuung über
> mehr als zwei Läufe und der WARNING-Blindfleck.

---

## 0. Vorbemerkung: Zweck, Aufbau und Belegprinzip

Dieser Bericht schreibt den Stand vom Juli 2026 fort. Er ist nach vier
**Arbeitspaketen** (AP1–AP4) gegliedert, die aus den vier Leitfragen des
Auftraggebers hervorgehen. Jedes Arbeitspaket folgt derselben Gliederung:
*Fragestellung — Vorgehen — Ergebnis — Belege — Gültigkeitsgrenzen*. Abschnitt 8
beantwortet die vier Leitfragen zusätzlich in kompakter Form.

Es gilt durchgehend dasselbe Belegprinzip wie in den übrigen Projektdokumenten:

1. **Jede quantitative Aussage ist auf ein reproduzierbares Kommando oder eine
   Datei mit Zeilenangabe zurückgeführt.** Aussagen ohne Beleg sind als solche
   gekennzeichnet.
2. **Negative Befunde werden mitberichtet.** Blinde Flecken, Gegenbeispiele und
   bewusst offen gelassene Punkte stehen in Abschnitt 9, nicht in einer Fußnote.
3. **Es wird zwischen *heute nachgerechnet* und *dokumentiert übernommen*
   unterschieden.** Welche Zahlen zu welcher Klasse gehören, weist Abschnitt 11
   einzeln aus.

Der Bericht enthält **keine neuen Messwerte für die Bachelorarbeit**. Alle
Eingriffe des Berichtszeitraums sind so ausgelegt, dass die im Juli erhobenen
Messgrößen unverändert bleiben; der Nachweis dafür ist Gegenstand von
Abschnitt 5.4.

---

## 1. Zusammenfassung

Im Berichtszeitraum wurde der Schwerpunkt von der *Erhebung* auf die
**Belastbarkeit der Erhebung** verlagert. Drei Ergebnisse tragen den Bericht:

1. **Der im Juli benannte P0-Blocker ist aufgelöst.** Der GPTScan-Zielkorpus war
   zu 95/96 nicht kompilierbar; nach der Rekonstruktion kompilieren 96/96 nativ
   und 94/96 in GPTScans eigener Analyse-Toolchain. Die statische
   Bestätigungsstufe — der methodische Kernbeitrag des Werkzeugs — ist damit
   erstmals auf diesem Korpus aktiv.
2. **Ein stiller Datenverlust in der Ergebnisverarbeitung wurde gefunden und
   beseitigt.** Von 1464 Rohmeldungen erreichten 1368 die Ergebnisdateien nicht;
   sie gingen ausnahmslos im GPTScan-Parser verloren. Ein nicht übersetzbarer
   Contract war dadurch von einem sauber analysierten nicht zu unterscheiden.
   Nach der Reparatur: 0 Lücken über alle 930 Tasks.
3. **Die Messwerte der Arbeit sind davon nachweislich unberührt.** Das Feld
   `findings` ist in allen 930 Tasks identisch geblieben; sämtliche Änderungen
   sind additiv (`errors`, `infos`). Recall, Precision und F1 können sich
   folglich nicht verschoben haben.

Hinzu kommen die Herstellung der Weitergabefähigkeit des Repositories
(Geheimnisschutz, Lizenzlage, Eigenanteil-Nachweis) und ein Demonstrationslauf
beider Werkzeuge, der einen zuvor unbekannten, ergebnisvernichtenden Fehler in
SmartBugs zutage gefördert hat.

---

## 2. Fortschreibung gegenüber dem Stand Juli 2026

Die Prioritätenliste des Kontextpapiers vom Juli 2026 (P0 bis P2) im
Soll-Ist-Vergleich:

| Prio | Punkt (Juli 2026) | Stand August 2026 |
|---|---|---|
| **P0** | GPTScan-Kompilierung stabilisieren | **erledigt.** Korpus `mwevariety_fixed`: 96/96 nativ, 94/96 in der Toolchain (`docs/BA-KORPUS-REPARATUR.md`, Durchführung 21.07.2026) |
| **P0** | Statische Bestätigungsstufe reaktivieren | **erledigt, mit Einschränkung.** Die Stufe läuft; sie stürzt jedoch auf **35 von 96** übersetzbaren Contracts mit `Static analysis failed: Invalid args` ab. Das war vor der Parser-Reparatur unsichtbar |
| **P1** | GPTScan-Massenlauf nachziehen | **teilweise.** `curated_mwefixed_live` (96 Contracts) liegt vor; ein Massenlauf auf dem reparierten Korpus *nach* der Parser-Reparatur steht aus |
| **P2** | Evaluation beginnen | **offen.** `evaluate_curated.py` liefert Recall/Precision/F1 je DASP-Kategorie; die Auswertung des Hauptlaufs ist nicht Gegenstand dieses Berichts |

Ergänzend zu Abschnitt 7 des Juli-Dokuments („Nicht im Deck belegt"): Die dort
als ungeklärt geführte **Reproduzierbarkeit** ist inzwischen negativ beantwortet
— die Werkzeugausgabe ist nicht deterministisch (Abschnitt 7.2). Für **Kosten
und Laufzeit** liegen erstmals gemessene Werte vor, allerdings nur für GPTScan;
LLMSmartAudit weist keine Kosten aus.

---

## 3. AP1 — Fehlerklassifikation: Errors gegenüber Fails

### 3.1 Fragestellung

SmartBugs schreibt in jede `result.json` die Gruppen `findings`, `infos`,
`errors` und `fails`. Errors und Fails wurden in der bisherigen Auswertung
gemeinsam geführt. Zu klären war, ob die Unterscheidung eine inhaltliche
Bedeutung trägt, und falls ja, wie sie so ausgewiesen werden kann, dass sie ohne
Rückgriff auf die Rohdaten interpretierbar ist.

### 3.2 Vorgehen

Die Semantik wurde **aus dem Quelltext hergeleitet, nicht gesetzt**. Maßgeblich
ist `smartbugs/sb/parse_utils.py:66-90` (`errors_fails()`), dessen
Upstream-Kommentar die Absicht benennt:

```python
errors = set()  # errors detected and handled by the tool
fails  = set()  # exceptions not caught by the tool, or outside events leading to abortion
```

Daraus die im gesamten Projekt verwendete Definition:

| Klasse | Bedeutung |
|---|---|
| **error** | Das Werkzeug hat das Problem bemerkt, behandelt und weitergearbeitet. Ein Ergebnis liegt vor, möglicherweise unvollständig. |
| **fail** | Eine Exception ist dem Werkzeug entkommen, oder der Lauf wurde von außen abgebrochen. Ein Ergebnis liegt nicht vor. |

Drei Eigenschaften der Implementierung sind für die Interpretation wesentlich
und in `docs/BA-ERRORS-VS-FAILS.md` einzeln belegt:

* **Beides sind Mengen (`set`).** Die Spalten `errors`/`fails` zählen
  *verschiedene Meldungen*, nicht *Vorkommen*.
* **Ein beliebiger Exit-Code ≠ 0 gilt als *error*, nicht als *fail*.** Ein
  Werkzeug darf den Exit-Code als Ergebniskanal verwenden. Slither tut genau
  das und liefert 255, sobald es etwas gefunden hat; sein Parser verwirft den
  Code deshalb ausdrücklich (`smartbugs/tools/slither-0.11.3/parser.py:126`).
  Das erklärt die 140 slither-Tasks, die trotz Exit-Code 255 als sauber gelten.
* **Nur bestimmte Exit-Codes sind *fails*** — `None` (Docker-Timeout), 127,
  die Docker-Codes 125/126/137/139/143 sowie 128–192
  (`parse_utils.py:8-15`, `:71-85`).

Für die Ausgabe entstand `analysis_tools/errors_fails_report.py`. Es arbeitet
über beliebige Ergebnisordner und gibt je Lauf und Werkzeug aus: Tasks, sauber
durchgelaufene Tasks, Tasks mit Errors, Tasks mit Fails, Anzahl der Errors,
Anzahl der Fails, Tasks mit gescheitertem Compilat — dazu jede Meldung **im
Wortlaut** mit den betroffenen Contracts. Ausgabeformate sind Markdown
(übernahmefertig) und CSV (maschinenlesbar).

### 3.3 Ergebnis

Bilanz über alle 19 Ergebnisordner (`docs/errors-fails.md`):

| Kennzahl | Wert |
|---|---:|
| Tasks gesamt | 930 |
| davon sauber (weder Error noch Fail) | 586 |
| Tasks mit Errors | 344 |
| Tasks mit Fails | 50 |
| Tasks mit gescheitertem Compilat | 246 |
| verschiedene Errors | 1427 |
| verschiedene Fails | 91 |

**Zur Lesart:** Die vier Task-Zahlen sind **keine disjunkten Klassen** und
dürfen nicht addiert werden. Es gilt 586 + 344 = 930; die 50 Tasks mit Fails
sind vollständig eine Teilmenge der 344 mit Errors (nachgerechnet: 50 Tasks mit
beidem, 0 mit Fails ohne Errors), und die 246 nicht übersetzten verteilen sich
über beide Gruppen.

Die Verteilung ist stark inhomogen und selbst ein Befund: Der Hauptlauf
`curated_gptscan_v1_20260705` trägt 2 von 143 Tasks mit Errors, der Lauf
`curated_gptscan_mwe_20260706` dagegen 95 von 96 — Letzterer ist der Lauf auf
dem unreparierten Korpus. LLMSmartAudit weist über 147 Tasks **null** Errors und
Fails auf, mit Ausnahme eines Stub-Laufs.

### 3.4 Belege

* Herleitung mit Zeilenverweisen: `docs/BA-ERRORS-VS-FAILS.md`
* Erzeugte Bilanz: `docs/errors-fails.md`, `docs/errors-fails.csv`
* Werkzeug: `analysis_tools/errors_fails_report.py`
* Alle neun Zeilenverweise der Herleitung wurden unabhängig am Code
  nachgeschlagen und bestätigt (`docs/BA-VERIFIKATIONSBERICHT.md`, Abschnitt 2.4)

### 3.5 Gültigkeitsgrenzen

Die Zuordnung *roh auf stderr ⇒ fail* gilt für **638 von 640** GPTScan-Tasks,
nicht ausnahmslos: `16_Liquidation.sol` trägt in zwei Läufen ein rohes
Traceback, beendet sich aber mit Exit-Code 0 und liefert ein — degradiertes —
Ergebnis. Die Fehlklassifikation entsteht upstream in
`sb.parse_utils.exceptions()`, nicht im überarbeiteten Parser. Die für die
Reparatur entscheidende Gegenrichtung (`rich`-gerendert ⇒ vom Werkzeug
abgefangen) ist dagegen **ausnahmslos** bestätigt: kein einziger Fall, in dem
ein `rich`-gerendertes Traceback den Prozess doch beendet hätte.

---

## 4. AP2 — Vollständigkeit der Signalverarbeitung im Parser

AP1 und AP2 gehören sachlich zusammen: Eine Trennung von Errors und Fails ist
nur so viel wert wie die Vollständigkeit der Menge, über der sie operiert.

### 4.1 Fragestellung

Erreicht jede Meldung, die ein Werkzeug im Rohmaterial hinterlässt
(`result.log`, `result.tar`, Exit-Code), die Ergebnisdatei `result.json`? Oder
geht auf dem Weg durch den toolspezifischen Parser etwas verloren?

### 4.2 Vorgehen

Es entstand ein **unabhängiges Audit-Werkzeug**, `analysis_tools/parser_audit.py`.
Zwei Entwurfsentscheidungen sind methodisch entscheidend:

* **Eigene Detektoren, kein geteilter Code mit den Parsern.** Ein Audit, das die
  Sicht des Parsers wiederverwendet, kann nur bestätigen, dass der Parser mit
  sich selbst übereinstimmt. Die Detektoren lesen ausschließlich Rohmaterial.
* **Erkennung auf whitespace-freiem Text**, damit Treffer immun gegen die
  Zeilenumbrüche sind, die die Bibliothek `rich` einfügt.

Während der Entwicklung wurden drei Fehlklassifikationen im Detektor selbst
gefunden und korrigiert, bevor sie in einen Bericht gelangten: slithers
gutartiger Exit-Code 255, die Untauglichkeit von `Warning:`/`Error:` als
Compile-Kriterium, und `ContractSolcParsing` als Nicht-Compile-Fehler. Alle
drei sind in `docs/BA-VERIFIKATIONSBERICHT.md`, Abschnitt 2.5, im Feld
gegengeprüft.

### 4.3 Ergebnis

**Vor der Reparatur gingen 1368 von 1464 Rohmeldungen verloren — ausnahmslos
alle im GPTScan-Parser.** slither und LLMSmartAudit: keine Lücke.

| Signaltyp | verlorene Meldungen |
|---|---:|
| `LOG_ERROR` | 708 |
| `TRACEBACK` | 334 |
| `COMPILE_ERROR` | 246 |
| `OUTPUT_UNSUCCESSFUL` | 44 |
| `STATIC_SKIPPED` | 36 |

**Die mechanische Ursache** ist präzise benennbar: `parse_utils.exceptions()`
sucht eine Zeile, die auf `Traceback (most recent call last):` *endet*, gefolgt
von einer *nicht eingerückten* Zeile. GPTScan loggt über `rich`; dessen
Rendering setzt rechtsbündig eine Quellmarke (`tasks.py:177`) an die erste Zeile
und rückt jede Folgezeile ein. Beide Abbruchbedingungen greifen dadurch nie.

**Die inhaltliche Tragweite** ist größer als ein fehlender Logeintrag: GPTScan
fängt ein gescheitertes Compilat ab, überspringt ohne Falcon-IR die statische
Bestätigungsstufe, endet mit **Exit-Code 0** und schreibt
`{"success": true, "results": []}`. Ein nicht übersetzbarer Contract war damit
von einem sauber analysierten nicht zu unterscheiden — über alle Läufe betraf
das **246 Tasks (98 verschiedene Contracts in 9 Läufen)**. Der Hauptlauf
`curated_v1_20260705` ist davon **nicht** betroffen: dort ist kein einziges
Compilat gescheitert.

**Nach der Reparatur: 0 Lücken über alle 930 Tasks.** Der Nachweis ist
wiederholbar (`python analysis_tools/parser_audit.py`, rund 25 s über alle
Läufe) und wurde mit demselben Detektorkatalog gegen beide Datenstände geführt —
gegen den heutigen und gegen die vollständige Sicherung
`BA-results-raw-backup-20260802`. Dass die Zahl der Rohmeldungen in beiden
Läufen identisch 1464 beträgt, ist dabei die entscheidende Kontrolleigenschaft:
Verändert hat sich nur, wie viel davon im Parser-Output wiederauffindbar ist.

### 4.4 Absicherung

41 Regressionstests wurden aus **unveränderten Rohdaten echter Läufe** gebildet
(Herkunft in `tests/fixtures/MANIFEST.json`, vor Verwendung auf Klartext-
Schlüssel geprüft). Zwei Gegenproben belegen ihre Aussagekraft:

* **Rückspielprobe:** Mit den Parsern aus `f85946e` fallen **17 der 41 Tests**
  durch. Ein Test, der auch gegen die defekte Fassung besteht, wäre wertlos.
* **Mutationsprobe:** Von 31 gezielt eingebauten Fehlern werden 23 erkannt. Im
  Kernbereich — Errors/Fails-Trennung, Sichtbarkeit gescheiterter Compilate,
  De-Wrapper, Unterscheidung der Ausfallgründe — fällt **jede** Mutation auf
  (9 von 9 vorgegebenen, dazu 14 weitere).

Die Suite umfasst inzwischen **44 Tests** (drei kamen mit dem Docker-Cleanup-Fix
hinzu, Abschnitt 7.1). Stand heute: **44 passed** (nachgerechnet, Abschnitt 11).

### 4.5 Gültigkeitsgrenzen

Drei Einschränkungen begrenzen die Aussage „es geht nichts verloren":

1. **Meldungen werden gekürzt.** `sb.parse_utils.truncate_message` kürzt ab 205
   Zeichen, indem es die Mitte durch `...` ersetzt. Das ist
   SmartBugs-Konvention. Der vollständige Text bleibt unverändert in
   `result.log`, das der Parser nie anfasst.
2. **Das Audit kennt nur seinen Katalog.** Die Detektoren wurden aus den 19
   vorhandenen Läufen abgeleitet. Eine Meldungsart, die dort nie vorkam, würde
   nicht als fehlend erkannt. **Zwei solche Klassen sind inzwischen konkret
   nachgewiesen** — siehe Abschnitt 9.1 und 9.2. Die Aussage „0 Lücken" gilt
   daher präzise formuliert: *keine der gesuchten Meldungen geht verloren.*
3. **Die Entzerrung der `rich`-Umbrüche ist nicht zeichengenau.** Ob an einem
   Leerzeichen oder mitten im Token umgebrochen wurde, ist hinterher nicht mehr
   unterscheidbar. Betroffen sind lange Pfade
   (`14_YieldSourcePrizePool.so l`), nicht Exception-Namen oder Meldungstexte.

---

## 5. AP3 — Fehlertreue: alle Meldungen, auch die irreführenden

### 5.1 Fragestellung

Ein gescheitertes Compilat zieht eine Kette von Folgefehlern nach sich: Ohne
Falcon-IR laufen die Codepfade der statischen Stufe ins Leere und werfen
`TypeError: 'NoneType' object is not subscriptable` oder
`UnboundLocalError: local variable 'match_flag' referenced before assignment`.
Diese Meldungen benennen ein Symptom, nicht die Ursache — sie sind sachlich
irreführend. Zu entscheiden war, ob sie gefiltert, umgeschrieben oder
unverändert ausgegeben werden.

### 5.2 Entscheidung und Begründung

**Sie werden unverändert ausgegeben.** Kein Filtern, kein Umschreiben, kein
Ersetzen. Die Begründung ist methodisch: Ein Parser, der entscheidet, welche
Meldung „eigentlich gemeint" ist, verlagert eine Interpretationsentscheidung in
eine Schicht, in der sie nicht mehr überprüfbar ist. Was das Werkzeug gesagt
hat, und was man daraus schließt, sind zwei verschiedene Aussagen und gehören in
zwei verschiedene Spalten.

Die Einordnung geschieht deshalb **additiv** in einer eigenen Spalte
`classification`, die `analysis_tools/errors_fails_report.py` erzeugt:

| Klassifikation | Bedeutung |
|---|---|
| `root_cause` | Die Meldung benennt das Compilat selbst |
| `consequence` | Jede andere Meldung in einem Task, dessen Compilat gescheitert ist |
| `independent` | Der Contract wurde übersetzt; die Meldung steht für sich |

Die Grundlage dafür liefert der Parser als `info`-Eintrag im Wortlaut:
*„GPTScan analysis degraded: the contract did not compile, so the static
confirmation stage never ran. Any 'no findings' result for this contract is
inconclusive, not clean."*

### 5.3 Was ausdrücklich *kein* Fehler ist

Drei Beobachtungen sehen nach Defekten aus und sind keine. Weder das Audit noch
die Parser werten sie als Fehler:

1. **`vul_before_static > vul_after_static`** — das ist GPTScans statische
   Bestätigungsstufe, die LLM-Kandidaten verwirft, also der bestimmungsgemäße
   False-Positive-Filter. Er greift bei etwa der Hälfte aller Live-Contracts und
   wird als `info` mit Zahlen sichtbar gemacht. Gegenprobe: 202 Tasks weisen
   dieses Muster auf; **0** werden als Error oder Fail geführt, **0** bleiben
   ohne `info`-Eintrag.
2. **Reine solc-Warnungen.** Umgekehrt gilt jedoch nicht, dass eine Warnung
   harmlos wäre: Mit `--combined-json` schreibt älteres solc Warnungen nach
   stdout, zerstört damit das JSON und lässt crytic-compile abbrechen. Ein
   Contract kann an einer Meldung sterben, die nur
   „Warning: SPDX license identifier not provided" lautet. Maßgeblich ist die
   geworfene Exception, nicht das Wort „Warning".
3. **Slithers Exit-Code 255** (Abschnitt 3.2).

### 5.4 Nachweis der Unversehrtheit der Messwerte

Die entscheidende Kontrolle für die Bachelorarbeit: Alle 930 `result.json`
wurden gegen ihre Prä-Fix-Fassung im Backup verglichen.

| Feld | Tasks mit Änderung | Richtung |
|---|---:|---|
| `findings` | **0** | — |
| `errors` | 341 | ausnahmslos mehr |
| `infos` | 377 | ausnahmslos mehr |
| `fails` | 0 | — |

Kein Task hat ein Finding verloren oder gewonnen; **alle Änderungen sind
additiv**. `evaluate_curated.py` liefert vorher und nachher **byte-identische**
Ausgabe. Der Grund ist strukturell und nicht zufällig: Das Skript liest
ausschließlich das Feld `findings`, während die Reparatur nur `errors` und
`infos` berührt. Recall, Precision und F1 können sich folglich nicht verschoben
haben (`docs/parser-fix-vorher-nachher.md`).

Ein Regressionstest sichert die Fehlertreue ab
(`test_messages_are_passed_through_unrewritten`).

---

## 6. AP4 — Repository-Hygiene, Geheimnisschutz und Dokumentation

### 6.1 Fragestellung

Das Repository sollte so hergerichtet werden, dass der Betreuer eingeladen
werden kann. Das umfasst drei getrennte Anforderungen: **kein Geheimnis im
Baum oder in der Historie**, **nachvollziehbare Abgrenzung von Eigen- und
Fremdanteil**, und **eine Dokumentation, die den Betrieb ohne Rückfragen
erlaubt**.

### 6.2 Geheimnisschutz

**Befund.** Der DeepSeek-API-Schlüssel lag im Klartext in **62** Ergebnisdateien,
jeweils in genau einem Feld: `.docker.environment.DEEPSEEK_API_KEY` in
`smartbugs.json`. Ursache ist der Mechanismus, mit dem SmartBugs
Umgebungsvariablen in den Container reicht und protokolliert.

**Maßnahme.** `analysis_tools/redact_results.py` redigiert ausschließlich dieses
eine Feld. Das Werkzeug ist defensiv ausgelegt: Dry-Run als Standard, `--apply`
erforderlich, Abbruch, sobald sich mehr als dieses Feld ändern würde, und es
gibt nie einen Wert aus. Serialisiert wird über denselben
`json.dumps(..., sort_keys=True, indent=4)`-Aufruf wie in `sb.io.write_json`,
damit die Dateien byte-gleich zu dem bleiben, was SmartBugs selbst schreiben
würde. Vor dem Eingriff wurde `smartbugs/results/` vollständig gesichert
(4461 Dateien, 258,40 MB, 0 Fehler).

**Nachkontrolle.** Alle 930 Task-Verzeichnisse wurden gegen die Sicherung
verglichen: 868 der 930 `smartbugs.json` sind byte-identisch, 62 unterscheiden
sich in genau diesem einen Pfad, sonst nirgends. Die Rohdaten (`result.log`,
`result.tar`) wurden nie angefasst. Der echte Schlüssel existiert nur noch in
der git-ignorierten, ungetrackten `GPTScan/.env`. Eine unabhängige Prüfung mit
einem **anderen** Musterkatalog über den gesamten Baum einschließlich entpackter
`result.log.gz` und aller `.tar`-Member bestätigt das; die erreichbare
git-Historie wurde über 403.246 Diff-Zeilen gescannt, ohne Fund. **Eine
Schlüsselrotation ist nach Befundlage nicht erforderlich**, da nie ein echter
Schlüssel committet wurde.

**Prävention.** `analysis_tools/secret_scan.py` prüft gestagte Dateien als
pre-commit-Hook. Drei Eigenschaften sind im Berichtszeitraum ergänzt worden,
weil die erste Fassung jeweils eine stille Lücke hatte:

| Lücke | Behebung |
|---|---|
| Der Hook lag in `.git/hooks/` und wurde **nie mitgeklont** — wer das Repo klont, committet ungeschützt | Der Hook ist jetzt eine getrackte Datei (`.githooks/pre-commit`); `--install` setzt nur noch `core.hooksPath`. Änderungen erreichen alle Beteiligten über `git pull` |
| Der Scan sah **nicht in komprimierte Dateien hinein** — genau die Form, die die Test-Fixtures verwenden | gzip-Ströme sowie tar- und zip-Archive werden entpackt und bis `MAX_DEPTH=3` mitdurchsucht; ein Treffer nennt die Position innerhalb des Archivs |
| Dateien über `MAX_BYTES` lieferten **stillschweigend ein leeres Ergebnis** — von einer sauberen Datei nicht unterscheidbar | Übersprungenes wird namentlich mit Grund gemeldet, in beiden Ausgängen |
| Bei `core.autocrlf=true` (Windows-Standard) wäre der Hook mit CRLF ausgecheckt worden und **stillschweigend nicht mehr gelaufen** | `.gitattributes` erzwingt `eol=lf` |

Die dritte Behebung machte unmittelbar sichtbar, dass
`GPTScan/src/jars/SolidityStaticAnalysis-1.0-SNAPSHOT-standalone.jar`
(20.852.934 Bytes) nie geprüft worden war; eine Prüfung außer der Reihe ergab
keinen Treffer, dauert aber rund 10 s, weshalb die Größengrenze bestehen bleibt.

Der Scan ist **in beide Richtungen** gegengeprüft: kein Falschtreffer über den
gesamten Baum, und ein eingeschleuster Testschlüssel wird gefunden und blockiert
den Commit, ohne den Wert auszugeben — auch in `.gz` und in `.tar`→`.gz`.

### 6.3 Dokumentation und Kommentierung

Neu entstanden im Berichtszeitraum:

| Dokument | Inhalt |
|---|---|
| `README.md`, `LICENSE` | Einstieg; MIT für den Eigenanteil, Fremdlizenzen getrennt ausgewiesen |
| `docs/BA-EIGENANTEIL.md` | Abgrenzung Eigen-/Fremdanteil, per Datei-Hash gegen den Upstream abgeglichen |
| `docs/BA-BETRIEB.md` | Betriebsdoku: Parameter, Umgebungsvariablen, Fallstricke, Kosten, Einrichtung |
| `docs/BA-ERRORS-VS-FAILS.md` | Herleitung der Fehlersemantik aus dem Quelltext |
| `docs/BA-WERKZEUG-BEDIENUNG.md` | Bedienung beider Werkzeuge über SmartBugs |
| `docs/BA-DEMOLAUF-ERGEBNIS.md` | Laufbericht des Demonstrationslaufs |
| `docs/BA-VERIFIKATIONSBERICHT.md` | unabhängige Überprüfung des gesamten Arbeitsstands |

**Kommentierung des Quelltextes.** Der Eigenanteil ist durchgängig mit
Modul-Docstrings sowie Docstrings für jede Funktion und Klasse versehen; die
Begründung nicht offensichtlicher Entscheidungen steht als Inline-Kommentar an
der jeweiligen Stelle. Ausgangslage waren **59** Funktionen und Klassen ohne
Docstring, ermittelt per AST-Auswertung über den gesamten als Eigenanteil
ausgewiesenen Umfang; Endstand **0**.

**Markierung der Eingriffe in Fremdcode.** Alle inhaltlichen Änderungen an
SmartBugs sind in nummerierte Marker eingefasst
(`BA MODIFICATION <n>: BEGIN/END`): `sb/docker.py` 5 Blöcke, `sb/tools.py` 2,
`sb/analysis.py` 2, `sb/solidity.py` 1. Wo ein Block Upstream-Code ersetzt statt
ergänzt, steht die ersetzte Fassung wörtlich als Kommentar im Block; der Rückbau
ist damit rein mechanisch. **Geprüft:** Werden alle zehn Blöcke entfernt und die
zitierten Zeilen eingesetzt, stimmen alle vier Dateien mit dem Upstream-Tag
`v2.1.1` überein und übersetzen weiterhin. Es ist also weder eigener Code
unmarkiert geblieben noch fremder mitmarkiert.

### 6.4 Bei der Überprüfung gefundene Dokumentationsfehler

Die unabhängige Verifikation (Abschnitt 7.4) deckte in der Eigenanteil-Doku
selbst Fehler auf, die als schwerwiegender einzustufen sind als die
Parser-Befunde — für ein Dokument, dessen einziger Zweck die Abgrenzung von
Eigen- und Fremdleistung ist:

| Befund | Behebung |
|---|---|
| **SmartBugs hatte fünf geänderte Dateien, dokumentiert war eine.** `tools.py` wiegt am schwersten: ohne diesen Patch liest SmartBugs das Feld `env:` in den Tool-Konfigurationen gar nicht ein — der API-Schlüssel-Mechanismus besteht aus zwei Dateien, nicht einer | Abschnitt neu geschrieben, alle fünf mit *was* und *warum*; `LICENSE`-SCOPE nachgezogen |
| Die „neu"-Zahlen im Eigenanteil waren **arithmetisch unmöglich** (Summe > getrackte Dateien) | Neu gerechnet; beide Summen gehen auf. 10 generierte Lauf-Ergebnisse sind jetzt als solche ausgewiesen |
| **`sb/results2csv.py` war nicht versioniert.** `smartbugs/.gitignore:43` enthielt `results*` ohne führenden Schrägstrich und traf damit auch Quelldateien — der im README vorgeschriebene Arbeitsschritt war auf einem frischen Klon nicht durchführbar | Muster geankert (`/results*`); der Fehler schloss **sechs** Upstream-Dateien aus, alle sind jetzt versioniert und byte-identisch zum Upstream |
| Lizenzlage unklar | **GPTScan steht unter AGPL-3.0** (Copyleft), und der Baum enthält Änderungen am GPTScan-Quelltext: für ein privates Repo folgenlos, bei Veröffentlichung bindend. Dass SmartBugs sich selbst widerspricht (`LICENSE` Apache-2.0, `pyproject.toml` MIT), ist festgehalten statt aufgelöst |
| Upstream-Stände nicht fixiert | `BA-EIGENANTEIL.md` nennt jetzt `29a1747` / `c507fe4` / `v2.1.1` |

**Weiteres Aufräumen:** `.gitignore` um vier Lücken ergänzt (u. a.
`.pytest_cache/`, das bisher nur durch pytests eigene Datei ignoriert wurde,
was erst nach dem ersten Testlauf greift); rund 3,4 MB Reste eigener
Integrationstests aus dem Fremdcode entfernt, extern gesichert und über
`f85946e` weiterhin herstellbar.

### 6.5 Stand der Weitergabefähigkeit

Der Zweig `main` ist auf `origin` gespiegelt
(`https://github.com/Alex-Hofer/BA-Smartbugs-llm.git`, Stand `a2be0f3`). Aus
technischer Sicht steht der Einladung nichts entgegen. Zwei Punkte sind beim
Empfänger zu beachten und im README beschrieben:

* Der Secret-Scan muss auf einem frischen Klon einmalig aktiviert werden
  (`python analysis_tools\secret_scan.py --install`, setzt `core.hooksPath`).
* `core.longpaths` ist eine lokale Konfiguration und wird nicht mitgeklont.

**Ob die Einladung ausgesprochen wurde, ist aus dem Repository nicht
feststellbar** und daher hier nicht behauptet.

---

## 7. Weitere wesentliche Änderungen des Berichtszeitraums

### 7.1 Ein ergebnisvernichtender Fehler in SmartBugs

Beim Demonstrationslauf lieferte ein kostenloser Dry-Run **null Ergebnisse**:
0 von 5 Tasks, keine einzige `result.json` — bei `ExitCode=0` und ohne
Fehlermeldung.

**Ursache.** SmartBugs löscht das Task-Temp-Verzeichnis im `finally`-Block von
`sb.docker.execute`. Unter Docker Desktop ist das Handle auf die gerade im
Container ausgeführten Dateien noch offen; `os.rmdir` scheitert mit
`PermissionError: [WinError 5]`. Der Schaden entsteht eine Ebene höher:
`sb/analysis.py:96` wiederholt Docker-Probleme nur für `sb.errors.SmartBugsError`.
`PermissionError` fällt nicht darunter, entkommt und beendet den Worker-Prozess
— **bevor** `result.json`, `result.log` und `smartbugs.json` geschrieben werden.
Der Hauptprozess bemerkt davon nichts und meldet Erfolg.

**Behebung.** `rmtree_retry` wiederholt das Löschen mit kurzem Backoff; ein
dauerhaft gesperrtes Verzeichnis wird gemeldet und liegen gelassen, statt eine
Ausnahme zu werfen — ein Aufräumproblem darf eine fertige Analyse nie verwerfen.
Abgesichert durch `tests/test_docker_cleanup.py` (Normalfall, vorübergehende
Sperre, dauerhafte Sperre). Verifikation an der ursprünglichen Reproduktion:
danach 5 von 5 Tasks.

**Einordnung.** Die 19 Altläufe sind nicht berührt — sie liefen vor dem
Auftreten des Problems. Warum es jetzt auftritt und im Juli nicht, ist nicht
abschließend geklärt; naheliegend ist ein zwischenzeitliches Update von Docker
Desktop. Methodisch ist der Befund der wertvollste Nebenertrag des Laufs: **Ein
Fehler, der Ergebnisse lautlos auf null setzt und dabei Exit-Code 0 meldet, ist
die gefährlichste Sorte.** Ohne den vorgeschalteten kostenlosen Dry-Run wäre er
erst nach dem bezahlten Lauf aufgefallen.

### 7.2 Demonstrationslauf beider Werkzeuge

Funktionsnachweis an zwei Contract-Sätzen zu je fünf Contracts (Satz A: SWC/DASP
mit Ground Truth; Satz B: DeFi aus Web3Bugs), 20 Tasks, alle mit Exit-Code 0,
kein einziger Fail. **Ausdrücklich kein neuer Messwert für die Arbeit** — zehn
Contracts sind keine Stichprobe.

| | GPTScan | LLMSmartAudit |
|---|---:|---:|
| Findings Satz A (SWC) | **0** | **33** |
| Findings Satz B (DeFi) | **21** | **49** |
| Errors / Fails | 17 / 0 | 0 / 0 |
| LLM-Aufrufe | 193 | nicht ausgewiesen |
| Kosten | $0,0725 | nicht ausgewiesen |
| Wanduhrzeit | 17:04 min | 79:28 min |
| Zeilennummern in Findings | ja | nein |

Drei Beobachtungen sind für die Argumentation der Arbeit verwertbar:

* **GPTScans Null auf Satz A ist kein „nichts gefunden", sondern ein „gar nicht
  erst gesucht".** Alle fünf Tasks protokollieren `llm_calls=0`: Die vorgelagerte
  Stufe fand keine Funktion, die zu einem der zehn MWE-Szenarien passt, und
  verwarf die Contracts vor dem ersten Modellaufruf. Ein Nullergebnis von
  GPTScan auf klassischen SWC-Schwachstellen ist damit keine Aussage über diese
  Schwachstellen, sondern die Aussage, dass das Werkzeug für sie nicht zuständig
  ist. Dasselbe Werkzeug liefert auf den DeFi-Contracts 21 Findings aus sechs
  verschiedenen MWE-Regeln.
* **LLMSmartAudit trifft in Satz A die Ground-Truth-Kategorie bei allen fünf
  Contracts**, findet in Satz B aber **nicht** die DeFi-Logikfehler, sondern
  dieselbe Art allgemeiner Solidity-Mängel wie in Satz A. Die Werkzeuge
  konkurrieren also weniger, als sie einander ergänzen; auf `20_Synth.sol`
  überschneiden sie sich praktisch nur bei Front-Running.
* **Die Ausgabe ist nicht deterministisch.** Gegenüber dem Altlauf
  `curated_mwefixed_live` wichen die Findings je Contract ab, bei gleichem
  Werkzeug, gleichem Modell und gleicher Datei (6→4, 5→4, 4→3, 4→5, 4→5); auch
  die getroffenen MWE-Regeln deckten sich nicht vollständig. **Wer Läufe
  vergleicht, vergleicht damit immer auch Rauschen.** Aufwand und Kosten wichen
  ebenfalls erheblich ab: 28–65 LLM-Aufrufe je DeFi-Contract statt eines Medians
  von 9,5.

Damit ist zugleich der im Juli offene Punkt der **Reproduzierbarkeit**
beantwortet, und zwar negativ. Für die Arbeit heißt das: Einzelwerte aus einem
Lauf sind nicht belastbar; belastbar sind nur Aggregate über hinreichend viele
Contracts, und auch diese tragen eine Streuung, die bislang nicht quantifiziert
ist.

### 7.3 Reparatur des Zielkorpus (chronologisch vor diesem Berichtszeitraum)

Der im Juli benannte P0-Blocker ist auf einen Datensatzfehler zurückgeführt,
nicht auf eine Fehlkonfiguration der Werkzeugkette: Die Contracts sind einzeln
aus größeren Wettbewerbsprojekten extrahierte Fragmente, deren `import`-Ziele
nicht beiliegen. Nach der Rekonstruktion aus den Originalquellen des
Web3Bugs-Benchmarks kompilieren **96/96** nativ und **94/96** in GPTScans echter
Analyse-Toolchain (`docs/BA-KORPUS-REPARATUR.md`, Durchführung 21.07.2026).

**Bestätigt durch die neue Auswertung:** Im Lauf `curated_mwefixed_live` scheitert
nur **1 von 96** Contracts am Compilat. Damit ist die Korpus-Reparatur
unabhängig belegt.

**Neu sichtbar geworden — und vor der Parser-Reparatur unsichtbar:**

| Beobachtung im Lauf `curated_mwefixed_live` (96 Contracts) | Contracts |
|---|---:|
| `Static analysis failed: Invalid args` | **35** |
| Exception in der Variablenbeschreibung (`tasks.py:245`) | 31 |
| weitere Abbrüche der statischen Stufe (`tasks.py:325`, `:232`) | 21 |
| LLM-Antwort nicht als JSON lesbar (`JSONDecodeError`) | 3 |
| gescheitertes Compilat | 1 |

**GPTScans statische Bestätigungsstufe stürzt damit auf 35 von 96 übersetzbaren
Contracts ab.** Das ist genau der Präzisionsfilter, um den es in der
Argumentation der Arbeit geht. Der Befund verlagert den P0-Blocker: Er ist nicht
mehr *Kompilierung*, sondern *Stabilität der statischen Stufe auf kompilierendem
Code*.

### 7.4 Unabhängige Verifikation des Arbeitsstands

Der gesamte Arbeitsstand wurde einer Überprüfung unterzogen, deren Maßstab war,
jede Behauptung zu **widerlegen** (`docs/BA-VERIFIKATIONSBERICHT.md`): sieben
Prüfpakete, davon drei unabhängig voneinander bearbeitet. Alle Prüfungen liefen
lesend; schreibende Tests fanden in Klonen außerhalb des Repositories statt.

Die drei tragenden Aussagen haben standgehalten (1368 → 0 Lücken; Messwerte
unberührt; Fehlersemantik hergeleitet statt erfunden). Der Bericht führt
zusätzlich **sieben gescheiterte Angriffe** auf — ein Prüfbericht ohne
gescheiterte Angriffe sagt nichts über seine eigene Strenge aus. In vier Fällen
erwies sich der Verdacht als unbegründet und die Dokumentation als richtig; das
ist protokolliert.

Elf bestätigte Befunde wurden nach Schwere geordnet; sieben davon sind behoben
(Abschnitt 6.4), sechs bewusst offen geblieben (Abschnitt 9 und 10) — jeweils
mit Begründung, warum die Entscheidung den Verfassern der Arbeit vorbehalten
bleibt.

---

## 8. Beantwortung der vier Leitfragen

**Frage 1 — Errors und Fails getrennt und lesbar ausgeben.**
Erledigt. Die Semantik ist aus `sb/parse_utils.py:66-90` hergeleitet, nicht
gesetzt; `analysis_tools/errors_fails_report.py` gibt je Lauf und Werkzeug
Tasks, saubere Tasks, Tasks mit Errors, Tasks mit Fails, Anzahl Errors, Anzahl
Fails und Tasks mit gescheitertem Compilat aus, dazu jede Meldung im Wortlaut —
als Markdown und CSV. Bilanz über 19 Läufe: 930 Tasks, 586 sauber, 344 mit
Errors, 50 mit Fails, 246 mit gescheitertem Compilat (**keine disjunkten
Klassen**). Der Report ist in `run_curated.ps1` eingebunden und lief im
Demonstrationslauf in fünf Läufen live mit. → Abschnitt 3.

**Frage 2 — Sicherstellen, dass nichts durch den Parser verlorengeht,
insbesondere keine Fehlermeldungen.**
Erledigt, mit benannter Reichweite. Vorher gingen **1368 von 1464** Rohmeldungen
verloren, ausnahmslos im GPTScan-Parser; nachher **0 Lücken** über alle 930
Tasks, jederzeit nachprüfbar mit `python analysis_tools/parser_audit.py`. Die
Aussage gilt präzise formuliert *innerhalb des Detektorkatalogs*: Zwei
Meldungsklassen liegen nachweislich außerhalb (Abschnitt 9.1, 9.2), und
Meldungen werden nach SmartBugs-Konvention ab 205 Zeichen gekürzt — verworfen
wird nichts. → Abschnitt 4.

**Frage 3 — Cleanup und Sicherheit, damit eingeladen werden kann; dazu
Dokumentation und Kommentare.**
Erledigt. Der Schlüssel ist aus 62 Ergebnisdateien redigiert (alle 930 gegen die
Sicherung verifiziert), existiert nur noch in der git-ignorierten `GPTScan/.env`
und war nie in der Historie; eine Rotation ist nach Befundlage nicht nötig. Der
Secret-Scan ist als **mitgeklonter** Hook aktiv, sieht in Archive hinein und
meldet Übersprungenes namentlich. Sieben Dokumente sind neu, der Eigenanteil ist
per Datei-Hash gegen fixierte Upstream-Stände abgeglichen, Eingriffe in
Fremdcode sind blockweise markiert und mechanisch rückbaubar, der eigene Code
ist vollständig kommentiert (59 → 0 fehlende Docstrings). `main` ist gepusht.
**Offen bleibt allein die Einladung selbst**, die aus dem Repository nicht
feststellbar ist. → Abschnitt 6.

**Frage 4 — Alle Fehlermeldungen einbeziehen, auch die sachlich falschen wie
bei GPTScan.**
Erledigt. Irreführende Folgefehler wie
`TypeError: 'NoneType' object is not subscriptable` stehen **unverändert** im
Ergebnis; es wird nichts gefiltert und nichts umgeschrieben. Die Einordnung
Ursache/Folge steckt in einer **zusätzlichen** Spalte `classification`
(`root_cause` / `consequence` / `independent`), nie in einer Ersetzung. Ein
Regressionstest sichert das ab. Begründung: Was das Werkzeug gesagt hat und was
man daraus schließt, sind zwei Aussagen und gehören in zwei Spalten.
→ Abschnitt 5.

---

## 9. Gültigkeitsgrenzen

Die folgenden Punkte begrenzen die Reichweite der Ergebnisse. Sie sind
sämtlich nachgewiesen, nicht vermutet.

### 9.1 Blinder Fleck: WARNING-Log-Records

`WARNING utils: Cannot find functionB or same function` steht im Rohlog zweier
Tasks, aber **weder in `result.json` noch in der Signalliste des Audits**.
Ursache: Audit und Parser reagieren beide nur auf `ERROR|CRITICAL`. Ein
**gemeinsamer** blinder Fleck ist per Konstruktion unsichtbar — das Audit meldet
„0 Lücken", obwohl eine Meldung fehlt. Umfang: 2 von 930 Tasks, 2 von 142
WARNING-Records im Korpus. Im Demonstrationslauf reproduziert.

*Nicht behoben*, weil die Behebung `errors` in zwei Tasks erhöhen und damit
gemessene Werte verändern würde. Das ist eine Entscheidung des Autors.

### 9.2 Blinder Fleck: ANTLR-Grammatikmeldungen

GPTScans ANTLR-Grammatik lehnt Quelltext ab und schreibt roh auf stderr
(`line 14:46 extraneous input 'constant' expecting {...}`). Betroffen sind
**284 von 930 Tasks in 12 Läufen, darunter der Hauptlauf
`curated_v1_20260705` mit 87 Tasks**. Keine dieser Meldungen erreicht
`result.json`; sie sind weder Tracebacks noch Log-Records und werden von keiner
Schicht betrachtet. Die betroffenen Contracts sind überwiegend alte
Solidity-0.4-Quellen, deren Syntax (`constant`, `var`, `finney`) die verwendete
Grammatik nicht kennt.

**Ausdrücklich ungeklärt:** ob diese Ablehnungen GPTScans Funktionsextraktion
tatsächlich verstümmeln. ANTLR erholt sich von `extraneous input` und arbeitet
weiter. Dies ist **der einzige offene Befund, der potenziell die Interpretation
der Messwerte betrifft**, und deshalb der erste zu klärende Punkt
(Abschnitt 10).

### 9.3 Weitere Grenzen

| Grenze | Wirkung |
|---|---|
| Kürzung ab 205 Zeichen (`truncate_message`) | In `result.json` steht bei sehr langen Meldungen Anfang und Ende, nicht die Mitte. Der vollständige Text bleibt in `result.log` |
| `rich`-Entzerrung nicht zeichengenau | Betrifft lange Pfade, nicht Exception-Namen oder Meldungstexte |
| Diskriminator *roh ⇒ fail* | Gilt für 638 von 640 GPTScan-Tasks; die Fehlklassifikation entsteht upstream |
| Nichtdeterminismus der Werkzeuge | Einzelwerte aus einem Lauf sind nicht belastbar (Abschnitt 7.2) |
| Lücken der Testsuite außerhalb des Kernbereichs | Für GPTScan-Findings existiert keine Assertion auf `severity`, `line`, `line_end`, `filename`; `success=false` wird nur synthetisch geprüft, obwohl es 44-mal real vorkommt |
| Reichweite von `secret_scan.py` | Erfasst hoch-konfidente Schlüsselformen; **nicht** Google-Keys (`AIza…`), JWTs, generische `PASSWORD=`-Zuweisungen und Anthropic-Keys. Für dieses Projekt folgenlos, da nur ein DeepSeek-Schlüssel im `sk-`-Format existiert |
| `run_curated.ps1`-Integration | In fünf realen Läufen des Demonstrationslaufs durchlaufen, aber **nie in einem Massenlauf über 143 Contracts** |

---

## 10. Offene Punkte, priorisiert

| Prio | Punkt | Begründung |
|---|---|---|
| **P0** | **Klären, ob die ANTLR-Ablehnungen die Funktionsextraktion verstümmeln** (9.2) | Betrifft 87 Tasks des Hauptlaufs. Erst danach lässt sich sagen, ob es ein Melde- oder ein Messproblem ist. Einziger offener Befund mit möglicher Wirkung auf die Messwerte |
| **P0** | **Absturz der statischen Bestätigungsstufe auf 35/96 Contracts** (7.3) | Der Präzisionsfilter ist der methodische Kernbeitrag von GPTScan. Sein Ausfall auf einem Drittel des Zielkorpus ist der neue inhaltliche Blocker |
| **P1** | **Evaluation des Hauptlaufs** | Im Juli-Bericht als P2 geführt und weiterhin offen. Die Werkzeuge dafür (`evaluate_curated.py`) stehen |
| **P1** | **GPTScan-Massenlauf auf dem reparierten Korpus nach der Parser-Reparatur** | Die vorliegenden Läufe entstanden vor der Reparatur; ihre `result.json` sind zwar nachträglich neu erzeugt, ein frischer Lauf ist aber die sauberere Grundlage |
| **P2** | Streuung quantifizieren (Mehrfachläufe) | Ohne Maß für den Nichtdeterminismus (7.2) ist unklar, ab welcher Differenz zwei Läufe sich unterscheiden |
| **P2** | Kostenmessung für LLMSmartAudit | Das Werkzeug weist keine Kosten aus; die bisherige Angabe ist eine Schätzung aus dem Smoke-Test, keine Messung |
| **P2** | WARNING-Blindfleck schließen (9.1) | Erhöht `errors` in zwei Tasks — Entscheidung des Autors |
| **P3** | Durchführungsprotokoll bei Fehler #4 nachziehen | Dort steht als Maßnahme „Parser-Fix als Empfehlung dokumentiert"; der Fix ist gemacht. Der Eintrag gehört zur Darstellung der Arbeit und war zu diesem Zeitpunkt noch nicht geändert (seit 25.09.2026 nachgeführt) |

---

## 11. Verifikationsstand dieses Berichts

**Am 2026-08-03 in diesem Arbeitsbaum neu ausgeführt:**

| Prüfung | Kommando | Ergebnis |
|---|---|---|
| Testsuite | `python -m pytest tests -q` | **44 passed** (0,56 s) |
| Geheimnis-Scan über den gesamten Baum | `python analysis_tools/secret_scan.py --all` | **1139 Dateien, kein Fund**, 1 allowlisted, 1 ungeprüft (der 20,8-MB-JAR, namentlich gemeldet) |
| Spiegelung | `git log origin/main -1` | `a2be0f3`, identisch mit `main` |
| Eingriffsmarkierung | `git show cfe97c7` | 10 `BA MODIFICATION`-Blöcke in 4 Dateien |

**Dokumentiert übernommen, in diesem Arbeitsbaum nicht nachrechenbar:**

Alle Zahlen, die auf `smartbugs/results/` beruhen — 930 Tasks, 1464 Meldungen,
1368 → 0 Lücken, die Errors/Fails-Bilanz, der Vorher/Nachher-Vergleich und die
Ergebnisse des Demonstrationslaufs. Grund: **Das Verzeichnis `smartbugs/results/`
ist git-ignoriert und in diesem Klon nicht vorhanden**
(`parser_audit.py` meldet hier folgerichtig „No SmartBugs task directories
found"). Die Rohdaten liegen auf dem Erhebungsrechner samt der vollständigen
Sicherung `BA-results-raw-backup-20260802`.

Diese Zahlen sind dort jeweils **zweifach** belegt: durch den Arbeitsbericht und
durch die unabhängige Nachrechnung im Verifikationsbericht, die dieselben
Kommandos gegen beide Datenstände geführt hat. Sie sind auf dem
Erhebungsrechner mit den in Abschnitt 12 genannten Kommandos jederzeit
reproduzierbar.

---

## 12. Belegdokumente

| Dokument | Rolle |
|---|---|
| Kontextpapier Juli 2026 (entfernt) | Bezugsstand dieses Berichts; seine Prioritätenliste steht in Abschnitt 2 |
| `docs/BA-ARBEITSBERICHT-20260802.md` | Ausführungsprotokoll in der Reihenfolge der Durchführung |
| `docs/BA-AUFGABEN-UND-STATUS.md` | Soll-Ist-Abgleich je Teilaufgabe |
| `docs/BA-VERIFIKATIONSBERICHT.md` | unabhängige Überprüfung, bestätigte und widerlegte Befunde |
| `docs/BA-ERRORS-VS-FAILS.md` | Herleitung der Fehlersemantik aus dem Quelltext |
| `docs/errors-fails.md`, `docs/errors-fails.csv` | erzeugte Bilanz, Meldungen im Wortlaut |
| `docs/parser-audit-vorher.md`, `docs/parser-audit-nachher.md` | Lückenbericht vor und nach der Reparatur |
| `docs/parser-fix-vorher-nachher.md` | Nachweis, dass `findings` unverändert blieb |
| `docs/BA-KORPUS-REPARATUR.md` | Rekonstruktion des Zielkorpus |
| `docs/BA-DEMOLAUF-ERGEBNIS.md` | Laufbericht des Demonstrationslaufs, Konsolenausgaben im Wortlaut |
| `docs/BA-WERKZEUG-BEDIENUNG.md`, `docs/BA-BETRIEB.md` | Bedienung und Betrieb |
| `docs/BA-EIGENANTEIL.md` | Abgrenzung Eigen-/Fremdanteil, per Datei-Hash |

**Reproduktionskommandos** (auf dem Erhebungsrechner, lesend, ohne LLM-Kosten):

```powershell
python analysis_tools\parser_audit.py                  # Vollständigkeit, ~25 s
python analysis_tools\errors_fails_report.py --md docs\errors-fails.md --csv docs\errors-fails.csv
python analysis_tools\secret_scan.py --all             # Geheimnis-Scan
python -m pytest tests -q                              # Regressionstests
```
