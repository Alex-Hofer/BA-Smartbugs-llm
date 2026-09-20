"""Regressionstests fuer die Deckungspruefung in analysis_tools/parser_audit.py.

Das Audit sucht je Rohsignal einen Schluessel im Parser-Output. An zwei Stellen
wird dieselbe Tatsache aber in fremden Worten gemeldet:

* **Exit-Code 127.** ``sb/parse_utils.py`` uebersetzt ihn in den Satz
  „SmartBugs was invoked with option 'main', but the filename did not match any
  contract" und schreibt gerade *keinen* ``EXIT_CODE_127``-Marker.
* **Fehlende Ausgabe.** Beide Tool-Parser benennen den Grund
  (``no tar archive collected from the container`` und zwei Geschwister)
  statt das Wort ``output`` zu verwenden.

Auf den aufgezeichneten Laeufen ergab das 12 gemeldete Luecken, hinter denen
kein einziges verlorenes Signal stand -- die drei Exit-127-Contracts aus
``gptscan_mwefixed_v2_dry`` und ``_main``, je zweimal gezaehlt. Diese Tests
halten die Gleichsetzung fest **und** ihre Grenze: Sie gilt nur fuer die
Wortlaute, die im Code tatsaechlich vorkommen. Wird dort umformuliert, meldet
das Audit wieder eine Luecke, statt sie stillschweigend zu schlucken.

Alle Faelle sind ``synthetic``: sie bauen ihre Ein- und Ausgabe von Hand, damit
der Test nicht von ``smartbugs/results/`` abhaengt (git-ignoriert).
"""

import importlib.util
import os

import pytest

import conftest  # noqa: F401  -- legt REPO_ROOT und smartbugs/ auf sys.path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    path = os.path.join(REPO_ROOT, "analysis_tools", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pa = load("parser_audit")


def out(errors=(), fails=(), infos=()):
    return {"errors": list(errors), "fails": list(fails), "infos": list(infos)}


# --------------------------------------------------------------------------- #
# Der Normalfall bleibt, wie er war
# --------------------------------------------------------------------------- #

def test_a_key_found_verbatim_counts_as_covered_synthetic():
    s = pa.Signal("EXIT_NONZERO", "report", "container exited with code 1",
                  key="EXIT_CODE_1")
    assert pa.covered(s, out(errors=["EXIT_CODE_1"])) is True


def test_a_key_that_appears_nowhere_is_a_gap_synthetic():
    s = pa.Signal("LOG_ERROR", "report", "etwas ging schief", key="etwas ging schief")
    assert pa.covered(s, out(errors=["voellig anderer Text"])) is False


def test_without_parser_output_nothing_is_covered_synthetic():
    s = pa.Signal("EXIT_NONZERO", "report", "container exited with code 1",
                  key="EXIT_CODE_1")
    assert pa.covered(s, None) is False


def test_line_breaks_in_the_parser_output_do_not_create_a_gap_synthetic():
    """Der Abgleich laeuft ueber `squash`, ist also gegen Umbrueche immun."""
    s = pa.Signal("LOG_ERROR", "report", "Static analysis failed: Invalid args")
    assert pa.covered(s, out(errors=["Static analysis\n   failed: Invalid args"])) is True


# --------------------------------------------------------------------------- #
# Die beiden zugelassenen Ersatzwortlaute
# --------------------------------------------------------------------------- #

def test_exit_127_is_covered_by_smartbugs_own_sentence_synthetic():
    """SmartBugs schreibt nie 'EXIT_CODE_127' -- siehe sb/parse_utils.py:75-78."""
    s = pa.Signal("EXIT_NONZERO", "report", "container exited with code 127",
                  key="EXIT_CODE_127")
    fails = ["SmartBugs was invoked with option 'main', "
             "but the filename did not match any contract"]
    assert pa.covered(s, out(fails=fails)) is True


@pytest.mark.parametrize("wording", [
    "no tar archive collected from the container",
    "tar archive from the container is unreadable: unexpected end of data",
    "tar archive contains no output.json",
])
def test_a_missing_output_is_covered_by_the_reason_the_parser_names_synthetic(wording):
    s = pa.Signal("OUTPUT_MISSING", "report", "no usable output.json (tar: missing)",
                  key="output")
    assert pa.covered(s, out(fails=[wording])) is True


def test_the_equivalence_does_not_leak_to_other_exit_codes_synthetic():
    """Nur 127 traegt SmartBugs' Satz; ein anderer Code bleibt eine echte Luecke."""
    s = pa.Signal("EXIT_NONZERO", "report", "container exited with code 3",
                  key="EXIT_CODE_3")
    fails = ["SmartBugs was invoked with option 'main', "
             "but the filename did not match any contract"]
    assert pa.covered(s, out(fails=fails)) is False


def test_an_unrelated_failure_does_not_cover_a_missing_output_synthetic():
    s = pa.Signal("OUTPUT_MISSING", "report", "no usable output.json (tar: missing)",
                  key="output")
    assert pa.covered(s, out(fails=["DOCKER_TIMEOUT"])) is False


# --------------------------------------------------------------------------- #
# Die Tabelle selbst
# --------------------------------------------------------------------------- #

def test_the_accepted_wordings_are_quoted_from_the_code_that_produces_them():
    """Aendert sich dort der Wortlaut, muss diese Tabelle nachziehen."""
    sb = os.path.join(REPO_ROOT, "smartbugs")
    sources = [os.path.join(sb, "sb", "parse_utils.py")]
    for tool in ("gptscan", "llmsmartaudit"):
        sources.append(os.path.join(sb, "tools", tool, "parser.py"))
    haystack = ""
    for path in sources:
        with open(path, encoding="utf-8") as fh:
            haystack += fh.read()

    for alternatives in pa.EQUIVALENT_WORDINGS.values():
        for alt in alternatives:
            assert alt in haystack, (
                "Ersatzwortlaut %r kommt im Quelltext nicht mehr vor - entweder "
                "wurde dort umformuliert oder die Tabelle ist veraltet." % alt)


def test_the_table_stays_small_enough_to_review():
    """Eine wachsende Liste waere kein Abgleich mehr, sondern ein Freibrief."""
    assert set(pa.EQUIVALENT_WORDINGS) == {"EXIT_CODE_127", "output"}
    assert sum(len(v) for v in pa.EQUIVALENT_WORDINGS.values()) <= 4
