# curated_v1_20260705 -- llmsmartaudit

Erzeugt 2026-09-20T14:16:00+00:00 aus `smartbugs/results/llmsmartaudit/curated_v1_20260705` durch `analysis_tools/curated_eval.py`.
Backend deepseek/deepseek-v4-flash, Timeout 5400 s, MAIN=0.

## Zustaende

| Zustand | Contracts | Anteil |
|---|---:|---:|
| Findings gemeldet | 143 | 100.0 % |

Nur der Zustand *keine Findings* ist ein Ergebnis. Ein Contract, der nicht
uebersetzt wurde oder den Kontext sprengte, darf weder als sauber gelten
noch in eine Precision-Rechnung eingehen.

## Recall / Precision / F1 je DASP-Kategorie

| Kategorie | Contracts | Erkannt | Recall | Geflaggt | Precision | F1 |
|---|---:|---:|---:|---:|---:|---:|
| access_control | 18 | 18 | 100 % | 94 | 19 % | 32 % |
| arithmetic | 15 | 15 | 100 % | 75 | 20 % | 33 % |
| bad_randomness | 8 | 7 | 88 % | 16 | 44 % | 58 % |
| denial_of_service | 6 | 6 | 100 % | 77 | 8 % | 14 % |
| front_running | 4 | 4 | 100 % | 45 | 9 % | 16 % |
| other | 3 | 0 | 0 % | 0 | – | – |
| reentrancy | 31 | 31 | 100 % | 72 | 43 % | 60 % |
| short_addresses | 1 | 0 | 0 % | 0 | – | – |
| time_manipulation | 5 | 5 | 100 % | 19 | 26 % | 42 % |
| unchecked_low_level_calls | 52 | 52 | 100 % | 66 | 79 % | 88 % |
| **GESAMT** | **143** | **138** | **97 %** | **464** | **30 %** | **45 %** |

468 der 1 124 Findings tragen keine DASP-Klassifikation und gehen weder in
Recall noch in Precision ein.

## Findings je Kategorie

| Kategorie | Findings | DASP | Severity (aus findings.yaml) |
|---|---:|---|---|
| Missing Withdrawal Function (locked funds) | 112 | - | medium |
| Lack of Input Validation | 107 | - | medium |
| Storage/Memory Data Inconsistency | 84 | - | medium |
| Integer Overflow / Underflow | 75 | DASP-3 | high |
| Reentrancy | 72 | DASP-1 | high |
| Denial of Service | 69 | DASP-5 | medium |
| Unchecked External Call (send/transfer/ERC20 return) | 65 | DASP-4 | medium |
| Centralization Risk | 64 | DASP-2 | medium |
| Missing Access Control / Authorization | 63 | DASP-2 | high |
| Unchecked Low-level Call (call/delegatecall/send) | 63 | DASP-4 | medium |
| Missing Fallback Function (rejected/locked ether) | 47 | - | low |
| Transaction Order Dependence (front-running) | 45 | DASP-7 | medium |
| Missing onlyOwner Modifier | 41 | DASP-2 | high |
| Gas-Limit / Unbounded Operation | 35 | DASP-5 | medium |
| Incorrect Constructor Name (legacy syntax) | 28 | - | high |
| Timestamp Dependence | 19 | DASP-8 | low |
| Redundant Conditional Check | 17 | - | low |
| Unprotected Ownership Change | 17 | DASP-2 | high |
| Precision Loss / Integer-Division Truncation | 16 | - | medium |
| Predictable / Weak Randomness | 16 | DASP-6 | medium |
| Assumption of Fixed-Length Array | 12 | - | medium |
| Unnecessary Boolean Comparison | 9 | - | low |
| Authorization via tx.origin | 8 | DASP-2 | medium |
| Price Manipulation (centralized pricing) | 8 | - | high |
| Uninitialized Return Variable | 7 | - | medium |
| Single External Oracle Dependency | 6 | - | medium |
| Unprotected SELFDESTRUCT | 4 | DASP-2 | high |
| Inconsistent State Initialization Order | 4 | - | medium |
| Strict Balance Equality (this.balance ==) | 3 | - | low |
| Inheritance Initialization Order / Diamond | 2 | - | medium |
| Unhandled Partial Withdrawals on Migration | 2 | - | medium |
| Unlimited Token Approval | 1 | - | medium |
| Incorrect Signature / Signer Verification | 1 | - | high |
| Inconsistent Base Tokens on Migration | 1 | - | medium |
| Funding-Rate Calculation Precision | 1 | - | medium |

## Findings je Contract

Mittel 7.9, Median 7, Maximum 18, Contracts ohne Findings 0.

| Contract | Kategorie (Label) | Findings | Zustand |
|---|---|---:|---|
| rubixi | access_control | 18 | findings |
| 0x663e4229142a27f00bafb5d087e1e730648314c3 | unchecked_low_level_calls | 18 | findings |
| 0x19cf8481ea15427a98ba3cdd6d9e14690011ab10 | unchecked_low_level_calls | 16 | findings |
| 0xb620cee6b52f96f3c6b253e6eea556aa2d214a99 | unchecked_low_level_calls | 16 | findings |
| list_dos | denial_of_service | 15 | findings |
| 0x7d09edb07d23acb532a82be3da5c17d9d85806b4 | unchecked_low_level_calls | 15 | findings |
| 0xb11b2fed6c9354f7aa2f658d3b4d7b31d8a13b77 | unchecked_low_level_calls | 15 | findings |
| parity_wallet_bug_1 | access_control | 14 | findings |
| parity_wallet_bug_2 | access_control | 14 | findings |
| 0xbaa3de6504690efb064420d89e871c27065cdd52 | unchecked_low_level_calls | 14 | findings |
| 0xbebbfe5b549f5db6e6c78ca97cac19d1fb03082c | unchecked_low_level_calls | 14 | findings |
| 0xe09b1ab8111c2729a76f16de96bc86a7af837928 | unchecked_low_level_calls | 14 | findings |
| lucky_doubler | bad_randomness | 13 | findings |
| 0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839 | reentrancy | 13 | findings |
| spank_chain_payment | reentrancy | 13 | findings |

