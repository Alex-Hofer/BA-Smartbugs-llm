# Betrieb: Parameter, Pflichtvariablen, Kosten, Fallstricke

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Was wir beim Betrieb der drei Werkzeuge gelernt haben: welche Parameter sich
bewährt haben, welche Variablen gesetzt sein müssen, was ein Lauf kostet und wo
wir hineingelaufen sind. Die Zahlen stammen aus unseren aufgezeichneten Läufen
(Stand 24.09.2026) und sind gemessen, sofern nicht anders vermerkt.

## 1. Pflicht-Umgebungsvariablen

| Variable | Für | Pflicht | Bemerkung |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | beide LLM-Scanner | **ja** | `run_curated.ps1` liest ihn aus `GPTScan/.env`; `sb/docker.py` reicht ihn in den Container und schwärzt ihn im Ergebnis. |
| `LLM_MODEL` | LLMSmartAudit | **ja** | `deepseek-v4-flash` (Fallstrick 2). |
| `LLM_PROVIDER` | LLMSmartAudit | nein | Default `deepseek`. |
| `LLM_CONTEXT_TOKENS` | LLMSmartAudit | nein | `65536`. Completion-Budget für unbekannte Modell-IDs; seit 24.09.2026 hebt es auch die Agentengrenze an (Ursache der 37 Kontextabbrüche), wenn das Image danach gebaut wurde. |
| `LLM_BASE_URL` | LLMSmartAudit | nein | nur bei `LLM_PROVIDER=custom`. |
| `GPTSCAN_PROVIDER` / `GPTSCAN_MODEL` | GPTScan | nein | Default `deepseek` / `deepseek-v4-flash`. |
| `GPTSCAN_DRY_RUN=1` | GPTScan | nein | kein API-Aufruf, keine Kosten, kein Schlüssel nötig. |
| `GPTSCAN_BASE_URL` | GPTScan | nein | nur bei `GPTSCAN_PROVIDER=custom`, etwa für den lokalen Prüfstand (Abschnitt 8). |

In den Container gelangt nur, was in der `env:`-Zeile der jeweiligen
`config.yaml` steht.

## 2. Bewährte Laufparameter

| Parameter | Wert | Grundlage |
|---|---|---|
| `--processes` | **4** | Bei rund 580 Aufrufen mit 3 Prozessen kein Rate-Limit; 4 ist die getestete Obergrenze. |
| `--timeout` GPTScan | **1800 s** | längster Task: 922 s (`32_LendingPair`). |
| `--timeout` LLMSmartAudit | **5400 s** | curated: Mittel 299 s, Median 264 s, Maximum 923 s; der Puffer fängt Retry-Schleifen ab. |
| Reihenfolge | **sequenziell** | erst GPTScan, dann LLMSmartAudit — weniger parallele Last auf demselben Schlüssel. |

Seit AP5 wirkt `--timeout` **im** Container, nicht nur als harter Abbruch von
außen (Abschnitt 8).

## 3. Kosten

| Werkzeug | Pro Contract | Kostenbremse |
|---|---|---|
| GPTScan | curated: Mittel $0,00007, Median $0 (127 von 143 ohne LLM-Aufruf); DeFi: Median $0,0013, Mittel $0,0029, Maximum $0,020 | **ja** — `MAX_COST_USD` in `GPTScan/src/config.py`, $0,50 je Contract; danach keine Aufrufe mehr, Vermerk `budget_exceeded` |
| LLMSmartAudit | Mittel ≈ $0,017, Median ≈ $0,012 (aus Token gerechnet), Mittel 299 s | **nein** |

Komplette Läufe zum Vergleich: curated GPTScan 3:19 min für ≈ $0,01, curated
LLMSmartAudit 3:02 h für ≈ $2,44, DeFi GPTScan 36:45 min für ≈ $0,28.

**Schätzung gegen Abbuchung.** Runner und `build_eval.py` rechnen mit festen
Sätzen (0,0908 bzw. 0,3695 USD je Million Prompt- bzw. Completion-Token, aus
`curated_v1_20260705` zurückgerechnet). Den Cache-Rabatt des Anbieters kennen
sie nicht und liegen deshalb zu hoch:

