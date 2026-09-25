# GPTScan-Lauf `gptscan_mwefixed_v2_dry` -- Auswertung

Erzeugt 2026-09-25T16:18:26.823060+00:00 von `analysis_tools/gptscan_eval.py`.
Rohergebnisse: `smartbugs/results/gptscan/gptscan_mwefixed_v2_dry` (unveraendert).

## Eckdaten

| | |
|---|---|
| Contracts | 96 |
| Findings | 5 auf 5 Contracts |
| Provider / Modell | deepseek / deepseek-v4-flash |
| MAIN | True |
| processes / timeout / mem-limit | None / None s / None |
| Kosten | $0.3838 (Median $0.00268, max $0.03148) |
| Tokens | 1186820 prompt / 777250 completion, 3109 LLM-Calls |
| Laufzeit | Wanduhr None s, Task-Summe 1890.7 s, Median 19.5 s, max 28.0 s |

Der Timeout wirkt seit AP5 im Container (Bremse bei GPTScan, Netz als letzte Stufe); Docker bleibt als aeusserer Fallback bestehen.

## Zustaende

Begriffe nach `docs/BA-ERRORS-VS-FAILS.md`.

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| findings | 5 | Verdachtsfall ueber den Contract |
| Tasks mit errors | 51 | Werkzeug hat das Problem bemerkt, abgefangen und weitergearbeitet |
| Tasks mit fails | 3 | Werkzeug ausgehebelt, kein Ergebnis zustande gekommen |
| Contract nicht uebersetzt (degraded) | 2 | Compilat gescheitert -> ein Lauf ohne Findings ist hier UNBESTIMMT, nicht sauber |
| ohne Findings, sauber | 86 | uebersetzt, vollstaendig gelaufen, nichts gemeldet |

Davon Teillaeufe (Timeout): 0 von 96. Ein durch die AP5-Deadline vorzeitig beendeter Lauf liefert weniger Findings als ein Volllauf; er bleibt dennoch in allen Zahlen oben mitgezaehlt, siehe `sb_timeout` in `docs/BA-AP5-TIMEOUT-DESIGN.md`.

**Fehlerquote** (Tasks mit fails / alle Tasks): 3/96 = 3.1 %.
**Errorquote** (Tasks mit errors / alle Tasks): 51/96 = 53.1 %.

Tasks mit fails: `31_veCVXStrategy`, `62_Locke`, `8_NFTXEligiblityManager`

Nicht uebersetzt (nie als 'keine Findings' zaehlen): `19_TransactionManager`, `58_UniV3Vault`

## Findings je Kategorie

`category_defi_logic` = die Regel hat in SWC/DASP kein redliches Gegenstueck (8 von 10, so in `findings.yaml` begruendet).

| MWE-Regel | Anzahl | Contracts | DeFi-Logik | DASP-10 | SWC |
|---|---:|---:|---|---|---|
| MWE-205: Front Running | 5 | 5 | nein | DASP-7 | SWC-114 |

Regeln ohne Treffer in diesem Lauf: 9 von 10

- MWE-200: Insecure LP Token Value Calculation
- MWE-201: Insecure Vote Calculation
- MWE-202: Insecure Token Buying Behavior
- MWE-203: Approval Not Revoked
- MWE-204: Unsafe First Deposit
- MWE-206: No Slippage Limit Check
- MWE-207: Unauthorized Transfer
- MWE-208: Wrong Order for Checkpoint
- MWE-209: Wrong Order for Interest or ExchangeRate

### Severity

| Severity | Findings |
|---|---:|
| high | 5 |

## Findings je Contract

5 von 96 Contracts tragen mindestens ein Finding.

| Contract | Findings | Regeln |
|---|---:|---|
| `13_RCTreasury` | 1 | MWE-205 |
| `20_Pool` | 1 | MWE-205 |
| `20_Synth` | 1 | MWE-205 |
| `32_LendingPair` | 1 | MWE-205 |
| `5_Pools` | 1 | MWE-205 |

