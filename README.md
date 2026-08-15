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
als austauschbare Werkzeuge im selben Rahmen. Die Integration der beiden
KI-Scanner in SmartBugs (Parser, Konfiguration, Findings-Mapping,
Entrypoint-Skripte) ist Teil dieser Arbeit — siehe
[`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md).

Datensatz ist [smartbugs-curated](https://github.com/smartbugs/smartbugs-curated)
(143 gelabelte Contracts, DASP-Top-10-Kategorien). Ergänzend ein aus Web3Bugs
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
│   ├── parser_audit.py         prüft, dass kein Rohsignal im Parser verlorengeht
│   ├── errors_fails_report.py  Errors/Fails je Lauf, als CSV und Markdown
│   ├── compare_csv.py          Vorher/Nachher-Vergleich zweier results2csv-Exporte
│   ├── redact_results.py       entfernt API-Schlüssel aus alten Task-Logs
│   ├── secret_scan.py          Leak-Vorsorge, auch als pre-commit-Hook
│   └── rawlog.py               Rohmaterial lesen, rich-Logs entzerren
├── corpus_tools/       Rekonstruktion des mwevariety-Korpus
├── docs/               Ausarbeitungen, Protokolle, Berichte  (Einstieg unten)
├── tests/              pytest-Regressionstests beider Parser + Fixtures
├── smartbugs/          SmartBugs 2.1.1 (fremd) …
│   ├── sb/docker.py            … mit einem gekennzeichneten Patch
│   ├── tools/gptscan/          Tool-Integration (eigener Code)
│   ├── tools/llmsmartaudit/    Tool-Integration (eigener Code)
│   ├── samples/                Testkorpora, u. a. gptscan/mwevariety_fixed/
│   └── results/                Messdaten — git-ignoriert, siehe unten
├── GPTScan/                    GPTScan (fremd, AGPL-3.0) mit Änderungen
├── LLMSmartAuditTool-main/     LLMSmartAudit (fremd, Apache-2.0) mit Änderungen
├── run_curated.ps1             Massenlauf-Runner
├── evaluate_curated.py         Recall/Precision/F1 gegen die Ground Truth
└── LICENSE                     MIT für den Eigenanteil; Fremdlizenzen separat
```

### Wo die Ergebnisse liegen

`smartbugs/results/` — **19 abgeschlossene Läufe, 930 Tasks, 4.461 Dateien,
258 MB. Bewusst nicht im Git** (`smartbugs/.gitignore` schließt `results*` aus).
Die Läufe sind ohne neue, kostenpflichtige LLM-Aufrufe nicht reproduzierbar.

| Werkzeug | Läufe | Tasks |
|---|---:|---:|
| `gptscan` | 15 | 640 |
| `llmsmartaudit` | 3 | 147 |
| `slither-0.11.3` | 1 | 143 |

Der Hauptlauf über den curated-Datensatz heißt in allen drei Fällen
`curated_v1_20260705`. Die aggregierten Auswertungen sind versioniert:

* [`docs/errors-fails.md`](docs/errors-fails.md) — Errors/Fails je Lauf, mit Wortlaut
* [`docs/parser-audit-nachher.md`](docs/parser-audit-nachher.md) — Vollständigkeitsnachweis der Parser
* [`docs/parser-fix-vorher-nachher.md`](docs/parser-fix-vorher-nachher.md) — Auswirkung der Parser-Reparatur

---

## Voraussetzungen

* **Windows 11 mit PowerShell** — die Skripte sind darauf ausgelegt. Git Bash
  wird nur zum Bauen des LLMSmartAudit-Images gebraucht.
* **Docker Desktop**, laufend.
* **Python 3.10+** für SmartBugs (venv unter `smartbugs/.venv`), Python 3.11+
  für die Werkzeuge in `analysis_tools/` und die Tests.
* **Beide Images lokal gebaut** — sie liegen auf keinem Registry.
* **solc**: SmartBugs lädt passende Compiler selbst und legt sie unter
  `~/.smartbugs/solc` ab. Für GPTScan reicht SmartBugs den passenden Compiler
  als `$BIN/solc` in den Container.

### Images bauen

```powershell
docker build -t smartbugs/gptscan:1.0 .\GPTScan
```

```bash
# Git Bash, nicht PowerShell. git archive liefert den Baum ohne evaluation/.
git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main \
  | docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -
```

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

In kein Image gelangt je ein Schlüssel: `.dockerignore` schließt `.env` aus.

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
> Werkzeug hat **keine** Kostenbremse. Ein Volllauf dauert dort 3,5–4,5 Stunden.

## Auswerten

```powershell
# Recall / Precision / F1 je DASP-Kategorie
smartbugs\.venv\Scripts\python.exe evaluate_curated.py --suffix v1_20260705 --csv

# Rohdaten als CSV
cd smartbugs
.venv\Scripts\python.exe -m sb.results2csv results > ..\curated_results.csv
cd ..

# Errors und Fails getrennt, mit Wortlaut
python analysis_tools\errors_fails_report.py --md docs\errors-fails.md --csv docs\errors-fails.csv

# Nachweis, dass kein Rohsignal im Parser verlorengeht
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

41 Regressionstests für beide Tool-Parser. Die Fixtures sind unveränderte
Rohdaten echter Läufe; ihre Herkunft steht in `tests/fixtures/MANIFEST.json`.
Fälle, die in den 19 Läufen nie auftraten (Timeout, leeres Archiv, kaputtes
JSON), sind synthetisch und tragen `synthetic` im Testnamen.

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
dadurch von 5,13 GB auf 590 MB, und das Repository bleibt handhabbar (Pack
66 MB statt 461,50 MiB). Das Verzeichnis enthält die Evaluationsdaten der
ursprünglichen Veröffentlichung und wird für diese Arbeit nicht gebraucht — die
eigenen Messungen liegen unter `smartbugs/results/`.
**Extern gesichert** unter
`…\BACHELORARBEIT\BA-history-backup-20260802.git` (vollständiger Mirror der
alten Historie inklusive `evaluation/`) sowie
`…\BACHELORARBEIT\BA-ausgelagert-20260802\`.

**2 — Ein Patch in `smartbugs/sb/docker.py`.**
SmartBugs reicht keine Umgebungsvariablen in Tool-Container durch. Ohne diesen
Patch gäbe es keinen Weg, den API-Schlüssel zur Laufzeit zu übergeben, außer ihn
ins Image zu backen. Der Patch reicht eine Allowlist durch und redigiert die
Werte anschließend im Task-Log. Beide Stellen sind im Quelltext kommentiert.

Alle weiteren Änderungen an Fremdcode — 7 Dateien in GPTScan, 9 in
LLMSmartAuditTool — sind mit *was* und *warum* in
[`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md) aufgeführt, gegen die
Upstream-Stände per Hash abgeglichen.

