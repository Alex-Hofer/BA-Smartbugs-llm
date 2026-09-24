# eval/llmsa_mwefixed_v2/ — LLMSmartAudit über den reparierten DeFi-Korpus

LLMSmartAudit auf `mwevariety_fixed`, also auf demselben Korpus, auf dem GPTScan
seine Zieldomäne hat. Der Lauf ist damit die Gegenprobe zur Frage, ob die
Multi-Agenten-Pipeline auf großen DeFi-Contracts überhaupt bis zum Ende kommt.

> **Nachtrag 20.09.2026: die Rohergebnisse liegen jetzt hier.** Der Lauf wurde
> auf dem Rechner des Co-Autors gefahren -- das Konsolenprotokoll nennt als
> Ablageort `C:\Users\Alex Unterleitner\Desktop\BA-Smartbugs-llm\`. Seine
> Rohergebnisse sind am 20.09.2026 in diesen Arbeitsbaum uebernommen worden und
> liegen unter `smartbugs/results/llmsmartaudit/llmsa_mwefixed_v2/` sowie
> `…_retry/` (96 + 4 Tasks, je `result.json`, `result.log`, `result.tar`,
> `smartbugs.json`).
>
> **Gegengeprueft:** `build_eval.py llmsa_mwefixed_v2 --merge-run
> llmsa_mwefixed_v2_retry` ueber diese Rohdaten erzeugt dieselben 437 Findings,
> Feld fuer Feld identisch mit der hier eingecheckten `findings.jsonl` --
> einzige Abweichung ist der Zeitstempel des Exports. Dieselben Kennzahlen: 96
> Contracts, 37 `context_exceeded`, 59 mit Findings, rund $8,37. Der Lauf ist
> damit vollstaendig belegt, und eine spaetere Parser-Aenderung laesst sich per
> `sb.reparse` auch auf ihn anwenden.

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `llmsa_mwefixed_v2`, zusammengeführt mit dem Nachlauf `llmsa_mwefixed_v2_retry` |
| Werkzeug | LLMSmartAudit, Image `smartbugs/llmsmartaudit:1.0` |
| Modus | `SmartContractTA`, fest in `scripts/do_solidity.sh` |
| Modell | `deepseek/deepseek-v4-flash` |
| Umgebung | `LLM_PROVIDER=deepseek`, `LLM_MODEL=deepseek-v4-flash`, `LLM_CONTEXT_TOKENS=65536` |
| Korpus | `smartbugs/samples/gptscan/mwevariety_fixed/`, 96 DeFi-Contracts |
| Parameter | `--processes 3`, `--timeout 7200`, MAIN nicht gesetzt |
| Durchführung | 15./16.08.2026, Nachlauf 15.09.2026; Protokolle in [`eval/_runlogs/`](../_runlogs/README.md) |
| Auswertung erzeugt | 15.09.2026 |

Der Nachlauf ersetzte genau vier Tasks, die der Hauptlauf nicht entschieden
hatte: `12_Witch`, `25_CompositeMultiOracle`, `43_DelegatedStaking`, `62_Locke`.

> **Woran diese vier scheiterten — und warum das kein Auswahleffekt ist.**
> Alle vier liefen in denselben Fehler: `openai.APIStatusError: Error code:
> 402 — Insufficient Balance`. Das DeepSeek-Guthaben war während des
> Hauptlaufs aufgebraucht; die vier Aufrufe wurden serverseitig abgewiesen,
> bevor das Modell den Contract überhaupt gesehen hatte. Nach dem Auffüllen
> lieferten alle vier ein Ergebnis.
>
> Der Grund, warum das erst seit dem 21.09.2026 in den Daten steht: SmartBugs'
> `sb/parse_utils.py` griff die Token-Buchhaltung des Werkzeugs als Ausnahme
> ab und erreichte die eigentliche Zeile nie, sodass in `result.json`
> `exception (num_prompt_tokens: 22878)` stand. Der Defekt ist im eigenen
> Tool-Parser behoben und per `reparse` auf alle Läufe angewandt; `run_meta.json`
> in diesem Ordner trägt seither die wirkliche Ursache. Hergeleitet in
> [`docs/BA-PARSER-AUDIT-LUECKEN.md`](../../docs/BA-PARSER-AUDIT-LUECKEN.md).
>
> Damit ist der Nachlauf **kein Wiederholen bis zum besseren Ergebnis**: Er
> behebt eine Störung der Infrastruktur, die mit Contract, Werkzeug und Modell
> nichts zu tun hat. Ein Nachlauf über Contracts, die *inhaltlich* gescheitert
> wären — etwa an der Kontextgrenze — hätte diese Eigenschaft nicht; die 37
> Kontext-Überschreitungen sind deshalb bewusst **nicht** wiederholt worden.

## Wie die Dateien entstanden sind

```powershell
.\run_full_v2_llmsa.ps1 -Corpus mwefixed -Processes 3
.\run_retry_llmsa.ps1
python analysis_tools\build_eval.py llmsa_mwefixed_v2 --merge-run llmsa_mwefixed_v2_retry
```

## Kernzahlen

| | |
|---|---:|
| Contracts | 96 |
| davon mit Findings | 59 |
| Kontext überschritten — **nicht analysiert** | 37 |
| Findings | 437 |
| gesehene Kategorien | 34 von 41 |
| Container-Zeit (Summe) | 90 206,2 s |
| Token | 54 901 634 prompt / 9 155 559 completion, 2 624 LLM-Aufrufe |
| Kosten (geschätzt) | ≈ $8,37 |

## Der zentrale Befund

**38,5 % der Contracts (37 von 96) sprengten die Kontextgrenze und wurden nie
analysiert.** Auf dem curated-Korpus war es genau einer von 143. Der Unterschied
ist der Korpus: Die geflatteten DeFi-Contracts enthalten ihren vollständigen
Import-Closure und sind um ein Vielfaches größer. Am Verhältnis der Token sieht
man dasselbe von der anderen Seite — 54,9 Mio. Prompt-Token auf nur 2 624
Aufrufe, also im Mittel rund 20 900 Token je Aufruf. Die Grenze ist die
Konstante 65 536 in `camel/utils.py`, die das Werkzeug vor jedem Aufruf selbst
prüft, nicht eine Ablehnung der API; die Anbieterdokumentation nennt für
`deepseek-v4-flash` 1M Token Kontext (`BA-WERKZEUGE-IM-VERGLEICH.md`,
Abschnitt „Kontextgrenze“).

## Was man daraus schließen darf

* Dass LLMSmartAudits Kontextgrenze auf realen DeFi-Contracts die bindende
  Beschränkung ist, nicht die Kosten und nicht die Laufzeit.
* Wie sich die 437 Findings der 59 auswertbaren Contracts über die
  Detektorkategorien verteilen.

## Was man daraus nicht schließen darf

1. **Nicht bitgleich wiederholbar.** Die Zahlen sind aus den Rohdaten
   nachvollziehbar, aber ein *neuer* Lauf ergaebe andere: LLM-gestuetzte
   Werkzeuge sind nicht deterministisch.
2. **Die 437 Findings gelten für 59 Contracts, nicht für 96.** Jede
   Hochrechnung auf den ganzen Korpus unterstellt, dass die 37 übersprungenen
   Contracts sich wie die übrigen verhalten — dafür gibt es keinen Beleg, und
   sie sind systematisch die größeren.
3. **Kein Vergleich mit GPTScan auf demselben Korpus ohne diesen Vorbehalt.**
   GPTScan kam auf allen 96 Contracts zu einem Ergebnis, LLMSmartAudit auf 59.
   Absolute Findingzahlen nebeneinanderzustellen wäre irreführend — siehe
   `docs/BA-WERKZEUGE-IM-VERGLEICH.md`.
4. **Keine Ground Truth.** `mwevariety_fixed` besitzt keinen annotierten
   Referenzstand; Recall und Precision lassen sich hier nicht bilden.
5. **Die Kosten sind gerechnet, nicht gemessen** (`chatdev/statistics.py`
   kennt das Modell nicht); maßgeblich ist die DeepSeek-Rechnung.
6. **`severity_doc` ist kein Urteil des Modells**, sondern der Default aus
   `findings.yaml`. `function`, `lines`, `severity` und `confidence` bleiben
   durchgehend `null`.
