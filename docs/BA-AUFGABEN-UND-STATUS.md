# Aufgaben und Status

> Datierte Momentaufnahme · aktueller Stand im Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Was zu tun war, was wir davon erledigt haben und was offen bleibt.
Stand 2026-08-02. Die Ausführung steht in
[`BA-ARBEITSBERICHT-20260802.md`](BA-ARBEITSBERICHT-20260802.md).

> **Datierter Bericht.** Die Zahlen und Statusangaben sind der Stand vom
> 02.08.2026 (19 Läufe, 930 Tasks). Spätere Änderungen stehen in den
> Nachträgen weiter unten (21.09. und 25.09.2026) und in den lebenden
> Dokumenten, die die `README.md` unter „Dokumentation“ führt.

---

## Teil A — Die vier Hauptaufgaben aus dem Auftrag

### Ziel 1: Parser-Vollständigkeit — nichts darf verlorengehen

| Teilaufgabe | Status |
|---|---|
| Audit-Werkzeug (Rohmaterial gegen Parser-Output) | **erledigt** — `analysis_tools/parser_audit.py` |
| Lückenbericht über alle 19 Läufe | **erledigt** — `docs/parser-audit-vorher.md` |
| Parser reparieren, alle Lücken schließen | **erledigt** — 1368 → 0 Lücken |
| GPTScan-Silent-Failure sichtbar machen | **erledigt** |
| Tool-interne Python-Crashes sichtbar machen | **erledigt** |
| Static-Filtering nicht als Fehler werten | **erledigt** — erscheint als `info` mit Zahlen |
| Regressionstests mit Fixtures aus echten Altläufen | **erledigt** — 41 Parser-Tests (Suite gesamt 44) |
| Fixtures vorher auf Klartext-Schlüssel prüfen | **erledigt** — Prüfung bricht ab, statt einen Fund zu kopieren |
| Synthetische Fälle als solche kennzeichnen | **erledigt** — `synthetic` im Testnamen |
| Auswirkung messen (reparse, results2csv, evaluate) | **erledigt** — `docs/parser-fix-vorher-nachher.md` |

### Ziel 2: Errors und Fails sauber getrennt ausgeben

| Teilaufgabe | Status |
|---|---|
| Report-Skript über beliebige Ergebnisordner | **erledigt** — `analysis_tools/errors_fails_report.py` |
| Anzahl Errors / Fails, betroffene Contracts, Meldung im Wortlaut, saubere Tasks | **erledigt** |
| Ausgabe als CSV **und** Markdown | **erledigt** — `docs/errors-fails.{csv,md}` |
| Zusammenfassung am Ende von `run_curated.ps1` | **erledigt** — mit Einschränkung, siehe Teil C |
| Semantik dokumentieren, aus `parse_utils.py` hergeleitet | **erledigt** — `docs/BA-ERRORS-VS-FAILS.md` |

### Ziel 3: Dokumentation und Kommentare

| Teilaufgabe | Status |
|---|---|
| `README.md` im Repo-Root | **erledigt** |
| `LICENSE` | **erledigt** — MIT für den Eigenanteil, Fremdlizenzen getrennt ausgewiesen |
| Hinweis zur Entfernung von `evaluation/` mit Begründung und Backup-Verweis | **erledigt** — im README |
| Kommentare/Docstrings für eigenen Code | **erledigt bis auf interne Helfer**, siehe Teil C |
| Änderungen an Fremdcode kenntlich machen (was und warum) | **erledigt** — `docs/BA-EIGENANTEIL.md`, per Datei-Hash gegen Upstream abgeglichen |
| Betriebsdoku (Parameter, Env-Variablen, Fallstricke, Kosten) | **erledigt** — `docs/BA-BETRIEB.md` |

### Ziel 4: Cleanup und Sicherheit

| Teilaufgabe | Status |
|---|---|
| 62 Ergebnisdateien redigieren, **nicht** löschen | **erledigt** — Backup vorher, alle 930 Task-Logs gegen das Backup verifiziert |
| Secret-Scan-Schritt (Hook/Skript, Windows-tauglich) | **erledigt** — `analysis_tools/secret_scan.py`, Hook installiert |
| `.gitignore` final durchsehen | **erledigt** — vier Lücken geschlossen |
| Toter Querverweis in `BA-DURCHFUEHRUNGSPROTOKOLL` | **erledigt** — nach Vorgabe, in `.md` und `.tex` |
| Empfehlung zu den Thesis-PDFs | **erledigt** — Empfehlung „drinlassen", bestätigt |

