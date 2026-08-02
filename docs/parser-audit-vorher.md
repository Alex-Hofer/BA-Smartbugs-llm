# Lueckenbericht Parser-Audit

Geprueft: **930 Task-Verzeichnisse** aus 19 Laeufen, **1464 extrahierte Rohmeldungen**, davon **1368** im Parser-Output nicht wiederauffindbar.

Erzeugt mit `python analysis_tools/parser_audit.py`. Das Werkzeug liest das
Container-Rohmaterial (`result.log`, `result.tar`, `smartbugs.json`, Exit-Code)
mit eigenen Detektoren und prueft, ob jede gefundene Meldung in `result.json`
wieder auftaucht. Nicht als Fehler gewertet werden bewusst: das normale
Static-Filtering von GPTScan (`vul_before_static > vul_after_static`), reine
solc-Warnungen und slithers Exit-Code 255.

## Uebersicht je Lauf

| Tool | Lauf | Tasks | Rohmeldungen | Luecken |
|---|---|---:|---:|---:|
| gptscan | assign6_dry | 10 | 7 | 7 |
| gptscan | assign6_dry_0_6_12 | 10 | 7 | 7 |
| gptscan | assign6_dry_0_8_24 | 10 | 7 | 7 |
| gptscan | assign6_live | 10 | 0 | 0 |
| gptscan | assign6_live_0612 | 10 | 0 | 0 |
| gptscan | curated_gptscan_mwe_20260706 | 96 | 300 | 256 |
| gptscan | curated_gptscan_mwefixed_dry | 96 | 479 | 479 |
| gptscan | curated_gptscan_mwefixed_live | 96 | 174 | 174 |
| gptscan | curated_gptscan_v1_20260705 | 143 | 8 | 8 |
| gptscan | mwevar_dry | 96 | 286 | 242 |
| gptscan | mwevar_live | 27 | 101 | 101 |
| gptscan | phase6_dry | 15 | 37 | 37 |
| gptscan | phase6_live | 15 | 41 | 41 |
| gptscan | smoke1_dry | 3 | 6 | 6 |
| gptscan | smoke2_live | 3 | 3 | 3 |
| llmsmartaudit | curated_llmsa_v1_20260705 | 143 | 0 | 0 |
| llmsmartaudit | smoke1_stub | 1 | 2 | 0 |
| llmsmartaudit | smoke2_live | 3 | 0 | 0 |
| slither-0.11.3 | curated_slither_v1_20260705 | 143 | 6 | 0 |
| **Summe** | | **930** | **1464** | **1368** |

## Luecken je Lauf und Signaltyp

