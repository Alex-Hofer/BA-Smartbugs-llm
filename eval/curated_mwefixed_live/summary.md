# GPTScan-Lauf `curated_mwefixed_live` -- Auswertung

Erzeugt 2026-09-25T09:32:28.584436+00:00 von `analysis_tools/gptscan_eval.py`.
Rohergebnisse: `smartbugs/results/gptscan/curated_mwefixed_live` (unveraendert).

## Eckdaten

| | |
|---|---|
| Contracts | 96 |
| Findings | 77 auf 40 Contracts |
| Provider / Modell | deepseek / deepseek-v4-flash |
| MAIN | False |
| processes / timeout / mem-limit | None / None s / None |
| Kosten | $0.2769 (Median $0.00133, max $0.02019) |
| Tokens | 668808 prompt / 654392 completion, 1614 LLM-Calls |
| Laufzeit | Wanduhr None s, Task-Summe 8217.2 s, Median 42.0 s, max 657.5 s |

Der Timeout wirkt seit AP5 im Container (Bremse bei GPTScan, Netz als letzte Stufe); Docker bleibt als aeusserer Fallback bestehen.

## Zustaende

Begriffe nach `docs/BA-ERRORS-VS-FAILS.md`.

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| findings | 77 | Verdachtsfall ueber den Contract |
| Tasks mit errors | 36 | Werkzeug hat das Problem bemerkt, abgefangen und weitergearbeitet |
| Tasks mit fails | 0 | Werkzeug ausgehebelt, kein Ergebnis zustande gekommen |
| Contract nicht uebersetzt (degraded) | 1 | Compilat gescheitert -> ein Lauf ohne Findings ist hier UNBESTIMMT, nicht sauber |
| ohne Findings, sauber | 55 | uebersetzt, vollstaendig gelaufen, nichts gemeldet |

Davon Teillaeufe (Timeout): 0 von 96. Ein durch die AP5-Deadline vorzeitig beendeter Lauf liefert weniger Findings als ein Volllauf; er bleibt dennoch in allen Zahlen oben mitgezaehlt, siehe `sb_timeout` in `docs/BA-AP5-TIMEOUT-DESIGN.md`.

**Fehlerquote** (Tasks mit fails / alle Tasks): 0/96 = 0.0 %.
**Errorquote** (Tasks mit errors / alle Tasks): 36/96 = 37.5 %.

Nicht uebersetzt (nie als 'keine Findings' zaehlen): `58_UniV3Vault`

## Findings je Kategorie

`category_defi_logic` = die Regel hat in SWC/DASP kein redliches Gegenstueck (8 von 10, so in `findings.yaml` begruendet).

| MWE-Regel | Anzahl | Contracts | DeFi-Logik | DASP-10 | SWC |
|---|---:|---:|---|---|---|
| MWE-200: Insecure LP Token Value Calculation | 44 | 25 | ja | -- | -- |
| MWE-209: Wrong Order for Interest or ExchangeRate | 7 | 6 | ja | -- | -- |
| MWE-206: No Slippage Limit Check | 7 | 5 | ja | -- | -- |
| MWE-203: Approval Not Revoked | 6 | 6 | ja | -- | -- |
| MWE-205: Front Running | 4 | 4 | nein | DASP-7 | SWC-114 |
| MWE-207: Unauthorized Transfer | 4 | 3 | nein | DASP-2 | -- |
| MWE-201: Insecure Vote Calculation | 4 | 1 | ja | -- | -- |
| MWE-202: Insecure Token Buying Behavior | 1 | 1 | ja | -- | -- |

Regeln ohne Treffer in diesem Lauf: 2 von 10

- MWE-204: Unsafe First Deposit
- MWE-208: Wrong Order for Checkpoint

### Severity

| Severity | Findings |
|---|---:|
| high | 77 |

## Findings je Contract

40 von 96 Contracts tragen mindestens ein Finding.

