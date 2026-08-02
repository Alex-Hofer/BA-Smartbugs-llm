# Errors und Fails je Lauf

SmartBugs trennt **errors** (das Werkzeug hat das Problem bemerkt, behandelt
und weitergearbeitet) von **fails** (eine Exception ist dem Werkzeug entkommen
oder der Lauf wurde von aussen abgebrochen). Die Trennung stammt aus
`smartbugs/sb/parse_utils.py::errors_fails`; hergeleitet in
`docs/BA-ERRORS-VS-FAILS.md`.

Erzeugt mit `python analysis_tools/errors_fails_report.py --md ... --csv ...`.

## Bilanz je Lauf

| Tool | Lauf | Tasks | sauber | Tasks mit Errors | Tasks mit Fails | Errors | Fails | nicht uebersetzt |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| gptscan | assign6_dry | 10 | 9 | 1 | 0 | 7 | 0 | 0 |
| gptscan | assign6_dry_0_6_12 | 10 | 9 | 1 | 0 | 7 | 0 | 0 |
| gptscan | assign6_dry_0_8_24 | 10 | 9 | 1 | 0 | 7 | 0 | 0 |
| gptscan | assign6_live | 10 | 10 | 0 | 0 | 0 | 0 | 0 |
| gptscan | assign6_live_0612 | 10 | 10 | 0 | 0 | 0 | 0 | 0 |
| gptscan | curated_gptscan_mwe_20260706 | 96 | 1 | 95 | 23 | 278 | 40 | 95 |
| gptscan | curated_gptscan_mwefixed_dry | 96 | 41 | 55 | 0 | 483 | 0 | 2 |
| gptscan | curated_gptscan_mwefixed_live | 96 | 60 | 36 | 0 | 175 | 0 | 1 |
| gptscan | curated_gptscan_v1_20260705 | 143 | 141 | 2 | 0 | 8 | 0 | 0 |
| gptscan | mwevar_dry | 96 | 1 | 95 | 23 | 266 | 40 | 95 |
| gptscan | mwevar_live | 27 | 0 | 27 | 0 | 101 | 0 | 27 |
| gptscan | phase6_dry | 15 | 3 | 12 | 0 | 39 | 0 | 12 |
| gptscan | phase6_live | 15 | 3 | 12 | 0 | 41 | 0 | 12 |
| gptscan | smoke1_dry | 3 | 1 | 2 | 0 | 6 | 0 | 1 |
| gptscan | smoke2_live | 3 | 2 | 1 | 0 | 3 | 0 | 1 |
| llmsmartaudit | curated_llmsa_v1_20260705 | 143 | 143 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | smoke1_stub | 1 | 0 | 1 | 1 | 3 | 2 | 0 |
| llmsmartaudit | smoke2_live | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| slither-0.11.3 | curated_slither_v1_20260705 | 143 | 140 | 3 | 3 | 3 | 9 | 0 |
| **Summe** | | **930** | **586** | **344** | **50** | **1427** | **91** | **246** |

Spalte *sauber*: Tasks ohne jeden Error und Fail. Spalte *nicht uebersetzt*:
Tasks, deren Contract nicht kompiliert werden konnte — dort ist ein leeres
Finding-Ergebnis unbestimmt, nicht sauber.

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
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 3 | analysis unsuccessful, check output.json |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 3 | error parsing results: file could not be opened successfully: - method gz: ReadError('empty file') - method bz2: ReadError('not a bzip2 file') - method xz: ReadError('not an lzma file') - method tar: ReadError('empty file') |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 2 | exception (AssertionError) |
| llmsmartaudit | smoke1_stub | fail | independent | 1 | exception (openai.BadRequestError: Error code: 400 - {'error': {'message': 'The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed STUB.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}) |
| llmsmartaudit | smoke1_stub | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x7ff553bdcbe0 state=finished raised BadRequestError>]) |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 1 | exception (slither.visitors.expression.constants_folding.NotConstant) |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 54 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 47 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 281, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 47 | TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 36 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 360, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 35 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 31 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 22 | EXIT_CODE_1 |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 22 | GPTScan reported success=false: no output produced |
| gptscan | mwevar_dry | error | consequence | 22 | EXIT_CODE_1 |
| gptscan | mwevar_dry | error | consequence | 22 | GPTScan reported success=false: no output produced |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 19 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 14 | AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 14 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 250, in si ... ower() in answer[to_exclude_key].lower(): AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | mwevar_dry | error | consequence | 13 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | mwevar_live | error | consequence | 10 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 9 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 256, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 9 | IndexError: list index out of range |
| gptscan | mwevar_live | error | consequence | 9 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | phase6_dry | error | consequence | 8 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 6 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 336, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 5 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | curated_gptscan_mwe_20260706 | error | consequence | 4 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | mwevar_live | error | consequence | 4 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | mwevar_live | error | consequence | 4 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 3 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 256, in si ... ingle return {answer_key: list(data.values())[0]} IndexError: list index out of range call_arg_check |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 3 | IndexError: list index out of range call_arg_check |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 3 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 232, in si ... ue", s, err.value) from None json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| gptscan | curated_gptscan_mwefixed_live | error | independent | 3 | json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| gptscan | mwevar_dry | error | consequence | 3 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | phase6_live | error | consequence | 3 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | phase6_live | error | consequence | 3 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 245, in si ... lidation") Exception: The description of variable did not pass the `validate_description` validation |
| gptscan | phase6_live | error | consequence | 3 | WARNING  static_check: Falcon is not initialized, skipping first deposit check |
| slither-0.11.3 | curated_slither_v1_20260705 | error | independent | 3 | EXIT_CODE_1 |
| gptscan | curated_gptscan_mwe_20260706 | error | root_cause | 2 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Warning: SPDX license i ... ppelin/contracts/token/ERC20/IERC20.sol"; \| ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ |
| gptscan | curated_gptscan_v1_20260705 | error | independent | 2 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | mwevar_dry | error | consequence | 2 | AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | mwevar_dry | error | consequence | 2 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 250, in si ... ower() in answer[to_exclude_key].lower(): AttributeError: 'NoneType' object has no attribute 'lower' |
| gptscan | mwevar_dry | error | consequence | 2 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 256, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | mwevar_dry | error | consequence | 2 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 336, in si ... r_static_json_single return {answer_key: list(data.values())[0]} IndexError: list index out of range |
| gptscan | mwevar_dry | error | consequence | 2 | IndexError: list index out of range |
| gptscan | mwevar_dry | error | root_cause | 2 | falcon.exceptions.FalconError: Invalid compilation: Invalid solc compilation Warning: SPDX license i ... ppelin/contracts/token/ERC20/IERC20.sol"; \| ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ |
| gptscan | phase6_live | error | consequence | 2 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 325, in si ... ble did not pass the validation") Exception: The description of variable did not pass the validation |
| gptscan | assign6_dry | error | independent | 1 | ERROR    tasks: Current File: /work/input/SmartBillions.sol, current function: commitDividend, current vul: first-deposit |
| gptscan | assign6_dry | error | independent | 1 | ERROR    tasks: Current File: /work/input/SmartBillions.sol, current function: disinvest, current vul: first-deposit |
| gptscan | assign6_dry | error | independent | 1 | ERROR    tasks: Current File: /work/input/SmartBillions.sol, current function: invest, current vul: first-deposit |
| gptscan | assign6_dry | error | independent | 1 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | assign6_dry | error | independent | 1 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 281, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| gptscan | assign6_dry | error | independent | 1 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 360, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| ... | | | | | *892 weitere Meldungen, vollstaendig in der CSV* |
