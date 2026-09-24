# llmsa_mwefixed_v2_ctx1m

Erzeugt 2026-09-24T21:40:08+00:00 aus `smartbugs/results/llmsmartaudit/llmsa_mwefixed_v2_ctx1m`.
Backend deepseek/deepseek-v4-flash, Modus SmartContractTA (fixed in scripts/do_solidity.sh), MAIN=0.

## Zustaende

| Zustand | Contracts | Anteil |
|---|---:|---:|
| Findings gemeldet | 37 | 100.0 % |

Die Zeile *Kontext ueberschritten* ist kein Ergebnis. Diese Contracts
wurden nie analysiert; sie duerfen weder als 'clean' noch in einer
Precision-Rechnung auftauchen.

## Findings je Kategorie

| Kategorie | Findings | DASP | DeFi-Logik | Severity (aus findings.yaml) |
|---|---:|---|---|---|
| Centralization Risk | 29 | DASP-2 | nein | medium |
| Gas-Limit / Unbounded Operation | 26 | DASP-5 | nein | medium |
| Precision Loss / Integer-Division Truncation | 22 | - | nein | medium |
| Timestamp Dependence | 21 | DASP-8 | nein | low |
| Single External Oracle Dependency | 20 | - | ja | medium |
| Unchecked External Call (send/transfer/ERC20 return) | 18 | DASP-4 | nein | medium |
| Unchecked Low-level Call (call/delegatecall/send) | 15 | DASP-4 | nein | medium |
| Transaction Order Dependence (front-running) | 13 | DASP-7 | nein | medium |
| Missing Withdrawal Function (locked funds) | 12 | - | nein | medium |
| Reentrancy | 12 | DASP-1 | nein | high |
| Assumption of Fixed-Length Array | 10 | - | nein | medium |
| Missing onlyOwner Modifier | 10 | DASP-2 | nein | high |
| Price Manipulation (centralized pricing) | 9 | - | ja | high |
| Denial of Service | 9 | DASP-5 | nein | medium |
| Missing Access Control / Authorization | 9 | DASP-2 | nein | high |
| Inconsistent State Initialization Order | 8 | - | nein | medium |
| Funding-Rate Calculation Precision | 7 | - | ja | medium |
| Redundant Conditional Check | 6 | - | nein | low |
| Unlimited Token Approval | 6 | - | ja | medium |
| Lack of Input Validation | 6 | - | nein | medium |
| Integer Overflow / Underflow | 6 | DASP-3 | nein | high |
| Uninitialized Return Variable | 5 | - | nein | medium |
| Yield-Source Swap Token Mismatch | 5 | - | ja | medium |
| Storage/Memory Data Inconsistency | 5 | - | nein | medium |
| Unnecessary Boolean Comparison | 5 | - | nein | low |
| Unhandled Partial Withdrawals on Migration | 4 | - | ja | medium |
| Missing Fallback Function (rejected/locked ether) | 4 | - | nein | low |
| Unimplemented Interface Function | 3 | - | nein | low |
| Inconsistent Base Tokens on Migration | 3 | - | ja | medium |
| Authorization via tx.origin | 3 | DASP-2 | nein | medium |
| Unprotected Ownership Change | 2 | DASP-2 | nein | high |
| Strict Balance Equality (this.balance ==) | 2 | - | nein | low |
| Incorrect Signature / Signer Verification | 1 | - | nein | high |
| Predictable / Weak Randomness | 1 | DASP-6 | nein | medium |

## Findings je Contract

37 Contracts mit mindestens einem Finding, 0 ohne.

| Contract | Findings | Zustand |
|---|---:|---|
| 71_IndexTemplate | 19 | Findings gemeldet |
| 5_Router | 18 | Findings gemeldet |
| 13_RCTreasury | 13 | Findings gemeldet |
| 36_Basket | 13 | Findings gemeldet |
| 58_UniV3Vault | 12 | Findings gemeldet |
| 78_FlashGovernanceArbiter | 12 | Findings gemeldet |
| 67_Vault | 11 | Findings gemeldet |
| 78_FlanBackstop | 11 | Findings gemeldet |
| 13_RCFactory | 10 | Findings gemeldet |
| 16_Trader | 10 | Findings gemeldet |
| 30_Vault | 10 | Findings gemeldet |
| 10_Visor | 9 | Findings gemeldet |
| 13_RCMarket | 9 | Findings gemeldet |
| 22_LongShort | 9 | Findings gemeldet |
| 22_Staker | 9 | Findings gemeldet |
| 23_nTokenAction | 9 | Findings gemeldet |
| 3_MarginRouter | 9 | Findings gemeldet |
| 69_NFTXStakingZap | 9 | Findings gemeldet |
| 8_NFTXVaultUpgradeable | 9 | Findings gemeldet |
| 13_RCOrderbook | 8 | Findings gemeldet |
| 16_TracerPerpetualSwaps | 8 | Findings gemeldet |
| 14_BadgerYieldSource | 7 | Findings gemeldet |
| 16_Pricing | 7 | Findings gemeldet |
| 26_RCOrderbook | 7 | Findings gemeldet |
| 34_ConcentratedLiquidityPosition | 7 | Findings gemeldet |
| 70_VaderPoolV2 | 7 | Findings gemeldet |
| 75_XDEFIDistribution | 7 | Findings gemeldet |
| 14_PrizePool | 6 | Findings gemeldet |
| 16_Liquidation | 6 | Findings gemeldet |
| 16_TracerPerpetualsFactory | 6 | Findings gemeldet |
| 29_HybridPool | 6 | Findings gemeldet |
| 66_StabilityPool | 6 | Findings gemeldet |
| 14_YieldSourcePrizePool | 5 | Findings gemeldet |
| 106_NFTLoanFacilitator | 4 | Findings gemeldet |
| 74_TimeswapPair | 4 | Findings gemeldet |
| 34_ConcentratedLiquidityPool | 3 | Findings gemeldet |
| 12_YieldMath | 2 | Findings gemeldet |

## Aufwand

- LLM-Calls: 1625
- Prompt-Tokens: 100250727
- Completion-Tokens: 6267999
- Kosten geschaetzt: $11.42 (Estimated from token counts; the tool reports $0.0000 because chatdev/statistics.py::prompt_cost has no entry for deepseek-v4-flash. Authoritative figure: DeepSeek invoice.)
- Summe Task-Laufzeit: 35028 s

## Nicht vom Werkzeug geliefert

`function`, `lines`, `severity`, `confidence` sind in findings.jsonl `null`.
Das Werkzeug liest Quelltext als Text und meldet weder Positionen noch
Schweregrade. `severity_doc` traegt den dokumentationsseitigen Default aus
findings.yaml und ist kein Urteil des Modells.
