# LLMSmartAudit: Zuordnung der 41 Detektoren zu SWC und DASP, begründet

Stand 24.09.2026. Maschinenlesbar ist [`findings.yaml`](findings.yaml) in diesem
Verzeichnis (41 Einträge, erzeugt aus `chatdev/audit_report.py::DETECTORS`);
die englische Übersicht der Detektoren ist
[`docs/coverage.md`](../../../LLMSmartAuditTool-main/LLMSmartAuditTool-main/docs/coverage.md)
im Werkzeugbaum. Dieses Dokument tut für LLMSmartAudit, was
[`GPTScan/taxonomy/mapping.md`](../../../GPTScan/taxonomy/mapping.md) für
GPTScan tut: Es sagt je Detektor, **warum** er die Klassifikation trägt, die
er trägt, und belegt das am Prompt, den das Werkzeug tatsächlich stellt
(`CompanyConfig/SmartContractTA/PhaseConfig.json`, Feld `phase_prompt`).

**Das ist eine Begründung der bestehenden Zuordnung, keine Neuzuordnung.**
Keine Klassifikation in `findings.yaml` wurde geändert; die Kennzahlen des
curated-Laufs (`eval/curated_v1_20260705__llmsmartaudit/`: Recall 97 %,
Precision 30 %) bleiben, wie sie sind. Wo die Begründung nicht trägt, steht
das unten unter „Offene Punkte“, mit der Zahl, um die sich die Metrik bewegen
würde. `tests/test_llmsa_mapping_doc.py` prüft, dass die Tabellen hier und
`findings.yaml` nicht auseinanderlaufen.

## Die Regel

Die Auswertung (`evaluate_curated.py`, `analysis_tools/curated_eval.py`) liest
aus der Klassifikation nur die erste `DASP-n`-Nummer (`DASP_RE`) und bildet sie
auf die zehn Ordner des Datensatzes `smartbugs-curated` ab
(`DASP_TO_CATEGORY`: 1 `reentrancy`, 2 `access_control`, 3 `arithmetic`,
4 `unchecked_low_level_calls`, 5 `denial_of_service`, 6 `bad_randomness`,
7 `front_running`, 8 `time_manipulation`, 9 `short_addresses`, 10 `other`).
Ein Finding ohne DASP-Nummer geht weder in Recall noch in Precision ein.
Daraus folgt die Regel:

1. **Ein Detektor bekommt eine DASP-Nummer genau dann, wenn sein Prompt die
   Schwäche prüft, die `smartbugs-curated` unter dieser Kategorie labelt.**
   Maßstab ist das Label, nicht der Name des Detektors: Ein Treffer des
   Detektors auf einem so gelabelten Contract muss ein Treffer im Sinne des
   Labels sein.
2. **Keine DASP-Nummer** bekommen Detektoren für DeFi-Protokolllogik (der
   Datensatz enthält Solidity-0.4-Contracts ohne DeFi-Muster), für
   Code-Qualität und Stil, für Schnittstellen- und Übersetzungsfragen und für
   eingefrorene oder abgewiesene Mittel. Für sie gibt es kein curated-Label,
   das ein Treffer bestätigen könnte.
3. **DASP-9 und DASP-10 werden nicht vergeben.** `short_addresses` (1 Contract)
   prüft kein Detektor; `other` (3 Contracts) ist ein Sammelbecken, eine
   Zuordnung dorthin wäre willkürlich.
4. **SWC-Nummern ohne DASP-Klasse** (SWC-118, SWC-122, SWC-123, SWC-132,
   SWC-133) bleiben als Dokumentation stehen; sie wirken nicht auf die Metrik.
   `(approx.)` und `family` markieren, dass der SWC-Eintrag nur näherungsweise
   passt.

Nach dieser Regel tragen 15 der 41 Detektoren eine DASP-Nummer, 26 keine. Im
curated-Lauf `curated_v1_20260705` entfallen auf die 15 zusammen 656 der
1 124 Findings, auf die 26 die übrigen 468.

## Die 15 Detektoren mit DASP-Nummer

Spalte „Prompt“ zitiert den Prüffall aus `phase_prompt`; „Begründung“ misst
ihn am curated-Label.

