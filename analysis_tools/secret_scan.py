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
    Point ``core.hooksPath`` at the tracked ``.githooks/`` directory so the
    default mode runs automatically. The hook itself is versioned: a hook
    written into ``.git/hooks/`` protects one machine, because ``.git/`` is
    never cloned.

What counts as a secret
-----------------------
Only high-confidence key shapes, and never a value is printed --- the report
names the file, the line and the pattern, nothing else.

The ``sk-`` pattern requires a word boundary in front and allows no hyphens in
the body. Both matter: without them, every CSS class named ``.task-list-item``
in the vendored LLMSmartAudit visualiser matches on the ``sk-`` inside "ta*sk-*
list" --- a false alarm on a tracked file makes a hook that people switch off.

Containers are opened, not skipped
----------------------------------
A regex over the raw bytes of a ``.gz`` finds nothing --- the text is
compressed, so a key inside it is invisible to a byte scan. The test fixtures
use exactly that shape (``result.log.gz``, ``result.tar``), so the scan
decompresses gzip streams and walks tar members before matching. Nesting is
bounded by :data:`MAX_DEPTH`; a container deeper than that is reported as a
skip rather than passed over in silence.

Anything the scan cannot read --- too large, malformed archive, unreadable
path --- is counted and printed. A silent skip is indistinguishable from a
clean file, which is the failure mode this tool exists to prevent.

Usage
-----
::

    python analysis_tools/secret_scan.py            # staged files
    python analysis_tools/secret_scan.py --all      # whole working tree
    python analysis_tools/secret_scan.py --install  # set up the hook
"""

import argparse
import gzip
import io
import os
import re
import subprocess
import sys
import tarfile
import zipfile

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

# Largest blob handed to the matcher, compressed or expanded. Anything above is
# reported as a skip, never dropped quietly.
MAX_BYTES = 20_000_000
# How far to descend into nested containers (a .tar holding a .gz, say).
MAX_DEPTH = 3


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


def _scan_blob(data: bytes, where: str, depth: int,
               hits: list[tuple[str, str]], skips: list[tuple[str, str]]) -> None:
    """Match *data*, then open it if it turns out to be a container.

    *where* is the location shown in the report: the path for a plain file, and
    the path plus ``::member`` or ``(gunzipped)`` for bytes that came out of an
    archive. Recursion is bounded by :data:`MAX_DEPTH`.

    Every branch that gives up appends a reason to *skips*. A container the
    scan could not open must not look like a container that held nothing.
    """
    if len(data) > MAX_BYTES:
        skips.append((where, f"larger than MAX_BYTES ({len(data)} bytes)"))
        return

    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(data):
            line = data.count(b"\n", 0, m.start()) + 1
            hits.append((name, f"{where}:{line}"))

    is_gzip, is_zip = data[:2] == b"\x1f\x8b", data[:4] == b"PK\x03\x04"
    if depth >= MAX_DEPTH:
        if is_gzip or is_zip:
            skips.append((where, f"container nested deeper than MAX_DEPTH ({MAX_DEPTH})"))
        return

    # gzip: the byte match above cannot see through compression at all.
    if is_gzip:
        try:
            _scan_blob(gzip.decompress(data), f"{where}(gunzipped)", depth + 1, hits, skips)
        except Exception as e:
            skips.append((where, f"gzip stream unreadable: {type(e).__name__}"))
        return

    if is_zip:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist():
                    if not info.is_dir():
                        _scan_blob(zf.read(info), f"{where}::{info.filename}",
                                   depth + 1, hits, skips)
        except Exception as e:
            skips.append((where, f"zip archive unreadable: {type(e).__name__}"))
        return

    # tar is uncompressed, so the match above already covered the payload bytes;
    # walking the members only turns a hit into a usable location.
    try:
        tar = tarfile.open(fileobj=io.BytesIO(data))
    except tarfile.TarError:
        return  # not a tar, and nothing was hidden from the match above
    with tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            fh = tar.extractfile(member)
            if fh is None:
                skips.append((where, f"tar member not extractable: {member.name}"))
                continue
            _scan_blob(fh.read(), f"{where}::{member.name}", depth + 1, hits, skips)


def scan_file(rel: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Scan one path. Returns ``(hits, skips)``; a hit never carries the value.

    Both lists matter to the caller: a file that was skipped has not been
    cleared, and the summary has to say so.
    """
    hits: list[tuple[str, str]] = []
    skips: list[tuple[str, str]] = []
    try:
        with open(os.path.join(REPO_ROOT, rel), "rb") as fh:
            data = fh.read()
    except OSError as e:
        skips.append((rel, f"unreadable: {type(e).__name__}"))
        return hits, skips
    _scan_blob(data, rel, 0, hits, skips)
    return hits, skips