| Lauf | Schätzung | Abgebucht | Beleg |
|---|---:|---:|---|
| `curated_v1_20260705` LLMSmartAudit | 2,44 | 2,44 | Sätze aus diesem Lauf, kein unabhängiger Beleg |
| `llmsa_mwefixed_v2` (+ Nachlauf) | ≈ 8,37 | – | Kontostand damals nicht protokolliert |
| `llmsa_mwefixed_v2_ctx1m` | 11,42 | 5,55 | Kontostand 14,31 → 8,14 USD abzüglich 0,62 für zwei abgebrochene Läufe; Faktor 2,06 |

Die Sätze lassen wir bewusst so: Der Kostendeckel der Runner soll lieber zu früh
greifen als zu spät. Seit dem 24.09.2026 fragen alle Runner bei
`-Provider deepseek` den Kontostand vor und nach dem Lauf ab und protokollieren
die Differenz als „abgebucht“ — die zählt.

**Vor jedem Massenlauf ein Dry-Run:** `run_curated.ps1 -GptscanDry` kostet
nichts und findet Pipeline-Fehler, bevor Geld fließt. Für LLMSmartAudit gibt es
keinen Dry-Modus (Fallstrick 3).

## 4. Bekannte Fallstricke

**1 — GPTScan liefert bei bestimmten Pfaden still nichts.** Enthält der Pfad
`external`, `openzeppelin`, `uniswap`, `pancakeswap`, `legacy` oder `test`,
ist die Ausgabe leer. Der Entrypoint kopiert die Datei deshalb immer nach
`/work/input`.

**2 — `LLM_MODEL=deepseek-v4-flash` ist für LLMSmartAudit Pflicht.** Bis zum
24.09.2026 hatte das Image `deepseek-chat` eingebrannt; DeepSeek hat dieses
Modell am 24.07.2026 abgeschaltet. Ohne Override kam HTTP 400, und der Lauf
scheiterte erst nach dem vollen Retry-Budget. Seitdem trägt das Image kein
Modell mehr, und der Entrypoint bricht bei leerem `LLM_MODEL` sofort ab
(Exit 2, `error: LLM_MODEL not set`, kein LLM-Aufruf;
`tests/test_entrypoint_model_guard.py`). Gegen den Prüfstand nachgestellt
(Image `fe758cf6410c`): ohne Variable Exit 2 nach 15 s, mit Variable alle 41
Kategorien. Die Runner setzen die Variable immer, beim direkten `sb`-Aufruf
muss man sie selbst setzen.

**3 — LLMSmartAudit hat keinen Stub-Modus.** `LLM_MODEL=STUB` geht wörtlich an
die API und scheitert mit HTTP 400 (`results/llmsmartaudit/smoke1_stub`, heute
Test-Fixture). Ohne echte API — oder den Prüfstand aus Abschnitt 8 — lässt sich
das Werkzeug nicht testen.

**4 — GPTScan meldete Compile-Fehler nicht** (behoben 02.08.2026). Ein nicht
übersetzbarer Contract lief mit Exit 0 und `{"success": true, "results": []}`
durch ([`BA-ERRORS-VS-FAILS.md`](BA-ERRORS-VS-FAILS.md)). Bei neuen Läufen
prüfen:

```powershell
python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_<suffix>
```

**5 — `vul_before_static > vul_after_static` ist kein Fehler**, sondern GPTScans
gewollter False-Positive-Filter. Er greift bei etwa der Hälfte der Contracts
und erscheint als `info`.

**6 — LLMSmartAudit liefert keine Zeilennummern.** Deshalb werten wir auf
Contract-Ebene aus. Kein Bug.

**7 — `reparse` ohne `--sarif` löscht vorhandene SARIF-Dateien.** Unsere Läufe
sind mit `--json --sarif` erzeugt, also:

```powershell
cd smartbugs
.venv\Scripts\python.exe -m sb.reparse --sarif --processes 4 results
```

