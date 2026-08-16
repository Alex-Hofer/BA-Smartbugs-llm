"""Regression tests for analysis_tools/build_eval.py.

The export turns a SmartBugs result tree into the three files the evaluation
consumes. Almost all of it is plumbing; the parts that can be silently *wrong*
are the three derivations tested here, because a mistake in any of them is
invisible in the output and changes the measured numbers:

* ``dasp10`` --- a DASP class may only be claimed where findings.yaml actually
  states one. Inventing one would fabricate a mapping the thesis then cites.
* ``category_defi_logic`` --- the field GPTScan and LLMSmartAudit are compared
  on. Widening it silently inflates whichever tool it is widened for.
* ``task_state`` --- "no findings" and "was never analysed" must not collapse
  into one state, which is the whole point of the LLMSmartAudit context work.
"""

import importlib.util
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    path = os.path.join(REPO_ROOT, "analysis_tools", "build_eval.py")
    spec = importlib.util.spec_from_file_location("build_eval", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


be = load()


# --------------------------------------------------------------------------- #
# dasp10: only what findings.yaml states
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("classification,expected", [
    ("SWC-104, DASP-4", "DASP-4"),
    ("DASP-2 (no specific SWC)", "DASP-2"),
    ("SWC-105 (approx.), DASP-2", "DASP-2"),
    ("DASP-2 / governance (no standard SWC)", "DASP-2"),
    ("SWC-133", ""),
    ("SWC-118", ""),
    ("logic/DeFi (no standard SWC)", ""),
    ("code-quality (no standard SWC)", ""),
    ("", ""),
])
def test_dasp10_is_only_claimed_where_stated(classification, expected):
    assert be.dasp10(classification) == expected


# --------------------------------------------------------------------------- #
# category_defi_logic: the field both tools are compared on
# --------------------------------------------------------------------------- #

def test_defi_logic_is_true_only_for_the_defi_label():
    assert be.is_defi_logic("logic/DeFi (no standard SWC)") is True


@pytest.mark.parametrize("classification", [
    "logic (no standard SWC)",
    "logic (locked funds)",
    "logic (arithmetic)",
    "logic/compile (no standard SWC)",
    "code-quality (no standard SWC)",
    "SWC-107, DASP-1",
    "",
])
def test_plain_logic_is_not_defi_logic(classification):
    """Deliberately narrow.

    GPTScan looks for DeFi logic weaknesses in ten named scenarios. Counting
    every "logic" label of this tool as the same thing would compare a narrow
    detector against a broad one and credit LLMSmartAudit for the difference.
    ``classification_raw`` travels with every row, so a wider rule can be
    re-derived later without re-running anything.
    """
    assert be.is_defi_logic(classification) is False


# --------------------------------------------------------------------------- #
# task_state: "not analysed" must never read as "clean"
# --------------------------------------------------------------------------- #

def test_a_contract_with_findings_is_reported_as_such():
    assert be.task_state([{"name": "x"}], [], []) == "findings"


def test_context_exceeded_wins_over_everything_else():
    """It explains the empty finding list, so it is the state that matters."""
    errors = ["context window exceeded: the agent aborted a call with ...",
              "LLMSmartAudit checked 0 of 41 detector categories: ..."]
    assert be.task_state([], errors, ["exception (RuntimeError: ...)"]) == "context_exceeded"


def test_a_contract_without_a_report_is_not_clean():
    assert be.task_state([], ["no report produced"], []) == "no_output"


def test_an_uncaught_failure_is_its_own_state():
    assert be.task_state([], [], ["exception (ValueError)"]) == "failed"


def test_only_a_complete_empty_run_counts_as_clean():
    assert be.task_state([], [], []) == "clean"


def test_context_exceeded_is_not_counted_as_clean_even_with_no_other_signal():
    assert be.task_state([], ["context window exhausted: ..."], []) == "context_exceeded"
