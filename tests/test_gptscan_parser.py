"""Regression tests for smartbugs/tools/gptscan/parser.py.

The defect these guard against: GPTScan catches a failed compilation, logs it
through ``rich``, carries on with a degraded pipeline, exits 0 and writes
``{"success": true, "results": []}``. Before the 2026-08-02 parser revision that
was indistinguishable from a clean contract --- across the 19 recorded runs, 246
tasks (98 distinct contracts in 9 runs) read as "clean" although nothing had
compiled. The main curated run is not among them: there, every contract built.
"""

import json

import pytest

from conftest import contains, parse, raw, synthetic_empty_tar, synthetic_tar

TOOL = "gptscan"


# --------------------------------------------------------------------------- #
# Recorded runs
# --------------------------------------------------------------------------- #

def test_clean_run_reports_no_error_or_fail(gptscan):
    """A contract that compiled and analysed cleanly must stay clean.

    Guards the other direction of the fix: the new log scanning must not
    invent errors for well-behaved runs.
    """
    out = parse(gptscan, TOOL, "clean_with_finding")
    assert out["errors"] == set()
    assert out["fails"] == set()
    assert len(out["findings"]) == 1
    assert contains(out["infos"], "GPTScan run: backend=")


def test_recorded_finding_keeps_position_severity_and_file(gptscan):
    """Line range, severity and file name must survive the mapping.

    Mutation probe of 2026-09-24: dropping the line number left every test
    green. Expected values come from the recorded
    ``tests/fixtures/gptscan/clean_with_finding/result.tar`` (``output.json``).
    """
    (finding,) = parse(gptscan, TOOL, "clean_with_finding")["findings"]
    assert finding["name"] == "MWE-200: Insecure LP Token Value Calculation"
    assert finding["severity"] == "high"
    assert finding["filename"] == "Vault.sol"
    assert (finding["line"], finding["line_end"]) == (24, 29)


def test_clean_run_is_not_marked_degraded(gptscan):
    """The degradation notice must be tied to a real compile failure.

    If it were emitted unconditionally it would be worthless: every "no
    findings" result would read as inconclusive.
    """
    out = parse(gptscan, TOOL, "clean_with_finding")
    assert not contains(out["infos"], "analysis degraded")


def test_silent_compile_failure_becomes_visible(gptscan):
    """exit 0 + ``success: true`` + zero findings, yet nothing compiled."""
    exit_code, _log, _tar = raw(TOOL, "compile_failure_silent")
    assert exit_code == 0, "the fixture must be the silent case, not a crash"

    out = parse(gptscan, TOOL, "compile_failure_silent")
    assert out["errors"], "a failed compilation must not read as a clean run"
    assert contains(out["errors"], "Invalid compilation")
    assert contains(out["infos"], "analysis degraded")
    assert contains(out["infos"], "inconclusive, not clean")


def test_compile_failure_names_the_solc_diagnostic(gptscan):
    """The reason must be reported in its own right, not only inside a trace."""
    out = parse(gptscan, TOOL, "compile_failure_silent")
    assert contains(out["errors"], "solc rejected 74_TimeswapPair.sol")
    assert contains(out["errors"], "Expected ',' but got identifier")


def test_compile_failure_reports_skipped_static_stage(gptscan):
    """Without a Falcon IR the static confirmation stage never runs.

    GPTScan announces this at WARNING level only, so it is the one warning the
    parser has to pick up explicitly.
    """
    out = parse(gptscan, TOOL, "compile_failure_silent")
    assert contains(out["errors"], "Falcon is not initialized")


def test_rich_wrapped_traceback_is_recovered(gptscan):
    """``sb.parse_utils`` cannot see a rich-rendered traceback; the parser must.

    The exception class name is split across rendered lines, so finding it
    proves the de-wrapper reassembled the record.
    """
    out = parse(gptscan, TOOL, "compile_failure_silent")
    assert contains(out["errors"], "falcon.exceptions.FalconError")


def test_static_check_crash_without_compile_failure(gptscan):
    """GPTScan's static stage can crash on a contract that compiled fine.

    Taken from the main curated run, so the case is not exotic. It must be
    reported, and it must *not* be labelled a compilation problem.
    """
    out = parse(gptscan, TOOL, "static_check_crash")
    assert contains(out["errors"], "Static analysis failed")
    assert not contains(out["infos"], "analysis degraded")


