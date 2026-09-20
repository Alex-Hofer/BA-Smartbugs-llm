# eval/_runlogs/ — Konsolenprotokolle der LLMSmartAudit-Massenläufe

Hier liegen die Laufprotokolle, die `run_full_v2_llmsa.ps1` und
`run_retry_llmsa.ps1` während eines Massenlaufs mitschreiben. Sie sind die
einzige Aufzeichnung dessen, was **während** eines Laufs geschah — die
Auswertungen unter `eval/<runid>/` kennen nur den Endstand.

## Die Dateien

| Datei | Lauf | Inhalt |
|---|---|---|
| `llmsa_full_20260815-181656.log` | Fehlstart | abgebrochen nach fünf Zeilen, unmittelbar neu gestartet |
| `llmsa_full_20260815-181854.log` | `llmsa_curated_v2` + `llmsa_mwefixed_v2` | der eigentliche Volllauf über beide Korpora, 15.08.2026 18:18 bis 16.08.2026 13:14 |
| `llmsa_retry_20260915-141858.log` | `llmsa_mwefixed_v2_retry` | Nachlauf über vier unentschiedene Contracts, 15.09.2026 |

## Was eine Zeile enthält

* **Kopf:** Korpus, Prozesszahl, Kostendeckel, Backend (`provider`, `model`,
  `context`), ob der MAIN-Parameter gesetzt war.
* **Zwischenstand** alle paar Minuten: fertige Tasks, Prompt- und
  Completion-Token, laufende Kostenschätzung.
* **Ende:** Exit-Code, der anschließende `reparse`-Aufruf, die Gesamtsumme und
  der nächste vorgesehene Schritt.

Der API-Schlüssel steht **nicht** in den Protokollen. Der Runner notiert nur,
dass einer gesetzt war, und seine Länge — der Wert selbst wird nie geschrieben.

## Was man daraus schließen darf

* Den zeitlichen Verlauf eines Laufs: wann Tasks fertig wurden, wo er stockte,
  wie die Kosten anwuchsen. Für `llmsa_curated_v2` etwa knapp 19 Stunden
  Wanduhr für beide Korpora zusammen.
* Die Parameter, mit denen ein Lauf tatsächlich gestartet wurde — unabhängig
  davon, was später in `run_meta.json` steht.
* Dass kein Rate-Limit auftrat und kein Retry nötig war.

## Was man daraus nicht schließen darf

1. **Die Kostenzahl im Protokoll ist eine laufende Schätzung des Runners**
   (239 Tasks, ≈ $13,16) und weicht von der Schätzung in den `run_meta.json`
   ab ($5,16 + $8,37 = $13,53), weil beide mit unterschiedlichen Preisannahmen
   rechnen. Maßgeblich ist in beiden Fällen die DeepSeek-Rechnung.
2. **`ExitCode=` ohne Wert ist kein Fehler.** Die Zeile entsteht, wenn der
   Runner den Exit-Code des Unterprozesses nicht mehr abgreifen konnte; der
   nachfolgende `reparse`-Schritt und die Task-Zahlen zeigen, dass der Lauf
   durchlief.
3. **Kein Ergebnis über Contracts.** Findings stehen in den Protokollen nicht;
   dafür sind die `eval/<runid>/`-Ordner da.

## Wo die zugehörigen Rohergebnisse liegen

Die Protokolle nennen als Ablageort
`C:\Users\Alex Unterleitner\Desktop\BA-Smartbugs-llm\`. Die beiden
`llmsa_*_v2`-Läufe wurden also auf dem Rechner des Co-Autors gefahren.

* **`llmsa_mwefixed_v2`** (samt `_retry`): am 20.09.2026 in diesen
  Arbeitsbaum übernommen. Die Rohergebnisse liegen unter
  `smartbugs/results/llmsmartaudit/`, und `build_eval.py` erzeugt daraus
  dieselbe Auswertung, die unter
  [`eval/llmsa_mwefixed_v2/`](../llmsa_mwefixed_v2/README.md) eingecheckt ist.
  Bei derselben Gelegenheit kam der bis dahin unbekannte Lauf
  `llmsa_smoke_curated` (3 Contracts) dazu; er hat keine eigene Auswertung,
  taucht aber in der Errors/Fails-Bilanz und im Parser-Audit auf.
* **`llmsa_curated_v2`**: die Rohergebnisse fehlen hier weiterhin. Für
  LLMSmartAudit auf `smartbugs-curated` ist ohnehin `curated_v1_20260705`
  der Bezugslauf — er liegt vollständig vor und ist in
  [`eval/curated_v1_20260705__llmsmartaudit/`](../curated_v1_20260705__llmsmartaudit/README.md)
  ausgewertet.
