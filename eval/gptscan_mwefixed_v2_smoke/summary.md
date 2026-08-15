# GPTScan-Lauf `gptscan_mwefixed_v2_smoke` -- Auswertung

Erzeugt 2026-08-15T16:19:30.595066+00:00 von `analysis_tools/gptscan_eval.py`.
Rohergebnisse: `smartbugs/results/gptscan/gptscan_mwefixed_v2_smoke` (unveraendert).

## Eckdaten

| | |
|---|---|
| Contracts | 3 |
| Findings | 0 auf 0 Contracts |
| Provider / Modell | deepseek / deepseek-v4-flash |
| MAIN | True |
| processes / timeout / mem-limit | 3 / 1800 s / 4g |
| Kosten | $0.0177 (Median $0.00444, max $0.01325) |
| Tokens | 51323 prompt / 37514 completion, 92 LLM-Calls |
| Laufzeit | Wanduhr 298.2 s, Task-Summe 443.4 s, Median 134.3 s, max 291.0 s |

Der Timeout wird derzeit nur von Docker durchgesetzt, nicht vom Werkzeug selbst (AP5, offen).

## Zustaende

Begriffe nach `docs/BA-ERRORS-VS-FAILS.md`.

| Zustand | Anzahl | Bedeutung |
|---|---|---|
| findings | 0 | Verdachtsfall ueber den Contract |
| Tasks mit errors | 2 | Werkzeug hat das Problem bemerkt, abgefangen und weitergearbeitet |
| Tasks mit fails | 0 | Werkzeug ausgehebelt, kein Ergebnis zustande gekommen |
| Contract nicht uebersetzt (degraded) | 0 | Compilat gescheitert -> ein Lauf ohne Findings ist hier UNBESTIMMT, nicht sauber |
| ohne Findings, sauber | 3 | uebersetzt, vollstaendig gelaufen, nichts gemeldet |

**Fehlerquote** (Tasks mit fails / alle Tasks): 0/3 = 0.0 %.
**Errorquote** (Tasks mit errors / alle Tasks): 2/3 = 66.7 %.

## Findings je Kategorie

`category_defi_logic` = die Regel hat in SWC/DASP kein redliches Gegenstueck (8 von 10, so in `findings.yaml` begruendet).

| MWE-Regel | Anzahl | Contracts | DeFi-Logik | DASP-10 | SWC |
|---|---:|---:|---|---|---|

Regeln ohne Treffer in diesem Lauf: 10 von 10

- MWE-200: Insecure LP Token Value Calculation
- MWE-201: Insecure Vote Calculation
- MWE-202: Insecure Token Buying Behavior
- MWE-203: Approval Not Revoked
- MWE-204: Unsafe First Deposit
- MWE-205: Front Running
- MWE-206: No Slippage Limit Check
- MWE-207: Unauthorized Transfer
- MWE-208: Wrong Order for Checkpoint
- MWE-209: Wrong Order for Interest or ExchangeRate

### Severity

| Severity | Findings |
|---|---:|

## Findings je Contract

0 von 3 Contracts tragen mindestens ein Finding.

| Contract | Findings | Regeln |
|---|---:|---|

## Contracts ohne Findings

3 Contracts sind uebersetzt, vollstaendig gelaufen und melden nichts. Getrennt davon: 0 nicht uebersetzt (unbestimmt) und 0 fails.

`14_IdleYieldSource`, `23_nTokenAction`, `25_CTokenInterface`

## Vorbehalte zu den Feldern in findings.jsonl

- `confidence` ist immer `null`. GPTScans `output.json` kennt nur `code`, `severity`, `title`, `description`, `recommendation`, `affectedFiles` -- einen Konfidenzwert gibt das Werkzeug nicht aus. Das Feld bleibt leer, statt einen Wert zu erfinden.
- `function` ist heuristisch aus dem analysierten Quelltext bestimmt (Deklarationskopf + Klammerzaehlung), nicht von GPTScan geliefert. Wo die Zuordnung nicht greift, bleibt das Feld leer.
- `lines` bezieht sich auf die Datei, die GPTScan tatsaechlich gesehen hat: 0 Contracts main-reduziert, 3 voll, 0 unbestimmt. Das Feld `lines_refer_to` haelt das je Finding fest. Zeilennummern aus einem MAIN-Lauf sind mit denen eines Laufs ohne MAIN NICHT vergleichbar.
- `dasp10` bleibt leer, wo `findings.yaml` kein redliches Mapping kennt. Die dort unter `related` vermerkten Naeherungen werden bewusst NICHT eingesetzt.
