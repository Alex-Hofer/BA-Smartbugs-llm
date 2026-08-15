# GPTScan-Lauf `gptscan_mwefixed_v2_main` -- Auswertung

Erzeugt 2026-08-15T16:27:03.794639+00:00 von `analysis_tools/gptscan_eval.py`.
Rohergebnisse: `smartbugs/results/gptscan/gptscan_mwefixed_v2_main` (unveraendert).

## Eckdaten

| | |
|---|---|
| Contracts | 96 |
| Findings | 74 auf 37 Contracts |
| Provider / Modell | deepseek / deepseek-v4-flash |
| MAIN | True |
| processes / timeout / mem-limit | 4 / 1800 s / 4g |
| Kosten | $0.3638 (Median $0.00135, max $0.02639) |
| Tokens | 736374 prompt / 930986 completion, 1518 LLM-Calls |
| Laufzeit | Wanduhr 3055 s, Task-Summe 11771.7 s, Median 54.2 s, max 922.2 s |

Der Timeout wird derzeit nur von Docker durchgesetzt, nicht vom Werkzeug selbst (AP5, offen).

## Zustaende

Begriffe nach `docs/BA-ERRORS-VS-FAILS.md`.

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| findings | 74 | Verdachtsfall ueber den Contract |
| Tasks mit errors | 31 | Werkzeug hat das Problem bemerkt, abgefangen und weitergearbeitet |
| Tasks mit fails | 0 | Werkzeug ausgehebelt, kein Ergebnis zustande gekommen |
| Contract nicht uebersetzt (degraded) | 1 | Compilat gescheitert -> ein Lauf ohne Findings ist hier UNBESTIMMT, nicht sauber |
| ohne Findings, sauber | 58 | uebersetzt, vollstaendig gelaufen, nichts gemeldet |

**Fehlerquote** (Tasks mit fails / alle Tasks): 0/96 = 0.0 %.
**Errorquote** (Tasks mit errors / alle Tasks): 31/96 = 32.3 %.

> **Zusammengefuehrter Blick.** Die Zahlen oben schliessen den Nachlauf `gptscan_mwefixed_v2_main_nomain` ein. Im Hauptlauf `gptscan_mwefixed_v2_main` selbst scheiterten `31_veCVXStrategy.sol`, `62_Locke.sol`, `8_NFTXEligiblityManager.sol` mit Exit 127: ihr Dateiname benennt keinen im File enthaltenen Contract, `--main` hat also nichts, worauf es reduzieren koennte. SmartBugs fuehrt das als fail mit Klartext (`sb/parse_utils.py`), nicht als 'keine Findings'. Ersetzt wurden dadurch: `31_veCVXStrategy`, `62_Locke`, `8_NFTXEligiblityManager` -- diese Contracts sind OHNE `--main` analysiert und in der Spalte `function_source` als `voll` erkennbar. Der Hauptlauf allein hat damit 3 fails; hier stehen 0, weil der Nachlauf sie aufgeloest hat.

Nicht uebersetzt (nie als 'keine Findings' zaehlen): `58_UniV3Vault`

## Findings je Kategorie

`category_defi_logic` = die Regel hat in SWC/DASP kein redliches Gegenstueck (8 von 10, so in `findings.yaml` begruendet).

| MWE-Regel | Anzahl | Contracts | DeFi-Logik | DASP-10 | SWC |
|---|---:|---:|---|---|---|
| MWE-200: Insecure LP Token Value Calculation | 41 | 25 | ja | -- | -- |
| MWE-203: Approval Not Revoked | 8 | 7 | ja | -- | -- |
| MWE-206: No Slippage Limit Check | 8 | 5 | ja | -- | -- |
| MWE-209: Wrong Order for Interest or ExchangeRate | 6 | 4 | ja | -- | -- |
| MWE-201: Insecure Vote Calculation | 4 | 1 | ja | -- | -- |
| MWE-205: Front Running | 3 | 3 | nein | DASP-7 | SWC-114 |
| MWE-207: Unauthorized Transfer | 3 | 3 | nein | DASP-2 | -- |
| MWE-202: Insecure Token Buying Behavior | 1 | 1 | ja | -- | -- |

Regeln ohne Treffer in diesem Lauf: 2 von 10

- MWE-204: Unsafe First Deposit
- MWE-208: Wrong Order for Checkpoint

### Severity

| Severity | Findings |
|---|---:|
| high | 74 |

## Findings je Contract

37 von 96 Contracts tragen mindestens ein Finding.