| Detektor | Findingname | Klassifikation | curated-Kategorie | Prompt (Auszug) | Begründung |
|---|---|---|---|---|---|
| `ArithmeticDetector` | Integer Overflow / Underflow | `SWC-101, DASP-3` | `arithmetic` | „result of an arithmetic operation exceeds the maximum or falls below the minimum value … ensure that each arithmetic operation uses `SafeMath`“ | Über- und Unterlauf ist genau das, was `arithmetic` labelt. Trägt. |
| `ReentrancyDetector` | Reentrancy | `SWC-107, DASP-1` | `reentrancy` | „external call … can re-enter the original contract … state changes … performed after an external call … Checks-Effects-Interactions pattern or ReentrancyGuard“ | Trägt. |
| `UncheckedSendDetector` | Unchecked External Call (send/transfer/ERC20 return) | `SWC-104, DASP-4` | `unchecked_low_level_calls` | „external calls are made without checking the success of the call … instances of ERC20 transfer and transferFrom“ | Das Label steht für ungeprüfte Rückgabewerte von `send`/`call`; die ERC20-Erweiterung greift auf curated kaum. Trägt. |
| `UncheckedLowLevelCallDetector` | Unchecked Low-level Call (call/delegatecall/send) | `SWC-104, DASP-4` | `unchecked_low_level_calls` | „low-level calls (such as `call`, `delegatecall`, `send`) are not adequately checked … the contract does not handle errors“ | Fälle 1 und 3 sind SWC-104; Fall 2 (nicht vertrauenswürdiger Callee) ist breiter, ändert die Klasse aber nicht. Trägt. |
| `TODDetector` | Transaction Order Dependence (front-running) | `SWC-114, DASP-7` | `front_running` | „order of transaction execution might have an impact on the contract's behavior … gas prices can be manipulated to change the order“ | Trägt. |
| `TimeStampManipulationDetector` | Timestamp Dependence | `SWC-116, DASP-8` | `time_manipulation` | „relies on block timestamps (e.g., block.timestamp, now) for critical decisions … auction timing or lockup periods“ | Fall 2 des Prompts (Zeitstempel als Zufallsquelle) überschneidet sich mit DASP-6; Gegenstand bleibt der Zeitstempel. Trägt. |
| `PredictableRandDetector` | Predictable / Weak Randomness | `SWC-120, DASP-6` | `bad_randomness` | „Reliance on blockhash for randomness … Reliance on blocknumber for randomness“ | Trägt. |
| `TXRelianceDetector` | Authorization via tx.origin | `SWC-115, DASP-2` | `access_control` | „relies on `tx.origin` to verify the owner of the contract … unsafe access control method“ | curated führt den tx.origin-Fall unter `access_control` (`phishable.sol`). Trägt. |
| `SuicideDetector` | Unprotected SELFDESTRUCT | `SWC-106, DASP-2` | `access_control` | „determine if the `selfdestruct` function is safeguarded with appropriate restrictions … `suicide(owner)`“ | curated führt den ungeschützten `selfdestruct` unter `access_control` (`simple_suicide.sol`). Trägt. |
| `GasLimitDetector` | Gas-Limit / Unbounded Operation | `SWC-128, DASP-5` | `denial_of_service` | „a while loop that can potentially iterate a large number of times, leading to out-of-gas errors … denial-of-service (DoS)“ | Trägt. |
| `LackAuthorizationDetector` | Missing Access Control / Authorization | `SWC-105 (approx.), DASP-2` | `access_control` | „functions that modify the state of the contract … appropriate access control mechanisms, such as `onlyOwner`, `onlyAdmin`“ | DASP-2 trägt. SWC-105 (Unprotected Ether Withdrawal) ist nur ein Näherungswert und so markiert. |
| `MissingOnlyOwnerDetector` | Missing onlyOwner Modifier | `DASP-2 (no specific SWC)` | `access_control` | „callable by any user due to the absence of the `onlyOwner` modifier … token minting, ownership transfer, or critical state changes“ | Dieselbe Klasse wie `LackAuthorizationDetector`, zweiter Prompt. Trägt. |
| `OwnershipHijackingDetector` | Unprotected Ownership Change | `DASP-2 (no specific SWC)` | `access_control` | „The changeOwner function allows any address to change the owner of the contract without any authorization checks“ | Spezialfall fehlender Zugriffskontrolle. Trägt. |
| `CentralizationRiskDetector` | Centralization Risk | `DASP-2 / governance (no standard SWC)` | `access_control` | „Functions that can only be executed by a single address (e.g., owner) … Lack of decentralized or multi-signature mechanisms“ | **Trägt nicht sicher.** Der Prompt schlägt an, wenn Zugriffskontrolle *vorhanden* ist (Owner-Privilegien); das Label `access_control` steht für *fehlende* Kontrolle. Offener Punkt 1. |
| `DoSDetector` | Denial of Service | `SWC-113 / SWC-128, DASP-5` | `denial_of_service` | „loops have an unbounded iteration count … external calls that can fail or consume excessive gas … high-gas transactions to consume most of the block's gas limit“ | Fall 1 ist SWC-128, Fall 2 SWC-113; das Label deckt beides. Trägt. |

