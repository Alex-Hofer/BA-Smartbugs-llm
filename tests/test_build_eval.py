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


# --------------------------------------------------------------------------- #
# merge_tasks: a follow-up run may only replace what the main run failed
# --------------------------------------------------------------------------- #
#
# The case this exists for: in llmsa_mwefixed_v2 four tasks died on HTTP 402
# "Insufficient Balance" -- the DeepSeek account ran empty while the run was
# still going. Those four say nothing about the contracts, so they are repeated
# in a separate run and folded back in here. Two mistakes would be invisible in
# the output and both would move the measured numbers:
#
# * letting a follow-up overwrite a task the main run *did* decide, which would
#   quietly substitute a second opinion for the recorded result;
# * letting a follow-up add a contract the main run never had, which would
#   change the size of the corpus the percentages are computed on.


def task(contract_id, run_id="main", findings=(), errors=(), fails=()):
    return {"contract_id": contract_id, "run_id": run_id,
            "findings": list(findings), "errors": list(errors), "fails": list(fails)}


FAILED_402 = ["no report produced"]


def test_a_follow_up_replaces_the_task_the_main_run_failed():
    main = [task("62_Locke", errors=FAILED_402)]
    extra = [task("62_Locke", run_id="retry", findings=[{"name": "Reentrancy"}])]

    tasks, replaced, ignored = be.merge_tasks(main, extra)

    assert [t["run_id"] for t in tasks] == ["retry"]
    assert be.task_state(tasks[0]["findings"], tasks[0]["errors"], tasks[0]["fails"]) == "findings"
    assert replaced == ["62_Locke"]
    assert ignored == []


def test_a_follow_up_never_overwrites_a_decided_task():
    """The main run is authoritative wherever it produced a result."""
    main = [task("12_Cauldron", findings=[{"name": "Centralization Risk"}])]
    extra = [task("12_Cauldron", run_id="retry", findings=[{"name": "Reentrancy"}])]

    tasks, replaced, ignored = be.merge_tasks(main, extra)

    assert tasks == main
    assert replaced == []
    assert ignored == ["12_Cauldron"]


def test_a_clean_task_counts_as_decided_and_is_kept():
    main = [task("16_GasOracle")]
    extra = [task("16_GasOracle", run_id="retry", findings=[{"name": "Reentrancy"}])]

    tasks, replaced, ignored = be.merge_tasks(main, extra)

    assert tasks == main
    assert ignored == ["16_GasOracle"]


def test_a_follow_up_does_not_grow_the_corpus():
    """A contract the main run never had is not silently appended to it."""
    main = [task("62_Locke", errors=FAILED_402)]
    extra = [task("99_Stranger", run_id="retry", findings=[{"name": "Reentrancy"}])]

    tasks, replaced, ignored = be.merge_tasks(main, extra)

    assert [t["contract_id"] for t in tasks] == ["62_Locke"]
    assert replaced == []
    assert ignored == ["99_Stranger"]


def test_a_follow_up_that_failed_again_still_replaces_the_older_failure():
    """Newer evidence about an undecided task, even when it is another failure."""
    main = [task("13_RCTreasury", errors=FAILED_402)]
    extra = [task("13_RCTreasury", run_id="retry",
                  errors=["context window exceeded: the agent aborted a call ..."])]

    tasks, replaced, ignored = be.merge_tasks(main, extra)

    state = be.task_state(tasks[0]["findings"], tasks[0]["errors"], tasks[0]["fails"])
    assert state == "context_exceeded"
    assert replaced == ["13_RCTreasury"]


def test_merging_nothing_leaves_the_run_untouched():
    main = [task("a", findings=[{"name": "x"}]), task("b", errors=FAILED_402)]

    tasks, replaced, ignored = be.merge_tasks(main, [])

    assert tasks == main
    assert (replaced, ignored) == ([], [])


def test_an_ambiguous_follow_up_is_refused_rather_than_guessed():
    """smartbugs-curated holds two files with the same basename.

    SmartBugs resolves that into `<name>.sol` and `<name>.sol_2`, but both carry
    the same contract_id here. A follow-up containing both would leave it open
    which of the two is meant, and picking one silently would move a number
    nobody is watching. Say so instead.
    """
    main = [task("0x627fa62c", errors=FAILED_402)]
    extra = [task("0x627fa62c", run_id="retry", findings=[{"name": "Reentrancy"}]),
             task("0x627fa62c", run_id="retry", findings=[{"name": "Denial of Service"}])]

    with pytest.raises(ValueError, match="0x627fa62c"):
        be.merge_tasks(main, extra)


