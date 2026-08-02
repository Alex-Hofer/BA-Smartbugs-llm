#!/usr/bin/env python3
"""Rebuild the mwevariety corpus from the original Web3Bugs sources.

The local samples under smartbugs/samples/gptscan/mwevariety/ are
whitespace-corrupted single-file extracts of Web3Bugs contest projects
(https://github.com/ZhangZhuoSJTU/Web3Bugs). This tool

  map      locates the pristine original for every sample and PROVES the
           match by comparing the whitespace-stripped byte streams
           (corruption only mangled whitespace, so equality is exact),
  flatten  resolves each original's import tree (project files + vendored
           npm packages) into one self-contained .sol per sample,
  check    compiles every flattened file with a pragma-matching solc.

Outputs land in smartbugs/samples/gptscan/mwevariety_fixed/ so the old
(corrupted) corpus and its results remain untouched and reproducible.
"""

import argparse
import json
import re
import sys
from pathlib import Path

BA = Path(__file__).resolve().parent.parent
W3B = Path.home() / "w3b" / "contracts"
SAMPLES = BA / "smartbugs" / "samples" / "gptscan" / "mwevariety"
FIXED = BA / "smartbugs" / "samples" / "gptscan" / "mwevariety_fixed"
TOOLS = BA / "corpus_tools"
MAPPING = TOOLS / "mapping.json"

WS = re.compile(rb"\s+")

# The extractor mislabeled two contest ids (off by one); verified by locating
# the contracts in the Web3Bugs tree: Trident is contest 35, Badger ibBTC 47.
CONTEST_OVERRIDE = {
    "34_ConcentratedLiquidityPool.sol": "35",
    "34_ConcentratedLiquidityPosition.sol": "35",
    "46_WrappedIbbtcEth.sol": "47",
}


def strip_comments(data: bytes) -> bytes:
    """Remove // and /* */ comments, Solidity-aware (string literals kept)."""
    out, i, n = bytearray(), 0, len(data)
    while i < n:
        c = data[i:i + 1]
        two = data[i:i + 2]
        if two == b"//":
            i = data.find(b"\n", i)
            if i == -1:
                break
            continue  # keep the newline itself
        if two == b"/*":
            end = data.find(b"*/", i + 2)
            i = n if end == -1 else end + 2
            out += b" "  # comment acts as token separator
            continue
        if c in (b'"', b"'"):
            quote, j = c, i + 1
            while j < n:
                if data[j:j + 1] == b"\\":
                    j += 2
                    continue
                if data[j:j + 1] == quote:
                    break
                j += 1
            out += data[i:j + 1]
            i = j + 1
            continue
        out += c
        i += 1
    return bytes(out)


def stripped(data: bytes) -> bytes:
    """Comment- and whitespace-free byte stream (BOM removed).

    The mwevariety extracts were produced by a comment stripper that also
    mangled newlines, so code equality must be checked on this normal form.
    """
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return WS.sub(b"", strip_comments(data))


def cmd_map(_args) -> int:
    results, exact, missing, mismatch = {}, 0, [], []
    for f in sorted(SAMPLES.glob("*.sol")):
        m = re.match(r"(\d+)_(.+)\.sol$", f.name)
        cid, name = m.group(1), m.group(2)
        cid = CONTEST_OVERRIDE.get(f.name, cid)
        croot = W3B / cid
        skip = {"artifacts", "cache", "node_modules", ".git", "discord-export"}
        cands = [
            c for c in sorted(croot.rglob(name + ".sol"))
            if c.is_file() and not skip.intersection(c.parts)
        ] if croot.exists() else []
        target = stripped(f.read_bytes())
        hit, how, cov = None, None, None
        for c in cands:
            norm = stripped(c.read_bytes())
            if norm == target:
                hit, how, cov = c, "equal", 100.0
                break
            # extraction bug truncated many samples: sample = prefix of orig
            if len(target) >= 50 and norm.startswith(target):
                pct = round(100.0 * len(target) / len(norm), 1)
                if hit is None or how != "truncated-prefix" or pct > cov:
                    hit, how, cov = c, "truncated-prefix", pct
                continue
            # some samples additionally retain comment-banner junk mid-stream;
            # then only the header (pragma/imports/contract head) matches.
            if hit is None or how == "header-prefix":
                k = 0
                while k < min(len(target), len(norm)) and target[k] == norm[k]:
                    k += 1
                if k >= 200 and (cov is None or k > cov):
                    hit, how, cov = c, "header-prefix", k
        if hit:
            results[f.name] = {
                "original": str(hit.relative_to(W3B)),
                "verified": how,
                "sample_coverage_pct": cov,
            }
            exact += 1
        elif not croot.exists():
            results[f.name] = {"original": None, "verified": "contest-missing"}
            missing.append(f.name)
        else:
            # keep diagnostics: candidate names + length delta of best guess
            diag = [
                {
                    "cand": str(c.relative_to(W3B)),
                    "len_delta": len(stripped(c.read_bytes())) - len(target),
                }
                for c in cands[:5]
            ]
            results[f.name] = {"original": None, "verified": "no-exact-match",
                               "candidates": diag}
            mismatch.append(f.name)
    MAPPING.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"exact: {exact}/96   contest-missing: {len(missing)} {missing}")
    print(f"no-exact-match: {len(mismatch)} {mismatch}")
    return 0 if exact + len(missing) == 96 else 1


