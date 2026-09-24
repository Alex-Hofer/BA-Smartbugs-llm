# Slither 0.11.3 auf einer glibc-Basis (Debian bookworm) statt Alpine/musl.
# Grund und Kontext: config.yaml in diesem Verzeichnis, docs/BA-BETRIEB.md
# Fallstrick 10. Kein solc im Image: SmartBugs reicht die passende Version
# als $BIN/solc in den Container.
#
# Bauen (aus dem Repo-Wurzelverzeichnis):
#   docker build -t smartbugs/slither:0.11.3-glibc smartbugs/tools/slither-0.11.3-glibc
FROM python:3.12-slim-bookworm
RUN pip install --no-cache-dir slither-analyzer==0.11.3
WORKDIR /sb
