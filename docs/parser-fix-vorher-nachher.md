# Vorher/Nachher-Vergleich der Parser-Ausgabe

Stand 02.08.2026: Ausgabe von `analysis_tools/compare_csv.py` über die 930
Tasks der damals 19 Läufe, einmal mit dem Parser vor und einmal nach der
Reparatur vom 02.08.2026. Die Spalte `findings` blieb für jeden Task gleich;
`errors` und `infos` kamen hinzu. Einordnung: `BA-ERRORS-VS-FAILS.md` und
`BA-ARBEITSBERICHT-20260802.md`.

```
Rows: 930 before, 930 after (0 disappeared, 0 appeared)

tool/run                                       tasks  changed  errors  fails  infos  findings
---------------------------------------------------------------------------------------------
gptscan/assign6_dry                               10       10       1      0      3         0
gptscan/assign6_dry_0_6_12                        10       10       1      0      3         0
gptscan/assign6_dry_0_8_24                        10       10       1      0      3         0
gptscan/assign6_live                              10       10       0      0      1         0
gptscan/assign6_live_0612                         10       10       0      0      1         0
gptscan/curated_gptscan_mwe_20260706              96       96      95      0     95         0
gptscan/curated_gptscan_mwefixed_dry              96       96      55      0     78         0
gptscan/curated_gptscan_mwefixed_live             96       96      36      0     39         0
gptscan/curated_gptscan_v1_20260705              143      143       2      0      4         0
gptscan/mwevar_dry                                96       96      95      0     95         0
gptscan/mwevar_live                               27       27      27      0     27         0
gptscan/phase6_dry                                15       15      12      0     13         0
gptscan/phase6_live                               15       15      12      0     12         0
gptscan/smoke1_dry                                 3        3       2      0      2         0
gptscan/smoke2_live                                3        3       1      0      1         0
llmsmartaudit/curated_llmsa_v1_20260705          143      143       0      0      0         0
llmsmartaudit/smoke1_stub                          1        1       1      0      0         0
llmsmartaudit/smoke2_live                          3        3       0      0      0         0
slither-0.11.3/curated_slither_v1_20260705       143        0       0      0      0         0
---------------------------------------------------------------------------------------------
TOTAL                                            930      787     341      0    377         0

findings column: unchanged for every task -- recall/precision cannot have moved.

Newly reported in 'errors' (1378 entries, 343 distinct):
    222  ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 
    121  ERROR    tasks: Static analysis failed: Invalid args
    100  falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Error: Expect
     75  falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Error: Functi
     62  falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Warning: SPDX
     51  TypeError: 'in <string>' requires string as left operand, not NoneType
     44  GPTScan reported success=false: no output produced
     34  WARNING  static_check: Falcon is not initialized, skipping first deposit check
     16  AttributeError: 'NoneType' object has no attribute 'lower'
     12  ERROR    tasks: Current File: /work/input/14_YieldSourcePrizePool.so l, current function: 
     12  IndexError: list index out of range
     10  ERROR    tasks: Current File: /work/input/24_SwappableYieldSource.so l, current function: 
      7  ERROR    tasks: Current File: /work/input/70_LiquidityBasedTWAP.sol, current function: _ad
      6  ERROR    tasks: Current File: /work/input/70_LiquidityBasedTWAP.sol, current function: _up
      6  solc rejected 74_TimeswapPair.sol: Error: Expected ',' but got identifier --> /work/input/

Newly reported in 'infos' (448 entries, 65 distinct):
    246  GPTScan analysis degraded: the contract did not compile, so the static confirmation stage 
     41  static confirmation filtered LLM candidates: 1 before, 0 after (intended behaviour)
     12  static confirmation filtered LLM candidates: 4 before, 0 after (intended behaviour)
     12  static confirmation filtered LLM candidates: 2 before, 0 after (intended behaviour)
     11  static confirmation filtered LLM candidates: 5 before, 0 after (intended behaviour)
     10  static confirmation filtered LLM candidates: 3 before, 0 after (intended behaviour)
      9  static confirmation filtered LLM candidates: 6 before, 0 after (intended behaviour)
      7  static confirmation filtered LLM candidates: 2 before, 1 after (intended behaviour)
      7  static confirmation filtered LLM candidates: 8 before, 0 after (intended behaviour)
      5  static confirmation filtered LLM candidates: 15 before, 0 after (intended behaviour)
      5  static confirmation filtered LLM candidates: 7 before, 0 after (intended behaviour)
      5  static confirmation filtered LLM candidates: 4 before, 1 after (intended behaviour)
      4  static confirmation filtered LLM candidates: 10 before, 0 after (intended behaviour)
      4  static confirmation filtered LLM candidates: 29 before, 0 after (intended behaviour)
      3  static confirmation filtered LLM candidates: 20 before, 0 after (intended behaviour)
```
