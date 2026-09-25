# curated_v1_20260705 -- gptscan

Erzeugt 2026-09-25T08:44:40+00:00 aus `smartbugs/results/gptscan/curated_v1_20260705` durch `analysis_tools/curated_eval.py`.
Backend deepseek/deepseek-v4-flash, Timeout 1800 s, MAIN=0.

## Zustaende

| Zustand | Contracts | Anteil |
|---|---:|---:|
| keine Findings, Contract wurde analysiert | 137 | 95.8 % |
| Findings gemeldet | 6 | 4.2 % |

Nur der Zustand *keine Findings* ist ein Ergebnis. Ein Contract, der nicht
uebersetzt wurde oder den Kontext sprengte, darf weder als sauber gelten
noch in eine Precision-Rechnung eingehen.

## Recall / Precision / F1 je DASP-Kategorie

| Kategorie | Contracts | Erkannt | Recall | Geflaggt | Precision | F1 |
|---|---:|---:|---:|---:|---:|---:|
| access_control | 18 | 0 | 0 % | 6 | 0 % | – |
| arithmetic | 15 | 0 | 0 % | 0 | – | – |
| bad_randomness | 8 | 0 | 0 % | 0 | – | – |
| denial_of_service | 6 | 0 | 0 % | 0 | – | – |
| front_running | 4 | 0 | 0 % | 0 | – | – |
| other | 3 | 0 | 0 % | 0 | – | – |
| reentrancy | 31 | 0 | 0 % | 0 | – | – |
| short_addresses | 1 | 0 | 0 % | 0 | – | – |
| time_manipulation | 5 | 0 | 0 % | 0 | – | – |
| unchecked_low_level_calls | 52 | 0 | 0 % | 0 | – | – |
| **GESAMT** | **143** | **0** | **0 %** | **6** | **0 %** | **–** |

0 der 6 Findings tragen keine DASP-Klassifikation und gehen weder in
Recall noch in Precision ein.

## Findings je Kategorie

| Kategorie | Findings | DASP | Severity (aus findings.yaml) |
|---|---:|---|---|
| MWE-207: Unauthorized Transfer | 6 | DASP-2 | high |

## Findings je Contract

Mittel 0.0, Median 0, Maximum 1, Contracts ohne Findings 137.

| Contract | Kategorie (Label) | Findings | Zustand |
|---|---|---:|---|
| 0x2972d548497286d18e92b5fa1f8f9139e5653fd2 | unchecked_low_level_calls | 1 | findings |
| 0x4051334adc52057aca763453820cb0e045076ef3 | unchecked_low_level_calls | 1 | findings |
| 0x4b71ad9c1a84b9b643aa54fdd66e2dec96e8b152 | unchecked_low_level_calls | 1 | findings |
| 0x524960d55174d912768678d8c606b4d50b79d7b1 | unchecked_low_level_calls | 1 | findings |
| 0xa46edd6a9a93feec36576ee5048146870ea2c3ae | unchecked_low_level_calls | 1 | findings |
| 0xd5967fed03e85d1cce44cab284695b41bc675b5c | unchecked_low_level_calls | 1 | findings |
| arbitrary_location_write_simple | access_control | 0 | clean |
| FibonacciBalance | access_control | 0 | clean |
| incorrect_constructor_name1 | access_control | 0 | clean |
| incorrect_constructor_name2 | access_control | 0 | clean |
| incorrect_constructor_name3 | access_control | 0 | clean |
| mapping_write | access_control | 0 | clean |
| multiowned_vulnerable | access_control | 0 | clean |
| mycontract | access_control | 0 | clean |
| parity_wallet_bug_1 | access_control | 0 | clean |