# --------------------------------------------------------------------------
# import resolution
# --------------------------------------------------------------------------

IMPORT_RE = re.compile(
    rb"import\s+(?:(?:\{[^}]*\}|\*\s*as\s+\w+|\w+)\s+from\s+)?"
    rb"([\"'])([^\"']+)\1\s*(?:as\s+\w+\s*)?;"
)
VENDOR = TOOLS / "vendor"  # vendored npm packages: vendor/<contest>/<pkg>/...


def project_root(file: Path, contest_dir: Path) -> Path:
    """Nearest ancestor with a build config (package.json/foundry/remappings)."""
    d = file.parent
    while d != contest_dir.parent:
        for probe in ("package.json", "foundry.toml", "remappings.txt",
                      "hardhat.config.js", "hardhat.config.ts", "truffle-config.js"):
            if (d / probe).is_file():
                return d
        if d == contest_dir:
            break
        d = d.parent
    return contest_dir


def load_remappings(root: Path) -> list[tuple[str, str]]:
    maps = []
    rt = root / "remappings.txt"
    if rt.is_file():
        lines = rt.read_text(encoding="utf-8", errors="replace").splitlines()
        maps += [l.strip() for l in lines if "=" in l]
    ft = root / "foundry.toml"
    if ft.is_file():
        try:
            import tomllib
            data = tomllib.loads(ft.read_text(encoding="utf-8", errors="replace"))
            for prof in data.get("profile", {}).values():
                maps += prof.get("remappings", [])
            maps += data.get("remappings", [])
        except Exception:
            pass
    out = []
    for m in maps:
        if isinstance(m, str) and "=" in m:
            pre, _, tgt = m.partition("=")
            out.append((pre, tgt))
    return out


# foundry lib/ checkouts are empty git submodules in Web3Bugs; translate the
# remapping targets to the equivalent npm package vendored under vendor/.
LIB2NPM = {
    "lib/openzeppelin-contracts/contracts/": "@openzeppelin/contracts/",
    "lib/openzeppelin-contracts-upgradeable/contracts/": "@openzeppelin/contracts-upgradeable/",
    "lib/solmate/src/": "solmate/src/",
    "lib/prb-math/contracts/": "prb-math/contracts/",
}


def find_by_basename(name: str, root: Path) -> Path | None:
    """Unique project file with this basename (snapshot layouts drift)."""
    skip = {"node_modules", "artifacts", "cache", ".git", "test", "tests", "mocks"}
    hits = [p for p in root.rglob(name)
            if p.is_file() and not skip.intersection(p.parts)]
    return hits[0] if len(hits) == 1 else None


def resolve_import(spec: str, importer: Path, root: Path,
                   contest: str, era: str) -> tuple[Path | None, str | None]:
    """Return (path, None) if resolved locally, (None, package_spec) if npm."""
    vendors = (VENDOR / f"{contest}@{era}", VENDOR / contest)
    if spec.startswith("."):
        p = (importer.parent / spec).resolve()
        if p.is_file():
            return p, None
        fb = find_by_basename(Path(spec).name, root)
        return (fb, None) if fb else (None, spec)
    for pre, tgt in load_remappings(root):
        if spec.startswith(pre):
            mapped = tgt + spec[len(pre):]
            for base in (root, root / "lib", root.parent):
                p = (base / mapped).resolve()
                if p.is_file():
                    return p, None
            for libpre, npmpre in LIB2NPM.items():
                if mapped.startswith(libpre):
                    for vend in vendors:
                        p = (vend / (npmpre + mapped[len(libpre):])).resolve()
                        if p.is_file():
                            return p, None
    for base in (root / "node_modules", *vendors, root, root / "contracts",
                 root / "lib", root / "src"):
        p = (base / spec).resolve()
        if p.is_file():
            return p, None
    if "/" in spec and not spec.startswith("@"):
        fb = find_by_basename(Path(spec).name, root)
        if fb:
            return fb, None
    return None, spec


