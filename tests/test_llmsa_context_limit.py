"""Die Agentengrenze von LLMSmartAudit fuer Provider ``deepseek``.

``camel/utils.py::get_model_token_limit`` liefert die Zahl, gegen die
``chat_agent.py`` vor jedem Aufruf die Token der Konversation prueft; wird sie
erreicht, bricht der Agent mit ``max_tokens_exceeded_by_camel`` ab, ohne dass
die API je gefragt wurde. Bis zum 24.09.2026 stand fuer ``DEEPSEEK_CHAT`` fest
65 536 im Code -- daran scheiterten 37 der 96 DeFi-Contracts. Seitdem gilt:
Default weiterhin 65 536 (Vergleichbarkeit mit den Altlaeufen),
``LLM_CONTEXT_TOKENS`` hebt die Grenze an.

Das Modul haengt an ``tiktoken``, ``requests`` und ``camel.messages``, die auf
dem Host nicht installiert sein muessen; sie werden hier durch leere Module
ersetzt. ``camel.typing`` wird echt geladen, damit der Test die Enum-Eintraege
prueft, die ``run.py`` tatsaechlich setzt.
"""

import importlib.util
import os
import sys
import types

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLMSA = os.path.join(REPO_ROOT, "LLMSmartAuditTool-main", "LLMSmartAuditTool-main")


@pytest.fixture(scope="module")
def camel_utils():
    saved = {k: sys.modules.get(k) for k in ("camel", "camel.typing", "camel.messages",
                                             "camel.utils", "tiktoken", "requests")}
    pkg = types.ModuleType("camel")
    pkg.__path__ = [os.path.join(LLMSA, "camel")]
    sys.modules["camel"] = pkg
    for name in ("tiktoken", "requests"):
        sys.modules.setdefault(name, types.ModuleType(name))
    messages = types.ModuleType("camel.messages")
    messages.OpenAIMessage = dict
    sys.modules["camel.messages"] = messages
    spec = importlib.util.spec_from_file_location("camel.utils", os.path.join(LLMSA, "camel", "utils.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def test_deepseek_limit_defaults_to_the_value_of_the_recorded_runs(camel_utils, monkeypatch):
    monkeypatch.delenv("LLM_CONTEXT_TOKENS", raising=False)
    ModelType = camel_utils.ModelType
    assert camel_utils.get_model_token_limit(ModelType.DEEPSEEK_CHAT) == 65536


def test_deepseek_limit_follows_llm_context_tokens(camel_utils, monkeypatch):
    monkeypatch.setenv("LLM_CONTEXT_TOKENS", "200000")
    ModelType = camel_utils.ModelType
    assert camel_utils.get_model_token_limit(ModelType.DEEPSEEK_CHAT) == 200000
    # Der Provider ``custom`` las die Variable schon immer, mit anderem Default.
    assert camel_utils.get_model_token_limit(ModelType.CUSTOM) == 200000
    monkeypatch.delenv("LLM_CONTEXT_TOKENS")
    assert camel_utils.get_model_token_limit(ModelType.CUSTOM) == 16384
