# AP5 — Timeout durchreichen: Implementierungsplan

> **Zum Gebrauch:** Wir arbeiten diesen Plan Aufgabe für Aufgabe ab. Die Schritte
> tragen Checkbox-Syntax (`- [ ]`), damit sich der Fortschritt direkt darin
> abhaken lässt.

**Ziel:** Der von SmartBugs übergebene Timeout wirkt innerhalb des Containers, und
was ein Werkzeug bis zum Ablaufen ermittelt hat, landet gekennzeichnet im Ergebnis.

**Architektur:** Der Entrypoint rechnet aus `$TIMEOUT` drei Marken (70 % Bremse,
90 % Netz, Rest Aufräumen) und exportiert die Bremse als absoluten Zeitstempel
`SB_DEADLINE_EPOCH`. GPTScan wertet ihn in seiner zentralen LLM-Messstelle aus und
läuft freiwillig aus; LLMSmartAudit schreibt stattdessen nach jeder Detektor-Phase
einen Zwischenstand, den der Entrypoint nach einem harten Abbruch birgt. Beide
Ergebnisse tragen denselben Marker `sb_timeout`.

**Tech-Stack:** Python 3, POSIX `sh`, `pytest`, Docker.

**Entwurf:** `docs/BA-AP5-TIMEOUT-DESIGN.md` — dieser Plan argumentiert aus dem
Entwurf; wir arbeiten aus beiden Dokumenten.

---

## Globale Randbedingungen

Gelten für **jede** Aufgabe, ohne dass sie dort wiederholt werden.

* **`TIMEOUT=0` ändert nichts.** Ohne Timeout muss sich jede berührte Komponente
  Byte für Byte wie vorher verhalten. Die 19 bereits gefahrenen Messläufe müssen
  vergleichbar bleiben. Jede Aufgabe, die Verhalten hinzufügt, testet diesen Fall.
* **Keine neue Fremddatei.** Es dürfen ausschließlich Dateien geändert werden, die
  `docs/BA-EIGENANTEIL.md` bereits als geändert oder neu führt. Zeigt sich bei einer
  Aufgabe, dass sie eine bisher unberührte Fremddatei verlangt: **anhalten und
  gemeinsam entscheiden**, nicht stillschweigend ändern.
* **Name der Umgebungsvariable:** `SB_DEADLINE_EPOCH` — absoluter Unix-Zeitstempel
  in ganzen Sekunden. Ungesetzt oder leer bedeutet: keine Deadline.
* **Marker-Schema** (oberste Ebene des jeweiligen Report-JSON, Pflichtfelder
  `hit` und `stage`):
  ```json
  "sb_timeout": {"hit": true, "stage": "brake", "detail": "Freitext"}
  ```
  `stage` ist genau `"brake"` oder `"net"`. Fehlt `sb_timeout`, war der Lauf
  vollständig.
* **Marken:** Bremse = 70 % von `TIMEOUT`, Netz = 90 %, ganzzahlig abgerundet,
  Mindestwert 1 s.
* **Normalisierter Exit-Code:** Hat das Netz gegriffen, beendet sich der Entrypoint
  mit **124** — auch wenn `timeout` selbst 143 oder 137 gemeldet hat.
* **Sprache:** Kommentare und Docstrings in neuem Code auf **Englisch** (so hält es
  der gesamte Code des Projekts); Dokumentation unter `docs/` auf **Deutsch**.
* **Commits:** eine Betreffzeile je Commit, kein Body, kein Trailer.
* **Tests laufen mit:** `python -m pytest tests/ -q` aus dem Repository-Wurzelverzeichnis.

---

## Dateiübersicht

| Datei | Verantwortung | Aufgabe |
|---|---|---|
| `docs/BA-AP5-VORPRUEFUNG.md` | *neu* — Befund: gibt es `timeout` in den Images, mit welchem Exit-Code | 0 |
| `testing_tools/fake_llm_endpoint.py` | *neu* — langsamer OpenAI-kompatibler Prüfstand-Endpunkt | 1 |
| `tests/test_fake_llm_endpoint.py` | *neu* — Tests dazu | 1 |
| `GPTScan/src/llm_backend.py` | Deadline-Entscheidung (`deadline_exceeded`), Endpunkt-Override | 2, 6 |
| `GPTScan/src/chatgpt_api.py` | Zähler `num_calls_skipped_deadline`, Grund-Variable | 2 |
| `GPTScan/src/analyze_pipeline.py` | Wächter in `ask_with_timeout` | 3 |
| `GPTScan/src/tasks.py` | `sb_timeout` in die Metadaten | 3 |
| `GPTScan/src/config.py` | Provider-Eintrag `custom` für den Prüfstand | 6 |
| `tests/test_gptscan_deadline.py` | *neu* — Tests zu 2 | 2 |
| `smartbugs/tools/gptscan/scripts/do_solidity.sh` | Marken, Netz, Exit-Normalisierung | 4 |
| `smartbugs/tools/gptscan/scripts/mark_timeout.py` | *neu* — stempelt `sb_timeout` in einen Report | 4 |
| `smartbugs/tools/gptscan/parser.py` | `sb_timeout` → `errors` | 5 |
| `LLMSmartAuditTool-main/.../chatdev/audit_report.py` | Zwischenstand nach jeder Phase | 7 |
| `tests/test_audit_report_partial.py` | *neu* — Tests zu 7 | 7 |
| `smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh` | Marken, Netz, Bergung | 8 |
| `smartbugs/tools/llmsmartaudit/scripts/mark_timeout.py` | *neu* — Zwilling von Aufgabe 4 | 8 |
| `smartbugs/tools/llmsmartaudit/parser.py` | `sb_timeout` → `errors` | 9 |
| `tests/test_entrypoint_timeout.py` | *neu* — beide Entrypoints, echtes `sh` | 10 |
| `analysis_tools/gptscan_eval.py`, `errors_fails_report.py` | Spalten `timeout_hit`, `timeout_stage` | 11 |
| `docs/*` | Nachzug der Dokumentation | 12 |

## Reihenfolge und Abhängigkeiten

Wir arbeiten die Aufgaben in Wellen ab. Innerhalb einer Welle sind die Aufgaben
dateidisjunkt und lassen sich deshalb nebeneinander bearbeiten; zwischen den
Wellen bestehen echte Abhängigkeiten. Der Schnittstellenvertrag aus den globalen
Randbedingungen — Name der Umgebungsvariablen, Marker-Schema, Marken — steht
fest, bevor die erste Aufgabe beginnt, und ändert sich danach nicht mehr.

| Welle | Aufgaben | Warum in dieser Reihenfolge |
|---|---|---|
| 1 | **0** (Vorprüfung) · **1** (Prüfstand) | mechanisch, klar umrissen; voneinander unabhängig |
| 2 | **2** (GPTScan-Wächter) · **7** (LLMSA-Flush) | Kern der Arbeit: Nebenläufigkeit und Zustand über Prozessgrenzen |
| 3 | **3** (GPTScan-Verdrahtung) · **8** (LLMSA-Entrypoint) | 3 hängt an 2; 8 folgt einem in 4 vorgegebenen Muster |
| 4 | **4** (GPTScan-Entrypoint) · **9** (LLMSA-Parser) · **6** (Prüfstand-Anbindung) | 4 legt das Shell-Muster fest, das 8 spiegelt |
| 5 | **5** (GPTScan-Parser) · **10** (Entrypoint-Tests) · **11** (Auswertung) | Routine gegen einen inzwischen festen Vertrag |
| 6 | **12** (Doku) | zieht nach, was die Aufgaben davor geschaffen haben |
| 7 | **13** (scharfer Lauf) | erst wenn alles steht; hier entstehen Kosten |

**Aufgabe 0 blockiert alles.** Fehlt `timeout` in einem Image, ändert sich das
Vorgehen in den Aufgaben 4 und 8.

---

### Aufgabe 0: Vorprüfung — gibt es `timeout` in den Images?

**Einordnung:** Rein diagnostisch, ohne Eingriff in den Produktivcode.

**Dateien:**
- Erstellen: `docs/BA-AP5-VORPRUEFUNG.md`

**Schnittstellen:**
- Liefert: den Befund, auf den sich die Aufgaben 4 und 8 stützen — ob `timeout`
  vorhanden ist und welchen Exit-Code es bei Ablauf meldet.

- [ ] **Schritt 1: Vorhandensein prüfen, beide Images**

