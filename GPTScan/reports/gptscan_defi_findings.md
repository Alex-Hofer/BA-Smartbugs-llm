# GPTScan — DeFi logic-vulnerability findings (variety run)

Live DeepSeek (deepseek-v4-flash) run via the SmartBugs integration over **27 DeFi contracts** (code4rena set, pre-selected by a dry-run to those whose functions match a GPTScan scenario). **8 contracts produced findings**, **11 findings total**, spanning **3 distinct MWE detector(s)**. Run cost: 246 LLM calls, $0.0447.

## Findings per MWE detector (the 'variety')

| MWE detector | # findings | contracts |
|---|--:|---|
| **MWE-200**: Insecure LP Token Value Calculation | 8 | 107_yVault, 14_BadgerYieldSource, 14_SushiYieldSource, 30_Vault, 32_LendingPair, 37_TempusController |
| **MWE-203**: Approval Not Revoked | 2 | 10_Visor |
| **MWE-209**: Wrong Order for Interest or ExchangeRate | 1 | 14_PrizePool |

## All findings

| Contract | MWE | Lines | Severity | Description |
|---|---|---|---|---|
| 107_yVault | MWE-200 | 102-106 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 14_BadgerYieldSource | MWE-200 | 21-26 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 14_SushiYieldSource | MWE-200 | 20-25 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 30_Vault | MWE-200 | 83-106 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 32_LendingPair | MWE-200 | 172-180 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 32_LendingPair | MWE-200 | 315-322 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 32_LendingPair | MWE-200 | 323-330 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 37_TempusController | MWE-200 | 80-93 | high | Liquidity token value/price can be manipulated to cause flashloan attacks. |
| 10_Visor | MWE-203 | 242-249 | high | Approval is not revoked or reset after the code functionality finishes. |
| 10_Visor | MWE-203 | 256-270 | high | Approval is not revoked or reset after the code functionality finishes. |
| 14_PrizePool | MWE-209 | 143-158 | high | Update of interest or exchange rate should be executed before calculating new balance, sha |

## Per-contract summary (only contracts with findings)

| Contract | #Findings | MWE types | LLM calls | Cost $ |
|---|--:|---|--:|--:|
| 32_LendingPair | 3 | MWE-200 | 76 | 0.0154 |
| 10_Visor | 2 | MWE-203 | 9 | 0.0009 |
| 107_yVault | 1 | MWE-200 | 9 | 0.0022 |
| 14_BadgerYieldSource | 1 | MWE-200 | 7 | 0.0017 |
| 14_PrizePool | 1 | MWE-209 | 25 | 0.0052 |
| 14_SushiYieldSource | 1 | MWE-200 | 7 | 0.0020 |
| 30_Vault | 1 | MWE-200 | 12 | 0.0017 |
| 37_TempusController | 1 | MWE-200 | 8 | 0.0012 |
