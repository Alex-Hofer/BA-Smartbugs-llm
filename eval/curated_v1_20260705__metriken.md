# Recall, Precision und F1 je DASP-Kategorie -- `curated_v1_20260705`

Erzeugt durch `analysis_tools/curated_eval.py` aus den Rohergebnissen unter
`smartbugs/results/<werkzeug>/curated_v1_20260705/`. Die Zaehlweise und die
DASP-Zuordnung stammen aus `evaluate_curated.py`; dieselben Zahlen gibt
dessen Konsolenausgabe aus:

```powershell
smartbugs\.venv\Scripts\python.exe evaluate_curated.py --suffix v1_20260705 `
    --tools gptscan llmsmartaudit slither-0.11.3 --csv
```

Alle Werte sind **Contract-Level**: ein gelabelter Contract gilt als
erkannt, wenn das Werkzeug mindestens ein Finding meldet, dessen
DASP-Klassifikation auf die gelabelte Kategorie abbildet.

## Gesamtbild

| Werkzeug | Recall | Precision | F1 | Findings | davon DASP-zugeordnet | Kosten |
|---|---:|---:|---:|---:|---:|---:|
| gptscan | 0 % | 0 % | – | 6 | 6 | $0.01 |
| llmsmartaudit | 97 % | 30 % | 45 % | 1 124 | 656 | $2.44 |
| slither-0.11.3 | 64 % | 45 % | 52 % | 2 154 | 300 | $0.00 |

## gptscan

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
Recall noch in Precision ein (0.0 %).

## llmsmartaudit

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
Recall noch in Precision ein (41.6 %).

## slither-0.11.3

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
Recall noch in Precision ein (86.1 %).

## Die wichtigste Einschraenkung

1 854 der 2 154 Slither-Findings (86.1 %) haben weder in SmartBugs'
`findings.yaml` noch ueber die beiden kanonischen Zusatz-Mappings
(`timestamp` -> DASP-8, `weak-prng` -> DASP-6) eine DASP-Zuordnung und
gehen deshalb nicht in Recall und Precision ein. Keine Zuordnung heisst
nicht belanglos: nach der Impact-Stufe des jeweiligen Detektors sind
1 480 davon Informational oder Optimization, 166 Low, 148 Medium und 60 High.
Die Herleitung steht in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`,
Abschnitt 4.1 und 5.

Weitere Einschraenkungen stehen je Werkzeug in der `README.md` des
zugehoerigen Ordners `eval/curated_v1_20260705__<werkzeug>/`.

