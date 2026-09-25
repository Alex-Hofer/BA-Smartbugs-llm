# AP5 — Timeout ins Werkzeug durchreichen: Entwurf

Umsetzungsentwurf zu **AP5** aus `docs/BA-BETREUERGESPRAECH-AUFGABEN.md`. Dieses
Dokument legt fest, *wie* der SmartBugs-Timeout in GPTScan und LLMSmartAudit
ankommt und was beim Ablaufen herauskommt. Der ausführbare Arbeitsplan entsteht
getrennt daraus.

Datum: 2026-08-17 · Status bei Erstellung: abgestimmt, Umsetzung ausstehend ·
Umgesetzt am 18.08.2026, siehe `BA-AP5-ABSCHLUSSBERICHT.md`

---

## 1. Ziel

SmartBugs übergibt jedem Entrypoint vier Argumente — `FILENAME TIMEOUT BIN MAIN`.
Beide Integrationen nehmen `TIMEOUT` als `$2` entgegen und **benutzen es nicht**
(`smartbugs/tools/gptscan/scripts/do_solidity.sh:5`,
`smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh:5`). Nach Abschluss dieses
Arbeitspakets gilt:

* Ein ablaufender Timeout beendet den Lauf **innerhalb** des Containers, nicht
  durch einen Kill von außen.
* Was das Werkzeug bis dahin ermittelt hat, liegt im Ergebnis — als
  gekennzeichnetes Teilergebnis, nicht als vollwertiger Lauf.
* Die Kennzeichnung ist in `result.json` sichtbar und in der Auswertung
  auswertbar, sodass ein Teillauf die Recall-Zahlen nicht still verzerrt.
* Kein Werkzeug bekommt eine neue Kommandozeilenschnittstelle, und **keine
  bisher unberührte Fremddatei** wird angefasst.

## 2. Befund

### 2.1 Einen Timeout für den *Lauf* kennt keines der beiden Werkzeuge

Zu unterscheiden sind zwei Dinge, die beide „Timeout" heißen: die Frist für einen
**einzelnen LLM-Aufruf** und die Frist für den **gesamten Lauf**. Nur die zweite
ist es, die SmartBugs übergibt.

| Werkzeug | Aufruf-Frist | Lauf-Frist |
|---|---|---|
| GPTScan | **ja** — `analyze_pipeline.ask_with_timeout(..., timeout=90)`, durchgesetzt in Zeile 79-85 über einen Worker-Prozess | **nein** — die Optionsliste in `src/tasks.py:122-140` kennt `-s`, `-o`, `-k`, `--provider`, `--model`, `--dry-run`, `--format`, sonst nichts |
| LLMSmartAudit | **nein** — keine `.py`-Datei des Werkzeugs nennt „timeout" | **nein** — `run.py:64-87` kennt nur `--config`, `--org`, `--task`, `--name`, `--provider`, `--model`, `--task-file`, `--path` |

GPTScans Aufruf-Frist ist für AP5 nur insofern von Belang, als sie die Obergrenze
dafür setzt, wie lange ein bereits laufender Aufruf die Bremse noch überdauern
kann — sie geht in die Bemessung der Marken in Abschnitt 4.1 ein.

Das Mythril-Muster (`smartbugs/tools/mythril-0.23.15/scripts/do_solidity.sh:25-30`),
das den Timeout auf 80 % herunterrechnet und als `--execution-timeout` weiterreicht,
ist deshalb **nicht direkt übertragbar**: es gibt kein Flag, an das man ihn hängen
könnte.

### 2.2 Der Mechanismus für Teilergebnisse existiert bereits — in eigenem Code

Das ist der Befund, der den Zuschnitt dieses Arbeitspakets bestimmt.

**GPTScan.** `GPTScan/src/analyze_pipeline.py:36-70` ist die zentrale Messstelle
für jeden LLM-Aufruf und trägt bereits einen Budget-Wächter. Dessen Kommentar
(Zeile 56-57) hält das Verhalten wörtlich fest:

