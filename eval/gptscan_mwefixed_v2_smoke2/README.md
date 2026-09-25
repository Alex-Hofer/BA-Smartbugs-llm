# eval/gptscan_mwefixed_v2_smoke2/ — zweite Live-Stichprobe, drei andere Contracts

Gegenprobe zur ersten Stichprobe (`gptscan_mwefixed_v2_smoke`), die auf ihren
drei Contracts nichts fand. Zweck war die Frage, ob das an der Pipeline oder an
der Auswahl lag. **Kein Messergebnis über den Korpus.**

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `gptscan_mwefixed_v2_smoke2` |
| Werkzeug | GPTScan, Image `smartbugs/gptscan:1.0` |
| Modell | `deepseek/deepseek-v4-flash` |
| Contracts | `14_BadgerYieldSource.sol`, `5_Router.sol`, `71_IndexTemplate.sol` aus `mwevariety_fixed` |
| Parameter | `--processes 3`, `--timeout 1800`, `--mem-limit 4g`, MAIN aktiv |
| Wanduhr | 352,8 s |
| Durchführung | 15.08.2026, Git-Commit `58971ba`, Skript `run_full_v2.ps1`; Auswertung nachgezogen am 17.08.2026 |
| Rohergebnisse | `smartbugs/results/gptscan/gptscan_mwefixed_v2_smoke2/` (`result.json` und `smartbugs.json` je Task versioniert; Logs und Archive im Release-Zip, siehe README „Wo die Ergebnisse liegen“) |

## Wie die Dateien entstanden sind

```powershell
.\run_full_v2.ps1 -Mode smoke
python analysis_tools\gptscan_eval.py gptscan_mwefixed_v2_smoke2
```

## Kernzahlen

| | |
|---|---:|
| Contracts | 3 |
| Findings | 6 |
| Kosten | $0,0272 |
| Tasks mit `errors` | 2 |
| Tasks mit `fails` | 0 |
| ohne Findings, sauber | 1 |

## Was man daraus schließen darf

* Dass die Live-Kette Findings erzeugt und der Parser sie korrekt überträgt —
  die 0 Findings der ersten Stichprobe lagen an der Auswahl, nicht an der
  Pipeline.

## Was man daraus nicht schließen darf

1. **Sechs Findings auf drei Contracts sind keine Trefferquote.** Die Auswahl
   fiel bewusst auf Contracts, bei denen Findings erwartbar waren.
2. **Der Unterschied zur ersten Stichprobe misst nicht den Nicht-Determinismus.**
   Es sind andere Contracts; ein Wiederholungslauf über dieselben Contracts
   wurde hier nicht gefahren. Die Reproduzierbarkeitszahl steht in
   `docs/BA-GPTSCAN-VERGLEICH.md`, Abschnitt 4.
3. **Logs und Archive liegen nicht im Repository** (nur `result.json` und
   `smartbugs.json` je Task, Rest im Release-Zip, README „Wo die Ergebnisse
   liegen“), und ein Nachfahren erzeugt keine bitgleichen Ergebnisse.