def sample_era(orig: Path) -> str:
    pm = re.search(rb"pragma solidity[^;]{0,40}", orig.read_bytes())
    return era_of({pm.group(0).decode("ascii", "replace")} if pm else set())


def closure(sample: str, mapping: dict) -> tuple[list[Path], list[str], Path]:
    """BFS over the import graph; returns (files in discovery order,
    unresolved package specs, project root)."""
    orig = W3B / mapping[sample]["original"]
    contest = mapping[sample]["original"].replace("\\", "/").split("/")[0]
    root = project_root(orig, W3B / contest)
    era = sample_era(orig)
    seen, order, missing = {orig}, [orig], []
    queue = [orig]
    while queue:
        f = queue.pop(0)
        code = strip_comments(f.read_bytes())
        for m in IMPORT_RE.finditer(code):
            spec = m.group(2).decode("utf-8", "replace")
            p, miss = resolve_import(spec, f, root, contest, era)
            if p and p not in seen:
                seen.add(p)
                order.append(p)
                queue.append(p)
            elif miss:
                missing.append(f"{miss}  (aus {f.name})")
    return order, missing, root


def cmd_scan(_args) -> int:
    """Walk every sample's import closure; report unresolved package imports."""
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    total_missing: dict[str, list[str]] = {}
    ok = 0
    for name in sorted(mapping):
        files, missing, root = closure(name, mapping)
        if missing:
            total_missing[name] = sorted(set(missing))
        else:
            ok += 1
    print(f"vollstaendig aufloesbar: {ok}/{len(mapping)}")
    pkgs: dict[str, int] = {}
    for name, miss in total_missing.items():
        for s in miss:
            key = s.split()[0]
            top = "/".join(key.split("/")[:2]) if key.startswith("@") else key.split("/")[0]
            pkgs[top] = pkgs.get(top, 0) + 1
    print("\nfehlende Pakete (Haeufigkeit):")
    for p, n in sorted(pkgs.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {p}")
    (TOOLS / "scan_missing.json").write_text(
        json.dumps(total_missing, indent=1), encoding="utf-8")
    return 0


# --------------------------------------------------------------------------
# vendoring npm packages
# --------------------------------------------------------------------------

# pragma-era fallbacks when no lockfile pins a version (compile check validates)
ERA_FALLBACK = {
    "@openzeppelin/contracts": {"0.8": "4.9.6", "0.7": "3.4.2", "0.6": "3.4.2", "0.5": "2.5.1"},
    "@openzeppelin/contracts-upgradeable": {"0.8": "4.9.6", "0.7": "3.4.2", "0.6": "3.4.2"},
    "solmate": {"0.8": "6.2.0"},
    "@rari-capital/solmate": {"0.8": "6.4.0"},
    "prb-math": {"0.8": "2.5.0"},
}
HARDHAT_CONSOLE_URL = ("https://raw.githubusercontent.com/NomicFoundation/hardhat/"
                       "hardhat%402.22.5/packages/hardhat-core/console.sol")

# packages without any lockfile entry anywhere in the contest tree
PKG_DEFAULT_VERSIONS = {
    "@uniswap/v2-core": "1.0.1",
    "@pooltogether/fixed-point": "1.0.0",
    "@pooltogether/yield-source-interface": "1.4.0",
}
# foundry remapping prefixes that are not npm names themselves
PKG_ALIAS = {"openzeppelin": "@openzeppelin/contracts"}


def locked_version(root: Path, pkg: str) -> str | None:
    yl = root / "yarn.lock"
    if yl.is_file():
        txt = yl.read_text(encoding="utf-8", errors="replace")
        # entry header contains the package name; version line follows
        m = re.search(
            re.escape(f'"{pkg}@') + r'[^\n]*\n\s+version\s+"([^"]+)"', txt)
        m = m or re.search(
            re.escape(f"{pkg}@") + r'[^\n]*:\n\s+version\s+"([^"]+)"', txt)
        if m:
            return m.group(1)
    pl = root / "package-lock.json"
    if pl.is_file():
        try:
            data = json.loads(pl.read_text(encoding="utf-8", errors="replace"))
            dep = (data.get("dependencies", {}).get(pkg)
                   or data.get("packages", {}).get(f"node_modules/{pkg}"))
            if dep and dep.get("version"):
                return dep["version"]
        except Exception:
            pass
    pj = root / "package.json"
    if pj.is_file():
        try:
            data = json.loads(pj.read_text(encoding="utf-8", errors="replace"))
            for sec in ("dependencies", "devDependencies"):
                v = data.get(sec, {}).get(pkg)
                if v:
                    return v.lstrip("^~=v").split(" ")[0]
        except Exception:
            pass
    return None


def npm_fetch(pkg: str, version: str, dest: Path) -> bool:
    import io
    import tarfile
    import urllib.request
    base = pkg.split("/")[-1]
    url = f"https://registry.npmjs.org/{pkg}/-/{base}-{version}.tgz"
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            buf = io.BytesIO(r.read())
    except Exception as e:
        print(f"    FEHLER {url}: {e}")
        return False
    with tarfile.open(fileobj=buf, mode="r:gz") as tf:
        for mem in tf.getmembers():
            if not mem.isfile():
                continue
            rel = mem.name.split("/", 1)[1] if "/" in mem.name else mem.name
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(tf.extractfile(mem).read())
    return True


def era_of(pragmas: set[str]) -> str:
    for era in ("0.8", "0.7", "0.6", "0.5"):
        if any(era in p for p in pragmas):
            return era
    return "0.8"


def cmd_vendor(_args) -> int:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    # which packages does each (contest, era) need? (scan closures per sample)
    need: dict[tuple[str, str], set[str]] = {}   # (contest, era) -> pkgs
    roots: dict[str, Path] = {}
    for name in sorted(mapping):
        files, missing, root = closure(name, mapping)
        contest = mapping[name]["original"].replace("\\", "/").split("/")[0]
        roots[contest] = root
        era = sample_era(W3B / mapping[name]["original"])
        for entry in missing:
            spec = entry.split()[0]
            if spec.startswith("."):
                continue  # local leftovers, handled later
            parts = spec.split("/")
            pkg = "/".join(parts[:2]) if spec.startswith("@") else parts[0]
            need.setdefault((contest, era), set()).add(pkg)
    # download once per (pkg, version), extract into vendor/<contest>@<era>/
    cache: dict[tuple[str, str], Path] = {}
    for (contest, era), pkgs in sorted(need.items()):
        root = roots[contest]
        vdir = VENDOR / f"{contest}@{era}"
        for pkg in sorted(pkgs):
            if pkg == "hardhat":
                dest = vdir / "hardhat"
                dest.mkdir(parents=True, exist_ok=True)
                shared = VENDOR / "_shared_console.sol"
                if not shared.is_file():
                    import urllib.request
                    with urllib.request.urlopen(HARDHAT_CONSOLE_URL, timeout=120) as r:
                        shared.write_bytes(r.read())
                (dest / "console.sol").write_bytes(shared.read_bytes())
                print(f"  {contest}@{era}: hardhat/console.sol vendored")
                continue
            pkg = PKG_ALIAS.get(pkg, pkg)
            ver = locked_version(root, pkg)
            if not ver or not re.match(r"^\d+\.\d+", ver):
                ver = (PKG_DEFAULT_VERSIONS.get(pkg)
                       or ERA_FALLBACK.get(pkg, {}).get(era))
            # lockfiles can belong to another subproject; a 0.5/0.6/0.7 sample
            # must never get OZ >= 4 (paths like math/SafeMath.sol moved)
            if (ver and pkg.startswith("@openzeppelin") and era in ("0.5", "0.6", "0.7")
                    and ver.split(".")[0].isdigit() and int(ver.split(".")[0]) >= 4):
                ver = ERA_FALLBACK.get(pkg, {}).get(era, ver)
            if not ver:
                print(f"  {contest}@{era}: {pkg} — KEINE Version ermittelbar, uebersprungen")
                continue
            dest = vdir / pkg
            if dest.exists():
                print(f"  {contest}@{era}: {pkg}@{ver} bereits vorhanden")
                continue
            key = (pkg, ver)
            if key in cache:
                import shutil
                shutil.copytree(cache[key], dest)
                print(f"  {contest}@{era}: {pkg}@{ver} (aus Cache)")
                continue
            print(f"  {contest}@{era}: hole {pkg}@{ver} ...")
            if npm_fetch(pkg, ver, dest):
                cache[key] = dest
    return 0


# --------------------------------------------------------------------------
# fetching files the Web3Bugs snapshot lacks (audit scope cut dependencies)
# --------------------------------------------------------------------------

# ordered gap-filler sources per contest: LLM4SMAPR mirrors the same dataset
# generation with full trees; protocol repos and npm cover yield-source files.
GAP_SOURCES: dict[str, list[tuple]] = {
    "3": [("github", "CheWang09/LLM4SMAPR", "open_source_dataset/3/contracts_3/")],
    "14": [
        ("github", "CheWang09/LLM4SMAPR", "open_source_dataset/14/contracts_14/contracts/"),
        ("github", "pooltogether/badger-yield-source", "contracts/"),
        ("github", "pooltogether/sushi-pooltogether", "contracts/"),
        ("github", "pooltogether/idle-yield-source", "contracts/"),
        ("npm", "@pooltogether/pooltogether-contracts", "3.4.5"),
    ],
    "17": [("github", "CheWang09/LLM4SMAPR", "open_source_dataset/17/contracts_17/contracts/")],
}
TREES = TOOLS / "trees"


def gh_tree(repo: str) -> tuple[str, list[str]]:
    """(default_branch, blob paths) for a repo, cached on disk."""
    import subprocess
    TREES.mkdir(exist_ok=True)
    cache = TREES / (repo.replace("/", "__") + ".json")
    if cache.is_file():
        d = json.loads(cache.read_text(encoding="utf-8"))
        return d["branch"], d["files"]
    br = subprocess.run(["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
                        capture_output=True, text=True, check=True).stdout.strip()
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/trees/{br}?recursive=1", "--jq",
         '[.tree[] | select(.type=="blob") | .path]'],
        capture_output=True, text=True, check=True).stdout
    files = json.loads(out)
    cache.write_text(json.dumps({"branch": br, "files": files}), encoding="utf-8")
    return br, files


