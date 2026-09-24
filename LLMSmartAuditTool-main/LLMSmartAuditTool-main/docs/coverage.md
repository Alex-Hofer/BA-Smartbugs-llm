# LLMSmartAudit — Vulnerability Coverage & Test Scope

This document describes which weakness classes LLMSmartAudit actually probes, modelled on the
structure Mythril uses for its detector documentation
(`smartbugs/tools/mythril-0.24.8/findings.yaml`: *classification → method → severity*). It is
derived from the real analysis code, not from the tool's marketing name — specifically from the
detector phases listed in `CompanyConfig/SmartContractTA/ChatChainConfig.json` and their prompts
in `CompanyConfig/SmartContractTA/PhaseConfig.json`.

The machine-readable source of truth for this table is `chatdev/audit_report.py::DETECTORS`;
this file is the human-facing companion and is kept consistent with it.

## How the tool actually works (read this first)

LLMSmartAudit is **not** a symbolic-execution or bytecode scanner. It is a ChatDev/CAMEL
multi-agent **LLM** pipeline. A contract's *source code* is passed as the `--task` argument and a
team of role-playing agents (Security Analyst, Solidity Expert, …) runs a fixed chain of
single-shot "detector" prompts, each focused on one weakness class, followed by a consolidating
summary phase.

Consequences for coverage interpretation:

- **No 1:1 SWC/DASP mapping.** Many detectors target *logic / DeFi-level* weaknesses (price
  manipulation, oracle dependency, flash-loan fee manipulation, yield-source/token-migration
  consistency) that have **no clean SWC or DASP-10 classification**. This mirrors the documented
  GPTScan finding (`Beachlor/GPTScan-SmartBugs-Integration.md`): an LLM scanner's real strength is
  scenario/logic reasoning, not classic bytecode-pattern coverage. Where a clean mapping exists it
  is given below; where it does not, the entry is honestly labelled `logic/DeFi (no standard SWC)`.
- **The name oversells classic-SWC coverage.** Several "detectors" are really code-quality or
  style probes (e.g. *Unnecessary Boolean Comparison*, *Misuse of Mapping Getter*, *Redundant
  Conditional Check*) rather than security-critical SWC patterns.
- **Severities are documentation-assigned defaults**, not tool output. The prompts ask only for a
  *VULNERABILITY NAME/TYPE* and a free-text description; they do **not** emit a severity, SWC id,
  or line number. The severity column below is a sensible default per category (used by the
  generated Markdown report) — treat it as guidance, not a tool verdict.
- **Findings are free-text and non-deterministic.** Output rarely contains exact line numbers; it
  references functions/patterns in prose. Re-runs and different providers (OpenAI vs DeepSeek) can
  yield different results.
- **Detection signal.** A category is reported as a finding when its phase concludes
  `<INFO> … Identified.` (or the one `Identify.` typo) and not the templated negative `<INFO> NO …`.

## Two analysis modes

| Config (`--config`) | Purpose | Coverage |
|---|---|---|
| `SmartContractTA` | Technical Analysis — the 41 single-purpose detectors documented below | This document |
| `SmartContractBA` | Business Analysis — holistic, free-form contract review (no fixed detector list) | Out of scope here; produces narrative output, not categorized findings |

## Coverage table (SmartContractTA, 41 detectors)

Order matches the execution chain. `Classification` uses `(approx.)` where the mapping is a close
analogue rather than an exact match.