```bash
docker run --rm --entrypoint sh smartbugs/gptscan:1.0 -c \
  'command -v timeout || echo MISSING; timeout --version 2>&1 | head -1'
docker run --rm --entrypoint sh smartbugs/llmsmartaudit:1.0 -c \
  'command -v timeout || echo MISSING; timeout --version 2>&1 | head -1'
```

Erwartet: ein Pfad wie `/usr/bin/timeout` und eine Versionszeile mit `coreutils`.

- [ ] **Schritt 2: Exit-Code bei Ablauf messen, beide Images**

```bash
docker run --rm --entrypoint sh smartbugs/gptscan:1.0 -c \
  'timeout 1 sleep 5; echo "RC=$?"'
docker run --rm --entrypoint sh smartbugs/llmsmartaudit:1.0 -c \
  'timeout 1 sleep 5; echo "RC=$?"'
```

Erwartet: `RC=124` (GNU coreutils) oder `RC=143` (BusyBox). **Beides ist in
Ordnung** — der Entrypoint normalisiert später ohnehin auf 124. Notiert wird der
tatsächlich gemessene Wert.

- [ ] **Schritt 3: Befund festhalten**

`docs/BA-AP5-VORPRUEFUNG.md` anlegen mit: je Image der Pfad zu `timeout`, die
Versionszeile, der gemessene Exit-Code, das Datum der Messung und die wörtlich
ausgeführten Kommandos. Kurz halten — eine Seite genügt.

- [ ] **Schritt 4: Sonderfall melden**

Fällt ein Image auf `MISSING`, **hier anhalten** und den Befund festhalten. Dann
tritt in den Aufgaben 4 und 8 die Ersatzlösung in Kraft (Hintergrundprozess mit
`kill` statt `timeout`), die dort gesondert beschrieben ist.

- [ ] **Schritt 5: Commit**

```bash
git add docs/BA-AP5-VORPRUEFUNG.md
git commit -m "AP5: Vorpruefung timeout-Kommando in beiden Images"
```

---

### Aufgabe 1: Prüfstand — langsamer LLM-Endpunkt

**Einordnung:** Abgeschlossenes Stück Standard-Python, keine Verflechtung.

**Dateien:**
- Erstellen: `testing_tools/fake_llm_endpoint.py`, `testing_tools/__init__.py`
- Ändern: `tests/conftest.py` (Wurzelverzeichnis auf den Suchpfad)
- Test: `tests/test_fake_llm_endpoint.py`

**Vorbedingung, geprüft:** Das Projekt hat **keine** pytest-Konfiguration
(kein `pytest.ini`, `setup.cfg`, `pyproject.toml`, `tox.ini`). pytest legt
deshalb nur das Verzeichnis der `conftest.py` auf den Suchpfad, nicht das
Repository-Wurzelverzeichnis — `import testing_tools` schlägt ohne den Zusatz
aus Schritt 3a fehl.

**Schnittstellen:**
- Liefert: `serve(host, port, delay, reply)` und einen CLI-Einstieg
  `python -m testing_tools.fake_llm_endpoint --port 8099 --delay 30`.
  Beantwortet `POST /chat/completions` **und** `POST /v1/chat/completions`
  OpenAI-kompatibel. Aufgabe 6 und Aufgabe 13 benutzen ihn.

- [ ] **Schritt 1: Den fehlschlagenden Test schreiben**

`tests/test_fake_llm_endpoint.py`:

```python
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
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_fake_llm_endpoint.py -q`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'testing_tools'`

- [ ] **Schritt 3a: Das Wurzelverzeichnis auf den Suchpfad legen**

In `tests/conftest.py`, direkt hinter der Zeile, die `SMARTBUGS` auf den Pfad
legt (`if SMARTBUGS not in sys.path: sys.path.insert(0, SMARTBUGS)`):

```python
# The project has no pytest configuration, so pytest puts only this directory
# on the path -- not the repository root. Tests that import a project package
# (testing_tools) need it there explicitly.
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
```

`REPO_ROOT` ist in der Datei bereits definiert.

- [ ] **Schritt 3b: Die minimale Implementierung schreiben**

`testing_tools/__init__.py` als leere Datei anlegen, dann
`testing_tools/fake_llm_endpoint.py`:

```python
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
```

- [ ] **Schritt 4: Tests laufen lassen, Erfolg bestätigen**

Ausführen: `python -m pytest tests/test_fake_llm_endpoint.py -q`
Erwartet: 3 passed

- [ ] **Schritt 5: Commit**

```bash
git add testing_tools/ tests/test_fake_llm_endpoint.py tests/conftest.py
git commit -m "AP5: lokaler LLM-Endpunkt fuer wiederholbare Timeout-Tests"
```

---

### Aufgabe 2: GPTScan — die Deadline-Entscheidung

**Einordnung:** Heikel. Der Zustand muss über die `multiprocessing`-Grenze hinweg
stimmen; hier wird falsch gebaut, wenn man das Muster des Budget-Wächters nicht
genau nachvollzieht.

**Dateien:**
- Ändern: `GPTScan/src/llm_backend.py` (neue Funktion ans Ende, hinter `budget_exceeded`)
- Ändern: `GPTScan/src/chatgpt_api.py:27-31` (Zähler und Grund-Variable)
- Test: `tests/test_gptscan_deadline.py` *(neu)*

**Schnittstellen:**
- Liefert: `llm_backend.deadline_exceeded() -> Optional[str]` — gibt einen
  lesbaren Grund zurück, wenn `SB_DEADLINE_EPOCH` gesetzt und überschritten ist,
  sonst `None`. Aufgabe 3 ruft sie auf.
- Liefert: `chatgpt_api.num_calls_skipped_deadline` (ein
  `multiprocessing.Value("i", 0)`) und `chatgpt_api.deadline_exceeded_reason`
  (Modul-Global, nur im Elternprozess gesetzt). Aufgabe 3 zählt hoch, Aufgabe 3
  liest den Grund für die Metadaten.

**Hintergrund für die ausführende Person.** `llm_backend.py` ist absichtlich frei
von schweren Importen (nur `os`, `typing`, `config`) — deshalb ist es die einzige
Stelle in GPTScan, die sich auf dem Host ohne Container testen lässt. Die
Entscheidung „Frist abgelaufen?" gehört genau deshalb hierher, nicht in
`analyze_pipeline.py`; dort steht später nur die Verdrahtung. Das ist dasselbe
Muster wie beim Budget: `budget_exceeded()` entscheidet hier, `ask_with_timeout()`
handelt danach.

- [ ] **Schritt 1: Den fehlschlagenden Test schreiben**

`tests/test_gptscan_deadline.py`:

```python
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
```

**Warum statisch.** `GPTScan/src/chatgpt_api.py` importiert auf Modulebene
`openai`, `tiktoken` und `rich`; `GPTScan/requirements.txt:31` pinnt
`openai==0.27.8`, weil nur die Pre-1.0-SDK `openai.error` kennt. Das Modul ist
damit container-only — dieselbe Grenze, die die Entscheidungsfunktion nach
`llm_backend.py` gebracht hat. Ein Laufzeittest wäre hier in jeder real
genutzten Umgebung übersprungen worden.

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_gptscan_deadline.py -q`
Erwartet: FAIL mit `AttributeError: module 'llm_backend' has no attribute 'deadline_exceeded'`

- [ ] **Schritt 3: Die Entscheidungsfunktion schreiben**

In `GPTScan/src/llm_backend.py`, unmittelbar hinter `budget_exceeded` (Zeile 192)
anfügen — und `import time` oben bei `import os` ergänzen:

```python
# ---------------------------------------------------------------------------
# Deadline guard (SmartBugs --timeout, see docs/BA-AP5-TIMEOUT-DESIGN.md)
# ---------------------------------------------------------------------------

# Absolute wall-clock deadline in Unix seconds, exported by the SmartBugs
# entrypoint. Absolute rather than a remaining duration because every real LLM
# call runs in a multiprocessing worker: an absolute instant means the same
# thing in parent and child, a remaining duration does not.
ENV_DEADLINE = "SB_DEADLINE_EPOCH"


def deadline_exceeded() -> Optional[str]:
    """Return a human-readable reason once the run's deadline has passed.

    Returns None when no deadline is configured, when it lies in the future, or
    when the value cannot be read as a number. That last case is deliberate: a
    malformed variable must never cut a paid run short --- it disables the
    guard, exactly as an unset variable does.
    """
    raw = os.environ.get(ENV_DEADLINE)
    if not raw:
        return None
    try:
        deadline = float(raw)
    except (TypeError, ValueError):
        return None
    overdue = time.time() - deadline
    if overdue < 0:
        return None
    return (f"SmartBugs deadline reached ({ENV_DEADLINE}={int(deadline)}, "
            f"{overdue:.0f}s over)")
```

