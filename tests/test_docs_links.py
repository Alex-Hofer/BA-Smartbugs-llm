"""Relative Markdown-Links in der eigenen Dokumentation muessen auf vorhandene
Dateien zeigen.

Geprueft werden alle getrackten ``.md``-Dateien ausserhalb der drei Fremdbaeume
(``smartbugs/``, ``GPTScan/``, ``LLMSmartAuditTool-main/``) sowie die eigene
Integrationsdokumentation ``GPTScan/docs/SMARTBUGS_INTEGRATION.md`` und
``smartbugs/tools/llmsmartaudit/mapping.md``. Externe
Links (``http``, ``https``, ``mailto``) und reine Anker werden nicht geprueft;
ein Anker hinter einem Dateinamen wird abgeschnitten, die Datei selbst muss
existieren.
"""

import os
import re
import subprocess

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FOREIGN = ("smartbugs/", "GPTScan/", "LLMSmartAuditTool-main/")
KEEP = ("GPTScan/docs/SMARTBUGS_INTEGRATION.md",
        "smartbugs/tools/llmsmartaudit/mapping.md")


def tracked_markdown():
    try:
        out = subprocess.run(["git", "ls-files", "*.md"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git nicht verfuegbar; die Dateiliste kommt aus git ls-files")
    return [f for f in out.split() if not f.startswith(FOREIGN) or f in KEEP]


def dead_links(relpath):
    path = os.path.join(REPO_ROOT, relpath)
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    dead = []
    for m in LINK.finditer(text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = target.split("#")[0]
        if not target:
            continue
        candidate = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not os.path.exists(candidate):
            dead.append((text[:m.start()].count("\n") + 1, m.group(1)))
    return dead


def test_the_documentation_set_is_found():
    files = tracked_markdown()
    assert "README.md" in files
    assert "docs/BA-WERKZEUGE-IM-VERGLEICH.md" in files
    assert len(files) >= 40


def test_relative_links_in_the_documentation_resolve():
    broken = {}
    for relpath in tracked_markdown():
        dead = dead_links(relpath)
        if dead:
            broken[relpath] = dead
    assert not broken, "tote relative Links (Datei: [(Zeile, Ziel)]): %r" % broken