---

## Teil B — Die vier Stichpunkte

### 1. Errors vs. Fails sauber ausgeben

**Erledigt.**

* `analysis_tools/errors_fails_report.py` gibt je Lauf und Werkzeug aus: Tasks,
  sauber durchgelaufene Tasks, Tasks mit Errors, Tasks mit Fails, Zahl der
  Errors, Zahl der Fails, Tasks mit gescheitertem Compilat.
* Jede Meldung im Wortlaut, mit den betroffenen Contracts.
* CSV und Markdown, letzteres übernahmefertig.
* Bilanz über alle 19 Läufe: **930 Tasks — 586 sauber, 344 mit Errors, 50 mit
  Fails, 246 mit gescheitertem Compilat.**
* Die Semantik ist aus `sb/parse_utils.py` hergeleitet, nicht erfunden
  (`docs/BA-ERRORS-VS-FAILS.md`): warum ein beliebiger Exit-Code ≠ 0 als *error*
  gilt, warum slither deshalb `EXIT_CODE_255` verwirft, und die drei
  Beobachtungen, die wie Defekte aussehen und keine sind.

**Offen:** die Einbindung in `run_curated.ps1` ist per Syntaxprüfung und per
echtem Aufruf auf vorhandenen Ergebnisordnern validiert, aber **nie in einem
vollständigen Massenlauf** durchlaufen — das hätte Docker und Geld gekostet.

### 2. Sicherstellen, dass nichts durch den Parser verlorengeht

**Erledigt — mit einer Einschränkung, die zu beachten ist.**

* Vorher: **1368 von 1464 Rohmeldungen gingen verloren**, restlos alle im
  GPTScan-Parser. slither und LLMSmartAudit: null Lücken.
* Nachher: **0 Lücken** über alle 930 Tasks.
* Der Nachweis ist jederzeit wiederholbar: `python analysis_tools/parser_audit.py`
  (~23 s über alle Läufe).

**Einschränkung 1 — Meldungen werden gekürzt.** `sb.parse_utils.truncate_message`
kürzt Meldungen ab 205 Zeichen, indem es die Mitte durch `...` ersetzt. Das ist
SmartBugs-Konvention und wird von allen Werkzeugen so gehandhabt. Für sehr lange
Meldungen — etwa eine mehrzeilige solc-Diagnose — steht in `result.json` also
Anfang und Ende, nicht die Mitte. **Der vollständige Text bleibt unverändert in
`result.log`**, das der Parser nie anfasst. Das Audit toleriert diese Kürzung
bewusst (40-Zeichen-Vergleich), sonst würde es die Upstream-Konvention selbst als
Datenverlust melden.