## Die 26 Detektoren ohne DASP-Nummer

| Detektor | Findingname | Klassifikation | Prompt (Auszug) | Warum keine DASP-Nummer |
|---|---|---|---|---|
| `PriceManipulationDetector` | Price Manipulation (centralized pricing) | `logic/DeFi (no standard SWC)` | „arbitrary adjustment of token prices by a centralized authority … no decentralized or transparent mechanisms for determining token prices“ | DeFi-Logik (Regel 2). |
| `OracleDependencyDetector` | Single External Oracle Dependency | `logic/DeFi (no standard SWC)` | „Dependence on a single external oracle for critical data … Lack of fallback mechanisms“ | DeFi-Logik (Regel 2). |
| `FundingCalculationDetector` | Funding-Rate Calculation Precision | `logic/DeFi (no standard SWC)` | „Simplistic funding rate calculation … Lack of input validation for critical parameters (e.g., spotPrice, markPrice)“ | DeFi-Logik (Regel 2). |
| `FlashLoanDetector` | Flash-Loan Fee Manipulation | `logic/DeFi (no standard SWC)` | „Lack of access control on the function that sets the flash loan fee“ | DeFi-Logik (Regel 2); im Kern aber ein Zugriffskontroll-Prüffall, siehe offener Punkt 3. |
| `SourceSwappingDetector` | Yield-Source Swap Token Mismatch | `logic/DeFi (no standard SWC)` | „swap the current yield source with a new one without verifying that the deposit token … is the same“ | DeFi-Logik (Regel 2). |
| `InconsistentTokensDetector` | Inconsistent Base Tokens on Migration | `logic/DeFi (no standard SWC)` | „does not verify that both the old and new strategies use the same base token during migration“ | DeFi-Logik (Regel 2). |
| `PartialWithdrawalsDetector` | Unhandled Partial Withdrawals on Migration | `logic/DeFi (no standard SWC)` | „assumes that the old strategy will have sufficient funds to fulfill the `withdraw` call for the full amount during migration“ | DeFi-Logik (Regel 2). |
| `UnlimitedTokenDetector` | Unlimited Token Approval | `logic/DeFi (no standard SWC)` | „Calls to approve() or increaseAllowance() methods with very large values (e.g., type(uint256).max …)“ | DeFi-Logik (Regel 2). |
| `DataCorruptionDetector` | Assumption of Fixed-Length Array | `logic (no standard SWC)` | „incorrectly assumes that an array returned by a function has a fixed length“ | Korrektheitsfehler ohne DASP-Klasse (Regel 2). |
| `DataInconsistencyDetector` | Storage/Memory Data Inconsistency | `logic (no standard SWC)` | „assumptions made about the behavior of storage and memory … data is copied from storage to memory, or vice versa“ | Korrektheitsfehler ohne DASP-Klasse (Regel 2). |
| `UninitializedReturnVariableDetector` | Uninitialized Return Variable | `logic (SWC-109 family)` | „declares a return variable but does not properly initialize or set it“ | Nur verwandt mit SWC-109 (Uninitialized Storage Pointer); keine DASP-Klasse (Regel 4). |
| `MisuseMsgValueDetector` | Misuse of msg.value in a Loop | `logic (no standard SWC)` | „allocating the total `msg.value` to each item within a loop, rather than dividing `msg.value`“ | Korrektheitsfehler ohne DASP-Klasse (Regel 2). |
| `PrecisionLossDetector` | Precision Loss / Integer-Division Truncation | `logic (arithmetic)` | „Use of integer division for operations requiring high precision, which can result in truncation“ | Kein Über-/Unterlauf; `arithmetic` in curated labelt genau den (Regel 1). `coverage.md` führt den Detektor als „Arithmetic (partial)“, das ist thematische Nähe, keine Zuordnung. |
| `InconsistentInitializationDetector` | Inconsistent State Initialization Order | `logic (no standard SWC)` | „Initialization of a state variable using a function call where the function's logic depends on the state of other variables that are not yet initialized“ | Korrektheitsfehler ohne DASP-Klasse (Regel 2). |
| `OrderInitializationDetector` | Inheritance Initialization Order / Diamond | `logic (SWC-125 family)` | „constructors of the inherited contracts are called in the order determined by the linearized order … diamond problem“ | Nur verwandt mit SWC-125 (Incorrect Inheritance Order); keine DASP-Klasse (Regel 4). |
| `InputValidationDetector` | Lack of Input Validation | `SWC-123 (approx.)` | „inputs are not properly validated … zero addresses, negative values, or values exceeding certain thresholds“ | SWC-123 (Requirement Violation) näherungsweise; keine DASP-Klasse (Regel 4). Häufigster Detektor ohne Nummer im curated-Lauf (107 Findings). |
| `SignatureVerificationDetector` | Incorrect Signature / Signer Verification | `SWC-122 (approx.)` | „uses the signature to recover the signer and then verifies that the signer is the `msg.sender`“ | SWC-122 (Lack of Proper Signature Verification) näherungsweise; keine DASP-Klasse (Regel 4). |
| `WithdrawalFunctionDetector` | Missing Withdrawal Function (locked funds) | `logic (locked funds)` | „determine if there is a function that allows users to withdraw their deposited funds“ | Eingefrorene Mittel haben in curated kein Label (Regel 2). 112 Findings im curated-Lauf, alle außerhalb der Metrik. |
| `FallbackFunctionDetector` | Missing Fallback Function (rejected/locked ether) | `logic (no standard SWC)` | „do not define a fallback function, which could lead to accidental loss of ether sent to the contract“ | Abgewiesene oder eingefrorene Mittel, kein Label (Regel 2). |
| `HashCollisionDetector` | Hash Collision via abi.encodePacked | `SWC-133` | „multiple input values are concatenated without clear delimiters before hashing … `abi.encodePacked`“ | SWC-133 trägt; DASP kennt keine Klasse dafür (Regel 4). |
| `MisdeclaredConstructorDetector` | Incorrect Constructor Name (legacy syntax) | `SWC-118` | „functions that have the same name as the contract … public and can be called by any user“ | SWC-118 trägt. Ohne DASP-Nummer, obwohl curated diesen Fall unter `access_control` labelt: offener Punkt 2. |
| `ImpracticalityMatchDetector` | Strict Balance Equality (this.balance ==) | `SWC-132` | „The use of `this.balance` for checking if the funding goal is reached … exact comparison“ | SWC-132 trägt; keine DASP-Klasse (Regel 4). |
| `RedundantConditionalDetector` | Redundant Conditional Check | `code-quality (no standard SWC)` | „Conditional checks that always evaluate to true or false … duplicate checks already performed earlier“ | Stil (Regel 2). |
| `MappingGetterDetector` | Misuse of Mapping Getter | `code-quality (no standard SWC)` | „call the mapping as a function, e.g., `this.mappingName(key)`, instead of accessing it directly“ | Stil (Regel 2). |
| `GetterFunctionDetector` | Unimplemented Interface Function | `logic/compile (no standard SWC)` | „Interface functions are declared but not implemented in the contract“ | Schnittstellen- und Übersetzungsfrage (Regel 2). |
| `UnnecessaryComparisonDetector` | Unnecessary Boolean Comparison | `code-quality (no standard SWC)` | „Comparing a boolean value to true or false explicitly, instead of using the boolean value directly“ | Stil (Regel 2). |

