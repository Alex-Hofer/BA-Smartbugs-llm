# GPTScan via SmartBugs — Live run summary

Backend: **deepseek / deepseek-v4-flash**  ·  Contracts: **15**

## Per contract

| Contract | Findings | Categories | LLM calls | Cost (USD) |
| --- | --- | --- | --- | --- |
| 107_yVault.sol | 1 | MWE-200 | 11 | 0.0022 |
| 16_Pricing.sol | 0 | — | 6 | 0.0010 |
| 30_Vault.sol | 1 | MWE-200 | 12 | 0.0020 |
| 32_LendingPair.sol | 3 | MWE-200 | 89 | 0.0186 |
| 44_Swap.sol | 0 | — | 3 | 0.0003 |
| 64_TwabRewards.sol | 0 | — | 4 | 0.0005 |
| 70_LiquidityBasedTWAP.sol | 1 | MWE-200 | 20 | 0.0034 |
| 74_TimeswapPair.sol | 0 | — | 6 | 0.0015 |
| 83_StakingRewards.sol | 0 | — | 4 | 0.0004 |
| BitCash.sol | 0 | — | 4 | 0.0002 |
| HotDollarsToken.sol | 0 | — | 0 | 0.0000 |
| ProofOfExistence.sol | 0 | — | 1 | 0.0001 |
| StableDEX.sol | 0 | — | 0 | 0.0000 |
| Uniswap.sol | 0 | — | 0 | 0.0000 |
| WETH9.sol | 0 | — | 2 | 0.0001 |
| **Total** | **6** | | **162** | **0.0304** |

## Findings per category

| Category (MWE) | Taxonomy | Count |
| --- | --- | --- |
| MWE-200: Insecure LP Token Value Calculation | BUSINESS-LOGIC (no SWC/DASP) | 6 |

## Totals

- Contracts scanned: **15**
- Findings: **6**
- LLM calls: **162**
- Tokens sent / received: **56867 / 80039**
- Estimated cost: **$0.0304**
