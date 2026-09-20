# eval/gptscan_mwefixed_v2_smoke/ — erste Live-Stichprobe vor dem Volllauf

Drei Contracts mit echten API-Aufrufen, gefahren als Kostengate vor dem
Volllauf. **Kein Messergebnis über den Korpus.**

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `gptscan_mwefixed_v2_smoke` |
| Werkzeug | GPTScan, Image `smartbugs/gptscan:1.0` |
| Modell | `deepseek/deepseek-v4-flash` |
| Contracts | `25_CTokenInterface.sol`, `14_IdleYieldSource.sol`, `23_nTokenAction.sol` aus `mwevariety_fixed` |
| Parameter | `--processes 3`, `--timeout 1800`, `--mem-limit 4g`, MAIN aktiv |
| Wanduhr | 298,2 s |
| Durchführung | 15.08.2026, Git-Commit `58971ba`, Skript `run_full_v2.ps1` |
| Rohergebnisse | `smartbugs/results/gptscan/gptscan_mwefixed_v2_smoke/` (git-ignoriert) |

## Wie die Dateien entstanden sind

```powershell
.\run_full_v2.ps1 -Mode smoke
python analysis_tools\gptscan_eval.py gptscan_mwefixed_v2_smoke
```

## Kernzahlen

| | |
|---|---:|
| Contracts | 3 |
| Findings | 0 |
| Kosten | $0,0177 |
| Tasks mit `errors` | 2 |
| Tasks mit `fails` | 0 |
| ohne Findings, sauber | 3 |

## Was man daraus schließen darf

* Dass die Live-Kette mit echtem Schlüssel und echtem Endpunkt funktioniert.
* Eine belastbare Kostenschätzung je Contract für die Hochrechnung auf den
  Volllauf: $0,0177 für drei Contracts.

## Was man daraus nicht schließen darf

1. **„0 Findings" heißt hier nichts.** Drei Contracts sind keine Stichprobe, aus
   der sich eine Trefferquote ableiten ließe. Der zweite Smoke-Lauf
   (`gptscan_mwefixed_v2_smoke2`) fand auf drei anderen Contracts 6 Findings.
2. **Die Kosten skalieren nicht linear.** Die Contracts unterscheiden sich stark
   in Größe und in der Zahl der Funktionen, die den Vorfilter passieren.
3. **Zwei Tasks mit `errors` sind kein Defekt.** Das Werkzeug hat ein Problem
   bemerkt, abgefangen und weitergearbeitet (`docs/BA-ERRORS-VS-FAILS.md`).
4. **Die Rohergebnisse liegen nicht im Repository** und ein Nachfahren erzeugt
   keine bitgleichen Ergebnisse.
