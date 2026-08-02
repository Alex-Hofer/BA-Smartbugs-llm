"""Auswertungswerkzeuge fuer den SmartBugs-Benchmark dieser Bachelorarbeit.

Alle Module hier sind eigener Code (kein SmartBugs-Upstream) und arbeiten
ausschliesslich lesend auf ``smartbugs/results`` --- mit einer Ausnahme:
:mod:`analysis_tools.redact_results` schreibt, und zwar nur den API-Schluessel
in den Task-Logs.

============================  ===============================================
:mod:`~analysis_tools.rawlog`             Rohmaterial lesen, ``rich``-Logs entzerren
:mod:`~analysis_tools.parser_audit`       Lueckenbericht: was verlieren die Parser?
:mod:`~analysis_tools.errors_fails_report` Errors/Fails getrennt ausgeben
:mod:`~analysis_tools.redact_results`     API-Schluessel aus Alt-Ergebnissen entfernen
:mod:`~analysis_tools.secret_scan`        Leak-Vorsorge fuer kuenftige Commits
============================  ===============================================
"""