| Tool | Lauf | Signal | Klassifikation | Contracts | Beispielmeldung |
|---|---|---|---|---:|---|
| gptscan | assign6_dry | `LOG_ERROR` | independent | 6 | tasks: Static analysis failed: Invalid args |
| gptscan | assign6_dry | `TRACEBACK` | independent | 1 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | assign6_dry_0_6_12 | `LOG_ERROR` | independent | 6 | tasks: Static analysis failed: Invalid args |
| gptscan | assign6_dry_0_6_12 | `TRACEBACK` | independent | 1 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | assign6_dry_0_8_24 | `LOG_ERROR` | independent | 6 | tasks: Static analysis failed: Invalid args |
| gptscan | assign6_dry_0_8_24 | `TRACEBACK` | independent | 1 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwe_20260706 | `COMPILE_ERROR` | root_cause | 95 | solc diagnostics for 106_NFTLoanFacilitator.sol: Error: Expected ',' but got identifier --> /work/input/106_NFTLoanFacilitator.sol: 37:248: \| 37 \|   |
| gptscan | curated_gptscan_mwe_20260706 | `LOG_ERROR` | consequence | 39 | tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwe_20260706 | `OUTPUT_UNSUCCESSFUL` | independent | 22 | output.json reports success=false (message: no output produced) |
| gptscan | curated_gptscan_mwe_20260706 | `STATIC_SKIPPED` | consequence | 5 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | curated_gptscan_mwe_20260706 | `TRACEBACK` | consequence | 95 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Error: Expected ',' but got identifier --> /work/input/106_NFTLoanFacilit |
| gptscan | curated_gptscan_mwefixed_dry | `COMPILE_ERROR` | root_cause | 2 | solc diagnostics for 19_TransactionManager.sol: Warning: Unnamed return variable can remain unassigned. Add an explicit return with value to all non-r |
| gptscan | curated_gptscan_mwefixed_dry | `LOG_ERROR` | consequence | 5 | ContractSolcParsing: Missing function Incorrect ternary conversion IFulfillHelper(txData.callTo).addFu nds{value: if LibAsset.isEther(txData.receiving |
| gptscan | curated_gptscan_mwefixed_dry | `LOG_ERROR` | independent | 396 | tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_dry | `STATIC_SKIPPED` | consequence | 1 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | curated_gptscan_mwefixed_dry | `TRACEBACK` | consequence | 2 | IndexError: list index out of range |
| gptscan | curated_gptscan_mwefixed_dry | `TRACEBACK` | independent | 73 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_live | `COMPILE_ERROR` | root_cause | 1 | solc diagnostics for 58_UniV3Vault.sol: Compiler error: Stack too deep when compiling inline assembly: Variable headStart is 1 slot(s) too deep inside |
| gptscan | curated_gptscan_mwefixed_live | `LOG_ERROR` | consequence | 3 | tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_live | `LOG_ERROR` | independent | 166 | tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_live | `TRACEBACK` | consequence | 1 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Compiler error: Stack too deep when compiling inline assembly: Variable h |
| gptscan | curated_gptscan_mwefixed_live | `TRACEBACK` | independent | 3 | json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| gptscan | curated_gptscan_v1_20260705 | `LOG_ERROR` | independent | 7 | tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_v1_20260705 | `TRACEBACK` | independent | 1 | json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| gptscan | mwevar_dry | `COMPILE_ERROR` | root_cause | 95 | solc diagnostics for 106_NFTLoanFacilitator.sol: Error: Expected ',' but got identifier --> /work/input/106_NFTLoanFacilitator.sol: 37:248: \| 37 \|   |
| gptscan | mwevar_dry | `LOG_ERROR` | consequence | 13 | tasks: Static analysis failed: Invalid args |
| gptscan | mwevar_dry | `OUTPUT_UNSUCCESSFUL` | independent | 22 | output.json reports success=false (message: no output produced) |
| gptscan | mwevar_dry | `STATIC_SKIPPED` | consequence | 13 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | mwevar_dry | `TRACEBACK` | consequence | 99 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Error: Expected ',' but got identifier --> /work/input/106_NFTLoanFacilit |
| gptscan | mwevar_live | `COMPILE_ERROR` | root_cause | 27 | solc diagnostics for 107_yVault.sol: Warning: SPDX license identifier not provided in source file. Before publishing, consider adding a comment contai |
| gptscan | mwevar_live | `LOG_ERROR` | consequence | 40 | tasks: Static analysis failed: Invalid args |
| gptscan | mwevar_live | `STATIC_SKIPPED` | consequence | 5 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | mwevar_live | `TRACEBACK` | consequence | 29 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Warning: SPDX license identifier not provided in source file. Before publ |
| gptscan | phase6_dry | `COMPILE_ERROR` | root_cause | 12 | solc diagnostics for 107_yVault.sol: Warning: SPDX license identifier not provided in source file. Before publishing, consider adding a comment contai |
| gptscan | phase6_dry | `LOG_ERROR` | consequence | 4 | tasks: Static analysis failed: Invalid args |
| gptscan | phase6_dry | `STATIC_SKIPPED` | consequence | 8 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | phase6_dry | `TRACEBACK` | consequence | 13 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Warning: SPDX license identifier not provided in source file. Before publ |
| gptscan | phase6_live | `COMPILE_ERROR` | root_cause | 12 | solc diagnostics for 107_yVault.sol: Warning: SPDX license identifier not provided in source file. Before publishing, consider adding a comment contai |
| gptscan | phase6_live | `LOG_ERROR` | consequence | 14 | tasks: Static analysis failed: Invalid args |
| gptscan | phase6_live | `STATIC_SKIPPED` | consequence | 3 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | phase6_live | `TRACEBACK` | consequence | 12 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Warning: SPDX license identifier not provided in source file. Before publ |
| gptscan | smoke1_dry | `COMPILE_ERROR` | root_cause | 1 | solc diagnostics for 20_Pool.sol: Error: Function, variable, struct or modifier declaration expected. --> /work/input/20_Pool.sol:22:12944: \| 22 \|   |
| gptscan | smoke1_dry | `LOG_ERROR` | independent | 3 | tasks: Static analysis failed: Invalid args |
| gptscan | smoke1_dry | `TRACEBACK` | consequence | 1 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Error: Function, variable, struct or modifier declaration expected. --> / |
| gptscan | smoke1_dry | `TRACEBACK` | independent | 1 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | smoke2_live | `COMPILE_ERROR` | root_cause | 1 | solc diagnostics for 74_TimeswapPair.sol: Error: Expected ',' but got identifier --> /work/input/74_TimeswapPair.sol:51:80: \| 51 \| function constant |
| gptscan | smoke2_live | `STATIC_SKIPPED` | consequence | 1 | static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | smoke2_live | `TRACEBACK` | consequence | 1 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Error: Expected ',' but got identifier --> /work/input/74_TimeswapPair.so |

## Betroffene Contracts je Lauf

- **gptscan/assign6_dry** — 1 Contracts: SmartBillions.sol
- **gptscan/assign6_dry_0_6_12** — 1 Contracts: SmartBillions.sol
- **gptscan/assign6_dry_0_8_24** — 1 Contracts: SmartBillions.sol
- **gptscan/curated_gptscan_mwe_20260706** — 95 Contracts: 106_NFTLoanFacilitator.sol, 107_yVault.sol, 10_Visor.sol, 12_AccessControl.sol, 12_Cauldron.sol, 12_Witch.sol, 12_YieldMath.sol, 13_RCFactory.sol, 13_RCMarket.sol, 13_RCOrderbook.sol, 13_RCTreasury.sol, 14_BadgerYieldSource.sol ... (+83 weitere)
- **gptscan/curated_gptscan_mwefixed_dry** — 55 Contracts: 106_NFTLoanFacilitator.sol, 107_yVault.sol, 14_BadgerYieldSource.sol, 14_IdleYieldSource.sol, 14_PrizePool.sol, 14_SushiYieldSource.sol, 14_YieldSourcePrizePool.sol, 17_Buoy3Pool.sol, 18_LendingPair.sol, 193_Pair.sol, 19_TransactionManager.sol, 20_Pool.sol ... (+43 weitere)
- **gptscan/curated_gptscan_mwefixed_live** — 36 Contracts: 107_yVault.sol, 14_BadgerYieldSource.sol, 14_IdleYieldSource.sol, 14_SushiYieldSource.sol, 14_YieldSourcePrizePool.sol, 17_Buoy3Pool.sol, 193_Pair.sol, 19_TransactionManager.sol, 20_Pool.sol, 20_Synth.sol, 22_LongShort.sol, 23_nTokenAction.sol ... (+24 weitere)
- **gptscan/curated_gptscan_v1_20260705** — 2 Contracts: 0xe894d54dca59cb53fe9cbc5155093605c7068220.sol, smart_billions.sol
- **gptscan/mwevar_dry** — 95 Contracts: 106_NFTLoanFacilitator.sol, 107_yVault.sol, 10_Visor.sol, 12_AccessControl.sol, 12_Cauldron.sol, 12_Witch.sol, 12_YieldMath.sol, 13_RCFactory.sol, 13_RCMarket.sol, 13_RCOrderbook.sol, 13_RCTreasury.sol, 14_BadgerYieldSource.sol ... (+83 weitere)
- **gptscan/mwevar_live** — 27 Contracts: 107_yVault.sol, 10_Visor.sol, 14_BadgerYieldSource.sol, 14_PrizePool.sol, 14_SushiYieldSource.sol, 16_Pricing.sol, 16_TracerPerpetualSwaps.sol, 17_Buoy3Pool.sol, 17_Exposure.sol, 24_SwappableYieldSource.sol, 28_PostAuctionLauncher.sol, 30_Controller.sol ... (+15 weitere)
- **gptscan/phase6_dry** — 12 Contracts: 107_yVault.sol, 16_Pricing.sol, 30_Vault.sol, 32_LendingPair.sol, 44_Swap.sol, 64_TwabRewards.sol, 70_LiquidityBasedTWAP.sol, 74_TimeswapPair.sol, 83_StakingRewards.sol, BitCash.sol, HotDollarsToken.sol, WETH9.sol
- **gptscan/phase6_live** — 12 Contracts: 107_yVault.sol, 16_Pricing.sol, 30_Vault.sol, 32_LendingPair.sol, 44_Swap.sol, 64_TwabRewards.sol, 70_LiquidityBasedTWAP.sol, 74_TimeswapPair.sol, 83_StakingRewards.sol, BitCash.sol, HotDollarsToken.sol, WETH9.sol
- **gptscan/smoke1_dry** — 2 Contracts: 20_Pool.sol, Vault.sol
- **gptscan/smoke2_live** — 1 Contracts: 74_TimeswapPair.sol

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
