# GPTScan-Lauf `gptscan_mwefixed_v2_smoke2` -- Auswertung

Erzeugt 2026-09-25T16:18:30.730133+00:00 von `analysis_tools/gptscan_eval.py`.
Rohergebnisse: `smartbugs/results/gptscan/gptscan_mwefixed_v2_smoke2` (unveraendert).

## Eckdaten

| | |
|---|---|
| Contracts | 3 |
| Findings | 6 auf 2 Contracts |
| Provider / Modell | deepseek / deepseek-v4-flash |
| MAIN | True |
| processes / timeout / mem-limit | 3 / 1800 s / 4g |
| Kosten | $0.0272 (Median $0.00874, max $0.01417) |
| Tokens | 47073 prompt / 73738 completion, 90 LLM-Calls |
| Laufzeit | Wanduhr 352.8 s, Task-Summe 697.7 s, Median 218.1 s, max 345.8 s |

Der Timeout wirkt seit AP5 im Container (Bremse bei GPTScan, Netz als letzte Stufe); Docker bleibt als aeusserer Fallback bestehen.

## Zustaende

Begriffe nach `docs/BA-ERRORS-VS-FAILS.md`.

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| findings | 6 | Verdachtsfall ueber den Contract |
| Tasks mit errors | 2 | Werkzeug hat das Problem bemerkt, abgefangen und weitergearbeitet |
| Tasks mit fails | 0 | Werkzeug ausgehebelt, kein Ergebnis zustande gekommen |
| Contract nicht uebersetzt (degraded) | 0 | Compilat gescheitert -> ein Lauf ohne Findings ist hier UNBESTIMMT, nicht sauber |
| ohne Findings, sauber | 1 | uebersetzt, vollstaendig gelaufen, nichts gemeldet |

Davon Teillaeufe (Timeout): 0 von 3. Ein durch die AP5-Deadline vorzeitig beendeter Lauf liefert weniger Findings als ein Volllauf; er bleibt dennoch in allen Zahlen oben mitgezaehlt, siehe `sb_timeout` in `docs/BA-AP5-TIMEOUT-DESIGN.md`.

**Fehlerquote** (Tasks mit fails / alle Tasks): 0/3 = 0.0 %.
**Errorquote** (Tasks mit errors / alle Tasks): 2/3 = 66.7 %.

## Findings je Kategorie

`category_defi_logic` = die Regel hat in SWC/DASP kein redliches Gegenstueck (8 von 10, so in `findings.yaml` begruendet).

| MWE-Regel | Anzahl | Contracts | DeFi-Logik | DASP-10 | SWC |
|---|---:|---:|---|---|---|
| MWE-200: Insecure LP Token Value Calculation | 5 | 2 | ja | -- | -- |
| MWE-206: No Slippage Limit Check | 1 | 1 | ja | -- | -- |

Regeln ohne Treffer in diesem Lauf: 8 von 10

- MWE-201: Insecure Vote Calculation
- MWE-202: Insecure Token Buying Behavior
- MWE-203: Approval Not Revoked
- MWE-204: Unsafe First Deposit
- MWE-205: Front Running
- MWE-207: Unauthorized Transfer
- MWE-208: Wrong Order for Checkpoint
- MWE-209: Wrong Order for Interest or ExchangeRate

### Severity

| Severity | Findings |
|---|---:|
| high | 6 |

## Findings je Contract

2 von 3 Contracts tragen mindestens ein Finding.

| Contract | Findings | Regeln |
|---|---:|---|
| `5_Router` | 3 | MWE-200, MWE-206 |
| `71_IndexTemplate` | 3 | MWE-200 |

## Contracts ohne Findings

1 Contracts sind uebersetzt, vollstaendig gelaufen und melden nichts. Getrennt davon: 0 nicht uebersetzt (unbestimmt) und 0 fails.

`14_BadgerYieldSource`

## Vorbehalte zu den Feldern in findings.jsonl

- `confidence` ist immer `null`. GPTScans `output.json` kennt nur `code`, `severity`, `title`, `description`, `recommendation`, `affectedFiles` -- einen Konfidenzwert gibt das Werkzeug nicht aus. Das Feld bleibt leer, statt einen Wert zu erfinden.
- `function` ist heuristisch aus dem analysierten Quelltext bestimmt (Deklarationskopf + Klammerzaehlung), nicht von GPTScan geliefert. Wo die Zuordnung nicht greift, bleibt das Feld leer.
- `lines` bezieht sich auf die Datei, die GPTScan tatsaechlich gesehen hat: 3 Contracts main-reduziert, 0 voll, 0 unbestimmt. Das Feld `lines_refer_to` haelt das je Finding fest. Zeilennummern aus einem MAIN-Lauf sind mit denen eines Laufs ohne MAIN NICHT vergleichbar.
- `dasp10` bleibt leer, wo `findings.yaml` kein redliches Mapping kennt. Die dort unter `related` vermerkten Naeherungen werden bewusst NICHT eingesetzt.
