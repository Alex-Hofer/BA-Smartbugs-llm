# eval/per_contract/ — eine Zeile je Contract

Erzeugt von [`analysis_tools/per_contract_stats.py`](../../analysis_tools/per_contract_stats.py)
am 2026-09-16.

> **Zweck und Geltungsbereich (Entscheidung vom 2026-09-16).** Diese Tabellen
> und das Skript sind eine **Auswertungshilfe für die Bachelorarbeit** — damit
> die Läufe je Contract verglichen und ausgewertet werden können. Sie sind
> **nicht Teil der Werkzeugintegration**: GPTScan, LLMSmartAudit, SmartBugs,
> Parser und Entrypoints bleiben unverändert, und eine Instrumentierung der
> Werkzeuge wird nicht verfolgt.
>
> **Verlässlich sind die Werte für die neun Läufe (zwölf Dateien) unten**, mit
> der bei `llmsa_mwefixed_v2` genannten Einschränkung. Auf andere Läufe
> angewendet liefert das Skript in seiner jetzigen Form an bestimmten Stellen
> irreführende Werte — siehe „Bekannte Einschränkungen". **Insbesondere die
> LLMSmartAudit-v2-Läufe nicht damit auswerten**, sondern deren Gesamtzahlen aus
> `eval/llmsa_curated_v2/run_meta.json` und `eval/llmsa_mwefixed_v2/run_meta.json`
> verwenden.

**Hier steht keine neue Messung.** Jede Zahl liegt schon in den Rohergebnissen
unter `smartbugs/results/`; sie wird nur je Contract zusammengetragen, weil die
bestehenden Auswertungen (`gptscan_eval.py`, `build_eval.py`) ausschließlich
Laufsummen exportieren. Es wurde kein Lauf wiederholt und kein API-Aufruf
gemacht.

## Dateien

| Datei | Lauf | Zeilen |
|---|---|---:|
| `curated_v1_20260705__gptscan.csv` | GPTScan über `smartbugs-curated` | 143 |
| `curated_v1_20260705__llmsmartaudit.csv` | LLMSmartAudit über `smartbugs-curated` | 143 |
| `curated_v1_20260705__llmsmartaudit__phases.csv` | dieselbe Messung, je Detektor-Phase | 6 174 |
| `curated_v1_20260705__slither-0.11.3.csv` | Slither über `smartbugs-curated` | 143 |
| `curated_mwefixed_live__gptscan.csv` | GPTScan über `mwevariety_fixed`, ohne MAIN | 96 |
| `gptscan_mwefixed_v2_main__gptscan.csv` | GPTScan über `mwevariety_fixed`, MAIN=1, mit eingemischtem Nachlauf `_nomain` | 96 |
| `slither_mwefixed_v1__slither-0.11.3.csv` | Slither über `mwevariety_fixed` (24.09.2026, Upstream-Image); 45 Contracts ohne Ergebnis, Ursache in `docs/BA-WERKZEUGE-IM-VERGLEICH.md` 4.2 | 96 |
| `slither_mwefixed_v2__slither-0.11.3-glibc.csv` | Slither über `mwevariety_fixed` (24.09.2026, eigenes glibc-Image); 95 von 96 analysiert, der Rest ein Compilerfehler, siehe `docs/BA-WERKZEUGE-IM-VERGLEICH.md` 4.2 | 96 |
| `llmsa_mwefixed_v2__llmsmartaudit.csv` | LLMSmartAudit über `mwevariety_fixed` (16.08.2026) mit eingemischtem Nachlauf `llmsa_mwefixed_v2_retry` (15.09.2026). **Vorbehalt:** Bei den 37 am Kontextfenster abgebrochenen Contracts bleiben `prompt_tokens`, `completion_tokens` und `cost_usd_est` leer (Einschränkung 1); Zustand, Findings, Aufrufe und Laufzeit sind vollständig. Die Summen treffen `eval/llmsa_mwefixed_v2/run_meta.json` (437 Findings, 2 624 Aufrufe, 90 206 s); die Kostensumme der 59 durchgelaufenen Contracts ist 8,10 USD gegen 8,37 USD für alle 96 | 96 |
| `llmsa_mwefixed_v2__llmsmartaudit__phases.csv` | dieselbe Messung, je Detektor-Phase | 2 661 |
| `llmsa_mwefixed_v2_ctx1m__llmsmartaudit.csv` | LLMSmartAudit über die 37 Kontext-Contracts mit angehobener Grenze (24.09.2026); kein Abbruch, alle Spalten gefüllt; Summen treffen `eval/llmsa_mwefixed_v2_ctx1m/run_meta.json` (317 Findings, 1 625 Aufrufe, 35 028 s, 11,42 USD geschätzt) | 37 |
| `llmsa_mwefixed_v2_ctx1m__llmsmartaudit__phases.csv` | dieselbe Messung, je Detektor-Phase | 1 625 |

