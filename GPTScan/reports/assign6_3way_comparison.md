# Mythril vs. LLMSmartAudit vs. GPTScan — SmartBugs-curated (N=10)

Reference: SmartBugs-curated, exactly one labeled DASP vulnerability per contract. Mythril and LLMSmartAudit columns are taken verbatim from the BA validation PDFs (*Assigment_6* / *comparison_side_by_side*); the GPTScan column is a live DeepSeek (deepseek-v4-flash) run via the SmartBugs integration. *Findings* = total reported points; *Hit* = the tool flagged the one labeled vulnerability (strict SmartBugs definition).

## Table 1 — Detection per contract

| Contract | DASP category | Labeled vulnerability | Mythril Hit | Mythril # | LLMAudit Hit | LLMAudit # | GPTScan Hit | GPTScan # |
|---|---|---|:---:|--:|:---:|--:|:---:|--:|
| BecToken.sol | arithmetic | Integer Overflow / Underflow | NO | 0 | YES | 16 | NO | 0 |
| ERC20.sol | front_running | Front-Running (TOD) | NO | 0 | YES | 6 | NO | 0 |
| EtherLotto.sol | time_manipulation | Timestamp-Abhaengigkeit | YES | 4 | YES | 16 | NO | 0 |
| Government.sol | denial_of_service | Denial of Service | NO | 3 | YES | 22 | NO | 0 |
| MyToken.sol | short_addresses | Short Address | NO | 0 | NO | 7 | NO | 0 |
| OpenAddressLottery.sol | other | Manipulierbarer Zufalls-Seed | NO | 0 | YES | 27 | NO | 0 |
| ReturnValue.sol | unchecked_low_level_calls | Unchecked Low-level Call | YES | 2 | YES | 4 | NO | 0 |
| Rubixi.sol | access_control | Access Control (offener Konstruktor) | NO | 1 | YES | 21 | NO | 0 |
| SimpleDAO.sol | reentrancy | Reentrancy | YES | 4 | YES | 9 | NO | 0 |
| SmartBillions.sol | bad_randomness | Schwache Zufallsquelle | NO | 0 | YES | 30 | NO | 0 |

## Table 2 — Validation metrics (strict: only the labeled gap counts as correct)

| Metric | Mythril | LLMSmartAudit | GPTScan |
|---|--:|--:|--:|
| Detected gaps (True Positives) | 3 | 9 | 0 |
| Missed gaps (False Negatives) | 7 | 1 | 10 |
| Findings total | 14 | 158 | 0 |
| Noise findings (False Positives) | 11 | 149 | 0 |
| Recall | 30.0% | 90.0% | 0.0% |
| Precision | 21.4% | 5.7% | n/a* |
| F1-Score | 25.0% | 10.7% | n/a* |
| Avg noise / contract | 1.1 | 14.9 | 0.0 |

*\* Precision and F1 are undefined for GPTScan on this set: it reports **zero** findings (TP+FP = 0), so `TP/(TP+FP)` is 0/0 — undefined, not 0%. It makes no wrong predictions; it simply makes none here.*

## Table 3 — Specific findings per tool

