"""Auswertungswerkzeuge fuer den SmartBugs-Benchmark dieser Bachelorarbeit.

Alle Module hier sind eigener Code (kein SmartBugs-Upstream) und arbeiten
ausschliesslich lesend auf ``smartbugs/results`` --- mit einer Ausnahme:
:mod:`analysis_tools.redact_results` schreibt, und zwar nur den API-Schluessel
in den Task-Logs. Die Exporte legen ihre abgeleiteten Daten unter ``eval/`` ab,
nie unter ``smartbugs/results``.

=========================================  ===============================================
:mod:`~analysis_tools.rawlog`             Rohmaterial lesen, ``rich``-Logs entzerren
:mod:`~analysis_tools.parser_audit`       Lueckenbericht: was verlieren die Parser?
:mod:`~analysis_tools.errors_fails_report` Errors/Fails getrennt ausgeben
:mod:`~analysis_tools.redact_results`     API-Schluessel aus Alt-Ergebnissen entfernen
:mod:`~analysis_tools.secret_scan`        Leak-Vorsorge fuer kuenftige Commits
:mod:`~analysis_tools.compare_csv`        zwei ``sb.results2csv``-Exporte vergleichen, etwa vor und nach einer Parseraenderung
:mod:`~analysis_tools.gptscan_run_stats`  GPTSCAN_META-Zeilen eines Laufs zu Token-, Kosten- und Laufzeitkennzahlen summieren
:mod:`~analysis_tools.gptscan_eval`       GPTScan-Lauf nach ``eval/<runid>/`` exportieren, gegen einen Altlauf vergleichen, ``eval/README.md`` fortschreiben
:mod:`~analysis_tools.build_eval`         LLMSmartAudit-Lauf nach ``eval/<runid>/`` exportieren, Nachlauf per ``--merge-run`` einfalten
:mod:`~analysis_tools.curated_eval`       curated-Hauptlauf je Werkzeug auswerten, Recall/Precision/F1 je DASP-Kategorie
:mod:`~analysis_tools.per_contract_stats` eine CSV-Zeile je Contract (und je Phase) nach ``eval/per_contract/``
=========================================  ===============================================
"""
