"""Tests for the per-phase partial report (AP5).

LLMSmartAudit keeps everything in memory and writes only at the very end, so a
run stopped by a timeout used to lose all 40 detectors it had already finished.
Flushing after every phase turns the hard stop into a survivable event: the
entrypoint picks up the last file on disk and only the detector that was in
flight is lost.
"""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_SRC = os.path.join(REPO_ROOT, "LLMSmartAuditTool-main",
                        "LLMSmartAuditTool-main")
if TOOL_SRC not in sys.path:
    sys.path.insert(0, TOOL_SRC)

from chatdev.audit_report import AuditReportCollector  # noqa: E402


IDENTIFIED = "The analysis is complete. <INFO> Reentrancy Identified."
CLEAN = "The analysis is complete. <INFO> NO Integer Overflow."


def test_no_env_var_means_no_flush(tmp_path, monkeypatch):
    """The default path: nothing is written, exactly as before AP5."""
    monkeypatch.delenv("SB_PARTIAL_REPORT", raising=False)
    collector = AuditReportCollector()
    collector.record("ReentrancyDetector", IDENTIFIED)
    assert list(tmp_path.iterdir()) == []


def test_flush_after_every_phase(tmp_path, monkeypatch):
    out = tmp_path / "partial.json"
    monkeypatch.setenv("SB_PARTIAL_REPORT", str(out))
    monkeypatch.setenv("SB_CONTRACT_NAME", "sb_Visor")
    collector = AuditReportCollector()

    collector.record("ReentrancyDetector", IDENTIFIED)
    first = json.loads(out.read_text(encoding="utf-8"))
    assert first["categories_checked"] == 1
    assert first["contract"] == "sb_Visor"
    assert len(first["findings"]) == 1

    collector.record("ArithmeticDetector", CLEAN)
    second = json.loads(out.read_text(encoding="utf-8"))
    assert second["categories_checked"] == 2
    assert len(second["findings"]) == 1  # the clean one adds coverage, no finding


def test_every_flush_is_complete_json(tmp_path, monkeypatch):
    """A half-written file would be worse than none: the parser would read it
    as malformed and the partial result would be lost anyway."""
    out = tmp_path / "partial.json"
    monkeypatch.setenv("SB_PARTIAL_REPORT", str(out))
    collector = AuditReportCollector()
    for phase in ("ReentrancyDetector", "ArithmeticDetector", "TODDetector"):
        collector.record(phase, CLEAN)
        json.loads(out.read_text(encoding="utf-8"))  # raises if truncated


def test_flush_failure_never_breaks_the_run(tmp_path, monkeypatch):
    """An unwritable path must not take down a paid analysis."""
    monkeypatch.setenv("SB_PARTIAL_REPORT", str(tmp_path / "no" / "such" / "dir"
                                                / "x.json"))
    collector = AuditReportCollector()
    collector.record("ReentrancyDetector", IDENTIFIED)  # must not raise
    assert collector.checked == ["ReentrancyDetector"]


def test_non_detector_phases_do_not_flush(tmp_path, monkeypatch):
    """Unrelated chat phases must not rewrite the file or inflate coverage."""
    out = tmp_path / "partial.json"
    monkeypatch.setenv("SB_PARTIAL_REPORT", str(out))
    collector = AuditReportCollector()
    collector.record("DemandAnalysis", "something unrelated")
    assert not out.exists()