## Was die Zuordnung im curated-Lauf bewirkt

Zahlen aus `eval/curated_v1_20260705__llmsmartaudit/findings.jsonl`
(1 124 Findings auf 143 Contracts). Die 656 Findings mit DASP-Nummer verteilen
sich so auf die 15 Detektoren:

| Detektor | Findings | Detektor | Findings |
|---|---:|---|---:|
| ArithmeticDetector | 75 | MissingOnlyOwnerDetector | 41 |
| ReentrancyDetector | 72 | GasLimitDetector | 35 |
| DoSDetector | 69 | TimeStampManipulationDetector | 19 |
| UncheckedSendDetector | 65 | OwnershipHijackingDetector | 17 |
| CentralizationRiskDetector | 64 | PredictableRandDetector | 16 |
| LackAuthorizationDetector | 63 | TXRelianceDetector | 8 |
| UncheckedLowLevelCallDetector | 63 | SuicideDetector | 4 |
| TODDetector | 45 | | |

Sechs Detektoren zeigen auf DASP-2. Die Metrik arbeitet auf Contract-Ebene
(ein Paar aus Contract und Kategorie zählt einmal, gleich wie viele Findings
es tragen), deshalb verschieben Mehrfachprompts derselben Klasse Recall und
Precision nicht; sie erhöhen nur die Findingzahl.