- [ ] **Schritt 4: Zähler und Grund-Variable anlegen**

In `GPTScan/src/chatgpt_api.py`, direkt hinter `num_calls_skipped_budget`
(Zeile 29) bzw. `budget_exceeded_reason` (Zeile 31):

```python
# Calls suppressed because the SmartBugs deadline passed (AP5). Kept apart from
# num_calls_skipped_budget so the metadata can say WHY a run stopped early.
num_calls_skipped_deadline = Value("i", 0)

# Set once in the parent process when the deadline guard first trips; None means
# it never did. Plain global, not a Value: only the parent ever writes it, the
# same way budget_exceeded_reason works.
deadline_exceeded_reason = None
```

- [ ] **Schritt 5: Tests laufen lassen, Erfolg bestätigen**

Ausführen: `python -m pytest tests/test_gptscan_deadline.py -q`
Erwartet: 6 passed

- [ ] **Schritt 6: Commit**

```bash
git add GPTScan/src/llm_backend.py GPTScan/src/chatgpt_api.py tests/test_gptscan_deadline.py
git commit -m "AP5: Deadline-Entscheidung und Zaehler fuer GPTScan"
```

---

### Aufgabe 3: GPTScan — Wächter verdrahten und Marker melden

**Einordnung:** Heikel. Der Eingriff sitzt in der heißesten Funktion des Werkzeugs;
ein Fehler hier kostet bei jedem künftigen Lauf Geld.

**Dateien:**
- Ändern: `GPTScan/src/analyze_pipeline.py:56-70` (Wächterblock erweitern)
- Ändern: `GPTScan/src/tasks.py:429-431` (Metadatenfelder)

**Schnittstellen:**
- Verbraucht: `llm_backend.deadline_exceeded()`,
  `chatgpt_api.num_calls_skipped_deadline`, `chatgpt_api.deadline_exceeded_reason`
  aus Aufgabe 2.
- Liefert: in `/output.json.metadata.json` die Felder
  `llm_calls_skipped_deadline` (int), `deadline_exceeded` (str oder null) und
  `sb_timeout` (Objekt oder fehlend). Aufgabe 5 liest sie.

- [ ] **Schritt 1: Den Wächter einsetzen**

In `GPTScan/src/analyze_pipeline.py`, **vor** dem bestehenden Budget-Block
(aktuell Zeile 56, beginnend mit dem Kommentar `# Hard budget guard`) einfügen:

```python
    # Deadline guard (live runs only), the twin of the budget guard below: once
    # the SmartBugs deadline has passed we stop issuing calls and return
    # sentinels, so the scan still finishes and writes partial results instead
    # of being killed with nothing to show. Checked in the parent for the same
    # reason as the budget: it must hold regardless of the multiprocessing
    # start method.
    if not dry_run and chatgpt_api.deadline_exceeded_reason is None:
        reason = llm_backend.deadline_exceeded()
        if reason:
            chatgpt_api.deadline_exceeded_reason = reason
            logger.warning(
                f"Deadline guard tripped: {reason}. Skipping all remaining LLM calls.")
    if not dry_run and chatgpt_api.deadline_exceeded_reason is not None:
        chatgpt_api.num_calls_skipped_deadline.value += 1
        return llm_backend.dry_sentinel(kind)
```

Der Budget-Block bleibt **unverändert** darunter stehen. Beide Wächter sind
unabhängig; welcher zuerst greift, entscheidet allein die Lage.

- [ ] **Schritt 2: Prüfen, dass ohne Deadline nichts passiert**

Ausführen: `python -m pytest tests/ -q`
Erwartet: alle bisherigen Tests weiterhin grün (78 + die neuen). Der Wächter darf
sich ohne gesetzte Umgebungsvariable nicht bemerkbar machen.

- [ ] **Schritt 3: Die Metadatenfelder ergänzen**

In `GPTScan/src/tasks.py`, direkt hinter `meta_data["budget_exceeded"] = ...`
(Zeile 431):

```python
    meta_data["llm_calls_skipped_deadline"] = int(chatgpt_api.num_calls_skipped_deadline.value)
    meta_data["deadline_exceeded"] = chatgpt_api.deadline_exceeded_reason
    # The marker SmartBugs' parser looks for. Present only when the deadline
    # actually cut the run short, so its absence means "this run was complete"
    # (docs/BA-AP5-TIMEOUT-DESIGN.md, 4.2).
    if chatgpt_api.deadline_exceeded_reason:
        meta_data["sb_timeout"] = {
            "hit": True,
            "stage": "brake",
            "detail": "{} LLM-Aufrufe wegen der Frist unterdrueckt: {}".format(
                int(chatgpt_api.num_calls_skipped_deadline.value),
                chatgpt_api.deadline_exceeded_reason),
        }
```

**Achtung:** dieser Block muss **vor** der Schleife stehen, die Mengen in
Längen umrechnet (`for metadata_key, metadata_value in meta_data.copy().items()`,
Zeile 433) — sonst wird `sb_timeout` nicht angefasst, was hier zwar folgenlos
wäre, aber die Reihenfolge lesbar hält.

- [ ] **Schritt 4: Gegenprobe von Hand**

```bash
cd GPTScan/src && SB_DEADLINE_EPOCH=1 python -c "
import llm_backend
print('reason:', llm_backend.deadline_exceeded())"
```
Erwartet: eine Zeile mit `SmartBugs deadline reached (SB_DEADLINE_EPOCH=1, …s over)`.

**Warum hier kein `import chatgpt_api`.** Das Modul zieht `openai==0.27.8`,
`tiktoken` und `rich` und ist auf dem Host nicht ladbar — dieselbe container-only
Grenze, die schon Test 6 der Aufgabe 2 auf eine statische Prüfung gebracht hat.
Der Anfangswert von `num_calls_skipped_deadline` ist dort bereits abgedeckt; eine
zweite, hier nicht ausführbare Prüfung bringt nichts dazu.

- [ ] **Schritt 5: Commit**

```bash
git add GPTScan/src/analyze_pipeline.py GPTScan/src/tasks.py
git commit -m "AP5: Deadline-Waechter in GPTScans LLM-Messstelle verdrahtet"
```

---

### Aufgabe 4: GPTScan — Entrypoint rechnet die Marken

**Einordnung:** Weitreichend. Legt das Shell-Muster fest, das Aufgabe 8 spiegelt;
die Exit-Code-Normalisierung entscheidet darüber, ob SmartBugs den Timeout als
`error` oder als `fail` verbucht.

**Dateien:**
- Ändern: `smartbugs/tools/gptscan/scripts/do_solidity.sh`
- Erstellen: `smartbugs/tools/gptscan/scripts/mark_timeout.py`

**Schnittstellen:**
- Liefert: das Marken-Rechenwerk als Shell-Block, den Aufgabe 8 wörtlich
  übernimmt, und `mark_timeout.py` mit dem Aufruf
  `python3 mark_timeout.py <report.json> <stage> [detail]`.

**Vorbedingung:** Befund aus Aufgabe 0. Meldete ein Image dort `MISSING`, ist
statt `timeout` die Ersatzlösung in Schritt 6 zu verwenden.

- [ ] **Schritt 1: Den Stempel-Helfer schreiben**

`smartbugs/tools/gptscan/scripts/mark_timeout.py`:

```python
#!/usr/bin/env python3
"""Stamp the sb_timeout marker onto a tool report that was cut short.

Called by the entrypoint when the net fired: the tool was stopped from the
outside, so it never got the chance to record that fact itself. When the *brake*
fired instead, the tool writes the marker on its own and this script is not
involved.

Never fails destructively --- a report that cannot be read or written is left
exactly as it is and the reason goes to stderr, where SmartBugs captures it as
part of the log. Losing a partial result to a marker script would defeat the
entire point of AP5.
"""

import json
import sys


def stamp(path, stage, detail=""):
    """Add sb_timeout to the JSON object at *path*. Returns True when written."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            report = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"mark_timeout: cannot read {path}: {e}", file=sys.stderr)
        return False

    if not isinstance(report, dict):
        print(f"mark_timeout: {path} is not a JSON object", file=sys.stderr)
        return False

    report["sb_timeout"] = {"hit": True, "stage": stage, "detail": detail}

    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"mark_timeout: cannot write {path}: {e}", file=sys.stderr)
        return False
    return True


def main(argv):
    if len(argv) < 3:
        print("usage: mark_timeout.py <report.json> <brake|net> [detail]",
              file=sys.stderr)
        return 2
    stage = argv[2]
    if stage not in ("brake", "net"):
        print(f"mark_timeout: stage must be 'brake' or 'net', got {stage!r}",
              file=sys.stderr)
        return 2
    detail = argv[3] if len(argv) > 3 else ""
    return 0 if stamp(argv[1], stage, detail) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Schritt 2: Den Helfer testen**

Ausführen:
```bash
python -c "
import json, tempfile, os, sys
sys.path.insert(0, 'smartbugs/tools/gptscan/scripts')
import mark_timeout
p = tempfile.mktemp(suffix='.json')
json.dump({'results': []}, open(p, 'w'))
assert mark_timeout.stamp(p, 'net', 'abgebrochen')
d = json.load(open(p))
assert d['sb_timeout'] == {'hit': True, 'stage': 'net', 'detail': 'abgebrochen'}
assert d['results'] == []
assert not mark_timeout.stamp('/nonexistent/x.json', 'net')
os.remove(p); print('ok')"
```
Erwartet: `ok`

- [ ] **Schritt 3: Das Marken-Rechenwerk in den Entrypoint einsetzen**

In `smartbugs/tools/gptscan/scripts/do_solidity.sh`, **nach** dem MAIN-Block
(hinter Zeile 34) und vor dem `WORK=/work/input`-Block einfügen:

```sh
# --- Timeout budget (AP5, docs/BA-AP5-TIMEOUT-DESIGN.md 4.1) ----------------
# Three marks out of the one TIMEOUT SmartBugs hands us:
#   70%  brake -- exported as an absolute deadline; GPTScan stops issuing LLM
#         calls and runs out on its own, writing what it confirmed so far
#   90%  net   -- 'timeout' stops the tool if the brake did not take effect
#   rest       -- belongs to this script, to salvage and write /output.json
# TIMEOUT=0 (no --timeout) leaves every one of them unset: the run then behaves
# byte for byte as it did before AP5, which keeps the earlier runs comparable.
NET=0
if [ "${TIMEOUT:-0}" -gt 0 ]; then
    BRAKE=$(( TIMEOUT * 7 / 10 ))
    NET=$(( TIMEOUT * 9 / 10 ))
    [ "$BRAKE" -lt 1 ] && BRAKE=1
    [ "$NET" -lt 1 ] && NET=1
    SB_DEADLINE_EPOCH=$(( $(date +%s) + BRAKE ))
    export SB_DEADLINE_EPOCH
    echo "SB_TIMEOUT_BUDGET timeout=${TIMEOUT}s brake=${BRAKE}s net=${NET}s"
fi
```

- [ ] **Schritt 4: Den Werkzeugaufruf unter das Netz stellen**

Die Zeile 59 (`python3 main.py -s "$WORK" ...`) ersetzen durch:

```sh
if [ "$NET" -gt 0 ]; then
    timeout -s TERM "$NET" python3 main.py -s "$WORK" -o /output.json \
        --provider "$PROVIDER" $MODEL_OPT $DRY_OPT --format json
else
    python3 main.py -s "$WORK" -o /output.json \
        --provider "$PROVIDER" $MODEL_OPT $DRY_OPT --format json
fi
RC=$?

# 'timeout' reports 124 (GNU) or 143 (BusyBox); 137 appears when a SIGTERM was
# escalated to SIGKILL. All three mean "we stopped it on purpose", but SmartBugs
# reads 143 and 137 as DOCKER_RECEIVED_SIGNAL_n and files them under *fails*
# (sb/parse_utils.py:81-82) --- the category for a tool that was knocked out.
# A deliberate timeout is not that, so the code is normalised to 124, which
# lands in *errors*: noticed and handled.
TIMED_OUT=0
if [ "$NET" -gt 0 ]; then
    case "$RC" in
        124|137|143) TIMED_OUT=1; RC=124 ;;
    esac
fi
```

- [ ] **Schritt 5: Den Marker setzen, wenn das Netz griff**

Direkt vor dem abschließenden `exit $RC` (bisher Zeile 74), **nach** dem Block,
der ein fehlendes `/output.json` erzeugt:

```sh
# The brake writes its own marker (GPTScan does it in tasks.py); only the net
# needs a stamp from outside, because the tool never learned it was stopped.
if [ "$TIMED_OUT" = "1" ]; then
    python3 "$BIN/mark_timeout.py" /output.json net \
        "GPTScan nach ${NET}s hart beendet; Bremse bei ${BRAKE}s griff nicht" \
        || echo "GPTScan: could not stamp the timeout marker"
fi
```

- [ ] **Schritt 6: Nur falls Aufgabe 0 `MISSING` meldete — entfällt**

> **Erledigt durch die Vorprüfung.** `docs/BA-AP5-VORPRUEFUNG.md` weist für beide
> Images GNU-coreutils-`timeout` nach (gptscan 9.1, llmsmartaudit 9.7), Exit-Code
> 124 bei Ablauf. Dieser Schritt ist **nicht auszuführen**; er bleibt als
> dokumentierte Rückfallebene stehen, falls sich ein Image später ändert.

Fehlt `timeout` im Image, statt Schritt 4 diese Fassung verwenden — gleiche
Wirkung, ohne das Kommando:

```sh
if [ "$NET" -gt 0 ]; then
    python3 main.py -s "$WORK" -o /output.json \
        --provider "$PROVIDER" $MODEL_OPT $DRY_OPT --format json &
    TOOL_PID=$!
    ( sleep "$NET"; kill -TERM "$TOOL_PID" 2>/dev/null ) &
    WATCHDOG_PID=$!
    wait "$TOOL_PID"
    RC=$?
    kill "$WATCHDOG_PID" 2>/dev/null
else
    ...
fi
```
Die Exit-Normalisierung aus Schritt 4 bleibt unverändert: ein per SIGTERM
beendeter Prozess meldet 143, und genau den fängt die `case`-Zeile ab.

- [ ] **Schritt 7: Syntaxprüfung**

Ausführen: `sh -n smartbugs/tools/gptscan/scripts/do_solidity.sh`
Erwartet: keine Ausgabe (die Datei ist syntaktisch gültig). Der volle
Verhaltenstest folgt in Aufgabe 10.

- [ ] **Schritt 8: Commit**

```bash
git add smartbugs/tools/gptscan/scripts/
git commit -m "AP5: GPTScan-Entrypoint rechnet Timeout-Marken und stempelt den Marker"
```

---

### Aufgabe 5: GPTScan — Parser meldet den Timeout

**Einordnung:** Fester Vertrag, vorhandenes Muster.

**Dateien:**
- Ändern: `smartbugs/tools/gptscan/parser.py`
- Test: `tests/test_gptscan_parser.py` (ergänzen)

**Schnittstellen:**
- Verbraucht: `sb_timeout` aus dem Report und aus dem `GPTSCAN_META`-Block
  (Aufgaben 3 und 4).
- Liefert: einen Eintrag in `errors` mit dem Präfix `TIMEOUT_`.

- [ ] **Schritt 1: Die fehlschlagenden Tests schreiben**

An `tests/test_gptscan_parser.py` anfügen — dem Stil der Datei folgen und
`synthetic` im Namen führen, weil das Material konstruiert ist:

```python
def test_synthetic_timeout_brake_is_reported_as_error(gptscan):
    """The brake fired: GPTScan ran out on its own and wrote what it had."""
    report = {
        "version": "1.1.0", "success": True, "results": [],
        "sb_timeout": {"hit": True, "stage": "brake",
                       "detail": "17 LLM-Aufrufe wegen der Frist unterdrueckt"},
    }
    findings, infos, errors, fails = gptscan.parse(
        0, ["GPTScan: provider=deepseek"], synthetic_tar(
            json.dumps(report).encode("utf-8")))
    assert contains(errors, "TIMEOUT")
    assert contains(errors, "brake")
    assert not fails


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
```

Am Kopf der Testdatei sicherstellen, dass `json`, `synthetic_tar` und `contains`
importiert sind (aus `conftest`).

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_gptscan_parser.py -q -k timeout`
Erwartet: 2 FAILED (die beiden Marker-Tests), 1 passed

- [ ] **Schritt 3: Den Parser-Zweig schreiben**

In `smartbugs/tools/gptscan/parser.py`, in `parse()` unmittelbar hinter dem
`success is false`-Zweig (Zeile 330-331) und **vor** der Schleife
`for r in result.get("results", []) or []` (Zeile 333):

