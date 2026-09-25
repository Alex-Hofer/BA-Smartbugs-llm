# eval/curated_mwefixed_live/ — GPTScan über `mwevariety_fixed`, der Referenzlauf

Der erste GPTScan-Lauf über den reparierten DeFi-Korpus, gefahren am
21.07.2026 direkt nach der Korpus-Reparatur. Er ist der **Referenzlauf** aller
GPTScan-Vergleiche: Gegen ihn misst `eval/gptscan_mwefixed_v2_main/` die
Reproduzierbarkeit (75,3 % der Findings wiedergefunden), und seine 77 Findings
sind die Zahl, die `docs/BA-WERKZEUGE-IM-VERGLEICH.md` (4.2 und 5),
`docs/BA-GPTSCAN-VERGLEICH.md` und `docs/BA-KORPUS-REPARATUR.md` (9) für
GPTScan auf seiner Zieldomäne nennen.

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `curated_mwefixed_live` |
| Werkzeug | GPTScan, Image `smartbugs/gptscan:1.0` |
| Modell | `deepseek/deepseek-v4-flash` |
| Korpus | `smartbugs/samples/gptscan/mwevariety_fixed/`, 96 DeFi-Contracts |
| Parameter | `--timeout 1800`, MAIN nicht gesetzt (`'0'` im Entrypoint); Prozesszahl nicht protokolliert, der Lauf liegt vor der Einführung von `run_params.json` |
| Durchführung | 21.07.2026, 12:39 bis 13:12 Uhr (36,7 min Wanduhr, 8 217,2 s Container-Zeit) |
| Rohergebnisse | `smartbugs/results/gptscan/curated_mwefixed_live/` (git-ignoriert) |
| Trockenlauf davor | `curated_mwefixed_dry` (96 Contracts, 0 API-Aufrufe, nur in `docs/errors-fails.md`) |

## Wie die Dateien entstanden sind

```powershell
python analysis_tools\gptscan_eval.py curated_mwefixed_live --no-compare
```

Erzeugt am 25.09.2026 aus den Rohergebnissen; das Skript liest nur und setzt
keinen API-Aufruf ab. `--no-compare`, weil dieser Lauf selbst die Referenz
ist, gegen die die übrigen GPTScan-Ordner verglichen werden. Ohne
`run_params.json` leitet das Skript die Laufparameter aus den
`smartbugs.json` der Tasks ab und kennzeichnet das im Feld
`run_parameters.source`.

## Was in den Dateien steht

| Datei | Inhalt |
|---|---|
| `findings.jsonl` | eine Zeile je Finding: Contract, MWE-Regel, Funktion, Zeilen, Severity, Begründung, Empfehlung |
| `run_meta.json` | Zustände, Token, Kosten, Laufzeiten, Fehlerliste |
| `summary.md` | dieselben Zahlen als Tabellen |

Spaltenbedeutung wie in den übrigen GPTScan-Ordnern: `mwe` und `gptscan_code`
sind die Regelkennung; `dasp10` und `swc` bleiben leer, wo
`smartbugs/tools/gptscan/findings.yaml` die Regel als `BUSINESS-LOGIC (no
SWC/DASP)` führt (8 der 10 Regeln).

## Kernzahlen

| | |
|---|---:|
| Contracts | 96 |
| Findings | 77 auf 40 Contracts, aus 8 der 10 Regeln |
| LLM-Aufrufe | 1 614 |
| Token | 668 808 prompt / 654 392 completion |
| Kosten (GPTScans eigene Schätzung) | $0,2769 |
| Tasks mit `errors` | 36 (37,5 %) |
| Tasks mit `fails` | 0 |
| nicht übersetzt (degraded) | 1 (`58_UniV3Vault.sol`, solc `Stack too deep` ohne `--optimize`) |
| ohne Findings, sauber | 55 |

Je Contract mit Zustand, Stufenzahlen des Vorfilters und Kosten:
`eval/per_contract/curated_mwefixed_live__gptscan.csv`; Aggregation der
Stufen in `corpus_tools/curated_mwefixed_live.analysis.json`
(`corpus_tools/analyze_run.py`).

## Was man daraus schließen darf

* Was GPTScan auf seiner Zieldomäne meldet, wenn der Korpus kompiliert: welche
  Regeln anschlagen, auf welchen Contracts, zu welchen Kosten.
* Dass die statische Bestätigungsstufe auf diesem Korpus aktiv war: Alle 77
  Findings haben sie passiert (`vul_after_static` in der per_contract-CSV).

## Was man daraus nicht schließen darf

1. **Keine Ground Truth.** `mwevariety_fixed` hat keinen annotierten
   Referenzstand; Recall und Precision lassen sich nicht bilden. Ob die 77
   Findings zutreffen, ist nur an Stichproben geprüft
   (`docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.3, `docs/BA-KORPUS-REPARATUR.md` 9).
2. **Die Errorquote von 37,5 % ist kein Scheitern.** Größter Einzelposten ist
   `Static analysis failed: Invalid args`: GPTScans statische Stufe stürzt auf
   einem Teil der übersetzbaren Contracts ab; die Findings dieser Contracts
   entstehen ohne den Präzisionsschutz. Die Ursache ist nicht untersucht
   (`docs/BA-WERKZEUGE-IM-VERGLEICH.md` 4.3).
3. **Ein Lauf ist keine Verteilung.** Der Wiederholungslauf mit MAIN fand
   75,3 % dieser Findings wieder; die Differenz vermischt MAIN-Effekt und
   Nicht-Determinismus (`eval/gptscan_mwefixed_v2_main/README.md`).
4. **Die Kosten sind GPTScans eigene Schätzung** aus `GPTSCAN_META`, nicht die
   Abrechnung des Anbieters.
5. **Die Rohergebnisse liegen nicht im Repository.** Was hier liegt, ist die
   einzige versionierte Fassung der Einzel-Findings dieses Laufs.
