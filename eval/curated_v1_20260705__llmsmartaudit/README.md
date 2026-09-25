# curated_v1_20260705__llmsmartaudit

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `curated_v1_20260705` |
| Werkzeug | `llmsmartaudit` |
| Image | `smartbugs/llmsmartaudit:1.0` |
| Modell | `deepseek/deepseek-v4-flash` |
| Datensatz | `smartbugs-curated`, 143 gelabelte Contracts, DASP-Top-10 |
| Contracts im Lauf | 143 |
| Timeout je Task | 5400 s |
| Rohergebnisse | `smartbugs/results/llmsmartaudit/curated_v1_20260705` (result.json und smartbugs.json je Task versioniert; Logs und Archive im Release-Zip, siehe README) |
| Erzeugt am | 2026-09-25T16:33:39+00:00 |

Der Lauf fand am 05./06.07.2026 statt (Datum im Laufnamen). Von den
Rohergebnissen sind je Task `result.json` und `smartbugs.json` versioniert;
Logs und Archive liegen im Release-Zip (README, "Wo die Ergebnisse
liegen"). Dieser Ordner ist die daraus abgeleitete Auswertung.

## Wie die Dateien entstanden sind

```
python analysis_tools/curated_eval.py --run curated_v1_20260705 --tools llmsmartaudit
```

Das Skript liest ausschliesslich; es setzt keinen einzigen API-Aufruf ab
und veraendert nichts unter `smartbugs/results/`.

## Was in den Dateien steht

**`findings.jsonl`** -- eine Zeile je Finding, JSON pro Zeile.

| Feld | Bedeutung |
|---|---|
| `contract_id` | Dateiname ohne `.sol`. **Kein Schluessel**: der Datensatz fuehrt `0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol` sowohl unter `reentrancy` als auch unter `unchecked_low_level_calls`; eindeutig ist erst das Paar `(label_dir, contract_id)`. |
| `contract_file` | Pfad, wie SmartBugs ihn protokolliert hat |
| `label_dir`, `labels` | Kategorie des Datensatzes bzw. die Labels der Ground Truth |
| `category_raw` | Name des Findings, wie das Werkzeug ihn meldet |
| `classification_raw`, `dasp10` | Klassifikation aus `smartbugs/tools/llmsmartaudit/findings.yaml` |
| `dasp_category` | daraus abgeleiteter curated-Kategoriename, leer wenn keine Zuordnung |
| `category_defi_logic` | ob die Klassifikation DeFi-Logik im Sinne GPTScans ist |
| `function`, `lines` | Fundstelle, sofern das Werkzeug sie meldet -- sonst `null` |
| `severity`, `confidence` | Urteil des Werkzeugs, sofern vorhanden |
| `severity_doc` | Severity aus findings.yaml -- Dokumentations-Default, **kein** Urteil des Werkzeugs |
| `description` | Begruendungstext des Werkzeugs |
| `run_id`, `timestamp` | Lauf und Zeitpunkt des Exports |

**`run_meta.json`** -- Laufparameter, Zustandsverteilung, Token, Kosten,
Recall/Precision/F1 je Kategorie und die Liste aller Tasks, die nicht
sauber durchliefen.

**`summary.md`** -- dieselben Zahlen als Tabellen zum Lesen.

## Was man daraus schliessen darf

* Wie viele Findings dieses Werkzeug auf diesem Korpus meldet und wie sie
  sich auf die Kategorien verteilen.
* Contract-Level-Recall gegen die Ground Truth: ob das Werkzeug zu einem
  gelabelten Contract mindestens ein passendes Finding meldet.
* Wie oft das Werkzeug ueberhaupt zu einem Ergebnis kam (Spalte *Zustand*).

## Was man daraus nicht schliessen darf

1. **Kein Precision-Mass im ueblichen Sinn.** Der Datensatz labelt genau
   *eine* Primaer-Schwachstelle je Contract. Ein zutreffender
   Sekundaer-Befund zaehlt hier als False Positive; die Precision-Werte
   sind Untergrenzen.
2. **Nur DASP-klassifizierte Findings zaehlen.** 468 der 1 124 Findings dieses
   Laufs tragen keine DASP-Zuordnung und gehen weder in Recall noch in
   Precision ein. Keine Zuordnung heisst nicht belanglos.
3. **Contract-Level, nicht zeilengenau.** Ein Werkzeug, das viel meldet,
   trifft haeufiger zufaellig. Zeilengenau laesst sich nicht auswerten,
   weil LLMSmartAudit grundsaetzlich keine Zeilennummern emittiert.
4. **`severity_doc` ist kein Urteil.** Der Wert kommt aus findings.yaml und
   ist je Detektorname konstant.
5. **Ein Lauf ist keine Verteilung.** LLM-gestuetzte Werkzeuge sind nicht
   deterministisch; fuer GPTScan sind 74 % Lauf-zu-Lauf-Uebereinstimmung
   gemessen (`docs/BA-GPTSCAN-VERGLEICH.md`, Abschnitt 4).
6. **Kein Werkzeugvergleich ueber Korpora hinweg.** GPTScans Zieldomaene
   ist DeFi-Logik, nicht DASP. Auf diesem Korpus misst man, was es *nicht*
   sucht -- siehe `docs/BA-WERKZEUGE-IM-VERGLEICH.md`.
7. **Die Kostenangabe ist gerechnet, nicht gemessen.** Sie folgt den
   Preisen in `build_eval.py`; massgeblich ist die DeepSeek-Rechnung.

