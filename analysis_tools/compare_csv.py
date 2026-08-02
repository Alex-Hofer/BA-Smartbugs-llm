#!/usr/bin/env python3
"""Compare two ``sb.results2csv`` exports, e.g. before and after a parser change.

Reports, per run: how many tasks changed, in which columns, and --- the number
that matters for the benchmark --- whether the ``findings`` column moved at all.
A parser change that only adds diagnostics must leave ``findings`` untouched;
this is the check that proves it.

Usage
-----
::

    python analysis_tools/compare_csv.py before.csv after.csv
    python analysis_tools/compare_csv.py before.csv after.csv --md vergleich.md
"""

import argparse
import csv
from collections import Counter, defaultdict

KEY = ("toolid", "runid", "filename")
TRACKED = ("findings", "infos", "errors", "fails", "parser_version")


def load(path: str) -> dict:
    # utf-8-sig: PowerShell's ``>`` redirection writes a BOM, which would
    # otherwise end up glued to the first column name.
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {tuple(r[k] for k in KEY): r for r in csv.DictReader(fh)}


def cells(value: str) -> set:
    """``results2csv`` writes lists as one CSV-quoted cell; split it back.

    ``sb.results2csv.list2excel`` quotes any entry containing ``"``, ``,`` or a
    newline and joins the result with commas -- so the cell is itself a CSV row.
    Splitting it on plain commas would tear messages apart at every comma they
    contain.
    """
    if not value:
        return set()
    try:
        parts = next(csv.reader([value]))
    except (csv.Error, StopIteration):
        parts = value.split(",")
    return {p.strip() for p in parts if p.strip()}


def main() -> None:
    ap = argparse.ArgumentParser(prog="compare_csv", description=__doc__)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--md", metavar="FILE", help="write the comparison as Markdown")
    args = ap.parse_args()

    before, after = load(args.before), load(args.after)
    only_before = set(before) - set(after)
    only_after = set(after) - set(before)

    changed: dict = defaultdict(Counter)
    added_items: dict = defaultdict(Counter)
    findings_moved: list = []

    for key in sorted(set(before) & set(after)):
        b, a = before[key], after[key]
        run = f"{key[0]}/{key[1]}"
        changed[run]["tasks"] += 1
        row_changed = False
        for col in TRACKED:
            if b.get(col, "") == a.get(col, ""):
                continue
            row_changed = True
            changed[run][col] += 1
            if col in ("errors", "fails", "infos"):
                for item in cells(a[col]) - cells(b[col]):
                    added_items[col][item[:90]] += 1
            if col == "findings":
                findings_moved.append((key, b[col], a[col]))
        if row_changed:
            changed[run]["rows_changed"] += 1

    lines = []
    lines.append(f"Rows: {len(before)} before, {len(after)} after"
                 f" ({len(only_before)} disappeared, {len(only_after)} appeared)")
    lines.append("")
    header = (f"{'tool/run':<46}{'tasks':>6}{'changed':>9}"
              f"{'errors':>8}{'fails':>7}{'infos':>7}{'findings':>10}")
    lines.append(header)
    lines.append("-" * len(header))
    for run in sorted(changed):
        c = changed[run]
        lines.append(f"{run:<46}{c['tasks']:>6}{c['rows_changed']:>9}"
                     f"{c['errors']:>8}{c['fails']:>7}{c['infos']:>7}{c['findings']:>10}")
    lines.append("-" * len(header))
    tot = Counter()
    for c in changed.values():
        tot.update(c)
    lines.append(f"{'TOTAL':<46}{tot['tasks']:>6}{tot['rows_changed']:>9}"
                 f"{tot['errors']:>8}{tot['fails']:>7}{tot['infos']:>7}{tot['findings']:>10}")

    lines.append("")
    if findings_moved:
        lines.append(f"!! findings changed for {len(findings_moved)} tasks:")
        for key, b, a in findings_moved[:20]:
            lines.append(f"   {key} : {b!r} -> {a!r}")
    else:
        lines.append("findings column: unchanged for every task"
                     " -- recall/precision cannot have moved.")

    for col in ("errors", "fails", "infos"):
        if not added_items[col]:
            continue
        lines.append(f"\nNewly reported in '{col}' ({sum(added_items[col].values())} entries,"
                     f" {len(added_items[col])} distinct):")
        for item, n in added_items[col].most_common(15):
            lines.append(f"  {n:5d}  {item}")

    text = "\n".join(lines)
    print(text)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write("# Vorher/Nachher-Vergleich der Parser-Ausgabe\n\n```\n" + text + "\n```\n")
        print(f"\nMarkdown: {args.md}")


if __name__ == "__main__":
    main()
