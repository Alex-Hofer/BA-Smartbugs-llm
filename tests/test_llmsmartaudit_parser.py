"""Regression tests for smartbugs/tools/llmsmartaudit/parser.py.

The audit in ``analysis_tools/parser_audit.py`` finds no lost message across
this tool's 147 recorded tasks: LLMSmartAudit writes plain, un-wrapped output,
so an uncaught exception reaches stderr in the shape
``sb.parse_utils.errors_fails`` expects. These tests pin that down and cover the
failure modes the recorded runs never produced.

Note the imbalance in the material: only one real corpus run exists for this
tool (143 contracts) plus two smoke runs. Timeout, empty archive and malformed
JSON therefore have no recorded example and are exercised synthetically ---
every such test says ``synthetic`` in its name.
"""

import json

import pytest

from conftest import contains, parse, raw, synthetic_empty_tar, synthetic_tar

TOOL = "llmsmartaudit"


# --------------------------------------------------------------------------- #
# Recorded runs
# --------------------------------------------------------------------------- #

def test_clean_run_reports_no_error_or_fail(llmsmartaudit):
    """A complete run must stay clean, and say how much it actually checked.

    The ``41/41`` info is what distinguishes a genuinely complete audit from a
    partial one that happens to have found nothing.
    """
    out = parse(llmsmartaudit, TOOL, "clean_with_findings")
    assert out["errors"] == set()
    assert out["fails"] == set()
    assert out["findings"], "the fixture is a run that produced findings"
    assert contains(out["infos"], "categories checked: 41/41")


def test_findings_carry_no_line_numbers(llmsmartaudit):
    """The tool reasons over source text and emits no positions.

    Documented behaviour, not a defect --- pinned so a future change to the
    report format cannot introduce fabricated line numbers unnoticed.
    """
    out = parse(llmsmartaudit, TOOL, "clean_with_findings")
    for finding in out["findings"]:
        assert "line" not in finding
        assert "line_end" not in finding


def test_findings_are_attributed_to_the_contract(llmsmartaudit):
    """The report names no file, so the filename comes from ``LLMSA_META``.

    Without it every finding would be unattributed, which SmartBugs renders as
    an empty column in the CSV.
    """
    out = parse(llmsmartaudit, TOOL, "clean_with_findings")
    assert all(f.get("filename") for f in out["findings"])


def test_backend_rejection_is_reported_as_error_and_fail(llmsmartaudit):
    """The recorded ``LLM_MODEL=STUB`` run: the API refused the model name.

    The tool's own placeholder report lands in ``errors``, the uncaught
    ``BadRequestError`` in ``fails`` --- exactly the split SmartBugs defines.
    """
    exit_code, _log, _tar = raw(TOOL, "backend_rejected")
    assert exit_code == 1

    out = parse(llmsmartaudit, TOOL, "backend_rejected")
    assert contains(out["errors"], "no report produced")
    assert "EXIT_CODE_1" in out["errors"]
    assert contains(out["fails"], "BadRequestError")
    assert out["findings"] == []


def test_zero_categories_checked_is_an_error(llmsmartaudit):
    """An empty finding list after zero checks must not read as "clean"."""
    out = parse(llmsmartaudit, TOOL, "backend_rejected")
    assert contains(out["errors"], "checked 0 of 41 detector categories")


# --------------------------------------------------------------------------- #
# Synthetic cases --- no recorded example exists for these
# --------------------------------------------------------------------------- #

def test_synthetic_timeout_is_a_fail(llmsmartaudit):
    """A run this tool never finished: SmartBugs signals it with ``exit_code=None``.

    Plausible here in a way it is not for GPTScan --- a 41-phase multi-agent
    audit is the slowest tool in the benchmark.
    """
    findings, _i, _e, fails = llmsmartaudit.parse(None, ['LLMSA_META {"provider":"deepseek"}'], None)
    assert "DOCKER_TIMEOUT" in fails
    assert findings == []


def test_synthetic_missing_archive_is_reported(llmsmartaudit):
    """Nothing was collected at all --- distinct from an empty collection."""
    _f, _i, _e, fails = llmsmartaudit.parse(0, [], None)
    assert contains(fails, "no tar archive collected")


def test_synthetic_empty_archive_is_reported(llmsmartaudit):
    """Collection worked, but the container produced no report."""
    _f, _i, _e, fails = llmsmartaudit.parse(0, [], synthetic_empty_tar())
    assert contains(fails, "contains no output.json")