| Contract | Mythril findings | LLMAudit findings | GPTScan findings |
|---|---|---|---|
| BecToken.sol | — | Centralization Risk \| Denial of Service \| Gas-Limit / Unbounded Operation \| Inconsistent State Initialization Order \| Incorrect Constructor Name (legacy syntax) \| Inheritance Initialization Order / Diamond \| Integer Overflow / Underflow \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Fallback Function (rejected/locked ether) \| Missing Withdrawal Function (locked funds) \| Missing onlyOwner Modifier \| Precision Loss / Integer-Division Truncation \| Redundant Conditional Check \| Unnecessary Boolean Comparison \| Unprotected Ownership Change | — |
| ERC20.sol | — | Lack of Input Validation \| Missing Access Control / Authorization \| Missing Withdrawal Function (locked funds) \| Redundant Conditional Check \| Transaction Order Dependence (front-running) \| Unprotected Ownership Change | — |
| EtherLotto.sol | Dependence on predictable environment variable (SWC 116) \| Exception State (SWC 110) \| Multiple Calls in a Single Transaction (SWC 113) \| Transaction Order Dependence (SWC 114) | Centralization Risk \| Denial of Service \| Gas-Limit / Unbounded Operation \| Incorrect Constructor Name (legacy syntax) \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Withdrawal Function (locked funds) \| Missing onlyOwner Modifier \| Predictable / Weak Randomness \| Reentrancy \| Storage/Memory Data Inconsistency \| Timestamp Dependence \| Transaction Order Dependence (front-running) \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) \| Unprotected Ownership Change | — |
| Government.sol | Dependence on predictable environment variable (SWC 116) \| Exception State (SWC 110) \| Unchecked return value from external call. (SWC 104) | Assumption of Fixed-Length Array \| Centralization Risk \| Denial of Service \| Gas-Limit / Unbounded Operation \| Inconsistent State Initialization Order \| Incorrect Constructor Name (legacy syntax) \| Integer Overflow / Underflow \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Fallback Function (rejected/locked ether) \| Missing Withdrawal Function (locked funds) \| Missing onlyOwner Modifier \| Precision Loss / Integer-Division Truncation \| Redundant Conditional Check \| Reentrancy \| Storage/Memory Data Inconsistency \| Strict Balance Equality (this.balance ==) \| Timestamp Dependence \| Transaction Order Dependence (front-running) \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) \| Unprotected Ownership Change | — |
| MyToken.sol | — | Authorization via tx.origin \| Incorrect Constructor Name (legacy syntax) \| Integer Overflow / Underflow \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Withdrawal Function (locked funds) \| Unnecessary Boolean Comparison | — |
| OpenAddressLottery.sol | — | Assumption of Fixed-Length Array \| Centralization Risk \| Denial of Service \| Gas-Limit / Unbounded Operation \| Hash Collision via abi.encodePacked \| Inconsistent State Initialization Order \| Incorrect Constructor Name (legacy syntax) \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Fallback Function (rejected/locked ether) \| Missing Withdrawal Function (locked funds) \| Missing onlyOwner Modifier \| Precision Loss / Integer-Division Truncation \| Predictable / Weak Randomness \| Price Manipulation (centralized pricing) \| Redundant Conditional Check \| Reentrancy \| Single External Oracle Dependency \| Storage/Memory Data Inconsistency \| Strict Balance Equality (this.balance ==) \| Timestamp Dependence \| Transaction Order Dependence (front-running) \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) \| Uninitialized Return Variable \| Unnecessary Boolean Comparison \| Unprotected Ownership Change | — |
| ReturnValue.sol | External Call To User-Supplied Address (SWC 107) \| Unchecked return value from external call. (SWC 104) | Lack of Input Validation \| Missing Withdrawal Function (locked funds) \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) | — |
| Rubixi.sol | Exception State (SWC 110) | Assumption of Fixed-Length Array \| Centralization Risk \| Denial of Service \| Gas-Limit / Unbounded Operation \| Inconsistent State Initialization Order \| Incorrect Constructor Name (legacy syntax) \| Integer Overflow / Underflow \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Fallback Function (rejected/locked ether) \| Missing Withdrawal Function (locked funds) \| Missing onlyOwner Modifier \| Precision Loss / Integer-Division Truncation \| Price Manipulation (centralized pricing) \| Redundant Conditional Check \| Reentrancy \| Storage/Memory Data Inconsistency \| Transaction Order Dependence (front-running) \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) \| Unprotected Ownership Change | — |
| SimpleDAO.sol | External Call To User-Supplied Address (SWC 107) \| State access after external call (SWC 107) \| Unchecked return value from external call. (SWC 104) \| Unprotected Ether Withdrawal (SWC 105) | Denial of Service \| Gas-Limit / Unbounded Operation \| Lack of Input Validation \| Missing Withdrawal Function (locked funds) \| Reentrancy \| Storage/Memory Data Inconsistency \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) \| Unprotected Ownership Change | — |
| SmartBillions.sol | — | Assumption of Fixed-Length Array \| Centralization Risk \| Denial of Service \| Gas-Limit / Unbounded Operation \| Hash Collision via abi.encodePacked \| Inconsistent State Initialization Order \| Incorrect Constructor Name (legacy syntax) \| Inheritance Initialization Order / Diamond \| Integer Overflow / Underflow \| Lack of Input Validation \| Missing Access Control / Authorization \| Missing Fallback Function (rejected/locked ether) \| Missing Withdrawal Function (locked funds) \| Missing onlyOwner Modifier \| Precision Loss / Integer-Division Truncation \| Predictable / Weak Randomness \| Price Manipulation (centralized pricing) \| Redundant Conditional Check \| Reentrancy \| Single External Oracle Dependency \| Storage/Memory Data Inconsistency \| Strict Balance Equality (this.balance ==) \| Timestamp Dependence \| Transaction Order Dependence (front-running) \| Unchecked External Call (send/transfer/ERC20 return) \| Unchecked Low-level Call (call/delegatecall/send) \| Unimplemented Interface Function \| Uninitialized Return Variable \| Unnecessary Boolean Comparison \| Unprotected Ownership Change | — |