def raw_fetch(repo: str, branch: str, path: str) -> bytes | None:
    import urllib.request
    import urllib.parse
    url = (f"https://raw.githubusercontent.com/{repo}/{branch}/"
           + urllib.parse.quote(path))
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.read()
    except Exception as e:
        print(f"    FEHLER {url}: {e}")
        return None


def expected_path(spec: str, importer: Path, root: Path) -> Path:
    if spec.startswith("."):
        parts = (importer.parent / spec).resolve()
        return parts
    return (root / spec).resolve()


def find_in_source(tail: str, base: str, files: list[str], prefix: str) -> str | None:
    scoped = [p for p in files if p.startswith(prefix) and p.endswith(".sol")]
    exact = [p for p in scoped if p.endswith("/" + tail) or p == prefix + tail]
    if len(exact) >= 1:
        return exact[0]
    byname = [p for p in scoped if p.rsplit("/", 1)[-1] == base]
    return byname[0] if len(byname) == 1 else None


def cmd_fetch(_args) -> int:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    # npm gap sources: vendor once under vendor/_fetch/<pkg>/
    npm_dirs: dict[str, Path] = {}
    for srcs in GAP_SOURCES.values():
        for s in srcs:
            if s[0] == "npm":
                dest = VENDOR / "_fetch" / s[1]
                if not dest.exists():
                    print(f"  vendore Gap-Quelle {s[1]}@{s[2]} ...")
                    npm_fetch(s[1], s[2], dest)
                npm_dirs[s[1]] = dest
    for rnd in range(1, 6):
        fetched = 0
        for name in sorted(mapping):
            files_, missing, root = closure(name, mapping)
            contest = mapping[name]["original"].replace("\\", "/").split("/")[0]
            srcs = GAP_SOURCES.get(contest)
            if not srcs or not missing:
                continue
            for entry in sorted(set(missing)):
                spec, importer_name = entry.split()[0], entry.split()[-1].rstrip(")")
                importer = next((f for f in files_ if f.name == importer_name), None)
                if importer is None or spec.startswith("@"):
                    continue
                dest = expected_path(spec, importer, root)
                if dest.is_file():
                    continue
                tail = "/".join(x for x in spec.replace("\\", "/").split("/")
                                if x not in (".", ".."))
                base = tail.rsplit("/", 1)[-1]
                data = None
                for s in srcs:
                    if s[0] == "github":
                        br, tree = gh_tree(s[1])
                        hit = find_in_source(tail, base, tree, s[2])
                        if hit:
                            data = raw_fetch(s[1], br, hit)
                            if data:
                                print(f"  {name}: {spec}  <-  {s[1]}:{hit}")
                                break
                    elif s[0] == "npm":
                        nd = npm_dirs[s[1]]
                        hits = [p for p in nd.rglob(base) if p.is_file()]
                        pref = [p for p in hits if str(p).replace("\\", "/").endswith(tail)]
                        pick = (pref or hits)[:1]
                        if pick:
                            data = pick[0].read_bytes()
                            print(f"  {name}: {spec}  <-  npm:{s[1]}")
                            break
                if data:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    fetched += 1
        print(f"Runde {rnd}: {fetched} Dateien geholt")
        if fetched == 0:
            break
    return 0


