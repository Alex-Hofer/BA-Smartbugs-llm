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
| llmsmartaudit | llmsa_mwefixed_v2 | 96 | 55 | 41 | 41 | 160 | 45 | 0 | 0 |
| llmsmartaudit | llmsa_mwefixed_v2_retry | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| llmsmartaudit | llmsa_smoke_curated | 3 | 2 | 1 | 1 | 4 | 1 | 0 | 0 |
| llmsmartaudit | smoke1_stub | 1 | 0 | 1 | 1 | 3 | 2 | 0 | 0 |
| llmsmartaudit | smoke2_live | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| slither-0.11.3 | curated_slither_v1_20260705 | 143 | 140 | 3 | 3 | 3 | 9 | 0 | 0 |
| **Summe** | | **1272** | **780** | **486** | **98** | **2330** | **149** | **249** | **10** |

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
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 4 | exception (openai.APIStatusError: Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}) |
| gptscan | gptscan_mwefixed_v2_dry | fail | independent | 3 | SmartBugs was invoked with option 'main', but the filename did not match any contract |
| gptscan | gptscan_mwefixed_v2_dry | fail | independent | 3 | no tar archive collected from the container |
| gptscan | gptscan_mwefixed_v2_main | fail | independent | 3 | SmartBugs was invoked with option 'main', but the filename did not match any contract |
| gptscan | gptscan_mwefixed_v2_main | fail | independent | 3 | no tar archive collected from the container |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 3 | analysis unsuccessful, check output.json |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 3 | error parsing results: file could not be opened successfully: - method gz: ReadError('empty file') - method bz2: ReadError('not a bzip2 file') - method xz: ReadError('not an lzma file') - method tar: ReadError('empty file') |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 2 | exception (AssertionError) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 126980}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 66624}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 66663}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 66798}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 66868}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 67108}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 67796}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 68712}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 68970}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 69518}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 70000}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 70032}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 70339}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 70448}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 70500}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 71536}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 71618}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 72588}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 75109}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 76456}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 76570}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 76912}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 77553}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 78618}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 80623}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 81192}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 81279}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 81504}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 84821}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 89881}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 89965}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 90117}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 92149}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 92976}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 93900}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 95209}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 97252}) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x706d249fb430 state=finished raised APIStatusError>]) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x77f8f87f4970 state=finished raised APIStatusError>]) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x7897bfc33730 state=finished raised APIStatusError>]) |
| llmsmartaudit | llmsa_mwefixed_v2 | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x7e3abc14b3d0 state=finished raised APIStatusError>]) |
| llmsmartaudit | llmsa_smoke_curated | fail | independent | 1 | exception (RuntimeError: error in ChatAgentResponse, info:{'id': None, 'usage': None, 'termination_reasons': ['max_tokens_exceeded_by_camel'], 'num_tokens': 68978}) |
| llmsmartaudit | smoke1_stub | fail | independent | 1 | exception (openai.BadRequestError: Error code: 400 - {'error': {'message': 'The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed STUB.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}) |
| llmsmartaudit | smoke1_stub | fail | independent | 1 | exception (tenacity.RetryError: RetryError[<Future at 0x7ff553bdcbe0 state=finished raised BadRequestError>]) |
| slither-0.11.3 | curated_slither_v1_20260705 | fail | independent | 1 | exception (slither.visitors.expression.constants_folding.NotConstant) |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 54 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | gptscan_mwefixed_v2_dry | error | independent | 50 | ERROR    tasks: Static analysis failed: Invalid args |
| gptscan | curated_gptscan_mwefixed_dry | error | independent | 47 | ERROR    tasks: Traceback (most recent call last): File "/opt/gptscan/src/tasks.py", line 281, in si ... ar1 in text and var2 in text: TypeError: 'in <string>' requires string as left operand, not NoneType |
| ... | | | | | *1380 weitere Meldungen, vollstaendig in der CSV* |
