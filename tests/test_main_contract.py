"""Regression tests for scripts/main_contract.py (AP6, the MAIN parameter).

SmartBugs hands every entrypoint a MAIN flag: at ``MAIN=1`` a tool is meant to
look at the *main contract* of a file only --- the one the file is named after
--- and not at every library, interface and base contract that a flattened
source drags along. Both LLM entrypoints accepted the flag and ignored it.

Neither GPTScan nor LLMSmartAudit offers a contract selection on its command
line (``GPTScan/src/tasks.py::simple_cli`` takes a source *directory*;
``run.py`` takes a source *file*). The restriction therefore has to happen
before the tool is called, by reducing the source to the main contract and the
definitions it actually needs. That reduction is what this module tests.

The reduction removes byte ranges, it never rewrites them: everything that is
not a discarded top-level definition survives unchanged --- licence header,
pragma, imports, free functions, the text between definitions. This makes the
transformation conservative by construction; the only way it can go wrong is by
discarding a definition that is still referenced, which is what the closure
tests below pin down.
"""

import os
import re
import subprocess
import sys

import pytest

from conftest import load_tool_script, tool_script

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(
    REPO_ROOT, "smartbugs", "samples", "gptscan", "mwevariety_fixed"
)

mc = load_tool_script("gptscan", "main_contract")


def names(source: str) -> list:
    return [d.name for d in mc.top_level_definitions(source)]


# --------------------------------------------------------------------------- #
# Finding the top-level definitions
# --------------------------------------------------------------------------- #

def test_finds_every_top_level_definition_with_its_kind():
    src = """
pragma solidity ^0.8.0;
library L { function f() internal {} }
interface I { function g() external; }
abstract contract A is I { }
contract C is A { }
"""
    defs = mc.top_level_definitions(src)
    assert [(d.kind, d.name) for d in defs] == [
        ("library", "L"),
        ("interface", "I"),
        ("contract", "A"),
        ("contract", "C"),
    ]


def test_definition_range_covers_the_whole_body():
    """Brace matching, not a line heuristic --- bodies contain braces."""
    src = "contract C {\n  function f() public {\n    if (true) { }\n  }\n}\nlibrary L { }\n"
    c = mc.top_level_definitions(src)[0]
    assert src[c.start:c.end].endswith("}")
    assert "library" not in src[c.start:c.end]


def test_the_word_contract_in_a_comment_is_not_a_definition():
    src = """
// contract Ghost is a comment, not a definition
/* library Phantom { } */
contract Real { string s = "contract Fake {"; }
"""
    assert names(src) == ["Real"]


# --------------------------------------------------------------------------- #
# Resolving the main contract from the file name
# --------------------------------------------------------------------------- #

def test_exact_file_stem_wins():
    """SmartBugs' own convention, as used by mythril and honeybadger."""
    assert mc.resolve_main_name("BecToken", ["ERC20", "BecToken"]) == "BecToken"


def test_corpus_numbering_prefix_is_stripped():
    """``10_Visor.sol`` is ``Visor.sol`` of GPTScan project 10.

    ``corpus_tools/mapping.json`` records the provenance of every file in
    mwevariety_fixed as ``<projectNumber>\\<path>\\<original>.sol``; the corpus
    builder prefixed the project number to keep the names unique. The stem
    behind that prefix is the original Solidity file name, which is what the
    "named after its contract" convention refers to. Without this step the
    convention resolves nothing at all: 0 of the 96 files match exactly.
    """
    assert mc.resolve_main_name("10_Visor", ["SafeMath", "Visor"]) == "Visor"


def test_case_differences_in_the_file_name_are_tolerated_when_unambiguous():
    """``yVault.sol`` holds ``contract YVault`` --- an upstream naming slip."""
    assert mc.resolve_main_name("107_yVault", ["ERC20", "YVault"]) == "YVault"


def test_ambiguous_case_insensitive_match_resolves_to_nothing():
    """Two candidates mean the file name does not identify one contract."""
    assert mc.resolve_main_name("107_yvault", ["YVault", "YVAULT"]) is None


def test_unrelated_file_name_resolves_to_nothing():
    assert mc.resolve_main_name("62_Locke", ["Stream", "StreamFactory"]) is None


def test_exact_match_is_preferred_over_the_case_insensitive_one():
    assert mc.resolve_main_name("1_Vault", ["vault", "Vault"]) == "Vault"


# --------------------------------------------------------------------------- #
# Reducing the source
# --------------------------------------------------------------------------- #

BASE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library Unused { function u() internal pure returns (uint) { return 1; } }

interface IThing { function t() external; }

abstract contract Base is IThing { uint internal x; }

library Helper { function h() internal pure returns (uint) { return 2; } }