## Offene Punkte (nicht geändert)

Die Wirkung ist mit derselben Zählweise wie in `evaluate_curated.py` auf
`findings.jsonl` nachgerechnet; der Ausgangswert (Recall 96,5 %, Precision
29,7 %, 464 Paare, 138 Treffer) reproduziert sich dabei exakt.

1. **`CentralizationRiskDetector` als DASP-2.** 64 Findings auf 64 Contracts,
   davon 15 auf Contracts mit Label `access_control` und 36 auf
   `unchecked_low_level_calls`. Der Prompt fragt nach vorhandenen
   Owner-Privilegien, das Label nach fehlender Kontrolle; ein Treffer bestätigt
   das Label also nicht im Sinne von Regel 1. Ohne DASP-Nummer läge die
   Precision bei 30,9 % statt 29,7 % und der Recall bei 95,8 % statt 96,5 %
   (`wallet_02_refund_nosub` wird nur über diesen Detektor gefunden). Die
   Zuordnung bleibt, weil sie zum Zeitpunkt der Messung galt und die
   Verschiebung klein ist; wer sie ändert, muss `metriken.md` und alle
   Nennungen von 30 % nachziehen.
2. **`MisdeclaredConstructorDetector` ohne DASP-2.** curated labelt falsch
   benannte Konstruktoren als `access_control` (`incorrect_constructor_name1`
   bis `3`, `rubixi`, `wallet_03_wrong_constructor`). Nach Regel 1 wäre DASP-2
   vertretbar. Der Detektor meldete 28 Findings, 7 davon auf
   `access_control`-Contracts, die alle schon über andere DASP-2-Detektoren
   erkannt sind: Recall unverändert, Precision 29,5 % statt 29,7 %. Bleibt
   ohne Nummer.
3. **`FlashLoanDetector`.** Der Prompt prüft fehlende Zugriffskontrolle auf
   einen Fee-Setter; `coverage.md` zählt ihn thematisch zu DASP-2,
   `findings.yaml` gibt ihm keine Nummer. Im curated-Lauf 0 Findings, auf dem
   DeFi-Korpus keine Ground Truth; eine Nummer hätte auf keine Kennzahl
   Einfluss. Bleibt bei DeFi-Logik.
4. **Nicht abgedeckt:** `short_addresses` (DASP-9) prüft kein Detektor;
   klassische Bytecode-Schwächen (SWC-112, SWC-124, SWC-127) ebenso wenig
   (`coverage.md`, „Gaps“).