`llmsa_curated_v2` fehlt hier und wird fehlen: Seine Rohergebnisse existieren
seit dem 24.09.2026 nirgends mehr (bis dahin auf dem Rechner des zweiten
Verfassers, siehe Runlog `eval/_runlogs/llmsa_full_20260815-181854.log`).
`llmsa_mwefixed_v2` (Rohdaten seit dem 20.09.2026 hier) und der Nachlauf
`llmsa_mwefixed_v2_ctx1m` sind seit dem 25.09.2026 aufgenommen; bei den 37
im Hauptlauf am Kontextfenster abgebrochenen Contracts bleiben die Token- und
Kostenzellen leer (Einschränkung 1), und das Skript meldet diese 37 beim
Erzeugen als „Phasenmarker ≠ Usage-Blöcke“. Für Kosten- und Token-Summen
dieses Laufs gelten die Werte in `eval/llmsa_mwefixed_v2/run_meta.json`.

## Woher jede Spalte kommt

### Für alle Werkzeuge

| Spalte | Quelle |
|---|---|
| `run_id`, `source_run` | Aufrufparameter; `source_run` sagt, aus welchem Lauf die Zeile stammt — bei eingemischten Nachläufen weicht sie von `run_id` ab |
| `contract_id` | Dateiname ohne `.sol` (`build_eval.contract_id`) |
| `task_dir` | Pfad des Task-Ordners unterhalb des Laufs. **Nötig, weil `contract_id` nicht eindeutig ist:** `0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` liegt in `smartbugs-curated` zweimal, unter `reentrancy/` und unter `unchecked_low_level_calls/` |
| `start_unix`, `duration_s`, `exit_code` | `smartbugs.json`, Feld `result` — `duration_s` ist die **Container**-Laufzeit |
| `main`, `timeout_s` | die letzten Argumente des Docker-Entrypoints (`FILENAME TIMEOUT BIN MAIN`). Bewusst von dort und nicht aus `run_meta.json`, weil die dortige Begründung zu `--main` am Code widerlegt ist |
| `state` | siehe unten |
| `n_findings`, `n_errors`, `n_fails` | Länge der Felder in `result.json` |

### Nur GPTScan (aus der Zeile `GPTSCAN_META` im `result.log`)

| Spalte | Bedeutung |
|---|---|
| `tool_time_s` | Laufzeit, die das Werkzeug selbst gemessen hat (`used_time`) — **nicht** dasselbe wie `duration_s` |
| `llm_calls`, `calls_skipped_budget`, `calls_skipped_deadline` | ausgeführte und übersprungene LLM-Aufrufe. Die Deadline-Spalte bleibt für Läufe vor AP5 leer, weil das Image das Feld noch nicht schrieb |
| `prompt_tokens`, `completion_tokens`, `cost_usd` | Tokens und die Kostenschätzung des Werkzeugs (Preise aus `GPTScan/src/config.py`) |
| `files`, `contracts`, `functions`, `loc` | Größe der Eingabe |
| `contracts_after_filter`, `…_step_1`, `…_step_2`, `…_static` | der Trichter: was nach Keyword-Vorfilter, den beiden LLM-Stufen und der statischen Bestätigung übrig blieb |
| `vul_before_static`, `vul_after_static`, `vul_after_merge` | Kandidaten vor und nach der Static-Stufe, danach dedupliziert |
| `degraded` | Contract nicht übersetzt — Ergebnis unbestimmt, **nie „keine Findings"** |
| `static_invalid_args` | die Static-Stufe ist abgestürzt (`Static analysis failed: Invalid args`) |

