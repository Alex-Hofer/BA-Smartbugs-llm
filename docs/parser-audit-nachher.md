# Lueckenbericht Parser-Audit

Geprueft: **1272 Task-Verzeichnisse** aus 48 Laeufen, **2289 extrahierte Rohmeldungen**, davon **0** im Parser-Output nicht wiederauffindbar.

**Laufbestand dieses Berichts:** 48 Laeufe, 1272 Tasks, erzeugt am 21.09.2026. Ein Bericht ueber einen anderen Laufbestand ist damit nicht unmittelbar vergleichbar.

Erzeugt mit `python analysis_tools/parser_audit.py`. Das Werkzeug liest das
Container-Rohmaterial (`result.log`, `result.tar`, `smartbugs.json`, Exit-Code)
mit eigenen Detektoren und prueft, ob jede gefundene Meldung in `result.json`
wieder auftaucht. Nicht als Fehler gewertet werden bewusst: das normale
Static-Filtering von GPTScan (`vul_before_static > vul_after_static`), reine
solc-Warnungen und slithers Exit-Code 255.

## Uebersicht je Lauf

| Tool | Lauf | Tasks | Rohmeldungen | Luecken |
|---|---|---:|---:|---:|
| gptscan | ap5_free_gptscan_brake | 2 | 40 | 0 |
| gptscan | ap5_free_gptscan_net | 1 | 0 | 0 |
| gptscan | ap5_free_gptscan_net2 | 1 | 3 | 0 |
| gptscan | ap5_free_gptscan_notimeout | 1 | 0 | 0 |
| gptscan | ap5_live_gptscan_full | 1 | 0 | 0 |
| gptscan | ap5_live_gptscan_partial | 1 | 5 | 0 |
| gptscan | ap5_verify2_gptscan_full | 1 | 0 | 0 |
| gptscan | ap5_verify2_gptscan_part | 1 | 5 | 0 |
| gptscan | ap5_verify_gptscan_brake | 1 | 22 | 0 |
| gptscan | ap5_verify_gptscan_net | 1 | 3 | 0 |
| gptscan | ap5_verify_gptscan_notimeout | 1 | 0 | 0 |
| gptscan | assign6_dry | 10 | 7 | 0 |
| gptscan | assign6_dry_0_6_12 | 10 | 7 | 0 |
| gptscan | assign6_dry_0_8_24 | 10 | 7 | 0 |
| gptscan | assign6_live | 10 | 0 | 0 |
| gptscan | assign6_live_0612 | 10 | 0 | 0 |
| gptscan | curated_gptscan_demo_defi | 5 | 17 | 0 |
| gptscan | curated_gptscan_demo_swc | 5 | 0 | 0 |
| gptscan | curated_gptscan_mwe_20260706 | 96 | 300 | 0 |
| gptscan | curated_gptscan_mwefixed_dry | 96 | 479 | 0 |
| gptscan | curated_gptscan_mwefixed_live | 96 | 174 | 0 |
| gptscan | curated_gptscan_v1_20260705 | 143 | 8 | 0 |
| gptscan | gptscan_mwefixed_v2_dry | 96 | 459 | 0 |
| gptscan | gptscan_mwefixed_v2_main | 96 | 162 | 0 |
| gptscan | gptscan_mwefixed_v2_main_nomain | 3 | 4 | 0 |
| gptscan | gptscan_mwefixed_v2_smoke | 3 | 8 | 0 |
| gptscan | gptscan_mwefixed_v2_smoke2 | 3 | 9 | 0 |
| gptscan | mwevar_dry | 96 | 286 | 0 |
| gptscan | mwevar_live | 27 | 101 | 0 |
| gptscan | phase6_dry | 15 | 37 | 0 |
| gptscan | phase6_live | 15 | 41 | 0 |
| gptscan | smoke1_dry | 3 | 6 | 0 |
| gptscan | smoke2_live | 3 | 3 | 0 |
| llmsmartaudit | ap5_free_llmsa_net | 2 | 2 | 0 |
| llmsmartaudit | ap5_free_llmsa_notimeout | 1 | 0 | 0 |
| llmsmartaudit | ap5_live_llmsa_full | 1 | 0 | 0 |
| llmsmartaudit | ap5_live_llmsa_partial | 1 | 1 | 0 |
| llmsmartaudit | ap5_verify_llmsa_net | 1 | 1 | 0 |
| llmsmartaudit | curated_llmsa_demo_defi_llm | 4 | 0 | 0 |
| llmsmartaudit | curated_llmsa_demo_kostenprobe | 1 | 0 | 0 |
| llmsmartaudit | curated_llmsa_demo_swc_llm | 5 | 0 | 0 |
| llmsmartaudit | curated_llmsa_v1_20260705 | 143 | 0 | 0 |
| llmsmartaudit | llmsa_mwefixed_v2 | 96 | 82 | 0 |
| llmsmartaudit | llmsa_mwefixed_v2_retry | 4 | 0 | 0 |
| llmsmartaudit | llmsa_smoke_curated | 3 | 2 | 0 |
| llmsmartaudit | smoke1_stub | 1 | 2 | 0 |
| llmsmartaudit | smoke2_live | 3 | 0 | 0 |
| slither-0.11.3 | curated_slither_v1_20260705 | 143 | 6 | 0 |
| **Summe** | | **1272** | **2289** | **0** |

## Ergebnis

**Keine Luecke.** Jede im Rohmaterial gefundene Meldung ist im
Parser-Output wiederauffindbar.


## Signaltypen

| Signal | Bedeutung |
|---|---|
| `TRACEBACK` | Python-Traceback im Log (roh oder `rich`-gerendert) |
| `LOG_ERROR` | Log-Record des Tools auf Stufe ERROR/CRITICAL |
| `COMPILE_ERROR` | solc-Diagnose zu einem Contract, der nicht uebersetzt wurde |
| `STATIC_SKIPPED` | GPTScans Static-Stufe lief mangels Falcon-IR nicht |
| `OUTPUT_MISSING` | kein brauchbares `output.json` im eingesammelten tar |
| `OUTPUT_UNSUCCESSFUL` | `output.json` meldet `success: false` |
| `OUTPUT_ERROR` | `output.json` traegt ein `error`-Feld |
| `META_MISSING` | `GPTSCAN_META` fehlt trotz Exit-Code 0 |
| `EXIT_NONZERO` / `EXIT_TIMEOUT` | Container-Abbruch bzw. SmartBugs-Timeout |
| `BUDGET_EXCEEDED` / `BUDGET_SKIPS` | GPTScans Kostenbremse hat gegriffen |

Klassifikation: `root_cause` = Ursache, `consequence` = Folgefehler eines
gescheiterten Compilats, `independent` = davon unabhaengig. Die Einordnung
ersetzt keine Meldung — jede Meldung wird unveraendert weitergereicht.
