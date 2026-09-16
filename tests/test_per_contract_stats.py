"""Regression tests for analysis_tools/per_contract_stats.py.

The script turns a recorded SmartBugs run into one row per contract. It computes
nothing new --- every number already exists in ``smartbugs.json``,
``result.json`` or ``result.log``. What can go silently wrong is *which* number
a column picks up, and that is what these tests pin down:

* GPTScan keeps its per-contract accounting in a single ``GPTSCAN_META`` line.
  Where that line is missing --- a crash before the tool got that far --- the
  cells must stay empty. A 0 would read as "no tokens, no cost, no time".
* LLMSmartAudit writes the same words twice per log: 40-odd client-side
  estimates before the calls, and once the real total in the ChatDev statistics
  at the end. Anchoring on the wrong one understates a run by orders of
  magnitude.
* A phase without a call is the fingerprint of a run that was cut short. It has
  to survive into the phase table instead of being smoothed away.
* A follow-up run may only speak for tasks the main run left undecided --- the
  merge rule of ``gptscan_eval.py`` and ``build_eval.py``.

The recorded fixtures under ``tests/fixtures/`` are the raw material of real
tasks (see ``tests/conftest.py``). Tests that build their input by hand say
``synthetic`` in the name; that is the case for the merge of two runs, for the
Slither row and for the writing of empty cells, none of which a single recorded
task can show.

``smartbugs/results/`` is deliberately not touched here --- it is git-ignored,
so a fresh clone has none of it, and a test that needed it would fail for the
wrong reason.
"""

import csv
import gzip
import importlib.util
import inspect
import json
import os
import shutil

import pytest