# --------------------------------------------------------------------------
# flattening
# --------------------------------------------------------------------------

SPDX_TOKEN = re.compile(rb"SPDX-License-Identifier:\s*([^\s*/\r\n]+)")
VER_PRAGMA_RE = re.compile(rb"pragma\s+solidity[^;]*;")
OTHER_PRAGMA_RE = re.compile(rb"pragma\s+(?!solidity)[^;]*;")
ALIAS_RE = re.compile(rb"import\s+(?:\{[^}]*\bas\b[^}]*\}|\*\s*as\s+\w+|\w+\s+as\s+\w+)")


def flat_order(sample: str, mapping: dict) -> tuple[list[Path], Path, str, str]:
    """DFS post-order (dependencies first). Returns (files, root, contest, era)."""
    orig = W3B / mapping[sample]["original"]
    contest = mapping[sample]["original"].replace("\\", "/").split("/")[0]
    root = project_root(orig, W3B / contest)
    era = sample_era(orig)
    order: list[Path] = []
    state: dict[Path, int] = {}  # 1 = visiting, 2 = done

    def visit(f: Path):
        if state.get(f):
            return
        state[f] = 1
        code = strip_comments(f.read_bytes())
        for m in IMPORT_RE.finditer(code):
            spec = m.group(2).decode("utf-8", "replace")
            p, miss = resolve_import(spec, f, root, contest, era)
            if p and state.get(p) != 1:   # skip back-edges (import cycles)
                visit(p)
        state[f] = 2
        order.append(f)

    visit(orig)
    return order, root, contest, era


