"""Tests for GPTScan's deadline guard (AP5).

The guard is the twin of the existing budget guard: once tripped, no further
LLM call is issued and the pipeline runs to its normal end, writing whatever it
confirmed so far. Only the decision is tested here --- it lives in llm_backend
because that module imports nothing heavier than os/typing/config and is
therefore the only part of GPTScan importable on the host.
"""

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPTSCAN_SRC = os.path.join(REPO_ROOT, "GPTScan", "src")
if GPTSCAN_SRC not in sys.path:
    sys.path.insert(0, GPTSCAN_SRC)

import llm_backend  # noqa: E402  (path set up above)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """No deadline leaks between tests."""
    monkeypatch.delenv("SB_DEADLINE_EPOCH", raising=False)


def test_no_deadline_set_means_no_limit():
    """The default path: SmartBugs was invoked without --timeout."""
    assert llm_backend.deadline_exceeded() is None


def test_empty_deadline_means_no_limit(monkeypatch):
    """The entrypoint exports an empty value when TIMEOUT is 0."""
    monkeypatch.setenv("SB_DEADLINE_EPOCH", "")
    assert llm_backend.deadline_exceeded() is None


def test_future_deadline_does_not_trip(monkeypatch):
    monkeypatch.setenv("SB_DEADLINE_EPOCH", str(int(__import__("time").time()) + 3600))
    assert llm_backend.deadline_exceeded() is None


def test_past_deadline_trips_with_a_readable_reason(monkeypatch):
    monkeypatch.setenv("SB_DEADLINE_EPOCH", str(int(__import__("time").time()) - 1))
    reason = llm_backend.deadline_exceeded()
    assert reason is not None
    assert "deadline" in reason.lower()


def test_garbage_deadline_is_ignored(monkeypatch):
    """A malformed value must never abort a paid run --- it disables the guard."""
    monkeypatch.setenv("SB_DEADLINE_EPOCH", "not-a-number")
    assert llm_backend.deadline_exceeded() is None


def test_custom_provider_reads_its_endpoint_from_the_environment(monkeypatch):
    """The stand-in endpoint (testing_tools/fake_llm_endpoint.py) is reached
    this way; without it GPTScan cannot be pointed anywhere but the two
    hard-coded providers."""
    monkeypatch.setenv("GPTSCAN_PROVIDER", "custom")
    monkeypatch.setenv("GPTSCAN_BASE_URL", "http://host.docker.internal:8099")
    assert llm_backend.base_url() == "http://host.docker.internal:8099"


def test_custom_provider_is_priced_at_zero(monkeypatch):
    """A local stand-in costs nothing; the cost estimate must not invent a bill."""
    monkeypatch.setenv("GPTSCAN_PROVIDER", "custom")
    assert llm_backend.estimate_cost(1_000_000, 1_000_000) == 0.0


def test_known_providers_ignore_the_override(monkeypatch):
    """The override must not silently redirect a real, paid provider."""
    monkeypatch.setenv("GPTSCAN_PROVIDER", "deepseek")
    monkeypatch.setenv("GPTSCAN_BASE_URL", "http://127.0.0.1:1")
    assert llm_backend.base_url() == "https://api.deepseek.com"


def test_counter_and_reason_exist_on_chatgpt_api():
    """Task 3 relies on both names; they belong next to the budget bookkeeping.

    Checked statically rather than by importing: chatgpt_api imports openai
    0.27.8 (pinned in GPTScan/requirements.txt because openai.error exists only
    in the pre-1.0 SDK), tiktoken and rich, none of which are installed on the
    host. That is the same container-only boundary that put deadline_exceeded()
    into llm_backend in the first place. A runtime check here would be skipped
    in every environment this suite actually runs in --- assurance in name only.
    """
    import ast

    source = os.path.join(GPTSCAN_SRC, "chatgpt_api.py")
    with open(source, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=source)

    assigned = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                assigned[target.id] = node.value

    counter = assigned.get("num_calls_skipped_deadline")
    assert counter is not None, "num_calls_skipped_deadline is missing"
    assert isinstance(counter, ast.Call), "expected a multiprocessing Value"
    assert getattr(counter.func, "id", None) == "Value"
    assert [ast.literal_eval(a) for a in counter.args] == ["i", 0]

    reason = assigned.get("deadline_exceeded_reason")
    assert reason is not None, "deadline_exceeded_reason is missing"
    assert ast.literal_eval(reason) is None, "must start out as None"