> *„Hard budget guard (live runs only). Once tripped we stop issuing calls and
> return sentinels so the scan still finishes and writes partial results."*

Ein Zeitwächter ist derselbe Wächter mit einer Uhr statt eines Betrags. Die Datei
steht bereits auf der Liste geänderter Dateien (`docs/BA-EIGENANTEIL.md:147`).

**LLMSmartAudit.** `chatdev/audit_report.py` ist **eigener Code** — eine der vier
neu hinzugefügten Dateien (`docs/BA-EIGENANTEIL.md:219`). `chatdev/phase.py:405`
ruft nach *jeder* der 41 Detektor-Phasen `audit_report.record()` auf; geschrieben
wird bisher erst am Ende (`chatdev/chat_chain.py:344`). Das Schema kennt mit
`categories_checked` bereits den Begriff der Teilabdeckung, und der Modul-Docstring
hält fest, dass eine leere Findings-Liste nur bei vollen 41 geprüften Kategorien
„sauber" bedeutet. Ein Teilergebnis ist dort kein neues Konzept, sondern der
vorgesehene Fall.

### 2.3 Wie SmartBugs einen Timeout heute einsortiert

`sb/parse_utils.py:66-89` entscheidet allein am Exit-Code:

| Exit-Code | Einordnung |
|---|---|
| `None` (Container von außen abgeschossen) | `fails = {DOCKER_TIMEOUT}` |
| `127` | `fails` — MAIN-Name traf keinen Contract |
| in `DOCKER_CODES` (125, 126, 127, **137**, 139, **143**) | `fails` unter dem dort hinterlegten Namen, z. B. `DOCKER_KILL_OOM`, `DOCKER_TERM` |
| übrige `128 … 192` | `fails = {DOCKER_RECEIVED_SIGNAL_n}` |
| sonstiger Code ≠ 0 | `errors = {EXIT_CODE_n}` |

Daraus folgt unmittelbar: ein Abbruch **innerhalb** des Containers mit einem
Exit-Code außerhalb des Signalbereichs landet in `errors` — SmartBugs' Kategorie
für „das Werkzeug hat ein Problem bemerkt und abgefangen". Genau dorthin gehört
ein beherrschter Timeout. Das ist der eigentliche Gewinn von AP5 gegenüber dem
heutigen Zustand.

## 3. Entscheidungen

| # | Frage | Entscheidung |
|---|---|---|
| E1 | Teilergebnis oder sauberer Abbruch? (offene Rückfrage 3 in AP5) | **Teilergebnis**, da ohne Eingriff in fremden Code erreichbar |
| E2 | Umfang | Beide Werkzeuge voll, plus harter Abbruch als Netz |
| E3 | Nachweis | Lokaler Fake-Endpunkt für wiederholbare Tests **und** ein kleiner scharfer Lauf fürs Protokoll |

Zu E1: die Rückfrage an den Betreuer war bei Erstellung offen (inzwischen
beantwortet: Teilergebnis, `BA-BETREUERGESPRAECH-AUFGABEN.md` Abschnitt 2,
Punkt 3), war aber entschärft — die gelieferte Variante ist die stärkere von
beiden und schließt die schwächere ein.

## 4. Entwurf

### 4.1 Zeitbudget: drei Marken aus einem `TIMEOUT`

Der Entrypoint rechnet aus `$2` drei Marken aus:

| Marke | Anteil | Wirkung |
|---|---|---|
| Deadline-Bremse | 70 % | keine neuen LLM-Aufrufe mehr; das Werkzeug läuft aus und schreibt seinen Report |
| Netz | 90 % | `timeout` beendet das Werkzeug, falls die Bremse nicht griff |
| Aufräumen | 90–100 % | der Entrypoint birgt den Teilstand und schreibt `/output.json` |
| Docker-Kill | 100 % | `sb/docker.py:185`, unverändert, letzte Instanz |