contract Main is Base {
    function t() external override { x = Helper.h(); }
}
"""


def test_reduction_keeps_the_main_contract():
    out = mc.reduce_source(BASE, "Main")
    assert "contract Main is Base" in out


def test_reduction_keeps_inherited_definitions_transitively():
    """``Main is Base``, ``Base is IThing`` --- both must survive."""
    out = mc.reduce_source(BASE, "Main")
    assert "abstract contract Base" in out
    assert "interface IThing" in out


def test_reduction_keeps_a_library_used_in_a_body():
    out = mc.reduce_source(BASE, "Main")
    assert "library Helper" in out


def test_reduction_drops_what_the_main_contract_never_references():
    out = mc.reduce_source(BASE, "Main")
    assert "Unused" not in out


def test_reduction_keeps_licence_and_pragma():
    """The result still has to be a compilable Solidity file."""
    out = mc.reduce_source(BASE, "Main")
    assert "SPDX-License-Identifier: MIT" in out
    assert "pragma solidity ^0.8.0;" in out


def test_a_name_mentioned_only_in_a_comment_does_not_keep_a_definition():
    src = """
library Ghost { function g() internal pure returns (uint) { return 1; } }
contract Main {
    // Ghost.g() was used here before the refactoring
    uint x;
}
"""
    assert "library Ghost" not in mc.reduce_source(src, "Main")


def test_reduction_keeps_text_that_is_not_a_definition():
    """Free functions and stray statements are never inside a dropped range."""
    src = """
pragma solidity ^0.8.0;
function freeHelper() pure returns (uint) { return 7; }
library Unused { function u() internal pure returns (uint) { return 1; } }
contract Main { uint x = freeHelper(); }
"""
    out = mc.reduce_source(src, "Main")
    assert "function freeHelper()" in out
    assert "Unused" not in out


def test_reduction_of_an_unknown_name_is_refused():
    with pytest.raises(KeyError):
        mc.reduce_source(BASE, "NoSuchContract")


# --------------------------------------------------------------------------- #
# The command line, as the entrypoints call it
# --------------------------------------------------------------------------- #

SCRIPT = tool_script("gptscan", "main_contract.py")


def run_cli(*args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True, env=e,
    )


def test_cli_writes_a_smaller_file_for_a_matching_name(tmp_path):
    src = tmp_path / "10_Main.sol"
    src.write_text(BASE, encoding="utf-8")
    out = tmp_path / "out.sol"

    r = run_cli(str(src), str(out))

    assert r.returncode == 0, r.stderr
    assert out.exists()
    assert len(out.read_text(encoding="utf-8")) < len(BASE)


def test_cli_exits_127_and_writes_nothing_when_no_contract_matches(tmp_path):
    """127 is SmartBugs' established code for exactly this situation.

    ``sb/parse_utils.py`` maps it to the fail "SmartBugs was invoked with
    option 'main', but the filename did not match any contract".
    """
    src = tmp_path / "62_Locke.sol"
    src.write_text("contract Stream { }\ncontract StreamFactory { }\n", encoding="utf-8")
    out = tmp_path / "out.sol"

    r = run_cli(str(src), str(out))

    assert r.returncode == 127
    assert not out.exists()


def test_cli_lists_the_definitions_it_found(tmp_path):
    src = tmp_path / "10_Main.sol"
    src.write_text(BASE, encoding="utf-8")

    r = run_cli("--list", str(src))

    assert r.returncode == 0
    assert set(r.stdout.split()) == {"Unused", "IThing", "Base", "Helper", "Main"}


# --- compile verification (GPTScan compiles; LLMSmartAudit does not) -------- #

def write_solc_stub(directory, report: str) -> None:
    """A fake ``solc`` on PATH, so the fallback can be tested without solc.

    Written twice: the shell form is what a Linux container would pick up, the
    ``.bat`` form is what Windows resolves via PATHEXT. Which one runs depends
    only on the host the tests happen to run on.
    """
    posix = os.path.join(directory, "solc")
    with open(posix, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("#!/bin/sh\ncat > /dev/null\n")
        fh.write("printf '%s' '" + report + "'\nexit 0\n")
    os.chmod(posix, 0o755)

    with open(os.path.join(directory, "solc.bat"), "w", encoding="utf-8") as fh:
        fh.write("@echo off\r\necho " + report + "\r\nexit /b 0\r\n")


def test_verified_reduction_is_kept_when_the_result_compiles(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    write_solc_stub(str(bindir), '{"errors": []}')
    src = tmp_path / "10_Main.sol"
    src.write_text(BASE, encoding="utf-8")
    out = tmp_path / "out.sol"

    r = run_cli("--verify-compile", str(src), str(out),
                env={"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"})

    assert r.returncode == 0, r.stderr
    assert "Unused" not in out.read_text(encoding="utf-8")


def test_reduction_falls_back_to_the_full_source_when_it_stops_compiling(tmp_path):
    """Never worse than MAIN=0: a bad reduction costs context, not the run."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    write_solc_stub(str(bindir), '{"errors": [{"severity": "error"}]}')
    src = tmp_path / "10_Main.sol"
    src.write_text(BASE, encoding="utf-8")
    out = tmp_path / "out.sol"

    r = run_cli("--verify-compile", str(src), str(out),
                env={"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"})

    assert r.returncode == 0, r.stderr
    assert out.read_text(encoding="utf-8") == BASE
    assert "fallback" in (r.stdout + r.stderr).lower()


