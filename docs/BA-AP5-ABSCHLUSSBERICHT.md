# AP5 — Timeout ins Werkzeug durchreichen: Abschlussbericht

Gesamtdarstellung des Arbeitspakets AP5: was gebaut wurde, wie es funktioniert,
was belegt ist und was nicht, wie es entstand, und was offen bleibt.

Branch `ap5-timeout`, abgezweigt von `main` bei `f03fe98` · Stand: 2026-08-18

Zugehörige Dokumente: `BA-AP5-TIMEOUT-DESIGN.md` (Entwurf),
`BA-AP5-TIMEOUT-PLAN.md` (Arbeitsplan), `BA-AP5-VORPRUEFUNG.md` (Vorprüfung),
`BA-DURCHFUEHRUNGSPROTOKOLL.md` (Messläufe).

---

## 1. Das Problem

SmartBugs übergibt jedem Werkzeug-Entrypoint vier Argumente:
`FILENAME TIMEOUT BIN MAIN`. Beide Integrationen dieses Projekts nahmen `TIMEOUT`
entgegen und **benutzten es nicht**. Lief die Zeit ab, schoss SmartBugs den
gesamten Container von außen ab (`sb/docker.py:185`). Das Skript im Container kam
dabei nie wieder zum Zug: kein Ergebnis, keine Notiz, keine Metadaten. SmartBugs
sah nur „Container ist weg" und verbuchte `fails: DOCKER_TIMEOUT`.

Für ein Werkzeug wie LLMSmartAudit, das einen Contract in 41 aufeinanderfolgenden
Detektor-Phasen prüft, bedeutete das: die Arbeit von vierzig fertigen Detektoren
konnte restlos verloren gehen.

**Zwei Befunde vorweg**, die den Zuschnitt der Lösung bestimmt haben:

* Keines der beiden Werkzeuge kennt einen Timeout für den **Lauf**. GPTScan hat
  eine Frist je einzelnem LLM-Aufruf (`ask_with_timeout(..., timeout=90)`),
  LLMSmartAudit gar keine. Das Mythril-Muster (Timeout auf 80 % herunterrechnen
  und als `--execution-timeout` weiterreichen) war deshalb nicht übertragbar —
  es gibt kein Flag, an das man ihn hängen könnte.
* Der Mechanismus für Teilergebnisse existierte bereits, in Code, der dem Projekt
  selbst gehört. GPTScans Budget-Wächter (`analyze_pipeline.py:56`) hält im
  Kommentar wörtlich fest: *„Once tripped we stop issuing calls and return
  sentinels so the scan still finishes and writes partial results."* Und
  `chatdev/audit_report.py` ist eine der vier selbst hinzugefügten Dateien im
  LLMSmartAudit-Baum. Deshalb kostete die stärkere Lösung (Teilergebnis) keine
  zusätzliche Nachweislast gegenüber der schwächeren (sauberer Abbruch).

---

## 2. Wie es funktioniert

### 2.1 Drei Marken aus einem Timeout

Der Entrypoint rechnet aus `$TIMEOUT` drei Zeitpunkte:

| Marke | Anteil | Wirkung |
|---|---|---|
| **Bremse** | 70 % | keine neuen LLM-Aufrufe mehr; das Werkzeug läuft aus und schreibt seinen Report selbst |
| **Netz** | 90 % | `timeout` beendet das Werkzeug, falls die Bremse nicht griff |
| Aufräumen | 90–100 % | gehört dem Entrypoint: Teilstand bergen, `/output.json` schreiben |
| Docker-Kill | 100 % | `sb/docker.py`, unverändert, letzte Instanz |

Die Bremse reist als **absoluter Unix-Zeitstempel** `SB_DEADLINE_EPOCH` in den
Prozess — nicht als Restlaufzeit. Grund: GPTScan startet für jeden LLM-Aufruf
einen Worker per `multiprocessing`, und ein absoluter Zeitpunkt bedeutet in jedem
Kindprozess dasselbe.

