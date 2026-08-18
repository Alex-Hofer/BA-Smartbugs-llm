# llmsa_curated_v2

Erzeugt 2026-08-16T11:19:32+00:00 aus `smartbugs/results/llmsmartaudit/llmsa_curated_v2`.
Backend deepseek/deepseek-v4-flash, Modus SmartContractTA (fixed in scripts/do_solidity.sh), MAIN=0.

## Zustaende

| Zustand | Contracts | Anteil |
|---|---:|---:|
| Findings gemeldet | 142 | 99.3 % |
| Kontext ueberschritten - NICHT analysiert | 1 | 0.7 % |

Die Zeile *Kontext ueberschritten* ist kein Ergebnis. Diese Contracts
wurden nie analysiert; sie duerfen weder als 'clean' noch in einer
Precision-Rechnung auftauchen.

## Findings je Kategorie

| Kategorie | Findings | DASP | DeFi-Logik | Severity (aus findings.yaml) |
|---|---:|---|---|---|
| Missing Withdrawal Function (locked funds) | 106 | - | nein | medium |
| Lack of Input Validation | 87 | - | nein | medium |
| Storage/Memory Data Inconsistency | 74 | - | nein | medium |
| Missing Access Control / Authorization | 70 | DASP-2 | nein | high |
| Unchecked Low-level Call (call/delegatecall/send) | 69 | DASP-4 | nein | medium |
| Unchecked External Call (send/transfer/ERC20 return) | 64 | DASP-4 | nein | medium |
| Denial of Service | 63 | DASP-5 | nein | medium |
| Centralization Risk | 61 | DASP-2 | nein | medium |
| Reentrancy | 56 | DASP-1 | nein | high |
| Integer Overflow / Underflow | 55 | DASP-3 | nein | high |
| Gas-Limit / Unbounded Operation | 43 | DASP-5 | nein | medium |
| Transaction Order Dependence (front-running) | 42 | DASP-7 | nein | medium |
| Missing onlyOwner Modifier | 42 | DASP-2 | nein | high |
| Missing Fallback Function (rejected/locked ether) | 36 | - | nein | low |
| Unprotected Ownership Change | 25 | DASP-2 | nein | high |
| Timestamp Dependence | 20 | DASP-8 | nein | low |
| Redundant Conditional Check | 19 | - | nein | low |
| Predictable / Weak Randomness | 16 | DASP-6 | nein | medium |
| Precision Loss / Integer-Division Truncation | 12 | - | nein | medium |
| Unnecessary Boolean Comparison | 12 | - | nein | low |
| Incorrect Constructor Name (legacy syntax) | 12 | - | nein | high |
| Assumption of Fixed-Length Array | 8 | - | nein | medium |
| Inconsistent State Initialization Order | 8 | - | nein | medium |
| Price Manipulation (centralized pricing) | 6 | - | ja | high |
| Authorization via tx.origin | 4 | DASP-2 | nein | medium |
| Unprotected SELFDESTRUCT | 4 | DASP-2 | nein | high |
| Strict Balance Equality (this.balance ==) | 3 | - | nein | low |
| Single External Oracle Dependency | 3 | - | ja | medium |
| Uninitialized Return Variable | 3 | - | nein | medium |
| Inheritance Initialization Order / Diamond | 2 | - | nein | medium |
| Yield-Source Swap Token Mismatch | 1 | - | ja | medium |
| Flash-Loan Fee Manipulation | 1 | - | ja | high |
| Funding-Rate Calculation Precision | 1 | - | ja | medium |

## Findings je Contract

141 Contracts mit mindestens einem Finding, 1 ohne.