| Contract | Findings | Regeln |
|---|---:|---|
| `20_Synth` | 6 | MWE-200, MWE-205, MWE-206 |
| `5_Pools` | 5 | MWE-200, MWE-205, MWE-206 |
| `29_HybridPool` | 4 | MWE-200, MWE-207 |
| `5_DAO` | 4 | MWE-201 |
| `70_VaderPoolV2` | 4 | MWE-200, MWE-203, MWE-206 |
| `14_PrizePool` | 3 | MWE-207, MWE-209 |
| `20_Pool` | 3 | MWE-200, MWE-205, MWE-206 |
| `29_IndexPool` | 3 | MWE-200 |
| `32_LendingPair` | 3 | MWE-200 |
| `5_Router` | 3 | MWE-200, MWE-206 |
| `68_BasketFacet` | 3 | MWE-200 |
| `71_PoolTemplate` | 3 | MWE-200 |
| `14_IdleYieldSource` | 2 | MWE-200 |
| `193_Pair` | 2 | MWE-200 |
| `30_Vault` | 2 | MWE-200 |
| `43_DelegatedStaking` | 2 | MWE-200 |
| `71_IndexTemplate` | 2 | MWE-200 |
| `106_NFTLoanFacilitator` | 1 | MWE-209 |
| `107_yVault` | 1 | MWE-200 |
| `10_Visor` | 1 | MWE-203 |
| `13_RCTreasury` | 1 | MWE-205 |
| `14_BadgerYieldSource` | 1 | MWE-200 |
| `14_SushiYieldSource` | 1 | MWE-200 |
| `14_YieldSourcePrizePool` | 1 | MWE-209 |
| `16_TracerPerpetualSwaps` | 1 | MWE-209 |
| `18_LendingPair` | 1 | MWE-209 |
| `192_Position` | 1 | MWE-203 |
| `19_TransactionManager` | 1 | MWE-203 |
| `22_LongShort` | 1 | MWE-200 |
| `25_CompoundMultiOracle` | 1 | MWE-200 |
| `36_Basket` | 1 | MWE-200 |
| `37_TempusController` | 1 | MWE-200 |
| `39_VaultTracker` | 1 | MWE-207 |
| `3_MarginRouter` | 1 | MWE-209 |
| `5_USDV` | 1 | MWE-200 |
| `5_Vader` | 1 | MWE-200 |
| `66_sYETIToken` | 1 | MWE-200 |
| `67_Vault` | 1 | MWE-203 |
| `69_NFTXMarketplaceZap` | 1 | MWE-202 |
| `75_XDEFIDistribution` | 1 | MWE-203 |

## Contracts ohne Findings

55 Contracts sind uebersetzt, vollstaendig gelaufen und melden nichts. Getrennt davon: 1 nicht uebersetzt (unbestimmt) und 0 fails.

`12_AccessControl`, `12_Cauldron`, `12_Witch`, `12_YieldMath`, `13_RCFactory`, `13_RCMarket`, `13_RCOrderbook`, `16_GasOracle`, `16_Liquidation`, `16_Pricing`, `16_TracerPerpetualsFactory`, `16_Trader`, `17_Buoy3Pool`, `17_Exposure`, `17_PnL`, `22_Staker`, `23_CompoundToNotionalV2`, `23_NotionalV1ToNotionalV2`, `23_nTokenAction`, `24_SwappableYieldSource`, `25_CTokenInterface`, `25_CompositeMultiOracle`, `26_RCOrderbook`, `28_PostAuctionLauncher`, `28_SushiToken`, `30_Controller`, `31_veCVXStrategy`, `34_ConcentratedLiquidityPool`, `34_ConcentratedLiquidityPosition`, `36_Auction`, `38_Identity`, `38_QuickAccManager`, `44_Swap`, `45_CreditLimitByMedian`, `46_WrappedIbbtcEth`, `5_Vether`, `62_Locke`, `64_TwabRewards`, `66_StabilityPool`, `68_SingleTokenJoinV2`, `69_NFTXSimpleFeeDistributor`, `69_NFTXStakingZap`, `6_Beebots`, `70_LiquidityBasedTWAP`, `71_Vault`, `74_TimeswapPair`, `78_FlanBackstop`, `78_FlashGovernanceArbiter`, `83_ConvexStakingWrapper`, `83_MasterChef`, `83_Shelter`, `83_StakingRewards`, `8_ERC20FlashMintUpgradeable`, `8_NFTXEligiblityManager`, `8_NFTXVaultUpgradeable`

## Vorbehalte zu den Feldern in findings.jsonl

- `confidence` ist immer `null`. GPTScans `output.json` kennt nur `code`, `severity`, `title`, `description`, `recommendation`, `affectedFiles` -- einen Konfidenzwert gibt das Werkzeug nicht aus. Das Feld bleibt leer, statt einen Wert zu erfinden.
- `function` ist heuristisch aus dem analysierten Quelltext bestimmt (Deklarationskopf + Klammerzaehlung), nicht von GPTScan geliefert. Wo die Zuordnung nicht greift, bleibt das Feld leer.
- `lines` bezieht sich auf die Datei, die GPTScan tatsaechlich gesehen hat: 0 Contracts main-reduziert, 96 voll, 0 unbestimmt. Das Feld `lines_refer_to` haelt das je Finding fest. Zeilennummern aus einem MAIN-Lauf sind mit denen eines Laufs ohne MAIN NICHT vergleichbar.
- `dasp10` bleibt leer, wo `findings.yaml` kein redliches Mapping kennt. Die dort unter `related` vermerkten Naeherungen werden bewusst NICHT eingesetzt.