Die 70 % sind bewusst großzügiger als Mythrils 80 %: bei Mythril endet mit dem
Timeout die Rechnung, bei uns muss danach noch ein LLM-Aufruf zu Ende laufen
(bis zu 90 s, `ask_with_timeout`-Vorgabe) und ein Report geschrieben werden.

**`TIMEOUT=0` schaltet alles ab.** Ohne Timeout verhält sich die Integration
Byte für Byte wie bisher — Voraussetzung dafür, dass die 19 bereits gefahrenen
Messläufe vergleichbar bleiben.

### 4.2 Schnittstellenvertrag

Verbindlich für alle Beteiligten; wer eines dieser Felder ändert, ändert es an
allen Stellen zugleich.

**Übergabe an das Werkzeug.** Umgebungsvariable, kein CLI-Flag:

```
SB_DEADLINE_EPOCH   absoluter Unix-Zeitstempel in Sekunden (ganzzahlig)
                    ungesetzt oder leer = keine Deadline
```

Absolut, nicht als Dauer: GPTScan startet für jeden LLM-Aufruf einen Worker per
`multiprocessing`, und ein absoluter Zeitstempel bedeutet in jedem Kindprozess
dasselbe — eine Restlaufzeit nicht.

**Keine Änderung an den beiden `config.yaml` nötig.** Die `env:`-Zeile dort
regelt, welche Variablen vom *Host* in den Container gereicht werden. Die
Deadline entsteht dagegen im Container selbst: der Entrypoint rechnet sie aus
`$2` aus und exportiert sie für seinen Kindprozess.

**Marker im Ergebnis.** Gleicher Schlüssel in beiden Werkzeugen, oberste Ebene
des jeweiligen JSON:

```json
"sb_timeout": {
  "hit":    true,              // Timeout hat gegriffen
  "stage":  "brake" | "net",   // Bremse ausgelaufen oder hart beendet
  "detail": "28 von 41 Detektor-Kategorien geprüft"
}
```

`hit` und `stage` sind Pflicht, `detail` ist sprechender Freitext. Bewusst
*keine* einheitlichen Zählfelder: LLMSmartAudit hat mit den 41 Detektoren eine
natürliche Einheit, GPTScan nicht — dort ist die aussagekräftige Größe die Zahl
der wegen der Frist unterdrückten LLM-Aufrufe. Beide Werkzeuge führen ihre
jeweilige Zahl in ihren eigenen, bereits vorhandenen Feldern
(`categories_checked`/`categories_total` bzw. `llm_calls_skipped_deadline`); der
Marker verweist nur darauf.

Fehlt `sb_timeout` ganz, war der Lauf vollständig — Abwesenheit ist die Aussage
„kein Timeout".

**Exit-Code, normalisiert.** Der Entrypoint entscheidet, was SmartBugs sieht:

| Lage | Exit |
|---|---|
| Bremse griff, Werkzeug lief sauber aus | `0`, Marker im Report |
| Netz griff, Teilstand geborgen | `124` |
| Netz griff, nichts zu bergen | `124`, Report mit leerer Findings-Liste |

Die `124` wird **erzwungen**, nicht durchgereicht: GNU-`timeout` meldet 124,
BusyBox-`timeout` dagegen 143, und ein zu SIGKILL eskaliertes SIGTERM 137. Beide
letzteren stehen namentlich in `DOCKER_CODES` (`sb/parse_utils.py:8-15`) und
werden dort als `DOCKER_TERM` bzw. `DOCKER_KILL_OOM` nach **`fails`** gebucht —
also als „Werkzeug ausgehebelt", obwohl der Abbruch beabsichtigt war. Nur die 124
fällt durch alle Sonderfälle hindurch in den `else`-Zweig und landet als
`EXIT_CODE_124` in `errors`. Der Entrypoint fängt deshalb 124, 137 und 143 ab und
beendet sich einheitlich mit 124.

Die Vorprüfung (`docs/BA-AP5-VORPRUEFUNG.md`) hat für beide Images GNU-coreutils
nachgewiesen, der BusyBox-Fall tritt hier also nicht ein. Die Normalisierung
bleibt trotzdem: sie kostet nichts und deckt weiterhin die 137 ab.

