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

Welche Variablen überhaupt in einen Container gelangen können, steht in der
`env:`-Zeile der jeweiligen `config.yaml` — nur diese Allowlist wird
durchgereicht.

## 2. Validierte Laufparameter

| Parameter | Wert | Grundlage |
|---|---|---|
| `--processes` | **4** | Über ~580 DeepSeek-Calls bei `processes=3` traten keine Rate-Limits auf; 4 ist die getestete Obergrenze. Nicht ohne eigenen Test erhöhen. |
| `--timeout` GPTScan | **1800 s** | Längster gemessener Task: 600 s. |
| `--timeout` LLMSmartAudit | **5400 s** | Gemessen ~366 s/Contract, Maximum 559 s — der große Puffer fängt Retry-Schleifen ab. |
| Reihenfolge der Läufe | **sequenziell** | Erst GPTScan, dann LLMSmartAudit. Begrenzt API-Nebenläufigkeit auf demselben Schlüssel und den CPU-Druck. |

## 3. Kosten

| Werkzeug | Pro Contract | Kostenbremse |
|---|---|---|
| GPTScan | Median ~$0,0009 | **ja** — `MAX_COST_USD` in `GPTScan/src/config.py`, $0,50 pro Contract. Bei Erreichen stoppt der Lauf die Aufrufe, stürzt nicht ab, und vermerkt `budget_exceeded` in den Metadaten. |
| LLMSmartAudit | ~$0,01, Dauer ~366 s | **nein** — das Werkzeug hat keinerlei Budgetgrenze. |

Referenzwerte kompletter Läufe:

| Lauf | Umfang | Dauer | Kosten |
|---|---|---|---|
| `curated_v1_20260705` GPTScan | 143 Contracts | ~15–38 min | < $0,50 |
| `curated_v1_20260705` LLMSmartAudit | 143 Contracts | ~3,5–4,5 h | ~$1,50–3 (Ceiling ~$8–10) |
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
`docs/BA-KORPUS-REPARATUR.tex` und `corpus_tools/README.md`).

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