---

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [`docs/BA-BETRIEB.md`](docs/BA-BETRIEB.md) | Validierte Parameter, Pflichtvariablen, Kosten, 9 bekannte Fallstricke |
| [`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md) | Eigenanteil und jede Änderung an Fremdcode, mit Begründung |
| [`docs/BA-ERRORS-VS-FAILS.md`](docs/BA-ERRORS-VS-FAILS.md) | Herleitung der errors/fails-Semantik aus `smartbugs/sb/parse_utils.py` |
| [`docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`](docs/BA-DURCHFUEHRUNGSPROTOKOLL.md) | Protokoll der Durchführung |
| `docs/BA-KORPUS-REPARATUR.tex` | Rekonstruktion des mwevariety-Korpus |
| `docs/BA-GPTSCAN-VERGLEICH.tex` | GPTScan im Vergleich |
| `GPTScan/docs/SMARTBUGS_INTEGRATION.md` | Wie GPTScan als SmartBugs-Werkzeug verpackt ist |
| `corpus_tools/README.md` | Werkzeuge der Korpus-Reparatur |

Die PDF-Fassungen der Ausarbeitungen liegen neben ihren `.tex`-Quellen in
`docs/`.

## Lizenz

Der Eigenanteil steht unter der **MIT-Lizenz** (siehe [`LICENSE`](LICENSE)).

Die mitgelieferten Fremdkomponenten behalten ihre eigenen Lizenzen. Zu beachten:
**GPTScan steht unter AGPL-3.0** (Copyleft), und dieser Baum enthält Änderungen
am GPTScan-Quellcode. Eine Veröffentlichung des Repositorys müsste die
AGPL-3.0-Bedingungen für diesen Teil erfüllen. Die vollständige Aufstellung
steht in [`LICENSE`](LICENSE) und [`docs/BA-EIGENANTEIL.md`](docs/BA-EIGENANTEIL.md).
