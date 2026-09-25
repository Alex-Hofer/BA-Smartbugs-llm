# Laufregister: alle Läufe unter `smartbugs/results/`

Stand 25.09.2026, gezählt über die `smartbugs.json` jedes Task-Verzeichnisses.
Von den Rohergebnissen sind je Task `result.json` und `smartbugs.json`
versioniert, Logs und Archive liegen im Release-Zip (README, „Wo die
Ergebnisse liegen“); dieses Register sagt für jedes
Laufverzeichnis, wozu der Lauf diente und wo er ausgewertet ist. Läufe ohne
Ordner unter `eval/` erscheinen in `docs/errors-fails.md` (Zustände je Lauf)
und `docs/parser-audit-nachher.md` (Parser-Deckung), sonst nirgends.

Zwei Zählweisen kommen im Repository vor: **50 Laufverzeichnisse**, aber
**51 `runid`-Werte**, weil das Verzeichnis `gptscan/ap5_free_net` zwei Tasks mit
verschiedenem `runid`-Feld enthält (`ap5_free_gptscan_net`, `ap5_free_gptscan_net2`).
`docs/errors-fails.md` und `docs/parser-audit-nachher.md` zählen nach dem Feld
(51 Läufe); `eval/` und die übrigen Dokumente nennen den Verzeichnisnamen. Bei
26 Verzeichnissen weicht das Feld vom Verzeichnisnamen ab (`run_curated.ps1`
schreibt zum Beispiel `curated_gptscan_v1_20260705` in das Verzeichnis
`curated_v1_20260705`); die Spalte „Feld `runid`“ nennt den abweichenden Wert.

