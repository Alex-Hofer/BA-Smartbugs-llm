# Verifikationsbericht

Unabhängige Überprüfung der Arbeit vom 2026-08-02, dokumentiert in
`BA-ARBEITSBERICHT-20260802.md` und `BA-AUFGABEN-UND-STATUS.md`.

**Maßstab:** Jede Behauptung wurde mit dem Ziel geprüft, sie zu *widerlegen*.
Jede Aussage in diesem Bericht ist mit dem tatsächlich ausgeführten Befehl
belegt. Befunde aus der ersten Durchsicht sind nur dann als bestätigt
geführt, wenn sie anschließend selbst nachgerechnet wurden.

Stand: 2026-08-02. Rohdaten und Prüfskripte lagen in einem temporären
Arbeitsverzeichnis; die verwendeten Befehle stehen bei jedem Punkt.

> **Nachtrag 24.09.2026.** Befund 3.1 und die Reparatur in Abschnitt 6
> beruhten auf dem Vergleich gegen den Tag `v2.1.1`. Gegen den tatsächlich
> geklonten Stand `7ddaf6c` weichen in `smartbugs/sb/` nur `docker.py` und
> `tools.py` ab; `solidity.py`, `analysis.py` und `io.py` sind Upstream-Arbeit
> (`BA-EIGENANTEIL.md` 2.1, Korrektur vom 21.09.2026). Zeilenangaben zu
> `sb/docker.py` in 2.4 haben sich durch spätere Einfügungen verschoben. Die
> übrigen Befunde gelten unverändert; der Stand vom 24.09.2026 steht in
> [`BA-VERIFIKATIONSBERICHT-20260924.md`](BA-VERIFIKATIONSBERICHT-20260924.md).
> Von den in Abschnitt 6 „bewusst offen“ gebliebenen Befunden ist 3.3 (ANTLR)
> am 24.09.2026 geklärt (`BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.7) und 3.9
> (Testsuite-Lücken) teilweise geschlossen (M4 im Bericht vom 24.09.2026).

---

## 1. Vorgehen

Sieben Prüfpakete. Drei davon (Sicherheit, Testsuite/Mutationsprobe,
Eigenanteil-Diff) wurden bewusst getrennt und ohne Kenntnis der übrigen
Befunde bearbeitet, die vier anderen (Parser-Audit, Errors/Fails-Semantik,
Zahlenkontrolle, Reproduzierbarkeit) im Zusammenhang.

Alle Prüfungen liefen **lesend**. Schreibende Tests (Mutationsprobe,
pre-commit-Hook) fanden in Klonen außerhalb des Repos statt. Es entstanden
keine LLM-Kosten, es wurde kein Rohdatum verändert, nichts gepusht.

Die Gegenprobe stützt sich auf `BA-results-raw-backup-20260802`, die
vollständige Kopie von `smartbugs/results/` **vor** allen Eingriffen. Sie
enthält die Prä-Fix-`result.json` und erlaubt damit, den Vorher/Nachher-Vergleich
unter identischen Regeln zu rechnen.

---

## 2. Was der Prüfung standgehalten hat

### 2.1 Die zentrale Behauptung: 1368 → 0 Lücken

Dasselbe Audit, derselbe Detektor-Katalog, gegen beide Datenstände:

```powershell
python analysis_tools\parser_audit.py
#  TOTAL   930 Tasks   1464 Meldungen   0 Lücken        (25,4 s)

python analysis_tools\parser_audit.py "…\BA-results-raw-backup-20260802"
#  TOTAL   930 Tasks   1464 Meldungen   1368 Lücken
#  LOG_ERROR 708 | TRACEBACK 334 | COMPILE_ERROR 246
#  OUTPUT_UNSUCCESSFUL 44 | STATIC_SKIPPED 36
```

Alle fünf Signaltypen exakt wie dokumentiert. Dass die Zahl der Rohmeldungen
in beiden Läufen identisch **1464** ist, ist dabei die entscheidende
Kontrolleigenschaft: die Detektoren lesen ausschließlich Rohmaterial, und das
wurde nicht angefasst. Verändert hat sich nur, wie viel davon im Parser-Output
wiederauffindbar ist.

### 2.2 Die BA-Zahlen sind unberührt

Vergleich aller 930 `result.json` gegen ihre Prä-Fix-Fassung im Backup:

| Feld | Tasks mit Änderung | Richtung |
|---|---:|---|
| `findings` | **0** | — |
| `errors` | 341 | ausnahmslos mehr |
| `infos` | 377 | ausnahmslos mehr |
| `fails` | 0 | — |

Kein einziger Task hat ein Finding verloren oder gewonnen. Alle Änderungen
sind additiv — es wurde nichts entfernt. Damit ist belegt, was
`evaluate_curated.py` byte-gleich lässt: das Skript liest ausschließlich
`findings`.

### 2.3 Nachgerechnete Zahlen

| Behauptung | Ist | Prüfung |
|---|---|---|
| 930 Task-Verzeichnisse | 930 | Auszählung aus `smartbugs.json` |
| gptscan / llmsmartaudit / slither | 640 / 147 / 143 | dito |
| 19 Läufe | 19 Ergebnisordner | siehe Anmerkung unten |
| 586 sauber / 344 Errors / 50 Fails | exakt | `errors_fails_report.py` |
| 246 Tasks, 98 Contracts, 9 Läufe | exakt | eigene Auszählung |
| 62 Dateien mit Klartext-Schlüssel | exakt | Auszählung im Backup |
| 44 Tasks mit Exit-Code 1 | 44, **alle** mit rohem Traceback | eigene Auszählung |
| slither: 140 Tasks mit Exit 255 | exakt | eigene Auszählung |
| Audit-Laufzeit ~23 s | 25,4 s | Stoppuhr |
| 41 pytest-Tests | 41 grün | `pytest tests -q` |
| 17 Fehlschläge gegen `f85946e` | 17 failed / 24 passed | Klon, namentlich belegt |
| `curated_mwefixed_live`: 96 Contracts | 96 | eigene Auszählung |
| davon 35 Static-Crash, 31 × `tasks.py:245`, 3 JSON-Fehler, 1 Compilat | exakt | eigene Auszählung |

**Anmerkung zu „19 Läufe":** Es sind 19 Ergebnisordner (`<tool>/<lauf>`) und
19 (Werkzeug, `runid`)-Paare, aber nur **18 verschiedene `runid`s** — der Lauf
`smoke2_live` umfasste gptscan *und* llmsmartaudit. Die Zahl 19 ist damit
korrekt, wenn man Ergebnisordner zählt, und das tut die Auswertung durchgehend.
Kein Fehler.

**Wichtig zur Lesart der Bilanz:** 586 / 344 / 50 / 246 sind **keine
disjunkten Klassen**. Es gilt 586 + 344 = 930; die 50 Tasks mit Fails sind
vollständig eine **Teilmenge** der 344 mit Errors (nachgerechnet: 50 Tasks mit
beidem, 0 mit Fails ohne Errors), und die 246 nicht übersetzten verteilen sich
über beide. Die Zahlen dürfen nicht addiert werden.

### 2.4 Die Semantik-Herleitung

Jeder Zeilenverweis in `BA-ERRORS-VS-FAILS.md` wurde am Code nachgeschlagen:

| Verweis | Inhalt | Urteil |
|---|---|---|
| `parse_utils.py:66-90` | `errors_fails()` | korrekt |
| `parse_utils.py:8-15` | `DOCKER_CODES` | korrekt |
| `parse_utils.py:40-54` | `exceptions()` | korrekt |
| `parse_utils.py:71-85` | Exit-Code-Kaskade | korrekt |
| `parse_utils.py:86-89` | Log-Auswertung | korrekt |
| `parse_utils.py:84` | zitierter Upstream-Kommentar | korrekt |
| `parse_utils.py:32-37` | `EXCEPTIONS`-Muster | korrekt |
| `slither-0.11.3/parser.py:126` | `errors.discard("EXIT_CODE_255")` | korrekt, Zitat wortgleich |
| `sb/docker.py:159-163` | Redaktions-Patch | korrekt |

### 2.5 Die drei Detektor-Korrekturen

1. **slither Exit-255 gutartig** — belegt an `parser.py:126` und an 140 realen
   Tasks.
2. **`Warning:`/`Error:` als Compile-Kriterium unzuverlässig** — im Feld
   bestätigt: `58_UniV3Vault.sol` stirbt in
   `crytic_compile/platform/solc.py:575` an `json.loads(stdout)`. Genau der
   beschriebene Mechanismus, mit dem `--combined-json` an einer bloßen Warnung
   scheitert.
3. **`ContractSolcParsing` ist kein Compile-Fehler** — nachgeprüft an
   `19_TransactionManager.sol` im Lauf `curated_mwefixed_live`:
   `ContractSolcParsing` vorhanden, `InvalidCompilation` **nicht**, kein
   „Falcon is not initialized", kein Degradations-Info — und **ein Finding**
   (`MWE-203`). Der Contract hat übersetzt. Die Korrektur ist richtig; ohne sie
   wäre dieser Task fälschlich als „nicht übersetzt" geführt worden.

### 2.6 Static-Filtering

202 Tasks weisen `vul_before_static > vul_after_static` auf. Davon werden
**0** als error oder fail geführt, und **0** bleiben ohne info-Eintrag. Beide
Richtungen sauber.

### 2.7 Sicherheit

* Kein echter Schlüssel im Arbeitsbaum — geprüft mit einem vom
  `secret_scan.py` **unabhängigen** Musterkatalog über den gesamten Baum,
  einschließlich der entpackten `result.log.gz` und aller `.tar`-Member unter
  `tests/fixtures/`. Einzige Fundstelle: die git-ignorierte, ungetrackte
  `GPTScan/.env`.
* Kein Schlüssel in der erreichbaren git-History (403.246 Diff-Zeilen gescannt).
* Die Redaktion hat **ausschließlich** `.docker.environment.DEEPSEEK_API_KEY`
  verändert: 868 der 930 `smartbugs.json` sind byte-identisch zum Backup, 62
  unterscheiden sich in genau diesem einen Pfad, sonst nirgends.
* `secret_scan.py --all`: 1123 Dateien, kein Fund, kein Falschtreffer.
  (1123 = die dokumentierten 1121 plus die beiden inzwischen gestagten
  Berichtsdokumente.)
* Der pre-commit-Hook blockiert einen eingeschleusten Testschlüssel zuverlässig
  und gibt den Wert nicht aus; eine harmlose Datei geht durch.

### 2.8 Testsuite

Die Behauptung „41 Tests, 17 fallen gegen die Vorversion" trägt exakt:
`git checkout f85946e -- <beide parser.py>` → **17 failed, 24 passed**,
13 gptscan- und 4 llmsmartaudit-Tests, namentlich protokolliert.

**Mutationsprobe:** 31 gezielt eingebaute Fehler, **23 erkannt**. Im Kernbereich
— errors/fails-Trennung, Sichtbarkeit gescheiterter Compilate, De-Wrapper,
Unterscheidung der Ausfallgründe — fällt **jede** Mutation auf (9 von 9 der
vorgegebenen, dazu 14 weitere). Die Suite passiert nicht zufällig.

Die 18 Fixture-Dateien sind byte-identisch zu ihren Quellen; die gzip-Kompression
ist verlustfrei (489.366 B dekomprimiert, identisch).

### 2.9 Reproduzierbarkeit

* `run_curated.ps1` ist syntaktisch fehlerfrei (`PSParser::Tokenize`, 0 Fehler).
* Kein toter Verweis in der Dokumentation. Die 120 geprüften Datei- und
  Zeilenverweise lösen alle auf; scheinbare Treffer sind kontextrelative Pfade
  (`src/tasks.py` im GPTScan-Abschnitt, `sb/parse_utils.py` im
  SmartBugs-Abschnitt) und existieren sämtlich.
* Die einzige verbliebene Erwähnung des entfernten Dokuments ist der Satz,
  der seine Entfernung beschreibt.

---

## 3. Bestätigte Befunde

Nach Schwere geordnet.

### 3.1 KRITISCH — `smartbugs/sb/` hat fünf geänderte Dateien, nicht eine

`BA-EIGENANTEIL.md` Abschnitt 2.1 trägt die Überschrift „SmartBugs — genau eine
Änderung" und nennt `sb/docker.py`. Der Hash-Vergleich gegen den frisch
geklonten Upstream-Tag `v2.1.1` zeigt **fünf** abweichende Dateien:

| Datei | dokumentiert | Inhalt der Änderung |
|---|---|---|
| `docker.py` | ja | `env`-Passthrough in den Container, Redaktion der Werte |
| `tools.py` | **nein** | fügt `env` zu `FIELDS` und zur `Tool`-Dataclass hinzu |
| `solidity.py` | **nein** | `CONTRACT_NAMES`: `[A-Za-z0-9_]*` → `[a-zA-Z$_][a-zA-Z0-9$_]*` |
| `analysis.py` | **nein** | Retry-Logik umgestellt, `os.makedirs` in try/except |
| `io.py` | **nein** | rein kosmetisch |

`tools.py` wiegt am schwersten: ohne diesen Patch liest SmartBugs das Feld
`env:` in `tools/gptscan/config.yaml` und `tools/llmsmartaudit/config.yaml` gar
nicht ein. Der API-Schlüssel-Mechanismus, den die Dokumentation vollständig
`docker.py` zuschreibt, besteht tatsächlich aus **zwei** Dateien.
`solidity.py` verändert, welche Contract-Namen SmartBugs überhaupt erkennt.

**Wirkung auf die Messwerte: keine.** Alle 19 Läufe entstanden bereits mit
diesem Stand. Es ist eine Lücke in der Abgrenzung von Eigen- und Fremdanteil —
für ein Dokument, dessen einziger Zweck genau diese Abgrenzung ist, der
schwerste Einzelbefund.

Folgefehler: der SCOPE-Abschnitt in `LICENSE` nennt ebenfalls nur `docker.py`.

### 3.2 HOCH — Blindfleck im Detektor-Katalog: WARNING-Records

`WARNING utils: Cannot find functionB or same function` steht im Rohlog von
`curated_mwefixed_live/5_Pools.sol` und `70_VaderPoolV2.sol`, aber **weder in
`result.json`** (nicht in errors, fails oder infos) **noch in der Signalliste
des Audits**.

Ursache: Audit (`_LOG_ERROR`) und Parser (`_LOG_LEVEL`) reagieren beide nur auf
`ERROR|CRITICAL`. WARNING wird nur im Sonderfall „Falcon is not initialized"
erfasst. Ein **gemeinsamer** blinder Fleck ist per Konstruktion unsichtbar: das
Audit meldet „0 Lücken", obwohl eine Meldung fehlt.

Umfang: 2 von 930 Tasks; 2 von 142 WARNING-Records im gesamten Korpus.

Das qualifiziert die Kernaussage „über alle 930 Tasks geht keine Meldung mehr
verloren" unmittelbar. `BA-AUFGABEN-UND-STATUS.md` benennt diese Klasse von
Problem bereits als „Einschränkung 2", allerdings hypothetisch — hier ist ein
konkreter Fall im vorhandenen Material.

### 3.3 HOCH — Blindfleck im Detektor-Katalog: ANTLR-Grammatikmeldungen

GPTScans ANTLR-Grammatik lehnt Quelltext ab und schreibt roh auf stderr:

```
line 14:46 extraneous input 'constant' expecting {'error', 'external', …}
line 43:8  extraneous input 'var'      expecting {…}
```

Betroffen sind **284 von 930 Tasks** in 12 Läufen, darunter der **Hauptlauf
`curated_v1_20260705` mit 87 Tasks**. Keine einzige dieser Meldungen erreicht
`result.json`; weder Parser noch Audit noch `sb.parse_utils` sehen sie an (es
sind weder Tracebacks noch Log-Records).

Die betroffenen Contracts sind überwiegend alte Solidity-0.4-Quellen, deren
Syntax (`constant`, `var`, `finney`) die verwendete Grammatik nicht kennt.

**Nicht geklärt und ausdrücklich offen:** ob diese Ablehnungen GPTScans
Funktionsextraktion tatsächlich verstümmeln. ANTLR erholt sich von
`extraneous input` und arbeitet weiter. Ob dabei Funktionen verlorengehen,
wäre eigens zu untersuchen — es berührt die Aussagekraft des Hauptlaufs und
ist damit der einzige Befund dieses Berichts, der potenziell die Interpretation
der Messwerte betrifft.

Getrennt davon: 14 Tasks zeigen `token recognition error at: '═'`. Das ist
Rauschen — gerenderte Konsolenzeichen im Lexer-Eingang, kein Diagnosewert.

### 3.4 MITTEL — Der rich/roh-Diskriminator hat zwei Gegenbeispiele

`BA-ERRORS-VS-FAILS.md` stellt die Regel absolut auf: „roh auf stderr = dem
Prozess entkommen → fail", und definiert fail als „Das Ergebnis ist nicht
zustande gekommen."

`16_Liquidation.sol` (in den Läufen `curated_mwe_20260706` und `mwevar_dry`)
trägt ein **rohes** Traceback aus `src/antlr4helper/SolidityParser.py`, der
Container beendet sich aber mit **Exit-Code 0**, und ein — degradiertes —
Ergebnis liegt vor. `result.json` führt trotzdem
`exception (TypeError: 'NoneType' object is not subscriptable)` unter `fails`.

Die Regel gilt für **638 von 640** gptscan-Tasks, nicht ausnahmslos. Die
Fehlklassifikation entsteht **upstream** in `sb.parse_utils.exceptions()`, nicht
im überarbeiteten Parser — dieser reicht rohe Records bewusst dorthin weiter.

Gegenprobe in die andere Richtung: **kein** Fall, in dem ein `rich`-gerendertes
Traceback den Prozess doch beendet hätte. Die Hälfte der Regel, auf der die
Silent-Failure-Reparatur beruht, ist damit ausnahmslos bestätigt.

### 3.5 MITTEL — `sb/results2csv.py` ist nicht versioniert

`smartbugs/.gitignore:43` enthält das Muster `results*` ohne führenden
Schrägstrich. Es trifft damit nicht nur den Ergebnisordner, sondern auch die
Quelldatei `smartbugs/sb/results2csv.py`:

```
git check-ignore -v smartbugs/sb/results2csv.py
→ smartbugs/.gitignore:43:results*   smartbugs/sb/results2csv.py
```

Die Datei liegt lokal vor, ist aber **nicht getrackt**. Ein frischer Klon
enthält sie nicht, während `README.md` `python -m sb.results2csv results` als
Arbeitsschritt vorschreibt. Der dokumentierte Ablauf ist auf einem frischen
Checkout nicht durchführbar.

### 3.6 MITTEL — Die „neu"-Zahlen im Eigenanteil sind arithmetisch unmöglich

| Komponente | Doku | getrackte Dateien insgesamt |
|---|---|---|
| GPTScan | 38 + 7 + 22 = **67** | **66** |
| LLMSmartAuditTool | 212 + 9 + 36 = **257** | **235** |

Die Summe übersteigt in beiden Fällen die Gesamtzahl der getrackten Dateien.
Die Werte „unverändert" und „geändert" sind korrekt; falsch ist jeweils die
Spalte „neu". Zusätzlich zählen 10 Dateien unter `GPTScan/reports/` — generierte
Lauf-Ergebnisse (CSV/HTML/PDF) — in die „neu"-Zahl hinein, ohne in einer
Tabelle des Dokuments als Eigenanteil ausgewiesen zu sein.

### 3.7 MITTEL — `secret_scan.py` ist enger als dargestellt

`PATTERNS` erfasst OpenAI/DeepSeek (`sk-`), OpenAI-Projekt-Keys, GitHub
(classic und fine-grained), AWS, Slack und Private-Key-Blöcke. Es fehlen:

* Google-API-Schlüssel (`AIza…`)
* JWTs (`eyJ…`)
* generische Zuweisungen `PASSWORD=` / `SECRET=`
* **Anthropic-Schlüssel** (`sk-ant-api03-…`) — das Muster
  `sk-[A-Za-z0-9]{20,}` lässt keine Bindestriche im Körper zu und bricht nach
  `sk-ant` ab

Für dieses Projekt folgenlos: es existiert nur ein DeepSeek-Schlüssel im
`sk-`-Format, und der wird erfasst. Die Beschreibung „hoch-konfidente
Schlüsselformen" ist zutreffend, die Darstellung im Arbeitsbericht („in beide
Richtungen gegengeprüft") legt jedoch eine Breite nahe, die der Scan nicht hat.

### 3.8 NIEDRIG — Off-by-one bei den Static-Abbrüchen

`BA-AUFGABEN-UND-STATUS.md`, Teil C Punkt 3: „weitere Static-Check-Abbrüche
(`tasks.py:325`, `:232`) — **22**". Tatsächlich sind es **21 verschiedene
Contracts**: `14_YieldSourcePrizePool.sol` trägt beide Abbruchstellen und wurde
doppelt gezählt (19 + 3 summiert statt vereinigt).

Alle übrigen Zahlen dieser Tabelle stimmen exakt (35 / 31 / 3 / 1).

### 3.9 NIEDRIG — Lücken in der Testsuite außerhalb des Kernbereichs

Die Mutationsprobe fand 8 unerkannte Mutationen, sämtlich im Finding-Inhalt und
bei Info-Meldungen:

* Für GPTScan-Findings existiert **keine** Assertion auf `severity`, `line`,
  `line_end` oder `filename` — alle vier lassen sich ersatzlos streichen, ohne
  dass ein Test fällt. LLMSmartAudit hat genau diese Tests; es ist eine
  Asymmetrie, kein Konzept.
* `test_synthetic_budget_cap_is_an_error` wirkt wie zwei Prüfungen, ist aber
  eine: die Meldung `"7 LLM calls skipped: per-contract cost cap reached"`
  erfüllt beide Assertions allein. Fällt `budget_exceeded` still aus, bleibt
  der Test grün.
* `GPTScan reported success=false` kommt **44-mal real** vor, wird aber nur
  synthetisch geprüft.

### 3.10 NIEDRIG — Restliste offener Docstrings unzutreffend

`BA-AUFGABEN-UND-STATUS.md` nennt „rund 13 **interne** Helfer in
`corpus_tools/build_fixed.py` sowie **private** Helfer in
`GPTScan/src/llm_backend.py` und `report_md.py`".

Tatsächlich (AST-Auswertung über den gesamten Eigenanteil):

| Datei | ohne Docstring | Art |
|---|---:|---|
| `corpus_tools/build_fixed.py` | 18 | **öffentlich**, nicht intern |
| `GPTScan/src/llm_backend.py` | 5 | **öffentlich**, nicht privat |
| `GPTScan/src/report_md.py` | 4 | privat — stimmt |
| `corpus_tools/analyze_run.py` | 2 | in der Doku nicht erwähnt |
| `chatdev/audit_report.py` | 14 | nicht erwähnt, **und kein Modul-Docstring** |
| Testfunktionen | 15 | laut Doku Absicht |

Summe: **59** Funktionen/Klassen ohne Docstring. `audit_report.py` ist die
einzige Datei des Eigenanteils ganz ohne Modul-Docstring.

### 3.11 HYGIENE — unerreichbarer Blob im Objektspeicher

`git fsck` meldet einen unerreichbaren 53-Byte-Blob mit dem Inhalt
`DEEPSEEK_API_KEY=sk-abc123def4…`. Die Struktur ist erkennbar sequenziell und
entspricht keinem echten Schlüsselformat; der Blob ist in keinem Commit oder
Tree referenziert. Kein Leck. Er verschwindet mit dem nächsten `git gc`.

---

## 4. Widerlegte Verdachtsmomente

Diese Punkte wurden gezielt angegriffen und haben gehalten. Sie stehen hier,
weil ein Prüfbericht ohne gescheiterte Angriffe nichts über seine eigene
Strenge aussagt.

| Verdacht | Prüfung | Ergebnis |
|---|---|---|
| Das Audit sucht `ERROR` unverankert, der Parser verankert (`^`) — eine Lücke müsste möglich sein | 640 gptscan-Tasks, beide Regexe gegeneinander | **1916 Records, identische Treffer, 0 Abweichungen.** Die Differenz existiert im Code, wirkt auf diesem Korpus nicht. |
| Ein `rich`-gerendertes Traceback, das den Prozess doch beendet hat | Kreuztabelle über alle 640 gptscan-Tasks | **kein einziger Fall** |
| Die 40-Zeichen-Toleranz des Audits versteckt echten Verlust | Signalabgleich | keine Meldung, die nur durch die Toleranz als abgedeckt gilt |
| Ein vierter `JSONDecodeError` in `curated_mwefixed_live` widerspricht der „3" | Einzelfallanalyse | **Die Doku hat recht.** Der vierte Fall (`58_UniV3Vault.sol`) ist das gescheiterte Compilat, das separat geführt wird. Der Prüfer lag falsch. |
| „19 Läufe" ist falsch, es sind 18 `runid`s | Auszählung | **Die Doku hat recht.** 19 Ergebnisordner; die 18 entstehen nur, weil `smoke2_live` zwei Werkzeuge umfasst. |
| `curated_mwefixed_live` sei ein falscher Laufname | Verzeichnisprüfung | **Die Doku hat recht** — es ist der Verzeichnisname und ein gültiger Pfad. |
| Tote Verweise in der Dokumentation | 120 Verweise maschinell geprüft | **keiner tot**; scheinbare Treffer sind kontextrelative Pfade, alle existent |
| Exception-Zeilen ohne Traceback-Kopf gehen verloren | 4 Formen, 86 Records | alle erreichen `result.json` |

---

## 5. Zusammenfassung

Die drei Aussagen, an denen die Arbeit hängt, halten stand:

1. **1368 → 0 Lücken** — mit derselben Methode gegen beide Datenstände belegt.
2. **Die BA-Zahlen sind unberührt** — `findings` bei allen 930 Tasks identisch,
   alle Änderungen additiv.
3. **Die errors/fails-Trennung ist hergeleitet, nicht erfunden** — jeder
   Zeilenverweis stimmt, und die für die Reparatur entscheidende Richtung
   (`rich`-gerendert ⇒ abgefangen) ist ausnahmslos bestätigt.

Der Vorbehalt betrifft die Reichweite von Aussage 1: „keine Meldung geht
verloren" gilt **innerhalb des Detektor-Katalogs**. Zwei Meldungsklassen liegen
nachweislich außerhalb — WARNING-Log-Records (2 Tasks) und ANTLR-Grammatik-
diagnostik (284 Tasks). Beide waren dem Audit per Konstruktion unsichtbar, weil
Detektor und Parser dieselbe Einschränkung teilen.

Der schwerste dokumentarische Befund liegt nicht beim Parser, sondern im
Eigenanteil-Nachweis: vier von fünf Änderungen am SmartBugs-Kern sind nicht
ausgewiesen, darunter mit `tools.py` die funktionale Hälfte des dokumentierten
API-Schlüssel-Mechanismus.

---

## 6. Was daraufhin repariert wurde

| Befund | Erledigt |
|---|---|
| 3.1 SmartBugs: 5 statt 1 geänderte Datei | `BA-EIGENANTEIL.md` 2.1 neu geschrieben — `tools.py` als zweite Hälfte des Schlüssel-Mechanismus, `solidity.py`/`analysis.py`/`io.py` mit Was und Warum. `LICENSE` SCOPE nennt jetzt alle fünf |
| 3.5 `sb/results2csv.py` nicht versioniert | `smartbugs/.gitignore` geankert (`results*` → `/results*`). Der Bug schloss **sechs** Upstream-Dateien aus, nicht eine; alle sechs sind jetzt versioniert und byte-identisch zum Upstream |
| 3.6 „neu"-Zahlen arithmetisch unmöglich | Selbst neu gerechnet: GPTScan 38 + 7 + **21** = 66, LLMSmartAudit 212 + 9 + **14** = 235. Beide Summen gehen jetzt auf. Die 10 generierten Dateien unter `GPTScan/reports/` sind als Lauf-Ergebnisse ausgewiesen statt stillschweigend mitgezählt |
| 3.8 Off-by-one Static-Abbrüche | 22 → **21** in `BA-AUFGABEN-UND-STATUS.md`, mit Begründung (ein Contract trägt beide Abbruchstellen) |
| 3.10 Docstring-Restliste unzutreffend | Abgearbeitet statt korrigiert: **59 → 0** Funktionen/Klassen ohne Docstring über den gesamten Eigenanteil |
| Upstream-Stände nicht fixiert | `BA-EIGENANTEIL.md` nennt jetzt `29a1747` / `c507fe4` / `v2.1.1` und enthält den fehlenden SmartBugs-Klonbefehl |
| conftest-Begründung ungenau | Präzisiert: synthetisches Material entsteht aus zwei Gründen, nicht nur „kam nie vor" |

Gegenprobe nach allen Änderungen: `pytest tests -q` → **41 passed**,
`parser_audit.py` → **930 Tasks, 1464 Meldungen, 0 Lücken**.

### Bewusst offen geblieben

| Befund | Grund |
|---|---|
| 3.2 WARNING-Blindfleck | Die Reparatur würde `errors` in 2 Tasks erhöhen und damit gemessene Werte verändern — das ist eine Entscheidung des Autors, keine des Prüfers |
| 3.3 ANTLR-Blindfleck | Vorher ist zu klären, ob die Grammatik-Ablehnung GPTScans Funktionsextraktion tatsächlich verstümmelt. Erst danach lässt sich sagen, ob es ein Melde- oder ein Messproblem ist |
| 3.4 Diskriminator-Gegenbeispiele | Betrifft die Formulierung in `BA-ERRORS-VS-FAILS.md`, also BA-Prosa |
| 3.7 `secret_scan.py`-Muster | Für dieses Projekt folgenlos; eine Erweiterung ist eine Funktionsänderung, keine Korrektur |
| 3.9 Testsuite-Lücken | Neue Assertions sind neue Tests, nicht Dokumentation |
| 3.11 dangling Blob | Verschwindet mit dem nächsten `git gc`; kein Leck |
