"""Dateien, die in zwei Werkzeugverzeichnissen als Kopie liegen, muessen gleich bleiben.

Zwei Faelle:

* ``scripts/mark_timeout.py`` liegt fuer GPTScan und LLMSmartAudit je einmal vor,
  weil SmartBugs einem Werkzeug nur sein eigenes Verzeichnis in den Container
  reicht. Fuer ``main_contract.py`` prueft ``tests/test_main_contract.py`` die
  Identitaet schon; hier dasselbe fuer den Timeout-Stempel.
* ``smartbugs/tools/slither-0.11.3-glibc/`` ist laut ``config.yaml`` und
  ``docs/BA-EIGENANTEIL.md`` eine Kopie des Upstream-Werkzeugs mit anderem
  Image; ``parser.py`` und ``findings.yaml`` sollen unveraendert aus
  ``smartbugs/tools/slither-0.11.3/`` stammen. Weichen sie ab, stimmt die
  Eigenanteilsaufstellung nicht mehr.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO_ROOT, "smartbugs", "tools")


def _read(*parts):
    with open(os.path.join(TOOLS, *parts), "rb") as fh:
        return fh.read()


def test_mark_timeout_copies_are_identical():
    assert _read("gptscan", "scripts", "mark_timeout.py") == \
        _read("llmsmartaudit", "scripts", "mark_timeout.py")


def test_slither_glibc_parser_is_the_upstream_parser():
    assert _read("slither-0.11.3-glibc", "parser.py") == _read("slither-0.11.3", "parser.py")


def test_slither_glibc_findings_are_the_upstream_findings():
    assert _read("slither-0.11.3-glibc", "findings.yaml") == \
        _read("slither-0.11.3", "findings.yaml")


def test_slither_glibc_config_names_its_own_image():
    """Das eigene Verzeichnis muss auf das glibc-Image zeigen, nicht auf das Upstream-Image."""
    cfg = _read("slither-0.11.3-glibc", "config.yaml").decode("utf-8")
    assert "smartbugs/slither:0.11.3-glibc" in cfg
