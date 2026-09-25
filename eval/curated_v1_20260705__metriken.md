# Recall, Precision und F1 je DASP-Kategorie -- `curated_v1_20260705`

Erzeugt durch `analysis_tools/curated_eval.py` aus den Rohergebnissen unter
`smartbugs/results/<werkzeug>/curated_v1_20260705/`. Die Zaehlweise und die
DASP-Zuordnung stammen aus `evaluate_curated.py`; dieselben Zahlen gibt
dessen Konsolenausgabe aus (System-Python oder SmartBugs-venv, beide mit
PyYAML):

```powershell
python evaluate_curated.py --suffix v1_20260705 `
    --tools gptscan llmsmartaudit slither-0.11.3 --csv
```

Ground Truth: `smartbugs-curated/vulnerabilities.json` auf Commit `230e649`
(`run_curated.ps1` pinnt den Clone auf `230e649`, 16.06.2024).

Alle Werte sind **Contract-Level**: ein gelabelter Contract gilt als
erkannt, wenn das Werkzeug mindestens ein Finding meldet, dessen
DASP-Klassifikation auf die gelabelte Kategorie abbildet.

## Gesamtbild

| Werkzeug | Recall | Precision | F1 | Findings | davon DASP-zugeordnet | Kosten |
|---|---:|---:|---:|---:|---:|---:|
| gptscan | 0 % | 0 % | – | 6 | 6 | $0.01 |
| llmsmartaudit | 97 % | 30 % | 45 % | 1 124 | 656 | $2.44 |
| slither-0.11.3 | 67 % | 45 % | 54 % | 2 154 | 391 | $0.00 |

## gptscan

| Kategorie | Contracts | Erkannt | Recall | Recall 95-%-Intervall | Geflaggt | Precision | Basisrate | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| access_control | 18 | 0 | 0 % | 0–18 % | 6 | 0 % | 13 % | – |
| arithmetic | 15 | 0 | 0 % | 0–20 % | 0 | – | 10 % | – |
| bad_randomness | 8 | 0 | 0 % | 0–32 % | 0 | – | 6 % | – |
| denial_of_service | 6 | 0 | 0 % | 0–39 % | 0 | – | 4 % | – |
| front_running | 4 | 0 | 0 % | 0–49 % | 0 | – | 3 % | – |
| other | 3 | 0 | 0 % | 0–56 % | 0 | – | 2 % | – |
| reentrancy | 31 | 0 | 0 % | 0–11 % | 0 | – | 22 % | – |
| short_addresses | 1 | 0 | 0 % | 0–79 % | 0 | – | 1 % | – |
| time_manipulation | 5 | 0 | 0 % | 0–43 % | 0 | – | 3 % | – |
| unchecked_low_level_calls | 52 | 0 | 0 % | 0–7 % | 0 | – | 36 % | – |
| **GESAMT** | **143** | **0** | **0 %** | **0–3 %** | **6** | **0 %** | – | **–** |

*Basisrate*: Anteil der Contracts mit diesem Label an allen 143 Contracts
des Laufs -- die Precision, die ein Werkzeug erreichte, das die Kategorie
auf jedem Contract meldet. Eine Precision knapp ueber der Basisrate
unterscheidet sich kaum vom Raten. *Recall 95-%-Intervall*: Wilson-Intervall;
bei Kategorien mit acht oder weniger Contracts ist es breiter als 40
Prozentpunkte, der Punktwert allein traegt dort wenig.

0 der 6 Findings tragen keine DASP-Klassifikation und gehen weder in
Recall noch in Precision ein (0.0 %).

## llmsmartaudit

| Kategorie | Contracts | Erkannt | Recall | Recall 95-%-Intervall | Geflaggt | Precision | Basisrate | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| access_control | 18 | 18 | 100 % | 82–100 % | 94 | 19 % | 13 % | 32 % |
| arithmetic | 15 | 15 | 100 % | 80–100 % | 75 | 20 % | 10 % | 33 % |
| bad_randomness | 8 | 7 | 88 % | 53–98 % | 16 | 44 % | 6 % | 58 % |
| denial_of_service | 6 | 6 | 100 % | 61–100 % | 77 | 8 % | 4 % | 14 % |
| front_running | 4 | 4 | 100 % | 51–100 % | 45 | 9 % | 3 % | 16 % |
| other | 3 | 0 | 0 % | 0–56 % | 0 | – | 2 % | – |
| reentrancy | 31 | 31 | 100 % | 89–100 % | 72 | 43 % | 22 % | 60 % |
| short_addresses | 1 | 0 | 0 % | 0–79 % | 0 | – | 1 % | – |
| time_manipulation | 5 | 5 | 100 % | 57–100 % | 19 | 26 % | 3 % | 42 % |
| unchecked_low_level_calls | 52 | 52 | 100 % | 93–100 % | 66 | 79 % | 36 % | 88 % |
| **GESAMT** | **143** | **138** | **97 %** | **92–98 %** | **464** | **30 %** | – | **45 %** |

*Basisrate*: Anteil der Contracts mit diesem Label an allen 143 Contracts
des Laufs -- die Precision, die ein Werkzeug erreichte, das die Kategorie
auf jedem Contract meldet. Eine Precision knapp ueber der Basisrate
unterscheidet sich kaum vom Raten. *Recall 95-%-Intervall*: Wilson-Intervall;
bei Kategorien mit acht oder weniger Contracts ist es breiter als 40
Prozentpunkte, der Punktwert allein traegt dort wenig.

468 der 1 124 Findings tragen keine DASP-Klassifikation und gehen weder in
Recall noch in Precision ein (41.6 %).

## slither-0.11.3

| Kategorie | Contracts | Erkannt | Recall | Recall 95-%-Intervall | Geflaggt | Precision | Basisrate | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| access_control | 18 | 7 | 39 % | 20–61 % | 33 | 21 % | 13 % | 27 % |
| arithmetic | 15 | 0 | 0 % | 0–20 % | 0 | – | 10 % | – |
| bad_randomness | 8 | 3 | 38 % | 14–69 % | 13 | 23 % | 6 % | 29 % |
| denial_of_service | 6 | 1 | 17 % | 3–56 % | 17 | 6 % | 4 % | 9 % |
| front_running | 4 | 0 | 0 % | 0–49 % | 0 | – | 3 % | – |
| other | 3 | 0 | 0 % | 0–56 % | 0 | – | 2 % | – |
| reentrancy | 31 | 29 | 94 % | 79–98 % | 39 | 74 % | 22 % | 83 % |
| short_addresses | 1 | 0 | 0 % | 0–79 % | 0 | – | 1 % | – |
| time_manipulation | 5 | 5 | 100 % | 57–100 % | 24 | 21 % | 3 % | 34 % |
| unchecked_low_level_calls | 52 | 51 | 98 % | 90–100 % | 88 | 58 % | 36 % | 73 % |
| **GESAMT** | **143** | **96** | **67 %** | **59–74 %** | **214** | **45 %** | – | **54 %** |

*Basisrate*: Anteil der Contracts mit diesem Label an allen 143 Contracts
des Laufs -- die Precision, die ein Werkzeug erreichte, das die Kategorie
auf jedem Contract meldet. Eine Precision knapp ueber der Basisrate
unterscheidet sich kaum vom Raten. *Recall 95-%-Intervall*: Wilson-Intervall;
bei Kategorien mit acht oder weniger Contracts ist es breiter als 40
Prozentpunkte, der Punktwert allein traegt dort wenig.

1 763 der 2 154 Findings tragen keine DASP-Klassifikation und gehen weder in
Recall noch in Precision ein (81.8 %).

## Die wichtigste Einschraenkung

1 763 der 2 154 Slither-Findings (81.8 %) haben weder in SmartBugs'
`findings.yaml` noch ueber die kanonischen Zusatz-Mappings in
`evaluate_curated.py` (`timestamp` -> DASP-8, `weak-prng` -> DASP-6,
`unchecked-lowlevel`/`unchecked-send`/`unchecked-transfer` -> DASP-4)
eine DASP-Zuordnung und
gehen deshalb nicht in Recall und Precision ein. Keine Zuordnung heisst
nicht belanglos: nach der Impact-Stufe des jeweiligen Detektors sind
1 480 davon Informational oder Optimization, 166 Low, 60 Medium und 57 High.
Die Herleitung steht in `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`,
Abschnitt 4.1 und 5.

Weitere Einschraenkungen stehen je Werkzeug in der `README.md` des
zugehoerigen Ordners `eval/curated_v1_20260705__<werkzeug>/`.

