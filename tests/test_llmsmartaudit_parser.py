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

import pytest

from conftest import contains, parse, raw, synthetic_empty_tar, synthetic_tar

TOOL = "llmsmartaudit"


# --------------------------------------------------------------------------- #
# Recorded runs
# --------------------------------------------------------------------------- #

def test_clean_run_reports_no_error_or_fail(llmsmartaudit):
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
    findings, _i, _e, fails = llmsmartaudit.parse(None, ['LLMSA_META {"provider":"deepseek"}'], None)
    assert "DOCKER_TIMEOUT" in fails
    assert findings == []


def test_synthetic_missing_archive_is_reported(llmsmartaudit):
    _f, _i, _e, fails = llmsmartaudit.parse(0, [], None)
    assert contains(fails, "no tar archive collected")


def test_synthetic_empty_archive_is_reported(llmsmartaudit):
    _f, _i, _e, fails = llmsmartaudit.parse(0, [], synthetic_empty_tar())
    assert contains(fails, "contains no output.json")


def test_synthetic_broken_json_names_the_reason(llmsmartaudit):
    _f, _i, _e, fails = llmsmartaudit.parse(0, [], synthetic_tar(b'{"tool":"LLMSmartAudit","find'))
    assert contains(fails, "not valid JSON")
    assert not contains(fails, "no tar archive collected")


def test_synthetic_report_error_field_is_an_error(llmsmartaudit):
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
