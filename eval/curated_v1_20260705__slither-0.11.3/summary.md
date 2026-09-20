# curated_v1_20260705 -- slither-0.11.3

Erzeugt 2026-09-20T10:01:09+00:00 aus `smartbugs/results/slither-0.11.3/curated_v1_20260705` durch `analysis_tools/curated_eval.py`.
Statische Analyse, Image `smartbugs/slither:0.11.3`, Timeout 600 s.

## Zustaende

| Zustand | Contracts | Anteil |
|---|---:|---:|
| Findings gemeldet | 140 | 97.9 % |
| gescheitert | 3 | 2.1 % |

Nur der Zustand *keine Findings* ist ein Ergebnis. Ein Contract, der nicht
uebersetzt wurde oder den Kontext sprengte, darf weder als sauber gelten
noch in eine Precision-Rechnung eingehen.

## Recall / Precision / F1 je DASP-Kategorie

| Kategorie | Contracts | Erkannt | Recall | Geflaggt | Precision | F1 |
|---|---:|---:|---:|---:|---:|---:|
| access_control | 18 | 7 | 39 % | 33 | 21 % | 27 % |
| arithmetic | 15 | 0 | 0 % | 0 | – | – |
| bad_randomness | 8 | 3 | 38 % | 13 | 23 % | 29 % |
| denial_of_service | 6 | 1 | 17 % | 17 | 6 % | 9 % |
| front_running | 4 | 0 | 0 % | 0 | – | – |
| other | 3 | 0 | 0 % | 0 | – | – |
| reentrancy | 31 | 29 | 94 % | 39 | 74 % | 83 % |
| short_addresses | 1 | 0 | 0 % | 0 | – | – |
| time_manipulation | 5 | 5 | 100 % | 24 | 21 % | 34 % |
| unchecked_low_level_calls | 52 | 46 | 88 % | 78 | 59 % | 71 % |
| **GESAMT** | **143** | **91** | **64 %** | **204** | **45 %** | **52 %** |

1 854 der 2 154 Findings tragen keine DASP-Klassifikation und gehen weder in
Recall noch in Precision ein.

## Findings je Kategorie

| Kategorie | Findings | DASP | Severity (aus findings.yaml) |
|---|---:|---|---|
| naming-convention | 828 | - | informational |
| solc-version | 280 | - | informational |
| deprecated-standards | 113 | - | informational |
| low-level-calls | 91 | DASP-4 | informational |
| missing-zero-check | 80 | - | low |
| external-function | 74 | - | optimization |
| constable-states | 65 | - | optimization |
| timestamp | 60 | - | low |
| unchecked-lowlevel | 54 | - | medium |
| reentrancy-unlimited-gas | 51 | - | informational |
| controlled-array-length | 40 | - | high |
| reentrancy-eth | 36 | DASP-1 | high |
| unchecked-send | 34 | - | medium |
| arbitrary-send-eth | 32 | DASP-2 | high |
| reentrancy-events | 29 | - | low |
| incorrect-equality | 26 | - | medium |
| reentrancy-benign | 26 | DASP-1 | low |
| incorrect-modifier | 16 | - | low |
| events-maths | 16 | - | low |
| too-many-digits | 16 | - | informational |
| reentrancy-no-eth | 15 | DASP-1 | medium |
| unused-state | 14 | - | informational |
| events-access | 14 | - | low |
| calls-loop | 14 | DASP-5 | low |
| weak-prng | 14 | - | high |
| boolean-equal | 11 | - | informational |
| divide-before-multiply | 9 | - | medium |
| dead-code | 9 | - | informational |
| shadowing-local | 9 | - | low |
| assembly | 8 | - | informational |
| shadowing-state | 8 | - | high |
| tautology | 7 | - | medium |
| erc20-interface | 7 | - | medium |
| uninitialized-state | 6 | - | high |
| constant-function-asm | 6 | - | medium |
| uninitialized-local | 5 | - | medium |
| cache-array-length | 4 | - | optimization |
| controlled-delegatecall | 3 | DASP-2 | high |
| suicidal | 3 | DASP-2 | high |
| missing-inheritance | 3 | - | informational |
| costly-loop | 3 | - | informational |
| uninitialized-storage | 3 | - | high |
| unchecked-transfer | 3 | - | high |
| locked-ether | 3 | DASP-5 | medium |
| tx-origin | 2 | DASP-2 | medium |
| redundant-statements | 1 | - | informational |
| shadowing-builtin | 1 | - | low |
| unused-return | 1 | DASP-4 | medium |
| return-bomb | 1 | - | low |

## Findings je Contract

Mittel 15.1, Median 9, Maximum 208, Contracts ohne Findings 3.

| Contract | Kategorie (Label) | Findings | Zustand |
|---|---|---:|---|
| 0x663e4229142a27f00bafb5d087e1e730648314c3 | unchecked_low_level_calls | 208 | findings |
| spank_chain_payment | reentrancy | 126 | findings |
| 0x19cf8481ea15427a98ba3cdd6d9e14690011ab10 | unchecked_low_level_calls | 99 | findings |
| parity_wallet_bug_1 | access_control | 81 | findings |
| smart_billions | bad_randomness | 79 | findings |
| parity_wallet_bug_2 | access_control | 64 | findings |
| rubixi | access_control | 32 | findings |
| blackjack | bad_randomness | 29 | findings |
| 0x96edbe868531bd23a6c05e9d0c424ea64fb1b78b | reentrancy | 29 | findings |
| 0xbe4041d55db380c5ae9d4a9b9703f1ed4e7e3888 | reentrancy | 29 | findings |
| BECToken | arithmetic | 27 | findings |
| 0xe09b1ab8111c2729a76f16de96bc86a7af837928 | unchecked_low_level_calls | 26 | findings |
| 0x561eac93c92360949ab1f1403323e6db345cbf31 | reentrancy | 25 | findings |
| 0xaae1f51cf3339f18b6d3f3bdc75a5facd744b0b8 | reentrancy | 25 | findings |
| 0xec329ffc97d75fe03428ae155fc7793431487f63 | unchecked_low_level_calls | 24 | findings |