def test_synthetic_broken_json_names_the_reason(llmsmartaudit):
    """A truncated report must not be indistinguishable from a missing one.

    The entrypoint writes the report incrementally, so a container killed
    mid-write leaves exactly this shape.
    """
    _f, _i, _e, fails = llmsmartaudit.parse(0, [], synthetic_tar(b'{"tool":"LLMSmartAudit","find'))
    assert contains(fails, "not valid JSON")
    assert not contains(fails, "no tar archive collected")


def test_synthetic_report_error_field_is_an_error(llmsmartaudit):
    """A report can carry its own error field and still be well-formed JSON.

    Built synthetically to isolate the field: the recorded ``backend_rejected``
    task carries one too, but together with a non-zero exit code, which would
    mask whether this branch fired.
    """
    payload = (b'{"tool":"LLMSmartAudit","categories_total":41,"categories_checked":12,'
               b'"findings":[],"error":"context_length_exceeded"}')
    _f, _i, errors, _fa = llmsmartaudit.parse(0, [], synthetic_tar(payload))
    assert contains(errors, "context_length_exceeded")


def test_synthetic_partial_run_is_not_silently_clean(llmsmartaudit):
    """A run that checked some but not all categories stays visible."""
    payload = (b'{"tool":"LLMSmartAudit","categories_total":41,"categories_checked":12,'
               b'"findings":[]}')
    _f, infos, _e, _fa = llmsmartaudit.parse(0, [], synthetic_tar(payload))
    assert contains(infos, "categories checked: 12/41")


@pytest.mark.parametrize("case", ["clean_with_findings", "backend_rejected"])
def test_every_recorded_case_parses_without_raising(llmsmartaudit, case):
    """``sb/parsing.py`` turns any parser exception into a SmartBugsError.

    A parser that raises loses the whole task, so the return shape is checked
    on every recorded case rather than only on the happy path.
    """
    findings, infos, errors, fails = llmsmartaudit.parse(*raw(TOOL, case))
    assert isinstance(findings, list)
    for group in (infos, errors, fails):
        assert isinstance(group, set)
        assert all(isinstance(m, str) for m in group)


@pytest.mark.parametrize("case", ["clean_with_findings", "backend_rejected"])
def test_finding_names_stay_within_the_declared_set(llmsmartaudit, case):
    """``sb/parsing.py`` rejects any finding name outside ``FINDINGS``."""
    findings, _i, _e, _f = llmsmartaudit.parse(*raw(TOOL, case))
    for finding in findings:
        assert finding["name"] in llmsmartaudit.FINDINGS


def test_synthetic_timeout_partial_is_reported_as_error(llmsmartaudit):
    """A salvaged partial report: 28 of 41 categories, findings kept."""
    report = {
        "tool": "LLMSmartAudit", "config": "SmartContractTA",
        "contract": "sb_Visor", "provider": "deepseek", "model": "m",
        "categories_total": 41, "categories_checked": 28, "checked": [],
        "summary": "", "findings": [
            {"name": "Reentrancy", "detector": "ReentrancyDetector",
             "classification": "SWC-107, DASP-1", "severity": "High",
             "description": "..."}],
        "sb_timeout": {"hit": True, "stage": "net",
                       "detail": "Zwischenstand geborgen"},
    }
    findings, infos, errors, fails = llmsmartaudit.parse(
        124, ["LLMSA_META {}"], synthetic_tar(
            json.dumps(report).encode("utf-8")))
    assert contains(errors, "TIMEOUT")
    # The salvaged finding must survive -- that is the whole point of AP5.
    assert len(findings) == 1
    assert contains(infos, "28/41")


def test_synthetic_no_marker_means_no_timeout_message(llmsmartaudit):
    report = {
        "tool": "LLMSmartAudit", "config": "SmartContractTA",
        "contract": "sb_Visor", "provider": "deepseek", "model": "m",
        "categories_total": 41, "categories_checked": 41, "checked": [],
        "summary": "", "findings": [],
    }
    findings, infos, errors, fails = llmsmartaudit.parse(
        0, ["LLMSA_META {}"], synthetic_tar(json.dumps(report).encode("utf-8")))
    assert not contains(errors, "TIMEOUT")
