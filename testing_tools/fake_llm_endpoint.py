"""A deliberately slow, OpenAI-compatible Chat-Completions stand-in.

Why this exists
---------------
Neither GPTScan nor LLMSmartAudit ships an offline mode --- LLMSmartAudit sends
even ``LLM_MODEL=STUB`` verbatim to the API --- so every test that has to reach
a timeout would otherwise cost money and depend on a remote service's mood.
This server answers in the shape both tools expect and takes exactly as long as
it is told to, which makes the timeout path free, deterministic and repeatable.

It is a test fixture, not a mock of the models: the *content* it returns is a
fixed string. Anything asserting on findings must use a real backend.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Paths both clients use: the openai 0.x SDK appends "/chat/completions" to a
# bare api_base, while a base_url ending in /v1 yields the prefixed form.
PATHS = ("/chat/completions", "/v1/chat/completions")


def _completion(model, reply, prompt_tokens):
    """One Chat-Completions response body, as the OpenAI API shapes it."""
    return {
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": len(reply.split()),
            "total_tokens": prompt_tokens + len(reply.split()),
        },
    }


class _Handler(BaseHTTPRequestHandler):
    delay = 0.0
    reply = "yes"

    def do_POST(self):  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        if self.path.rstrip("/") not in PATHS:
            self.send_error(404, "no such endpoint")
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            request = json.loads(raw.decode("utf-8"))
        except ValueError:
            self.send_error(400, "body is not JSON")
            return

        # Sleep AFTER reading the body: the client has fully sent its request,
        # so what the caller measures is the response latency, which is what a
        # slow model looks like from the outside.
        if self.delay:
            time.sleep(self.delay)

        prompt_tokens = sum(
            len(str(m.get("content", "")).split())
            for m in request.get("messages", []) or []
        ) or 1
        body = json.dumps(
            _completion(request.get("model", "fake"), self.reply, prompt_tokens)
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        """Silence the default stderr access log; tests capture enough already."""


def serve(host="127.0.0.1", port=8099, delay=0.0, reply="yes"):
    """Start the server in a background thread.

    Returns ``(server, thread)``. Call ``server.shutdown()`` then
    ``thread.join()`` to stop it. Passing ``port=0`` picks a free port, which
    the caller reads back from ``server.server_address[1]``.
    """
    handler = type("_BoundHandler", (_Handler,), {"delay": delay, "reply": reply})
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0",
                        help="bind address; 0.0.0.0 so containers can reach it")
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--delay", type=float, default=0.0,
                        help="seconds to wait before answering")
    parser.add_argument("--reply", default="yes",
                        help="assistant message content returned every time")
    args = parser.parse_args()

    server, thread = serve(args.host, args.port, args.delay, args.reply)
    print(f"fake LLM endpoint on http://{args.host}:{args.port} "
          f"(delay={args.delay}s, reply={args.reply!r})", flush=True)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
