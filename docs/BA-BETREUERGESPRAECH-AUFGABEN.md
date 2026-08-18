# Aufgaben aus dem Betreuergespräch

Grundlage sind die Mitschriften aus dem Bachelorgespräch mit Betreuer
**Gernot Salzer** (GitHub-User `Gsalzer`). Dieses Dokument hält fest, *was zu tun
ist* — nicht, wie es umgesetzt wird. Die Umsetzungsplanung folgt je Arbeitspaket
separat.

> **Status:** Entwurf. Die Arbeitspakete sind aus Stichworten rekonstruiert und
> vor Arbeitsbeginn mit dem Betreuer abzugleichen. Offene Rückfragen stehen in
> Abschnitt 2.

---

## 1. Überblick

| # | Arbeitspaket | Art | Aufwand (grob) | Stand |
|---|---|---|---|---|
| AP1 | Terminologie: `error` → `Finding` / `Weakness` | Doku | S | **erledigt** |
| AP2 | Integrationstreue: Originaltool vs. SmartBugs | Experiment | L | offen |
| AP3 | Betreuer ins Repository einladen | Organisation | XS | offen |
| AP4 | Reproduzierbarkeit (a) fremd, (b) eigen | Experiment + Doku | L | offen |
| AP5 | Timeout ins Werkzeug durchreichen | Code | M | **erledigt** |
| AP6 | `MAIN`-Parameter umsetzen | Code | M | offen |
| AP7 | Meta-Findings-Dokument (LLM-Tools allgemein) | Doku | M | offen |
| AP8 | Aufwandsschätzung an den Betreuer mailen | Organisation | XS | offen |

XS = unter 1 h · S = 1–4 h · M = 4–12 h · L = 12–30 h

---

## 2. Offene Rückfragen an den Betreuer

1. **„Monar"** — in der Mitschrift ein Werkzeugname, direkt vor „Tool im
   Originalzustand außerhalb von Docker vergleichen". **Keines der 53
   SmartBugs-Werkzeuge heißt so** (nächste Kandidaten: `mando`, `maian`,
   `manticore`). Zwei Lesarten: entweder ein Werkzeug außerhalb von SmartBugs,
   oder schlicht „nochmal" als Füllwort. **Blockiert nichts** — die Anweisung
   selbst ist eindeutig (AP2). Bei Gelegenheit nachfragen.
2. **AP2, Vergleichsumfang** — reicht ein Beleg an wenigen Contracts, oder wird
   Deckungsgleichheit über einen ganzen Korpus erwartet? Letzteres kostet echtes
   Geld (LLM-Aufrufe doppelt).
3. **AP5, Zielverhalten bei Timeout — beantwortet: Teilergebnis.** Umgesetzt ist
   die stärkere der beiden Lesarten: Beim Ablaufen liefert das Werkzeug, was bis
   dahin ermittelt wurde, gekennzeichnet über den Marker `sb_timeout`. Begründung:
   Der Mechanismus lag in beiden Fällen (GPTScan läuft freiwillig aus,
   LLMSmartAudit hält nach jeder Phase einen Zwischenstand) in eigenem Code, nicht
   in fremdem — die stärkere Variante kostete damit keine zusätzliche Nachweislast
   in AP2 und schließt die schwächere (sauberer Abbruch mit Kennzeichnung) mit ein.
   Details im AP5-Abschnitt unten.

---

## 3. Arbeitspakete

### AP1 — Terminologie: `error` → `Finding` / `Weakness`

**Was gesagt wurde.** „Statt error → weakness oder findings." Und: „Tools suchen
NICHT errors sondern Verdachtsfälle, Name soll geändert werden. Finding ist ein
besserer Name."

**Worum es geht.** Ein Scanner stellt keine Fehler fest, sondern äußert einen
*Verdacht*. Die Wortwahl darf das nicht verwischen. SmartBugs trennt drei Dinge
sauber, und diese Trennung ist zu respektieren:

| Feld | Bedeutung |
|---|---|
| `findings` | Was das Werkzeug über den Contract **meldet** — der Verdachtsfall |
| `errors` | Das Werkzeug hat ein Problem **bemerkt und abgefangen**, lief weiter |
| `fails` | Das Werkzeug wurde **ausgehebelt** — Exception entkommen, Lauf kaputt |

Damit ist auch die Notiz „Fails sind was das Tool ausgehebelt wird" aufgelöst:
`fails` betreffen den *Zustand des Werkzeugs*, nie den Contract. Hergeleitet ist
das bereits in `docs/BA-ERRORS-VS-FAILS.md`.

**Zu tun.**
* Eigene Dokumente durchgehen: „Fehler" nur noch für Ausführungsfehler, nie für
  das, was ein Werkzeug über einen Contract sagt.
* Konkret falsch ist bisher **„DeFi-Logikfehler"** an drei Stellen
  (`README.md:9`, `docs/BA-DEMOLAUF-ERGEBNIS.md:443` und `:758`) — dort sind
  Findings gemeint.
* Gleiche Prüfung für Bezeichner und Ausgabetexte im **eigenen** Code.

**Abgrenzung (wichtig).** `errors` / `fails` / `findings` sind **SmartBugs'
eigene Feldnamen** in `result.json` und SARIF. Sie bleiben unangetastet — eine
Umbenennung würde die Ausgabe inkompatibel zum Framework des Betreuers machen.
Geändert wird ausschließlich unsere Prosa und unser eigener Code.