| # | Detector (phase) | Category | Classification | Severity* | What it checks (method) |
|---|---|---|---|---|---|
| 1 | ArithmeticDetector | Integer Overflow / Underflow | SWC-101, DASP-3 | High | Arithmetic that can exceed type bounds; missing/incomplete SafeMath usage |
| 2 | ReentrancyDetector | Reentrancy | SWC-107, DASP-1 | High | External call before state update; missing Checks-Effects-Interactions / ReentrancyGuard |
| 3 | UncheckedSendDetector | Unchecked External Call | SWC-104, DASP-4 | Medium | Return value of send/transfer and ERC20 transfer/transferFrom not checked |
| 4 | UncheckedLowLevelCallDetector | Unchecked Low-level Call | SWC-104, DASP-4 | Medium | `call`/`delegatecall`/`send` results unchecked; untrusted callee behaviour |
| 5 | TODDetector | Transaction Order Dependence | SWC-114, DASP-7 | Medium | Behaviour depends on tx ordering / gas-price-driven sequencing (front-running) |
| 6 | TimeStampManipulationDetector | Timestamp Dependence | SWC-116, DASP-8 | Low | Critical logic/randomness based on `block.timestamp`/`now` |
| 7 | PredictableRandDetector | Predictable / Weak Randomness | SWC-120, DASP-6 | Medium | Randomness from `blockhash`/`block.number` (miner-predictable) |
| 8 | TXRelianceDetector | Authorization via tx.origin | SWC-115, DASP-2 | Medium | `tx.origin` used for access control / ownership checks |
| 9 | SuicideDetector | Unprotected SELFDESTRUCT | SWC-106, DASP-2 | High | `selfdestruct`/`suicide` reachable without strong access control |
| 10 | GasLimitDetector | Gas-Limit / Unbounded Operation | SWC-128, DASP-5 | Medium | Unbounded loops / missing gas considerations enabling DoS |
| 11 | PriceManipulationDetector | Price Manipulation (centralized pricing) | logic/DeFi (no standard SWC) | High | Token prices arbitrarily set by a central authority; no oracle/AMM/governance guard |
| 12 | DataCorruptionDetector | Assumption of Fixed-Length Array | logic (no standard SWC) | Medium | Code assumes a returned array has fixed length → corruption/out-of-bounds |
| 13 | WithdrawalFunctionDetector | Missing Withdrawal Function | logic (locked funds) | Medium | No secure way for users to withdraw deposited funds |
| 14 | LackAuthorizationDetector | Missing Access Control / Authorization | SWC-105 (approx.), DASP-2 | High | State-changing functions lack `onlyOwner`/role modifiers |
| 15 | DataInconsistencyDetector | Storage/Memory Data Inconsistency | logic (no standard SWC) | Medium | Wrong storage↔memory copy assumptions causing inconsistent data |
| 16 | HashCollisionDetector | Hash Collision via abi.encodePacked | SWC-133 | Medium | `abi.encodePacked` of dynamic args without delimiters → ambiguous hashes |
| 17 | UninitializedReturnVariableDetector | Uninitialized Return Variable | logic (SWC-109 family) | Medium | Declared return var never assigned → unpredictable return value |
| 18 | MisdeclaredConstructorDetector | Incorrect Constructor Name (legacy) | SWC-118 | High | Old-style constructor (function == contract name) treated as public fn |
| 19 | MissingOnlyOwnerDetector | Missing onlyOwner Modifier | DASP-2 (no specific SWC) | High | Owner-only operations callable by anyone (mint, transfer ownership, …) |
| 20 | MisuseMsgValueDetector | Misuse of msg.value in a Loop | logic (no standard SWC) | High | Full `msg.value` applied each loop iteration instead of split |
| 21 | PrecisionLossDetector | Precision Loss / Integer-Division Truncation | logic (arithmetic) | Medium | Integer division/precision loss in reward/proportional math |
| 22 | RedundantConditionalDetector | Redundant Conditional Check | code-quality (no standard SWC) | Low | Always-true/false or duplicated conditions; wasted gas |
| 23 | OracleDependencyDetector | Single External Oracle Dependency | logic/DeFi (no standard SWC) | Medium | Reliance on one oracle without fallback/validation |
| 24 | OwnershipHijackingDetector | Unprotected Ownership Change | DASP-2 (no specific SWC) | High | `changeOwner` callable by anyone (no auth check) |
| 25 | CentralizationRiskDetector | Centralization Risk | DASP-2 / governance (no standard SWC) | Medium | Critical ops gated on a single address; no multisig/decentralization |
| 26 | FundingCalculationDetector | Funding-Rate Calculation Precision | logic/DeFi (no standard SWC) | Medium | Simplistic/unvalidated funding-rate math (spotPrice/markPrice manipulation) |
| 27 | FlashLoanDetector | Flash-Loan Fee Manipulation | logic/DeFi (no standard SWC) | High | Flash-loan fee setter lacks access control |
| 28 | MappingGetterDetector | Misuse of Mapping Getter | code-quality (no standard SWC) | Low | `this.mapping(key)` instead of `mapping[key]` |
| 29 | GetterFunctionDetector | Unimplemented Interface Function | logic/compile (no standard SWC) | Low | Interface-declared functions not implemented |
| 30 | UnnecessaryComparisonDetector | Unnecessary Boolean Comparison | code-quality (no standard SWC) | Low | `x == true/false` instead of using the boolean directly |
| 31 | InconsistentInitializationDetector | Inconsistent State Initialization Order | logic (no standard SWC) | Medium | State var initialized from not-yet-initialized state |
| 32 | SourceSwappingDetector | Yield-Source Swap Token Mismatch | logic/DeFi (no standard SWC) | Medium | Yield source swapped without verifying deposit-token match |
| 33 | SignatureVerificationDetector | Incorrect Signature / Signer Verification | SWC-122 (approx.) | High | Recovered signer compared to `msg.sender` → any caller authorizes self |
| 34 | OrderInitializationDetector | Inheritance Initialization Order / Diamond | logic (SWC-125 family) | Medium | Linearized constructor order / diamond-problem init issues |
| 35 | ImpracticalityMatchDetector | Strict Balance Equality | SWC-132 | Low | `this.balance == target` exact checks (forced-send manipulation) |
| 36 | InconsistentTokensDetector | Inconsistent Base Tokens on Migration | logic/DeFi (no standard SWC) | Medium | Strategy migration without verifying base-token consistency |
| 37 | PartialWithdrawalsDetector | Unhandled Partial Withdrawals on Migration | logic/DeFi (no standard SWC) | Medium | Migration assumes full withdraw possible; partials leave funds behind |
| 38 | FallbackFunctionDetector | Missing Fallback Function | logic (no standard SWC) | Low | No payable fallback → ether transfers revert / funds locked |
| 39 | UnlimitedTokenDetector | Unlimited Token Approval | logic/DeFi (no standard SWC) | Medium | `approve`/`increaseAllowance` with `type(uint256).max` etc. |
| 40 | InputValidationDetector | Lack of Input Validation | SWC-123 (approx.) | Medium | Missing checks (zero address, bounds) on critical inputs |
| 41 | DoSDetector | Denial of Service | SWC-113 / SWC-128, DASP-5 | Medium | Unbounded loops, failing external calls, gas-griefing |

