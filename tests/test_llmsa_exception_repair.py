"""Regression tests for ``_repair_exception_fails`` in the LLMSmartAudit parser.

Background
----------
``sb.parse_utils.exceptions`` treats the first *unindented* line after a
``Traceback (most recent call last):`` header as the exception. LLMSmartAudit
writes its token accounting (``num_prompt_tokens: ...``, ``String length: ...``)
to the same stream, unindented, so those lines can sit between the header and
the closing line. Upstream then reports the accounting line as the exception
and never reaches the real one.

Ten tasks in this project were affected. In four of them the true cause was
``openai.APIStatusError: Error code: 402 - Insufficient Balance`` — an
exhausted API balance, reported by upstream as ``num_prompt_tokens: 22878``.
Losing that turns an infrastructure outage into an apparent tool failure.

The repair runs in this parser, never in ``sb/parse_utils.py``: upstream
parsing stays untouched, so the fix travels with ``sb.reparse`` and affects no
other tool.
"""

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_DIR = os.path.join(REPO_ROOT, "smartbugs", "tools", "llmsmartaudit")
SMARTBUGS = os.path.join(REPO_ROOT, "smartbugs")

for p in (SMARTBUGS, TOOL_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="module")
def parser_mod():
    """The tool's parser module, loaded from its own directory."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "llmsa_parser", os.path.join(TOOL_DIR, "parser.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def repair(parser_mod):
    """``_repair_exception_fails`` from the tool's parser module."""
    return parser_mod._repair_exception_fails


# The shape observed in llmsa_mwefixed_v2/12_Witch.sol
BALANCE_LOG = [
    "Traceback (most recent call last):",
    '  File "/app/run.py", line 120, in <module>',
    "    main()",
    "num_prompt_tokens (before adjustment): 22878",
    "gap_between_send_receive: 60",
    "num_max_token: 65536",
    "  File \"/usr/local/lib/python3.10/site-packages/openai/_client.py\", line 1",
    "    raise self._make_status_error_from_response(err.response) from None",
    "openai.APIStatusError: Error code: 402 - {'error': {'message': "
    "'Insufficient Balance'}}",
]

CONTEXT_LOG = [
    "Traceback (most recent call last):",
    '  File "/app/chatdev/phase.py", line 88, in execute',
    "String length: 109412",
    "RuntimeError: error in ChatAgentResponse, info:{'termination_reasons': "
    "['max_tokens_exceeded_by_camel']}",
]


def test_replaces_accounting_line_with_the_real_cause(repair):
    """The exhausted-balance case: the 402 must survive, the noise must not."""
    fails = {"exception (num_prompt_tokens (before adjustment): 22878)"}

    repair(BALANCE_LOG, fails)

    assert not any("num_prompt_tokens" in f for f in fails)
    assert any("402" in f and "Insufficient Balance" in f for f in fails)


def test_replaces_string_length_with_context_abort(repair):
    """The context-window case, the other six of the ten."""
    fails = {"exception (String length: 109412)"}

    repair(CONTEXT_LOG, fails)

    assert not any("String length" in f for f in fails)
    assert any("max_tokens_exceeded_by_camel" in f for f in fails)


def test_keeps_an_unrelated_fail_untouched(repair):
    """Only mis-picked accounting lines are dropped, not every fail.

    ``tenacity.RetryError`` accompanies the balance failures and is a real
    message; removing it would trade one loss for another.
    """
    retry = ("exception (tenacity.RetryError: RetryError[<Future at 0x7f "
             "state=finished raised APIStatusError>])")
    fails = {"exception (num_prompt_tokens (before adjustment): 22878)", retry,
             "DOCKER_TIMEOUT"}

    repair(BALANCE_LOG, fails)

    assert retry in fails
    assert "DOCKER_TIMEOUT" in fails


def test_leaves_a_correctly_parsed_log_alone(repair):
    """Where upstream already got it right, the result must not change.

    This is what keeps the repair from rewriting the other 256 tasks.
    """
    log = [
        "Traceback (most recent call last):",
        '  File "/app/run.py", line 12, in <module>',
        "ValueError: bad input",
    ]
    fails = {"exception (ValueError: bad input)"}
    before = set(fails)

    repair(log, fails)

    assert fails == before


def test_ignores_accounting_lines_outside_a_traceback(repair):
    """A log without any traceback yields no new fails.

    The accounting lines appear in every successful run too; treating them as
    exceptions there would mark healthy tasks as failed.
    """
    log = [
        "num_prompt_tokens (before adjustment): 1000",
        "String length: 4096",
        "LLMSA_META filename=Contract.sol",
    ]
    fails: set = set()

    repair(log, fails)

    assert fails == set()


def test_exception_named_in_prose_is_not_a_fail(repair):
    """Only a line *starting* with the exception counts.

    The tool echoes contract text and findings; a description mentioning an
    exception must not become a reported failure.
    """
    log = [
        "The contract may raise ValueError: consider validating input",
        "  indented ArithmeticError: overflow",
    ]
    fails: set = set()

    repair(log, fails)

    assert fails == set()


def test_parse_actually_applies_the_repair(parser_mod):
    """The repair must be wired into ``parse``, not merely defined.

    Without this test, deleting the call in ``parse`` leaves every test above
    green while the defect returns in full: the unit tests exercise the helper
    directly and would never notice.
    """
    _, _, _, fails = parser_mod.parse(1, list(BALANCE_LOG), None)

    assert any("Insufficient Balance" in f for f in fails), (
        "parse() did not apply _repair_exception_fails"
    )
    assert not any("num_prompt_tokens" in f for f in fails)


def test_collects_every_closing_line_in_a_chained_traceback(repair):
    """Chained tracebacks carry more than one cause; keep them all.

    "During handling of the above exception, another exception occurred"
    produces two closing lines, and either may be the informative one.
    """
    log = [
        "Traceback (most recent call last):",
        '  File "a.py", line 1',
        "num_max_token: 65536",
        "ConnectionError: upstream closed",
        "",
        "During handling of the above exception, another exception occurred:",
        "",
        "Traceback (most recent call last):",
        '  File "b.py", line 2',
        "RuntimeError: giving up after 3 attempts",
    ]
    fails: set = set()

    repair(log, fails)

    assert any("ConnectionError" in f for f in fails)
    assert any("RuntimeError" in f for f in fails)