```python
    # Timeout marker (AP5). Two routes lead here: the brake writes it into the
    # metadata GPTScan produces itself (GPTSCAN_META), the net gets stamped onto
    # /output.json by the entrypoint. Either way it belongs in *errors* --
    # SmartBugs' category for a problem the run noticed and handled -- and never
    # in *fails*, which is reserved for a tool that was knocked out.
    sb_timeout = result.get("sb_timeout") or (meta or {}).get("sb_timeout")
    if isinstance(sb_timeout, dict) and sb_timeout.get("hit"):
        stage = str(sb_timeout.get("stage", "unknown"))
        detail = sb_timeout.get("detail") or ""
        errors.add(f"TIMEOUT_{stage.upper()}: run cut short ({stage})"
                   + (f" -- {detail}" if detail else ""))
```

**`meta` kann `None` sein.** Zeile 298-299 der Datei setzt `meta = _meta(log)` und
behandelt `meta is None` als eigenen Fall — die `GPTSCAN_META`-Zeile fehlt, wenn
der Container mitten in der Analyse starb. Genau das ist bei einem harten Abbruch
der Normalfall, deshalb das `(meta or {})` oben. Ohne die Klammer wirft der Parser
an der Stelle, an der er am dringendsten gebraucht wird.

- [ ] **Schritt 4: Tests laufen lassen, Erfolg bestätigen**

Ausführen: `python -m pytest tests/test_gptscan_parser.py -q`
Erwartet: alle grün, inklusive der bisherigen Fälle

- [ ] **Schritt 5: Commit**

```bash
git add smartbugs/tools/gptscan/parser.py tests/test_gptscan_parser.py
git commit -m "AP5: GPTScan-Parser meldet den Timeout als error"
```

---

### Aufgabe 6: GPTScan — Anbindung an den Prüfstand

**Einordnung:** Zwei kleine, klar umrissene Ergänzungen.

**Dateien:**
- Ändern: `GPTScan/src/config.py:41-67` (dritter Provider-Eintrag)
- Ändern: `GPTScan/src/llm_backend.py:90-96` (Endpunkt-Override)
- Test: `tests/test_gptscan_deadline.py` (ergänzen)

**Hintergrund.** Die Provider-Tabelle kennt heute nur `openai` und `deepseek`, beide
mit fest hinterlegter `base_url`. Ohne einen dritten Eintrag lässt sich GPTScan
nicht auf den Prüfstand aus Aufgabe 1 richten. LLMSmartAudit kann das bereits
(`LLM_PROVIDER=custom` plus `LLM_BASE_URL`); dieser Schritt gleicht GPTScan an.

- [ ] **Schritt 1: Die fehlschlagenden Tests schreiben**

An `tests/test_gptscan_deadline.py` anfügen:

```python
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
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_gptscan_deadline.py -q -k custom`
Erwartet: FAIL — `custom` ist kein bekannter Provider

- [ ] **Schritt 3: Den Provider-Eintrag ergänzen**

In `GPTScan/src/config.py`, in `PROVIDERS` hinter dem `deepseek`-Block (Zeile 66):

```python
    "custom": {
        # An OpenAI-compatible endpoint chosen at run time, e.g. the local
        # stand-in in testing_tools/fake_llm_endpoint.py. The URL comes from
        # GPTSCAN_BASE_URL because a local endpoint has no fixed address.
        # Prices are zero: nothing is billed, and a cost estimate that invented
        # a figure here would poison the measurements.
        "base_url": None,
        "api_key_env": "GPTSCAN_API_KEY",
        "models": {"cheap": "custom-cheap", "strong": "custom-strong"},
        "prices": {
            "custom-cheap":  {"in": 0.0, "out": 0.0},
            "custom-strong": {"in": 0.0, "out": 0.0},
        },
    },
```

- [ ] **Schritt 4: Den Endpunkt-Override einsetzen**

In `GPTScan/src/llm_backend.py` bei den anderen `ENV_`-Konstanten (Zeile 29-31):

```python
ENV_BASE_URL = "GPTSCAN_BASE_URL"
```

und `base_url()` (Zeile 90-96) ersetzen durch:

```python
def base_url() -> Optional[str]:
    """Chat-Completions endpoint of the active provider.

    None for OpenAI itself, whose endpoint is the SDK default --- see
    :func:`configure_sdk`, which leaves ``api_base`` untouched in that case.

    The "custom" provider has no fixed address and reads GPTSCAN_BASE_URL
    instead. The override is deliberately confined to that provider: it must be
    impossible to redirect a real, paid backend by setting a variable.
    """
    config = provider_config()
    if active_provider() == "custom":
        return os.environ.get(ENV_BASE_URL) or config.get("base_url")
    return config.get("base_url")
```

- [ ] **Schritt 5: Tests laufen lassen, Erfolg bestätigen**

Ausführen: `python -m pytest tests/test_gptscan_deadline.py -q`
Erwartet: 9 passed

- [ ] **Schritt 6: Commit**

```bash
git add GPTScan/src/config.py GPTScan/src/llm_backend.py tests/test_gptscan_deadline.py
git commit -m "AP5: GPTScan kann auf einen frei waehlbaren Endpunkt zeigen"
```

---

### Aufgabe 7: LLMSmartAudit — Zwischenstand nach jeder Phase

**Einordnung:** Heikel. Der Kern der Teilergebnis-Rettung; der Eingriff sitzt im
Sammler, den alle 41 Detektoren durchlaufen.

**Dateien:**
- Ändern: `LLMSmartAuditTool-main/LLMSmartAuditTool-main/chatdev/audit_report.py`
- Test: `tests/test_audit_report_partial.py` *(neu)*

**Schnittstellen:**
- Liefert: `record()` schreibt zusätzlich einen vollständigen Report an den Pfad
  aus `SB_PARTIAL_REPORT`, sofern gesetzt. Aufgabe 8 birgt diese Datei.

**Hintergrund für die ausführende Person.** `audit_report.py` ist **eigener Code**
(`docs/BA-EIGENANTEIL.md:219`), keine fremde Datei. `chatdev/phase.py:405` ruft
`record()` nach jeder Phase auf; `chatdev/chat_chain.py:344` schreibt den Report
erst am Ende. Genau diese Lücke wird hier geschlossen — und zwar **ohne** dass
`phase.py` oder `chat_chain.py` angefasst werden: die Konfiguration kommt aus der
Umgebung, die der Entrypoint setzt. Der Kontext (Contract-Name, Provider, Modell)
steht in `record()` nicht zur Verfügung und wird deshalb ebenfalls aus der
Umgebung gelesen, mit denselben Variablen, die der Entrypoint ohnehin kennt.

- [ ] **Schritt 1: Den fehlschlagenden Test schreiben**

`tests/test_audit_report_partial.py`:

```python
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
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_audit_report_partial.py -q`
Erwartet: FAIL — `test_flush_after_every_phase` findet die Datei nicht

- [ ] **Schritt 3: Den Flush einbauen**

In `chatdev/audit_report.py` bei den Modul-Konstanten (hinter `SUMMARY_PHASES`):

```python
# Where to drop a running snapshot of the report, and the context it needs.
# Set by the SmartBugs entrypoint; unset outside SmartBugs, where the tool keeps
# its original behaviour of writing only once, at the end.
ENV_PARTIAL = "SB_PARTIAL_REPORT"
ENV_CONTRACT = "SB_CONTRACT_NAME"
```

In `AuditReportCollector` eine neue Methode ergänzen:

```python
    def flush_partial(self):
        """Write a snapshot of everything collected so far, if configured.

        Called after every detector phase. The tool aggregates in memory and
        writes only once at the very end, so without this a run stopped by a
        timeout loses every detector it had already finished --- see
        docs/BA-AP5-TIMEOUT-DESIGN.md, 4.4.

        The context (contract, provider, model) is read from the environment
        because record() has none: it sees a phase name and a conclusion, and
        nothing else. The entrypoint knows all three and exports them.

        Failure is swallowed on purpose. This runs inside a paid analysis; an
        unwritable snapshot path must cost the snapshot, never the run.
        """
        out_path = os.environ.get(ENV_PARTIAL)
        if not out_path:
            return None
        try:
            return self.write_json(
                out_path=out_path,
                contract_name=os.environ.get(ENV_CONTRACT, "unknown"),
                provider=os.environ.get("LLM_PROVIDER", "unknown"),
                model=os.environ.get("LLM_MODEL_ID")
                      or os.environ.get("LLM_MODEL", "unknown"),
                timestamp="partial",
            )
        except Exception as e:  # noqa: BLE001 - see docstring
            print(f"audit_report: partial snapshot failed: {e}")
            return None
```

Und in `record()` als **letzte** Anweisung des `if phase_name in DETECTORS`-Zweigs
(nach dem `self._findings.append(...)`-Block, aber noch innerhalb des Zweigs, auf
der Einrückungsebene von `self._checked.append(phase_name)`):