**`TIMEOUT=0` schaltet alles ab.** Ohne Timeout verhält sich die Integration wie
vor AP5 — Voraussetzung dafür, dass die 19 bereits gefahrenen Messläufe
vergleichbar bleiben. Am echten Container geprüft, für beide Werkzeuge.

### 2.2 GPTScan — die Bremse

Ein zweiter Wächter in `ask_with_timeout()`, gebaut in der Form des vorhandenen
Budget-Wächters: Ist die Frist überschritten, wird der Grund einmalig vermerkt,
jeder weitere Aufruf gibt sofort einen Platzhalter zurück und zählt
`num_calls_skipped_deadline` hoch. Die Pipeline merkt nichts davon, läuft normal
bis zu ihrer Ausgabestufe durch und schreibt ihr Ergebnis **selbst** — samt der
Zusammenführung in `utils.convert_output`, die bei einem Kill verloren ginge.

Die Entscheidung „Frist abgelaufen?" liegt in `llm_backend.deadline_exceeded()`,
nicht in der Pipeline. Das ist kein Zufall: `llm_backend.py` importiert nur `os`,
`typing` und `config` und ist damit die einzige Stelle in GPTScan, die sich auf
dem Host ohne Container testen lässt.

### 2.3 LLMSmartAudit — der Zwischenstand

Hier ist ein harter Abbruch unschädlich, sobald der Stand auf Platte liegt.
`audit_report.record()` — aufgerufen nach jeder der 41 Phasen — schreibt den
aktuellen Stand **atomar** weg: erst in eine Temporärdatei, dann per
`os.replace()` an ihren Platz. Ohne diese Atomarität würde ein Kill mitten im
Schreiben den vorherigen guten Zwischenstand vernichten, weil das Öffnen mit `"w"`
die Datei vorher abschneidet.

Läuft die Frist ab, beendet das Netz den Prozess, und der Entrypoint befördert
den Zwischenstand zu `/output.json`. Verloren geht allein der Detektor, der gerade
lief.

**ChatDevs Ablaufsteuerung bleibt unberührt** — kein Signal-Handler, keine
Exception durch fremden Kontrollfluss. `chatdev/phase.py` und
`chatdev/chat_chain.py` sind auf dem gesamten Branch nicht angefasst.

### 2.4 Warum zwei verschiedene Lösungen

Nicht aus Bequemlichkeit, sondern weil die Werkzeuge verschieden gebaut sind:
GPTScan aggregiert, dedupliziert und schreibt **am Ende**, muss also freiwillig
auslaufen dürfen. LLMSmartAudit hält nach jeder Phase einen vollständigen
Zwischenstand, dort genügt Festhalten und Abbrechen.

Verallgemeinert: *Ob sich ein Teilergebnis retten lässt, hängt daran, ob ein
Werkzeug inkrementell festhält oder erst am Schluss zusammenführt.*

**Das sind zwei verschiedene Zusagen, und die Dokumentation darf sie nicht
vermengen.** Der wertschöpfende Pfad bei GPTScan ist die Bremse; ein Netz-Timeout
rettet dort **kein** Teilergebnis, sondern erzeugt einen Platzhalter-Report. Das
Bergen von Teilergebnissen ist LLMSmartAudits Mechanismus.

### 2.5 Kennzeichnung — und warum sie die Messung berührt

Beide Wege tragen denselben Marker im Ergebnis:

```json
"sb_timeout": {"hit": true, "stage": "brake" | "net", "detail": "Freitext"}
```

Fehlt er, war der Lauf vollständig — Abwesenheit ist die Aussage „kein Timeout".

| Lage | Exit | SmartBugs sieht |
|---|---|---|
| Bremse griff, sauber ausgelaufen | 0 + Marker | **error** — bemerkt und abgefangen |
| Netz griff, Teilstand geborgen | 124 | **error** `EXIT_CODE_124` + `TIMEOUT_NET` |
| Container von außen abgeschossen | `None` | **fail** `DOCKER_TIMEOUT` |

