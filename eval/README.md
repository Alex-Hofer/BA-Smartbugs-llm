# eval/ -- Auswertungen der aufgezeichneten Laeufe

Hier liegen ausschliesslich ABGELEITETE Daten. Die Rohergebnisse stehen unter
`smartbugs/results/<werkzeug>/<runid>/` und werden von den Skripten nur gelesen,
nie veraendert oder geloescht. Alt und Neu bleiben beide erhalten.

Diese Datei wird von `analysis_tools/gptscan_eval.py` fortgeschrieben; sie
fuehrt die GPTScan-Laeufe im Detail und die uebrigen Auswertungen als
Verweis. **Was jeder Ordner enthaelt, steht in seiner eigenen `README.md`.**

> **Die Rohergebnisse liegen nicht im Repository.** `smartbugs/.gitignore` schliesst
> `/results*` aus. Alle Pfade unter `smartbugs/results/` in diesem Ordner verweisen
> also auf lokale Artefakte der Maschine, auf der der Lauf stattfand; in einem
> frischen Clone existieren sie nicht. Was hier unter `eval/` liegt, ist damit die
> einzige versionierte Fassung der Ergebnisse. Zum Nachfahren eines Laufs:
> `.\run_full_v2.ps1 -Mode full -MainFallback` (Parameter und Commit stehen in
> `run_params.json`); bitgleiche Ergebnisse sind dabei nicht zu erwarten, siehe die
> Reproduzierbarkeitszahlen im Vergleichsdokument.

## Wie ein Ordner hier entsteht

1. `run_full_v2.ps1` faehrt den Lauf und legt `eval/<runid>/run_params.json` ab
   (Aufrufparameter, Versionen, SHA1 der Tool-Dateien, Git-Commit).
2. `analysis_tools/gptscan_eval.py <runid>` liest die Rohergebnisse und erzeugt
   `findings.jsonl`, `run_meta.json`, `summary.md` und den Vergleich gegen einen
   Altlauf.

Das SWC/DASP-Mapping wird nirgends hier dupliziert, sondern bei jedem Lauf aus
`smartbugs/tools/gptscan/findings.yaml` gelesen. 8 der 10 MWE-Regeln sind dort
bewusst als `BUSINESS-LOGIC (no SWC/DASP)` gefuehrt; nur MWE-205 (SWC-114/DASP-7)
und MWE-207 (DASP-2) haben ein redliches Gegenstueck. `dasp10` bleibt sonst leer.

## Laeufe

Kosten in Klammern sind SIMULIERT: im Dry-Run wird kein API-Call abgesetzt,
GPTScan schaetzt den Betrag nur. Gemessen an den Live-Laeufen ueberschaetzt
diese Schaetzung die tatsaechlichen Kosten um rund die Haelfte.

| Ordner | Rohergebnis | MAIN | Contracts | Findings | Kosten | Zweck |
|---|---|---|---:|---:|---:|---|
| `eval/gptscan_mwefixed_v2_dry/` | `smartbugs/results/gptscan/gptscan_mwefixed_v2_dry/` | ja | 96 | 5 | (0.3838) | Pipelinetest, 0 API-Calls |
| `eval/gptscan_mwefixed_v2_main/` | `smartbugs/results/gptscan/gptscan_mwefixed_v2_main/` | ja | 96 | 74 | $0.3638 | Volllauf (inkl. Nachlauf gptscan_mwefixed_v2_main_nomain) |
| `eval/gptscan_mwefixed_v2_smoke/` | `smartbugs/results/gptscan/gptscan_mwefixed_v2_smoke/` | ja | 3 | 0 | $0.0177 | Live-Stichprobe |
| `eval/gptscan_mwefixed_v2_smoke2/` | `smartbugs/results/gptscan/gptscan_mwefixed_v2_smoke2/` | ja | 3 | 6 | $0.0272 | Live-Stichprobe |

## Weitere Auswertungen in diesem Verzeichnis

Erzeugt von `analysis_tools/build_eval.py` (LLMSmartAudit-Laeufe) bzw.
`analysis_tools/curated_eval.py` (curated-Hauptlauf, alle drei Werkzeuge).
Sie tragen ein eigenes `run_meta.json`-Schema und stehen deshalb nicht in
der Tabelle oben.

| Ordner | Werkzeug | Contracts | Findings |
|---|---|---:|---:|
| [`eval/curated_v1_20260705__gptscan/`](curated_v1_20260705__gptscan/README.md) | gptscan | 143 | 6 |
| [`eval/curated_v1_20260705__llmsmartaudit/`](curated_v1_20260705__llmsmartaudit/README.md) | llmsmartaudit | 143 | 1124 |
| [`eval/curated_v1_20260705__slither-0.11.3/`](curated_v1_20260705__slither-0.11.3/README.md) | slither-0.11.3 | 143 | 2154 |
| [`eval/llmsa_curated_v2/`](llmsa_curated_v2/README.md) | llmsmartaudit | 143 | 1028 |
| [`eval/llmsa_mwefixed_v2/`](llmsa_mwefixed_v2/README.md) | llmsmartaudit | 96 | 437 |
| [`eval/llmsa_mwefixed_v2_ctx1m/`](llmsa_mwefixed_v2_ctx1m/README.md) | llmsmartaudit | 37 | 317 |

Dazu kommen `eval/per_contract/` (eine Zeile je Contract, `analysis_tools/per_contract_stats.py`) und `eval/_runlogs/` (Konsolenprotokolle der Massenlaeufe) -- beide mit eigener `README.md`.

## Verhaeltnis zu den Altlaeufen

Unter `smartbugs/results/gptscan/` liegen 17 aeltere Laeufe. Sie sind SAEMTLICH
ohne `--main` entstanden -- nachpruefbar am Docker-Entrypoint in der jeweiligen
`smartbugs.json`, der dort auf `'0'` endet. Der Volllauf mit `--main` ist der
erste seiner Art; der Vergleich Alt gegen Neu ist damit ein Vergleich
MAIN=0 gegen MAIN=1 auf demselben Korpus, Image und Modell.

Referenzlauf fuer den Vergleich ist `curated_mwefixed_live`
(96 Contracts, 77 Findings auf 40 Contracts, $0.2769).

## Zustaende

Nach `docs/BA-ERRORS-VS-FAILS.md`:

- **findings** -- Verdachtsfall ueber den Contract.
- **errors** -- das Werkzeug hat ein Problem bemerkt, abgefangen und weitergearbeitet.
- **fails** -- das Werkzeug wurde ausgehebelt, ein Ergebnis kam nicht zustande.
- **nicht uebersetzt** -- das Compilat ist gescheitert. GPTScan faengt das ab und
  endet trotzdem mit Exit-Code 0; der Parser markiert es als Info
  `analysis degraded`. Solche Contracts werden NIE als 'keine Findings' gezaehlt,
  ihr Ergebnis ist unbestimmt.
