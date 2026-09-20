# Errors und Fails je Lauf

SmartBugs trennt **errors** (das Werkzeug hat das Problem bemerkt, behandelt
und weitergearbeitet) von **fails** (eine Exception ist dem Werkzeug entkommen
oder der Lauf wurde von aussen abgebrochen). Die Trennung stammt aus
`smartbugs/sb/parse_utils.py::errors_fails`; hergeleitet in
`docs/BA-ERRORS-VS-FAILS.md`.

Erzeugt mit `python analysis_tools/errors_fails_report.py --md ... --csv ...`.

## Bilanz je Lauf

| Tool | Lauf | Tasks | sauber | Tasks mit Errors | Tasks mit Fails | Errors | Fails | nicht uebersetzt | Teillauf (Timeout) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gptscan | ap5_free_gptscan_brake | 2 | 0 | 2 | 0 | 39 | 0 | 0 | 1 |
| gptscan | ap5_free_gptscan_net | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | ap5_free_gptscan_net2 | 1 | 0 | 1 | 0 | 3 | 0 | 0 | 1 |
| gptscan | ap5_free_gptscan_notimeout | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | ap5_live_gptscan_full | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | ap5_live_gptscan_partial | 1 | 0 | 1 | 0 | 6 | 0 | 0 | 1 |
| gptscan | ap5_verify2_gptscan_full | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | ap5_verify2_gptscan_part | 1 | 0 | 1 | 0 | 6 | 0 | 0 | 1 |
| gptscan | ap5_verify_gptscan_brake | 1 | 0 | 1 | 0 | 22 | 0 | 0 | 1 |
| gptscan | ap5_verify_gptscan_net | 1 | 0 | 1 | 0 | 3 | 0 | 0 | 1 |
| gptscan | ap5_verify_gptscan_notimeout | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | assign6_dry | 10 | 9 | 1 | 0 | 7 | 0 | 0 | 0 |
| gptscan | assign6_dry_0_6_12 | 10 | 9 | 1 | 0 | 7 | 0 | 0 | 0 |
| gptscan | assign6_dry_0_8_24 | 10 | 9 | 1 | 0 | 7 | 0 | 0 | 0 |
| gptscan | assign6_live | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | assign6_live_0612 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | curated_gptscan_demo_defi | 5 | 2 | 3 | 0 | 17 | 0 | 0 | 0 |
| gptscan | curated_gptscan_demo_swc | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| gptscan | curated_gptscan_mwe_20260706 | 96 | 1 | 95 | 23 | 278 | 40 | 95 | 0 |
| gptscan | curated_gptscan_mwefixed_dry | 96 | 41 | 55 | 0 | 483 | 0 | 2 | 0 |
| gptscan | curated_gptscan_mwefixed_live | 96 | 60 | 36 | 0 | 175 | 0 | 1 | 0 |
| gptscan | curated_gptscan_v1_20260705 | 143 | 141 | 2 | 0 | 8 | 0 | 0 | 0 |
| gptscan | gptscan_mwefixed_v2_dry | 96 | 42 | 51 | 3 | 457 | 6 | 2 | 0 |
| gptscan | gptscan_mwefixed_v2_main | 96 | 63 | 30 | 3 | 157 | 6 | 1 | 0 |
| gptscan | gptscan_mwefixed_v2_main_nomain | 3 | 2 | 1 | 0 | 4 | 0 | 0 | 0 |
| gptscan | gptscan_mwefixed_v2_smoke | 3 | 1 | 2 | 0 | 8 | 0 | 0 | 0 |
| gptscan | gptscan_mwefixed_v2_smoke2 | 3 | 1 | 2 | 0 | 9 | 0 | 0 | 0 |
| gptscan | mwevar_dry | 96 | 1 | 95 | 23 | 266 | 40 | 95 | 0 |
| gptscan | mwevar_live | 27 | 0 | 27 | 0 | 101 | 0 | 27 | 0 |
| gptscan | phase6_dry | 15 | 3 | 12 | 0 | 39 | 0 | 12 | 0 |
| gptscan | phase6_live | 15 | 3 | 12 | 0 | 41 | 0 | 12 | 0 |
| gptscan | smoke1_dry | 3 | 1 | 2 | 0 | 6 | 0 | 1 | 0 |
| gptscan | smoke2_live | 3 | 2 | 1 | 0 | 3 | 0 | 1 | 0 |
| llmsmartaudit | ap5_free_llmsa_net | 2 | 0 | 2 | 0 | 4 | 0 | 0 | 2 |
| llmsmartaudit | ap5_free_llmsa_notimeout | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | ap5_live_llmsa_full | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | ap5_live_llmsa_partial | 1 | 0 | 1 | 0 | 2 | 0 | 0 | 1 |
| llmsmartaudit | ap5_verify_llmsa_net | 1 | 0 | 1 | 0 | 2 | 0 | 0 | 1 |
| llmsmartaudit | curated_llmsa_demo_defi_llm | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | curated_llmsa_demo_kostenprobe | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | curated_llmsa_demo_swc_llm | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | curated_llmsa_v1_20260705 | 143 | 143 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | smoke1_stub | 1 | 0 | 1 | 1 | 3 | 2 | 0 | 0 |
| llmsmartaudit | smoke2_live | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| slither-0.11.3 | curated_slither_v1_20260705 | 143 | 140 | 3 | 3 | 3 | 9 | 0 | 0 |
| **Summe** | | **1169** | **719** | **444** | **56** | **2166** | **103** | **249** | **10** |