```python
            # A detector finished: put the new state on disk before the next one
            # starts, so a hard stop costs at most the detector in flight.
            self.flush_partial()
```

`write_json` ruft `os.makedirs(os.path.dirname(out_path), exist_ok=True)` — bei
einem Pfad ohne Verzeichnisanteil wirft das; der `try`-Block fängt es ab.

- [ ] **Schritt 4: Tests laufen lassen, Erfolg bestätigen**

Ausführen: `python -m pytest tests/test_audit_report_partial.py -q`
Erwartet: 5 passed

- [ ] **Schritt 5: Prüfen, dass der Endbericht unverändert bleibt**

Ausführen: `python -m pytest tests/test_llmsmartaudit_parser.py -q`
Erwartet: alle grün — die aufgezeichneten Läufe müssen sich unverändert lesen.

- [ ] **Schritt 6: Commit**

```bash
git add LLMSmartAuditTool-main/LLMSmartAuditTool-main/chatdev/audit_report.py tests/test_audit_report_partial.py
git commit -m "AP5: LLMSmartAudit haelt nach jeder Detektor-Phase einen Zwischenstand"
```

---

### Aufgabe 8: LLMSmartAudit — Entrypoint mit Bergung

**Einordnung:** Spiegelt Aufgabe 4; das Muster liegt vor.

**Dateien:**
- Ändern: `smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh`
- Erstellen: `smartbugs/tools/llmsmartaudit/scripts/mark_timeout.py`

**Schnittstellen:**
- Verbraucht: das Marken-Rechenwerk aus Aufgabe 4 (wörtlich zu übernehmen),
  `SB_PARTIAL_REPORT` aus Aufgabe 7.

- [ ] **Schritt 1: Den Stempel-Helfer kopieren**

```bash
cp smartbugs/tools/gptscan/scripts/mark_timeout.py \
   smartbugs/tools/llmsmartaudit/scripts/mark_timeout.py
```

Die Datei ist bewusst identisch. Beide Werkzeugverzeichnisse werden getrennt in
ihren jeweiligen Container kopiert (`bin: scripts`); ein geteilter Ort existiert
nicht. Dasselbe gilt upstream für `printContractNames.py`.

- [ ] **Schritt 2: Das Marken-Rechenwerk einsetzen**

In `smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh`, nach dem MAIN-Block
(hinter Zeile 31), den Block aus Aufgabe 4 Schritt 3 **wörtlich** einfügen —
inklusive der Kommentare. Ein Test in Aufgabe 10 hält beide Fassungen
deckungsgleich.

Direkt darunter, zusätzlich zu Aufgabe 4, die Konfiguration des Zwischenstands:

```sh
# Where audit_report.record() drops its running snapshot after every detector
# phase (AP5). Only set when a timeout is in play: without one the tool keeps
# its original behaviour of writing exactly once, at the end.
if [ "${TIMEOUT:-0}" -gt 0 ]; then
    SB_PARTIAL_REPORT="${TMPDIR:-/tmp}/sb_partial.json"
    export SB_PARTIAL_REPORT
fi
```

**Wichtig:** `SB_CONTRACT_NAME` muss ebenfalls exportiert werden, aber `$NAME`
wird erst weiter unten berechnet (Zeile 44-45). Deshalb der Export **dort**,
unmittelbar hinter der `NAME=`-Zuweisung:

```sh
# The snapshot writer (chatdev/audit_report.py) reads its context from the
# environment, because record() sees nothing but a phase name and a conclusion.
SB_CONTRACT_NAME="$NAME"
export SB_CONTRACT_NAME
# Make the resolved provider explicit. The script reads LLM_PROVIDER with a
# default of "deepseek" but never exports it, so a host that left it unset
# would give the snapshot provider="unknown" while the final report says
# "deepseek" --- the same run described two ways.
export LLM_PROVIDER="$PROVIDER"
```

- [ ] **Schritt 3: Den Werkzeugaufruf unter das Netz stellen**

Die Zeilen 60-62 (`python3 run.py --config SmartContractTA ...`) ersetzen durch:

```sh
if [ "$NET" -gt 0 ]; then
    timeout -s TERM "$NET" python3 run.py --config SmartContractTA --org "$ORG" \
        --name "$NAME" --provider "$PROVIDER" $MODEL_OPT --task-file "$SOURCE"
else
    python3 run.py --config SmartContractTA --org "$ORG" --name "$NAME" \
        --provider "$PROVIDER" $MODEL_OPT --task-file "$SOURCE"
fi
RC=$?

# See the note in the GPTScan entrypoint: 124/137/143 all mean "stopped on
# purpose", and only 124 lands in SmartBugs' *errors* rather than *fails*.
TIMED_OUT=0
if [ "$NET" -gt 0 ]; then
    case "$RC" in
        124|137|143) TIMED_OUT=1; RC=124 ;;
    esac
fi
```

- [ ] **Schritt 4: Die Bergung einbauen**

Den Block, der den Report sucht (Zeilen 65-75), so erweitern, dass bei einem
Timeout der Zwischenstand einspringt. Die neue Reihenfolge:

```sh
# Copy the machine-readable report to the fixed location SmartBugs retrieves.
REPORT=$(ls -t WareHouse/"${NAME}_${ORG}_"*/"${NAME}_audit_report.json" 2>/dev/null | head -1)
if [ -n "$REPORT" ] && [ -f "$REPORT" ]; then
    cp "$REPORT" /output.json
elif [ "$TIMED_OUT" = "1" ] && [ -f "${SB_PARTIAL_REPORT:-/nonexistent}" ]; then
    # The tool was stopped before it could write its final report, but every
    # finished detector left a complete snapshot behind. That snapshot IS the
    # result: only the detector in flight is lost (AP5).
    cp "$SB_PARTIAL_REPORT" /output.json
    echo "LLMSmartAudit: salvaged the partial report after the timeout"
else
    # Guarantee a well-formed (empty-findings) report so SmartBugs can always
    # retrieve /output.json; force a non-zero exit so the failure is visible.
    printf '%s' "{\"tool\":\"LLMSmartAudit\",\"config\":\"SmartContractTA\",\"contract\":\"$NAME\",\"provider\":\"$PROVIDER\",\"model\":\"$MODEL\",\"categories_total\":41,\"categories_checked\":0,\"checked\":[],\"summary\":\"\",\"findings\":[],\"error\":\"no report produced\"}" > /output.json
    if [ "$RC" -eq 0 ]; then
        RC=1
    fi
fi

if [ "$TIMED_OUT" = "1" ]; then
    python3 "$BIN/mark_timeout.py" /output.json net \
        "LLMSmartAudit nach ${NET}s hart beendet; Zwischenstand geborgen" \
        || echo "LLMSmartAudit: could not stamp the timeout marker"
fi
```

- [ ] **Schritt 5: Syntaxprüfung**

Ausführen: `sh -n smartbugs/tools/llmsmartaudit/scripts/do_solidity.sh`
Erwartet: keine Ausgabe

- [ ] **Schritt 6: Commit**

```bash
git add smartbugs/tools/llmsmartaudit/scripts/
git commit -m "AP5: LLMSmartAudit-Entrypoint birgt den Zwischenstand nach Timeout"
```

---

### Aufgabe 9: LLMSmartAudit — Parser meldet den Timeout

**Einordnung:** Zwilling von Aufgabe 5.

**Dateien:**
- Ändern: `smartbugs/tools/llmsmartaudit/parser.py`
- Test: `tests/test_llmsmartaudit_parser.py` (ergänzen)

- [ ] **Schritt 1: Die fehlschlagenden Tests schreiben**

An `tests/test_llmsmartaudit_parser.py` anfügen:

```python
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
```

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_llmsmartaudit_parser.py -q -k timeout`
Erwartet: 1 FAILED, 1 passed

- [ ] **Schritt 3: Den Parser-Zweig schreiben**

In `smartbugs/tools/llmsmartaudit/parser.py`, in `parse()` hinter dem Block, der
`categories_checked` auswertet (hinter `if result.get("error"): ...`):

```python
    # Timeout marker (AP5): stamped by the entrypoint when the run was cut
    # short. It goes into *errors*, never into *fails* -- the run was stopped on
    # purpose and produced a usable, if incomplete, result. The coverage figure
    # above already says how incomplete.
    sb_timeout = result.get("sb_timeout")
    if isinstance(sb_timeout, dict) and sb_timeout.get("hit"):
        stage = sb_timeout.get("stage", "unknown")
        detail = sb_timeout.get("detail") or ""
        errors.add(f"TIMEOUT_{stage.upper()}: run cut short after"
                   f" {checked} of {total} detector categories"
                   + (f" -- {detail}" if detail else ""))