**Einschränkung 2 — das Audit kennt nur seinen Katalog.** Die Detektoren wurden
aus den 19 vorhandenen Läufen abgeleitet. Eine Meldungsart, die dort nie vorkam,
würde nicht als fehlend erkannt. Nach einem Werkzeug-Update lohnt ein Blick in
den Katalog (`parser_audit.py`, Abschnitt „Detector patterns").

**Einschränkung 3 — die Entzerrung der `rich`-Logs ist nicht zeichengenau.**
`rich` füllt jede Zeile auf Blockbreite auf; ob an einem Leerzeichen oder mitten
im Token umgebrochen wurde, ist hinterher nicht mehr unterscheidbar. Das ist am
Material geprüft, nicht vermutet. Betroffen sind lange Pfade
(`14_YieldSourcePrizePool.so l`), nicht Exception-Namen oder Meldungstexte.

### 3. Cleanup, Sicherheit, Dokumentation — damit die Einladung möglich wird

**Erledigt bis auf zwei Punkte, die noch offen sind.**

* Der DeepSeek-Key ist aus den Messdaten entfernt: 62 Task-Logs redigiert, alle
  930 gegen das Backup verifiziert. Er existiert nur noch in der git-ignorierten
  `GPTScan/.env`.
* `secret_scan.py` ist als pre-commit-Hook aktiv und in beide Richtungen
  gegengeprüft: 1121 Dateien ohne Falschtreffer, ein eingeschleuster Test-Key
  wird gefunden und blockiert den Commit.
* `README.md`, `LICENSE`, `docs/BA-EIGENANTEIL.md`, `docs/BA-BETRIEB.md` neu.
* `.gitignore` ergänzt (u. a. `.pytest_cache/`, das bisher nur durch pytests
  eigene Datei ignoriert wurde).
* 3,4 MB Testlauf-Reste aus dem Fremdcode entfernt, extern gesichert.

**Offen — beides bewusst nicht gemacht:**

* **Die fünf Commits waren zunächst nicht gepusht** (Push erst nach
  Freigabe; inzwischen erledigt, siehe Nachtrag in Teil C).
* **Der Betreuer war noch nicht eingeladen** (inzwischen erledigt, AP3 in
  `BA-BETREUERGESPRAECH-AUFGABEN.md`).

### 4. Alle Fehlermeldungen einbeziehen, auch die falschen

**Erledigt.**

Der `TypeError: 'NoneType' object is not subscriptable`, der nur Folge eines
gescheiterten Compilats ist, steht unverändert im Ergebnis. Nichts wird
gefiltert, nichts umgeschrieben. Die Einordnung Ursache/Folge steckt in einer
**zusätzlichen Spalte**, nie in einer Ersetzung:

| `classification` | Bedeutung |
|---|---|
| `root_cause` | Die Meldung benennt das Compilat selbst |
| `consequence` | Jede andere Meldung in einem Task mit gescheitertem Compilat |
| `independent` | Der Contract wurde übersetzt; die Meldung steht für sich |

Ein Regressionstest sichert das ab
(`test_messages_are_passed_through_unrewritten`). Es gilt dieselbe
Einschränkung wie unter Punkt 2: gekürzt wird nach SmartBugs-Konvention,
verworfen wird nichts.

---

## Teil C — Was wir offen lassen

> **Nachtrag 21.09.2026.** Teil C beschreibt den Stand vom 02.08.2026. Vier
> Angaben sind seitdem überholt und unten an Ort und Stelle richtiggestellt:
> der Push ist erfolgt (`origin/main` aktuell, am Abend des 21.09.2026 bei 83 Commits), der pre-commit-Hook
> ist versioniert, die `.tex`-Fassungen existieren nicht mehr, und die
> History umfasst nicht mehr 13 Commits. Die übrigen Punkte gelten
> unverändert. Der Rest des Dokuments ist historischer Stand und wird nicht
> nachgeführt.
>
> **Ein Punkt kam neu hinzu und ist erledigt.** Die oben und in Teil A/B
> berichteten „0 Lücken" des Parser-Audits galten für den damaligen
> Detektor-Katalog. Ein am 21.09.2026 ergänzter Detektor für allein stehende
> Ausnahme-Abschlusszeilen legte **10 echte Lücken** frei, alle im Lauf
> `llmsa_mwefixed_v2`: `sb/parse_utils.py` griff die Token-Buchhaltung des
> Werkzeugs als Ausnahme ab und erreichte die eigentliche Ursache nie. Behoben
> im eigenen Tool-Parser, `reparse` über alle Läufe gefahren; das Audit meldet
> jetzt **0 Lücken bei 2 417 Rohmeldungen** — diesmal belegt statt per Katalog.
> Keine Kennzahl der Arbeit hat sich dadurch bewegt. Hergeleitet in
> [`BA-PARSER-AUDIT-LUECKEN.md`](BA-PARSER-AUDIT-LUECKEN.md).

### Offene Entscheidungen

**1. Push und Einladung.** ~~Fünf Commits liegen lokal.~~ **Erledigt:** Das
Repo ist gepusht, `origin/main` ist aktuell (Stand 21.09.2026 abends: 83
Commits, nichts liegt lokal).

**2. Das Durchführungsprotokoll ist an einer Stelle überholt.** In
`BA-DURCHFUEHRUNGSPROTOKOLL.md` steht bei Fehler #4 (Silent Failure) als
Maßnahme *„Parser-Fix als Empfehlung dokumentiert"*. Der Fix ist jetzt gemacht.
Der Eintrag gehört zur Darstellung der Arbeit und wurde zunächst nicht
geändert. *(Nachtrag 21.09.2026: nur noch in der
`.md`-Fassung — die `.tex`-Fassungen wurden nach Markdown überführt und aus dem
Repository entfernt, siehe `README.md`, Abschnitt „Dokumentation". Nachtrag
25.09.2026: Der Eintrag zu Fehler #4 im Protokoll nennt jetzt die erfolgte
Reparatur.)*

**3. Ein neuer Befund, der die Aussagen zum reparierten Korpus betrifft.**
Im Lauf `curated_mwefixed_live` (96 Contracts) wird jetzt sichtbar:

| Beobachtung | Contracts |
|---|---:|
| `Static analysis failed: Invalid args` | **35 von 96** |
| Exception in der Variablenbeschreibung (`tasks.py:245`) | 31 |
| weitere Static-Check-Abbrüche (`tasks.py:325`, `:232`) | 21 |
| LLM-Antwort nicht als JSON lesbar (`JSONDecodeError`) | 3 |
| gescheitertes Compilat | **1** (`58_UniV3Vault.sol`) |

Die 21 sind *verschiedene Contracts*: 19 mit `tasks.py:325`, 3 mit `:232`,
wobei `14_YieldSourcePrizePool.sol` beide trägt und daher nur einmal zählt.

Die Korpus-Reparatur selbst ist damit **bestätigt** — nur 1 von 96 Contracts
scheitert am Compilat, wie in `BA-KORPUS-REPARATUR.md` beschrieben. Neu ist
etwas anderes: GPTScans **Static-Bestätigungsstufe stürzt auf 35 von 96
übersetzbaren Contracts ab**. Das ist genau der Präzisionsfilter, um den es in
der Argumentation geht, und es war vor dem Parser-Fix unsichtbar. Ob und wie das
in die Arbeit einfließt, ist noch zu entscheiden.

*(Nachtrag 25.09.2026: Eingeordnet. Die Ausnahme trifft die Prüfung eines
einzelnen Kandidaten, nicht die Stufe; `GPTScan/src/tasks.py` setzt dessen
Ergebnis auf `False`, der Kandidat entfällt. Die Abbrüche kosten deshalb
Recall, nicht Precision, und jedes gemeldete Finding hat eine bestandene
statische Prüfung hinter sich. In `curated_mwefixed_live` sind es 80 Kandidaten
auf 35 Contracts; `BA-WERKZEUGE-IM-VERGLEICH.md` 4.3 und `BA-ARBEIT.md` 5.2.)*

**4. `GPTScan/reports/`** (≈340 KB HTML/PDF/CSV aus früheren Läufen) bleibt
unangetastet. Kandidat für weiteres Aufräumen, aber es sind eigene
Auswertungen — bei Bedarf entfernbar.

### Bekannte Einschränkungen, kein Handlungsbedarf

* **Der Hook-Inhalt wird mitgeklont, seine Aktivierung nicht.** *(Korrigiert
  am 21.09.2026 — die frühere Fassung sagte „Der pre-commit-Hook wird nicht
  mitgeklont. Hooks liegen in `.git/hooks/` und sind nie Teil eines
  Repositorys." Das trifft auf diesen Aufbau nicht zu.)* Das Hook-Skript liegt
  versioniert unter `.githooks/pre-commit`; `--install` setzt lediglich
  `core.hooksPath` darauf. Weil `core.hooksPath` eine lokale Einstellung ist,
  braucht ein frischer Clone weiterhin einmalig
  `python analysis_tools\secret_scan.py --install`. Im README beschrieben.
* **Keine Schlüssel-Rotation.** Die alte History wurde vollständig gesweept:
  es wurde nie ein echter Schlüssel committet. Nach Befundlage nicht nötig.
  *(Die frühere Angabe „über alle 13 Commits" bezog sich auf den Stand vom
  02.08.2026; der Sweep deckte die History, wie sie damals war.)*
* **Docstrings.** Vollständig. Der Eigenanteil ist durchgängig mit
  Modul-Docstrings und Docstrings für jede Funktion und Klasse versehen; die
  Begründung nicht offensichtlicher Entscheidungen steht als Inline-Kommentar
  an der jeweiligen Stelle. Nachgeprüft per AST-Auswertung über den gesamten in
  `BA-EIGENANTEIL.md` als Eigenanteil ausgewiesenen Umfang.
* **`slither` blieb unangetastet.** Fremder Upstream-Code; das Audit bestätigt,
  dass sein Parser keine Meldung verliert.
* **Die Audit-Detail-CSVs sind git-ignoriert** (mehrere MB, in ~25 s
  regenerierbar). Die Markdown-Berichte sind getrackt — sie sind das Lieferobjekt.

### Ausdrücklich nicht gemacht

* Keine neuen Live-LLM-Läufe. Es sind keine Kosten entstanden.
* Keine History umgeschrieben. Die fünf Commits sitzen auf `f85946e`.
* Keine Messdaten gelöscht. Die einzige Änderung an `smartbugs/results/` ist die
  Redaktion eines einzigen Feldes in 62 Dateien; `result.json` und
  `result.sarif` wurden durch `reparse` regeneriert, das Rohmaterial
  (`result.log`, `result.tar`) nie angefasst.