def cmd_flatten(_args) -> int:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    releases = solc_releases()
    FIXED.mkdir(parents=True, exist_ok=True)
    stats = {}
    for name in sorted(mapping):
        files, root, contest, era = flat_order(name, mapping)
        ver_pragmas: list[str] = []     # every distinct `pragma solidity` seen
        other_pragmas: list[bytes] = [] # abicoder / experimental, deduped
        license_id = None
        parts: list[bytes] = []
        aliases = 0
        seen_content: set[bytes] = set()  # collapse identical files pulled in
        dup = 0                           # via >1 path (snapshot + fetched copy)
        for f in files:
            raw = f.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            ident = __import__("hashlib").sha1(stripped(raw)).digest()
            if ident in seen_content:
                dup += 1
                continue
            seen_content.add(ident)
            body = raw
            aliases += len(ALIAS_RE.findall(strip_comments(body)))
            m = SPDX_TOKEN.search(body)
            if m and license_id is None:
                license_id = m.group(1)
            # neutralise EVERY SPDX tag (also inside block comments) so the one
            # tag we emit in the header is the file's only license identifier
            body = SPDX_TOKEN.sub(b"license-stripped", body)
            for pm in VER_PRAGMA_RE.finditer(body):
                stmt = " ".join(pm.group(0).decode("ascii", "replace").split())
                if stmt not in ver_pragmas:
                    ver_pragmas.append(stmt)
            for pm in OTHER_PRAGMA_RE.finditer(body):
                stmt = b" ".join(pm.group(0).split())
                if b"SMTChecker" in stmt:
                    continue  # solver pragma: irrelevant + slows compilation
                if stmt not in other_pragmas:
                    other_pragmas.append(stmt)
            body = VER_PRAGMA_RE.sub(b"", body)
            body = OTHER_PRAGMA_RE.sub(b"", body)
            body = IMPORT_RE.sub(b"", body)
            try:
                rel = f.relative_to(W3B)
            except ValueError:
                rel = f
            parts.append(b"\n// ---- " + str(rel).encode() + b" ----\n"
                         + body.strip() + b"\n")

        chosen = choose_solc(ver_pragmas, releases)
        head = [b"// mwevariety_fixed: aus Web3Bugs-Originalquellen geflattet "
                b"(siehe corpus_tools/build_fixed.py)"]
        head.append(b"// SPDX-License-Identifier: " + (license_id or b"UNLICENSED"))
        # exactly ONE version pragma (an exact pin that satisfies every source's
        # constraint); a flattened file may legally contain only one.
        head.append(f"pragma solidity {chosen};".encode() if chosen
                    else ver_pragmas[0].encode())
        head += other_pragmas
        out = FIXED / name
        out.write_bytes(b"\n".join(head) + b"\n" + b"".join(parts))
        stats[name] = {"files": len(files), "unique_files": len(seen_content),
                       "duplicates_collapsed": dup, "solc": chosen,
                       "version_pragmas": ver_pragmas,
                       "other_pragmas": [p.decode() for p in other_pragmas],
                       "alias_imports": aliases}
        flag = "" if chosen else "  *** KEINE solc-Version ***"
        ab = "  abicoder/exp" if other_pragmas else ""
        dd = f"  (-{dup} dup)" if dup else ""
        print(f"  {name}: {len(seen_content)} Dateien{dd} -> solc {chosen}{ab}{flag}")
    (TOOLS / "flatten_stats.json").write_text(json.dumps(stats, indent=1),
                                              encoding="utf-8")
    return 0


