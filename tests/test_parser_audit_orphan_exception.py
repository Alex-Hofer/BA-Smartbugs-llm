"""Regression tests for the orphan-exception detector in ``parser_audit.py``.

Background
----------
A ``TRACEBACK`` signal used to require that a single log record carried *both*
the string ``Traceback (most recent call last)`` and the closing
``Module.Error: message`` line. LLMSmartAudit logs through ``rich``, whose
console sometimes flushes the header and the closing line into two separate
records. The closing line then stood alone and the audit saw nothing — it
reported "no gaps" regardless of what the parser had done with it.

That made the headline "0 gaps" a property of the detector catalogue rather
than a measurement. ``_ORPHAN_EXC`` closes the hole: a record that *begins*
with an exception line counts as a report of that exception.

The anchor matters as much as the pattern. An exception name quoted inside a
finding description or in prose must not be mistaken for a raised exception —
that direction would manufacture gaps that do not exist. Both directions are
pinned below.
"""

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from analysis_tools.parser_audit import _ORPHAN_EXC  # noqa: E402


# --- what must be detected --------------------------------------------------


@pytest.mark.parametrize(
    "record",
    [
        # the case observed in llmsa_mwefixed_v2, record 1341 of 10_Visor.sol
        "RuntimeError: error in ChatAgentResponse, info:{'termination_reasons': "
        "['max_tokens_exceeded_by_camel'], 'num_tokens': 84821}",
        # the exhausted-balance case, four contracts in the same run
        "openai.APIStatusError: Error code: 402 - {'error': {'message': "
        "'Insufficient Balance'}}",
        # dotted module prefixes must survive
        "tenacity.RetryError: RetryError[<Future at 0x7f state=finished>]",
        "falcon.exceptions.FalconError: Invalid input",
        # leading whitespace is stripped by the caller, but be explicit
        "ValueError: something went wrong",
        "KeyboardInterrupt: user abort",
        "TimeoutError: deadline exceeded",
    ],
)
def test_detects_standalone_closing_line(record):
    """A record that begins with an exception line is a reported exception."""
    assert _ORPHAN_EXC.match(record) is not None


# --- what must NOT be detected ---------------------------------------------


@pytest.mark.parametrize(
    "record",
    [
        # the decisive one: an exception named inside a finding description.
        # Treating this as a raised exception would invent a gap.
        "The contract may raise ValueError: consider validating the input",
        "Detected pattern where ArithmeticError: can occur on overflow",
        # a log line that merely mentions the word
        "INFO chatdev: retrying after RuntimeError: backing off",
        # no colon-space, so not a closing line
        "RuntimeError",
        "SomeError:no space after the colon",
        # not an exception-shaped name
        "Result: analysis finished",
        "Warning: deprecated pragma",
        "",
    ],
)
def test_ignores_mentions_and_non_exceptions(record):
    """Only a record *starting* with the exception counts; prose does not."""
    assert _ORPHAN_EXC.match(record) is None


def test_anchor_is_what_separates_the_two():
    """The same text counts at the start and does not count mid-record.

    This is the property the whole detector rests on: without the anchor, every
    finding description that names an exception would become a gap.
    """
    exc = "RuntimeError: error in ChatAgentResponse"

    assert _ORPHAN_EXC.match(exc) is not None
    assert _ORPHAN_EXC.match(f"the tool logged {exc}") is None
