#!/usr/bin/env python3
"""Audit: does anything get lost on the way from the container to ``result.json``?

For every SmartBugs task directory this tool re-reads the *raw* material
(``result.log``, ``result.tar``, ``smartbugs.json``, exit code), extracts every
message a reader would expect to survive, and checks whether that message is
still visible in the parser's output (``result.json``). Whatever is not is
reported as a **gap**.

Why an independent detector set
-------------------------------
The detectors below deliberately do *not* share code with the tool parsers in
``smartbugs/tools/*/parser.py``. An audit that reused the parser's own view of
the log could only ever confirm the parser agrees with itself. Everything here
is derived from the raw log instead, so a parser bug shows up as a gap.

Signal catalogue
----------------
Every detector carries an ``expect``:

``report``
    The message must appear in ``errors`` or ``fails`` --- it says the run did
    not do what it was asked to do.
``mention``
    Appearing in ``infos`` is enough --- the message is informational.

Deliberate non-signals
----------------------
Two things look like failures and are not; the audit never flags them:

* ``vul_before_static > vul_after_static`` in ``GPTSCAN_META``. This is
  GPTScan's static confirmation stage discarding LLM candidates, i.e. the
  tool's intended false-positive filter, and it fires on roughly half of all
  live contracts.
* ``CryticCompile: Compilation warnings/errors on ...`` records that carry only
  ``Warning:`` entries. Solidity warnings do not stop the analysis.

Usage
-----
::

    python analysis_tools/parser_audit.py                       # all runs
    python analysis_tools/parser_audit.py --csv gaps.csv --md gaps.md
    python analysis_tools/parser_audit.py smartbugs/results/gptscan/phase6_live
"""

