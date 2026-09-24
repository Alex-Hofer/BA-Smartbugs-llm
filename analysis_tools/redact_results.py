#!/usr/bin/env python3
"""Remove API keys from task logs written before the ``sb/docker.py`` fix.

Background
----------
``sb/docker.py`` forwards the host's ``DEEPSEEK_API_KEY`` into the tool
container. The very arguments handed to Docker are persisted verbatim into
every ``smartbugs.json``, so early runs recorded the key in clear text. The
patch in ``sb/docker.py`` (block ``BA MODIFICATION 5``) now blanks the
forwarded values *before* they are returned for logging::

    if "environment" in args:
        args["environment"] = {k: "<redacted>" for k in args["environment"]}

Runs made before that patch keep the key on disk. This script brings them into
line with what SmartBugs writes today.

Why rewrite instead of delete
-----------------------------
The measurement data is not reproducible without new (paid) LLM runs and is the
evidence base for the whole benchmark. Only the single offending *value* is
replaced; every other byte of the task log is preserved, and the file is written
back through the same ``json.dumps(..., sort_keys=True, indent=4)`` call that
``sb.io.write_json`` uses, so redacted files stay byte-identical to what
SmartBugs itself would have produced.

Safety
------
* Dry run by default --- ``--apply`` is required to write anything.
* Refuses to touch a file unless the *only* difference is the redacted value.
* Never prints a secret, not even partially.

Usage
-----
::

    python analysis_tools/redact_results.py                  # report only
    python analysis_tools/redact_results.py --apply
"""

import argparse
import copy
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_tools.rawlog import TASK_LOG, find_task_dirs  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RESULTS = os.path.join(REPO_ROOT, "smartbugs", "results")

PLACEHOLDER = "<redacted>"

# Value shapes that count as a secret. Deliberately narrow: the point is to
# catch real provider keys, not to guess at every string that looks odd.
SECRET_VALUE = re.compile(r"(?:sk-|sk_live_|ghp_|gho_|github_pat_)[A-Za-z0-9_\-]{16,}")

# Environment variables whose value is a credential by definition. Their value
# is redacted regardless of shape, so a key in a future format is still caught.
SECRET_NAMES = ("API_KEY", "APIKEY", "TOKEN", "SECRET", "PASSWORD")


def is_secret(name: str, value: object) -> bool:
    """Should ``name = value`` be redacted?"""
    if not isinstance(value, str) or value == PLACEHOLDER or not value:
        return False
    if any(marker in name.upper() for marker in SECRET_NAMES):
        return True
    return bool(SECRET_VALUE.search(value))


def redact_task_log(data: dict) -> tuple[dict, list[str]]:
    """Return a redacted copy of a task log plus the names that were replaced."""
    out = copy.deepcopy(data)
    env = out.get("docker", {}).get("environment")
    replaced: list[str] = []
    if isinstance(env, dict):
        for name, value in env.items():
            if is_secret(name, value):
                env[name] = PLACEHOLDER
                replaced.append(name)
    return out, replaced


def only_difference_is_redaction(before: dict, after: dict, names: list[str]) -> bool:
    """Guard: confirm nothing but the named environment values changed."""
    probe = copy.deepcopy(before)
    env = probe.get("docker", {}).get("environment", {})
    for name in names:
        env[name] = PLACEHOLDER
    return probe == after


def main() -> None:
    """Scan every task log for secrets and, with --apply, rewrite them."""
    ap = argparse.ArgumentParser(
        prog="redact_results",
        description="Replace API keys in SmartBugs task logs with a placeholder.",
    )
    ap.add_argument("results", nargs="*", default=[DEFAULT_RESULTS], metavar="DIR",
                    help=f"result directories to clean (default: {DEFAULT_RESULTS})")
    ap.add_argument("--apply", action="store_true",
                    help="actually rewrite the files (default: report only)")
    args = ap.parse_args()

    task_dirs = find_task_dirs(args.results)
    hits: list[tuple[str, list[str]]] = []
    per_run: Counter = Counter()

    for d in task_dirs:
        path = os.path.join(d, TASK_LOG)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as e:
            print(f"  ! unreadable, skipped: {os.path.relpath(path, REPO_ROOT)} ({e})")
            continue

        redacted, names = redact_task_log(data)
        if not names:
            continue
        if not only_difference_is_redaction(data, redacted, names):
            print(f"  ! refusing to write (unexpected diff): {os.path.relpath(path, REPO_ROOT)}")
            continue

        hits.append((path, names))
        per_run[(data.get("tool", {}).get("id", "?"), data.get("runid", "?"))] += 1

        if args.apply:
            # Same serialisation as sb.io.write_json, so the result is
            # indistinguishable from a file SmartBugs wrote itself.
            text = json.dumps(redacted, sort_keys=True, indent=4)
            with open(path, "w", encoding="utf-8") as fh:
                print(text, file=fh)

    verb = "Redacted" if args.apply else "Would redact"
    print(f"{verb} {len(hits)} of {len(task_dirs)} task logs.")
    for key in sorted(per_run):
        print(f"  {per_run[key]:4d}  {key[0]}/{key[1]}")
    fields = Counter(n for _p, names in hits for n in names)
    if fields:
        print("Fields:", ", ".join(f"{n} (x{c})" for n, c in fields.most_common()))
    if hits and not args.apply:
        print("\nNothing was written. Re-run with --apply once a backup exists.")


if __name__ == "__main__":
    main()