def test_uncaught_crash_stays_a_fail(gptscan):
    """An exception that killed the process belongs in ``fails``, not ``errors``.

    That split is the whole point of ``sb.parse_utils.errors_fails``: the
    parser's added log scanning must not reclassify a genuine crash.
    """
    exit_code, _log, _tar = raw(TOOL, "uncaught_crash_exit1")
    assert exit_code == 1

    out = parse(gptscan, TOOL, "uncaught_crash_exit1")
    assert out["fails"], "an uncaught exception must be a fail"
    assert contains(out["fails"], "exception (")
    assert contains(out["errors"], "EXIT_CODE_1")


def test_normal_static_filtering_is_never_an_error(gptscan):
    """``vul_before_static > vul_after_static`` is the intended FP filter.

    It fires on roughly half of all live contracts and must show up as an
    info, never as an error or fail.
    """
    out = parse(gptscan, TOOL, "static_check_crash")
    assert contains(out["infos"], "static confirmation filtered LLM candidates")
    assert not contains(out["errors"], "filtered LLM candidates")
    assert not contains(out["fails"], "filtered LLM candidates")


def test_messages_are_passed_through_unrewritten(gptscan):
    """Consequential errors are reported verbatim, not filtered or reworded.

    The ``TypeError`` GPTScan raises after a failed compilation is misleading
    but must survive; the cause/effect judgement belongs in ``infos``.
    """
    out = parse(gptscan, TOOL, "static_check_crash")
    assert contains(out["errors"], "ERROR    tasks:"), \
        "the tool's own log record must appear with its original wording"


# --------------------------------------------------------------------------- #
# Synthetic cases --- these failure modes never occurred in the recorded runs
# --------------------------------------------------------------------------- #

def test_synthetic_timeout_is_a_fail(gptscan):
    """``exit_code is None`` is SmartBugs' way of saying it killed the container."""
    findings, infos, errors, fails = gptscan.parse(None, ["GPTScan: provider=deepseek"], None)
    assert "DOCKER_TIMEOUT" in fails
    assert findings == []


def test_synthetic_missing_archive_is_reported(gptscan):
    """No archive at all --- distinct from an archive without a report."""
    _f, _i, _e, fails = gptscan.parse(0, ["GPTScan: provider=deepseek"], None)
    assert contains(fails, "no tar archive collected")


def test_synthetic_empty_archive_is_reported(gptscan):
    """A well-formed but memberless archive: collection worked, output did not."""
    _f, _i, _e, fails = gptscan.parse(0, [], synthetic_empty_tar())
    assert contains(fails, "contains no output.json")


def test_synthetic_broken_json_names_the_reason(gptscan):
    """A truncated report must not be indistinguishable from a missing one."""
    _f, _i, _e, fails = gptscan.parse(0, [], synthetic_tar(b'{"version": "1.1.0", "resu'))
    assert contains(fails, "not valid JSON")
    assert not contains(fails, "no tar archive collected")


def test_synthetic_unsuccessful_report_is_an_error(gptscan):
    """A report that declares itself unsuccessful must not read as a clean run.

    Synthetic only for convenience --- the shape occurs 44 times in the
    recorded runs, always together with a non-zero exit code. Building it here
    isolates the ``success: false`` handling from the exit-code path.
    """
    payload = b'{"version":"1.1.0","success":false,"message":"no output produced","results":[]}'
    _f, _i, errors, _fa = gptscan.parse(0, [], synthetic_tar(payload))
    assert contains(errors, "success=false")


def test_synthetic_missing_metadata_on_exit_zero_is_an_error(gptscan):
    """No ``GPTSCAN_META`` after a clean exit means GPTScan never finished."""
    payload = b'{"version":"1.1.0","success":true,"message":null,"results":[]}'
    _f, _i, errors, _fa = gptscan.parse(0, ["GPTScan: provider=deepseek"], synthetic_tar(payload))
    assert contains(errors, "GPTSCAN_META missing")


def test_synthetic_missing_metadata_on_crash_is_not_double_reported(gptscan):
    """On a non-zero exit the exit code already says the container died."""
    payload = b'{"version":"1.1.0","success":true,"message":null,"results":[]}'
    _f, _i, errors, _fa = gptscan.parse(1, ["GPTScan: provider=deepseek"], synthetic_tar(payload))
    assert not contains(errors, "GPTSCAN_META missing")


