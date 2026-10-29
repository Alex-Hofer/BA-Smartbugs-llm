# Aufgaben aus dem Betreuergespräch

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Grundlage sind unsere Mitschriften aus dem Gespräch mit unserem Betreuer
**Gernot Salzer** (GitHub `Gsalzer`). Die Arbeitspakete haben wir aus den
Stichworten der Mitschrift rekonstruiert; hier steht, *was* zu tun war und was
daraus geworden ist.

---

## 1. Überblick

| # | Arbeitspaket | Art | Aufwand | Stand |
|---|---|---|---|---|
| AP1 | Terminologie: `error` → `Finding` | Doku | S | **erledigt** |
| AP2 | Integrationstreue: Originalwerkzeug gegen SmartBugs | Experiment | L | offen |
| AP3 | Betreuer ins Repository einladen | Organisation | XS | **erledigt** |
| AP4 | Reproduzierbarkeit (a) der Messung, (b) des Aufbaus | Experiment + Doku | L | offen |
| AP5 | Timeout ins Werkzeug durchreichen | Code | M | **erledigt** |
| AP6 | `MAIN`-Parameter umsetzen | Code | M | **erledigt** |
| AP7 | Meta-Findings-Dokument (LLM-Werkzeuge allgemein) | Doku | M | offen, Material liegt vor |
| AP8 | Aufwandsschätzung an den Betreuer mailen | Organisation | XS | offen |
| — | Nachtrag 10.10.2026: beide Werkzeuge in SmartBugs selbst integrieren | Code | M | **erledigt**, [#222](https://github.com/smartbugs/smartbugs/pull/222) am 14.10.2026 übernommen |

XS = unter 1 h · S = 1–4 h · M = 4–12 h · L = 12–30 h

---

## 2. Offene Rückfragen

1. **„Monar“** — steht in der Mitschrift als Werkzeugname vor „Tool im
   Originalzustand außerhalb von Docker vergleichen“. Keine der 46
   Werkzeugkonfigurationen in `smartbugs/tools/` heißt so (am nächsten: `mando`,
   `maian`, `manticore`). Entweder ein Werkzeug außerhalb von SmartBugs oder
   ein verhörtes „nochmal“. Blockiert nichts.
2. **AP2, Umfang** — reicht ein Beleg an wenigen Contracts, oder soll es ein
   ganzer Korpus sein? Letzteres verdoppelt die LLM-Kosten.
3. **AP5, Verhalten bei Timeout — geklärt: Teilergebnis.** Beim Ablaufen
   liefert das Werkzeug, was bis dahin vorliegt, gekennzeichnet mit
   `sb_timeout`. Diese Variante schließt die schwächere (sauberer Abbruch mit
   Kennzeichnung) ein und liegt komplett in unserem eigenen Code.

---

## 3. Arbeitspakete

### AP1 — Terminologie

**Betreuer:** „Statt error → weakness oder findings.“ — „Tools suchen NICHT
errors sondern Verdachtsfälle […] Finding ist ein besserer Name.“

Ein Scanner stellt keine Fehler fest, er äußert einen *Verdacht*. SmartBugs
trennt das bereits sauber: `findings` (was das Werkzeug meldet), `errors`
(Problem bemerkt und abgefangen), `fails` (Werkzeug ausgehebelt). Die Feldnamen
selbst bleiben, sonst wäre die Ausgabe nicht mehr SmartBugs-kompatibel; ändern
konnten wir nur unsere Prosa und unseren Code.

**Erledigt.** Regel: Werkzeug → *Finding*, Ground Truth → *Schwachstelle*,
Ausführung → *Fehler* (Abschnitt „Begriffe“ in
[`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md)). Korrigiert haben wir drei
Stellen mit „DeFi-Logikfehler“ und den `info`-Text in
`smartbugs/tools/gptscan/config.yaml`. Die übrigen rund 78 „Fehler“ und 15
„Schwachstelle“ waren richtig verwendet; im Code war nichts zu ändern.

### AP2 — Integrationstreue

**Betreuer:** „SmartBugs-Integration von den Tools mit den Original-Tools […]
ob alles richtig ist.“ — „Tool im Originalzustand außerhalb von Docker
vergleichen mit SmartBugs. Zu testen ob es transparent ist.“

Zu zeigen wäre, dass unsere Integration das Werkzeug **nicht verändert** — sonst
bleibt bei jeder Zahl die Frage, ob sie das Werkzeug misst oder unseren Wrapper.
Plan: beide Werkzeuge nativ nach Upstream-Anleitung aufsetzen, dieselben
Contracts durch beide Wege schicken, Findings, Zuordnung, Laufzeit und Kosten
vergleichen. Schwierig ist die Einordnung: Beide Werkzeuge sind nicht
deterministisch, eine einzelne Abweichung beweist nichts. Zu prüfen wären die
7 geänderten Dateien in GPTScan, 9 in LLMSmartAudit und 2 in `smartbugs/sb/`
([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)). **Offen.**

### AP3 — Betreuer einladen

**Betreuer:** „SmartBugs Gsalzer ins GitHub inviten.“

**Erledigt.** `gsalzer` ist Collaborator (geprüft 16.09.2026); vorher lief der
Secret-Scan über das ganze Repository ohne Fund.

### AP4 — Reproduzierbarkeit

**Betreuer:** „Reproduzierbarkeit machen/testen.“ — „Laufzeit zum Finden.“

* **(b) Nachbaubarkeit, Vorrang:** Kann ein Dritter klonen und die Ergebnisse
  herstellen? Die Anleitung steht in [`BA-BETRIEB.md`](BA-BETRIEB.md) und
  [`BA-WERKZEUG-BEDIENUNG.md`](BA-WERKZEUG-BEDIENUNG.md); ehrlicherweise kosten
  LLM-Läufe Geld und brauchen einen Schlüssel. Der Beweis auf einer fremden
  Maschine fehlt. Die Kennzahlen lassen sich aber ohne Docker und Schlüssel aus
  den versionierten Dateien nachrechnen (`metrics_from_eval.py`, CI).
* **(a) Wiederholbarkeit:** Teilantworten liegen vor — GPTScan 74 % identische
  Finding-Sätze, LLMSmartAudit 61,4 % Jaccard, Slither bis auf einen Detektor
  identisch ([`BA-WERKZEUGE-IM-VERGLEICH.md`](BA-WERKZEUGE-IM-VERGLEICH.md),
  4.4). Eine systematische Messung über mehr als zwei Läufe fehlt.
* **Laufzeit** weisen wir je Lauf aus (curated: Slither 1:24 min, GPTScan
  3:19 min, LLMSmartAudit 3:02 h).

**Offen** in beiden Teilen.

### AP5 — Timeout ins Werkzeug durchreichen

**Betreuer:** „Timeout vlt einbauen und integrieren (bei Docker geht es?).“ —
„Docker ist hier die Notlösung wenn es im Tool nicht vorhanden ist.“

**Ausgangslage:** SmartBugs übergibt jedem Entrypoint `FILENAME TIMEOUT BIN
MAIN`; unsere Entrypoints nahmen `TIMEOUT` entgegen und nutzten es nicht. Es
griff nur der äußere Docker-Abbruch, ohne Teilergebnis. Vorbild im Upstream:
`tools/mythril-0.23.15/scripts/do_solidity.sh` reicht 80 % des Timeouts als
`--execution-timeout` weiter.

**Erledigt.** Keines der Werkzeuge kennt einen eigenen Lauf-Timeout (GPTScan
nur je LLM-Aufruf, LLMSmartAudit gar keinen). Der Entrypoint rechnet deshalb
drei Marken (70 % Bremse, 90 % Netz, Rest zum Bergen): GPTScan stellt an der
Bremse neue LLM-Aufrufe ein und läuft aus, LLMSmartAudit schreibt nach jeder
Detektorphase einen Zwischenstand, den der Entrypoint nach dem Netz birgt.
Beide setzen `sb_timeout` und melden Exit 124. `--timeout 0` ändert nichts am
alten Verhalten. Belegt durch 32 Tests, die Vorprüfung
([`BA-AP5-VORPRUEFUNG.md`](BA-AP5-VORPRUEFUNG.md)) und scharfe Läufe
([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), 4.5);
Details in [`BA-AP5-ABSCHLUSSBERICHT.md`](BA-AP5-ABSCHLUSSBERICHT.md).

Bewusst nicht umgesetzt: ein Timeout-Flag in den Werkzeugen selbst, ein
vorzeitiger Kettenabbruch in LLMSmartAudit, Wiederaufnahme abgebrochener Läufe
und jede Änderung am äußeren Docker-Timeout (bleibt letzte Instanz).

### AP6 — `MAIN`-Parameter

**Betreuer:** „Parameter um auszuwählen welche Art von Contract analysiert
werden. Damit nicht alles analysiert wird. Es heißt meist main.“

Bei `MAIN=1` soll ein Werkzeug nur den Contract analysieren, der wie die Datei
heißt — nicht jede mitimportierte Bibliothek. Unsere Entrypoints ignorierten den
Wert. Das betrifft die Messung selbst: Findings in Bibliotheken zählen sonst mit.

**Erledigt** (15.08.2026). Keines der Werkzeuge bietet eine Contract-Auswahl,
also reduzieren wir die Eingabe: `scripts/main_contract.py` kürzt die Datei auf
den Hauptcontract und was er braucht; bei GPTScan wird die volle Quelle
wiederhergestellt, wenn die reduzierte nicht mehr kompiliert; passt kein
Contract zum Dateinamen, Exit 127. Abgesichert durch `tests/test_main_contract.py`
und `tests/test_entrypoint_main.py`; angewendet in `gptscan_mwefixed_v2_main`
(41 von 96 reduziert).

### AP7 — Meta-Findings

**Betreuer:** „Aus Erkenntnissen sollten Empfehlungen, Standards ausgegeben
werden.“ — „Dokument aus METAFINDINGS (LLM-Tools allgemein).“

Gemeint ist nicht, was die Werkzeuge über Contracts sagen, sondern was **wir
über die Werkzeuge** gelernt haben — als Anforderungen an LLM-Analysewerkzeuge.
Das Material liegt vor, das Dokument haben wir nicht mehr geschrieben:

| Erkenntnis | Beleg |
|---|---|
| kein Lauf-Timeout, keine Kostenbremse | LLMSmartAudit; GPTScan nur Frist je Aufruf (AP5) |
| keine Contract-Auswahl | AP6 |
| kein Offline-/Stub-Modus, jeder Test kostet Geld | `LLM_MODEL=STUB` geht wörtlich an die API |
| Nichtdeterminismus trotz `temperature=0` | 74 % bzw. 61,4 % Übereinstimmung |
| stilles Scheitern statt Fehlermeldung | GPTScan: Compile-Fehler, Exit 0, `results: []` |
| Severity ist Katalogwert, kein Einzelurteil | konstant je Detektor über 1 124 Findings |
| keine Zeilennummern | LLMSmartAudit: SARIF ohne `region` |
| Modell fest im Image, Werkzeug veraltet still | `deepseek-chat` abgeschaltet, HTTP 400 |
| Kontextgrenze als Konstante im Code | 37 von 96 DeFi-Contracts nicht analysiert |
| keine Kosten und Laufzeit im Ergebnis | extern erhoben (`GPTSCAN_META`) |
| Ob ein Teilergebnis zu retten ist, hängt an der Architektur | GPTScan muss auslaufen, LLMSmartAudit sichert je Phase (AP5) |

### AP8 — Aufwandsschätzung

**Betreuer:** „Zeitaufwand berechnen und bei Mail senden.“ Schätzung in
Abschnitt 4; noch nicht verschickt.

---

## 4. Aufwandsschätzung

> Die Zählungen sind gemessen, die Stunden **geschätzt** — mitgestoppt hat
> niemand. Belastbar als Größenordnung, nicht als Abrechnung.

### 4.1 Was messbar vorliegt (Stand 25.09.2026)

| Größe | Wert |
|---|---|
| eigener Code | **15 907 Zeilen** (Python, PowerShell, Shell, YAML, Dockerfile), davon 4 351 Tests |
| eigene Dokumentation | **rund 78 000 Wörter** in 32 handgeschriebenen Dokumenten (vor der Straffung im Oktober 2026) |
| geänderte Fremddateien | **18** (7 GPTScan, 9 LLMSmartAudit, 2 SmartBugs) plus `smartbugs/.gitignore` |
| Werkzeug-Integrationen | **2** vollständig, dazu das glibc-Slither-Verzeichnis |
| Docker-Images | **3** selbst gebaut, eines von 5,13 GB auf 587 MB verkleinert |
| Messläufe | **51 Läufe, 1 501 Tasks, 7 494 Dateien, 2,68 GB** |
| Korpus | **96 Contracts**, von 1/96 auf 96/96 kompilierbar |
| Parser-Reparatur | **1 368 → 0** verlorene Rohmeldungen |
| Regressionstests | **276** |
| Zeitraum | 01.07. bis 24.09.2026 (erster und letzter Task-Start), dazu eine Vorphase vor dem ersten Commit |

Gezählt mit `wc -l` bzw. `wc -w` über die per `git ls-files` erfassten eigenen
Dateien ([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md), 1); generierte Berichte
zählen nicht. Die Vorphase (Läufe `assign6_*`, `phase6_*`, `GPTScan/reports/`)
ist älter als die Git-Historie; die Integration lief am Tag des ersten Commits
bereits.

### 4.2 Schätzung nach Arbeitspaketen

| Arbeitspaket | Stunden |
|---|---|
| Einarbeitung: SmartBugs, Docker, solc, Quellcode beider Werkzeuge | 25–35 |
| Integration GPTScan (u. a. Keyword-Falle, Metadaten-Kanal) | 30–40 |
| Integration LLMSmartAudit (Image-Verkleinerung, Report-Sammler, 41 Detektoren) | 30–40 |
| Eingriffe in `smartbugs/sb/` | 8–12 |
| Messläufe, Smoke- und Trockenläufe, Kosten-Forensik | 35–45 |
| Auswertung: Kennzahlen, DASP-Mapping, Stichproben am Code | 30–40 |
| Korpus-Rekonstruktion | 40–55 |
| Parser-Audit und -Reparatur | 30–40 |
| Tests, Verifikation, errors/fails-Report | 25–35 |
| Sicherheit und Repo-Hygiene (Secret-Scan, Schwärzung, Neugründung, Lizenzen) | 15–20 |
| Dokumentation und Eigenanteil-Nachweis | 45–60 |
| Abstimmung und Organisation | 8–12 |
| **Summe** | **320–435** (Mittel rund 375) |

Die Schätzung kennt nur, was im Repository Spuren hinterlassen hat — keine
Literatur, keine Sackgassen, keine Lehrveranstaltung, aus der die
`assign6`-Läufe stammen. Vor dem Versand gleichen wir sie mit unserer
Erinnerung ab.