Die 124 wird **erzwungen**, nicht durchgereicht: `timeout` meldet je nach
Herkunft 124, 143 oder (bei zu SIGKILL eskaliertem SIGTERM) 137. Die letzten
beiden stehen namentlich in `DOCKER_CODES` (`sb/parse_utils.py:8-15`) und würden
als `DOCKER_TERM` bzw. `DOCKER_KILL_OOM` nach **`fails`** gebucht — also als
„Werkzeug ausgehebelt", obwohl der Abbruch beabsichtigt war. Nur die 124 fällt
durch alle Sonderfälle in den `else`-Zweig und landet in `errors`.

**Diese Unterscheidung ist der eigentliche Gewinn des Arbeitspakets.**

Damit ein Teillauf die Messung nicht still verzerrt, führen
`analysis_tools/gptscan_eval.py` und `errors_fails_report.py` nun die Spalten
`timeout_hit` und `timeout_stage` und weisen Teilläufe in der Zusammenfassung
getrennt aus — als eigene Zeile, nicht als stille Beimischung.

---

## 3. Was belegt ist

### 3.1 Tests

**110 grüne Tests** (`python -m pytest tests/ -q`), Ausgangsstand vor AP5: 78.
Die 32 neuen decken ab: die Deadline-Entscheidung samt ihrem neutralen
Platzhalter, den Zwischenstand-Flush samt Atomarität, beide Parser-Zweige, die
Marken-Arithmetik beider Entrypoints inklusive ihrer Gleichheit, und den
Prüfstand-Endpunkt.

### 3.2 Echte Container-Läufe

Alle Läufe in eigenen Ergebnisbäumen; die 19 Altmessungen unberührt.

**Gegen einen lokalen Prüfstand (kostenlos, wiederholbar):**

| Fall | Ergebnis |
|---|---|
| GPTScan, Bremse | Exit 0, `stage=brake`, 21 Aufrufe gemacht, 7 unterdrückt, Report selbst geschrieben, 38 s vor dem Netz |
| GPTScan, Netz | Exit 124, `stage=net`, Normalisierung greift |
| LLMSmartAudit, Netz | Exit 124, `stage=net`, Zwischenstand geborgen, **24 von 41** Kategorien |
| beide, `TIMEOUT=0` | keine Marke, kein Marker, kein Zwischenstand geschrieben |
| **`fails` in allen Läufen** | **leer** |

Eine ungeplante Negativkontrolle: `71_IndexTemplate.sol` lief in 211,8 s durch —
1,8 s **nach** der Bremse — und trägt korrekt keinen Marker. Damit ist auch die
Umkehrung belegt: Markerfreiheit heißt „Lauf war vollständig".

**Gegen den echten DeepSeek-Endpunkt (Kosten rund $0,04):**

| | Volllauf | Teillauf |
|---|---|---|
| LLMSmartAudit `5_Vether.sol` | 719,9 s, 41/41, 9 Findings | 376,5 s, Exit 124, **23/41**, 5 Findings |
| GPTScan `5_Router.sol` | 172,2 s, 39 Aufrufe, 2 Findings, $0,0067 | 99,9 s, Exit 0, `brake`, 24 Aufrufe, 26 unterdrückt, 0 Findings |

### 3.3 Der Teilmengen-Nachweis

Die zentrale Frage lautete: **Erfindet ein Teilergebnis Findings?** Sie wurde in
zwei Tests zerlegt, weil nur einer den Mechanismus prüft:

* **Kein Finding aus einem Detektor, der nie lief** — ausnahmslos bestanden. Das
  ist die eigentliche Zusage.
