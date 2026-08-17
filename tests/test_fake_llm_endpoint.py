"""Tests for the stand-in LLM endpoint used to trigger timeouts for free.

The endpoint exists because LLMSmartAudit has no offline mode: every test
against the real backend costs money and is non-deterministic. A local,
deliberately slow OpenAI-compatible server makes the timeout path repeatable.
"""

import json
import urllib.request

import pytest

from testing_tools.fake_llm_endpoint import serve


@pytest.fixture
def endpoint():
    """A server on an ephemeral port, shut down after the test."""
    server, thread = serve(host="127.0.0.1", port=0, delay=0.0, reply="yes")
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    thread.join(timeout=5)


def post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer whatever"})
    with urllib.request.urlopen(req, timeout=10) as fh:
        return json.loads(fh.read().decode("utf-8"))


def test_answers_openai_shape(endpoint):
    body = post(endpoint + "/v1/chat/completions",
                {"model": "m", "messages": [{"role": "user", "content": "hi"}]})
    assert body["choices"][0]["message"]["content"] == "yes"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["usage"]["prompt_tokens"] > 0


def test_answers_without_v1_prefix(endpoint):
    """DeepSeek-style clients post to /chat/completions on a bare host."""
    body = post(endpoint + "/chat/completions",
                {"model": "m", "messages": [{"role": "user", "content": "hi"}]})
    assert body["choices"][0]["message"]["content"] == "yes"


def test_delay_is_honoured():
    """The point of the endpoint: it can be made slower than any deadline."""
    import time
    server, thread = serve(host="127.0.0.1", port=0, delay=1.0, reply="yes")
    try:
        start = time.time()
        post(f"http://127.0.0.1:{server.server_address[1]}/v1/chat/completions",
             {"model": "m", "messages": [{"role": "user", "content": "hi"}]})
        assert time.time() - start >= 1.0
    finally:
        server.shutdown()
        thread.join(timeout=5)