**Stand: erledigt.** Maßgeblich ist, wer im Satz das Subjekt ist — Werkzeug →
*Finding*, Ground Truth → *Schwachstelle*, Ausführung → *Fehler*. Die Regel steht
als Abschnitt „Wortwahl in dieser Arbeit" in `docs/BA-ERRORS-VS-FAILS.md`, aus
`README.md` verlinkt. Korrigiert wurden die drei „DeFi-Logikfehler"-Stellen sowie
`smartbugs/tools/gptscan/config.yaml`, dessen `info`-Text („GPTScan *detects* DeFi
logic *vulnerabilities*") bei `sb --tools` angezeigt wird.

Die Durchsicht der übrigen ~78 „Fehler"- und ~15 „Schwachstelle"-Vorkommen ergab
**keinen weiteren Änderungsbedarf**: sie bezeichnen durchweg Ausführungsfehler
(Compile-Fehler, Exit-Codes, Tracebacks) oder belegte Ground Truth. Im eigenen
Code war nichts zu ändern — `analysis_tools/errors_fails_report.py` benutzt
`errors`/`fails` als SmartBugs-Feldnamen und dokumentiert die Semantik bereits
korrekt, `evaluate_curated.py` liest die fremde Datei `vulnerabilities.json`, und
beide `findings.yaml` sprechen durchgehend von *findings*.

---

### AP2 — Integrationstreue: Originaltool gegen SmartBugs

**Was gesagt wurde.** „SmartBugs-Integration von den Tools mit den Original-Tools
(GPTScan, LLMSmartAuditTool), ob alles richtig ist." Und: „Tool im
Originalzustand außerhalb von Docker vergleichen mit SmartBugs. Zu testen ob es
transparent ist."

**Worum es geht.** Der Nachweis, dass unsere Integration das Werkzeug **nicht
verändert**. Solange der nicht vorliegt, steht hinter jedem Messwert die Frage,
ob er das Werkzeug misst oder unseren Wrapper.

**Zu tun.**
* Beide Werkzeuge im Originalzustand aufsetzen — nativ, ohne Docker, ohne
  SmartBugs, mit der Aufrufform aus der jeweiligen Upstream-Dokumentation.
* Dieselben Contracts durch beide Wege schicken und gegenüberstellen: gefundene
  Findings, deren Zuordnung, Laufzeit, Kosten.
* Abweichungen benennen und einordnen: Wrapper-Artefakt oder LLM-Streuung?
  **Das ist der Knackpunkt** — beide Werkzeuge sind nicht deterministisch (siehe
  AP4), eine einzelne Abweichung beweist für sich genommen nichts.
* Ergebnis als Dokument, das die Transparenz belegt oder die Grenzen benennt.

**Bekannte Eingriffe, die dabei geprüft gehören** (aus `docs/BA-EIGENANTEIL.md`):
7 geänderte Dateien in GPTScan, 9 in LLMSmartAuditTool, 5 in `smartbugs/sb/`.
Für jede ist zu zeigen, dass sie das Analyseergebnis nicht beeinflusst.

---

### AP3 — Betreuer ins Repository einladen

**Was gesagt wurde.** „SmartBugs Gsalzer ins GitHub inviten."

**Zu tun.** GitHub-User `Gsalzer` als Collaborator zu `Alex-Hofer/BA-Smartbugs-llm`
einladen (privates Repository).

**Vorher prüfen.** Der Secret-Scan ist über den Arbeitsbaum sauber
(1121 Dateien, kein Fund), und die Messdaten sind nicht getrackt. Vor der
Einladung ein letzter Durchlauf `python analysis_tools\secret_scan.py --all`.
Danach ist das Repository für ihn sichtbar — der `README.md`-Einstieg sollte
dann stimmen.

---

### AP4 — Reproduzierbarkeit

**Was gesagt wurde.** „Reproduzierbarkeit machen/testen." Und: „Reproduzierbarkeit.
Laufzeit zum Finden."

**Zwei getrennte Fragen. Reihenfolge: (b) zuerst.**

**(b) Nachbaubarkeit — hat Vorrang.** Kann ein Dritter das Repository klonen und
die Ergebnisse herstellen? Zu klären ist die ganze Kette: Images bauen,
Abhängigkeiten, `smartbugs-curated` beziehen, Umgebungsvariablen, `solc`,
Windows-Eigenheiten. Der ehrliche Teil der Antwort ist, dass die
LLM-Läufe **kostenpflichtig** sind und ein API-Schlüssel gebraucht wird — das
gehört benannt, nicht kaschiert. Die Vorarbeit liegt in `docs/BA-BETRIEB.md` und
`docs/BA-WERKZEUG-BEDIENUNG.md`; was fehlt, ist der **Beweis**, dass eine fremde
Maschine damit durchkommt.

**(a) Wiederholbarkeit der Messung.** Liefert derselbe Lauf dasselbe Ergebnis?
Teilantwort liegt vor: beim mwevariety-Vergleich waren **trotz `temperature=0`
nur 74 % der Findings identisch** (20 von 27 Contracts; 3 Findings verschwunden,
2 neu, 2 verändert). Das ist als systematische Messung auszubauen — mehrfache
Läufe über dieselbe Menge, Streuung beziffert.

**Laufzeit als Messgröße.** Laufzeit ist mitzuerheben und auszuweisen, nicht nur
Recall/Precision. Vorhandene Bezugswerte: Slither 1:24 min · GPTScan 3:19 min ·
LLMSmartAudit 3:02 h — jeweils über 143 Contracts.

---

### AP5 — Timeout ins Werkzeug durchreichen

**Was gesagt wurde.** „Timeout vlt einbauen und integrieren (bei Docker geht
es?)." Und: „Vielleicht in Docker Container. (Arbeiten mit Timeout.) Docker ist
hier die Notlösung wenn es im Tool nicht vorhanden ist."

**Befund — er hat recht, und die Lücke ist lokalisiert.** SmartBugs übergibt
jedem Entrypoint vier Argumente: `FILENAME TIMEOUT BIN MAIN`. Unsere beiden
Integrationen nehmen `TIMEOUT` entgegen und **verwenden es nicht**:

* `smartbugs/tools/gptscan/scripts/do_solidity.sh:5`
* `smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh:5`

So, wie es jetzt ist, greift nur der äußere Docker-Timeout
(`smartbugs/sb/docker.py:185-189`): der Container wird von außen abgeschossen,
das Werkzeug erfährt nichts davon und kann kein Teilergebnis sichern.

**Referenz aus dem Upstream.** `smartbugs/tools/mythril-0.23.15/scripts/do_solidity.sh:25-30`
rechnet den SmartBugs-Timeout auf 80 % herunter und reicht ihn dem Werkzeug als
`--execution-timeout` weiter. Das ist das Muster, an dem sich unsere
Integrationen messen lassen müssen.

**Zu tun.**
* Prüfen, ob GPTScan und LLMSmartAudit überhaupt einen eigenen Timeout kennen.
  Ersteinschätzung: eher nicht — LLMSmartAudit hat nachweislich auch keine
  Kostenbremse.
* Wo vorhanden: durchreichen, nach dem Mythril-Muster mit Sicherheitsabstand.
* Wo nicht vorhanden: den Docker-Timeout als das ausweisen, was er ist — eine
  **Notlösung**. Genau diese Unterscheidung gehört als Erkenntnis in AP7.

**Stand: erledigt.** Beide Werkzeuge kennen keinen eigenen Lauf-Timeout —
GPTScan hat eine Frist je einzelnem LLM-Aufruf, LLMSmartAudit gar keine (siehe
AP7 unten). Umgesetzt wurde deshalb ein Mechanismus, der den von SmartBugs
übergebenen `TIMEOUT` innerhalb des Containers nutzt, statt sich allein auf den
äußeren Docker-Abschuss zu verlassen: Der jeweilige Entrypoint rechnet aus
`TIMEOUT` drei Marken (70 % Bremse, 90 % Netz, Rest fürs Aufräumen) und
exportiert die Bremse als absoluten Zeitstempel `SB_DEADLINE_EPOCH`. GPTScan
wertet ihn in seiner zentralen LLM-Messstelle aus und läuft freiwillig aus, ohne
neue LLM-Aufrufe zu starten; LLMSmartAudit schreibt stattdessen nach jeder der
41 Detektor-Phasen einen Zwischenstand, den der Entrypoint nach einem harten
Abbruch durch `timeout` birgt. Beide Wege tragen denselben Marker `sb_timeout`
(Felder `hit`, `stage` mit `"brake"`/`"net"`, `detail`) im Ergebnis, und ein
per Netz beendeter Lauf meldet einheitlich Exit-Code 124, unabhängig davon, was
`timeout` selbst zurückgab. `TIMEOUT=0` (kein `--timeout`) ändert nichts am
bisherigen Verhalten — geprüft für beide Werkzeuge, damit die 19 bereits
gefahrenen Messläufe vergleichbar bleiben. Belegt sind 108 grüne Tests, eine
Vorprüfung des `timeout`-Kommandos in beiden Images
(`docs/BA-AP5-VORPRUEFUNG.md`) sowie die vollständige Dateibilanz in
`docs/BA-EIGENANTEIL.md` — **keine einzige neue Fremddatei**. Der Messlauf
gegen echte Endpunkte mit einem tatsächlich ablaufenden Timeout steht noch aus.

Bewusst **nicht** umgesetzt:
* kein Timeout-Flag in den Werkzeugen selbst (wäre eine Schnittstellenänderung
  an fremdem Code ohne Gewinn gegenüber der Umgebungsvariable),
* kein vorzeitiger Kettenabbruch in LLMSmartAudit (verlangte Eingriffe in
  ChatDevs Ablaufsteuerung und spart nur den einen gerade laufenden Aufruf),
* keine Wiederaufnahme abgebrochener Läufe,
* keine Änderung an `sb/docker.py` — der äußere Docker-Timeout bleibt als
  letzte Instanz bestehen, falls der innere Mechanismus versagt.

---

### AP6 — `MAIN`-Parameter umsetzen

**Was gesagt wurde.** „Parameter um auszuwählen welche Art von Contract
analysiert werden. Damit nicht alles analysiert wird. Es heißt meist main."

**Befund — dieselbe Lücke wie AP5.** SmartBugs hat dieses Konzept bereits: bei
`MAIN=1` soll ein Werkzeug nur den **Hauptcontract** analysieren, also den, dessen
Name zur Datei passt — nicht zusätzlich jede Bibliothek, jedes Interface, jeden
mitimportierten Contract. `sb/docker.py:120` setzt den Wert, beide Entrypoints
nehmen ihn als `$4` entgegen und **ignorieren ihn**:

* `smartbugs/tools/gptscan/scripts/do_solidity.sh:7`
* `smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh:7`

**Referenz aus dem Upstream.** `smartbugs/tools/mythril-0.23.15/scripts/do_solidity.sh:16-22`
hängt bei `MAIN=1` `:ContractName` an den Dateinamen und bricht mit Exit-Code 127
ab, wenn der Contract in der Datei nicht vorkommt. `honeybadger` macht es
analog.

**Warum das mehr ist als Kosmetik.** Es betrifft die Messung selbst: Findings in
mitgelieferten Bibliotheken zählen derzeit mit. Das trifft die Precision-Zahlen
und erklärt womöglich einen Teil der 468 nicht zugeordneten
LLMSmartAudit-Findings. Zusätzlich spart es Geld und Laufzeit.

**Zu tun.** Umsetzen, soweit die Werkzeuge eine Contract-Auswahl anbieten. Wenn
nicht: ebenfalls als Erkenntnis nach AP7 — ein Werkzeug ohne Contract-Auswahl
zwingt zu Messrauschen.

---

### AP7 — Meta-Findings-Dokument

**Was gesagt wurde.** „Meta Findings." Und: „Aus Erkenntnissen sollten
Empfehlungen, Standards ausgegeben werden." Und: „Dokument aus METAFINDINGS
(LLM-Tools allgemein)."

**Worum es geht.** Nicht was die Werkzeuge über Contracts sagen, sondern was
**wir über die Werkzeuge** gelernt haben — verallgemeinert auf LLM-gestützte
Analysewerkzeuge und formuliert als Empfehlung, was ein solches Werkzeug
mitbringen muss.

**Form.** Eigenständiges Dokument, zunächst getrennt von der Arbeit. Die
Bachelorarbeit wird später ohnehin neu verfasst; dann wandert der Inhalt dorthin.

**Material, das schon vorliegt** — jeder Punkt ist am eigenen Material belegt:

| Erkenntnis | Beleg |
|---|---|
| Kein eigener Timeout, keine Kostenbremse | LLMSmartAudit; Docker als Notlösung (AP5) |
| Keine Auswahl des zu prüfenden Contracts | AP6 |
| Kein Offline-/Stub-Modus → jeder Test kostet Geld | `LLM_MODEL=STUB` geht verbatim an die API |
| Nicht-Determinismus trotz `temperature=0` | 74 % Übereinstimmung bei Wiederholung |
| Stilles Scheitern statt Fehlermeldung | GPTScan: solc bricht ab, Exit-Code 0, `results: []` |
| Severity ist Kategorie-Default, kein Einzelfallurteil | 100 % konstant je Detektorname über 1.124 Findings |
| Keine Zeilennummern | LLMSmartAudit: SARIF ohne `region` |
| Modellname fest im Image → Werkzeug veraltet still | `deepseek-chat` abgeschaltet, HTTP 400 |
| Ground-Truth-Formate passen nicht zum Werkzeug-Output | Single-Label + DASP-only verzerrt die Precision |
| Keine Angabe von Kosten und Laufzeit im Ergebnis | musste extern erhoben werden (`GPTSCAN_META`) |
| Kein Werkzeug bringt einen Timeout für den gesamten Lauf mit | GPTScan kennt nur eine Frist je einzelnem LLM-Aufruf (`ask_with_timeout(..., timeout=90)`), LLMSmartAudit gar keine — Optionslisten beider Werkzeuge, AP5 (Spec `docs/BA-AP5-TIMEOUT-DESIGN.md`, Abschnitt 2.1) |
| Ob sich ein Teilergebnis retten lässt, hängt an der Ablageform des Werkzeugs, nicht an einem gemeinsamen Muster | GPTScan aggregiert und dedupliziert erst am Ende und muss deshalb freiwillig auslaufen dürfen; LLMSmartAudit hält nach jeder Phase einen vollständigen Zwischenstand und braucht nur Festhalten-und-Abbrechen. Dieselbe Anforderung erzwang zwei verschiedene Lösungen — AP5 (Spec Abschnitt 4.5) |

**Zu tun.** Erkenntnisse sammeln, je Punkt Beleg und Empfehlung formulieren, als
Anforderungsliste an LLM-Analysewerkzeuge zusammenführen. AP2, AP4, AP5 und AP6
liefern weitere Punkte nach — das Dokument wächst mit ihnen und wird deshalb
**früh angelegt, aber spät abgeschlossen**.

---

### AP8 — Aufwandsschätzung an den Betreuer

**Was gesagt wurde.** „Zeitaufwand berechnen und bei Mail senden."

**Zu tun.** Die Schätzung in Abschnitt 4 prüfen, an die eigene Erinnerung
anpassen und per Mail schicken.

---

## 4. Aufwandsschätzung der bisherigen Arbeit

> **Lies das kritisch.** Die Zählungen sind gemessen, die Stunden sind
> *geschätzt*. Niemand hat mitgestoppt. Die Zahlen sind bottom-up aus dem
> hergeleitet, was tatsächlich entstanden ist — belastbar als Größenordnung,
> nicht als Abrechnung.

### 4.1 Was messbar vorliegt

| Größe | Wert |
|---|---|
| Eigener Code | **6.121 Zeilen** (Python, PowerShell, Shell, YAML) |
| Eigene Dokumentation | **~31.600 Wörter** über 24 Dokumente, davon 4 in LaTeX |
| Geänderte Fremddateien | **21** (7 GPTScan · 9 LLMSmartAudit · 5 SmartBugs), je per Datei-Hash gegen Upstream belegt |
| Werkzeug-Integrationen | **2** vollständig (Dockerfile, Entrypoint, Config, Findings-Mapping, Parser) |
| Docker-Images | **2** selbst gebaut, eines von 5,13 GB auf 590 MB reduziert |
| Messläufe | **19 Läufe · 930 Tasks · 4.461 Dateien · 258 MB** |
| Rekonstruierter Korpus | **96 Contracts**, von 1/96 auf 96/96 kompilierbar gebracht |
| Parser-Reparatur | **1368 → 0** verlorene Rohmeldungen |
| Regressionstests | **44**, Fixtures aus echten Läufen |
| Belegter Kalenderzeitraum | 2026-07-05 bis 2026-08-03 (Git), zuzüglich einer Vorphase |

Zur Vorphase: die Läufe `assign6_*` und `phase6_*` sowie die fertigen
Auswertungen unter `GPTScan/reports/` sind **älter als der erste Commit**. Die
Integration war am Tag des ersten Commits bereits lauffähig. Diese Vorarbeit ist
im Git nicht datierbar und in der Tabelle unten mit einer eigenen Zeile
berücksichtigt.

### 4.2 Schätzung nach Arbeitspaketen

| Arbeitspaket | Stunden |
|---|---|
| Einarbeitung: SmartBugs, Docker, solc, Quellcode beider Werkzeuge | 25–35 |
| Integration GPTScan (inkl. Keyword-Filter-Falle, Metadaten-Kanal) | 30–40 |
| Integration LLMSmartAudit (Image-Reduktion, Report-Lokalisierung, 41 Detektoren abbilden) | 30–40 |
| Patches in `smartbugs/sb/` (Schlüssel-Durchreichung samt Redaktion) | 8–12 |
| Messkampagne: 19 Läufe, Smoke/Dry/Gates, Kosten- und Rate-Limit-Forensik | 35–45 |
| Auswertung: Recall/Precision/F1, DASP-Mapping, Stichproben am Quellcode | 30–40 |
| Korpus-Rekonstruktion `mwevariety_fixed` | 40–55 |
| Parser-Audit und -Reparatur (inkl. Silent-Failure-Diagnose) | 30–40 |
| Qualitätssicherung: 44 Tests, Verifikationsbericht, Errors/Fails-Report | 25–35 |
| Sicherheit und Repo-Hygiene (Secret-Scan, Redaktion, Neugründung, Lizenzen) | 15–20 |
| Dokumentation (~31.600 Wörter, Eigenanteil-Nachweis per Hash) | 45–60 |
| Betreuung, Abstimmung, Organisation | 8–12 |
| **Summe** | **320–435** |

**Mittelwert rund 375 Stunden.**

### 4.3 Zwei Lesarten — und welche in die Mail gehört

Die Arbeit wurde durchgehend KI-gestützt durchgeführt; das ist in
`.claude/INFOS/PROJEKT-STATUS.md` als Vorgehen dokumentiert. Das trennt zwei
Zahlen, die nicht verwechselt werden dürfen:

* **Tatsächlich aufgewendete Zeit: geschätzt 180–240 Stunden.** Code und
  Fließtext entstanden deutlich schneller als in Handarbeit. Nicht beschleunigt
  wurde alles andere: Messläufe brauchen ihre Laufzeit (allein der
  LLMSmartAudit-Volllauf 3 Stunden), Ergebnisse mussten gelesen, geprüft und
  am Quellcode verifiziert werden, und die Diagnosen — der Silent Failure, das
  abgeschaltete Modell, die 1368 Lücken — kosteten Nachdenken unabhängig vom
  Werkzeug.
* **Äquivalenter Aufwand in Handarbeit: 320–435 Stunden.** Das ist der Umfang
  des Ergebnisses, gemessen an dem, was entstanden ist.

**Empfehlung für die Mail:** die tatsächlich aufgewendete Zeit nennen, den
Umfang des Ergebnisses daneben stellen und den Einsatz KI-gestützter Werkzeuge
offenlegen. Das ist die Angabe, die einer Nachfrage standhält — und beim Autor
von SmartBugs ist mit Nachfragen zu rechnen.

**Vor dem Versand gegenprüfen.** Diese Schätzung kennt nur, was im Repository
Spuren hinterlassen hat. Sie kennt keine Literatur, keine Sackgassen, keine
Lehrveranstaltung, aus der die `assign6`-Läufe stammen. Der eigenen Erinnerung
ist mehr zu trauen als dieser Tabelle.

---

## 5. Vorgeschlagene Reihenfolge

1. **AP3** (Einladung) und **AP8** (Aufwand mailen) — beides kurz, beides
   erwartet er.
2. **AP6** und **AP5** — die beiden Code-Lücken sind lokalisiert, das Muster
   liegt im Upstream vor. AP6 zuerst, weil es die Messung berührt.
3. **AP4 (b)** — Nachbaubarkeit. Vorrang laut Absprache, und Voraussetzung
   dafür, dass der Betreuer selbst etwas nachvollziehen kann.
4. **AP2** — Integrationstreue. Aufwendig und kostenpflichtig, deshalb erst,
   wenn AP5/AP6 das Verhalten nicht mehr verändern.
5. **AP4 (a)** — Streuung systematisch messen. Läuft mit AP2 zusammen, weil
   beide dieselben Wiederholungsläufe brauchen.
6. **AP1** — Terminologie. Jederzeit möglich, aber sinnvoll erst am Ende, wenn
   keine neuen Texte mehr entstehen.
7. **AP7** — Meta-Findings. Früh anlegen, mit jedem Arbeitspaket ergänzen, zum
   Schluss abschließen.