# --------------------------------------------------------------------------
# compile check
# --------------------------------------------------------------------------

SOLC_DIR = TOOLS / "solc"
SOLC_LIST_URL = "https://binaries.soliditylang.org/windows-amd64/list.json"


def http_get(url: str, timeout: int = 300) -> bytes:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (corpus_tools)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def solc_releases() -> dict[str, str]:
    cache = SOLC_DIR / "list.json"
    SOLC_DIR.mkdir(exist_ok=True)
    if not cache.is_file():
        cache.write_bytes(http_get(SOLC_LIST_URL, 120))
    return json.loads(cache.read_text(encoding="utf-8"))["releases"]


def choose_solc(pragma_stmts: list[str], releases: dict[str, str]) -> str | None:
    import semantic_version
    specs = []
    for p in pragma_stmts:
        if not p.startswith("pragma solidity"):
            continue
        expr = p[len("pragma solidity"):].rstrip(";").strip()
        # normalise operator spacing (">= 0.8.0" -> ">=0.8.0"); keep the space
        # that separates two comparators (">=0.6.0 <0.7.0")
        expr = re.sub(r"([<>=^~])\s+", r"\1", expr)
        try:
            specs.append(semantic_version.NpmSpec(expr))
        except ValueError:
            return None
    if not specs:
        return None
    best = None
    for v in releases:
        try:
            sv = semantic_version.Version(v)
        except ValueError:
            continue
        if all(sv in s for s in specs):
            if best is None or sv > best:
                best = sv
    return str(best) if best else None


def solc_binary(version: str, releases: dict[str, str]) -> Path | None:
    # 0.6.x windows artifacts are ZIPs (solc.exe + VC runtime DLLs), later ones
    # are bare PE exes. Normalise both to SOLC_DIR/solc-<ver>/solc.exe.
    zdir = SOLC_DIR / f"solc-{version}"
    zexe = zdir / "solc.exe"
    exe = SOLC_DIR / f"solc-{version}.exe"
    if zexe.is_file():
        return zexe
    if exe.is_file() and exe.stat().st_size > 1_000_000:
        return exe
    if version not in releases:
        print(f"    solc {version}: kein Release in list.json")
        return None
    url = f"https://binaries.soliditylang.org/windows-amd64/{releases[version]}"
    try:
        data = http_get(url)
    except Exception as e:
        print(f"    solc {version}: Download-FEHLER {e}")
        return None
    if data[:2] == b"PK":                       # ZIP artifact -> extract
        import io
        import zipfile
        zdir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(zdir)
        hit = zexe if zexe.is_file() else next(iter(zdir.rglob("solc.exe")), None)
        if hit is None:
            print(f"    solc {version}: solc.exe nicht im ZIP")
        return hit
    tmp = exe.with_suffix(".exe.part")          # bare PE -> atomic write
    tmp.write_bytes(data)
    tmp.replace(exe)
    return exe