\* Documentation-assigned default severity (not emitted by the tool).

## Coverage mapped onto DASP-10

| DASP-10 category | Covered by detectors |
|---|---|
| 1. Reentrancy | ReentrancyDetector |
| 2. Access Control | TXReliance, Suicide, LackAuthorization, MissingOnlyOwner, OwnershipHijacking, Centralization (partial), FlashLoan |
| 3. Arithmetic | Arithmetic, PrecisionLoss (partial) |
| 4. Unchecked Return Values | UncheckedSend, UncheckedLowLevelCall |
| 5. Denial of Service | GasLimit, DoS |
| 6. Bad Randomness | PredictableRand |
| 7. Front-Running (TOD) | TODDetector |
| 8. Time Manipulation | TimeStampManipulation |
| 9. Short Address / Other | — (not specifically covered) |
| 10. Unknown Unknowns | The large logic/DeFi detector set (Price, Oracle, FlashLoan, FundingCalc, SourceSwapping, InconsistentTokens, PartialWithdrawals, UnlimitedToken, …) effectively targets this bucket |

Which classification actually enters the curated metric, why, and the two borderline cases
(`CentralizationRiskDetector` with DASP-2, `MisdeclaredConstructorDetector` without) are worked
out per detector in `smartbugs/tools/llmsmartaudit/mapping.md` (German, 2026-09-24). The table
above lists thematic coverage; `FlashLoanDetector` and `PrecisionLossDetector` appear there
without carrying a DASP number in `findings.yaml`.

**Gaps / honesty notes:**
- DASP-9 (short address / other) and several bytecode-level SWCs (delegatecall-to-user-address
  SWC-112, arbitrary jump SWC-127, arbitrary storage write SWC-124) are **not** covered — these
  are exactly what symbolic tools like Mythril find.
- A large share of detectors (≈ 20 of 41) carry **no standard SWC/DASP** and are logic/DeFi or
  code-quality probes. This is the tool's intended niche, not an oversight, but it means the
  coverage is **complementary to** rather than overlapping with classic scanners.

## Relationship to Mythril (comparison reference)

Mythril performs **symbolic execution over EVM bytecode** and reports a fixed SWC vocabulary
(see its `findings.yaml`). LLMSmartAudit performs **LLM reasoning over Solidity source**. They are
complementary:

- Mythril is strong on classic, machine-checkable SWC bug classes (SWC-101/104/106/107/110/116/…)
  with deterministic output.
- LLMSmartAudit is strong on logic/DeFi scenarios (price/oracle/flash-loan/migration consistency)
  that symbolic tools structurally cannot see, at the cost of non-determinism, cost-per-run, and
  possible hallucination/misses.

For the SmartBugs evaluation, picking the 10 test contracts across several DASP-10 categories lets
this coverage table be spot-checked: classic SWC contracts should surface in Mythril; logic/DeFi
contracts are where LLMSmartAudit is expected to add value.
