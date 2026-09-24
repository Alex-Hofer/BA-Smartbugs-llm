#!/usr/bin/env python3
"""Legt eine Kopie des Korpus ``mwevariety_fixed`` an, in der jede Datei nach
ihrem Hauptcontract heisst -- die Voraussetzung fuer SmartBugs' ``--main``.

Hintergrund
-----------
SmartBugs setzt ``--main`` beim Einsammeln der Tasks selbst durch
(``sb/smartbugs.py``: der Dateiname ohne ``.sol`` muss exakt einem Contract der
Datei entsprechen) und bricht sonst ab. Im reparierten Korpus heissen die
Dateien ``<contest>_<Contract>.sol`` (``106_NFTLoanFacilitator.sol``); diese
Pruefung bestand deshalb keine einzige Datei, und die MAIN-Reduktion in den
Entrypoints der beiden KI-Scanner (``scripts/main_contract.py``) wurde fuer
LLMSmartAudit nie erreicht (``run_full_v2_llmsa.ps1``, Kopfkommentar).

Was das Skript tut
------------------
Fuer jede gewuenschte Datei liest es aus ``corpus_tools/mapping.json`` den
Originalpfad (``original``), nimmt dessen Dateinamen als Hauptcontract und
prueft, dass die Datei einen Contract dieses Namens deklariert. Die Kopie
landet unter ``smartbugs/samples/gptscan/mwevariety_fixed_main/<contest>/<Contract>.sol``.
Der Contest-Unterordner ist noetig, weil Hauptcontracts mehrfach vorkommen
(``13_RCOrderbook`` und ``26_RCOrderbook`` heissen beide ``RCOrderbook``).
Die Dateien werden byte-identisch kopiert; die Reduktion auf den Hauptcontract
erledigt spaeter der Entrypoint im Container.

Das Zielverzeichnis ist nicht versioniert (es enthaelt nur Kopien); das Skript
erzeugt es jederzeit neu.

Aufruf (aus dem Repo-Root)::

    python corpus_tools/make_main_corpus.py                      # alle 96
    python corpus_tools/make_main_corpus.py 30_Vault 67_Vault    # Auswahl

SmartBugs-Aufruf danach (aus ``smartbugs/``), mit ``${RELDIR}`` im
Ergebnispfad, damit gleichnamige Hauptcontracts nicht kollidieren::

    python -m sb -t llmsmartaudit -f "samples/gptscan/mwevariety_fixed_main:**/*.sol" --main \\
        --results "results/${TOOL}/<runid>/${RELDIR}/${FILENAME}" --runid <runid> ...
"""

import json
import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "smartbugs" / "samples" / "gptscan" / "mwevariety_fixed"
DST = REPO / "smartbugs" / "samples" / "gptscan" / "mwevariety_fixed_main"
MAPPING = REPO / "corpus_tools" / "mapping.json"
DECL = re.compile(r"\b(?:contract|library|interface)\s+(\w+)")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    argv = [a.strip() for a in argv if a.strip()]
    wanted = [a if a.endswith(".sol") else a + ".sol" for a in argv] or sorted(mapping)
    written, skipped = [], []
    for name in wanted:
        entry = mapping.get(name)
        if not entry:
            skipped.append((name, "nicht in mapping.json"))
            continue
        stem = pathlib.PureWindowsPath(entry["original"]).stem
        source = (SRC / name).read_text(encoding="utf-8", errors="replace")
        if stem not in set(DECL.findall(source)):
            skipped.append((name, "kein Contract %r in der Datei" % stem))
            continue
        contest = name.split("_", 1)[0]
        target = DST / contest / (stem + ".sol")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / name, target)
        written.append((name, str(target.relative_to(REPO))))
    for name, target in written:
        print("%-40s -> %s" % (name, target))
    for name, why in skipped:
        print("UEBERSPRUNGEN %-26s %s" % (name, why))
    print("%d Dateien geschrieben, %d uebersprungen, Ziel %s" % (len(written), len(skipped), DST))
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
