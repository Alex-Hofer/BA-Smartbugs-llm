# eval/gptscan_mwefixed_v2_main/ — GPTScan-Volllauf über `mwevariety_fixed` mit MAIN

Der Hauptlauf dieses Ordners ist der **erste GPTScan-Lauf mit `--main`**. Er ist
damit die Referenz für die Frage, was der MAIN-Parameter (AP6) an den Ergebnissen
ändert.

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `gptscan_mwefixed_v2_main`, zusammengeführt mit dem Nachlauf `gptscan_mwefixed_v2_main_nomain` |
| Werkzeug | GPTScan, Image `smartbugs/gptscan:1.0` |
| Modell | `deepseek/deepseek-v4-flash` |
| Korpus | `smartbugs/samples/gptscan/mwevariety_fixed/`, 96 DeFi-Contracts |
| Parameter | `--processes 4`, `--timeout 1800`, `--mem-limit 4g`, MAIN aktiv mit Fallback |
| Wanduhr | 3 055 s (50:55 min), Task-Summe 11 771,7 s |
| Durchführung | 15.08.2026, Git-Commit `58971ba`, Skript `run_full_v2.ps1` |
| Rohergebnisse | `smartbugs/results/gptscan/gptscan_mwefixed_v2_main/` (git-ignoriert) |

Die genauen Aufrufparameter samt SHA1 aller beteiligten Tool-Dateien stehen in
`run_params.json`. Der Nachlauf `_nomain` wiederholt die drei Contracts, die im
Hauptlauf mit Exit-Code 127 endeten (`31_veCVXStrategy`, `62_Locke`,
`8_NFTXEligiblityManager`), ohne MAIN; er ersetzt genau diese drei Tasks.

## Wie die Dateien entstanden sind

```powershell
.\run_full_v2.ps1 -Mode full -MainFallback
python analysis_tools\gptscan_eval.py gptscan_mwefixed_v2_main `
    --merge-run gptscan_mwefixed_v2_main_nomain
```

Der zweite Schritt liest nur; er setzt keinen API-Aufruf ab.

## Was in den Dateien steht

| Datei | Inhalt |
|---|---|
| `run_params.json` | Aufrufparameter, Versionen, SHA1 der Tool-Dateien, Git-Commit — vom Runner geschrieben, **vor** der Auswertung |
| `findings.jsonl` | eine Zeile je Finding: Contract, MWE-Regel, Funktion, Zeilen, Severity, Begründung, Empfehlung |
| `run_meta.json` | Zustände, Token, Kosten, Laufzeiten, Fehlerliste, Vergleich gegen den Referenzlauf |
| `summary.md` | dieselben Zahlen als Tabellen |
| `comparison_curated_mwefixed_live.md` | Finding-für-Finding-Vergleich gegen den Referenzlauf ohne MAIN |

Die Spaltenbedeutung von `findings.jsonl` ist dieselbe wie in den übrigen
GPTScan-Ordnern: `mwe` und `gptscan_code` sind die Regelkennung, `dasp10` und
`swc` bleiben leer, wo `smartbugs/tools/gptscan/findings.yaml` die Regel bewusst
als `BUSINESS-LOGIC (no SWC/DASP)` führt — das betrifft 8 der 10 Regeln.

## Kernzahlen

| | |
|---|---:|
| Contracts | 96 |
| Findings | 74 auf 37 Contracts |
| Kosten | $0,3638 |
| Tasks mit `errors` | 31 (32,3 %) |
| Tasks mit `fails` | 0 |
| nicht übersetzt (degraded) | 1 |
| ohne Findings, sauber | 58 |

## Was man daraus schließen darf

* Wie sich GPTScans Ergebnisse auf dem reparierten Korpus verteilen, wenn der
  MAIN-Parameter aktiv ist.
* Wie stark sich zwei Läufe desselben Werkzeugs auf demselben Korpus
  unterscheiden: `comparison_curated_mwefixed_live.md` weist 75,3 % der
  Referenz-Findings als reproduziert aus.

## Was man daraus nicht schließen darf

1. **Der Vergleich gegen `curated_mwefixed_live` ist kein sauberes Experiment.**
   Er vermischt zwei Ursachen: den MAIN-Parameter und die Nicht-Determinismus
   des Modells. Die 75,3 % sind deshalb eine Obergrenze für den MAIN-Effekt und
   zugleich eine Untergrenze für die Streuung.
2. **Keine Ground Truth.** `mwevariety_fixed` besitzt keinen annotierten
   Referenzstand. Recall und Precision lassen sich hier nicht bilden, nur die
   Verteilung beschreiben.
3. **Eine Errorquote von 32,3 % ist kein Scheitern.** `errors` heißt: Das
   Werkzeug hat ein Problem bemerkt, abgefangen und weitergearbeitet. Die
   Abgrenzung zu `fails` steht in `docs/BA-ERRORS-VS-FAILS.md`. Der größte
   Einzelposten ist `Static analysis failed: Invalid args` — GPTScans statische
   Stufe stürzt auf einem Teil der übersetzbaren Contracts ab
   (`docs/Update_Bericht.md`).
4. **Der eine degradierte Contract ist kein „sauberes" Ergebnis.** Er wurde nicht
   übersetzt; sein Befund ist unbestimmt.
5. **Die Kostenangabe ist GPTScans eigene Schätzung** aus `GPTSCAN_META`, nicht
   die Abrechnung des Anbieters.
6. **Die Rohergebnisse liegen nicht im Repository.** In einem frischen Clone
   existiert `smartbugs/results/` nicht; was hier liegt, ist die einzige
   versionierte Fassung dieses Laufs. Ein Nachfahren erzeugt keine bitgleichen
   Ergebnisse.