Spalte *sauber*: Tasks ohne jeden Error und Fail. Spalte *nicht uebersetzt*:
Tasks, deren Contract nicht kompiliert werden konnte — dort ist ein leeres
Finding-Ergebnis unbestimmt, nicht sauber. Spalte *Teillauf (Timeout)*: Tasks,
deren Lauf durch die AP5-Deadline vorzeitig beendet wurde (AP5); sie zaehlen
regulaer in *Tasks* mit, statt herausgerechnet zu werden.

## Meldungen im Wortlaut

Klassifikation: `root_cause` benennt das Compilat selbst, `consequence` ist
eine Folge davon, `independent` steht fuer sich. Die Einordnung ersetzt keine
Meldung — jede wird unveraendert wiedergegeben.

| Tool | Lauf | Art | Klassifikation | Contracts | Meldung |
|---|---|---|---|---:|---|
| gptscan | curated_gptscan_mwe_20260706 | fail | consequence | 20 | exception (TypeError: 'NoneType' object is not subscriptable) |
| gptscan | curated_gptscan_mwe_20260706 | fail | consequence | 20 | exception (UnboundLocalError: local variable 'match_flag' referenced before assignment) |
| gptscan | mwevar_dry | fail | consequence | 20 | exception (TypeError: 'NoneType' object is not subscriptable) |
| gptscan | mwevar_dry | fail | consequence | 20 | exception (UnboundLocalError: local variable 'match_flag' referenced before assignment) |
| gptscan | gptscan_mwefixed_v2_dry | fail | independent | 3 | SmartBugs was invoked with option 'main', but the filename did not match any contract |
| gptscan | gptscan_mwefixed_v2_dry | fail | independent | 3 | no tar archive collected from the container |
| gptscan | gptscan_mwefixed_v2_main | fail | independent | 3 | SmartBugs was invoked with option 'main', but the filename did not match any contract |
| gptscan | gptscan_mwefixed_v2_main | fail | independent | 3 | no tar archive collected from the container |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 3 | analysis unsuccessful, check output.json |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 3 | error parsing results: file could not be opened successfully: - method gz: ReadError('empty file') - method bz2: ReadError('not a bzip2 file') - method xz: ReadError('not an lzma file') - method tar: ReadError('empty file') |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 2 | exception (AssertionError) |
| llmsmartaudit | smoke1_stub | fail | independent | 1 | exception (openai.BadRequestError: Error code: 400 - {'error': {'message': 'The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed STUB.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}) |
| llmsmartaudit | smoke1_stub | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x7ff553bdcbe0 state=finished raised BadRequestError>]) |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 1 | exception (slither.visitors.expression.constants_folding.NotConstant) |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 54 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 50 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 47 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 281, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 47 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 43 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 281, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 43 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 36 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 360, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 35 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 33 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 360, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 31 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 27 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 23 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 22 | EXIT_CODE_1 |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 22 | GPTScan reported success=false: no output produced |
| gptscan | mwevar_dry | error | consequence | 22 | EXIT_CODE_1 |
| gptscan | mwevar_dry | error | consequence | 22 | GPTScan reported success=false: no output produced |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 19 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 14 | AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 14 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 250, in si ... ower() in answer[to_exclude_key].lower(): AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 14 | AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 14 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 250, in si ... ower() in answer[to_exclude_key].lower(): AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 13 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | mwevar_dry | error | consequence | 13 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | mwevar_live | error | consequence | 10 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 9 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 256, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 9 | IndexError: list index out of range |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 256, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 9 | IndexError: list index out of range |
| gptscan | mwevar_live | error | consequence | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | phase6_dry | error | consequence | 8 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 7 | TimeoutError: Timeout |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 6 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 336, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 6 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 336, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 5 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 4 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 4 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 232, in si ... ue", s, err.value) from None json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 4 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 312, in si ... lyze_pipeline.py" , line 87, in ask_with_timeout raise TimeoutError("Timeout") TimeoutError: Timeout |
| gptscan | gptscan_mwefixed_v2_main | error | independent | 4 | json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| gptscan | mwevar_live | error | consequence | 4 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | mwevar_live | error | consequence | 4 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | curated_gptscan_demo_defi | error | independent | 3 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_demo_defi | error | independent | 3 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 3 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 256, in si ... ingle return {answer_key: list(data.values())[0]} IndexError: list index out of range call_arg_check |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 3 | IndexError: list index out of range call_arg_check |
| ... | | | | | *1329 weitere Meldungen, vollstaendig in der CSV* |