```

- [ ] **Schritt 4: Tests laufen lassen, Erfolg bestätigen**

Ausführen: `python -m pytest tests/test_llmsmartaudit_parser.py -q`
Erwartet: alle grün

- [ ] **Schritt 5: Commit**

```bash
git add smartbugs/tools/llmsmartaudit/parser.py tests/test_llmsmartaudit_parser.py
git commit -m "AP5: LLMSmartAudit-Parser meldet den Timeout als error"
```

---

### Aufgabe 10: Entrypoint-Tests für beide Werkzeuge

**Einordnung:** Das Muster liegt in `tests/test_entrypoint_main.py` vor.

**Dateien:**
- Erstellen: `tests/test_entrypoint_timeout.py`

**Hintergrund.** `tests/test_entrypoint_main.py` führt die echten Skripte mit `sh`
aus und stellt `python3` und die Dateiwerkzeuge als aufzeichnende Stubs auf den
PATH. Dasselbe Verfahren gilt hier. Die Skripte laufen außerhalb ihres Containers
nie zu Ende (sie wechseln in ein Image-spezifisches Verzeichnis und brechen mit 1
ab) — das ist beabsichtigt: der Timeout-Block steht davor, also ist alles
Geprüfte bereits geschehen, und es wird nie ein Werkzeug auf dem Host gestartet.

- [ ] **Schritt 1: Die fehlschlagenden Tests schreiben**

`tests/test_entrypoint_timeout.py`:

```python
"""Regression tests for the timeout wiring in both do_solidity.sh entrypoints.

Same approach as test_entrypoint_main.py: the real scripts run under sh with
recording stubs on PATH. Three things are checked, for both tools:

* TIMEOUT=0 --- nothing is computed, nothing is exported. Every result recorded
  so far was produced this way, so this is the test that keeps the earlier runs
  comparable;
* TIMEOUT>0 --- brake at 70 %, net at 90 %, and SB_DEADLINE_EPOCH exported as an
  absolute instant;
* both scripts compute the marks identically. The arithmetic is deliberately
  duplicated (as mythril and honeybadger do upstream), so something has to hold
  the two copies together.
"""

import os
import re
import shutil
import subprocess

import pytest

from conftest import tool_script

pytestmark = pytest.mark.skipif(
    shutil.which("sh") is None, reason="needs a POSIX shell"
)

TOOLS = ("gptscan", "llmsmartaudit")


def run_entrypoint(tmp_path, tool, timeout):
    """Run the entrypoint far enough to see the timeout block, return its log."""
    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    for helper in ("main_contract.py", "do_solidity.sh", "mark_timeout.py"):
        shutil.copyfile(tool_script(tool, helper), bindir / helper)

    source = tmp_path / "Visor.sol"
    source.write_text("contract Visor { }\n", encoding="utf-8")

    # Stub out everything the script would otherwise really invoke. 'timeout'
    # just succeeds: the command it would wrap is python3, itself a stub, and
    # these tests assert on the computed marks, not on the tool run.
    for name, body in (("python3", 'exit 0\n'),
                       ("timeout", 'exit 0\n'),
                       ("solc", 'exit 0\n')):
        path = bindir / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
        os.chmod(path, 0o755)

    env = dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")
    proc = subprocess.run(
        ["sh", str(bindir / "do_solidity.sh"), str(source), str(timeout),
         str(bindir), "0"],
        capture_output=True, text=True, env=env, cwd=str(tmp_path))
    return proc.stdout + proc.stderr


def marks(log):
    """Pull 'SB_TIMEOUT_BUDGET timeout=Ns brake=Ns net=Ns' out of the log."""
    m = re.search(r"SB_TIMEOUT_BUDGET timeout=(\d+)s brake=(\d+)s net=(\d+)s", log)
    return None if m is None else tuple(int(g) for g in m.groups())


@pytest.mark.parametrize("tool", TOOLS)
def test_timeout_zero_computes_nothing(tmp_path, tool):
    """No --timeout: the entrypoint must behave exactly as it did before AP5."""
    assert marks(run_entrypoint(tmp_path, tool, 0)) is None


@pytest.mark.parametrize("tool", TOOLS)
def test_marks_are_seventy_and_ninety_percent(tmp_path, tool):
    assert marks(run_entrypoint(tmp_path, tool, 1000)) == (1000, 700, 900)


@pytest.mark.parametrize("tool", TOOLS)
def test_marks_never_fall_below_one_second(tmp_path, tool):
    """A tiny timeout must not produce a mark of 0, which would disable it."""
    assert marks(run_entrypoint(tmp_path, tool, 1)) == (1, 1, 1)


def test_both_entrypoints_compute_the_same_marks(tmp_path):
    """The arithmetic is duplicated on purpose; this keeps the copies equal."""
    a = marks(run_entrypoint(tmp_path / "a", "gptscan", 3600))
    b = marks(run_entrypoint(tmp_path / "b", "llmsmartaudit", 3600))
    assert a == b == (3600, 2520, 3240)
```

Der letzte Test übergibt `tmp_path / "a"` und `tmp_path / "b"`, die es noch nicht
gibt — deshalb legt `run_entrypoint` sein `bin`-Verzeichnis mit `parents=True` an.

- [ ] **Schritt 2: Tests laufen lassen, Fehlschlag bestätigen**

Ausführen: `python -m pytest tests/test_entrypoint_timeout.py -q`
Erwartet: FAIL, solange die Aufgaben 4 und 8 nicht zusammengeführt sind

- [ ] **Schritt 3: Abweichungen beheben**

Schlägt ein Test fehl, liegt der Fehler in Aufgabe 4 oder 8 — **nicht** im Test.
Die Marken sind in den globalen Randbedingungen festgeschrieben.

- [ ] **Schritt 4: Die gesamte Testsuite laufen lassen**

Ausführen: `python -m pytest tests/ -q`
Erwartet: alle grün, die bisherigen 78 eingeschlossen

- [ ] **Schritt 5: Commit**

```bash
git add tests/test_entrypoint_timeout.py
git commit -m "AP5: Entrypoint-Tests fuer die Timeout-Marken beider Werkzeuge"
```

---

### Aufgabe 11: Auswertung sieht den Teillauf

**Einordnung:** Klar umrissene Ergänzung an zwei Auswertungsskripten.

**Dateien:**
- Ändern: `analysis_tools/gptscan_eval.py`
- Ändern: `analysis_tools/errors_fails_report.py`

**Warum das dazugehört.** Ohne diesen Schritt zählen Findings aus einem
abgebrochenen Lauf wie Findings aus einem Volllauf. Der Recall sinkt dann still,
und im Ergebnis steht nicht, warum. Das ist genau der Messfehler, den AP5
vermeiden soll.

- [ ] **Schritt 1: Den Marker in den Task-Datensatz aufnehmen**

`sb_timeout` steht **nicht** in `result.json` — dort liegt die geparste Ausgabe,
nicht der Rohbericht. Der Marker erreicht die Auswertung als der `errors`-Eintrag,
den die Aufgaben 5 und 9 erzeugen. Genau so behandelt die Datei bereits den
`degraded`-Fall, der aus `infos` gelesen wird (`gptscan_eval.py:286`).

In `analysis_tools/gptscan_eval.py`, im Wörterbuch, das `read_run()` je Task
anlegt (Zeile 270-288), hinter `"degraded"` ergänzen:

```python
            # Timeout marker (AP5). Read out of errors for the same reason
            # "degraded" is read out of infos: the parser has already
            # normalised it, and result.json carries no raw report.
            "timeout_hit": any(str(e).startswith("TIMEOUT_")
                               for e in (res.get("errors") or [])),
            "timeout_stage": next(
                (str(e).split(":", 1)[0][len("TIMEOUT_"):].lower()
                 for e in (res.get("errors") or [])
                 if str(e).startswith("TIMEOUT_")), ""),
