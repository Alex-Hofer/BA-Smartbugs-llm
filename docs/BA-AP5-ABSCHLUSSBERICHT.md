# AP5 — Timeout ins Werkzeug durchreichen: Abschlussbericht

> Datierte Momentaufnahme · aktueller Stand im Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Alles zum Arbeitspaket AP5: was wir gebaut haben, wie es funktioniert, was
belegt ist und was nicht, und was offen bleibt. Stand 18.08.2026 (Branch
`ap5-timeout`, inzwischen in `main` aufgegangen).

> **Nachtrag 25.09.2026.** AP5 ist seit dem 18.08.2026 im Einsatz
> ([`BA-BETRIEB.md`](BA-BETRIEB.md) 8). Die Zahl „SmartBugs `sb/` 5“ in
> Abschnitt 3.5 zählt gegen den Tag `v2.1.1`; gegen den tatsächlich geklonten
> Stand `7ddaf6c` sind es 2 Dateien ([`BA-EIGENANTEIL.md`](BA-EIGENANTEIL.md)
> 2.1). Seit dem 24.09.2026 protokollieren die Runner die tatsächliche
> Abbuchung je Lauf.

Dazu gehören [`BA-AP5-TIMEOUT-DESIGN.md`](BA-AP5-TIMEOUT-DESIGN.md) (Entwurf),
[`BA-AP5-VORPRUEFUNG.md`](BA-AP5-VORPRUEFUNG.md) (Vorprüfung) und
[`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md) 4.5
(Messläufe).

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

**AP5 hat die Suite von 78 auf 110 Tests gebracht**, alle grün
(`python -m pytest tests/ -q`). Die 32 neuen decken ab: die
Deadline-Entscheidung samt ihrem neutralen Platzhalter, den Zwischenstand-Flush
samt Atomarität, beide Parser-Zweige, die Marken-Arithmetik beider Entrypoints
inklusive ihrer Gleichheit, und den Prüfstand-Endpunkt.

Nach der Zusammenführung mit dem parallel auf `main` entstandenen Stand (Prüfung
des Kontextfensters im LLMSmartAudit-Parser) steht die Gesamtsuite bei **138
Tests, ebenfalls alle grün**. Die beiden Arbeiten berühren dieselbe Parser-Datei
an verschiedenen Stellen und laufen ohne gegenseitige Wirkung.

### 3.2 Echte Container-Läufe

Alle Läufe in eigenen Ergebnisbäumen; die 19 Altmessungen unberührt.

**Gegen einen lokalen Prüfstand (kostenlos, wiederholbar)** — Zahlen der
Erstmessung; zur Wiederholung nach der Korrektur siehe unten:

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

**Gegen den echten DeepSeek-Endpunkt (Kosten rund $0,04)** — ebenfalls
Erstmessung:

| | Volllauf | Teillauf |
|---|---|---|
| LLMSmartAudit `5_Vether.sol` | 719,9 s, 41/41, 9 Findings | 376,5 s, Exit 124, **23/41**, 5 Findings |
| GPTScan `5_Router.sol` | 172,2 s, 39 Aufrufe, 2 Findings, $0,0067 | 99,9 s, Exit 0, `brake`, 24 Aufrufe, 26 unterdrückt, 0 Findings |

**Nach der Korrektur des Platzhalters (Abschnitt 4) nachgemessen.** Die Korrektur
greift in den Deadline-Pfad ein, also in genau das, was diese Läufe messen. Dabei
fiel zuerst auf, dass das gptscan-Image GPTScans Quelltext einbackt und vor der
Korrektur gebaut war — ohne Neubau wäre die Änderung im Repository gewesen und in
keinem Lauf wirksam. Nach dem Neubau erneut gefahren:

* **alle vier Prüfstand-Fälle** (beide Werkzeuge) — wieder bestanden;
* **GPTScan scharf**, Voll- und Teillauf — bestätigt die beabsichtigte Wirkung
  (Abschnitt 4), Kosten $0,0124.

Den scharfen LLMSmartAudit-Lauf haben wir **nicht** erneut gefahren: die Korrektur
betrifft ausschließlich GPTScan-Quelltext, LLMSmartAudits Netz-Pfad ist am
Prüfstand verifiziert, und ein Wiederholungslauf hätte rund $0,03 gekostet, ohne
eine geänderte Codezeile zu berühren. Der Teilmengen-Nachweis in 3.3 bleibt damit
die Erstmessung. Zahlen zu allem in Abschnitt 4.5.6 von
`BA-DURCHFUEHRUNGSPROTOKOLL.md`.

### 3.3 Der Teilmengen-Nachweis

Unsere zentrale Frage lautete: **Erfindet ein Teilergebnis Findings?** Wir haben
sie in zwei Tests zerlegt, weil nur einer den Mechanismus prüft:

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

**Die Wirkung ist gemessen, nicht nur begründet.** Voll- und Teillauf haben wir mit
dem korrigierten Code wiederholt (`5_Router.sol`, DeepSeek `deepseek-v4-flash`,
$0,0124):

| `vul_before_static` | Volllauf | Teillauf (`--timeout 120`) |
|---|---|---|
| vor der Korrektur | 6 | **13** |
| nach der Korrektur | 7 | **5** |

Vorher schlug der Teillauf **mehr** Kandidaten vor als der Volllauf, jetzt
**weniger** — die Zusage „ein Teilergebnis erfindet nichts" ist damit nicht mehr
vom Zufall zweier nachgelagerter Sicherungen abhängig. Beide Vollläufe melden
dieselben zwei Findings, der reguläre Pfad ist also unverändert; der Unterschied
39/44 Aufrufe und 6/7 Kandidaten zwischen ihnen ist der bekannte
Nicht-Determinismus. Die Zahl 6→13 in `BA-DURCHFUEHRUNGSPROTOKOLL.md` bleibt als
historischer Messwert stehen, mit der Gegenprobe daneben (Abschnitt 4.5.6).

---

## 5. Was wir nebenbei richtiggestellt haben

1. **„Rund 76 s je Contract“ war Durchsatz, keine Bearbeitungszeit** (10 935 s
   Wanduhr / 143 Contracts bei 4 Prozessen). Tatsächlich: **Mittel 299,2 s,
   Median 264,1 s, Spanne 150,8–923,2 s**. Gegen 76 s gehalten hätte unser
   Volllauf (719,9 s) wie eine neunfache Verschlechterung ausgesehen.
2. **Die Image-Verkleinerung stimmt.** Der Neubau landet bei 586 MB; die
   Spanne 586–590 MB zwischen einzelnen Builds ist Rauschen. Das
   5,13-GB-Image war ein Stand vor unserer Arbeit.
3. **„Je vier Dateien nach dem SmartBugs-Schema“ war überholt** — der
   GPTScan-Skriptordner hat inzwischen sechs Dateien, alle selbst geschrieben.

---

## 6. Was wir daraus über LLM-Werkzeuge gelernt haben (für AP7)

1. **Kein Werkzeug bringt einen Lauf-Timeout mit** — GPTScan nur eine Frist je
   Aufruf, LLMSmartAudit gar keine.
2. **Ob ein Teilergebnis zu retten ist, hängt an der Ablageform** —
   Zwischenstand je Phase oder Zusammenführen am Ende. Dieselbe Anforderung
   brauchte zwei Lösungen.
3. **Die Grenze Host/Container verläuft entlang des LLM-SDKs.** Alles, was
   `openai` oder `tiktoken` braucht, läuft nur im Container; Konfiguration,
   Parser und Auswertung auf dem Host. Das hat zweimal bestimmt, wie wir testen
   konnten.
4. **`errors` gegen `fails` zeigt sich am Timeout besonders klar:** von außen
   abgeschossen (`exit_code=None`, nichts geborgen) → `fails`; Exit 124 mit
   geborgenem Zwischenstand → `errors`.
5. **Ohne Offline-Modus kostet jeder Test Geld.** Unser Prüfstand
   (`testing_tools/fake_llm_endpoint.py`) schließt diese Lücke.

---

## 7. Wie es entstanden ist

Wir haben AP5 in 14 kleine Aufgaben zerlegt und jede einzeln umgesetzt und
gegengelesen. Dabei fielen ein schwerer und vier gewichtige Mängel auf — keiner
im eigentlichen Code, alle in Tests oder Dokumentation, die schwächer waren als
die Behauptung, die sie stützen sollten:

| Aufgabe | Mangel |
|---|---|
| 2 | Ein Test importierte ein Modul, das auf dem Host nicht ladbar ist |
| 5 | Der Test des häufigeren Falls lief per `or`-Kurzschluss am geprüften Zweig vorbei |
| 7 (a) | Ein Fehlertest war schon vor der Implementierung grün, konnte also nie fehlschlagen |
| 7 (b) | Der Zwischenstand wurde nicht atomar geschrieben; ein Abbruch im falschen Moment hätte den letzten guten Stand zerstört |
| 12 | Die Doku nannte einen Test, den es nicht gab |

An zwei Stellen haben wir deshalb Mutationstests nachgeschoben — die Tests
gegen absichtlich kaputten Code laufen lassen, um zu sehen, dass sie dort
wirklich rot werden.

Bei der abschließenden Durchsicht des ganzen Branchs (Commit `a34f3067`) kamen
noch Fehler an den Nähten dazu, u. a.: Zwei Dokumente und ein Kommentar im
Entrypoint behaupteten, LLMSmartAudit lese die Bremse — tut es nicht.
`run_full_v2.ps1` schrieb „AP5 offen“ in die `run_meta.json` jedes künftigen
Laufs. Drei Dokumente führten den scharfen Lauf noch als ausstehend. Und im
LLMSmartAudit-Timeout-Test fehlte ausgerechnet `assert fails == set()`.
Außerdem fehlten `GPTSCAN_BASE_URL` und `GPTSCAN_API_KEY` in der `env:`-Zeile
der `config.yaml`, sodass der Prüfstand aus einem SmartBugs-Lauf heraus nicht
erreichbar gewesen wäre (nachgezogen in `a2611ea`).

Was wir daraus mitnehmen:

1. **Nur den Diff zu lesen reicht nicht.** Zwei Aussagen wurden durch unsere
   Änderungen *falsch*, ohne dass jemand sie angefasst hätte.
2. **Wer Doku vor dem Nachweis schreibt, muss sie danach gegen das Ergebnis
   prüfen** — sonst steht „ausstehend“ neben einem längst gelieferten Lauf.
3. **Wenn eine Korrektur mit „bricht Test X“ abgelehnt wird, Test X öffnen.**
   Bei einer der Falschaussagen oben war genau so ein Test nie vorhanden.

---

## 8. Offen

| Punkt | Stand |
|---|---|
| `ap5-timeout` nach `main` mergen | erledigt |
| DeepSeek-Schlüssel tauschen (er war zwischenzeitlich außerhalb der Schlüsseldatei im Klartext sichtbar) | im Repository nicht dokumentiert |
| belastbare Kostenzahl für LLMSmartAudit aus dem Anbieter-Dashboard | für Altläufe nicht vorhanden; neue Läufe protokollieren die Abbuchung |