# --------------------------------------------------------------------------- #
# The corpus this will be run on
# --------------------------------------------------------------------------- #

@pytest.mark.skipif(not os.path.isdir(CORPUS), reason="corpus not present")
def test_three_corpus_files_are_not_named_after_any_of_their_contracts():
    """Measured, not assumed --- and a deliberate exit 127 at MAIN=1.

    ``veCVXStrategy.sol`` holds ``MyStrategy``, ``Locke.sol`` holds ``Stream``
    and ``StreamFactory``, and ``NFTXEligiblityManager.sol`` misspells
    ``NFTXEligibilityManager``. All three names come from the upstream projects,
    so the convention genuinely does not apply to them. If this list ever
    changes, the budget figures derived from it are stale too.
    """
    unresolved = []
    for entry in sorted(os.listdir(CORPUS)):
        if not entry.endswith(".sol"):
            continue
        source = open(os.path.join(CORPUS, entry), encoding="utf-8",
                      errors="replace").read()
        found = mc.resolve_main_name(entry[:-4], names(source))
        if found is None:
            unresolved.append(entry)

    assert unresolved == [
        "31_veCVXStrategy.sol",
        "62_Locke.sol",
        "8_NFTXEligiblityManager.sol",
    ]


@pytest.mark.skipif(not os.path.isdir(CORPUS), reason="corpus not present")
def test_a_flattened_corpus_file_loses_the_contracts_around_its_main_one():
    """10_Visor.sol carries 32 definitions; Visor itself needs 18 of them.

    ``Hypervisor`` is the largest of the dropped ones and the clearest case:
    a sibling contract of the same project, in the file only because it was
    flattened in, and nothing Visor mentions. Note what is *not* asserted here
    --- ``EnumerableSet``, ``SafeMath`` and ``Address`` stay, because Visor
    really does use them. The reduction follows the source, not a list of
    library names.
    """
    source = open(os.path.join(CORPUS, "10_Visor.sol"), encoding="utf-8",
                  errors="replace").read()
    out = mc.reduce_source(source, "Visor")

    assert "contract Visor" in out
    assert "contract Hypervisor" not in out
    assert "contract RewardPool" not in out
    assert len(out.splitlines()) < len(source.splitlines()) * 0.7


@pytest.mark.skipif(not os.path.isdir(CORPUS), reason="corpus not present")
def test_no_corpus_reduction_orphans_a_base_contract():
    """The one way a reduction can stop a file from compiling.

    A dropped library only breaks the build if something still calls it; a
    dropped *base* breaks it immediately, and inheritance is where a flattened
    OpenZeppelin file has its deepest chains. This walks all 96 files and
    checks the ``is A, B`` clause of every surviving definition against the
    surviving set. It is not a substitute for solc --- GPTScan runs the real
    compiler through ``--verify-compile`` --- but it runs without one, which
    solc on this corpus does not: it needs a different version per file.
    """
    inherits = re.compile(
        r"\b(?:abstract\s+)?(?:contract|interface)\s+[A-Za-z_$][\w$]*\s+is\s+([^{]+)\{"
    )
    orphans = []
    for entry in sorted(os.listdir(CORPUS)):
        if not entry.endswith(".sol"):
            continue
        source = open(os.path.join(CORPUS, entry), encoding="utf-8",
                      errors="replace").read()
        defined = {d.name for d in mc.top_level_definitions(source)}
        found = mc.resolve_main_name(entry[:-4], defined)
        if found is None:
            continue
        out = mc.reduce_source(source, found)
        kept = {d.name for d in mc.top_level_definitions(out)}
        for clause in inherits.findall(mc.blank_noncode(out)):
            for base in re.findall(r"[A-Za-z_$][\w$]*", clause):
                if base in defined and base not in kept:
                    orphans.append(f"{entry}: {base}")

    assert orphans == []


# --------------------------------------------------------------------------- #
# The helper is duplicated per tool, as SmartBugs' packaging requires
# --------------------------------------------------------------------------- #

def test_both_tools_ship_the_same_helper():
    """``bin: scripts`` is copied per tool, so the file cannot be shared.

    Upstream does the same with ``printContractNames.py`` across 20 tools. The
    copies must not drift, or the two entrypoints stop selecting the same
    contract and the two tools' numbers stop being comparable.
    """
    a = open(tool_script("gptscan", "main_contract.py"), "rb").read()
    b = open(tool_script("llmsmartaudit", "main_contract.py"), "rb").read()
    assert a == b