```

Und oben bei den Konstanten, neben `DEGRADED_MARK`:

```python
# Prefix the tool parsers put on a timeout entry in `errors` (AP5).
TIMEOUT_MARK = "TIMEOUT_"
```

Die beiden Ausdrücke oben dann über `TIMEOUT_MARK` führen statt über das Literal.

- [ ] **Schritt 2: Die Spalten in die CSV aufnehmen**

In `finding_rows()` (Zeile 292) die beiden Werte aus dem Task-Datensatz in jede
Zeile übernehmen, mit denselben Namen `timeout_hit` und `timeout_stage`. Die
vorhandene Spaltenreihenfolge beibehalten und die neuen ans Ende hängen — eine
umsortierte CSV bricht den Vergleich mit den bereits abgelegten Auswertungen
unter `eval/`.

- [ ] **Schritt 3: Die Zusammenfassung trennen**

In `write_summary()` (Zeile 400) eine Zeile „davon Teilläufe (Timeout): N"
ergänzen, und dasselbe in `analysis_tools/errors_fails_report.py`, das seine
Tasks nach demselben Muster einliest. Teilläufe bleiben in der Gesamtzahl
enthalten — sie herauszurechnen wäre derselbe Messfehler mit umgekehrtem
Vorzeichen.

- [ ] **Schritt 4: Gegen ein vorhandenes Ergebnisverzeichnis laufen lassen**

```bash
python analysis_tools/gptscan_eval.py --help
```
und danach über eines der vorhandenen `eval/`-Verzeichnisse. Erwartet: unverändert
dieselben Zahlen wie bisher, zusätzlich die beiden neuen Spalten mit `False` bzw.
leer — die aufgezeichneten Läufe kennen keinen Timeout.

- [ ] **Schritt 5: Commit**

```bash
git add analysis_tools/gptscan_eval.py analysis_tools/errors_fails_report.py
git commit -m "AP5: Auswertung weist Teillaeufe getrennt aus"
```

---

### Aufgabe 12: Dokumentation nachziehen

**Einordnung:** Textarbeit gegen einen fertigen Befund.

**Dateien:**
- Ändern: `docs/BA-BETREUERGESPRAECH-AUFGABEN.md`
- Ändern: `docs/BA-EIGENANTEIL.md`
- Ändern: `docs/BA-BETRIEB.md`, `docs/BA-WERKZEUG-BEDIENUNG.md`
- Erstellen oder ändern: AP7-Material

- [ ] **Schritt 1: AP5 als erledigt ausweisen**

In `docs/BA-BETREUERGESPRAECH-AUFGABEN.md`: die Statusspalte in der Tabelle
(Zeile 22) auf **erledigt**, und im AP5-Abschnitt einen Absatz „Stand: erledigt"
nach dem Vorbild von AP1 — was umgesetzt wurde, was bewusst nicht.

Offene Rückfrage 3 (Zeile 42-44) beantworten: *Teilergebnis*, mit der Begründung,
dass der Mechanismus in beiden Fällen in eigenem Code lag und der Betreuer die
schwächere Variante damit ohnehin eingeschlossen bekommt.

- [ ] **Schritt 2: Den Eigenanteil nachführen**

In `docs/BA-EIGENANTEIL.md` je geänderter Datei Zeile und Begründung ergänzen.
Die Zahlen im Kopf des Dokuments (7 GPTScan, 9 LLMSmartAudit, 5 SmartBugs)
prüfen: **sie dürfen sich nicht geändert haben**, weil AP5 keine neue Fremddatei
anfasst. Hat sich eine Zahl geändert, ist etwas schiefgegangen — melden.

- [ ] **Schritt 3: Die Bedienung dokumentieren**

In `docs/BA-BETRIEB.md` und `docs/BA-WERKZEUG-BEDIENUNG.md`: was `--timeout` jetzt
bewirkt, die drei Marken, was ein Teilergebnis im Ergebnis erkennbar macht
(`sb_timeout`, `categories_checked`) und wie der Prüfstand aus
`testing_tools/fake_llm_endpoint.py` gestartet wird.

- [ ] **Schritt 4: AP7 füttern**

Zwei belegte Punkte für das Meta-Findings-Dokument:

1. *Kein Werkzeug bringt einen Timeout für den Lauf mit* — Beleg: die
   Optionslisten beider Werkzeuge (Spec 2.1). GPTScans Frist gilt je LLM-Aufruf,
   nicht für den Lauf.
2. *Ob sich ein Teilergebnis retten lässt, hängt daran, ob ein Werkzeug
   inkrementell festhält oder erst am Schluss zusammenführt* — Beleg: der
   unterschiedliche Weg, den beide Werkzeuge hier nehmen mussten (Spec 4.5).

- [ ] **Schritt 5: Commit**

```bash
git add docs/
git commit -m "AP5: Dokumentation zum Timeout-Durchreichen nachgezogen"
```

---

### Aufgabe 13: Scharfer Lauf und Protokoll

**Einordnung:** Hier fließt Geld, und das Ergebnis will beurteilt werden.

**Dateien:**
- Ändern: `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`

**Vorbedingung:** Aufgaben 0 bis 12 abgeschlossen, Testsuite grün, beide
Docker-Images neu gebaut.

- [ ] **Schritt 1: Images neu bauen**

```bash
docker build -t smartbugs/gptscan:1.0 ./GPTScan
docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 \
  ./LLMSmartAuditTool-main/LLMSmartAuditTool-main
```

- [ ] **Schritt 2: Kostenloser Durchgang gegen den Prüfstand**

```bash
python -m testing_tools.fake_llm_endpoint --port 8099 --delay 30
```
in einem eigenen Fenster starten, dann je Werkzeug einen Contract mit knappem
Timeout fahren (`--timeout 60`), `GPTSCAN_PROVIDER=custom` bzw.
`LLM_PROVIDER=custom` und die Basis-URL auf `http://host.docker.internal:8099`.

Erwartet: `result.json` trägt `sb_timeout`, `errors` enthält `TIMEOUT_…`, `fails`
ist leer. **Das ist das eigentliche Abnahmekriterium** — es kostet nichts und ist
beliebig oft wiederholbar.

- [ ] **Schritt 3: Scharfer Lauf**

2–3 Contracts je Werkzeug gegen den echten Endpunkt, mit einem Timeout, der
sicher zuschlägt (LLMSmartAudit: deutlich unter den ~76 s, die ein Contract im
Mittel braucht). `LLM_MODEL=deepseek-v4-flash` ist Pflicht.

- [ ] **Schritt 4: Nachweisen, dass das Teilergebnis wirklich Substanz hat**

Für LLMSmartAudit prüfen: `categories_checked` liegt zwischen 1 und 40, und die
`findings` des Teillaufs sind eine Teilmenge dessen, was ein Volllauf desselben
Contracts gemeldet hat. Ein Teilergebnis, das Findings **erfindet**, wäre
schlimmer als gar keines.

- [ ] **Schritt 5: Den Preis des Zwischenstands beziffern**

Einen Contract **ohne** Timeout durch LLMSmartAudit schicken und die Laufzeit
gegen den bekannten Bezugswert halten (3:02 h über 143 Contracts, also rund 76 s
je Contract). 41 zusätzliche Schreibvorgänge dürfen darin nicht messbar sein;
zeigt sich doch ein Aufschlag von mehr als ein paar Prozent, gehört das benannt —
und der Flush wäre auf „nur wenn `SB_PARTIAL_REPORT` gesetzt ist" einzuschränken,
was Aufgabe 7 ohnehin bereits tut.

- [ ] **Schritt 6: Ins Protokoll schreiben**

In `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`: Datum, Kommandos, Timeout-Werte,
`categories_checked`, Laufzeit, Kosten, die Gegenüberstellung aus Schritt 4 und
die Laufzeitmessung aus Schritt 5.

- [ ] **Schritt 7: Commit**

```bash
git add docs/BA-DURCHFUEHRUNGSPROTOKOLL.md
git commit -m "AP5: Nachweis des Timeout-Verhaltens im Durchfuehrungsprotokoll"
```

---

## Abnahme

AP5 gilt als erledigt, wenn alles davon zutrifft:

- [ ] `python -m pytest tests/ -q` ist grün, inklusive der 78 bisherigen Tests
- [ ] Ein Lauf **ohne** `--timeout` erzeugt dasselbe Ergebnis wie vor AP5
- [ ] Ein Lauf mit knappem `--timeout` liefert je Werkzeug ein Ergebnis mit
      `sb_timeout` in `result.json` und `TIMEOUT_…` in `errors`, **nicht** in `fails`
- [ ] LLMSmartAudit liefert dabei ein Teilergebnis mit `1 ≤ categories_checked ≤ 40`,
      dessen Findings eine Teilmenge des Volllaufs sind
- [ ] Die Zahlen geänderter Fremddateien in `docs/BA-EIGENANTEIL.md` sind
      unverändert (7 / 9 / 5)
- [ ] `docs/BA-BETREUERGESPRAECH-AUFGABEN.md` weist AP5 als erledigt aus und
      beantwortet die offene Rückfrage 3