## How to read the GPTScan result

GPTScan detects **10 DeFi logic-vulnerability types (MWE-200..209)**. None of the ten SmartBugs-curated labeled bugs (integer overflow, timestamp, DoS, short-address, weak randomness, unchecked call, access control, reentrancy, weak seed) fall inside those detectors, so a low recall here is **by design** — this benchmark measures GPTScan's *scope*, not its capability.

**Important caveat on the run.** GPTScan's function-extraction parser (a bundled ANTLR Solidity grammar) rejects legacy `constant`/`var` syntax, so the original SmartBugs 0.4.x sources yield mostly parse errors. This table therefore runs GPTScan on the **SmartBugs 0.6.12 ports** of the same ten contracts (identical contracts + labeled vulnerabilities; Mythril/LLMSmartAudit values remain the 0.4.x reference figures from the PDFs). Run: deepseek-v4-flash, **17 LLM calls, $0.0027**.

Even on the 0.6.12 ports GPTScan reports **0 findings on all 10**, but the zero is now genuine, not a parse artifact:

- **BecToken.sol** — evaluated, no DeFi-logic scenario matched
- **ERC20.sol** — not analyzable (parser rejected the file)
- **EtherLotto.sol** — evaluated, no DeFi-logic scenario matched
- **Government.sol** — evaluated by LLM, rejected at static-confirmation
- **MyToken.sol** — evaluated, no DeFi-logic scenario matched
- **OpenAddressLottery.sol** — evaluated by LLM, rejected at static-confirmation
- **ReturnValue.sol** — not analyzable (0 functions extracted)
- **Rubixi.sol** — evaluated, no DeFi-logic scenario matched
- **SimpleDAO.sol** — not analyzable (0 functions extracted)
- **SmartBillions.sol** — evaluated by LLM, rejected at static-confirmation

So **7/10 were genuinely analyzed** (functions extracted); three of those — Government.sol, OpenAddressLottery.sol, SmartBillions.sol — even reached the LLM, whose candidates GPTScan's static-confirmation stage then rejected (→ 0 findings, 0 false positives). The remaining 3 (ERC20.sol, ReturnValue.sol, SimpleDAO.sol) could not be analyzed at all (GPTScan's parser could not extract their functions). Net: Mythril is precise-but-narrow, LLMSmartAudit is exhaustive-but-noisy, and GPTScan is a specialised DeFi-logic tool that is simply out of scope on this classic benchmark — silent *and* clean where it runs, and unable to parse three legacy contracts.
