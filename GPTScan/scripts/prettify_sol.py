"""Insert newlines into minified (single-line) Solidity so GPTScan can analyse it.

GPTScan extracts and reasons about code per function and skips any function whose
body is a single source line (`if start_line == end_line: continue`). Minified
contracts (everything on one line) therefore yield zero analysis. This helper
adds a newline after every top-level `;`, `{` and `}` — skipping string literals
and comments so it never corrupts contents — which is enough to give each
statement/block its own line. Solidity is whitespace-insensitive, so the result
still compiles. Line numbers in reports then refer to this reformatted source.

Usage:
    python scripts/prettify_sol.py OUT_DIR FILE1.sol [FILE2.sol ...]
"""

import os
import sys


def prettify(src: str) -> str:
    """Return ``src`` with a newline after every ``;``, ``{`` and ``}`` outside strings and comments."""
    out = []
    i, n = 0, len(src)
    state = "normal"
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state == "normal":
            if c == "/" and nxt == "/":
                out.append(c)
                state = "line_comment"
            elif c == "/" and nxt == "*":
                out.append(c)
                state = "block_comment"
            elif c == '"':
                out.append(c)
                state = "dq"
            elif c == "'":
                out.append(c)
                state = "sq"
            else:
                out.append(c)
                if c in ";{}":
                    out.append("\n")
            i += 1
        elif state == "line_comment":
            out.append(c)
            if c == "\n":
                state = "normal"
            i += 1
        elif state == "block_comment":
            out.append(c)
            if c == "*" and nxt == "/":
                out.append(nxt)
                i += 2
                state = "normal"
                continue
            i += 1
        elif state in ("dq", "sq"):
            out.append(c)
            if c == "\\" and nxt:
                out.append(nxt)
                i += 2
                continue
            if (state == "dq" and c == '"') or (state == "sq" and c == "'"):
                state = "normal"
            i += 1
    return "".join(out)


def main():
    """CLI: ``OUT_DIR FILE1.sol [FILE2.sol ...]``; writes reformatted copies into OUT_DIR."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for path in sys.argv[2:]:
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
        pretty = prettify(src)
        dest = os.path.join(out_dir, os.path.basename(path))
        with open(dest, "w", encoding="utf-8") as f:
            f.write(pretty)
        print(f"{os.path.basename(path)}: {src.count(chr(10))} -> {pretty.count(chr(10))} lines")


if __name__ == "__main__":
    main()