import conftest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    path = os.path.join(REPO_ROOT, "analysis_tools", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pcs = load("per_contract_stats")


# --------------------------------------------------------------------------- #
# Turning a fixture into what a task directory looks like on disk
# --------------------------------------------------------------------------- #

def task_dir(tmp_path, tool, case, name=None):
    """Rebuild a recorded task as a directory, ``result.json`` included.

    The fixtures hold what the container produced. ``result.json`` is what
    SmartBugs writes *from* that material, so it is produced here the same way:
    by running the tool's own parser over the fixture.
    """
    src = os.path.join(conftest.FIXTURES, tool, case)
    dst = tmp_path / (name or case)
    dst.mkdir()
    shutil.copy(os.path.join(src, "smartbugs.json"), str(dst / "smartbugs.json"))
    tar = os.path.join(src, "result.tar")
    if os.path.exists(tar):
        shutil.copy(tar, str(dst / "result.tar"))
    plain = os.path.join(src, "result.log")
    if os.path.exists(plain):
        shutil.copy(plain, str(dst / "result.log"))
    else:
        with gzip.open(os.path.join(src, "result.log.gz"), "rt",
                       encoding="utf-8", errors="replace") as fh:
            (dst / "result.log").write_text(fh.read(), encoding="utf-8")
    parsed = conftest.parse(conftest.load_parser(tool), tool, case)
    # The parser hands back sets for infos/errors/fails and a list of dicts for
    # findings; SmartBugs writes both as JSON arrays.
    (dst / "result.json").write_text(json.dumps(
        {key: sorted(value) if isinstance(value, (set, frozenset)) else list(value)
         for key, value in parsed.items()}), encoding="utf-8")
    return str(dst)


def synthetic_task(tmp_path, name, findings=(), errors=(), fails=(),
                   duration="1.0", exit_code=0, timeout="1800", main="0", log=None):
    """A task directory holding only the two JSON files SmartBugs writes."""
    entry = ("'/sb/bin/do_solidity.sh' '/sb/" + name + ".sol' '" + timeout
             + "' '/sb/bin' '" + main + "'")
    d = tmp_path / name
    d.mkdir()
    (d / "smartbugs.json").write_text(json.dumps({
        "filename": name + ".sol",
        "docker": {"entrypoint": entry},
        "result": {"duration": duration, "exit_code": exit_code,
                   "start": 1786810000.0},
    }), encoding="utf-8")
    (d / "result.json").write_text(json.dumps({
        "findings": list(findings), "infos": [],
        "errors": list(errors), "fails": list(fails),
    }), encoding="utf-8")
    if log is not None:
        (d / "result.log").write_text(log, encoding="utf-8")
    return str(d)


# A log that carries the ChatDev statistics twice, as a container would that
# restarted the pipeline. Only the recorded fixtures have a single block, so
# without this case "first occurrence" and "last occurrence" are the same value
# and no test can tell them apart.
TWO_STATISTICS_BLOCKS = """
| **phase_name** | ContractAnalysis |
prompt_tokens: 100
completion_tokens: 10
num_max_token: 16384
❓**num_prompt_tokens**=111
❗**num_completion_tokens**=11
🕑**duration**=11.00s
| **phase_name** | ContractAnalysis |
prompt_tokens: 200
completion_tokens: 20
num_max_token: 65536
❓**num_prompt_tokens**=222
❗**num_completion_tokens**=22
🕑**duration**=22.00s
"""


# --------------------------------------------------------------------------- #
# GPTScan
# --------------------------------------------------------------------------- #

def test_gptscan_row_takes_tokens_time_and_cost_from_the_metadata_line(tmp_path):
    row = pcs.task_row("gptscan", task_dir(tmp_path, "gptscan", "clean_with_finding"))

    assert row["prompt_tokens"] == 641
    assert row["completion_tokens"] == 763
    assert row["llm_calls"] == 3
    assert row["cost_usd"] == pytest.approx(0.00030338)
    assert row["loc"] == 37


def test_gptscan_row_keeps_container_duration_apart_from_tool_time(tmp_path):
    row = pcs.task_row("gptscan", task_dir(tmp_path, "gptscan", "clean_with_finding"))

    assert row["duration_s"] == pytest.approx(16.0795450)
    assert row["tool_time_s"] == pytest.approx(13.4058897)


def test_gptscan_row_reads_main_and_timeout_from_the_entrypoint(tmp_path):
    row = pcs.task_row("gptscan", task_dir(tmp_path, "gptscan", "clean_with_finding"))

    assert row["main"] == 0
    assert row["timeout_s"] == 1800


def test_gptscan_row_leaves_cells_empty_where_the_tool_wrote_no_metadata(tmp_path):
    row = pcs.task_row("gptscan", task_dir(tmp_path, "gptscan", "uncaught_crash_exit1"))

    for column in ("prompt_tokens", "completion_tokens", "llm_calls",
                   "cost_usd", "tool_time_s", "loc"):
        assert row[column] is None, column
    assert row["n_fails"] == 1
    assert row["state"] == "failed"


def test_gptscan_row_flags_the_crash_of_the_static_stage(tmp_path):
    row = pcs.task_row("gptscan", task_dir(tmp_path, "gptscan", "static_check_crash"))

    assert row["static_invalid_args"] is True
    assert row["vul_before_static"] == 1
    assert row["vul_after_static"] == 0


def test_gptscan_row_marks_a_contract_that_did_not_compile_as_degraded(tmp_path):
    row = pcs.task_row("gptscan",
                       task_dir(tmp_path, "gptscan", "compile_failure_silent"))

    assert row["degraded"] is True
    assert row["state"] == "degraded"


# --------------------------------------------------------------------------- #
# LLMSmartAudit
# --------------------------------------------------------------------------- #

def test_llmsmartaudit_row_reads_the_final_statistics_not_the_first_estimate(tmp_path):
    row = pcs.task_row("llmsmartaudit",
                       task_dir(tmp_path, "llmsmartaudit", "clean_with_findings"))

    assert row["prompt_tokens"] == 26591
    assert row["completion_tokens"] == 15682
    assert row["tool_time_s"] == pytest.approx(196.0)


def test_llmsmartaudit_row_counts_one_call_per_usage_block(tmp_path):
    row = pcs.task_row("llmsmartaudit",
                       task_dir(tmp_path, "llmsmartaudit", "clean_with_findings"))

    assert row["llm_calls"] == 44
    assert row["max_prompt_est"] == 1142
    assert row["context_limit"] == 65536


def test_llmsmartaudit_row_prices_the_tokens_because_the_tool_reports_zero(tmp_path):
    row = pcs.task_row("llmsmartaudit",
                       task_dir(tmp_path, "llmsmartaudit", "clean_with_findings"))
    be = load("build_eval")
    expected = (26591 / 1e6 * be.PRICE_PROMPT_PER_M
                + 15682 / 1e6 * be.PRICE_COMPLETION_PER_M)

    assert row["cost_usd_est"] == pytest.approx(expected)


def test_llmsmartaudit_phase_rows_are_one_per_phase_in_order(tmp_path):
    rows = pcs.phase_rows(task_dir(tmp_path, "llmsmartaudit", "clean_with_findings"))

    assert len(rows) == 44
    assert [r["phase_index"] for r in rows[:3]] == [1, 2, 3]
    assert [r["phase_name"] for r in rows[:3]] == ["ContractAnalysis", "Reflection",
                                                   "ArithmeticDetector"]


def test_llmsmartaudit_phase_tokens_add_up_to_the_contract_row(tmp_path):
    rows = pcs.phase_rows(task_dir(tmp_path, "llmsmartaudit", "clean_with_findings"))

    assert sum(r["prompt_tokens"] for r in rows) == 26591
    assert sum(r["completion_tokens"] for r in rows) == 15682


def test_llmsmartaudit_phase_without_a_call_stays_visible(tmp_path):
    d = task_dir(tmp_path, "llmsmartaudit", "backend_rejected")

    rows = pcs.phase_rows(d)
    row = pcs.task_row("llmsmartaudit", d)

    assert [(r["phase_name"], r["calls"]) for r in rows] == [("ContractAnalysis", 0)]
    assert row["calls_match_phases"] is False


def test_llmsmartaudit_row_takes_the_last_statistics_block_synthetic(tmp_path):
    """A log with two statistics blocks: the run ended in the state of the last."""
    row = pcs.task_row("llmsmartaudit",
                       synthetic_task(tmp_path, "twice", log=TWO_STATISTICS_BLOCKS))

    assert row["prompt_tokens"] == 222
    assert row["completion_tokens"] == 22
    assert row["tool_time_s"] == pytest.approx(22.0)
    assert row["context_limit"] == 65536


def test_llmsmartaudit_row_leaves_cells_empty_when_the_run_never_reported(tmp_path):
    row = pcs.task_row("llmsmartaudit",
                       task_dir(tmp_path, "llmsmartaudit", "backend_rejected"))

    assert row["prompt_tokens"] is None
    assert row["completion_tokens"] is None
    assert row["tool_time_s"] is None
    assert row["cost_usd_est"] is None
    assert row["state"] == "no_output"


# --------------------------------------------------------------------------- #
# Two tasks, one file name
#
# smartbugs-curated holds 0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol twice:
# once under reentrancy/ and once under unchecked_low_level_calls/. Both tasks
# carry the same contract id and the same directory name, so anything that
# identifies a task by its name alone silently folds the two together --- or
# counts one of them twice.
# --------------------------------------------------------------------------- #

def synthetic_run(tmp_path, tool="llmsmartaudit", runid="run",
                  categories=("reentrancy", "unchecked_low_level_calls")):
    """A result tree with the same contract file under two categories."""
    root = tmp_path / "results" / tool / runid
    for category in categories:
        directory = root / category
        directory.mkdir(parents=True)
        synthetic_task(directory, "x", log=TWO_STATISTICS_BLOCKS)
    return str(tmp_path / "results")


def test_task_dir_tells_two_tasks_of_the_same_name_apart_synthetic(tmp_path):
    results = synthetic_run(tmp_path)

    rows = pcs.read_run("llmsmartaudit", "run", results)

    assert len(rows) == 2
    assert {r["contract_id"] for r in rows} == {"x"}
    # Slashes, not backslashes: the table is versioned and read on other systems.
    assert sorted(r["task_dir"] for r in rows) == ["reentrancy/x",
                                                   "unchecked_low_level_calls/x"]


def test_phase_table_counts_each_task_exactly_once_synthetic(tmp_path):
    results = synthetic_run(tmp_path)
    out = tmp_path / "out"

    pcs.main(["llmsmartaudit", "run", "--results", results, "--out-dir", str(out)])

    with open(str(out / "run__llmsmartaudit__phases.csv"),
              encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    # Two tasks, two phase markers each --- not four rows per task.
    assert len(rows) == 4
    assert sorted(r["task_dir"] for r in rows) == [
        "reentrancy/x", "reentrancy/x",
        "unchecked_low_level_calls/x", "unchecked_low_level_calls/x"]


# --------------------------------------------------------------------------- #
# Slither: the shared columns only
# --------------------------------------------------------------------------- #

def test_slither_row_has_no_token_columns_synthetic(tmp_path):
    row = pcs.task_row("slither-0.11.3",
                       synthetic_task(tmp_path, "proxy", findings=[{"name": "x"}]))

    assert row["duration_s"] == pytest.approx(1.0)
    assert row["n_findings"] == 1
    for column in ("prompt_tokens", "llm_calls", "cost_usd", "tool_time_s"):
        assert column not in row, column


# --------------------------------------------------------------------------- #
# Merging a follow-up run
# --------------------------------------------------------------------------- #

def test_merge_replaces_a_failed_task_and_records_where_it_came_from_synthetic(tmp_path):
    main = [pcs.task_row("gptscan", synthetic_task(tmp_path, "a", fails=["boom"]),
                         source_run="main"),
            pcs.task_row("gptscan",
                         synthetic_task(tmp_path, "b", findings=[{"name": "x"}]),
                         source_run="main")]
    extra = [pcs.task_row("gptscan",
                          synthetic_task(tmp_path, "a_retry", findings=[{"name": "y"}]),
                          source_run="retry")]
    extra[0]["contract_id"] = "a"

    rows, replaced = pcs.merge_rows("gptscan", main, extra)

    assert replaced == ["a"]
    assert [(r["contract_id"], r["source_run"]) for r in rows] == [("a", "retry"),
                                                                   ("b", "main")]


def test_merge_leaves_a_decided_task_to_the_main_run_synthetic(tmp_path):
    main = [pcs.task_row("gptscan",
                         synthetic_task(tmp_path, "a", findings=[{"name": "x"}]),
                         source_run="main")]
    extra = [pcs.task_row("gptscan",
                          synthetic_task(tmp_path, "a2", findings=[{"name": "y"}]),
                          source_run="retry")]
    extra[0]["contract_id"] = "a"

    rows, replaced = pcs.merge_rows("gptscan", main, extra)

    assert replaced == []
    assert rows[0]["source_run"] == "main"


def test_merge_of_an_llmsmartaudit_run_uses_the_undecided_rule_synthetic(tmp_path):
    """LLMSmartAudit replaces more than fails: a context abort is undecided too."""
    main = [pcs.task_row("llmsmartaudit",
                         synthetic_task(tmp_path, "a",
                                        errors=["context window exceeded: ..."]),
                         source_run="main")]
    extra = [pcs.task_row("llmsmartaudit",
                          synthetic_task(tmp_path, "a2", findings=[{"name": "y"}]),
                          source_run="retry")]
    extra[0]["contract_id"] = "a"

    rows, replaced = pcs.merge_rows("llmsmartaudit", main, extra)

    assert replaced == ["a"]
    assert rows[0]["source_run"] == "retry"


# --------------------------------------------------------------------------- #
# Writing the table
# --------------------------------------------------------------------------- #

def test_missing_values_are_written_as_empty_cells_not_zero_synthetic(tmp_path):
    rows = [pcs.task_row("gptscan",
                         task_dir(tmp_path, "gptscan", "uncaught_crash_exit1"))]
    out = tmp_path / "out.csv"

    pcs.write_csv(str(out), "gptscan", rows)

    with open(str(out), encoding="utf-8", newline="") as fh:
        written = list(csv.DictReader(fh))
    assert written[0]["prompt_tokens"] == ""
    assert written[0]["cost_usd"] == ""


def test_written_table_carries_no_internal_helper_columns_synthetic(tmp_path):
    rows = [pcs.task_row("gptscan",
                         synthetic_task(tmp_path, "a", findings=[{"name": "x"}]))]
    out = tmp_path / "out.csv"

    pcs.write_csv(str(out), "gptscan", rows)

    with open(str(out), encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))
    assert [h for h in header if h.startswith("_")] == []


# --------------------------------------------------------------------------- #
# The coupling to build_eval, which a rename must not break silently
# --------------------------------------------------------------------------- #

def test_the_helpers_imported_from_build_eval_keep_their_signature():
    be = load("build_eval")

    assert list(inspect.signature(be.is_decided).parameters) == ["task"]
    assert list(inspect.signature(be.task_state).parameters) == ["findings", "errors",
                                                                 "fails"]
    assert isinstance(be.PRICE_PROMPT_PER_M, float)
    assert isinstance(be.PRICE_COMPLETION_PER_M, float)
