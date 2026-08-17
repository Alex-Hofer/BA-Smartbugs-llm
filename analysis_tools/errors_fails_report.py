#!/usr/bin/env python3
"""Report SmartBugs *errors* and *fails* separately, per run and per tool.

``sb/results2csv.py`` already emits both as columns, but a CSV cell holding a
comma-joined set of truncated messages is not something anyone reads. This
turns the same data into a per-run balance sheet: how many tasks ran cleanly,
how many hit an error, how many failed, which contracts were affected, and what
each message said --- verbatim.

The split itself comes from ``sb/parse_utils.py::errors_fails`` and is not
reinterpreted here; see ``docs/BA-ERRORS-VS-FAILS.md`` for the derivation.

    error   the tool noticed a problem, handled it, and kept going
    fail    an exception escaped the tool, or the run was aborted from outside

Cause versus consequence
------------------------
A failed compilation drags a train of follow-up errors behind it: without a
Falcon IR, GPTScan's static stage raises ``TypeError`` and friends. Those are
reported with their original wording --- the judgement goes into a separate
``classification`` column, never into dropping or rewriting a message:

    root_cause    names the compilation itself
    consequence   any other message in a task whose compilation failed
    independent   the task compiled; the message stands on its own

Usage
-----
::

    python analysis_tools/errors_fails_report.py
    python analysis_tools/errors_fails_report.py --csv docs/errors-fails.csv \
                                                 --md  docs/errors-fails.md
    python analysis_tools/errors_fails_report.py smartbugs/results/gptscan
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_tools.rawlog import PARSER_OUTPUT, TASK_LOG, find_task_dirs  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RESULTS = os.path.join(REPO_ROOT, "smartbugs", "results")

# The info the GPTScan parser adds when the contract did not compile. Its
# presence is what turns every other message in that task into a consequence.
_DEGRADED = "analysis degraded"
# Messages that name the compilation itself.
_ROOT_MARKERS = ("Invalid compilation", "InvalidCompilation", "solc rejected")
# Prefix the tool parsers put on a timeout entry in `errors` (AP5).
_TIMEOUT_MARK = "TIMEOUT_"


def classify(message: str, degraded: bool) -> str:
    """Cause, after-effect, or neither -- see the module docstring."""
    if any(m in message for m in _ROOT_MARKERS):
        return "root_cause"
    return "consequence" if degraded else "independent"


def collect(task_dirs: list[str]) -> tuple[dict, list[dict]]:
    """Return per-run totals and one detail row per distinct message."""
    totals: dict = defaultdict(lambda: Counter())
    # (tool, runid, kind, message) -> set of contracts
    messages: dict = defaultdict(set)
    classes: dict = {}

    for d in task_dirs:
        try:
            with open(os.path.join(d, TASK_LOG), encoding="utf-8") as fh:
                task_log = json.load(fh)
        except (OSError, ValueError):
            continue
        key = (task_log.get("tool", {}).get("id", "?"), task_log.get("runid", "?"))
        totals[key]["tasks"] += 1

        try:
            with open(os.path.join(d, PARSER_OUTPUT), encoding="utf-8") as fh:
                parsed = json.load(fh)
        except (OSError, ValueError):
            totals[key]["unparsed"] += 1
            continue

        errors = parsed.get("errors", [])
        fails = parsed.get("fails", [])
        degraded = any(_DEGRADED in i for i in parsed.get("infos", []))
        # AP5: the run was cut short by the deadline/net. Read out of errors
        # for the same reason "degraded" is read out of infos: the parser has
        # already normalised it, and result.json carries no raw report.
        timeout_hit = any(str(e).startswith(_TIMEOUT_MARK) for e in errors)
        contract = os.path.basename(task_log.get("filename", d))

        if errors:
            totals[key]["tasks_with_errors"] += 1
        if fails:
            totals[key]["tasks_with_fails"] += 1
        if not errors and not fails:
            totals[key]["tasks_clean"] += 1
        totals[key]["errors"] += len(errors)
        totals[key]["fails"] += len(fails)
        if degraded:
            totals[key]["tasks_not_compiled"] += 1
        if timeout_hit:
            # Stays counted in every total above -- excluding it would be the
            # same measurement error with the opposite sign.
            totals[key]["tasks_timeout"] += 1

        for kind, group in (("error", errors), ("fail", fails)):
            for message in group:
                mkey = (key[0], key[1], kind, message)
                messages[mkey].add(contract)
                classes[mkey] = classify(message, degraded)

    rows = []
    for mkey, contracts in messages.items():
        rows.append({
            "tool": mkey[0],
            "runid": mkey[1],
            "kind": mkey[2],
            "classification": classes[mkey],
            "contracts": len(contracts),
            "message": mkey[3],
            "affected": "; ".join(sorted(contracts)),
        })
    rows.sort(key=lambda r: (r["tool"], r["runid"], r["kind"], -r["contracts"], r["message"]))
    return totals, rows


def summary_table(totals: dict) -> list[str]:
    """Render the per-run balance sheet as fixed-width console lines."""
    header = (f"{'tool/run':<46}{'tasks':>7}{'clean':>7}{'err.tasks':>10}"
              f"{'fail.tasks':>11}{'errors':>8}{'fails':>7}{'no-compile':>11}{'timeout':>9}")
    lines = [header, "-" * len(header)]
    grand: Counter = Counter()
    for key in sorted(totals):
        c = totals[key]
        grand.update(c)
        lines.append(f"{key[0] + '/' + key[1]:<46}{c['tasks']:>7}{c['tasks_clean']:>7}"
                     f"{c['tasks_with_errors']:>10}{c['tasks_with_fails']:>11}"
                     f"{c['errors']:>8}{c['fails']:>7}{c['tasks_not_compiled']:>11}"
                     f"{c['tasks_timeout']:>9}")
    lines.append("-" * len(header))
    lines.append(f"{'TOTAL':<46}{grand['tasks']:>7}{grand['tasks_clean']:>7}"
                 f"{grand['tasks_with_errors']:>10}{grand['tasks_with_fails']:>11}"
                 f"{grand['errors']:>8}{grand['fails']:>7}{grand['tasks_not_compiled']:>11}"
                 f"{grand['tasks_timeout']:>9}")
    return lines


def write_csv(rows: list[dict[str, Any]], path: str) -> None:
    """One row per distinct message, with the contracts it occurred on."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(totals: dict, rows: list[dict[str, Any]], path: str, max_rows: int) -> None:
    """Markdown report, ready to paste into the thesis."""
    grand: Counter = Counter()
    for c in totals.values():
        grand.update(c)

    lines = [
        "# Errors und Fails je Lauf",
        "",
        "SmartBugs trennt **errors** (das Werkzeug hat das Problem bemerkt, behandelt",
        "und weitergearbeitet) von **fails** (eine Exception ist dem Werkzeug entkommen",
        "oder der Lauf wurde von aussen abgebrochen). Die Trennung stammt aus",
        "`smartbugs/sb/parse_utils.py::errors_fails`; hergeleitet in",
        "`docs/BA-ERRORS-VS-FAILS.md`.",
        "",
        "Erzeugt mit `python analysis_tools/errors_fails_report.py --md ... --csv ...`.",
        "",
        "## Bilanz je Lauf",
        "",
        "| Tool | Lauf | Tasks | sauber | Tasks mit Errors | Tasks mit Fails | "
        "Errors | Fails | nicht uebersetzt | Teillauf (Timeout) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in sorted(totals):
        c = totals[key]
        lines.append(f"| {key[0]} | {key[1]} | {c['tasks']} | {c['tasks_clean']} | "
                     f"{c['tasks_with_errors']} | {c['tasks_with_fails']} | "
                     f"{c['errors']} | {c['fails']} | {c['tasks_not_compiled']} | "
                     f"{c['tasks_timeout']} |")
    lines.append(f"| **Summe** | | **{grand['tasks']}** | **{grand['tasks_clean']}** | "
                 f"**{grand['tasks_with_errors']}** | **{grand['tasks_with_fails']}** | "
                 f"**{grand['errors']}** | **{grand['fails']}** | "
                 f"**{grand['tasks_not_compiled']}** | **{grand['tasks_timeout']}** |")

    lines += [
        "",
        "Spalte *sauber*: Tasks ohne jeden Error und Fail. Spalte *nicht uebersetzt*:",
        "Tasks, deren Contract nicht kompiliert werden konnte — dort ist ein leeres",
        "Finding-Ergebnis unbestimmt, nicht sauber. Spalte *Teillauf (Timeout)*: Tasks,",
        "deren Lauf durch die AP5-Deadline vorzeitig beendet wurde (AP5); sie zaehlen",
        "regulaer in *Tasks* mit, statt herausgerechnet zu werden.",
        "",
        "## Meldungen im Wortlaut",
        "",
        "Klassifikation: `root_cause` benennt das Compilat selbst, `consequence` ist",
        "eine Folge davon, `independent` steht fuer sich. Die Einordnung ersetzt keine",
        "Meldung — jede wird unveraendert wiedergegeben.",
        "",
        "| Tool | Lauf | Art | Klassifikation | Contracts | Meldung |",
        "|---|---|---|---|---:|---|",
    ]
    fails_first = sorted(rows, key=lambda r: (r["kind"] != "fail", -r["contracts"]))
    for r in fails_first[:max_rows]:
        message = r["message"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r['tool']} | {r['runid']} | {r['kind']} | {r['classification']} | "
                     f"{r['contracts']} | {message} |")
    if len(rows) > max_rows:
        lines.append(f"| ... | | | | | *{len(rows) - max_rows} weitere Meldungen, "
                     f"vollstaendig in der CSV* |")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    """Collect every task under the given roots and report errors vs fails."""
    ap = argparse.ArgumentParser(
        prog="errors_fails_report",
        description="Report SmartBugs errors and fails separately, per run and tool.",
    )
    ap.add_argument("results", nargs="*", default=[DEFAULT_RESULTS], metavar="DIR",
                    help=f"result directories to report on (default: {DEFAULT_RESULTS})")
    ap.add_argument("--csv", metavar="FILE", help="write one row per distinct message")
    ap.add_argument("--md", metavar="FILE", help="write the report as Markdown")
    ap.add_argument("--max-md-rows", type=int, default=60, metavar="N",
                    help="cap the message table in the Markdown report (default 60)")
    args = ap.parse_args()

    task_dirs = find_task_dirs(args.results)
    if not task_dirs:
        print("No SmartBugs task directories found.", file=sys.stderr)
        sys.exit(1)

    totals, rows = collect(task_dirs)
    print("\n".join(summary_table(totals)))

    if rows:
        print("\nDistinct messages:", len(rows),
              f"({sum(1 for r in rows if r['kind'] == 'fail')} fails,"
              f" {sum(1 for r in rows if r['kind'] == 'error')} errors)")
        for kind in ("fail", "error"):
            ranked = sorted((r for r in rows if r["kind"] == kind),
                            key=lambda x: -x["contracts"])[:8]
            if not ranked:
                continue
            print(f"\n  most widespread {kind}s:")
            for r in ranked:
                message = r["message"].replace("\n", " ")[:100]
                print(f"    {r['contracts']:5d} contracts  [{r['classification']:11s}]"
                      f"  {r['tool']}/{r['runid']}")
                print(f"           {message}")

    if args.csv and rows:
        write_csv(rows, args.csv)
        print(f"\nCSV: {args.csv}")
    if args.md:
        write_md(totals, rows, args.md, args.max_md_rows)
        print(f"Markdown: {args.md}")


if __name__ == "__main__":
    main()