# The hook itself is a tracked file, not something this script writes. Enabling
# it is therefore a one-line config change rather than a file copy -- and it
# stays enabled through a `git pull` that changes the hook.
HOOKS_DIR = ".githooks"


def install_hook() -> int:
    """Point ``core.hooksPath`` at the tracked ``.githooks/`` directory.

    Also warns about a leftover ``.git/hooks/pre-commit``: once
    ``core.hooksPath`` is set, git ignores that directory entirely, so a hook
    someone installed there before would silently stop running.
    """
    hook = os.path.join(REPO_ROOT, HOOKS_DIR, "pre-commit")
    if not os.path.isfile(hook):
        print(f"Missing {HOOKS_DIR}/pre-commit -- is this the repository root?",
              file=sys.stderr)
        return 1

    # Read the default hook location *before* setting core.hooksPath -- once it
    # is set, "git rev-parse --git-path hooks" resolves to the new value and the
    # check below would inspect the tracked hook instead of the legacy one.
    git_dir = git("rev-parse", "--absolute-git-dir")
    legacy_hook = os.path.join(git_dir[0], "hooks", "pre-commit") if git_dir else None

    out = subprocess.run(["git", "-C", REPO_ROOT, "config", "core.hooksPath", HOOKS_DIR],
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        print(f"Could not set core.hooksPath: {out.stderr.strip()}", file=sys.stderr)
        return 1
    os.chmod(hook, 0o755)
    print(f"core.hooksPath = {HOOKS_DIR} -- the tracked pre-commit hook is now active.")

    if legacy_hook and os.path.exists(legacy_hook):
        print(f"Note: {legacy_hook} is left in place but git no longer runs it.")
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

    findings: list[tuple[str, str]] = []
    unread: list[tuple[str, str]] = []
    allowlisted = 0
    for rel in targets:
        rel_posix = rel.replace(os.sep, "/")
        if rel_posix in ALLOWLIST:
            allowlisted += 1
            continue
        hits, skips = scan_file(rel_posix)
        findings.extend((name, where) for name, where in hits)
        unread.extend(skips)

    scope = "working tree" if args.all else "staged files"
    # Printed whether or not anything was found: an unscanned file has not been
    # cleared, and that has to be visible in both outcomes.
    if unread:
        print(f"secret_scan: {len(unread)} item(s) could NOT be scanned:", file=sys.stderr)
        for where, why in unread:
            print(f"  {where}  [{why}]", file=sys.stderr)

    if not findings:
        print(f"secret_scan: {len(targets)} {scope} scanned, no secrets found"
              f"{f' ({allowlisted} allowlisted)' if allowlisted else ''}"
              f"{f', {len(unread)} unscanned' if unread else ''}.")
        return 0

    print(f"secret_scan: REFUSING -- {len(findings)} possible secret(s) "
          f"in {len({f[1].split('::')[0].rsplit(':', 1)[0] for f in findings})} file(s):",
          file=sys.stderr)
    for name, where in findings:
        print(f"  {where}  [{name}]", file=sys.stderr)
    print("\nThe value is not shown. Remove it, then commit again.\n"
          "If this is a false positive, add the path to ALLOWLIST in\n"
          "analysis_tools/secret_scan.py -- with a reason.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
