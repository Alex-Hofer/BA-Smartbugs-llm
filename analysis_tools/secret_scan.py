#!/usr/bin/env python3
"""Refuse to let an API key reach a commit.

This project talks to a paid LLM API, so a key is present on the machine at all
times. It lives in ``GPTScan/.env`` and nowhere else. Two things already guard
it --- ``.gitignore`` excludes ``.env``/``*.env``, and ``sb/docker.py`` redacts
forwarded environment values before they are written to a task log --- but both
are silent guarantees. This is the loud one.

Modes
-----
``(default)``
    Scan the files staged for the current commit. This is what the pre-commit
    hook runs; a hit exits 1 and the commit does not happen.
``--all``
    Scan everything that *could* be committed: tracked files plus untracked
    files that ``.gitignore`` does not exclude. Ignored files (the results
    tree, ``.env``, the virtualenv) are deliberately not scanned --- they are
    not going anywhere.
``--install``
    Write ``.git/hooks/pre-commit`` so the default mode runs automatically.

What counts as a secret
-----------------------
Only high-confidence key shapes, and never a value is printed --- the report
names the file, the line and the pattern, nothing else.

The ``sk-`` pattern requires a word boundary in front and allows no hyphens in
the body. Both matter: without them, every CSS class named ``.task-list-item``
in the vendored LLMSmartAudit visualiser matches on the ``sk-`` inside "ta*sk-*
list" --- a false alarm on a tracked file makes a hook that people switch off.

Usage
-----
::

    python analysis_tools/secret_scan.py            # staged files
    python analysis_tools/secret_scan.py --all      # whole working tree
    python analysis_tools/secret_scan.py --install  # set up the hook
"""

import argparse
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Provider key shapes. Each is anchored on a non-word character so a match
# cannot start in the middle of an identifier.
PATTERNS: dict[str, re.Pattern[bytes]] = {
    "openai/deepseek key": re.compile(rb"(?<![A-Za-z0-9_\-])sk-[A-Za-z0-9]{20,}"),
    "openai project key": re.compile(rb"(?<![A-Za-z0-9_\-])sk-proj-[A-Za-z0-9_\-]{20,}"),
    "github token": re.compile(rb"(?<![A-Za-z0-9_\-])gh[pousr]_[A-Za-z0-9]{30,}"),
    "github fine-grained pat": re.compile(rb"(?<![A-Za-z0-9_\-])github_pat_[A-Za-z0-9_]{30,}"),
    "aws access key id": re.compile(rb"(?<![A-Za-z0-9_\-])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])"),
    "slack token": re.compile(rb"(?<![A-Za-z0-9_\-])xox[baprs]-[A-Za-z0-9\-]{10,}"),
    "private key block": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
}

# Files that legitimately contain something key-shaped. Kept deliberately
# short: every entry here is a hole in the net, so each needs a reason.
ALLOWLIST: dict[str, str] = {
    # Documents the variable names with empty values -- that is its whole job.
    "GPTScan/.env.example": "documents variable names, values are empty",
}

MAX_BYTES = 20_000_000


def git(*args: str) -> list[str]:
    """Run a git command in the repository and return its output lines."""
    out = subprocess.run(["git", "-C", REPO_ROOT, *args],
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        return []
    return [line for line in out.stdout.splitlines() if line.strip()]


def files_to_scan(scan_all: bool) -> list[str]:
    """The paths this invocation is responsible for -- see the module docstring."""
    if scan_all:
        # Everything that could end up in a commit: tracked plus untracked
        # that .gitignore does not exclude.
        return sorted(set(git("ls-files")) |
                      set(git("ls-files", "--others", "--exclude-standard")))
    return sorted(set(git("diff", "--cached", "--name-only", "--diff-filter=ACM")))


def scan_file(rel: str) -> list[tuple[str, int]]:
    """Return ``(pattern name, line number)`` for every hit. Never the value."""
    path = os.path.join(REPO_ROOT, rel)
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return []
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return []

    hits = []
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(data):
            line = data.count(b"\n", 0, m.start()) + 1
            hits.append((name, line))
    return hits


HOOK = """#!/bin/sh
# Installed by analysis_tools/secret_scan.py --install
# Blocks a commit that would introduce an API key. See docs/BA-BETRIEB.md.
exec python "$(git rev-parse --show-toplevel)/analysis_tools/secret_scan.py"
"""


def install_hook() -> int:
    """Write .git/hooks/pre-commit, refusing to clobber an existing hook."""
    hooks = git("rev-parse", "--git-path", "hooks")
    hooks_dir = os.path.join(REPO_ROOT, hooks[0]) if hooks else None
    if not hooks_dir or not os.path.isdir(os.path.dirname(hooks_dir)):
        print("Not a git repository -- cannot install the hook.", file=sys.stderr)
        return 1
    os.makedirs(hooks_dir, exist_ok=True)
    path = os.path.join(hooks_dir, "pre-commit")
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            if "secret_scan.py" in fh.read():
                print(f"Hook already installed: {path}")
                return 0
        print(f"Refusing to overwrite an existing hook: {path}\n"
              f"Add this line to it instead:\n"
              f'  python "$(git rev-parse --show-toplevel)/analysis_tools/secret_scan.py"',
              file=sys.stderr)
        return 1
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(HOOK)
    os.chmod(path, 0o755)
    print(f"Installed pre-commit hook: {path}")
    return 0


def main() -> int:
    """Scan, report and return the process exit code (1 on any finding)."""
    ap = argparse.ArgumentParser(
        prog="secret_scan",
        description="Block API keys from reaching a commit. Values are never printed.",
    )
    ap.add_argument("--all", action="store_true",
                    help="scan the whole working tree instead of the staged files")
    ap.add_argument("--install", action="store_true",
                    help="install this scan as the repository's pre-commit hook")
    args = ap.parse_args()

    if args.install:
        return install_hook()

    targets = files_to_scan(args.all)
    if not targets:
        print("secret_scan: nothing to scan.")
        return 0

    findings: list[tuple[str, str, int]] = []
    skipped = 0
    for rel in targets:
        rel_posix = rel.replace(os.sep, "/")
        if rel_posix in ALLOWLIST:
            skipped += 1
            continue
        for name, line in scan_file(rel):
            findings.append((rel_posix, name, line))

    scope = "working tree" if args.all else "staged files"
    if not findings:
        print(f"secret_scan: {len(targets)} {scope} scanned, no secrets found"
              f"{f' ({skipped} allowlisted)' if skipped else ''}.")
        return 0

    print(f"secret_scan: REFUSING -- {len(findings)} possible secret(s) "
          f"in {len({f[0] for f in findings})} file(s):", file=sys.stderr)
    for rel, name, line in findings:
        print(f"  {rel}:{line}  [{name}]", file=sys.stderr)
    print("\nThe value is not shown. Remove it, then commit again.\n"
          "If this is a false positive, add the path to ALLOWLIST in\n"
          "analysis_tools/secret_scan.py -- with a reason.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