def test_synthetic_budget_cap_is_an_error(gptscan):
    """Hitting the per-contract cost cap truncates the analysis, so it is an error.

    Both metadata fields are set here because the guard writes them together.
    Note that the two assertions below are not independent: the message for
    ``llm_calls_skipped_budget`` reads "7 LLM calls skipped: per-contract cost
    cap reached" and satisfies both on its own.
    """
    meta = ('GPTSCAN_META {"provider":"deepseek","model":"deepseek-v4-flash",'
            '"llm_calls":3,"estimated_cost":0.5,"budget_exceeded":true,'
            '"llm_calls_skipped_budget":7}')
    payload = b'{"version":"1.1.0","success":true,"message":null,"results":[]}'
    _f, _i, errors, _fa = gptscan.parse(0, [meta], synthetic_tar(payload))
    assert contains(errors, "cost cap reached")
    assert contains(errors, "7 LLM calls skipped")


def test_synthetic_timeout_brake_is_reported_as_error(gptscan):
    """The brake fired: GPTScan ran out on its own and wrote what it had.

    The marker travels the route the brake actually uses --- GPTScan writes it
    into its own metadata, which reaches the parser as a GPTSCAN_META log line.
    Putting it into output.json instead would leave the meta branch of
    `result.get(...) or (meta or {}).get(...)` unevaluated, because `or`
    short-circuits, and the brake path would go untested.
    """
    meta = {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "llm_calls": 42,
        "llm_calls_skipped_deadline": 17,
        "sb_timeout": {"hit": True, "stage": "brake",
                       "detail": "17 LLM-Aufrufe wegen der Frist unterdrueckt"},
    }
    report = {"version": "1.1.0", "success": True, "results": []}
    findings, infos, errors, fails = gptscan.parse(
        0,
        ["GPTScan: provider=deepseek", "GPTSCAN_META " + json.dumps(meta)],
        synthetic_tar(json.dumps(report).encode("utf-8")))
    assert contains(errors, "TIMEOUT")
    assert contains(errors, "brake")
    assert not fails
    assert contains(infos, "GPTScan run: backend=deepseek/deepseek-v4-flash")


def test_synthetic_timeout_net_is_reported_as_error(gptscan):
    """The net fired: the entrypoint stamped the marker and forced exit 124."""
    report = {
        "version": "1.1.0", "success": False, "results": [],
        "sb_timeout": {"hit": True, "stage": "net", "detail": "hart beendet"},
    }
    findings, infos, errors, fails = gptscan.parse(
        124, ["GPTScan: provider=deepseek"], synthetic_tar(
            json.dumps(report).encode("utf-8")))
    assert contains(errors, "TIMEOUT")
    assert contains(errors, "net")


def test_synthetic_no_marker_means_no_timeout_message(gptscan):
    """Absence of sb_timeout is the statement 'this run was complete'."""
    report = {"version": "1.1.0", "success": True, "results": []}
    findings, infos, errors, fails = gptscan.parse(
        0, ["GPTScan: provider=deepseek"], synthetic_tar(
            json.dumps(report).encode("utf-8")))
    assert not contains(errors, "TIMEOUT")


@pytest.mark.parametrize("case", [
    "clean_with_finding", "compile_failure_silent",
    "uncaught_crash_exit1", "static_check_crash",
])
def test_every_recorded_case_parses_without_raising(gptscan, case):
    """``sb/parsing.py`` turns any parser exception into a SmartBugsError."""
    findings, infos, errors, fails = gptscan.parse(*raw(TOOL, case))
    assert isinstance(findings, list)
    for group in (infos, errors, fails):
        assert isinstance(group, set)
        assert all(isinstance(m, str) for m in group)


@pytest.mark.parametrize("case", [
    "clean_with_finding", "compile_failure_silent",
    "uncaught_crash_exit1", "static_check_crash",
])
def test_finding_names_stay_within_the_declared_set(gptscan, case):
    """``sb/parsing.py`` rejects any finding name outside ``FINDINGS``."""
    findings, _i, _e, _f = gptscan.parse(*raw(TOOL, case))
    for finding in findings:
        assert finding["name"] in gptscan.FINDINGS
