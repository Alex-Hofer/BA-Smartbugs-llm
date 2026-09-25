# eval/gptscan_mwefixed_v2_dry/ — Pipelinetest ohne einen einzigen API-Aufruf

Dieser Ordner enthält **keine Messung der Erkennungsleistung.** Der Lauf diente
allein dem Nachweis, dass die Kette Runner → SmartBugs → Container → Parser →
Auswertung über alle 96 Contracts durchläuft, bevor der kostenpflichtige
Volllauf gestartet wurde.

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `gptscan_mwefixed_v2_dry` |
| Werkzeug | GPTScan, Image `smartbugs/gptscan:1.0`, **`GPTSCAN_DRY_RUN=1`** |
| Modell | `deepseek/deepseek-v4-flash` — nur nominell, es wird nichts aufgerufen |
| Korpus | `smartbugs/samples/gptscan/mwevariety_fixed/`, 96 DeFi-Contracts |
| MAIN | aktiv |
| Durchführung | 15.08.2026 |
| Rohergebnisse | `smartbugs/results/gptscan/gptscan_mwefixed_v2_dry/` (git-ignoriert) |

Es gibt **kein `run_params.json`**: Der Lauf entstand vor dem Protokoll bzw. der
Runner kam nicht bis dorthin. Was sich aus den Rohergebnissen selbst belegen
lässt, hat `gptscan_eval.py` abgeleitet und im Feld `run_parameters.source`
ausdrücklich als abgeleitet gekennzeichnet; alles andere bleibt `null` statt
geraten.

## Wie die Dateien entstanden sind

```powershell
.\run_full_v2.ps1 -Mode dry
python analysis_tools\gptscan_eval.py gptscan_mwefixed_v2_dry
```

## Kernzahlen

| | |
|---|---:|
| Contracts | 96 |
| Findings | 5 |
| „Kosten" | (0,3838) — **simuliert** |
| Tasks mit `errors` | 51 |
| Tasks mit `fails` | 3 |
| nicht übersetzt (degraded) | 2 |

## Was man daraus schließen darf

* Dass die Pipeline über den gesamten Korpus läuft und der Parser für jeden Task
  ein wohlgeformtes Ergebnis erzeugt.
* Dass Fehlerpfade (`errors`, `fails`, `degraded`) tatsächlich ausgelöst und
  korrekt als solche protokolliert werden.

## Was man daraus nicht schließen darf

1. **Die 5 Findings sind keine Befunde.** Im Dry-Run wird kein LLM befragt;
   GPTScan erzeugt Platzhalterausgaben. Sie sagen nichts über den Korpus aus.
2. **Der Kostenwert ist erfunden — im wörtlichen Sinn.** GPTScan schätzt den
   Betrag, den ein echter Lauf gekostet hätte. Gemessen an den Live-Läufen
   liegt diese Schätzung über den tatsächlichen Kosten: Dry $0,3838 gegen
   $0,3638 im Live-Lauf mit MAIN (`gptscan_mwefixed_v2_main`) und $0,2769 im
   Referenzlauf ohne MAIN (`curated_mwefixed_live`), also 6 % beziehungsweise
   39 % darüber (vgl. `eval/README.md`).
3. **Die Static-Bestätigungsstufe läuft im Dry-Run nie.** Jede Aussage über
   Präzisionsfilterung ist hier bedeutungslos — genau deshalb hat die
   Manifest-Logik des Runners einen `dry_run`-Guard
   (`docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`, Fehler #7).
4. **Die erhöhte Fehlerzahl ist nicht mit dem Live-Lauf vergleichbar.** Sie
   entsteht überwiegend dort, wo der fehlende LLM-Rückgabewert den weiteren
   Ablauf stört.
