# llmsa_mwefixed_v2

Erzeugt 2026-08-16T11:19:37+00:00 aus `smartbugs/results/llmsmartaudit/llmsa_mwefixed_v2`.
Backend deepseek/deepseek-v4-flash, Modus SmartContractTA (fixed in scripts/do_solidity.sh), MAIN=0.

## Zustaende

| Zustand | Contracts | Anteil |
|---|---:|---:|
| Findings gemeldet | 55 | 57.3 % |
| Kontext ueberschritten - NICHT analysiert | 37 | 38.5 % |
| kein Report | 4 | 4.2 % |

Die Zeile *Kontext ueberschritten* ist kein Ergebnis. Diese Contracts
wurden nie analysiert; sie duerfen weder als 'clean' noch in einer
Precision-Rechnung auftauchen.

## Findings je Kategorie

| Kategorie | Findings | DASP | DeFi-Logik | Severity (aus findings.yaml) |
|---|---:|---|---|---|
| Centralization Risk | 43 | DASP-2 | nein | medium |
| Precision Loss / Integer-Division Truncation | 30 | - | nein | medium |
| Missing Access Control / Authorization | 24 | DASP-2 | nein | high |
| Single External Oracle Dependency | 24 | - | ja | medium |
| Price Manipulation (centralized pricing) | 21 | - | ja | high |
| Gas-Limit / Unbounded Operation | 21 | DASP-5 | nein | medium |
| Missing Withdrawal Function (locked funds) | 20 | - | nein | medium |
| Lack of Input Validation | 19 | - | nein | medium |
| Missing Fallback Function (rejected/locked ether) | 16 | - | nein | low |
| Unchecked External Call (send/transfer/ERC20 return) | 16 | DASP-4 | nein | medium |
| Missing onlyOwner Modifier | 16 | DASP-2 | nein | high |
| Transaction Order Dependence (front-running) | 15 | DASP-7 | nein | medium |
| Unchecked Low-level Call (call/delegatecall/send) | 15 | DASP-4 | nein | medium |
| Timestamp Dependence | 14 | DASP-8 | nein | low |
| Unnecessary Boolean Comparison | 13 | - | nein | low |
| Yield-Source Swap Token Mismatch | 9 | - | ja | medium |
| Unlimited Token Approval | 9 | - | ja | medium |
| Uninitialized Return Variable | 9 | - | nein | medium |
| Storage/Memory Data Inconsistency | 9 | - | nein | medium |
| Reentrancy | 8 | DASP-1 | nein | high |
| Denial of Service | 8 | DASP-5 | nein | medium |
| Assumption of Fixed-Length Array | 8 | - | nein | medium |
| Redundant Conditional Check | 7 | - | nein | low |
| Unhandled Partial Withdrawals on Migration | 6 | - | ja | medium |
| Integer Overflow / Underflow | 6 | DASP-3 | nein | high |
| Inconsistent Base Tokens on Migration | 6 | - | ja | medium |
| Authorization via tx.origin | 5 | DASP-2 | nein | medium |
| Unprotected Ownership Change | 4 | DASP-2 | nein | high |
| Strict Balance Equality (this.balance ==) | 4 | - | nein | low |
| Funding-Rate Calculation Precision | 3 | - | ja | medium |
| Unimplemented Interface Function | 2 | - | nein | low |
| Inconsistent State Initialization Order | 2 | - | nein | medium |
| Incorrect Constructor Name (legacy syntax) | 1 | - | nein | high |
| Flash-Loan Fee Manipulation | 1 | - | ja | high |

## Findings je Contract

55 Contracts mit mindestens einem Finding, 41 ohne.

