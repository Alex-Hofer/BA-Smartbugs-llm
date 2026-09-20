# Betriebsdoku: validierte Parameter, Pflichtvariablen, Fallstricke, Kosten

Alle Zahlen stammen aus den 19 durchgeführten Läufen (Stand 2026-08-02) und
sind gemessen, nicht geschätzt, sofern nicht ausdrücklich anders vermerkt.

## 1. Pflicht-Umgebungsvariablen

| Variable | Für | Pflicht? | Bemerkung |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | beide KI-Scanner | **ja** | Wird von `run_curated.ps1` aus `GPTScan/.env` gelesen und in die Prozessumgebung gesetzt. Der gepatchte `sb/docker.py` reicht ihn in den Container durch und redigiert ihn anschließend im Task-Log. |
| `LLM_MODEL` | LLMSmartAudit | **ja** | Muss auf `deepseek-v4-flash` stehen. Siehe Fallstrick 2. |
| `LLM_PROVIDER` | LLMSmartAudit | nein | Default `deepseek`. |
| `LLM_CONTEXT_TOKENS` | LLMSmartAudit | nein | `65536` als Versicherung gegen `context_length_exceeded`. |
| `LLM_BASE_URL` | LLMSmartAudit | nein | Nur für `LLM_PROVIDER=custom`. |
| `GPTSCAN_PROVIDER` | GPTScan | nein | Default `deepseek`. |
| `GPTSCAN_MODEL` | GPTScan | nein | Default `deepseek-v4-flash` (der „cheap"-Tier des Providers). |
| `GPTSCAN_DRY_RUN=1` | GPTScan | nein | Kein einziger API-Aufruf, keine Kosten, kein Schlüssel nötig. |
| `GPTSCAN_BASE_URL` | GPTScan | nein | Nur bei `GPTSCAN_PROVIDER=custom` (AP5) — zeigt auf einen frei wählbaren, OpenAI-kompatiblen Endpunkt, etwa den lokalen Prüfstand. Siehe Abschnitt 8. |

Welche Variablen überhaupt in einen Container gelangen können, steht in der
`env:`-Zeile der jeweiligen `config.yaml` — nur diese Allowlist wird
durchgereicht.

## 2. Validierte Laufparameter

| Parameter | Wert | Grundlage |
|---|---|---|
| `--processes` | **4** | Über ~580 DeepSeek-Calls bei `processes=3` traten keine Rate-Limits auf; 4 ist die getestete Obergrenze. Nicht ohne eigenen Test erhöhen. |
| `--timeout` GPTScan | **1800 s** | Längster gemessener Task: 922 s (`32_LendingPair` in `gptscan_mwefixed_v2_main`). |
| `--timeout` LLMSmartAudit | **5400 s** | Gemessen in `curated_v1_20260705`: im Mittel 299 s je Contract, Median 264 s, Maximum 923 s — der große Puffer fängt Retry-Schleifen ab. |
| Reihenfolge der Läufe | **sequenziell** | Erst GPTScan, dann LLMSmartAudit. Begrenzt API-Nebenläufigkeit auf demselben Schlüssel und den CPU-Druck. |

Seit AP5 wirkt `--timeout` **innerhalb** des Containers, nicht mehr nur als
äußerer Docker-Abschuss. Details, wie ein Teilergebnis daran zu erkennen ist
und wie sich der Timeout-Pfad ohne Kosten testen lässt: Abschnitt 8.

## 3. Kosten

| Werkzeug | Pro Contract | Kostenbremse |
|---|---|---|
| GPTScan | Median ~$0,0009 | **ja** — `MAX_COST_USD` in `GPTScan/src/config.py`, $0,50 pro Contract. Bei Erreichen stoppt der Lauf die Aufrufe, stürzt nicht ab, und vermerkt `budget_exceeded` in den Metadaten. |
| LLMSmartAudit | im Mittel ~$0,017, Median ~$0,012 (aus den Tokens hochgerechnet), Dauer im Mittel 299 s | **nein** — das Werkzeug hat keinerlei Budgetgrenze. |

Referenzwerte kompletter Läufe:

| Lauf | Umfang | Dauer | Kosten |
|---|---|---|---|
| `curated_v1_20260705` GPTScan | 143 Contracts | 3:19 min | ~$0,01 |
| `curated_v1_20260705` LLMSmartAudit | 143 Contracts | 3:02 h | ~$2,44 (aus den Tokens hochgerechnet) |
| `curated_mwefixed_live` GPTScan | 96 Contracts | 36:45 min | ~$0,28 |

**Vor jedem Massenlauf einen Dry-Run.** `run_curated.ps1 -GptscanDry` kostet
nichts und deckt Pipeline-Fehler auf, bevor Geld fließt. Für LLMSmartAudit gibt
es keinen Dry-Modus (Fallstrick 3).

## 4. Bekannte Fallstricke

**1 — GPTScan liefert leeren Output bei bestimmten Pfaden.**
Enthält der Quellpfad eines der Wörter `external`, `openzeppelin`, `uniswap`,
`pancakeswap`, `legacy` oder `test`, produziert GPTScan stillschweigend nichts.
Der Entrypoint `tools/gptscan/scripts/do_solidity.sh` kopiert die Datei deshalb
grundsätzlich nach `/work/input`.

**2 — `LLM_MODEL=deepseek-v4-flash` ist für LLMSmartAudit Pflicht.**
Das Image `smartbugs/llmsmartaudit:1.0` hat `deepseek-chat` eingebrannt. Dieses
Modell hat DeepSeek am 2026-07-24 abgeschaltet; ohne Override antwortet die API
mit HTTP 400 und der Lauf scheitert vollständig.

**3 — LLMSmartAudit hat keinen Stub-Modus.**
`LLM_MODEL=STUB` wird wörtlich an die API geschickt und mit HTTP 400 abgelehnt.
Der Lauf `results/llmsmartaudit/smoke1_stub` ist genau dieser Fehlschlag und
dient heute als Test-Fixture. Es gibt keine Möglichkeit, das Werkzeug ohne
echte API-Aufrufe zu testen.

**4 — GPTScan meldete Compile-Fehler nicht.**
Behoben am 2026-08-02. Ein nicht übersetzbarer Contract lief mit Exit-Code 0
durch und schrieb `{"success": true, "results": []}`. Hergeleitet und
dokumentiert in `docs/BA-ERRORS-VS-FAILS.md`. Bei künftigen Läufen prüfen:

```powershell
python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_<suffix>
```

**5 — `vul_before_static > vul_after_static` ist kein Fehler.**
Das ist GPTScans Static-Bestätigungsstufe, die LLM-Kandidaten verwirft — der
bestimmungsgemäße False-Positive-Filter. Er greift bei etwa der Hälfte aller
Live-Contracts und erscheint als `info`, nicht als Fehler.

**6 — LLMSmartAudit liefert keine Zeilennummern.**
Das Werkzeug argumentiert über den Quelltext und gibt keine Positionen aus. Eine
zeilengenaue Auswertung ist damit ausgeschlossen; die Arbeit wertet deshalb auf
Contract-Ebene aus. Kein Bug.

**7 — `reparse` ohne `--sarif` löscht vorhandene SARIF-Dateien.**
`sb/reparse.py` entfernt `result.json` *und* `result.sarif`, schreibt letztere
aber nur mit `--sarif` neu. Die Läufe dieser Arbeit wurden mit `--json --sarif`
erzeugt, also:

```powershell
cd smartbugs
.venv\Scripts\python.exe -m sb.reparse --sarif --processes 4 results
```

**8 — Bekannt defekte Samples.**
`samples/gptscan/_chk/{20_Pool,23_nTokenAction,5_Pools,67_Vault}.sol` sind zu
einer Zeile kollabierte Blobs und nicht übersetzbar; `74_TimeswapPair.sol` hat
einen solc-Fehler in Zeile 51. Kein Parser-Problem — der Korpus ist defekt.
Reparierter Ersatz: `samples/gptscan/mwevariety_fixed/` (siehe
`docs/BA-KORPUS-REPARATUR.md` und `corpus_tools/README.md`).

**9 — Im reparierten Korpus scheitern 2 von 96 Contracts.**
`58_UniV3Vault` bräuchte `--optimize` („Stack too deep"), `19_TransactionManager`
verliert eine Funktion an einen Falcon-IR-Konvertierungsfehler (der Contract
selbst übersetzt). Beides ist seit dem Parser-Fix im Ergebnis sichtbar.

## 5. Images bauen

```powershell
# GPTScan (aus dem Repo-Root)
docker build -t smartbugs/gptscan:1.0 .\GPTScan
```

```bash
# LLMSmartAudit -- Git Bash, nicht PowerShell.
# git archive liefert den Baum OHNE das entfernte evaluation/ (3,7 GB).
git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main \
  | docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -
```

Kein Schlüssel landet je im Image: `.dockerignore` schließt `.env` aus, und der
Schlüssel kommt zur Laufzeit aus der Prozessumgebung.

## 6. Umgebungsspezifische Stolpersteine

* **Git-Bash-Pfadumwandlung.** MSYS wandelt führende `/` in Argumenten in
  Windows-Pfade um (`!/foo/` wird zu `!C:/Program Files/Git/foo/`). Bei
  Pfadmustern `MSYS_NO_PATHCONV=1` voranstellen.
* **PowerShell-Umleitung schreibt ein BOM.** `> datei.csv` erzeugt UTF-8 mit
  BOM; Leser müssen `encoding="utf-8-sig"` verwenden (so macht es
  `analysis_tools/compare_csv.py`).
* **Windows-Pfadlänge.** `core.longpaths=true` ist **pro Clone zu setzen** — die
  Option ist eine lokale Git-Konfiguration und wird nicht mitgeklont. Ohne sie
  scheitern Operationen, die tiefer als der Arbeitsbaum liegen, mit
  `Filename too long`; ein `git worktree add` etwa bricht an
  `LLMSmartAuditTool-main/.../WareHouse/AISmartContract_…/` ab. Der längste
  getrackte Pfad misst 129 Zeichen, das Limit greift also erst zusammen mit dem
  Präfix des Zielverzeichnisses — was für einen Clone in einem tiefen Pfad
  bereits reicht. Siehe Abschnitt 7.
* **PowerShell 5.1 kennt kein `&&`/`||`.** Stattdessen `A; if ($?) { B }`.

## 7. Einrichtung nach dem Klonen

Zwei Git-Einstellungen sind **lokal pro Clone** und werden deshalb nicht
mitgeliefert. Beide gehören unmittelbar nach `git clone` gesetzt:

```powershell
git config core.longpaths true                   # sonst "Filename too long"
python analysis_tools\secret_scan.py --install    # setzt core.hooksPath auf .githooks
```

### Der pre-commit-Hook

Der Hook liegt als **getrackte Datei** unter `.githooks/pre-commit` und ruft
`analysis_tools/secret_scan.py` im Hook-Modus auf: findet er in einer gestagten
Datei einen Schlüssel, endet er mit Exit-Code 1 und der Commit kommt nicht
zustande. Der Wert wird dabei nie ausgegeben — gemeldet werden Datei, Position
und Mustername.

`--install` setzt lediglich `core.hooksPath` auf `.githooks`; es kopiert nichts
nach `.git/hooks/`. Der Unterschied ist wesentlich: `.git/` wird nie geklont, ein
dort installierter Hook schützt genau eine Maschine. Über `core.hooksPath` wirkt
stattdessen die versionierte Datei, und eine spätere Änderung am Hook erreicht
alle Beteiligten über `git pull`.

Kontrolle, dass der Hook aktiv ist:

```powershell
git config --get core.hooksPath     # muss .githooks ausgeben
```

### Was der Scan nicht sieht

Der Scan öffnet gzip-Ströme und tar-/zip-Archive und durchsucht deren Inhalt
(bis `MAX_DEPTH = 3` Schachtelungen) — ein Schlüssel in einer komprimierten
Datei bliebe einem reinen Byte-Scan sonst verborgen. Dateien über
`MAX_BYTES = 20 MB` werden **nicht** durchsucht, aber seit dieser Fassung
namentlich als „could NOT be scanned" gemeldet statt stillschweigend
übersprungen. Betroffen ist derzeit genau eine getrackte Datei:
`GPTScan/src/jars/SolidityStaticAnalysis-1.0-SNAPSHOT-standalone.jar`
(20.852.934 Bytes). Eine Prüfung außer der Reihe mit angehobenem Limit ergab
dort keinen Treffer; sie dauert allerdings rund 10 Sekunden, weshalb die Grenze
für den Hook-Betrieb bestehen bleibt.

## 8. Timeout-Verhalten und Prüfstand (AP5)

**Ausgangslage.** Keines der beiden Werkzeuge bringt einen Timeout für den
gesamten Lauf mit — GPTScan kennt nur eine Frist je einzelnem LLM-Aufruf,
LLMSmartAudit gar keine. Ohne eigenen Mechanismus greift deshalb ausschließlich
der äußere Docker-Timeout (`sb/docker.py`): Der Container wird von außen
abgeschossen, das Werkzeug erfährt nichts davon und kann kein Teilergebnis
sichern. Seit AP5 rechnet der jeweilige Entrypoint aus dem von SmartBugs
übergebenen `TIMEOUT` drei Marken:

| Marke | Anteil von `TIMEOUT` | Wirkung |
|---|---|---|
| Bremse | 70 %, mind. 1 s | Als absoluter Zeitstempel `SB_DEADLINE_EPOCH` exportiert. Nur **GPTScan** liest die Marke: Es stellt beim Erreichen keine neuen LLM-Aufrufe mehr und läuft danach regulär aus. **LLMSmartAudit liest `SB_DEADLINE_EPOCH` nicht** — der Export ist dort absichtlich wirkungslos, exportiert nur, damit beide Entrypoints dieselbe Marken-Rechnung teilen (Vergleichstest, siehe unten). |
| Netz | 90 %, mind. 1 s | `timeout` beendet den Werkzeugprozess hart, falls die Bremse nicht gegriffen hat (bei LLMSmartAudit: immer, da es keine Bremse kennt). Der Entrypoint normalisiert den Exit-Code danach einheitlich auf **124** — auch wenn `timeout` selbst 143 oder 137 meldete. Bei LLMSmartAudit ist das Netz damit die **einzige** wirksame Stufe; der Entrypoint birgt danach den Zwischenstand, den `audit_report.record()` nach jeder Detektor-Phase abgelegt hat. |
| Rest | verbleibende Zeit | Für den Entrypoint reserviert: Zwischenstand bergen, `sb_timeout` stempeln, `/output.json` garantieren. |

`--timeout 0` (kein `--timeout` gesetzt) schaltet den gesamten Mechanismus ab —
das Verhalten bleibt dann verhaltensgleich zu vor AP5, damit die bereits
gefahrenen Messläufe vergleichbar bleiben. Nicht ganz Byte für Byte: GPTScans
`tasks.py` schreibt `llm_calls_skipped_deadline` und `deadline_exceeded`
bedingungslos in die Metadaten, die `GPTSCAN_META`-Zeile hat also unabhängig
von `--timeout` immer zwei Schlüssel mehr als vor AP5. Kein Parser stört sich
daran.

**Ein Teilergebnis erkennen.** Drei Stellen im Ergebnis zeigen es an:

* Das Feld `sb_timeout` auf oberster Ebene des Reports —
  `{"hit": true, "stage": "brake"|"net", "detail": "..."}`. Fehlt es, war der
  Lauf vollständig.
* In `result.json` erscheint ein Eintrag in `errors` mit dem Präfix
  `TIMEOUT_` (`TIMEOUT_BRAKE` bzw. `TIMEOUT_NET`) — nie in `fails`, denn der
  Lauf wurde absichtlich beendet, nicht ausgehebelt.
* Bei LLMSmartAudit zusätzlich `categories_checked < categories_total` im
  Report: wie viele der 41 Detektor-Phasen tatsächlich liefen. `checked == 0`
  wird selbst ohne `sb_timeout` als `errors` gemeldet, damit eine leere
  Findings-Liste nie stillschweigend als „sauber" gelesen wird.

**Prüfstand ohne echte API-Kosten.** Da keines der beiden Werkzeuge einen
Offline- oder Stub-Modus kennt (bei LLMSmartAudit geht selbst `LLM_MODEL=STUB`
wörtlich an die API), gibt es seit AP5 einen lokalen, OpenAI-kompatiblen
Ersatz-Endpunkt, der absichtlich langsam antwortet und damit den Timeout-Pfad
kostenlos und deterministisch auslöst:

```powershell
python -m testing_tools.fake_llm_endpoint --port 8099 --delay 30
```

Aus dem Container ist der Host unter `host.docker.internal` erreichbar. Beide
Werkzeuge lassen sich darauf umleiten:

| Werkzeug | Umgebungsvariablen |
|---|---|
| GPTScan | `GPTSCAN_PROVIDER=custom` und `GPTSCAN_BASE_URL=http://host.docker.internal:8099` |
| LLMSmartAudit | `LLM_PROVIDER=custom` und `LLM_BASE_URL=http://host.docker.internal:8099` |

Der Provider `custom` ist bei beiden Werkzeugen mit Preis `0` hinterlegt — ein
Lauf gegen den Prüfstand kann keine Kosten erzeugen, auch nicht versehentlich.
`LLM_PROVIDER=custom` existierte für LLMSmartAudit bereits vor AP5 und ist über
`smartbugs/tools/llmsmartaudit/config.yaml`s `env:`-Allowlist bereits
containertauglich. `GPTSCAN_PROVIDER=custom`/`GPTSCAN_BASE_URL` sind mit AP5 neu
in `GPTScan/src/llm_backend.py` hinzugekommen und für sich getestet (siehe
`tests/test_gptscan_deadline.py`).

> **Nachgetragen (Commit `a2611ea`):** `smartbugs/tools/gptscan/config.yaml`s
> `env:`-Zeile führte `GPTSCAN_BASE_URL` zunächst nicht — nur
> `GPTSCAN_PROVIDER`. Das ist behoben: die `env:`-Zeile führt inzwischen auch
> `GPTSCAN_BASE_URL` und `GPTSCAN_API_KEY` (Mechanismus: Abschnitt 2 in
> `docs/BA-WERKZEUG-BEDIENUNG.md`), ein `sb -t gptscan`-Lauf über SmartBugs
> bekommt die Basis-URL damit in den Container gereicht. Belegt ist damit die
> Durchreichung der Variablen bis an den Container; ein tatsächlicher
> `sb -t gptscan`-Lauf gegen den Prüfstand-Endpunkt aus dem Container heraus
> ist mit dem scharfen Lauf in Abschnitt 4.5 von
> `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` inzwischen belegt (siehe unten).

**Was das nicht ersetzt.** Der Prüfstand belegt den Mechanismus in 32 eigenen Tests innerhalb einer
grünen Suite und in einer Vorprüfung des `timeout`-Kommandos in beiden Images
(`docs/BA-AP5-VORPRUEFUNG.md`). Der Nachweis im scharfen Betrieb — gegen einen
echten, tatsächlich ablaufenden Endpunkt — ist erledigt (Commit `43c3f32`,
Abschnitt 4.5 in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`): je ein Contract pro
Werkzeug zeigt, dass ein Teillauf nichts erfindet — nicht, wie viel ein
Teillauf im Mittel verpasst (dortige Limitation 7).