### 4.3 GPTScan — Deadline-Bremse

Ein zweiter Wächter in `ask_with_timeout()`, in der Form des vorhandenen
Budget-Wächters (`analyze_pipeline.py:56-70`):

* Ist `SB_DEADLINE_EPOCH` gesetzt und überschritten, wird der Grund einmalig
  vermerkt und geloggt, jeder weitere Aufruf gibt sofort
  `deadline_sentinel(kind)` zurück und zählt `num_calls_skipped_deadline` hoch.
  Der Platzhalter ist bewusst ein eigener und nicht der des `--dry-run`: dieser
  antwortet überall bejahend, um eine Oberschranke abzuschreiten, und würde die
  Kandidatenliste nach der Bremse aufblähen. `deadline_sentinel` liefert
  ausnahmslos `"{}"` — an jeder Auswertungsstelle „keine Angabe".
* Die Prüfung liegt im Elternprozess, neben der Budget-Prüfung — dieselbe
  Begründung wie dort: unabhängig von der `multiprocessing`-Startmethode.

Die Pipeline merkt davon nichts und läuft normal bis `tasks.py:465` durch. Das
ist der Punkt: dort steht die Zusammenführung über `utils.convert_output`, die
bei einem Kill verloren ginge. Das Werkzeug schreibt sein Ergebnis selbst — die
Ausgabe ist damit per Konstruktion wohlgeformt.

Der Marker reist über den bereits bestehenden Metadaten-Kanal: `meta_data` wird
um `sb_timeout` ergänzt, der Entrypoint gibt die Datei als `GPTSCAN_META`-Zeile
aus (`do_solidity.sh:64-66`). Ein neuer Ausgabekanal ist nicht nötig.

Berührte Dateien, alle bereits auf der Eigenanteil-Liste: `src/analyze_pipeline.py`,
`src/chatgpt_api.py` (Zähler, analog zu `num_calls_skipped_budget`), `src/tasks.py`
(Metadatenfeld).

### 4.4 LLMSmartAudit — Flush nach jeder Phase

Hier ist der harte Abbruch unschädlich, sobald der Stand auf Platte liegt.
`audit_report.record()` schreibt nach jeder Phase den aktuellen Stand über den
vorhandenen `write_json()`-Pfad an einen festen Ort (`/tmp/sb_partial.json`).
41 kleine Schreibvorgänge stehen gegen Minuten LLM-Latenz je Phase; die Kosten
sind vernachlässigbar.

Läuft die Frist ab, beendet das Netz den Prozess, und der Entrypoint befördert
`/tmp/sb_partial.json` zu `/output.json`, setzt `sb_timeout.stage` auf `"net"`
und beendet sich mit 124. Verloren geht allein der Detektor, der gerade lief.

**ChatDevs Ablaufsteuerung bleibt unberührt** — kein Signal-Handler, keine
Exception quer durch fremden Kontrollfluss, keine neue geänderte Fremddatei.

### 4.5 Warum die beiden Werkzeuge verschieden behandelt werden

Nicht aus Bequemlichkeit, sondern weil sie verschieden gebaut sind: GPTScan
aggregiert, dedupliziert und schreibt **am Ende**, also muss es freiwillig
auslaufen dürfen. LLMSmartAudit hält nach jeder Phase einen vollständigen
Zwischenstand, also genügt es, diesen festzuhalten und danach abzubrechen.

Verallgemeinert: *ob sich ein Teilergebnis retten lässt, hängt daran, ob ein
Werkzeug inkrementell festhält oder erst am Schluss zusammenführt.* Dieser Satz
geht als Erkenntnis nach AP7.

### 4.6 Parser und Auswertung

Beide Parser (`smartbugs/tools/gptscan/parser.py`,
`smartbugs/tools/llmsmartaudit/parser.py`) lesen `sb_timeout` und erzeugen daraus
einen sprechenden Eintrag in `errors`, etwa
`TIMEOUT_PARTIAL (28/41 Kategorien geprüft)`. In `fails` gehört ein beherrschter
Timeout nicht — dort steht laut `docs/BA-ERRORS-VS-FAILS.md`, was das Werkzeug
ausgehebelt hat.