* **Teillauf ⊆ Volllauf** — bestanden. Die 5 Findings des Teillaufs (Positionen
  #5, #13, #14, #19, #21) sind sämtlich im Volllauf enthalten; die Liste der
  geprüften Kategorien ist ein echtes Präfix der Detektor-Kette.

**Die Gegenrichtung gilt nicht, und das gehört gesagt:** Ein Detektor
(`RedundantConditional`, #22) lag im abgedeckten Bereich, feuerte im Volllauf,
im Teillauf aber nicht. Ein Teillauf kann ein Finding also **verpassen**. Das ist
der bekannte Nicht-Determinismus der Werkzeuge, nicht ein Fehler des Mechanismus.
Die Zusage lautet **„erfindet nichts"**, nicht „identisch".

### 3.4 Der Preis des Zwischenstands

Direkt vermessen (41 `record()`-Aufrufe, 20 Wiederholungen, Median):
**0,07 ms ohne** gegen **56,40 ms mit** Snapshot. Das sind **56,3 ms je Contract
= 0,019 %** der mittleren Bearbeitungszeit. Bei den 19 Altmessungen entstehen
**null** zusätzliche Schreibvorgänge, weil der Entrypoint `SB_PARTIAL_REPORT` nur
bei `TIMEOUT > 0` setzt.

### 3.5 Eigenanteil

**Keine einzige neue Fremddatei.** Die Zahlen in `BA-EIGENANTEIL.md` bleiben
unverändert gültig:

| Fremdcodebasis | dort gelistet | von AP5 geändert | neu |
|---|---|---|---|
| GPTScan | 7 | 5 | **0** |
| LLMSmartAudit | 9 | 1 (`audit_report.py`, eigener Code) | **0** |
| SmartBugs `sb/` | 5 | 0 | **0** |

Alles Übrige sind eigene Dateien: die beiden Werkzeugverzeichnisse unter
`smartbugs/tools/`, die Tests, `testing_tools/` und die Dokumentation.

---

## 4. Was nicht belegt ist

Ehrlichkeit über die Grenzen gehört zum Ergebnis:

* **Der Nachweis stützt sich auf je einen Contract.** Er zeigt „erfindet nichts",
  nicht „verpasst wenig". Eine statistische Aussage über die Güte von
  Teilergebnissen ist damit nicht getroffen.
* **LLMSmartAudits Kosten sind geschätzt, nicht gemessen** — das Werkzeug führt
  keine Token-Buchhaltung. Eine belastbare Zahl käme nur aus dem
  DeepSeek-Dashboard.
* **Ein Netz-Timeout bei GPTScan rettet kein Teilergebnis.** Der Teillauf verlor
  dort sogar beide echten Findings: ohne die zugehörigen LLM-Antworten kann die
  statische Bestätigungsstufe nichts mehr bestätigen. Die Bremse kostet dort
  also nicht nur Vollständigkeit, sie kann das Ergebnis auf null reduzieren.
* **Der Prüfstand kann die Echtheit von Findings prinzipiell nicht belegen**, weil
  er auf jede Anfrage denselben Text antwortet. Dafür war der scharfe Lauf nötig.

### Ein Befund mit Code-Bezug — nachträglich behoben

Im Messlauf gab der Deadline-Pfad noch `dry_sentinel` zurück, also **bejahende**
Platzhalter, und hob damit die Kandidatenliste von 6 auf 13. **Kein erfundenes
Finding kam durch** — aber nur, weil zwei Sicherungen dahinter greifen: die
statische Bestätigung verwarf alle 13, und für Static-Prompts liefert derselbe
Sentinel `"{}"`, also keine bestätigende Nebenbedingung. Der Schutz war damit ein
**Nebeneffekt der Implementierung, keine ausgesprochene Zusage**.

Das ist behoben. Der Deadline-Zweig gibt jetzt `llm_backend.deadline_sentinel`
zurück, der ausnahmslos `"{}"` liefert: leere Mehrfachauswahl, Ja/Nein zählt als
Nein, Static-Prompts unverändert. Der Budget-Zweig behält `dry_sentinel` — er ist
ein Kostenstopp, kein Zeitablauf, und seine Oberschranken-Antwort ist dort
gewollt. Zwei Tests halten das fest; beide fallen gegen die Fassung davor.

Kein neuer scharfer Lauf war dafür nötig: ein neutraler Platzhalter kann die
Kandidatenliste nur verkleinern, der Teilmengen-Nachweis gilt danach erst recht,
und der gemessene Teillauf lieferte ohnehin 0 Findings. Die Zahl 6→13 in
`BA-DURCHFUEHRUNGSPROTOKOLL.md` ist damit ein historischer Messwert.

---

## 5. Korrekturen an Projektangaben

Die Umsetzung hat drei Angaben berichtigt, die anderswo im Repository stehen:

1. **Die „rund 76 s je Contract" sind falsch verstanden worden.** Der Wert ist
   Wall-Clock geteilt durch 143 bei `--processes 4` (10 935 s / 143), also
   Durchsatz, keine Bearbeitungszeit. Aus den 143 `smartbugs.json` des
   Referenzlaufs ergibt sich: **Mittel 299,2 s, Median 264,1 s, Spanne
   150,8–923,2 s**. Der Volllauf dieses Arbeitspakets (719,9 s) liegt darin —
   gegen 76 s gehalten hätte er wie eine neunfache Regression ausgesehen.
2. **Die dokumentierte Image-Reduktion stimmt.** Der Neubau des
   LLMSmartAudit-Images landet bei **586 MB** gegenüber den in
   `BA-EIGENANTEIL.md` genannten 590 MB. Das lokal vorliegende 5,13-GB-Image war
   ein Stand vor dieser Arbeit.
3. **`BA-EIGENANTEIL.md:47` („je vier Dateien nach dem SmartBugs-Schema") ist
   überholt.** Der gptscan-Skriptordner hatte schon vor AP5 fünf Dateien und hat
   jetzt sechs. Die Randbedingung bleibt eingehalten, weil derselbe Abschnitt den
   Ordner als vollständig selbst geschrieben führt.

---

## 6. Material für AP7 (Meta-Findings)

Fünf belegte Punkte, alle in dieser Umsetzung entstanden:

1. **Kein Werkzeug bringt einen Timeout für den Lauf mit.** GPTScan kennt eine
   Frist je LLM-Aufruf, LLMSmartAudit gar keine.
2. **Ob ein Teilergebnis rettbar ist, hängt an der Ablageform** — inkrementell
   gegen Endaggregation. Dieselbe Anforderung erzwang zwei verschiedene Lösungen.
3. **Die Host/Container-Grenze verläuft entlang des LLM-SDK-Stacks.** Alles, was
   `openai` oder `tiktoken` anfasst, ist nur im Container ladbar; Konfiguration,
   Parser und Auswertung laufen auf dem Host. Das begrenzt, was sich ohne
   Container prüfen lässt, und hat hier zweimal die Testform bestimmt.
4. **`errors` gegen `fails` lässt sich am Timeout anschaulich zeigen.** In
   `tests/test_llmsmartaudit_parser.py` stehen nun zwei Fälle nebeneinander:
   `exit_code=None` (von außen abgeschossen, nichts geborgen) → `fails`;
   `exit_code=124` mit geborgenem Zwischenstand → `errors`.
5. **Kein Offline-Modus in den Werkzeugen — jetzt behoben.** Bisher kostete jeder
   Test, der einen Timeout auslösen sollte, echtes Geld. Der lokale
   Ersatz-Endpunkt (`testing_tools/fake_llm_endpoint.py`) schließt das und nützt
   auch AP4 (Nachbaubarkeit ohne API-Schlüssel).

---

## 7. Wie es entstanden ist

14 Aufgaben, jede einzeln umgesetzt, gegen den Plan durchgesehen und abgenommen;
an vier Stellen war eine Nachbesserungsrunde nötig. Bei den Durchsichten kamen
**ein schwerwiegender und vier gewichtige Mängel** zutage; keiner davon im
Produktivcode.

**Alle fünf betrafen Tests oder Dokumentation, die schwächer waren als die
Behauptung, die sie stützen sollten** — und alle fünf standen so bereits im
Arbeitsplan, entstanden also nicht erst bei der Umsetzung:

| Fund | Was daran falsch war |
|---|---|
| Aufgabe 2 | Ein Test importierte ein Modul, das auf dem Host nicht ladbar ist |
| Aufgabe 5 | Der Test des häufigeren Falls lief per `or`-Kurzschluss am geprüften Zweig vorbei |
| Aufgabe 7 (a) | Der Fehlertest konnte gar nicht fehlschlagen — er war schon vor der Implementierung grün |
| Aufgabe 7 (b) | Der Zwischenstand wurde nicht atomar geschrieben; ein Kill im Schreibfenster hätte den letzten guten Stand vernichtet |
| Aufgabe 12 | Die Dokumentation behauptete einen Test, den es nicht gibt |

Bemerkenswert an der Verteilung: Der Produktivcode war durchgehend in Ordnung.
Was fehlte, war die Strenge der Belege. An zwei Stellen haben wir deshalb
zusätzlich mit Mutationstests nachgesetzt — die eigenen Tests gegen absichtlich
kaputte Fassungen des Codes laufen lassen, um zu zeigen, dass sie dort auch
wirklich fehlschlagen.

**Eine Lücke fiel bei keiner Aufgabe auf:** `GPTSCAN_BASE_URL` und
`GPTSCAN_API_KEY` fehlten in der `env:`-Zeile der `config.yaml`, wodurch der frei
wählbare Endpunkt aus einem SmartBugs-Lauf unerreichbar gewesen wäre. Sie lag
außerhalb dessen, was Auftrag und Diff abdecken — neue Konfiguration, die sich
auf Verrohrung an anderer Stelle verlässt. Das ist die systematische Blindstelle
einer Durchsicht, die sich an den geänderten Zeilen orientiert.

---

## 8. Offene Punkte

| Punkt | Wem gehört die Entscheidung |
|---|---|
| `ap5-timeout` nach `main` mergen und pushen? | Projektinhaber |
| DeepSeek-Schlüssel tauschen (war zwischenzeitlich im Klartext außerhalb der Schlüsseldatei sichtbar) | Projektinhaber |
| Belastbare Kostenzahl für LLMSmartAudit aus dem DeepSeek-Dashboard | optional |

Erledigt, seit die Abschluss-Durchsicht sie aufgeworfen hat: der eigene neutrale
Platzhalter für den Deadline-Pfad (Abschnitt 4), das fehlende
`assert fails == set()` im LLMSmartAudit-Timeout-Test, und der Commit der drei
AP5-Dokumente — ohne ihn zeigten nach einem Merge sieben Verweise ins Leere,
darunter einer in `BA-BETREUERGESPRAECH-AUFGABEN.md`.

---

## 9. Ergebnis der Abschluss-Durchsicht

Zum Schluss haben wir den Branch als Ganzes durchgesehen, nicht mehr Aufgabe für
Aufgabe. **Urteil zu diesem Zeitpunkt: noch nicht merge-reif** — ein
schwerwiegender Punkt, sechs gewichtige, sieben neue geringfügige. Der
Mechanismus selbst war solide; sämtliche Mängel lagen an den Nähten und in der
Dokumentation.

**Als tragfähig bestätigt**, jeweils am Quelltext nachgeprüft statt aus den
Aufgabenberichten übernommen:

* der Deadline-Wächter als exakter Zwilling des Budget-Wächters, an derselben
  Messstelle,
* der absolute Zeitstempel als richtige Wahl für die Prozessgrenze,
* die Fehlerrichtung: ein unlesbarer Wert schaltet den Wächter ab, statt ihn
  auszulösen,
* das `custom`-Gate, das keinen bezahlten Anbieter umleiten kann,
* der atomare Flush samt einer Testfassung, die die Invariante wirklich belegt,
* die Exit-Code-Normalisierung, geprüft gegen die echte `DOCKER_CODES`-Tabelle,
* die automatische Redaktion des neuen Schlüsselnamens durch `sb/docker.py`,
* die Randbedingung 7 / 9 / 5.

**Behoben mit Commit `a34f3067`:**

| Punkt | Was falsch war |
|---|---|
| I1 | Zwei Dokumente behaupteten, LLMSmartAudit prüfe die Bremse zwischen den Phasen. Es liest `SB_DEADLINE_EPOCH` nicht. |
| I2 | Dieselbe Falschaussage an ihrer Quelle — im wörtlich gespiegelten Kommentar des LLMSmartAudit-Entrypoints. |
| I3 | `run_full_v2.ps1` stempelte `timeout_enforced_by = 'docker only (AP5 offen…)'` in die `run_meta.json` **jedes künftigen** Laufs: eine maschinenlesbare Falschaussage in der Provenienz, auf die AP4 sich stützt. |
| I4 | `gptscan_eval.py` schrieb in dasselbe erzeugte `summary.md` sowohl „AP5 offen" als auch die neue Teillauf-Zeile. |
| I5 | Drei Dokumente führten den scharfen Lauf noch als ausstehend, obwohl er geliefert war. |
| I6 | Fehlendes `assert fails == set()` im LLMSmartAudit-Timeout-Test — ausgerechnet bei der Kernaussage „`errors` statt `fails`". |
| M1/M2 | Fehlendes `str()` um `stage` im LLMSmartAudit-Parser (ein Nicht-String hätte über `sb/parsing.py` einen Task verloren) und „None of None" bei fehlenden Deckungsfeldern. |
| M3 | „Byte für Byte" → „verhaltensgleich": `tasks.py` schreibt zwei Metadatenschlüssel bedingungslos. |
| M4 | Der wirkungslose `SB_DEADLINE_EPOCH`-Export im LLMSmartAudit-Entrypoint ist jetzt als absichtlich wirkungslos kommentiert. |
| M6 | Limitation ergänzt: `evaluate_curated.py` kennt den Timeout-Marker nicht. |

Bemerkenswert an **I2**: Eine frühere Durchsicht hatte diese Korrektur mit der
Begründung abgelehnt, sie breche „den Gleichheitstest aus Aufgabe 10". Diesen
Test gibt es nicht — der Vergleichstest prüft geparste Zahlen, keinen Text. Eine
erfundene Begründung hat den Fehler durch zwei Dokumente getragen.

**Danach erledigt:** der neutrale Platzhalter für den Deadline-Pfad
(Abschnitt 4) und der Commit der drei AP5-Dokumente.

**Zwölf geringfügige Punkte bleiben bewusst liegen**, jeder einzeln begründet.

### Drei Beobachtungen zum Vorgehen

1. **Der Diff ist die falsche Grenze für eine Durchsicht.** Zwei Befunde
   betrafen Aussagen, die durch den Branch *falsch geworden* sind, ohne dass sie
   jemand angefasst hätte — einer außerhalb jeder geänderten Datei, einer
   innerhalb einer geänderten Datei außerhalb der geänderten Zeilen.
2. **Dokumentation vor Nachweis erzeugt I5 strukturell.** Liegt die
   Dokumentationsaufgabe vor dem Messlauf, muss der Messlauf einen eigenen Punkt
   tragen: „Aussagen der Dokumentation gegen das Ergebnis prüfen".
3. **Wird eine Korrektur mit „bricht Test X" abgelehnt, ist Test X zu öffnen.**
   Bei I2 hat das niemand getan, und der Fehler stand danach in zwei weiteren
   Dokumenten.
