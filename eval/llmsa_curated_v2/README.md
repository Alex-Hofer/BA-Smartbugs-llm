# eval/llmsa_curated_v2/ — LLMSmartAudit-Volllauf über `smartbugs-curated`

Der zweite vollständige LLMSmartAudit-Lauf über den curated-Datensatz, gefahren
mit dem seit 15.08.2026 um die Kontextzustände erweiterten Parser.

> **Dieser Lauf wurde auf dem Rechner des Co-Autors gefahren** — das
> Konsolenprotokoll nennt als Ablageort
> `C:\Users\Alex Unterleitner\Desktop\BA-Smartbugs-llm\`. Seine Rohergebnisse
> liegen dort; `smartbugs/results/llmsmartaudit/llmsa_curated_v2/` existiert in
> diesem Arbeitsbaum nicht, `build_eval.py llmsa_curated_v2` lässt sich hier
> also **nicht** wiederholen. Was in diesem Ordner liegt, ist die einzige im
> Repository erhaltene Fassung des Laufs.
>
> **Stand 21.09.2026: die Rohergebnisse liegen weiterhin beim Co-Autor, nicht
> in diesem Arbeitsbaum.** Eine Gegenprüfung auf dessen Rechner am 21.09.2026
> fand unter `smartbugs/results/llmsmartaudit/llmsa_curated_v2/` 143
> vollständige Task-Verzeichnisse vom 15./16.08.2026; die Summe ihrer Findings
> (1 028) stimmt exakt mit der `findings.jsonl` in diesem Ordner überein. Eine
> frühere Fassung dieses Absatzes behauptete, die Rohdaten existierten
> nirgends mehr — das war falsch und ist hiermit richtiggestellt.
>
> Für diesen Arbeitsbaum bleibt die Folge dieselbe: Solange die Daten nicht
> übertragen sind, lässt sich der Lauf **hier** weder reparsen noch in die
> Errors/Fails-Bilanz oder das Parser-Audit aufnehmen. Beides wäre nach einer
> Übertragung möglich; die Bilanzen in `docs/errors-fails.md` und
> `docs/parser-audit-nachher.md` führen ihn deshalb nicht.
>
> **Er ist trotzdem nicht wertlos, im Gegenteil.** Er ist der zweite
> LLMSmartAudit-Lauf über denselben Korpus und damit die einzige Grundlage, auf
> der sich die Streuung dieses Werkzeugs beziffern lässt: 61,4 % Übereinstimmung
> gegenüber `curated_v1_20260705`, nur 5 % der Contracts mit identischem
> Detektor-Satz. Herleitung und Vorbehalte in
> [`docs/BA-WERKZEUGE-IM-VERGLEICH.md`](../../docs/BA-WERKZEUGE-IM-VERGLEICH.md),
> Abschnitt 4.4. Wer
> LLMSmartAudit auf curated mit vorhandenen Rohdaten auswerten will, nimmt den
> Lauf `curated_v1_20260705` — siehe
> [`eval/curated_v1_20260705__llmsmartaudit/`](../curated_v1_20260705__llmsmartaudit/README.md).

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `llmsa_curated_v2` |
| Werkzeug | LLMSmartAudit, Image `smartbugs/llmsmartaudit:1.0` |
| Modus | `SmartContractTA`, fest in `scripts/do_solidity.sh` |
| Modell | `deepseek/deepseek-v4-flash` |
| Umgebung | `LLM_PROVIDER=deepseek`, `LLM_MODEL=deepseek-v4-flash`, `LLM_CONTEXT_TOKENS=65536` |
| Korpus | `smartbugs-curated`, 143 gelabelte Contracts |
| Parameter | `--processes 3`, `--timeout 3600`, MAIN nicht gesetzt |
| Taxonomie | `smartbugs/tools/llmsmartaudit/findings.yaml`, 41 Detektoren |
| Durchführung | 15./16.08.2026; Konsolenprotokoll in [`eval/_runlogs/`](../_runlogs/README.md) |
| Auswertung erzeugt | 16.08.2026 |

## Wie die Dateien entstanden sind

```powershell
.\run_full_v2_llmsa.ps1 -Corpus both -Processes 3
python analysis_tools\build_eval.py llmsa_curated_v2
```

## Kernzahlen

| | |
|---|---:|
| Contracts | 143 |
| davon mit Findings | 142 |
| Kontext überschritten — **nicht analysiert** | 1 |
| Findings | 1 028 |
| gesehene Kategorien | 33 von 41 |
| Container-Zeit (Summe) | 114 091,5 s |
| Token | 11 119 680 prompt / 11 235 316 completion, 6 126 LLM-Aufrufe |
| Kosten (geschätzt) | ≈ $5,16 |

## Was in den Dateien steht

| Datei | Inhalt |
|---|---|
| `findings.jsonl` | eine Zeile je Finding: Contract, Detektorname, DASP-Zuordnung, `severity_doc`, Begründungstext |
| `run_meta.json` | Laufparameter, Zustände, Token, Kosten, Liste der gescheiterten Tasks |
| `summary.md` | Findings je Kategorie und je Contract, Fehlerquoten |

`function`, `lines`, `severity` und `confidence` sind durchgehend `null`: Das
Werkzeug liest Quelltext als Text und meldet weder Positionen noch Schweregrade.
`severity_doc` trägt den dokumentationsseitigen Default aus `findings.yaml` und
ist **kein** Urteil des Modells.

## Was man daraus schließen darf

* Wie breit LLMSmartAudit auf klassischen SWC/DASP-Contracts meldet und wie sich
  die Findings auf die 41 Detektorkategorien verteilen.
* Welche Contractgrößen die Kontextgrenze sprengen — hier genau einer.

## Was man daraus nicht schließen darf

1. **In diesem Arbeitsbaum nicht reproduzierbar.** Ohne die Rohergebnisse lässt sich keine Zahl dieses
   Ordners am Ursprung nachprüfen. Für belegbare curated-Zahlen ist
   `curated_v1_20260705` heranzuziehen.
2. **Der eine Contract mit überschrittenem Kontext ist kein Ergebnis.**
   `0x663e4229142a27f00bafb5d087e1e730648314c3` wurde nie analysiert; er darf
   weder als sauber gelten noch in eine Precision-Rechnung eingehen.
3. **Die Kosten sind gerechnet, nicht gemessen.** Das Werkzeug meldet $0,0000,
   weil `chatdev/statistics.py::prompt_cost` keinen Eintrag für dieses Modell
   hat. Maßgeblich ist die DeepSeek-Rechnung.
4. **Kein Vergleich mit `curated_v1_20260705` ohne Vorbehalt.** Die beiden Läufe
   unterscheiden sich in Parser-Stand, Timeout und Prozesszahl; der Unterschied
   in der Findingzahl (1 028 gegen 1 124) misst nicht nur den
   Nicht-Determinismus.
5. **`severity_doc` ist kein Schweregrad des Modells** (siehe oben).
6. **Contract-Level, nicht zeilengenau.** Ohne Zeilennummern lässt sich nicht
   prüfen, ob ein Finding die gelabelte Stelle trifft.