**Die Auswertung muss den Teillauf sehen.** Findings aus einem abgebrochenen Lauf
dürfen nicht wie Findings aus einem Volllauf zählen, sonst sinkt der Recall still,
ohne dass die Ursache im Ergebnis steht. `analysis_tools/gptscan_eval.py` und
`analysis_tools/errors_fails_report.py` bekommen deshalb zwei Spalten,
`timeout_hit` und `timeout_stage`, und weisen Läufe mit `sb_timeout.hit` in der
Zusammenfassung getrennt aus — als eigene Zeile „davon Teilläufe", nicht als
stille Beimischung.

## 5. Nachweis

### 5.1 Prüfstand: lokaler Fake-Endpunkt

Ein kleiner OpenAI-kompatibler HTTP-Dienst, der gültige, aber absichtlich langsame
Antworten liefert; aus dem Container heraus erreichbar unter
`host.docker.internal`.

**LLMSmartAudit kommt ohne Änderung dorthin** — `LLM_PROVIDER=custom` und
`LLM_BASE_URL` sind bereits vorgesehen (`tools/llmsmartaudit/config.yaml`).

**GPTScan nicht.** Die Provider-Tabelle in `GPTScan/src/config.py:41-67` kennt
genau zwei Einträge, `openai` und `deepseek`, beide mit fest hinterlegter
`base_url`. Für den Prüfstand braucht es dort einen dritten Eintrag nach dem
Vorbild von LLMSmartAudit: ein Provider, dessen `base_url` aus der Umgebung kommt
(`GPTSCAN_BASE_URL`), mit Preisen auf 0. Die Datei steht bereits auf der
Eigenanteil-Liste, und der Eintrag ändert nichts an den beiden vorhandenen
Providern. Diese Ergänzung gehört zu Aufgabe A, nicht zu C, weil sie in derselben
Datei liegt wie die Bremse.

Damit wird der Timeout kostenlos, deterministisch und beliebig oft auslösbar.
Der Dienst schließt nebenbei eine Lücke, die AP7 als Mangel führt („kein
Offline-/Stub-Modus, jeder Test kostet Geld") und hilft AP4 (Nachbaubarkeit ohne
API-Schlüssel).

### 5.2 Tests

| Ebene | Inhalt |
|---|---|
| Entrypoint | nach dem Muster von `tests/test_entrypoint_main.py` (echtes `sh`, Stubs auf PATH): Marken korrekt gerechnet, `TIMEOUT=0` ändert nichts, Exit-Code-Normalisierung, Bergung des Teilstands |
| Gleichheit | beide `do_solidity.sh` rechnen dieselben Marken — ein Test prüft beide gegen dieselbe Erwartung |
| GPTScan | Deadline-Bremse mit gestellter Uhr: nach Ablauf kein weiterer Aufruf, Zähler stimmt, Report wird geschrieben |
| LLMSmartAudit | `record()` hinterlässt nach jeder Phase eine vollständige, gültige Datei |
| Parser | neue Fixtures: Teilreport mit `sb_timeout`, für beide Werkzeuge, für `brake` und `net` |

### 5.3 Scharfer Lauf

2–3 Contracts je Werkzeug mit knapp bemessenem Timeout gegen den echten Endpunkt.
Ergebnis, Kosten und Laufzeit nach `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`.

## 6. Nicht im Umfang

* **Kein Timeout-Flag in den Werkzeugen.** Eine neue CLI-Option wäre eine
  Schnittstellenänderung an fremdem Code ohne Gewinn gegenüber der
  Umgebungsvariable.
* **Kein vorzeitiger Kettenabbruch in LLMSmartAudit.** Die Bremse würde dort
  Eingriffe in ChatDevs Ablaufsteuerung verlangen und spart nur den einen
  Aufruf, der beim Abbruch gerade läuft.