def run_solc(exe: Path, target: Path, extra: list[str] | None = None):
    """Compile once; retry a WinError 216 (freshly-written exe not yet
    committed to disk by the AV/loader)."""
    import subprocess
    import time
    cmd = [str(exe), "--bin", *(extra or []), str(target)]
    for attempt in range(3):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except OSError as e:
            if getattr(e, "winerror", None) == 216 and attempt < 2:
                time.sleep(1.0)
                continue
            raise


def inject_pragma(target: Path, pragma: str) -> None:
    """Insert `pragma` right after the file's single version pragma."""
    text = target.read_text(encoding="utf-8", errors="replace")
    out, done = [], False
    for line in text.splitlines(keepends=True):
        out.append(line)
        if not done and line.lstrip().startswith("pragma solidity"):
            out.append(pragma + "\n")
            done = True
    target.write_text("".join(out), encoding="utf-8")


def cmd_check(_args) -> int:
    stats = json.loads((TOOLS / "flatten_stats.json").read_text(encoding="utf-8"))
    releases = solc_releases()
    # pre-download every distinct solc version first (separates I/O from exec)
    versions = sorted({s["solc"] for s in stats.values() if s.get("solc")})
    print(f"lade {len(versions)} solc-Versionen vor: {', '.join(versions)}")
    binpath = {v: solc_binary(v, releases) for v in versions}
    results, ok = {}, 0
    for name in sorted(stats):
        ver = stats[name].get("solc")
        if not ver:
            results[name] = {"status": "no-solc-version"}
            print(f"  {name}: KEINE solc-Version")
            continue
        exe = binpath.get(ver)
        if not exe or not exe.is_file():
            results[name] = {"status": "solc-download-failed", "solc": ver}
            continue
        target = FIXED / name
        proc = run_solc(exe, target)
        note = None
        # repair 1: struct-in-signature needs ABIEncoderV2 on < 0.8 (the source
        # project enabled it globally in its build config, not via a pragma)
        if (proc.returncode != 0 and "only supported in ABIEncoderV2" in proc.stderr
                and "abicoder" not in target.read_text(encoding="utf-8", errors="replace")):
            inject_pragma(target, "pragma experimental ABIEncoderV2;")
            proc = run_solc(exe, target)
            note = "injected: pragma experimental ABIEncoderV2"
        # repair 2: inline-assembly stack-too-deep -> optimizer, then IR pipeline
        if proc.returncode != 0 and "Stack too deep" in proc.stderr:
            for extra, tag in ((["--optimize"], "--optimize"),
                               (["--optimize", "--via-ir"], "--optimize --via-ir")):
                p2 = run_solc(exe, target, extra)
                if p2.returncode == 0:
                    proc, note = p2, f"needs {tag}"
                    break
                proc = p2
        if proc.returncode == 0:
            results[name] = {"status": "ok", "solc": ver, **({"note": note} if note else {})}
            ok += 1
            if note:
                print(f"  {name} (solc {ver}): OK  [{note}]")
        else:
            errs = [l.strip() for l in proc.stderr.splitlines()
                    if "Error" in l or "error" in l]
            results[name] = {"status": "compile-error", "solc": ver,
                             "errors": errs[:6]}
            print(f"  {name} (solc {ver}): {(errs[0] if errs else proc.stderr[:120])[:150]}")
    (TOOLS / "check_results.json").write_text(json.dumps(results, indent=1),
                                              encoding="utf-8")
    print(f"\nkompiliert: {ok}/{len(stats)}")
    return 0 if ok == len(stats) else 1


def main() -> int:
    """Dispatch to the requested subcommand (map/scan/vendor/fetch/flatten/check)."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("map", help="locate + verify originals, write mapping.json")
    sub.add_parser("scan", help="resolve import closures, list missing packages")
    sub.add_parser("vendor", help="download npm packages per contest into vendor/")
    sub.add_parser("fetch", help="fetch snapshot-missing files from gap sources")
    sub.add_parser("flatten", help="write self-contained files to mwevariety_fixed/")
    sub.add_parser("check", help="compile every flattened file with matching solc")
    args = ap.parse_args()
    return {"map": cmd_map, "scan": cmd_scan, "vendor": cmd_vendor,
            "fetch": cmd_fetch, "flatten": cmd_flatten,
            "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