import argparse
import csv
import datetime as _dt
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_tools.rawlog import (  # noqa: E402
    final_exception,
    find_task_dirs,
    read_task,
    squash,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RESULTS = os.path.join(REPO_ROOT, "smartbugs", "results")

# --------------------------------------------------------------------------- #
# Detector patterns
# --------------------------------------------------------------------------- #

# GPTScan's own logger, e.g. "ERROR    tasks: Static analysis failed: Invalid args".
# The message capture is bounded rather than anchored with ``$``: an unbounded
# ``(.+)$`` re-scans to the end of the record at every candidate position, which
# on LLMSmartAudit's multi-megabyte transcripts costs minutes.
_LOG_ERROR = re.compile(r"(?:^|\s)(ERROR|CRITICAL)\s+([\w.]+):[ \t]*(.{1,400})")
# crytic-compile echoes solc's diagnostics through this record
_COMPILE_REC = re.compile(r"CryticCompile: Compilation warnings/errors on ([^:]+):\s*(.*)$")
# GPTScan degrades to "no static confirmation" when Falcon never came up
_FALCON_DEAD = "Falconisnotinitialized"

# Exit codes a tool uses as a result channel rather than as a failure. slither
# returns 255 whenever it found something, which is why
# ``smartbugs/tools/slither-0.11.3/parser.py:126`` discards ``EXIT_CODE_255``.
# Flagging it here would report upstream's deliberate behaviour as a gap.
BENIGN_EXIT_CODES: dict[str, tuple[int, ...]] = {
    "slither": (255,),
    "slither-0.6.1": (255,),
    "slither-0.10.0": (255,),
    "slither-0.10.4": (255,),
    "slither-0.11.3": (255,),
}

# rich table titles that bleed into the record following them
_TRAILING_NOISE = re.compile(r"\s+(?:Scan Results|Summary)\s*$")

# A traceback whose closing line ended up in a record of its own, without the
# "Traceback (most recent call last)" header. LLMSmartAudit produces these when
# the rich console flushes the header and the final line into separate records.
# Anchored at the start of the record on purpose: an exception name quoted in
# the middle of prose or inside a finding description must not count as a
# report of that exception.
_ORPHAN_EXC = re.compile(
    r"^(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*"
    r"(?:Error|Exception|Interrupt|Exit|Timeout|Failure)"
    r":\s"
)

# Exceptions that are consequences of a failed compilation rather than defects
# of their own. Kept as data so the classification can be cited in the thesis.
_CONSEQUENCE_EXC = (
    "TypeError:'NoneType'objectisnotsubscriptable",
    "UnboundLocalError:localvariable'match_flag'referencedbeforeassignment",
)
# Exceptions that mean the contract never compiled, so no IR exists at all.
# ``ContractSolcParsing`` deliberately does *not* belong here: it reports that
# Falcon could not convert a single function to IR while the contract itself
# compiled and the analysis carried on. ``19_TransactionManager.sol`` is the
# case in point --- solc emitted only a warning, Falcon lost one function to an
# "Incorrect ternary conversion", and GPTScan still produced a finding.
_COMPILE_EXC = (
    "InvalidCompilation",
)

# GPTScan echoes every LLM prompt and response inside a rich panel. Those
# records are huge and full of Solidity source; scanning them costs a lot and
# can never yield a log message. A panel record is only kept when it also
# carries a hard log marker --- which happens when a table finishes on the same
# physical line a log record starts on, e.g.
# ``└──────────┴───────┘ ERROR    tasks: Static analysis failed``.
_PANEL_CHARS = "│╭╰┏┗└┌║╔╚╠╡┣┡┩╇┳┻━┃"
_HARD_MARKER = re.compile(r"(?:ERROR|CRITICAL|WARNING)\s+[\w.]+:|Traceback \(most recent call last\)")
_INTERESTING = ("Error", "Exception", "Traceback", "ERROR", "CRITICAL",
                "Falcon is not initialized", "warnings/errors")


# A log record carrying a diagnostic is at most a few kilobytes. Anything
# longer is an LLM transcript or a source listing that merely happens to
# contain a keyword; truncating it keeps the detector regexes linear.
MAX_RECORD = 20_000


def _candidate_records(records: list[str]) -> list[str]:
    """Records that could plausibly carry a diagnostic message.

    Purely a performance guard: everything it drops is either a rich panel
    echoing prompt/response text or a record without a single diagnostic
    keyword in it.
    """
    out = []
    for r in records:
        if not r:
            continue
        if r[0] in _PANEL_CHARS and not _HARD_MARKER.search(r[:MAX_RECORD]):
            continue
        if not any(needle in r for needle in _INTERESTING):
            continue
        out.append(r[:MAX_RECORD])
    return out


# How much of a message must reappear for it to count as reported. SmartBugs
# shortens long messages by design (``sb.parse_utils.truncate_message`` keeps
# the head and tail and elides the middle), so requiring the full text would
# flag upstream's own convention as data loss. Forty whitespace-free characters
# still identify a message unambiguously: no two distinct diagnostics in this
# corpus share a 40-character prefix.
KEY_LENGTH = 40


class Signal:
    """One message found in the raw material, plus how it should be reported.

    ``key`` is the substring the coverage check looks for in the parser output.
    It is matched whitespace-insensitively so that a parser is free to re-wrap
    or re-indent the text without counting as a loss.
    """

    __slots__ = ("sid", "expect", "message", "key", "klass")

    def __init__(self, sid: str, expect: str, message: str, key: Optional[str] = None,
                 klass: str = "independent") -> None:
        """Build a signal.

        *key* defaults to *message*; pass it explicitly when the wording the
        parser emits differs from the wording found in the raw log (for
        instance ``EXIT_CODE_1``, which no log line contains verbatim).
        """
        self.sid = sid
        self.expect = expect  # "report" | "mention"
        self.message = message.strip()
        self.key = squash(key if key is not None else message)[:KEY_LENGTH]
        self.klass = klass  # "root_cause" | "consequence" | "independent"


def detect(task: dict[str, Any]) -> list[Signal]:
    """Extract every reportable message from one task's raw material."""
    signals: list[Signal] = []
    candidates = _candidate_records(task["records"])
    sq = squash(" ".join(candidates))
    compile_broken = any(m in sq for m in _COMPILE_EXC) or _FALCON_DEAD in sq

    def klass_for(text: str) -> str:
        """Cause or after-effect?

        A message that names the compilation itself is the root cause. Every
        other message in a task whose compilation failed is downstream of it:
        without a Falcon IR there is no static confirmation stage, and the
        code paths that assume one raise ``TypeError`` / ``UnboundLocalError``.
        Both classes are reported verbatim --- this only labels them.
        """
        if any(m in squash(text) for m in _COMPILE_EXC):
            return "root_cause"
        if compile_broken:
            return "consequence"
        return "independent"

    # --- exit code ---------------------------------------------------------
    exit_code = task["exit_code"]
    if exit_code is None:
        signals.append(Signal("EXIT_TIMEOUT", "report",
                              "container did not finish (SmartBugs timeout)",
                              key="DOCKER_TIMEOUT"))
    elif exit_code != 0 and exit_code not in BENIGN_EXIT_CODES.get(task["tool"], ()):
        signals.append(Signal("EXIT_NONZERO", "report",
                              f"container exited with code {exit_code}",
                              key=f"EXIT_CODE_{exit_code}"))

    # --- log records -------------------------------------------------------
    seen: set[str] = set()
    for record in candidates:
        exc = final_exception(record)
        if exc and (
            "Traceback (most recent call last)" in record
            or _ORPHAN_EXC.match(record.lstrip())
        ):
            head = _TRAILING_NOISE.sub("", exc)[:200]
            if head not in seen:
                seen.add(head)
                signals.append(Signal("TRACEBACK", "report", head, klass=klass_for(head)))

        m = _LOG_ERROR.search(record)
        if m:
            text = _TRAILING_NOISE.sub("", f"{m.group(2)}: {m.group(3)}")[:200]
            if text not in seen:
                seen.add(text)
                signals.append(Signal("LOG_ERROR", "report", text, klass=klass_for(text)))

        # The solc diagnostic is only reported when the compilation actually
        # failed. Its severity word cannot be trusted for that decision: with
        # ``--combined-json`` an old solc prints warnings onto stdout, which
        # corrupts the JSON and makes crytic-compile bail out --- so a task can
        # die on a record whose only diagnostic reads "Warning: SPDX license
        # identifier not provided". The thrown exception is the reliable signal;
        # this record supplies the wording.
        m = _COMPILE_REC.search(record)
        if m and compile_broken:
            text = f"solc diagnostics for {os.path.basename(m.group(1))}: {m.group(2)}"[:250]
            if text not in seen:
                seen.add(text)
                signals.append(Signal("COMPILE_ERROR", "report", text,
                                      key=m.group(2)[:60], klass="root_cause"))

        if _FALCON_DEAD in squash(record) and "FALCON" not in seen:
            seen.add("FALCON")
            signals.append(Signal(
                "STATIC_SKIPPED", "report",
                "static_check: Falcon is not initialized, skipping first deposit check",
                key="Falcon is not initialized",
                klass="consequence" if compile_broken else "independent"))

    # --- collected output --------------------------------------------------
    if task["tar_state"] != "ok" or task["output_json"] is None:
        signals.append(Signal("OUTPUT_MISSING", "report",
                              f"no usable output.json (tar: {task['tar_state']})",
                              key="output"))
    else:
        oj = task["output_json"]
        if oj.get("error"):
            signals.append(Signal("OUTPUT_ERROR", "report", str(oj["error"])[:200]))
        if oj.get("success") is False:
            signals.append(Signal("OUTPUT_UNSUCCESSFUL", "report",
                                  f"output.json reports success=false"
                                  f" (message: {oj.get('message')})",
                                  key=str(oj.get("message") or "success")))
        if oj.get("message"):
            signals.append(Signal("OUTPUT_MESSAGE", "mention", str(oj["message"])[:200]))

    # --- GPTScan run metadata ---------------------------------------------
    if task["tool"] == "gptscan":
        meta = _gptscan_meta(task["log_lines"])
        if meta is None:
            # Only worth a signal of its own when the run otherwise looks fine.
            # On a non-zero exit the missing metadata is just another way of
            # saying "the container died", which the exit code already says.
            if exit_code == 0:
                signals.append(Signal("META_MISSING", "report",
                                      "GPTSCAN_META line absent although the container"
                                      " exited 0: the entrypoint never reached the"
                                      " metadata step",
                                      key="GPTSCAN_META"))
        else:
            if meta.get("budget_exceeded"):
                signals.append(Signal("BUDGET_EXCEEDED", "mention",
                                      "GPTScan stopped on its per-contract cost cap",
                                      key="budget"))
            if (meta.get("llm_calls_skipped_budget") or 0) > 0:
                signals.append(Signal("BUDGET_SKIPS", "mention",
                                      f"{meta['llm_calls_skipped_budget']} LLM calls"
                                      " skipped because of the cost cap",
                                      key="skipped"))
    return signals


def _gptscan_meta(log_lines: list[str]) -> Optional[dict[str, Any]]:
    """The entrypoint's ``GPTSCAN_META {json}`` line, or ``None`` if never printed."""
    import json as _json
    for line in log_lines:
        if line.startswith("GPTSCAN_META "):
            try:
                return _json.loads(line[len("GPTSCAN_META "):].strip())
            except ValueError:
                return {}
    return None


# Two signals are reported in somebody else's words rather than with the literal
# key this audit derives from the raw material. Matching on the key alone
# reported them as lost although the fact is plainly in the output --- 12 such
# false gaps over the recorded runs, all of them the three exit-127 contracts of
# gptscan_mwefixed_v2_{dry,main}. The alternatives below are quoted from the
# code that produces them, so a rewording there shows up here as a gap again
# instead of being silently accepted.
EQUIVALENT_WORDINGS: dict[str, tuple[str, ...]] = {
    # sb/parse_utils.py:75-78 turns exit code 127 into this sentence instead of
    # an "EXIT_CODE_127" marker. The code is reserved for exactly this case:
    # --main was given and no contract carries the file's name.
    "EXIT_CODE_127": ("filename did not match any contract",),
    # Both tool parsers name the way the output went missing instead of writing
    # the word "output" (tools/{gptscan,llmsmartaudit}/parser.py::_read_output_json).
    "output": (
        "no tar archive collected from the container",
        "tar archive from the container is unreadable",
        "tar archive contains no output.json",
    ),
}


def covered(signal: Signal, parser_output: Optional[dict[str, Any]]) -> bool:
    """Is *signal* still visible in the parser's output?"""
    if not parser_output:
        return False
    reported = squash(" ".join(parser_output.get("errors", []) + parser_output.get("fails", [])))
    if signal.expect == "report":
        haystack = reported
    else:
        haystack = reported + squash(" ".join(parser_output.get("infos", [])))
    if not signal.key:
        return False
    if signal.key in haystack:
        return True
    return any(squash(alt) in haystack
               for alt in EQUIVALENT_WORDINGS.get(signal.key, ()))


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def audit(task_dirs: list[str]) -> tuple[list[dict[str, Any]], Counter]:
    """Run every detector over every task.

    Returns one row per detected signal plus a ``(tool, runid) -> task count``
    tally, so the summary never has to re-read the results tree.
    """
    rows: list[dict[str, Any]] = []
    per_run: Counter = Counter()
    for d in task_dirs:
        task = read_task(d)
        per_run[(task["tool"], task["runid"])] += 1
        po = task["parser_output"]
        for s in detect(task):
            rows.append({
                "tool": task["tool"],
                "runid": task["runid"],
                "contract": os.path.basename(d),
                "task_dir": os.path.relpath(d, REPO_ROOT),
                "signal": s.sid,
                "expected_in": s.expect,
                "classification": s.klass,
                "message": s.message,
                "covered": covered(s, po),
                "parser_errors": " | ".join(po.get("errors", [])) if po else "",
                "parser_fails": " | ".join(po.get("fails", [])) if po else "",
            })
    return rows, per_run


def summarise(rows: list[dict[str, Any]], per_run_tasks: Counter) -> str:
    """Human-readable console summary."""
    out: list[str] = []
    sig = defaultdict(Counter)
    gap = defaultdict(Counter)
    for r in rows:
        key = (r["tool"], r["runid"])
        sig[key][r["signal"]] += 1
        if not r["covered"]:
            gap[key][r["signal"]] += 1

    out.append(f"{'tool/run':<46}{'tasks':>6}{'signals':>9}{'GAPS':>6}  gap breakdown")
    out.append("-" * 110)
    total_sig = total_gap = 0
    for key in sorted(per_run_tasks):
        n_sig = sum(sig[key].values())
        n_gap = sum(gap[key].values())
        total_sig += n_sig
        total_gap += n_gap
        detail = ", ".join(f"{k}={v}" for k, v in sorted(gap[key].items())) or "-"
        out.append(f"{key[0] + '/' + key[1]:<46}{per_run_tasks[key]:>6}{n_sig:>9}{n_gap:>6}  {detail}")
    out.append("-" * 110)
    out.append(f"{'TOTAL':<46}{sum(per_run_tasks.values()):>6}{total_sig:>9}{total_gap:>6}")

    by_signal = Counter(r["signal"] for r in rows if not r["covered"])
    if by_signal:
        out.append("\nGaps by signal type:")
        for k, v in by_signal.most_common():
            out.append(f"  {v:5d}  {k}")
        out.append("\nGaps by classification:")
        for k, v in Counter(r["classification"] for r in rows if not r["covered"]).most_common():
            out.append(f"  {v:5d}  {k}")
    return "\n".join(out)


def write_csv(rows: list[dict[str, Any]], path: str) -> None:
    """One row per detected signal, including the ones that were covered."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_md(rows: list[dict[str, Any]], per_run_tasks: Counter, path: str) -> None:
    """Markdown gap report, ready to paste into the thesis."""
    gaps = [r for r in rows if not r["covered"]]
    n_tasks = sum(per_run_tasks.values())
    lines = [
        "# Lueckenbericht Parser-Audit",
        "",
        f"Geprueft: **{n_tasks} Task-Verzeichnisse** aus {len(per_run_tasks)} Laeufen, "
        f"**{len(rows)} extrahierte Rohmeldungen**, davon **{len(gaps)}** im "
        f"Parser-Output nicht wiederauffindbar.",
        "",
        # Ohne diese Zeile laesst sich ein aelterer Bericht nicht von einem neuen
        # unterscheiden; zwei Berichte ueber verschieden grosse Laufbestaende
        # duerfen nicht als Vorher/Nachher gelesen werden.
        f"**Laufbestand dieses Berichts:** {len(per_run_tasks)} Laeufe, "
        f"{n_tasks} Tasks, erzeugt am "
        f"{_dt.date.today().strftime('%d.%m.%Y')}. Ein Bericht ueber einen "
        f"anderen Laufbestand ist damit nicht unmittelbar vergleichbar.",
        "",
        "Erzeugt mit `python analysis_tools/parser_audit.py`. Das Werkzeug liest das",
        "Container-Rohmaterial (`result.log`, `result.tar`, `smartbugs.json`, Exit-Code)",
        "mit eigenen Detektoren und prueft, ob jede gefundene Meldung in `result.json`",
        "wieder auftaucht. Nicht als Fehler gewertet werden bewusst: das normale",
        "Static-Filtering von GPTScan (`vul_before_static > vul_after_static`), reine",
        "solc-Warnungen und slithers Exit-Code 255.",
        "",
        "## Uebersicht je Lauf",
        "",
        "| Tool | Lauf | Tasks | Rohmeldungen | Luecken |",
        "|---|---|---:|---:|---:|",
    ]
    sig_per_run: Counter = Counter()
    gap_per_run: Counter = Counter()
    for r in rows:
        key = (r["tool"], r["runid"])
        sig_per_run[key] += 1
        if not r["covered"]:
            gap_per_run[key] += 1
    for key in sorted(per_run_tasks):
        lines.append(f"| {key[0]} | {key[1]} | {per_run_tasks[key]} | "
                     f"{sig_per_run[key]} | {gap_per_run[key]} |")
    lines.append(f"| **Summe** | | **{n_tasks}** | **{len(rows)}** | **{len(gaps)}** |")

    if not gaps:
        lines += [
            "",
            "## Ergebnis",
            "",
            "**Keine Luecke.** Jede im Rohmaterial gefundene Meldung ist im",
            "Parser-Output wiederauffindbar.",
            "",
        ]
    else:
        lines += [
            "",
            "## Ergebnis",
            "",
            # Ohne diesen Verweis steht eine nackte Lueckenzahl im Bericht. Die
            # Einordnung gehoert in ein geschriebenes Dokument, weil sie je
            # Fall verschieden ausfaellt; der Bericht selbst wird erzeugt.
            f"**{len(gaps)} Luecken.** Jede einzelne ist in",
            "`docs/BA-PARSER-AUDIT-LUECKEN.md` benannt und eingeordnet: was im",
            "Rohmaterial steht, was der Parser stattdessen meldet, und was das",
            "fuer die Auswertung bedeutet.",
            "",
            "## Luecken je Lauf und Signaltyp",
            "",
            "| Tool | Lauf | Signal | Klassifikation | Contracts | Beispielmeldung |",
            "|---|---|---|---|---:|---|",
        ]
        grouped: dict[tuple, list[dict]] = defaultdict(list)
        for r in gaps:
            grouped[(r["tool"], r["runid"], r["signal"], r["classification"])].append(r)
        for key in sorted(grouped):
            items = grouped[key]
            example = items[0]["message"].replace("|", "\\|")[:150]
            lines.append(f"| {key[0]} | {key[1]} | `{key[2]}` | {key[3]} | "
                         f"{len(items)} | {example} |")

        lines += ["", "## Betroffene Contracts je Lauf", ""]
        per_run_names: dict[tuple, set] = defaultdict(set)
        for r in gaps:
            per_run_names[(r["tool"], r["runid"])].add(r["contract"])
        for key in sorted(per_run_names):
            names = sorted(per_run_names[key])
            shown = ", ".join(names[:12])
            if len(names) > 12:
                shown += f" ... (+{len(names) - 12} weitere)"
            lines.append(f"- **{key[0]}/{key[1]}** — {len(names)} Contracts: {shown}")

    lines += [
        "",
        "## Signaltypen",
        "",
        "| Signal | Bedeutung |",
        "|---|---|",
        "| `TRACEBACK` | Python-Traceback im Log (roh oder `rich`-gerendert) |",
        "| `LOG_ERROR` | Log-Record des Tools auf Stufe ERROR/CRITICAL |",
        "| `COMPILE_ERROR` | solc-Diagnose zu einem Contract, der nicht uebersetzt wurde |",
        "| `STATIC_SKIPPED` | GPTScans Static-Stufe lief mangels Falcon-IR nicht |",
        "| `OUTPUT_MISSING` | kein brauchbares `output.json` im eingesammelten tar |",
        "| `OUTPUT_UNSUCCESSFUL` | `output.json` meldet `success: false` |",
        "| `OUTPUT_ERROR` | `output.json` traegt ein `error`-Feld |",
        "| `META_MISSING` | `GPTSCAN_META` fehlt trotz Exit-Code 0 |",
        "| `EXIT_NONZERO` / `EXIT_TIMEOUT` | Container-Abbruch bzw. SmartBugs-Timeout |",
        "| `BUDGET_EXCEEDED` / `BUDGET_SKIPS` | GPTScans Kostenbremse hat gegriffen |",
        "",
        "Klassifikation: `root_cause` = Ursache, `consequence` = Folgefehler eines",
        "gescheiterten Compilats, `independent` = davon unabhaengig. Die Einordnung",
        "ersetzt keine Meldung — jede Meldung wird unveraendert weitergereicht.",
    ]

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    """Audit every task under the given roots and report the gaps."""
    ap = argparse.ArgumentParser(
        prog="parser_audit",
        description="List every raw-material message that the tool parsers drop.",
    )
    ap.add_argument("results", nargs="*", default=[DEFAULT_RESULTS], metavar="DIR",
                    help=f"result directories to audit (default: {DEFAULT_RESULTS})")
    ap.add_argument("--csv", metavar="FILE", help="write one row per detected signal")
    ap.add_argument("--md", metavar="FILE", help="write the gap report as Markdown")
    ap.add_argument("--gaps-only", action="store_true",
                    help="restrict --csv to signals that are actually lost")
    args = ap.parse_args()

    task_dirs = find_task_dirs(args.results)
    if not task_dirs:
        print("No SmartBugs task directories found.", file=sys.stderr)
        sys.exit(1)

    rows, per_run = audit(task_dirs)
    print(summarise(rows, per_run))

    if args.csv:
        write_csv([r for r in rows if not r["covered"]] if args.gaps_only else rows, args.csv)
        print(f"\nCSV: {args.csv}")
    if args.md:
        write_md(rows, per_run, args.md)
        print(f"Markdown: {args.md}")


if __name__ == "__main__":
    main()
