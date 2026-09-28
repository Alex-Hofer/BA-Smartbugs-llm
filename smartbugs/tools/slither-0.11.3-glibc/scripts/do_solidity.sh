#!/bin/sh
# Entrypoint fuer Slither 0.11.3 im eigenen glibc-Image
# smartbugs/slither:0.11.3-glibc (Dockerfile im Werkzeugverzeichnis eine
# Ebene hoeher). SmartBugs ruft ihn laut config.yaml mit denselben drei
# Argumenten auf wie den Upstream-Entrypoint
# smartbugs/tools/slither-0.11.3/scripts/do_solidity.sh:
#   FILENAME  der zu analysierende .sol-Pfad im Container
#   TIMEOUT   das SmartBugs-Zeitlimit in Sekunden (hier nicht ausgewertet)
#   BIN       das Verzeichnis, in das SmartBugs scripts/ und den passenden
#             solc kopiert
#
# Unterschied zum Upstream-Entrypoint (diff der beiden Dateien): einzig die
# Zeile
#   export PYTHONPATH=/home/slither/.local/lib/python3.10/site-packages
# fehlt hier. Das Debian-Image installiert slither-analyzer per pip in das
# System-Python; einen Benutzer-site-Pfad gibt es dort nicht.
#
# parser.py und findings.yaml im Werkzeugverzeichnis sind unveraenderte Kopien
# aus smartbugs/tools/slither-0.11.3/.

FILENAME="$1"
TIMEOUT="$2"
BIN="$3"

export PATH="$BIN:$PATH"
chmod +x "$BIN/solc"

CMD="slither $FILENAME --json /output.json"
echo "$CMD" >> $BIN/log
$CMD