## Contracts ohne Findings

86 Contracts sind uebersetzt, vollstaendig gelaufen und melden nichts. Getrennt davon: 2 nicht uebersetzt (unbestimmt) und 3 fails.

`106_NFTLoanFacilitator`, `107_yVault`, `10_Visor`, `12_AccessControl`, `12_Cauldron`, `12_Witch`, `12_YieldMath`, `13_RCFactory`, `13_RCMarket`, `13_RCOrderbook`, `14_BadgerYieldSource`, `14_IdleYieldSource`, `14_PrizePool`, `14_SushiYieldSource`, `14_YieldSourcePrizePool`, `16_GasOracle`, `16_Liquidation`, `16_Pricing`, `16_TracerPerpetualSwaps`, `16_TracerPerpetualsFactory`, `16_Trader`, `17_Buoy3Pool`, `17_Exposure`, `17_PnL`, `18_LendingPair`, `192_Position`, `193_Pair`, `22_LongShort`, `22_Staker`, `23_CompoundToNotionalV2`, `23_NotionalV1ToNotionalV2`, `23_nTokenAction`, `24_SwappableYieldSource`, `25_CTokenInterface`, `25_CompositeMultiOracle`, `25_CompoundMultiOracle`, `26_RCOrderbook`, `28_PostAuctionLauncher`, `28_SushiToken`, `29_HybridPool`, `29_IndexPool`, `30_Controller`, `30_Vault`, `34_ConcentratedLiquidityPool`, `34_ConcentratedLiquidityPosition`, `36_Auction`, `36_Basket`, `37_TempusController`, `38_Identity`, `38_QuickAccManager`, `39_VaultTracker`, `3_MarginRouter`, `43_DelegatedStaking`, `44_Swap`, `45_CreditLimitByMedian`, `46_WrappedIbbtcEth`, `5_DAO`, `5_Router`, `5_USDV`, `5_Vader`, `5_Vether`, `64_TwabRewards`, `66_StabilityPool`, `66_sYETIToken`, `67_Vault`, `68_BasketFacet`, `68_SingleTokenJoinV2`, `69_NFTXMarketplaceZap`, `69_NFTXSimpleFeeDistributor`, `69_NFTXStakingZap`, `6_Beebots`, `70_LiquidityBasedTWAP`, `70_VaderPoolV2`, `71_IndexTemplate`, `71_PoolTemplate`, `71_Vault`, `74_TimeswapPair`, `75_XDEFIDistribution`, `78_FlanBackstop`, `78_FlashGovernanceArbiter`, `83_ConvexStakingWrapper`, `83_MasterChef`, `83_Shelter`, `83_StakingRewards`, `8_ERC20FlashMintUpgradeable`, `8_NFTXVaultUpgradeable`

## Vorbehalte zu den Feldern in findings.jsonl

- `confidence` ist immer `null`. GPTScans `output.json` kennt nur `code`, `severity`, `title`, `description`, `recommendation`, `affectedFiles` -- einen Konfidenzwert gibt das Werkzeug nicht aus. Das Feld bleibt leer, statt einen Wert zu erfinden.
- `function` ist heuristisch aus dem analysierten Quelltext bestimmt (Deklarationskopf + Klammerzaehlung), nicht von GPTScan geliefert. Wo die Zuordnung nicht greift, bleibt das Feld leer.
- `lines` bezieht sich auf die Datei, die GPTScan tatsaechlich gesehen hat: 41 Contracts main-reduziert, 52 voll, 3 unbestimmt. Das Feld `lines_refer_to` haelt das je Finding fest. Zeilennummern aus einem MAIN-Lauf sind mit denen eines Laufs ohne MAIN NICHT vergleichbar.
- `dasp10` bleibt leer, wo `findings.yaml` kein redliches Mapping kennt. Die dort unter `related` vermerkten Naeherungen werden bewusst NICHT eingesetzt.