### Nur LLMSmartAudit (aus dem `result.log`)

Im Log stehen dieselben Wörter zweimal: als Vorab-Schätzung vor jedem Aufruf und
als echte Summe in der ChatDev-Statistik am Ende. Jede Spalte hängt deshalb an
einem festgelegten Muster.

| Spalte | Muster im Log |
|---|---|
| `tool_time_s` | `**duration**=…s` |
| `prompt_tokens`, `completion_tokens` | `**num_prompt_tokens**=…`, `**num_completion_tokens**=…` |
| `llm_calls` | Zahl der Usage-Blöcke (`prompt_tokens: …` / `completion_tokens: …`) |
| `phases`, `calls_match_phases` | Zahl der Phasenmarker und die Prüfung, ob zu jeder Phase ein Aufruf gehört |
| `max_prompt_est` | größter Wert aus `num_prompt_tokens (before adjustment)` — die Auslastung je Aufruf |
| `context_limit` | `num_max_token` (bei DeepSeek fest 65 536 in allen Läufen bis zum 24.09.2026; `LLM_CONTEXT_TOKENS` hob das damals nicht an, seit dem Image vom 24.09.2026 tut es das, `README.md`, Tabelle der Variablen) |
| `categories_checked` | aus `result.json` („categories checked: n/41") |
| `cost_usd_est` | **Hochrechnung**, nicht abgelesen: Preise aus `build_eval.py` (dort aus `curated_v1` zurückgerechnet). Das Werkzeug meldet $0,0000. Maßgeblich bleibt die DeepSeek-Rechnung |
| `sb_timeout_stage` | gedacht für `brake` oder `net` aus dem AP5-Marker — **derzeit immer leer**, siehe Einschränkung 3 |

### Phasentabelle

`run_id`, `contract_id`, `task_dir`, `phase_index`, `phase_name`, `calls`,
`prompt_tokens`, `completion_tokens`, `max_prompt_est`. Die Tokens eines
Aufrufs gehören zu dem Phasenmarker, der im Log davor steht.

**`calls` ist keine Zierspalte.** Über alle 143 Tasks von `curated_v1_20260705`
ist sie konstant 1, also ein Aufruf je Phase. In abgebrochenen Läufen nicht: In
`ap5_free_net` (`5_Vether.sol` und `45_CreditLimitByMedian.sol`) und
`ap5_verify_net` (`5_Vether.sol`) stehen 27 Phasen gegen 26 Aufrufe, in
`ap5_live_partial` 25 gegen 24 — die letzte Phase wurde begonnen, aber ihr
Aufruf nicht mehr protokolliert. In `smoke1_stub` steht 1 Phase gegen 0 Aufrufe,
weil die API den Aufruf ablehnte. Eine Phase ohne Aufruf zeigt also, wo ein Lauf
abgeschnitten wurde; `calls_match_phases` weist das je Contract aus.

### `state`

| Wert | Bedeutung |
|---|---|
| `findings` | das Werkzeug hat etwas gemeldet |
| `clean` | analysiert, nichts gemeldet |
| `degraded` | GPTScan: Compilat gescheitert — Ergebnis **unbestimmt** |
| `context_exceeded` | LLMSmartAudit: Kontextfenster überschritten, **nie analysiert** |
| `no_output` | keine Findings, aber `errors` gemeldet — meist ist kein Report entstanden; nach einem Timeout kann es auch ein Teilbericht ohne Findings sein (Einschränkung 3) |
| `failed` | `fails` — das Werkzeug wurde ausgehebelt |

`degraded`, `context_exceeded`, `no_output` und `failed` dürfen **nicht** als
`clean` gezählt werden. Für LLMSmartAudit stammt die Einteilung aus
`build_eval.task_state`, damit hier und in `eval/<runid>/` dieselbe Regel gilt.

## Zwei Regeln

1. **Fehlt eine Angabe, bleibt die Zelle leer — niemals 0.** Ein Task, der vor
   der Metadatenzeile abbrach, hat keine Kosten von null, sondern keine
   bekannten Kosten. Durchgehend leer ist deshalb `calls_skipped_deadline` in
   den Läufen vor AP5. `sb_timeout_stage` ist dagegen aus einem anderen Grund
   immer leer (Einschränkung 3).
2. **Ein Nachlauf ersetzt nur unentschiedene Tasks** und kann keinen Contract
   hinzufügen, den der Hauptlauf nicht hatte. Bei GPTScan sind das die Tasks
   mit `fails` (Regel aus `gptscan_eval.py`), bei LLMSmartAudit alle nicht
   entschiedenen (`build_eval.is_decided`), also auch Kontextabbrüche.

## Gegenprobe

Die Summen der Tabellen treffen die bereits dokumentierten Zahlen. Nachgerechnet
am 2026-09-16:

| Lauf | Soll | Tabelle |
|---|---|---|
| `gptscan_mwefixed_v2_main` + Nachlauf | 74 Findings auf 37 Contracts, 31 Tasks mit `errors`, 0 mit `fails`, Task-Summe 11 771,7 s, $0,3638, 736 374/930 986 Tokens, 1 518 Calls | alle getroffen |
| dieselbe Tabelle, `tool_time_s` | — | 10 156,1 s, also 13,7 % unter der Container-Summe. Zwei verschiedene Messgrößen, kein Widerspruch |
| `curated_mwefixed_live` | 77 Findings auf 40 Contracts, $0,2769 | getroffen; `static_invalid_args` in 35 von 96 Tasks, wie in `docs/BA-AUFGABEN-UND-STATUS.md` |
| `curated_v1_20260705`, GPTScan | 6 Findings, ≈$0,01, 72 Calls | getroffen |
| `curated_v1_20260705`, LLMSmartAudit | 1 124 Findings, 143/143 mit Findings, 6 174 Calls, 12,55 M/3,52 M Tokens, ≈$2,44 | getroffen |
| `curated_v1_20260705`, Slither | 143 Tasks, 2 154 Findings | getroffen |
| Phasentabelle gegen Contracttabelle | Tokensummen müssen gleich sein | 12 554 710 / 3 517 916 in beiden |

Die $2,44 sind **kein unabhängiger Beleg**: Die Preise in `build_eval.py` wurden
aus genau diesem Lauf zurückgerechnet. Die Zeile zeigt nur, dass die
Hochrechnung konsistent angewandt wird.

## Neuer Befund aus der Phasentabelle

Die teuersten Detektoren des curated-Laufs nach Prompt-Tokens:
`LackAuthorizationDetector` (339 685), `DoSDetector` (329 845),
`ReentrancyDetector` (319 619), `HashCollisionDetector` (315 008). Damit lässt
sich erstmals sagen, welche Phasen die Kosten treiben. Die Phasentabelle enthält
44 verschiedene Phasennamen: die 41 Detektoren sowie `ContractAnalysis`,
`Reflection` und `TestBugsSummary`.

## Bekannte Einschränkungen

Gefunden bei einer unabhängigen Prüfung am 2026-09-16. **Auf die Werte der zwölf
Dateien oben wirken sie sich nicht aus**, mit der oben genannten Ausnahme
der leeren Token- und Kostenzellen in `llmsa_mwefixed_v2`:** Keiner dieser Läufe wurde per Timeout
abgebrochen, keiner lief gegen den lokalen Prüfstand, und die drei im
GPTScan-Nachlauf ersetzten Tasks (`31_veCVXStrategy`, `62_Locke`,
`8_NFTXEligiblityManager`) scheiterten mit Exit-Code 127 an der MAIN-Prüfung der
eigenen Integration (`main_contract.py`: der Dateiname benennt keinen der
enthaltenen Contracts), bevor GPTScan lief. Die Einschränkungen 3 und 6 gelten
zwar auch für diese Läufe, bleiben dort aber folgenlos. Das Skript wurde bewusst nicht
mehr angepasst; wer es auf andere Läufe anwendet, muss Folgendes wissen:

1. **Abgebrochene LLMSmartAudit-Tasks: Tokens und Kosten bleiben leer, obwohl sie
   verbraucht wurden.** Das Skript liest die Tokens aus ChatDevs Endstatistik am
   Logende; bei einem Abbruch (Timeout, Kontextüberlauf) fehlt sie. Die
   Usage-Blöcke je Aufruf stehen trotzdem im Log. Beispiel `ap5_live_partial`:
   24 Aufrufe mit 71 458 Prompt-Tokens, Zelle leer.
2. **Läufe gegen den lokalen Prüfstand bekommen Scheinkosten.** `cost_usd_est`
   wird ohne Blick auf das Backend aus den DeepSeek-Preisen berechnet; der
   Prüfstand meldet aber Wortzahlen statt Tokens. Beispiel `ap5_free_notimeout`:
   0,0055 USD, obwohl nichts bezahlt wurde.
3. **`sb_timeout_stage` ist immer leer.** Das Skript sucht `output.json` im
   Task-Ordner, die Datei liegt aber nur in `result.tar`. Ein Teillauf (weniger
   als 41 geprüfte Kategorien, z. B. 23 in `ap5_live_partial`) ist deshalb nur an
   `categories_checked` zu erkennen, nicht an `state`.
4. **Ein Nachlauf ersetzt Zeilen, ohne deren Verbrauch auszuweisen.** Die Tokens
   der ersetzten Tasks des Hauptlaufs tauchen in keiner Tabelle mehr auf. In
   `llmsa_mwefixed_v2` wären das 725 901 Prompt- und 126 700 Completion-Tokens
   (rund 0,11 USD).
5. **Doppelte Contract-IDs in einem Nachlauf werden nicht abgefangen**, anders als
   in `build_eval.merge_tasks`; der Kommentar im Skript, die Merge-Logik sei
   „importiert", gilt nur für die Entscheidung, welcher Task ersetzt wird.
6. **Die Endstatistik ist kein unabhängiger Abgleich:** ChatDev summiert dieselben
   `prompt_tokens:`-Zeilen seiner eigenen Logdatei. Bei hart beendeten Läufen
   kann außerdem der Ausgabepuffer fehlen, weil `PYTHONUNBUFFERED` im Image nicht
   gesetzt ist — dort sind die Log-Werte bestenfalls Untergrenzen.

## Was diese Tabellen nicht enthalten

Vier Größen fehlen, weil die Werkzeuge sie nicht aufzeichnen. Sie wären nur mit
einem Eingriff in GPTScan und LLMSmartAudit zu bekommen; **dieser Eingriff wird
nicht verfolgt** (Entscheidung vom 2026-09-16):

* Zeit je Aufruf und je Phase (beide Werkzeuge)
* Tokens je Aufruf und je MWE-Regel (GPTScan)
* Cache- und Reasoning-Tokens (beide) — davon hängt ab, wie belastbar die
  Kostenhochrechnung ist
* ein Zähler für wiederholte Aufrufe (beide)

## Neu erzeugen

```powershell
python analysis_tools\per_contract_stats.py gptscan gptscan_mwefixed_v2_main --merge-run gptscan_mwefixed_v2_main_nomain
python analysis_tools\per_contract_stats.py gptscan curated_mwefixed_live
python analysis_tools\per_contract_stats.py gptscan curated_v1_20260705
python analysis_tools\per_contract_stats.py slither-0.11.3 curated_v1_20260705
python analysis_tools\per_contract_stats.py slither-0.11.3 slither_mwefixed_v1
python analysis_tools\per_contract_stats.py slither-0.11.3-glibc slither_mwefixed_v2
python analysis_tools\per_contract_stats.py llmsmartaudit curated_v1_20260705
```

Regressionstests: `python -m pytest tests/test_per_contract_stats.py -q`