**8 — Defekte Samples im Altkorpus.**
`samples/gptscan/_chk/{20_Pool,23_nTokenAction,5_Pools,67_Vault}.sol` sind zu
einer Zeile kollabiert, `74_TimeswapPair.sol` hat einen solc-Fehler in Zeile
51. Ersatz: `samples/gptscan/mwevariety_fixed/`
([`BA-KORPUS-REPARATUR.md`](BA-KORPUS-REPARATUR.md)).

**9 — Im reparierten Korpus haken 2 von 96 Contracts.** `58_UniV3Vault`
bräuchte `--optimize` („Stack too deep“), `19_TransactionManager` verliert eine
Funktion an einen IR-Konvertierungsfehler. Beides ist im Ergebnis sichtbar.

**10 — Slither-Image und solc 0.7.6 bis 0.8.12 vertragen sich nicht.**
SmartBugs legt den passenden Compiler als `$BIN/solc` in den Container. Das
Image `smartbugs/slither:0.11.3` ist Alpine (musl), die Binaries 0.7.6 und
0.8.1 bis 0.8.12 sind gegen glibc gelinkt — Slither meldet
`No such file or directory: '/sb/bin/solc'`, obwohl die Datei da ist. In
`slither_mwefixed_v1` blieben so 45 von 96 Contracts ohne Ergebnis; curated
(Solidity 0.4) und GPTScan (Debian) sind nicht betroffen. **Lösung:**
`smartbugs/tools/slither-0.11.3-glibc/` mit glibc-Image (Abschnitt 5); damit
95 von 96. Der letzte (`58_UniV3Vault.sol`) ist ein Compilerfehler.

## 5. Images bauen

```powershell
docker build -t smartbugs/gptscan:1.0 .\GPTScan
# nur für den DeFi-Korpus nötig (Fallstrick 10)
docker build -t smartbugs/slither:0.11.3-glibc .\smartbugs\tools\slither-0.11.3-glibc
```

```bash
# LLMSmartAudit -- in Git Bash; git archive lässt das entfernte evaluation/ weg
git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main \
  | docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -
```

Kein Schlüssel landet im Image: `.dockerignore` schließt `.env` aus, der
Schlüssel kommt zur Laufzeit.

## 6. Stolpersteine unter Windows

* **Git-Bash-Pfadumwandlung.** MSYS macht aus führenden `/` Windows-Pfade
  (`!/foo/` → `!C:/Program Files/Git/foo/`). Bei Pfadmustern
  `MSYS_NO_PATHCONV=1` voranstellen.
* **PowerShell-Umleitung.** `> datei.csv` schreibt in PowerShell 5.1 je nach
  Sitzung UTF-16LE oder UTF-8 mit BOM; `compare_csv.py` bricht auf UTF-16 ab.
  Deshalb immer `... | Out-File -Encoding utf8 datei.csv`.
* **Pfadlänge.** `core.longpaths=true` muss man **pro Clone** setzen, sonst
  scheitern tiefe Pfade mit `Filename too long` (etwa ein `git worktree add`
  an `LLMSmartAuditTool-main/.../WareHouse/…`). Der längste getrackte Pfad hat
  129 Zeichen — in einem tief liegenden Clone reicht das schon.
* **PowerShell 5.1 kennt kein `&&`/`||`.** Stattdessen `A; if ($?) { B }`.

## 7. Einrichtung nach dem Klonen

Python-Umgebungen: README, „Umgebung anlegen“. Zwei Git-Einstellungen sind
lokal und werden nicht mitgeklont — direkt nach `git clone` setzen:

```powershell
git config core.longpaths true                   # sonst "Filename too long"
python analysis_tools\secret_scan.py --install    # setzt core.hooksPath auf .githooks
```

### Der pre-commit-Hook

`.githooks/pre-commit` ruft `analysis_tools/secret_scan.py` auf. Findet der
Scan in einer gestagten Datei einen Schlüssel, scheitert der Commit; gemeldet
werden Datei, Position und Muster, nie der Wert. `--install` setzt nur
`core.hooksPath` — so wirkt die versionierte Datei, und Änderungen am Hook
kommen bei allen per `git pull` an (ein Hook in `.git/hooks/` würde nur eine
Maschine schützen). Kontrolle: `git config --get core.hooksPath` muss
`.githooks` ausgeben.

### Was der Scan nicht sieht