| Contract | Findings | Zustand |
|---|---:|---|
| 5_Vader | 16 | Findings gemeldet |
| 5_Pools | 15 | Findings gemeldet |
| 5_DAO | 14 | Findings gemeldet |
| 36_Auction | 13 | Findings gemeldet |
| 5_USDV | 13 | Findings gemeldet |
| 16_GasOracle | 12 | Findings gemeldet |
| 20_Synth | 12 | Findings gemeldet |
| 66_sYETIToken | 12 | Findings gemeldet |
| 24_SwappableYieldSource | 11 | Findings gemeldet |
| 28_PostAuctionLauncher | 11 | Findings gemeldet |
| 30_Controller | 11 | Findings gemeldet |
| 31_veCVXStrategy | 11 | Findings gemeldet |
| 39_VaultTracker | 10 | Findings gemeldet |
| 20_Pool | 9 | Findings gemeldet |
| 23_CompoundToNotionalV2 | 9 | Findings gemeldet |
| 23_NotionalV1ToNotionalV2 | 9 | Findings gemeldet |
| 68_SingleTokenJoinV2 | 9 | Findings gemeldet |
| 83_Shelter | 9 | Findings gemeldet |
| 14_IdleYieldSource | 8 | Findings gemeldet |
| 46_WrappedIbbtcEth | 8 | Findings gemeldet |
| 69_NFTXSimpleFeeDistributor | 8 | Findings gemeldet |
| 71_PoolTemplate | 8 | Findings gemeldet |
| 83_MasterChef | 8 | Findings gemeldet |
| 107_yVault | 7 | Findings gemeldet |
| 12_Cauldron | 7 | Findings gemeldet |
| 14_SushiYieldSource | 7 | Findings gemeldet |
| 192_Position | 7 | Findings gemeldet |
| 28_SushiToken | 7 | Findings gemeldet |
| 45_CreditLimitByMedian | 7 | Findings gemeldet |
| 5_Vether | 7 | Findings gemeldet |
| 71_Vault | 7 | Findings gemeldet |
| 17_Buoy3Pool | 6 | Findings gemeldet |
| 17_PnL | 6 | Findings gemeldet |
| 18_LendingPair | 6 | Findings gemeldet |
| 69_NFTXMarketplaceZap | 6 | Findings gemeldet |
| 8_NFTXEligiblityManager | 6 | Findings gemeldet |
| 12_AccessControl | 5 | Findings gemeldet |
| 17_Exposure | 5 | Findings gemeldet |
| 25_CompoundMultiOracle | 5 | Findings gemeldet |
| 32_LendingPair | 5 | Findings gemeldet |
| 37_TempusController | 5 | Findings gemeldet |
| 38_Identity | 5 | Findings gemeldet |
| 64_TwabRewards | 5 | Findings gemeldet |
| 6_Beebots | 5 | Findings gemeldet |
| 70_LiquidityBasedTWAP | 5 | Findings gemeldet |
| 83_ConvexStakingWrapper | 5 | Findings gemeldet |
| 193_Pair | 4 | Findings gemeldet |
| 19_TransactionManager | 4 | Findings gemeldet |
| 29_IndexPool | 4 | Findings gemeldet |
| 38_QuickAccManager | 4 | Findings gemeldet |
| 44_Swap | 4 | Findings gemeldet |
| 68_BasketFacet | 4 | Findings gemeldet |
| 83_StakingRewards | 4 | Findings gemeldet |
| 25_CTokenInterface | 2 | Findings gemeldet |
| 8_ERC20FlashMintUpgradeable | 2 | Findings gemeldet |
| 106_NFTLoanFacilitator | 0 | Kontext ueberschritten - NICHT analysiert |
| 10_Visor | 0 | Kontext ueberschritten - NICHT analysiert |
| 12_Witch | 0 | kein Report |
| 12_YieldMath | 0 | Kontext ueberschritten - NICHT analysiert |
| 13_RCFactory | 0 | Kontext ueberschritten - NICHT analysiert |
| 13_RCMarket | 0 | Kontext ueberschritten - NICHT analysiert |
| 13_RCOrderbook | 0 | Kontext ueberschritten - NICHT analysiert |
| 13_RCTreasury | 0 | Kontext ueberschritten - NICHT analysiert |
| 14_BadgerYieldSource | 0 | Kontext ueberschritten - NICHT analysiert |
| 14_PrizePool | 0 | Kontext ueberschritten - NICHT analysiert |
| 14_YieldSourcePrizePool | 0 | Kontext ueberschritten - NICHT analysiert |
| 16_Liquidation | 0 | Kontext ueberschritten - NICHT analysiert |
| 16_Pricing | 0 | Kontext ueberschritten - NICHT analysiert |
| 16_TracerPerpetualSwaps | 0 | Kontext ueberschritten - NICHT analysiert |
| 16_TracerPerpetualsFactory | 0 | Kontext ueberschritten - NICHT analysiert |
| 16_Trader | 0 | Kontext ueberschritten - NICHT analysiert |
| 22_LongShort | 0 | Kontext ueberschritten - NICHT analysiert |
| 22_Staker | 0 | Kontext ueberschritten - NICHT analysiert |
| 23_nTokenAction | 0 | Kontext ueberschritten - NICHT analysiert |
| 25_CompositeMultiOracle | 0 | kein Report |
| 26_RCOrderbook | 0 | Kontext ueberschritten - NICHT analysiert |
| 29_HybridPool | 0 | Kontext ueberschritten - NICHT analysiert |
| 30_Vault | 0 | Kontext ueberschritten - NICHT analysiert |
| 34_ConcentratedLiquidityPool | 0 | Kontext ueberschritten - NICHT analysiert |
| 34_ConcentratedLiquidityPosition | 0 | Kontext ueberschritten - NICHT analysiert |
| 36_Basket | 0 | Kontext ueberschritten - NICHT analysiert |
| 3_MarginRouter | 0 | Kontext ueberschritten - NICHT analysiert |
| 43_DelegatedStaking | 0 | kein Report |
| 58_UniV3Vault | 0 | Kontext ueberschritten - NICHT analysiert |
| 5_Router | 0 | Kontext ueberschritten - NICHT analysiert |
| 62_Locke | 0 | kein Report |
| 66_StabilityPool | 0 | Kontext ueberschritten - NICHT analysiert |
| 67_Vault | 0 | Kontext ueberschritten - NICHT analysiert |
| 69_NFTXStakingZap | 0 | Kontext ueberschritten - NICHT analysiert |
| 70_VaderPoolV2 | 0 | Kontext ueberschritten - NICHT analysiert |
| 71_IndexTemplate | 0 | Kontext ueberschritten - NICHT analysiert |
| 74_TimeswapPair | 0 | Kontext ueberschritten - NICHT analysiert |
| 75_XDEFIDistribution | 0 | Kontext ueberschritten - NICHT analysiert |
| 78_FlanBackstop | 0 | Kontext ueberschritten - NICHT analysiert |
| 78_FlashGovernanceArbiter | 0 | Kontext ueberschritten - NICHT analysiert |
| 8_NFTXVaultUpgradeable | 0 | Kontext ueberschritten - NICHT analysiert |

## Aufwand

- LLM-Calls: 2481
- Prompt-Tokens: 52824882
- Completion-Tokens: 8662310
- Kosten geschaetzt: $8.00 (Estimated from token counts; the tool reports $0.0000 because chatdev/statistics.py::prompt_cost has no entry for deepseek-v4-flash. Authoritative figure: DeepSeek invoice.)
- Summe Task-Laufzeit: 88440 s

## Nicht vom Werkzeug geliefert

`function`, `lines`, `severity`, `confidence` sind in findings.jsonl `null`.
Das Werkzeug liest Quelltext als Text und meldet weder Positionen noch
Schweregrade. `severity_doc` traegt den dokumentationsseitigen Default aus
findings.yaml und ist kein Urteil des Modells.
