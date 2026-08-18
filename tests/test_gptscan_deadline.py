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
def test_deadline_sentinel_is_neutral_at_every_call_site():
    """After the deadline the pipeline must not be told "yes" by a call that
    never happened.

    dry_sentinel answers affirmatively on purpose --- it walks --dry-run along
    the most expensive path to get an upper bound on the call count. Reusing it
    after the deadline inflated GPTScan's candidate list from 6 to 13 in the
    measured run; nothing false reached the report, but only because the static
    confirmation stage happened to discard all of them. This pins the intended
    behaviour instead of relying on that.

    The three assertions replay the expressions the pipeline really applies to
    the answer (analyze_pipeline.py:384/474 for "choices", :404/:511 for
    "yesno").
    """
    import json

    res = llm_backend.deadline_sentinel("choices")
    assert json.loads(res.split("}")[0] + "}") == {}, "no scenario may match"

    res = llm_backend.deadline_sentinel("yesno")
    assert not res.lower().startswith("yes"), "nothing may be confirmed"

    assert llm_backend.deadline_sentinel(None) == "{}"
    assert llm_backend.deadline_sentinel("static") == "{}"

    # The point of a separate function: the dry-run sentinel still says yes.
    assert llm_backend.dry_sentinel("yesno") == "yes"


def test_deadline_branch_returns_the_neutral_sentinel():
    """Only the deadline branch switched; budget and --dry-run keep the old one.

    Read statically for the reason given in
    test_counter_and_reason_exist_on_chatgpt_api: analyze_pipeline imports
    chatgpt_api, which needs openai/tiktoken/rich --- not installed on the host.
    """
    import ast

    source = os.path.join(GPTSCAN_SRC, "analyze_pipeline.py")
    with open(source, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=source)

    func = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "ask_with_timeout")

    def sentinel_of(body):
        """Name of the llm_backend.*_sentinel this statement list returns."""
        for stmt in body:
            if (isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and getattr(stmt.value.func.value, "id", None) == "llm_backend"):
                return stmt.value.func.attr
        return None

    def counter_of(body):
        """Name of the chatgpt_api counter this statement list increments."""
        for stmt in body:
            if (isinstance(stmt, ast.AugAssign) and isinstance(stmt.op, ast.Add)
                    and isinstance(stmt.target, ast.Attribute)
                    and stmt.target.attr == "value"
                    and isinstance(stmt.target.value, ast.Attribute)):
                return stmt.target.value.attr
        return None

    guards = {counter_of(n.body): sentinel_of(n.body)
              for n in func.body if isinstance(n, ast.If)}

    assert guards.get("num_calls_skipped_deadline") == "deadline_sentinel", (
        "the deadline branch must feed back the neutral sentinel")
    assert guards.get("num_calls_skipped_budget") == "dry_sentinel", (
        "the budget branch is unchanged: it is a cost stop, not a deadline")

    # The --dry-run path has no counter of its own and keeps dry_sentinel.
    assert guards.get(None) == "dry_sentinel"