Der Scan öffnet gzip-, tar- und zip-Inhalte (bis zu drei Ebenen tief). Dateien
über 20 MB durchsucht er nicht, meldet sie aber namentlich als „could NOT be
scanned“. Betroffen ist genau eine Datei,
`GPTScan/src/jars/SolidityStaticAnalysis-1.0-SNAPSHOT-standalone.jar`; eine
Prüfung mit angehobenem Limit fand dort nichts, dauert aber rund 10 s, deshalb
bleibt die Grenze.

## 8. Timeout und Prüfstand (AP5)

Hier stehen die Regeln; die Bedienung mit Beispielausgaben steht in
[`BA-WERKZEUG-BEDIENUNG.md`](BA-WERKZEUG-BEDIENUNG.md), Abschnitt 8.

**Ausgangslage.** Keines der Werkzeuge kennt einen Timeout für den ganzen Lauf
(GPTScan nur je LLM-Aufruf, LLMSmartAudit gar keinen). Ohne Gegenmaßnahme
schießt SmartBugs den Container von außen ab, und kein Teilergebnis bleibt
übrig. Seit AP5 rechnet der Entrypoint aus `TIMEOUT` drei Marken:

| Marke | Anteil | Wirkung |
|---|---|---|
| Bremse | 70 % | exportiert als `SB_DEADLINE_EPOCH`. Nur **GPTScan** liest sie: keine neuen LLM-Aufrufe, danach reguläres Auslaufen. LLMSmartAudit ignoriert sie; der Export hält nur beide Entrypoints gleich. |
| Netz | 90 % | `timeout` beendet den Prozess hart, Exit-Code wird auf **124** normalisiert. Bei LLMSmartAudit die einzige wirksame Stufe; danach birgt der Entrypoint den letzten Zwischenstand. |
| Rest | bis 100 % | Zwischenstand bergen, `sb_timeout` setzen, `/output.json` garantieren. |

`--timeout 0` schaltet alles ab; das Verhalten entspricht dann dem vor AP5.
Einzige Ausnahme: GPTScans `GPTSCAN_META` enthält immer die zwei Felder
`llm_calls_skipped_deadline` und `deadline_exceeded` — kein Parser stört sich
daran.

**Teilergebnis erkennen:**

* Feld `sb_timeout` im Report (`{"hit": true, "stage": "brake"|"net", …}`);
  fehlt es, war der Lauf vollständig.
* Eintrag `TIMEOUT_BRAKE` oder `TIMEOUT_NET` in `errors` — nie in `fails`.
* Bei LLMSmartAudit `categories_checked < categories_total`. `checked == 0`
  wird auch ohne Timeout als `errors` gemeldet, damit eine leere Liste nie als
  „sauber“ durchgeht.

**Prüfstand ohne API-Kosten.** Ein lokaler, OpenAI-kompatibler Endpunkt
antwortet absichtlich langsam und löst den Timeout-Pfad kostenlos und
reproduzierbar aus:

```powershell
python -m testing_tools.fake_llm_endpoint --port 8099 --delay 30
```

| Werkzeug | Umgebungsvariablen |
|---|---|
| GPTScan | `GPTSCAN_PROVIDER=custom`, `GPTSCAN_BASE_URL=http://host.docker.internal:8099` |
| LLMSmartAudit | `LLM_PROVIDER=custom`, `LLM_BASE_URL=http://host.docker.internal:8099` |

Der Provider `custom` hat bei beiden Werkzeugen Preis 0 — auch versehentlich
entstehen keine Kosten. Beide Variablenpaare stehen in der `env:`-Allowlist der
jeweiligen `config.yaml` (für GPTScan nachgezogen in Commit `a2611ea`).

**Was belegt ist.** 32 Tests, eine Vorprüfung des `timeout`-Kommandos in beiden
Images ([`BA-AP5-VORPRUEFUNG.md`](BA-AP5-VORPRUEFUNG.md)) und scharfe Läufe gegen
einen echten Endpunkt (Commit `43c3f32`,
[`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md), 4.5). Je ein
Contract pro Werkzeug zeigt, dass ein Teillauf nichts erfindet — nicht, wie viel
er im Mittel verpasst.
