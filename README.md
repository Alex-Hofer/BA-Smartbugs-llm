# Benchmark dreier Smart-Contract-Scanner unter SmartBugs

Begleitrepository zur Bachelorarbeit. Untersucht wird, was zwei
LLM-gestützte Analysewerkzeuge auf einem etablierten Benchmark leisten — gemessen
gegen einen klassischen statischen Analysator als Referenz.

| Werkzeug | Art | Rolle | Upstream |
|---|---|---|---|
| **GPTScan** | LLM + leichte Programmanalyse | Prüfling; 10 MWE-Regeln für DeFi-Logik | [GPTScan/GPTScan](https://github.com/GPTScan/GPTScan) |
| **LLMSmartAudit** | LLM-Multi-Agenten-Pipeline (ChatDev/CAMEL) | Prüfling; 41 Detektor-Prompts | [LLMAudit/LLMSmartAuditTool](https://github.com/LLMAudit/LLMSmartAuditTool) |
| **Slither 0.11.3** | statische Analyse | statische Baseline | [crytic/slither](https://github.com/crytic/slither) |

Alle drei laufen unter [SmartBugs 2.1.1](https://github.com/smartbugs/smartbugs)
(Upstream-Commit `7ddaf6c`) als austauschbare Werkzeuge im selben Rahmen. Die Integration der beiden
KI-Scanner in SmartBugs (Parser, Konfiguration, Findings-Mapping,
Entrypoint-Skripte) ist Teil dieser Arbeit — siehe
[`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md).

Datensatz ist [smartbugs-curated](https://github.com/smartbugs/smartbugs-curated)
(143 gelabelte Contracts, DASP-Top-10-Kategorien), Stand `230e649`
(16.06.2024); `run_curated.ps1` klont und pinnt genau diesen Stand. Ergänzend ein aus Web3Bugs
rekonstruierter DeFi-Korpus mit 96 Contracts für GPTScans eigentliches
Einsatzgebiet.

Zur Wortwahl: Ein Werkzeug meldet **Findings** — Verdachtsfälle, keine
festgestellten Fehler. Was ein Finding von einem `error` und einem `fail`
unterscheidet, ist in
[`docs/BA-ERRORS-VS-FAILS.md`](docs/BA-ERRORS-VS-FAILS.md) aus dem
SmartBugs-Code hergeleitet.

---

## Aufbau des Repositorys

```
├── .githooks/          versionierter pre-commit-Hook (Secret-Scan)
├── analysis_tools/     Auswertungswerkzeuge (eigener Code)
│   ├── parser_audit.py         prüft, ob Rohsignal im Parser verlorengeht
│   ├── errors_fails_report.py  Errors/Fails je Lauf, als CSV und Markdown
│   ├── gptscan_eval.py         Auswertung eines GPTScan-Laufs nach eval/<runid>/
│   ├── gptscan_run_stats.py    Token-, Kosten- und Laufzeitkennzahlen eines GPTScan-Laufs
│   ├── build_eval.py           Auswertung eines LLMSmartAudit-Laufs nach eval/<runid>/
│   ├── curated_eval.py         curated-Hauptlauf, alle drei Werkzeuge, nach eval/<runid>__<tool>/
│   ├── per_contract_stats.py   eine Zeile je Contract nach eval/per_contract/
│   ├── compare_csv.py          Vorher/Nachher-Vergleich zweier results2csv-Exporte
│   ├── redact_results.py       entfernt API-Schlüssel aus alten Task-Logs
│   ├── secret_scan.py          Leak-Vorsorge, auch als pre-commit-Hook
│   └── rawlog.py               Rohmaterial lesen, rich-Logs entzerren
├── corpus_tools/       Rekonstruktion des mwevariety-Korpus
├── docs/               Ausarbeitungen, Protokolle, Berichte  (Einstieg unten)
├── eval/               versionierte, abgeleitete Auswertungen je Lauf
├── testing_tools/      lokaler LLM-Prüfstand für kostenlose Tests
├── tests/              pytest-Regressionstests + Fixtures aus echten Läufen
├── smartbugs/          SmartBugs 2.1.1 (fremd) …
│   ├── sb/                     … mit gekennzeichneten Eingriffen (BA MODIFICATION)
│   ├── tools/gptscan/          Tool-Integration (eigener Code)
│   ├── tools/llmsmartaudit/    Tool-Integration (eigener Code)
│   ├── tools/slither-0.11.3-glibc/  Slither im glibc-Image (Kopie des Upstream-Werkzeugs mit eigenem Dockerfile)
│   ├── samples/                Testkorpora, u. a. gptscan/mwevariety_fixed/
│   └── results/                Messdaten — git-ignoriert, siehe unten
├── GPTScan/                    GPTScan (fremd, AGPL-3.0) mit Änderungen
├── LLMSmartAuditTool-main/     LLMSmartAudit (fremd, Apache-2.0) mit Änderungen
├── run_curated.ps1             Massenlauf-Runner (curated, beide Werkzeuge)
├── run_full_v2.ps1             GPTScan-Volllauf über mwevariety_fixed, mit MAIN
├── run_full_v2_llmsa.ps1       LLMSmartAudit-Volllauf über beide Korpora
├── run_retry_llmsa.ps1         Nachlauf einzelner LLMSmartAudit-Contracts
├── evaluate_curated.py         Recall/Precision/F1 gegen die Ground Truth
└── LICENSE                     MIT für den Eigenanteil; Fremdlizenzen separat
```

### Wo die Ergebnisse liegen

`smartbugs/results/` — **bewusst nicht im Git** (`smartbugs/.gitignore` schließt
`results*` aus). Die Läufe sind ohne neue, kostenpflichtige LLM-Aufrufe nicht
reproduzierbar.

**Stand 24.09.2026: 51 Läufe, 1 501 Tasks, 7 494 Dateien, 2,68 GB** (2,50 GiB).
Gezählt nach der `runid` aus jeder `smartbugs.json`, wie sie
`analysis_tools/errors_fails_report.py` ausliest:

| Werkzeug | Läufe | Tasks |
|---|---:|---:|
| `gptscan` | 33 | 863 |
| `llmsmartaudit` | 15 | 303 |
| `slither-0.11.3` | 2 | 239 |
| `slither-0.11.3-glibc` | 1 | 96 |

Der Hauptlauf über den curated-Datensatz heißt in allen drei Fällen
`curated_v1_20260705` (143 Tasks je Werkzeug). Dazu kommen der GPTScan-Volllauf
mit MAIN über `mwevariety_fixed` (15.08.2026), die LLMSmartAudit-Volläufe über
beide Korpora (15./16.08.2026, Nachlauf 15.09.2026), die Prüfläufe zum
Timeout (17./18.08.2026), Slither über `mwevariety_fixed` (24.09.2026;
`slither_mwefixed_v1` mit dem Upstream-Image erreichte 51 von 96 Contracts,
Ursache in `docs/BA-BETRIEB.md`, Fallstrick 10; `slither_mwefixed_v2` mit dem
eigenen glibc-Image 95 von 96) und der LLMSmartAudit-Nachlauf über die
37 Kontext-Contracts mit angehobener Grenze (24.09.2026,
`llmsa_mwefixed_v2_ctx1m`; 37 von 37 analysiert, Auswertung in
`eval/llmsa_mwefixed_v2_ctx1m/`).

> Ein Lauf fehlt: `llmsa_curated_v2` wurde auf dem Rechner des Co-Autors
> gefahren, und seine Rohergebnisse existieren seit dem 24.09.2026 nirgends
> mehr. Die Auswertung unter `eval/llmsa_curated_v2/` ist die einzige erhaltene
> Fassung; ein Reparse ist nicht mehr möglich. Für LLMSmartAudit auf
> `smartbugs-curated` ist ohnehin `curated_v1_20260705` der Bezugslauf, der mit
> allen Rohdaten vorliegt. Einzelheiten in
> [`eval/_runlogs/README.md`](eval/_runlogs/README.md).

Die aggregierten Auswertungen sind versioniert:

* [`eval/curated_v1_20260705__metriken.md`](eval/curated_v1_20260705__metriken.md) — Recall/Precision/F1 je DASP-Kategorie für alle drei Werkzeuge
* [`eval/`](eval/README.md) — je Lauf ein Ordner mit `findings.jsonl`, `run_meta.json`, `summary.md` und einer `README.md`, die sagt, was man daraus schließen darf und was nicht
* [`eval/per_contract/`](eval/per_contract/README.md) — eine Zeile je Contract für acht Läufe, als Auswertungshilfe mit dokumentierten Einschränkungen
* [`docs/errors-fails.md`](docs/errors-fails.md) — Errors/Fails je Lauf, mit Wortlaut
* [`docs/parser-audit-nachher.md`](docs/parser-audit-nachher.md) — Lückenbericht der Parser über alle Läufe
* [`docs/parser-fix-vorher-nachher.md`](docs/parser-fix-vorher-nachher.md) — Auswirkung der Parser-Reparatur

### Die beiden CSVs im Wurzelverzeichnis

`curated_results.csv` und `evaluation_curated_v1_20260705.csv` liegen im
Wurzelverzeichnis und sind **bewusst nicht versioniert** (`.gitignore`,
Zeilen 13–14). Beide sind reine Zwischenstände, die sich jederzeit ohne einen
API-Aufruf neu erzeugen lassen, solange die Rohergebnisse vorliegen:

| Datei | Was drinsteht | Wie sie entsteht |
|---|---|---|
| `curated_results.csv` | Rohexport aller Findings aller Läufe, eine Zeile je Finding | `python -m sb.results2csv results` aus `smartbugs/` |
| `evaluation_curated_v1_20260705.csv` | eine Zeile je Contract und Werkzeug: Label, erkannt ja/nein, Findingzahl, getroffene Kategorien | `evaluate_curated.py --suffix v1_20260705 --csv` |

Kein Skript und kein Dokument verlangt sie an dieser Stelle — sie werden nur
geschrieben, nie gelesen. Wer die Zahlen versioniert braucht, nimmt
`eval/curated_v1_20260705__metriken.md` und die `findings.jsonl` der
`eval/`-Ordner; dort stehen dieselben Angaben, aber mit Herkunft und
Einschränkungen dokumentiert.

---

## Voraussetzungen

* **Windows 11 mit PowerShell** — die Skripte sind darauf ausgelegt. Git Bash
  wird nur zum Bauen des LLMSmartAudit-Images gebraucht.
* **Docker Desktop**, laufend.
* **Python 3.10+** für SmartBugs (venv unter `smartbugs/.venv`), Python 3.11+
  für die Werkzeuge in `analysis_tools/` und die Tests.
* **Die beiden KI-Images lokal gebaut** — sie liegen auf keinem Registry.
  Für den DeFi-Korpus zusätzlich das glibc-Slither-Image (siehe „Die vier Images“).
* **solc**: SmartBugs lädt passende Compiler selbst und legt sie unter
  `~/.smartbugs/solc` ab. Für GPTScan reicht SmartBugs den passenden Compiler
  als `$BIN/solc` in den Container.

### Umgebung anlegen

```powershell
cd smartbugs
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .        # SmartBugs 2.1.1 samt Docker-SDK und PyYAML
cd ..
python -m pip install -r requirements-dev.txt       # PyYAML und pytest für analysis_tools\, tests\, evaluate_curated.py
```

Die venv gehört nach `smartbugs\.venv`; alle vier Runner erwarten sie dort.
Welche Abhängigkeiten SmartBugs zieht, steht in `smartbugs\pyproject.toml`
(eine `uv.lock` gibt es seit dem 24.09.2026 nicht mehr; die frühere war leer). Die
Werkzeuge in `analysis_tools\` und die Tests laufen mit dem System-Python;
`evaluate_curated.py` läuft unter beiden Interpretern.

---

## Docker: was im Container läuft und was nicht

SmartBugs ist ein **Container-Orchestrator**, kein Container. Der Unterschied
entscheidet darüber, was man installiert haben muss.

| Läuft auf dem Host | Läuft im Container |
|---|---|
| SmartBugs selbst (`python -m sb`, venv unter `smartbugs/.venv`) | je Task genau ein Werkzeug-Container |
| die vier Runner-Skripte (`run_*.ps1`) | |
| alles unter `analysis_tools/` und `corpus_tools/` | |
| `evaluate_curated.py` | |
| die 258 pytest-Tests — **kein Docker nötig**, die Fixtures sind aufgezeichnete Rohdaten | |

SmartBugs startet für **jeden einzelnen Contract** einen frischen Container,
hängt ein temporäres Verzeichnis als `/sb` hinein, überschreibt den Entrypoint
mit `tools/<werkzeug>/scripts/do_solidity.sh` und holt danach `/output.json`
heraus. Deshalb gibt es **kein `docker-compose`**: Es gäbe nichts zu
komponieren — keine langlebigen Dienste, kein Netz zwischen Containern, keine
feste Anzahl. Die Parallelität steuert `--processes`, nicht Compose.

### Die vier Images

| Werkzeug | Image | Herkunft | Netz |
|---|---|---|---|
| GPTScan | `smartbugs/gptscan:1.0` | **lokal bauen** (`GPTScan/Dockerfile`) | `bridge` |
| LLMSmartAudit | `smartbugs/llmsmartaudit:1.0` | **lokal bauen** (`LLMSmartAuditTool-main/LLMSmartAuditTool-main/Dockerfile.smartbugs`) | `bridge` |
| Slither 0.11.3 | `smartbugs/slither:0.11.3` | Registry (Docker Hub) — SmartBugs zieht es beim ersten Lauf selbst, `sb/docker.py:77` | `none` |
| Slither 0.11.3, glibc | `smartbugs/slither:0.11.3-glibc` | **lokal bauen** (`smartbugs/tools/slither-0.11.3-glibc/Dockerfile`); nur für den DeFi-Korpus nötig, `docs/BA-BETRIEB.md` Fallstrick 10 | `none` |

Die beiden KI-Images müssen lokal gebaut werden, weil sie auf keinem Registry
liegen: Sie enthalten den **für diese Arbeit geänderten** Fremdcode (siehe
[`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md)), und ein Upload wäre bei
GPTScan zusätzlich eine AGPL-3.0-Weitergabe. Slither dagegen ist unverändert und
kommt fertig; das vierte Image ändert daran nichts, es tauscht nur die
Linux-Basis (Debian statt Alpine) und installiert dieselbe Version mit
`pip install slither-analyzer==0.11.3`.

> Am 21.09.2026 nachgeprüft, nicht bloß behauptet: Unter `/opt/gptscan/src/`
> im Image liegen alle sieben geänderten Dateien — `tasks.py`, `config.py`,
> `chatgpt_api.py`, `analyze_pipeline.py`, `rich_utils.py` — sowie die beiden
> eigenen, `llm_backend.py` und `report_md.py`, jede **byte-identisch** zum
> Stand in diesem Repository. Das Image trägt also tatsächlich modifizierten
> AGPL-3.0-Code; seine Weitergabe löste die Copyleft-Pflichten aus. Zugleich
> belegt der Abgleich, dass das Image zum Repo-Stand passt, aus dem die
> Messungen stammen.

Beide KI-Werkzeuge brauchen `network: bridge`, um die LLM-API zu erreichen;
SmartBugs isoliert Tool-Container sonst mit `network: none`. Slither bleibt
isoliert — es telefoniert nirgendwohin.

### Images bauen

```powershell
docker build -t smartbugs/gptscan:1.0 .\GPTScan
```

```bash
# Git Bash, nicht PowerShell. git archive liefert den Baum ohne evaluation/;
# der Tag muss exakt so lauten, wie tools/llmsmartaudit/config.yaml ihn erwartet.
git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main \
  | docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -
```

```powershell
# Slither im glibc-Image, nur für den DeFi-Korpus nötig
docker build -t smartbugs/slither:0.11.3-glibc .\smartbugs\tools\slither-0.11.3-glibc
```

Alle drei Befehle sind gegen die Dockerfiles geprüft: Build-Kontext, Pfad des
Dockerfiles und Tag stimmen mit dem überein, was die `config.yaml` des jeweiligen
Werkzeugs als `image:` verlangt. Der zweite Befehl umgeht bewusst den
Arbeitsbaum — ein `docker build .` in diesem Verzeichnis scheitert unter Windows
an den Langpfaden des Tool-Baums.

Gemessene Größen: `smartbugs/gptscan:1.0` 2,14 GB (Neubau 18.08.2026,
`docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` Abschnitt 4.5), `smartbugs/llmsmartaudit:1.0`
**587 MB** (Neubau 24.09.2026 aus dem Repo-Stand mit einstellbarer Kontextgrenze
und Modell-Wächter, ID `fe758cf6410c`; davor 20.09.2026 mit gleicher Größe),
`smartbugs/slither:0.11.3-glibc` **316 MB** (Bau 24.09.2026, ID `a7a63792a158`).

Am 21.09.2026 gegengeprüft — `docker images` bestätigte damals beide Werte
und beide Baudaten; das LLMSmartAudit-Image wurde am 24.09.2026 zweimal neu
gebaut (Kontextgrenze über `LLM_CONTEXT_TOKENS`, dann Modell-Wächter):

```
smartbugs/llmsmartaudit:1.0   587MB    2026-09-24   fe758cf6410c
smartbugs/gptscan:1.0         2.14GB   2026-08-18   de5ae99da7e7
smartbugs/slither:0.11.3-glibc 316MB   2026-09-24   a7a63792a158
smartbugs/slither:0.11.3      490MB    Docker Hub   475f5b72c25d
```

Beim selben Termin geprüft: Beide Images enthalten **keine `.env`-Datei** und
**kein Schlüsselmuster** (Export des Dateisystems, 31 337 bzw. 9 900 Einträge;
die vier Treffer auf `sk-…` stammen sämtlich aus der SPDX-Lizenzliste
`packaging/licenses/_spdx.py`, wo `asterisk-linking-protocols-exception`
steht). Im LLMSmartAudit-Image liegt **kein** `evaluation/`-Verzeichnis — der
benutzte Tag trägt also die verkleinerte Fassung, nicht das 5,13-GB-Original.
Eingebrannt war bis zum 24.09.2026 nur `LLM_MODEL=deepseek-chat`; seit dem
Neubau vom 24.09.2026 trägt das Image kein Modell mehr, und der Entrypoint
bricht ohne `LLM_MODEL` ab (siehe unten).

### API-Schlüssel setzen

Der Schlüssel steht **ausschließlich** in `GPTScan/.env` — git-ignoriert und
niemals committet. `GPTScan/.env.example` dokumentiert die Variablennamen mit
leeren Werten.

```
DEEPSEEK_API_KEY=sk-...
```

`run_curated.ps1` liest die Datei, setzt die Variable in die Prozessumgebung und
entfernt sie am Ende wieder. Der gepatchte `smartbugs/sb/docker.py` reicht sie
in den Container durch und **redigiert sie unmittelbar danach**, bevor die
Docker-Argumente ins Task-Log geschrieben werden — sonst stünde der Schlüssel im
Klartext in jeder `results/**/smartbugs.json`.

Stehen in der `.env` mehrere Schlüssel, entfernen die Runner vor dem Start
diejenigen wieder aus der Prozessumgebung, die der gewählte Anbieter nicht
braucht. In den Container gelangt so nur der Schlüssel des aktiven Anbieters.

In kein Image gelangt je ein Schlüssel: `.dockerignore` schließt `.env` aus.

---

## Modell wählen und wechseln

**Anbieter und Modell werden zur Laufzeit gewählt. Eine Code-Änderung ist dafür
nicht nötig** — weder an den Werkzeugen noch an SmartBugs. Möglich wird das
durch das Feld `env:` in den beiden `config.yaml`, das der gepatchte
`sb/docker.py` als Allowlist in den Container durchreicht. Nur Variablen, die
auf dem Host gesetzt sind, kommen an; nichts steckt im Image.

Die vier Runner-Skripte nehmen die Wahl als Parameter entgegen — `-Provider`,
`-Model`, `-BaseUrl` und bei LLMSmartAudit zusätzlich `-ContextTokens` und
`-MaxCompletionTokens` — und setzen daraus die Umgebungsvariablen.
`-ContextTokens` hob die Agentengrenze bei Provider `deepseek` bis zum
24.09.2026 nicht an; seitdem tut es das, sofern das Image nach diesem Datum
gebaut wurde (siehe die Tabelle der Variablen unten). Wer eine
Einstellung **dauerhaft** will, trägt sie stattdessen in `GPTScan\.env` ein;
welche der beiden Angaben gewinnt, klärt der nächste Abschnitt. Wer ohne
Runner arbeitet, setzt die Variablen selbst (letztes Beispiel unten).

### Drei Wege, dasselbe einzustellen — und welcher gewinnt

Anbieter und Modell lassen sich an drei Stellen festlegen. Es gilt eine feste
Rangfolge, **von oben nach unten**:

| Rang | Wo | Gilt für |
|---|---|---|
| **1** | Parameter am Runner: `-Provider`, `-Model`, … | genau diesen einen Lauf |
| **2** | Eintrag in `GPTScan\.env` | jeden Lauf, bis man ihn ändert |
| **3** | eingebauter Standard (`deepseek` / `deepseek-v4-flash`) | wenn sonst nichts gesetzt ist |

Ein ausdrücklich übergebener Parameter schlägt also immer die `.env`, und die
`.env` schlägt den Standard. Was tatsächlich gegriffen hat, steht in jedem
Lauflog:

```
Aus ...\GPTScan\.env uebernommen: Model=deepseek-v4-pro (ein ausdruecklicher Parameter haette Vorrang).
Backend: provider=deepseek, GPTScan-Modell=deepseek-v4-pro, LLMSA-Modell=deepseek-v4-pro
```

> **Bis zum 21.09.2026 war das anders**, und der Unterschied war teuer: Die
> Runner überschrieben jeden `.env`-Eintrag mit ihrem eigenen Standardwert. Wer
> dort `GPTSCAN_MODEL=deepseek-v4-pro` eintrug, bekam stillschweigend
> `deepseek-v4-flash` — zu merken erst an den Kostenzahlen. Seither wird ein
> `.env`-Eintrag übernommen, sofern der Parameter nicht ausdrücklich übergeben
> wurde, und die Übernahme wird protokolliert.

**Beide Schlüssel dürfen gleichzeitig in der `.env` stehen.** Welcher gebraucht
wird, ergibt sich aus dem Anbieter; der jeweils andere bleibt unbenutzt. Fehlt
der gebrauchte, bricht der Runner ab, **bevor** ein Container startet.

### Dauerhaft umstellen: das Modell in die `.env` schreiben

In `GPTScan\.env` eintragen — der Schlüssel bleibt, zwei Zeilen kommen dazu:

```
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...

GPTSCAN_MODEL=deepseek-v4-pro
LLM_MODEL=deepseek-v4-pro
```

Danach genügt der Aufruf ohne Parameter:

```powershell
.\run_curated.ps1                      # nimmt deepseek-v4-pro aus der .env
```

Und für einen einzelnen Lauf wieder zurück auf das günstige Modell, ohne die
Datei anzufassen:

```powershell
.\run_curated.ps1 -Model deepseek-v4-flash    # Parameter schlaegt .env
```

Verfügbare Modelle (aus `GPTScan/src/config.py`, `PROVIDERS`):

| Anbieter | günstig (Standard) | stark |
|---|---|---|
| `deepseek` | `deepseek-v4-flash` | `deepseek-v4-pro` |
| `openai` | `gpt-3.5-turbo` | `gpt-4` |

Welche `.env`-Namen die Runner auswerten: `GPTSCAN_PROVIDER`, `GPTSCAN_MODEL`,
`GPTSCAN_BASE_URL` für GPTScan; `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`,
`LLM_CONTEXT_TOKENS`, `LLM_MAX_COMPLETION_TOKENS` für LLMSmartAudit. In
`run_curated.ps1`, das beide Werkzeuge steuert, gilt `-Provider` für beide —
stehen `GPTSCAN_PROVIDER` und `LLM_PROVIDER` dort auf **verschiedenen** Werten,
bricht der Runner mit einer Meldung ab, statt sich einen auszusuchen.

| Variable | Werkzeug | Standard | Wo sie gelesen wird |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | beide | — (**Pflicht** bei Provider `deepseek`) | `GPTScan/src/config.py`; bei LLMSmartAudit über `run.py` → `camel/model_backend.py` |
| `OPENAI_API_KEY` | beide | — | dieselben Stellen, bei Provider `openai` |
| `GPTSCAN_PROVIDER` | GPTScan | `deepseek` | `scripts/do_solidity.sh` → `--provider`; `src/llm_backend.py:active_provider` |
| `GPTSCAN_MODEL` | GPTScan | „cheap"-Tier des Anbieters (`deepseek-v4-flash`) | `scripts/do_solidity.sh` → `--model`; `src/llm_backend.py:model_override` |
| `GPTSCAN_DRY_RUN` | GPTScan | `0` | `scripts/do_solidity.sh` → `--dry-run`; `src/llm_backend.py:is_dry_run` |
| `GPTSCAN_BASE_URL` | GPTScan | — | `src/llm_backend.py:base_url` — **nur** bei `GPTSCAN_PROVIDER=custom` |
| `GPTSCAN_API_KEY` | GPTScan | — | `src/config.py`, Schlüssel des Providers `custom` |
| `LLM_PROVIDER` | LLMSmartAudit | `deepseek` | `scripts/do_solidity.sh` → `--provider`; `chatdev/chat_chain.py` |
| `LLM_MODEL` | LLMSmartAudit | `deepseek-v4-flash` aus dem Runner — **muss gesetzt sein**, siehe unten | `scripts/do_solidity.sh` → `--model` → `run.py` setzt `LLM_MODEL_ID` → `camel/model_backend.py` |
| `LLM_BASE_URL` | LLMSmartAudit | Provider-Standard | `scripts/do_solidity.sh` exportiert als `BASE_URL`; `camel/model_backend.py:_resolve_endpoint` |
| `LLM_CONTEXT_TOKENS` | LLMSmartAudit | `16384`; für Provider `deepseek` `65536` | `camel/model_backend.py:_context_limit` für das Completion-Budget bei Modell-IDs ohne Eintrag in `num_max_token_map`; `camel/utils.py:get_model_token_limit` für die Agentengrenze (`max_tokens_exceeded_by_camel`). Für Provider `deepseek` las `camel/utils.py` bis zum 24.09.2026 fest 65 536, unabhängig von dieser Variablen; alle aufgezeichneten Läufe liefen mit dieser festen Grenze. Seitdem hebt die Variable auch sie an (Image neu bauen) |
| `LLM_MAX_COMPLETION_TOKENS` | LLMSmartAudit | keine zusätzliche Grenze | `camel/model_backend.py:_cap_completion_tokens` |

Jede Variable ist mit Zweck, Standardwert und Folgen des Fehlens in
[`GPTScan/.env.example`](GPTScan/.env.example) kommentiert.

### `LLM_MODEL=deepseek-v4-flash` ist Pflicht

Bis zum 24.09.2026 trug das LLMSmartAudit-Image `ENV LLM_MODEL=deepseek-chat`
eingebrannt (`Dockerfile.smartbugs`), und `run.py` hat denselben Standardwert.
Dieses Modell ist seit 24.07.2026 abgeschaltet, und der Name geht **verbatim**
an die DeepSeek-API: Ohne die Host-Variable scheiterte jeder Lauf mit HTTP 400,
aber erst nach dem Retry-Budget des Werkzeugs, Stunden später und ohne Report —
hergeleitet in
[`docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`](docs/BA-DURCHFUEHRUNGSPROTOKOLL.md),
Fehler #1. Seit dem 24.09.2026 ist kein Modell mehr eingebrannt, und der
Entrypoint `smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh` bricht bei
leerem `LLM_MODEL` sofort ab: Platzhalterreport mit `error: LLM_MODEL not set`,
Exit-Code 2, in der `result.json` als `errors` (`EXIT_CODE_2`, `checked 0 of
41`), kein LLM-Aufruf. Ein stiller Rückfall auf ein Standardmodell wäre der
schlechtere Fehler, weil er das Backend für den Benutzer wählt; wer einen
Standard will, setzt ihn in der `.env`.

**Über die Runner ist das erledigt:** Sie setzen `LLM_MODEL` bei jedem Lauf —
aus dem Parameter, aus der `.env` oder aus ihrem Standardwert, in dieser
Reihenfolge. Aufpassen muss nur, wer SmartBugs **ohne** Runner aufruft (letzter
Abschnitt dieses Kapitels) — dort ist die Variable von Hand zu setzen; fehlt
sie, endet der Task nach Sekunden mit dem Fehler statt nach Stunden.

### Beispiel 1 — anderes Modell beim selben Anbieter

```powershell
.\run_curated.ps1 -Model deepseek-v4-pro -RunIdSuffix v4pro
```

Der `-Model`-Wert wandert unverändert als `--model` bis in den API-Aufruf. Ein
Modell ohne Eintrag in der Preistabelle erscheint mit dem konservativen
Fallback-Preis in der Kostenschätzung (`GPTScan/src/config.py`). Brauchen die
beiden Werkzeuge verschiedene Modelle, gibt es zusätzlich `-GptscanModel` und
`-LlmModel`.

### Beispiel 2 — anderer Anbieter

```powershell
# OPENAI_API_KEY muss in GPTScan\.env stehen
.\run_curated.ps1 -Provider openai -Model gpt-4o -RunIdSuffix openai
```

Welcher Schlüssel gebraucht wird, ergibt sich aus dem Anbieter; fehlt er, bricht
der Runner ab, bevor ein Container startet. Ein **unbekannter** Anbietername
wird schon bei der Parameterprüfung abgelehnt — und auch im Werkzeug selbst
führt er zum Abbruch statt zu einem stillen Rückfall auf den Standard: Ein
Fallback würde ein anderes Backend abrechnen, und der Fehler fiele erst in den
Kostenzahlen auf (`GPTScan/src/llm_backend.py:active_provider`).

### Beispiel 3 — Test ohne Kosten gegen den lokalen Prüfstand

```powershell
.\run_curated.ps1 -Tool gptscan -Provider custom -Model custom-cheap `
    -BaseUrl 'http://host.docker.internal:8000/v1' -SkipClone `
    -FilePattern 'samples:gptscan/Vault.sol' -RunIdSuffix pruefstand
```

`testing_tools/fake_llm_endpoint.py` ist eine OpenAI-kompatible Attrappe mit
einstellbarer Antwortverzögerung. Die Umleitung ist absichtlich auf den Provider
`custom` beschränkt — ein bezahltes Backend darf sich nicht per
Umgebungsvariable umlenken lassen.

### Ohne Runner, direkt über SmartBugs

```powershell
cd smartbugs
$env:DEEPSEEK_API_KEY = '<Schlüssel>'
$env:GPTSCAN_PROVIDER = 'deepseek'
$env:GPTSCAN_MODEL    = 'deepseek-v4-pro'
.venv\Scripts\python.exe -m sb -t gptscan -f samples:gptscan/Vault.sol `
    --timeout 1800 --runid modelltest_pro
```

> **Vergleichbarkeit.** Alle aufgezeichneten Läufe dieser Arbeit sind mit
> `deepseek` / `deepseek-v4-flash` entstanden — das sind auch die Standardwerte
> der Runner. Ein Lauf mit anderem Backend ist mit ihnen **nicht** vergleichbar;
> dafür immer einen eigenen `-RunIdSuffix` bzw. `-RunId` vergeben, damit die
> Ergebnisordner getrennt bleiben.

---

## Einen Lauf reproduzieren

```powershell
# Pipeline-Test ohne Kosten und ohne API-Aufruf (dringend empfohlen)
.\run_curated.ps1 -Tool gptscan -GptscanDry -SkipClone -FilePattern 'samples:gptscan/Vault.sol'

# Volllauf beide Werkzeuge über die 143 curated-Contracts
.\run_curated.ps1

# Nur ein Werkzeug
.\run_curated.ps1 -Tool gptscan
```

Das Skript prüft die Voraussetzungen, klont den Datensatz bei Bedarf, führt die
Läufe **sequenziell** aus, schreibt Compile-Failure- und
Review-Kandidaten-Manifeste und gibt am Ende die Errors/Fails-Bilanz aus.

> **Kosten und Pflichtvariablen** stehen in
> [`docs/BA-BETRIEB.md`](docs/BA-BETRIEB.md). Wichtigster Punkt:
> `LLM_MODEL=deepseek-v4-flash` ist für LLMSmartAudit **Pflicht**, und das
> Werkzeug hat **keine** Kostenbremse. Gemessen dauerte der curated-Volllauf
> `curated_v1_20260705` 3:02 h bei vier parallelen Prozessen, `llmsa_curated_v2`
> 10:42 h bei drei.

## Auswerten

```powershell
# Recall / Precision / F1 je DASP-Kategorie, auf der Konsole
smartbugs\.venv\Scripts\python.exe evaluate_curated.py --suffix v1_20260705 `
    --tools gptscan llmsmartaudit slither-0.11.3 --csv

# Dieselben Zahlen versioniert ablegen: eval/curated_v1_20260705__<werkzeug>/
# und eval/curated_v1_20260705__metriken.md
python analysis_tools\curated_eval.py

# Rohdaten als CSV
cd smartbugs
.venv\Scripts\python.exe -m sb.results2csv results > ..\curated_results.csv
cd ..

# Errors und Fails getrennt, mit Wortlaut
python analysis_tools\errors_fails_report.py --md docs\errors-fails.md --csv docs\errors-fails.csv

# Prüfen, ob Rohsignal im Parser verlorengeht
python analysis_tools\parser_audit.py
```

Nach einer Parser-Änderung lassen sich alle Altläufe neu auswerten, ohne einen
einzigen API-Aufruf:

```powershell
cd smartbugs
.venv\Scripts\python.exe -m sb.reparse --sarif --processes 4 results
```

Das `--sarif` ist nicht optional: `reparse` löscht vorhandene SARIF-Dateien und
schreibt sie nur mit diesem Schalter neu.

## Tests

```powershell
python -m pytest tests -q
```

258 Tests (Stand 24.09.2026): Regressionstests für beide Tool-Parser, das
Aufräumen der Container, das Timeout-Verhalten (AP5), den `MAIN`-Parameter
(AP6), den lokalen LLM-Prüfstand und die Auswertungsskripte `build_eval.py`,
`per_contract_stats.py`, `curated_eval.py` und `parser_audit.py`. Sie brauchen **kein Docker**:
Die Fixtures sind unveränderte Rohdaten echter Läufe, ihre Herkunft steht in
`tests/fixtures/MANIFEST.json`. Fälle, die in den aufgezeichneten Läufen nie
auftraten (Timeout, leeres Archiv, kaputtes JSON), sind synthetisch und tragen
`synthetic` im Testnamen.

Dieselbe Suite und der Secret-Scan laufen bei jedem Push auf `main` und bei
jedem Pull Request als GitHub-Actions-Workflow
([`.github/workflows/tests.yml`](.github/workflows/tests.yml), Ubuntu,
Python 3.12; am 24.09.2026 in einem Linux-Container nachvollzogen).

## Secret-Scan

```powershell
python analysis_tools\secret_scan.py            # gestagte Dateien (Hook-Modus)
python analysis_tools\secret_scan.py --all      # gesamter Arbeitsbaum
python analysis_tools\secret_scan.py --install  # Hook aktivieren (einmal pro Clone)
```

Findet der Scan einen Schlüssel, endet er mit Exit-Code 1 und der Commit
scheitert. Der Wert selbst wird nie ausgegeben.

Der Hook ist versioniert: `.githooks/pre-commit` liegt im Repo, `--install`
setzt nur `core.hooksPath` darauf. Ein nach `.git/hooks/` kopierter Hook würde
nicht mitgeklont und schützte damit nur eine Maschine. **Nach dem Klonen einmal
ausführen** — zusammen mit `git config core.longpaths true`; beides steht in
[`docs/BA-BETRIEB.md`](docs/BA-BETRIEB.md), Abschnitt 7.

Komprimierte Dateien und Archive (`.gz`, `.tar`, `.zip`) werden entpackt und
mitdurchsucht. Was der Scan nicht lesen kann — zu groß, defektes Archiv — meldet
er namentlich, statt es stillschweigend zu überspringen.

---

## Zwei Eingriffe in den Fremdcode, die erklärt gehören

**1 — `evaluation/` wurde aus `LLMSmartAuditTool-main` entfernt.**
27.662 Dateien, 3,7 GB. Zur Laufzeit nirgends referenziert: der Entrypoint
startet `run.py --config SmartContractTA` aus `/app`. Das Docker-Image schrumpft
dadurch von 5,13 GB auf 587 MB, und das Repository bleibt handhabbar (Pack
66 MB statt 461,50 MiB). Das Verzeichnis enthält die Evaluationsdaten der
ursprünglichen Veröffentlichung und wird für diese Arbeit nicht gebraucht — die
eigenen Messungen liegen unter `smartbugs/results/`.
**Extern gesichert** unter
`…\BACHELORARBEIT\BA-history-backup-20260802.git` (vollständiger Mirror der
alten Historie inklusive `evaluation/`) sowie
`…\BACHELORARBEIT\BA-ausgelagert-20260802\`.

**2 — Die Eingriffe in `smartbugs/sb/`.**
SmartBugs reicht keine Umgebungsvariablen in Tool-Container durch. Ohne Eingriff
gäbe es keinen Weg, den API-Schlüssel zur Laufzeit zu übergeben, außer ihn ins
Image zu backen. `sb/tools.py` nimmt deshalb das Feld `env` auf, `sb/docker.py`
reicht die Allowlist durch und redigiert die Werte anschließend im Task-Log.
Die eigenen Eingriffe in `smartbugs/sb/` beschränken sich auf genau diese
beiden Dateien — sieben Blöcke, im Quelltext als `BA MODIFICATION`
gekennzeichnet und in [`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md)
begründet; als zwei Pull Requests an `smartbugs/smartbugs` vorbereitet
(ebendort, Abschnitt 2.5). Alle übrigen Dateien unter `smartbugs/sb/` sind byte-identisch zum
Upstream-Stand `7ddaf6c`; nachprüfbar mit einem `diff -r` gegen einen frischen
Klon (Befehl ebendort).

Alle weiteren Änderungen an Fremdcode — 7 Dateien in GPTScan, 9 in
LLMSmartAuditTool — sind mit *was* und *warum* in
[`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md) aufgeführt, gegen die
Upstream-Stände per Hash abgeglichen.

---

## Dokumentation

**Lebende Dokumente** (werden nachgeführt):

| Dokument | Inhalt |
|---|---|
| [`docs/BA-WERKZEUGE-IM-VERGLEICH.md`](docs/BA-WERKZEUGE-IM-VERGLEICH.md) | Architektur der drei Werkzeuge und ihre Gegenüberstellung anhand der Messdaten |
| [`docs/BA-BETRIEB.md`](docs/BA-BETRIEB.md) | Validierte Parameter, Pflichtvariablen, Kosten, 10 bekannte Fallstricke |
| [`docs/BA-WERKZEUG-BEDIENUNG.md`](docs/BA-WERKZEUG-BEDIENUNG.md) | Bedienung der beiden KI-Scanner Schritt für Schritt, Ist-Zustand |
| [`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md) | Eigenanteil und jede Änderung an Fremdcode, mit Begründung |
| [`docs/BA-ERRORS-VS-FAILS.md`](docs/BA-ERRORS-VS-FAILS.md) | Herleitung der errors/fails-Semantik aus `smartbugs/sb/parse_utils.py` |
| [`docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`](docs/BA-DURCHFUEHRUNGSPROTOKOLL.md) | Protokoll der Durchführung mit datierten Nachträgen |
| [`docs/BA-WERKZEUGKETTE.md`](docs/BA-WERKZEUGKETTE.md) | Die Werkzeugkette und die Timeout-Mechanik als Mermaid-Diagramme, mit Exportweg für den Fließtext |
| [`docs/BA-BETREUERGESPRAECH-AUFGABEN.md`](docs/BA-BETREUERGESPRAECH-AUFGABEN.md) | Arbeitspakete AP1–AP8 aus dem Betreuergespräch |
| [`docs/BA-PARSER-AUDIT-LUECKEN.md`](docs/BA-PARSER-AUDIT-LUECKEN.md) | Ein Ausnahme-Defekt im Zusammenspiel von SmartBugs und LLMSmartAudit: Fund, Ursache, Behebung |
| [`docs/BA-KORPUS-REPARATUR.md`](docs/BA-KORPUS-REPARATUR.md) | Rekonstruktion des mwevariety-Korpus |
| [`docs/BA-GPTSCAN-VERGLEICH.md`](docs/BA-GPTSCAN-VERGLEICH.md) | GPTScan auf curated gegen GPTScan auf seiner Zieldomäne |
| [`eval/README.md`](eval/README.md) | Wie die Auswertungen unter `eval/` entstehen |
| [`GPTScan/docs/SMARTBUGS_INTEGRATION.md`](GPTScan/docs/SMARTBUGS_INTEGRATION.md) | Wie GPTScan als SmartBugs-Werkzeug verpackt ist |
| [`corpus_tools/README.md`](corpus_tools/README.md) | Werkzeuge der Korpus-Reparatur |

**Datierte Berichte** (Stand bleibt, spätere Änderungen stehen als Nachtrag oder in den lebenden Dokumenten):

| Dokument | Inhalt |
|---|---|
| [`docs/BA-VERIFIKATIONSBERICHT-20260924.md`](docs/BA-VERIFIKATIONSBERICHT-20260924.md) | Zweitprüfung des Repositorys, Stand 24.09.2026: Befunde, Korrekturen mit Commit, neue Messungen |
| [`docs/BA-VERIFIKATIONSBERICHT.md`](docs/BA-VERIFIKATIONSBERICHT.md) | Überprüfung des Repositorys, Stand 02.08.2026, mit Nachtrag vom 24.09.2026 |
| [`docs/BA-TESTLAUF-AUSWERTUNG.md`](docs/BA-TESTLAUF-AUSWERTUNG.md) | Auswertung der v2-Läufe über `mwevariety_fixed`, Stand 18.08.2026 vor dem Nachlauf; aktuelle Zahlen in `BA-WERKZEUGE-IM-VERGLEICH.md` 4.2 |
| [`docs/BA-AP5-ABSCHLUSSBERICHT.md`](docs/BA-AP5-ABSCHLUSSBERICHT.md) | AP5: Timeout ins Werkzeug durchreichen, Stand 18.08.2026; Vorprüfung, Entwurf und Plan liegen daneben (`BA-AP5-*.md`) |
| [`docs/BA-AUFGABEN-UND-STATUS.md`](docs/BA-AUFGABEN-UND-STATUS.md) | Aufgaben und Status vom 02.08.2026, mit Nachtrag vom 21.09.2026 |
| [`docs/BA-ARBEITSBERICHT-20260802.md`](docs/BA-ARBEITSBERICHT-20260802.md) | Arbeitsbericht vom 02.08.2026 |
| [`docs/BA-DEMOLAUF-ERGEBNIS.md`](docs/BA-DEMOLAUF-ERGEBNIS.md) | Demonstrationslauf beider KI-Scanner vom 02.08.2026 |
| [`docs/Update_Bericht.md`](docs/Update_Bericht.md) | Zwischenbericht zum Arbeitsstand vom 03.08.2026 |
| [`docs/BA-Kontext-Stand-Juli-2026.md`](docs/BA-Kontext-Stand-Juli-2026.md) | Kontextpapier zum Projektstand Juli 2026 |

Dokumentation und Auswertungen liegen ausschließlich als `.md`, `.json` und
`.csv` vor. Die früheren `.tex`-, `.pdf`- und `.pptx`-Fassungen wurden nach
Markdown überführt und aus dem Repository entfernt.

## Lizenz

Der Eigenanteil steht unter der **MIT-Lizenz** (siehe [`LICENSE`](LICENSE)).

Die mitgelieferten Fremdkomponenten behalten ihre eigenen Lizenzen. Zu beachten:
**GPTScan steht unter AGPL-3.0** (Copyleft), und dieser Baum enthält Änderungen
am GPTScan-Quellcode. Eine Veröffentlichung des Repositorys müsste die
AGPL-3.0-Bedingungen für diesen Teil erfüllen. Die vollständige Aufstellung
steht in [`LICENSE`](LICENSE) und [`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md).