| Werkzeug | Verzeichnis | Feld `runid`, falls abweichend | Korpus | Tasks | Datum | Findings | Zweck | Auswertung |
|---|---|---|---|---:|---|---:|---|---|
| gptscan | `ap5_free_brake` | `ap5_free_gptscan_brake` | mwevariety_fixed | 2 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_free_net` | `ap5_free_gptscan_net2`, `ap5_free_gptscan_net` | mwevariety_fixed | 2 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_free_notimeout` | `ap5_free_gptscan_notimeout` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_live_full` | `ap5_live_gptscan_full` | mwevariety_fixed | 1 | 2026-08-18 | 2 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_live_partial` | `ap5_live_gptscan_partial` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_verify2_full` | `ap5_verify2_gptscan_full` | mwevariety_fixed | 1 | 2026-08-18 | 2 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_verify2_part` | `ap5_verify2_gptscan_part` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_verify_brake` | `ap5_verify_gptscan_brake` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_verify_net` | `ap5_verify_gptscan_net` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `ap5_verify_notimeout` | `ap5_verify_gptscan_notimeout` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| gptscan | `assign6_dry` |  | sonstiges: (9); smartbugs-curated(?basename) (1) | 10 | 2026-07-01 | 0 | Vorphase vor dem ersten Commit (Lehrveranstaltung; SmartBugs-Beispielcontracts unter `samples/0.4.x`) | keine; nur `docs/errors-fails.md`, Parser-Audit |
| gptscan | `assign6_dry_0_6_12` |  | sonstiges: (9); smartbugs-curated(?basename) (1) | 10 | 2026-07-01 | 0 | Vorphase vor dem ersten Commit (Lehrveranstaltung; SmartBugs-Beispielcontracts unter `samples/0.4.x`) | keine; nur `docs/errors-fails.md`, Parser-Audit |
| gptscan | `assign6_dry_0_8_24` |  | sonstiges: (9); smartbugs-curated(?basename) (1) | 10 | 2026-07-01 | 0 | Vorphase vor dem ersten Commit (Lehrveranstaltung; SmartBugs-Beispielcontracts unter `samples/0.4.x`) | keine; nur `docs/errors-fails.md`, Parser-Audit |
| gptscan | `assign6_live` |  | sonstiges: (9); smartbugs-curated(?basename) (1) | 10 | 2026-07-01 | 0 | Vorphase vor dem ersten Commit (Lehrveranstaltung; SmartBugs-Beispielcontracts unter `samples/0.4.x`) | keine; nur `docs/errors-fails.md`, Parser-Audit |
| gptscan | `assign6_live_0612` |  | sonstiges: (9); smartbugs-curated(?basename) (1) | 10 | 2026-07-01 | 0 | Vorphase vor dem ersten Commit (Lehrveranstaltung; SmartBugs-Beispielcontracts unter `samples/0.4.x`) | keine; nur `docs/errors-fails.md`, Parser-Audit |
| gptscan | `curated_demo_defi` | `curated_gptscan_demo_defi` | mwevariety_fixed(?basename) | 5 | 2026-08-02 | 21 | Demonstrationslauf vom 02./03.08.2026, Funktionsnachweis an fünf Contracts je Satz | `docs/BA-DEMOLAUF-ERGEBNIS.md` (ausdrücklich kein Messwert) |
| gptscan | `curated_demo_swc` | `curated_gptscan_demo_swc` | smartbugs-curated | 5 | 2026-08-02 | 0 | Demonstrationslauf vom 02./03.08.2026, Funktionsnachweis an fünf Contracts je Satz | `docs/BA-DEMOLAUF-ERGEBNIS.md` (ausdrücklich kein Messwert) |
| gptscan | `curated_mwe_20260706` | `curated_gptscan_mwe_20260706` | mwevariety | 96 | 2026-07-06 | 11 | GPTScan über den **unreparierten** Korpus `mwevariety`: 95 von 96 nicht übersetzbar, Anlass der Korpus-Reparatur | Prosa in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.3 und `docs/BA-KORPUS-REPARATUR.md` 1 |
| gptscan | `curated_mwefixed_dry` | `curated_gptscan_mwefixed_dry` | mwevariety_fixed | 96 | 2026-07-21 | 5 | Trockenlauf über den reparierten Korpus, unmittelbar vor dem Referenzlauf | keine; `docs/errors-fails.md` |
| gptscan | `curated_mwefixed_live` | `curated_gptscan_mwefixed_live` | mwevariety_fixed | 96 | 2026-07-21 | 77 | **Referenzlauf** GPTScan über `mwevariety_fixed` (ohne MAIN) | `eval/curated_mwefixed_live/`, `eval/per_contract/` |
| gptscan | `curated_v1_20260705` | `curated_gptscan_v1_20260705` | smartbugs-curated | 143 | 2026-07-05 | 6 | **Hauptlauf** über `smartbugs-curated` | `eval/curated_v1_20260705__gptscan/`, `eval/curated_v1_20260705__metriken.md`, `eval/per_contract/` |
| gptscan | `gptscan_mwefixed_v2_dry` |  | mwevariety_fixed | 96 | 2026-08-15 | 5 | Pipelinetest mit MAIN, 0 API-Aufrufe | `eval/gptscan_mwefixed_v2_dry/` |
| gptscan | `gptscan_mwefixed_v2_main` |  | mwevariety_fixed | 96 | 2026-08-15 | 73 | **Volllauf** GPTScan über `mwevariety_fixed` mit MAIN (AP6) | `eval/gptscan_mwefixed_v2_main/`, `eval/per_contract/` |
| gptscan | `gptscan_mwefixed_v2_main_nomain` |  | mwevariety_fixed | 3 | 2026-08-15 | 1 | Nachlauf ohne MAIN für die drei Contracts mit Exit 127 | eingemischt in `eval/gptscan_mwefixed_v2_main/` (`merged_runs`) |
| gptscan | `gptscan_mwefixed_v2_smoke` |  | mwevariety_fixed | 3 | 2026-08-15 | 0 | Live-Stichprobe vor dem Volllauf (Kostengate) | `eval/gptscan_mwefixed_v2_smoke/` |
| gptscan | `gptscan_mwefixed_v2_smoke2` |  | mwevariety_fixed | 3 | 2026-08-15 | 6 | zweite Live-Stichprobe, andere Contracts | `eval/gptscan_mwefixed_v2_smoke2/` |
| gptscan | `mwevar_dry` |  | mwevariety | 96 | 2026-07-01 | 0 | Trockenlauf über den unreparierten Korpus `mwevariety` (01.07.2026) | keine; `docs/errors-fails.md`, Parser-Audit |
| gptscan | `mwevar_live` |  | mwevariety_live | 27 | 2026-07-01 | 11 | Live-Lauf über 27 Contracts des unreparierten Korpus; zweiter Messpunkt für die 74-%-Reproduzierbarkeit | `docs/BA-GPTSCAN-VERGLEICH.md` 4; `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.3 |
| gptscan | `phase6_dry` |  | phase6 | 15 | 2026-07-01 | 0 | Vorphase: Trockenlauf über 15 Contracts (`samples/gptscan/phase6`) | keine; nur `docs/errors-fails.md`, Parser-Audit |
| gptscan | `phase6_live` |  | phase6 | 15 | 2026-07-01 | 6 | Vorphase: Live-Lauf über 15 Contracts; hier wurde der Silent Failure an `74_TimeswapPair.sol` reproduziert | `docs/BA-ARBEITSBERICHT-20260802.md`; `docs/errors-fails.md` |
| gptscan | `smoke1_dry` |  | mwevariety_fixed(?basename) (1); sonstiges:samples (2) | 3 | 2026-07-05 | 0 | Smoke-Test vor dem Hauptlauf vom 05.07.2026 (Phase 1/2 des Vorgehens) | `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 1 und 4.4; `docs/errors-fails.md` |
| gptscan | `smoke2_live` |  | mwevariety_fixed(?basename) (1); sonstiges:samples (2) | 3 | 2026-07-05 | 1 | Smoke-Test vor dem Hauptlauf vom 05.07.2026 (Phase 1/2 des Vorgehens) | `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 1 und 4.4; `docs/errors-fails.md` |
| llmsmartaudit | `ap5_free_net` | `ap5_free_llmsa_net` | mwevariety_fixed | 2 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| llmsmartaudit | `ap5_free_notimeout` | `ap5_free_llmsa_notimeout` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| llmsmartaudit | `ap5_live_full` | `ap5_live_llmsa_full` | mwevariety_fixed | 1 | 2026-08-18 | 9 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| llmsmartaudit | `ap5_live_partial` | `ap5_live_llmsa_partial` | mwevariety_fixed | 1 | 2026-08-18 | 5 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| llmsmartaudit | `ap5_verify_net` | `ap5_verify_llmsa_net` | mwevariety_fixed | 1 | 2026-08-18 | 0 | Nachweis AP5 (Timeout-Durchreichung): Bremse, Netz oder Vergleichslauf ohne Frist an ein bis zwei Contracts | Tabellen in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5 und `docs/BA-AP5-ABSCHLUSSBERICHT.md`; Zustände in `docs/errors-fails.md` |
| llmsmartaudit | `curated_demo_defi_llm` | `curated_llmsa_demo_defi_llm` | mwevariety_fixed(?basename) | 4 | 2026-08-03 | 38 | Demonstrationslauf vom 02./03.08.2026, Funktionsnachweis an fünf Contracts je Satz | `docs/BA-DEMOLAUF-ERGEBNIS.md` (ausdrücklich kein Messwert) |
| llmsmartaudit | `curated_demo_kostenprobe` | `curated_llmsa_demo_kostenprobe` | mwevariety_fixed(?basename) | 1 | 2026-08-02 | 11 | Kostenprobe an einem Contract vor dem Demonstrationslauf | `docs/BA-DEMOLAUF-ERGEBNIS.md` (ausdrücklich kein Messwert) |
| llmsmartaudit | `curated_demo_swc_llm` | `curated_llmsa_demo_swc_llm` | smartbugs-curated | 5 | 2026-08-03 | 33 | Demonstrationslauf vom 02./03.08.2026, Funktionsnachweis an fünf Contracts je Satz | `docs/BA-DEMOLAUF-ERGEBNIS.md` (ausdrücklich kein Messwert) |
| llmsmartaudit | `curated_v1_20260705` | `curated_llmsa_v1_20260705` | smartbugs-curated | 143 | 2026-07-05 bis 2026-07-06 | 1 124 | **Hauptlauf** über `smartbugs-curated` | `eval/curated_v1_20260705__llmsmartaudit/`, `eval/curated_v1_20260705__metriken.md`, `eval/per_contract/` |
| llmsmartaudit | `llmsa_mwefixed_v2` |  | mwevariety_fixed(?basename) | 96 | 2026-08-16 | 414 | **Volllauf** LLMSmartAudit über `mwevariety_fixed`; 37 Kontextabbrüche | `eval/llmsa_mwefixed_v2/`, `eval/per_contract/` |
| llmsmartaudit | `llmsa_mwefixed_v2_ctx1m` |  | mwevariety_fixed(?basename) | 37 | 2026-09-24 | 317 | Nachlauf über die 37 Kontext-Contracts mit `LLM_CONTEXT_TOKENS=1000000` | `eval/llmsa_mwefixed_v2_ctx1m/`, `eval/per_contract/` |
| llmsmartaudit | `llmsa_mwefixed_v2_retry` |  | mwevariety_fixed(?basename) | 4 | 2026-09-15 | 23 | Nachlauf über vier unentschiedene Contracts (15.09.2026) | eingemischt in `eval/llmsa_mwefixed_v2/` (`merged_runs`) |
| llmsmartaudit | `llmsa_smoke_curated` |  | smartbugs-curated | 3 | 2026-08-15 | 12 | Live-Stichprobe vor dem LLMSmartAudit-Volllauf | keine; `docs/errors-fails.md`, Parser-Audit (`eval/_runlogs/README.md`) |
| llmsmartaudit | `smoke1_stub` |  | sonstiges:samples | 1 | 2026-07-05 | 0 | Fehlversuch mit `LLM_MODEL=STUB`: LLMSmartAudit hat keinen Offline-Modus; dient heute als Test-Fixture | `docs/BA-BETRIEB.md`, Fallstrick 3; `docs/errors-fails.md` |
| llmsmartaudit | `smoke2_live` |  | mwevariety_fixed(?basename) (1); sonstiges:samples (2) | 3 | 2026-07-05 | 23 | Smoke-Test vor dem Hauptlauf vom 05.07.2026 (Phase 1/2 des Vorgehens) | `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 1 und 4.4; `docs/errors-fails.md` |
| slither-0.11.3 | `curated_v1_20260705` | `curated_slither_v1_20260705` | smartbugs-curated | 143 | 2026-07-06 | 2 154 | **Hauptlauf** über `smartbugs-curated` (statische Baseline) | `eval/curated_v1_20260705__slither-0.11.3/`, `eval/curated_v1_20260705__metriken.md`, `eval/per_contract/` |
| slither-0.11.3 | `slither_mwefixed_v1` |  | mwevariety_fixed(?basename) | 96 | 2026-09-24 | 4 319 | Slither über `mwevariety_fixed` mit dem Upstream-Image (Alpine): 45 Contracts ohne Ergebnis, Fallstrick 10 | `eval/per_contract/slither_mwefixed_v1__slither-0.11.3.csv`; `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.8 |
| slither-0.11.3-glibc | `slither_mwefixed_v2` |  | mwevariety_fixed(?basename) | 96 | 2026-09-24 | 7 096 | **Baseline** Slither über `mwevariety_fixed` im eigenen glibc-Image | `eval/slither_mwefixed_v2/`, `eval/per_contract/` |

Summe: 50 Laufverzeichnisse, 1 501 Tasks (jeder mit `result.json`).

Korpusnamen: `smartbugs-curated` (143 gelabelte Contracts), `mwevariety_fixed`
(96 reparierte DeFi-Contracts), `mwevariety` (der unreparierte Ausgangskorpus,
nicht mehr im Repository), `samples/0.4.x` und `samples/gptscan/phase6`
(Beispielcontracts der Vorphase). Bei `mwevar_live` ist es eine Teilmenge von
27 Contracts aus `mwevariety`.

Nicht in diesem Register, weil außerhalb von `smartbugs/results/` oder ohne
Rohdaten: `llmsa_curated_v2` (Rohdaten verloren, nur `eval/llmsa_curated_v2/`),
der abgebrochene erste Anlauf von `llmsa_mwefixed_v2_ctx1m` und der abgebrochene
Lauf `llmsa_mwefixed_v2_main37` (beide nur im Protokoll,
`eval/_runlogs/README.md`).