# --------------------------------------------------------------------------- #
# read_invocation: run parameters come from the run, not from a constant
# --------------------------------------------------------------------------- #
#
# Until 2026-09-24 the ``invocation`` block in run_meta.json was hard-coded
# (processes 3, LLM_CONTEXT_TOKENS 65536, main False). For the ctx1m follow-up
# every one of those was wrong. The block is now read from the entrypoint that
# SmartBugs records and from the runner protocol; what no source has stays
# null and says why.

ENTRY = "'/sb/bin/do_solidity.sh' '/sb/a.sol' '600' '/sb/bin' '1'"
PROTOCOL = """[2026-09-24 15:47:37] Nachlauf LLMSmartAudit, runid=x, Contracts=a
[2026-09-24 15:47:37] Backend: provider=deepseek model=deepseek-v4-flash context=1000000
[2026-09-24 15:47:37] Image: smartbugs/llmsmartaudit:1.0 sha256:7c111aa6b366
[2026-09-24 15:47:37] Aufruf: python -m sb -t llmsmartaudit -f samples:a.sol --timeout 600 --processes 2 --runid x
[2026-09-24 16:00:00] FERTIG: 1 Tasks, 1 Prompt-, 1 Completion-Tokens, geschaetzt ~0,01 USD
"""


def inv_task(run_id="x", entrypoint=ENTRY):
    return {"run_id": run_id, "entrypoint": entrypoint,
            "env_keys": ["LLM_CONTEXT_TOKENS", "LLM_MODEL", "LLM_PROVIDER"],
            "infos": ["LLMSmartAudit run: backend=deepseek/deepseek-v4-flash"]}


def test_invocation_is_read_from_entrypoint_and_protocol(tmp_path):
    (tmp_path / "llmsa_retry_x.log").write_text(PROTOCOL, encoding="utf-8")

    inv = be.read_invocation([inv_task()], "x", runlogs=str(tmp_path))

    assert inv["timeout_s"] == 600
    assert inv["main"] is True
    assert inv["processes"] == 2
    assert inv["env"] == {"LLM_PROVIDER": "deepseek", "LLM_MODEL": "deepseek-v4-flash",
                          "LLM_CONTEXT_TOKENS": "1000000"}
    assert inv["image_id"] == "sha256:7c111aa6b366"
    assert inv["invocation_note"] is None
    assert inv["protocols"][0]["completed"] is True


def test_invocation_without_protocol_stays_null_instead_of_a_default(tmp_path):
    inv = be.read_invocation([inv_task()], "x", runlogs=str(tmp_path))

    assert (inv["timeout_s"], inv["main"]) == (600, True)      # the entrypoint is still there
    assert inv["processes"] is None
    assert inv["env"]["LLM_CONTEXT_TOKENS"] is None
    assert inv["image_id"] is None
    assert "runid=x" in inv["invocation_note"]


def test_invocation_does_not_confuse_run_ids_that_share_a_prefix(tmp_path):
    """llmsa_mwefixed_v2 must not pick up the protocol of llmsa_mwefixed_v2_retry."""
    other = PROTOCOL.replace("runid=x", "runid=x_retry").replace("--runid x", "--runid x_retry")
    (tmp_path / "a.log").write_text(other, encoding="utf-8")

    inv = be.read_invocation([inv_task()], "x", runlogs=str(tmp_path))

    assert inv["protocols"] == []
    assert inv["processes"] is None


def test_disagreeing_protocols_leave_the_field_null_and_say_so(tmp_path):
    (tmp_path / "a.log").write_text(PROTOCOL, encoding="utf-8")
    (tmp_path / "b.log").write_text(PROTOCOL.replace("--processes 2", "--processes 4"), encoding="utf-8")

    inv = be.read_invocation([inv_task()], "x", runlogs=str(tmp_path))

    assert inv["processes"] is None
    assert "processes: Quellen widersprechen sich (2, 4)" in inv["invocation_note"]
    assert [p["processes"] for p in inv["protocols"]] == [2, 4]
    assert inv["env"]["LLM_CONTEXT_TOKENS"] == "1000000"      # the protocols agree on this one


def test_main_flag_comes_from_the_entrypoint(tmp_path):
    inv = be.read_invocation([inv_task(entrypoint=ENTRY.replace("'1'", "'0'"))], "x", runlogs=str(tmp_path))
    assert inv["main"] is False