* **Keine Wiederaufnahme.** Ein abgebrochener Lauf wird nicht fortgesetzt.
* **Keine Änderung an `sb/docker.py`.** Der äußere Kill bleibt, wie er ist.

## 7. Risiken

| Risiko | Umgang |
|---|---|
| `timeout` fehlt in einem der beiden Images | **Zuerst prüfen.** Fällt es aus, ersetzt ein Watchdog im Skript (Hintergrundprozess plus `kill`) das Kommando — mehr Code, gleiche Wirkung |
| `host.docker.internal` nicht erreichbar | unter Docker Desktop/Windows vorhanden; sonst über die Bridge-IP; der scharfe Lauf hängt nicht davon ab |
| Bremse verändert das Ergebnis eines Laufs *ohne* Timeout | Bei `TIMEOUT=0` wird der Wächter gar nicht erst betreten; ein Test hält das fest |
| Teilergebnisse verfälschen spätere Auswertungen | Abdeckungsspalte plus getrennter Ausweis, Abschnitt 4.6 |
| Der Flush verlangsamt LLMSmartAudit merklich | am scharfen Lauf gegen die bekannten 3:02 h über 143 Contracts gegenprüfen |

## 8. Dokumentation, die nachzuziehen ist

* `docs/BA-BETREUERGESPRAECH-AUFGABEN.md` — AP5 auf erledigt, offene Rückfrage 3
  mit der getroffenen Entscheidung beantwortet.
* `docs/BA-EIGENANTEIL.md` — geänderte Dateien und Begründungen ergänzen.
* `docs/BA-BETRIEB.md`, `docs/BA-WERKZEUG-BEDIENUNG.md` — `--timeout` und das
  Verhalten beim Ablaufen.
* AP7-Material — zwei Punkte: die Werkzeuge bringen keinen eigenen Timeout mit,
  und die Rettbarkeit eines Teilergebnisses hängt an inkrementeller Ablage
  (Abschnitt 4.5).

## 9. Arbeitsteilung

Geschnitten nach Dateibesitz, damit parallel gearbeitet werden kann, ohne dass
zwei Beteiligte dieselbe Datei anfassen.

| | Aufgabe | Besitz | Abhängigkeit |
|---|---|---|---|
| **V** | Vorprüfung: `timeout` in beiden Images, Exit-Code messen | — (nur Befund) | keine, **zuerst** |
| **A** | GPTScan-Seite | `GPTScan/src/{analyze_pipeline,chatgpt_api,tasks,config}.py`, `tools/gptscan/scripts/do_solidity.sh`, `tools/gptscan/parser.py`, `tools/gptscan/config.yaml` + zugehörige Tests | V |
| **B** | LLMSmartAudit-Seite | `chatdev/audit_report.py`, `tools/llmsmartaudit/scripts/do_solidity.sh`, `tools/llmsmartaudit/parser.py`, `tools/llmsmartaudit/config.yaml` + zugehörige Tests | V |
| **C** | Prüfstand: Fake-Endpunkt, `tests/conftest.py` | eigene neue Dateien | keine |
| **D** | Auswertung: Abdeckungsspalte | `analysis_tools/gptscan_eval.py`, `errors_fails_report.py` | Vertrag aus 4.2 |
| **E** | Dokumentation | `docs/*` | A, B |
| **F** | Scharfer Lauf und Protokoll | Messdaten, `BA-DURCHFUEHRUNGSPROTOKOLL` | A, B, C |

A und B teilen genau zwei Dinge: den Namen `SB_DEADLINE_EPOCH` und die Form des
`sb_timeout`-Markers. Beides steht in Abschnitt 4.2 fest, **bevor** verteilt wird.

Die 70/90-Rechnung steht bewusst doppelt in beiden Entrypoints. Das entspricht
der Handhabung im Upstream — `mythril` und `honeybadger` duplizieren ihre
Timeout-Arithmetik ebenfalls, statt sie zu teilen — und ein gemeinsamer Test
hält beide Fassungen deckungsgleich.