| Contract | Findings | Regeln |
|---|---:|---|
| `20_Synth` | 7 | MWE-200, MWE-205, MWE-206, MWE-207 |
| `20_Pool` | 5 | MWE-200, MWE-205, MWE-206 |
| `5_DAO` | 4 | MWE-201 |
| `68_BasketFacet` | 4 | MWE-200 |
| `70_VaderPoolV2` | 4 | MWE-200, MWE-203, MWE-206 |
| `71_PoolTemplate` | 4 | MWE-200 |
| `14_YieldSourcePrizePool` | 3 | MWE-200, MWE-209 |
| `29_HybridPool` | 3 | MWE-200, MWE-207 |
| `29_IndexPool` | 3 | MWE-200 |
| `32_LendingPair` | 3 | MWE-200 |
| `5_Pools` | 3 | MWE-205, MWE-206 |
| `10_Visor` | 2 | MWE-203 |
| `18_LendingPair` | 2 | MWE-209 |
| `193_Pair` | 2 | MWE-200 |
| `5_Router` | 2 | MWE-200, MWE-206 |
| `69_NFTXMarketplaceZap` | 2 | MWE-200, MWE-202 |
| `106_NFTLoanFacilitator` | 1 | MWE-209 |
| `107_yVault` | 1 | MWE-200 |
| `13_RCMarket` | 1 | MWE-203 |
| `14_BadgerYieldSource` | 1 | MWE-200 |
| `192_Position` | 1 | MWE-203 |
| `19_TransactionManager` | 1 | MWE-203 |
| `22_LongShort` | 1 | MWE-200 |
| `25_CompoundMultiOracle` | 1 | MWE-200 |
| `30_Vault` | 1 | MWE-200 |
| `31_veCVXStrategy` | 1 | MWE-200 |
| `34_ConcentratedLiquidityPosition` | 1 | MWE-207 |
| `36_Basket` | 1 | MWE-200 |
| `37_TempusController` | 1 | MWE-200 |
| `39_VaultTracker` | 1 | MWE-200 |
| `43_DelegatedStaking` | 1 | MWE-209 |
| `5_USDV` | 1 | MWE-200 |
| `5_Vader` | 1 | MWE-200 |
| `66_sYETIToken` | 1 | MWE-200 |
| `67_Vault` | 1 | MWE-203 |
| `71_IndexTemplate` | 1 | MWE-200 |
| `75_XDEFIDistribution` | 1 | MWE-203 |

## Contracts ohne Findings

58 Contracts sind uebersetzt, vollstaendig gelaufen und melden nichts. Getrennt davon: 1 nicht uebersetzt (unbestimmt) und 0 fails.

`12_AccessControl`, `12_Cauldron`, `12_Witch`, `12_YieldMath`, `13_RCFactory`, `13_RCOrderbook`, `13_RCTreasury`, `14_IdleYieldSource`, `14_PrizePool`, `14_SushiYieldSource`, `16_GasOracle`, `16_Liquidation`, `16_Pricing`, `16_TracerPerpetualSwaps`, `16_TracerPerpetualsFactory`, `16_Trader`, `17_Buoy3Pool`, `17_Exposure`, `17_PnL`, `22_Staker`, `23_CompoundToNotionalV2`, `23_NotionalV1ToNotionalV2`, `23_nTokenAction`, `24_SwappableYieldSource`, `25_CTokenInterface`, `25_CompositeMultiOracle`, `26_RCOrderbook`, `28_PostAuctionLauncher`, `28_SushiToken`, `30_Controller`, `34_ConcentratedLiquidityPool`, `36_Auction`, `38_Identity`, `38_QuickAccManager`, `3_MarginRouter`, `44_Swap`, `45_CreditLimitByMedian`, `46_WrappedIbbtcEth`, `5_Vether`, `62_Locke`, `64_TwabRewards`, `66_StabilityPool`, `68_SingleTokenJoinV2`, `69_NFTXSimpleFeeDistributor`, `69_NFTXStakingZap`, `6_Beebots`, `70_LiquidityBasedTWAP`, `71_Vault`, `74_TimeswapPair`, `78_FlanBackstop`, `78_FlashGovernanceArbiter`, `83_ConvexStakingWrapper`, `83_MasterChef`, `83_Shelter`, `83_StakingRewards`, `8_ERC20FlashMintUpgradeable`, `8_NFTXEligiblityManager`, `8_NFTXVaultUpgradeable`

## Vorbehalte zu den Feldern in findings.jsonl

- `confidence` ist immer `null`. GPTScans `output.json` kennt nur `code`, `severity`, `title`, `description`, `recommendation`, `affectedFiles` -- einen Konfidenzwert gibt das Werkzeug nicht aus. Das Feld bleibt leer, statt einen Wert zu erfinden.
- `function` ist heuristisch aus dem analysierten Quelltext bestimmt (Deklarationskopf + Klammerzaehlung), nicht von GPTScan geliefert. Wo die Zuordnung nicht greift, bleibt das Feld leer.
- `lines` bezieht sich auf die Datei, die GPTScan tatsaechlich gesehen hat: 41 Contracts main-reduziert, 55 voll, 0 unbestimmt. Das Feld `lines_refer_to` haelt das je Finding fest. Zeilennummern aus einem MAIN-Lauf sind mit denen eines Laufs ohne MAIN NICHT vergleichbar.
- `dasp10` bleibt leer, wo `findings.yaml` kein redliches Mapping kennt. Die dort unter `related` vermerkten Naeherungen werden bewusst NICHT eingesetzt.