| Contract | Findings | Zustand |
|---|---:|---|
| 0xb620cee6b52f96f3c6b253e6eea556aa2d214a99 | 16 | Findings gemeldet |
| rubixi | 15 | Findings gemeldet |
| arbitrary_location_write_simple | 14 | Findings gemeldet |
| 0x07f7ecb66d788ab01dc93b9b71a88401de7d0f2e | 13 | Findings gemeldet |
| 0x3a0e9acd953ffc0dd18d63603488846a6b8b2b01 | 13 | Findings gemeldet |
| 0x9d06cbafa865037a01d322d3f4222fa3e04e5488 | 13 | Findings gemeldet |
| 0xb0510d68f210b7db66e8c7c814f22680f2b8d1d6 | 13 | Findings gemeldet |
| FibonacciBalance | 13 | Findings gemeldet |
| 0x5aa88d2901c68fda244f1d0584400368d2c8e739 | 12 | Findings gemeldet |
| 0x7d09edb07d23acb532a82be3da5c17d9d85806b4 | 12 | Findings gemeldet |
| 0xa46edd6a9a93feec36576ee5048146870ea2c3ae | 12 | Findings gemeldet |
| 0xf70d589d76eebdd7c12cc5eec99f8f6fa4233b9e | 12 | Findings gemeldet |
| governmental_survey | 12 | Findings gemeldet |
| list_dos | 12 | Findings gemeldet |
| parity_wallet_bug_1 | 12 | Findings gemeldet |
| 0x4a66ad0bca2d700f11e1f2fc2c106f7d3264504c | 11 | Findings gemeldet |
| 0x7a4349a749e59a5736efb7826ee3496a2dfd5489 | 11 | Findings gemeldet |
| 0x01f8c4e3fa3edeb29e514cba738d87ce8c091d3f | 10 | Findings gemeldet |
| 0x2972d548497286d18e92b5fa1f8f9139e5653fd2 | 10 | Findings gemeldet |
| 0x52d2e0f9b01101a59b38a3d05c80b7618aeed984 | 10 | Findings gemeldet |
| 0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839 | 10 | Findings gemeldet |
| 0x78c2a1e91b52bca4130b6ed9edd9fbcfd4671c37 | 10 | Findings gemeldet |
| 0x806a6bd219f162442d992bdc4ee6eba1f2c5a707 | 10 | Findings gemeldet |
| 0x8fd1e427396ddb511533cf9abdbebd0a7e08da35 | 10 | Findings gemeldet |
| 0xbaa3de6504690efb064420d89e871c27065cdd52 | 10 | Findings gemeldet |
| 0xd5967fed03e85d1cce44cab284695b41bc675b5c | 10 | Findings gemeldet |
| 0xdb1c55f6926e7d847ddf8678905ad871a68199d2 | 10 | Findings gemeldet |
| 0xe894d54dca59cb53fe9cbc5155093605c7068220 | 10 | Findings gemeldet |
| etherpot_lotto | 10 | Findings gemeldet |
| lotto | 10 | Findings gemeldet |
| mapping_write | 10 | Findings gemeldet |
| open_address_lottery | 10 | Findings gemeldet |
| proxy | 10 | Findings gemeldet |
| 0x3e013fc32a54c4c5b6991ba539dcd0ec4355c859 | 9 | Findings gemeldet |
| 0x3f2ef511aa6e75231e4deafc7a3d2ecab3741de2 | 9 | Findings gemeldet |
| 0x4b71ad9c1a84b9b643aa54fdd66e2dec96e8b152 | 9 | Findings gemeldet |
| 0x4e73b32ed6c35f570686b89848e5f39f20ecc106 | 9 | Findings gemeldet |
| 0x70f9eddb3931491aab1aeafbc1e7f1ca2a012db4 | 9 | Findings gemeldet |
| 0x96edbe868531bd23a6c05e9d0c424ea64fb1b78b | 9 | Findings gemeldet |
| 0xbe4041d55db380c5ae9d4a9b9703f1ed4e7e3888 | 9 | Findings gemeldet |
| 0xe4eabdca81e31d9acbc4af76b30f532b6ed7f3bf | 9 | Findings gemeldet |
| blackjack | 9 | Findings gemeldet |
| incorrect_constructor_name3 | 9 | Findings gemeldet |
| lottopollo | 9 | Findings gemeldet |
| lucky_doubler | 9 | Findings gemeldet |
| parity_wallet_bug_2 | 9 | Findings gemeldet |
| 0x19cf8481ea15427a98ba3cdd6d9e14690011ab10 | 8 | Findings gemeldet |
| 0x4051334adc52057aca763453820cb0e045076ef3 | 8 | Findings gemeldet |
| 0x610495793564aed0f9c7fc48dc4c7c9151d34fd6 | 8 | Findings gemeldet |
| 0x7a8721a9d64c74da899424c1b52acbf58ddc9782 | 8 | Findings gemeldet |
| 0x84d9ec85c9c568eb332b7226a8f826d897e0a4a8 | 8 | Findings gemeldet |
| 0xa1fceeff3acc57d257b917e30c4df661401d6431 | 8 | Findings gemeldet |
| 0xaae1f51cf3339f18b6d3f3bdc75a5facd744b0b8 | 8 | Findings gemeldet |
| 0xb11b2fed6c9354f7aa2f658d3b4d7b31d8a13b77 | 8 | Findings gemeldet |
| 0xcead721ef5b11f1a7b530171aab69b16c5e66b6e | 8 | Findings gemeldet |
| 0xd2018bfaa266a9ec0a1a84b061640faa009def76 | 8 | Findings gemeldet |
| king_of_the_ether_throne | 8 | Findings gemeldet |
| multiowned_vulnerable | 8 | Findings gemeldet |
| odds_and_evens | 8 | Findings gemeldet |
| wallet_03_wrong_constructor | 8 | Findings gemeldet |
| 0x0cbe050f75bc8f8c2d6c0d249fea125fd6e1acc9 | 7 | Findings gemeldet |
| 0x23a91059fdc9579a9fbd0edc5f2ea0bfdb70deb4 | 7 | Findings gemeldet |
| 0x4320e6f8c05b27ab4707cd1f6d5ce6f3e4b3a5a1 | 7 | Findings gemeldet |
| 0x524960d55174d912768678d8c606b4d50b79d7b1 | 7 | Findings gemeldet |
| 0x561eac93c92360949ab1f1403323e6db345cbf31 | 7 | Findings gemeldet |
| 0xb37f18af15bafb869a065b61fc83cfc44ed9cc27 | 7 | Findings gemeldet |
| 0xbebbfe5b549f5db6e6c78ca97cac19d1fb03082c | 7 | Findings gemeldet |
| 0xe09b1ab8111c2729a76f16de96bc86a7af837928 | 7 | Findings gemeldet |
| 0xec329ffc97d75fe03428ae155fc7793431487f63 | 7 | Findings gemeldet |
| 0xf2570186500a46986f3139f65afedc2afe4f445d | 7 | Findings gemeldet |
| auction | 7 | Findings gemeldet |
| crypto_roulette | 7 | Findings gemeldet |
| incorrect_constructor_name1 | 7 | Findings gemeldet |
| mycontract | 7 | Findings gemeldet |
| reentrance | 7 | Findings gemeldet |
| wallet_02_refund_nosub | 7 | Findings gemeldet |
| 0x39cfd754c85023648bf003bea2dd498c5612abfa | 6 | Findings gemeldet |
| 0x7541b76cb60f4c60af330c208b0623b7f54bf615 | 6 | Findings gemeldet |
| 0x7b368c4e805c3870b6c49a3f1f49f69af8662cf3 | 6 | Findings gemeldet |
| 0x941d225236464a25eb18076df7da6a91d0f95e9e | 6 | Findings gemeldet |
| 0x958a8f594101d2c0485a52319f29b2647f2ebc06 | 6 | Findings gemeldet |
| 0xb5e1b1ee15c6fa0e48fce100125569d430f1bd12 | 6 | Findings gemeldet |
| 0xb7c5c5aa4d42967efe906e1b66cb8df9cebf04f7 | 6 | Findings gemeldet |
| 0xb93430ce38ac4a6bb47fb1fc085ea669353fd89e | 6 | Findings gemeldet |
| 0xe82f0742a71a02b9e9ffc142fdcb6eb1ed06fb87 | 6 | Findings gemeldet |
| 0xf015c35649c82f5467c9c74b7f28ee67665aad68 | 6 | Findings gemeldet |
| 0xf29ebe930a539a60279ace72c707cba851a57707 | 6 | Findings gemeldet |
| dos_address | 6 | Findings gemeldet |
| dos_number | 6 | Findings gemeldet |
| eth_tx_order_dependence_minimal | 6 | Findings gemeldet |
| etheraffle | 6 | Findings gemeldet |
| guess_the_random_number | 6 | Findings gemeldet |
| incorrect_constructor_name2 | 6 | Findings gemeldet |
| integer_overflow_mapping_sym_1 | 6 | Findings gemeldet |
| integer_overflow_multitx_multifunc_feasible | 6 | Findings gemeldet |
| lottery | 6 | Findings gemeldet |
| random_number_generator | 6 | Findings gemeldet |
| simple_dao | 6 | Findings gemeldet |
| token | 6 | Findings gemeldet |
| unprotected0 | 6 | Findings gemeldet |
| wallet_04_confused_sign | 6 | Findings gemeldet |
| 0x89c1b3807d4c67df034fffb62f3509561218d30b | 5 | Findings gemeldet |
| 0x8c7777c45481dba411450c228cb692ac3d550344 | 5 | Findings gemeldet |
| 0xbaf51e761510c1a11bf48dd87c0307ac8a8c8a4f | 5 | Findings gemeldet |
| BECToken | 5 | Findings gemeldet |
| ether_lotto | 5 | Findings gemeldet |
| insecure_transfer | 5 | Findings gemeldet |
| integer_overflow_1 | 5 | Findings gemeldet |
| mishandled | 5 | Findings gemeldet |
| old_blockhash | 5 | Findings gemeldet |
| phishable | 5 | Findings gemeldet |
| send_loop | 5 | Findings gemeldet |
| simple_suicide | 5 | Findings gemeldet |
| spank_chain_payment | 5 | Findings gemeldet |
| integer_overflow_add | 4 | Findings gemeldet |
| integer_overflow_minimal | 4 | Findings gemeldet |
| name_registrar | 4 | Findings gemeldet |
| overflow_simple_add | 4 | Findings gemeldet |
| overflow_single_tx | 4 | Findings gemeldet |
| reentrancy_bonus | 4 | Findings gemeldet |
| reentrancy_cross_function | 4 | Findings gemeldet |
| reentrancy_insecure | 4 | Findings gemeldet |
| reentrancy_simple | 4 | Findings gemeldet |
| unchecked_return_value | 4 | Findings gemeldet |
| 0x93c32845fae42c83a70e5f06214c8433665c2ab5 | 3 | Findings gemeldet |
| ERC20 | 3 | Findings gemeldet |
| FindThisHash | 3 | Findings gemeldet |
| dos_simple | 3 | Findings gemeldet |
| etherbank | 3 | Findings gemeldet |
| integer_overflow_benign_1 | 3 | Findings gemeldet |
| integer_overflow_mul | 3 | Findings gemeldet |
| integer_overflow_multitx_onefunc_feasible | 3 | Findings gemeldet |
| reentrancy_dao | 3 | Findings gemeldet |
| roulette | 3 | Findings gemeldet |
| short_address_example | 3 | Findings gemeldet |
| timelock | 3 | Findings gemeldet |
| etherstore | 2 | Findings gemeldet |
| modifier_reentrancy | 2 | Findings gemeldet |
| smart_billions | 2 | Findings gemeldet |
| timed_crowdsale | 2 | Findings gemeldet |
| tokensalechallenge | 2 | Findings gemeldet |
| 0x663e4229142a27f00bafb5d087e1e730648314c3 | 0 | Kontext ueberschritten - NICHT analysiert |

## Aufwand

- LLM-Calls: 6126
- Prompt-Tokens: 11119680
- Completion-Tokens: 11235316
- Kosten geschaetzt: $5.16 (Estimated from token counts; the tool reports $0.0000 because chatdev/statistics.py::prompt_cost has no entry for deepseek-v4-flash. Authoritative figure: DeepSeek invoice.)
- Summe Task-Laufzeit: 114092 s

## Nicht vom Werkzeug geliefert

`function`, `lines`, `severity`, `confidence` sind in findings.jsonl `null`.
Das Werkzeug liest Quelltext als Text und meldet weder Positionen noch
Schweregrade. `severity_doc` traegt den dokumentationsseitigen Default aus
findings.yaml und ist kein Urteil des Modells.
