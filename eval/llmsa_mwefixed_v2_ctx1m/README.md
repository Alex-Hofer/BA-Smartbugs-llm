# eval/llmsa_mwefixed_v2_ctx1m/ — die 37 Kontext-Contracts mit angehobener Grenze

Nachlauf von LLMSmartAudit über genau die 37 Contracts des DeFi-Korpus
`mwevariety_fixed`, die im Hauptlauf `llmsa_mwefixed_v2` (16.08.2026) mit
`max_tokens_exceeded_by_camel` abbrachen und dort als „Kontext überschritten,
nicht analysiert“ geführt sind. Der Lauf beantwortet die Frage, ob diese
Contracts am Modell scheiterten oder an der Konstante 65 536 in
`camel/utils.py`, die das Werkzeug vor jedem Aufruf selbst prüfte.

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `llmsa_mwefixed_v2_ctx1m`, 24.09.2026, in zwei Teilen: 26 Contracts 15:47–19:21 Uhr, 11 Contracts 19:25–20:54 Uhr (Grund unten) |
| Werkzeug | `llmsmartaudit`, Image `smartbugs/llmsmartaudit:1.0` mit ID `7c111aa6b366`, gebaut am 24.09.2026 aus Commit `8a53d79` (`camel/utils.py` liest die Agentengrenze aus `LLM_CONTEXT_TOKENS`) |
| Modell | `deepseek/deepseek-v4-flash`. Diesen Namen leitet der Anbieter seit September 2026 auf DeepSeek-V4.1-Flash; der Hauptlauf vom August lief auf V4-Flash |
| Parameter | `LLM_CONTEXT_TOKENS=1000000`, `LLM_MAX_COMPLETION_TOKENS=32768`, `--timeout 7200`, 2 Prozesse, kein `--main` |
| Korpus | 37 der 96 Dateien unter `smartbugs/samples/gptscan/mwevariety_fixed/`, Auswahl = alle Tasks des Hauptlaufs mit Kontextabbruch |
| Rohergebnisse | `smartbugs/results/llmsmartaudit/llmsa_mwefixed_v2_ctx1m/` 37 Task-Ordner mit `result.json`, `result.log`, `result.tar`, `smartbugs.json`; `result.json` und `smartbugs.json` sind versioniert, Logs und Archive liegen im Release-Zip (README „Wo die Ergebnisse liegen“) |
| Protokolle | `eval/_runlogs/llmsa_retry_20260924-154737.log` (Teil 1, Runner), `llmsa_ctx1m_kostenwaechter_20260924.log` (Teil 1, Kostenwächter), `llmsa_retry_20260924-192459.log` (Teil 2) |

Warum zwei Teile: Der Runner `run_retry_llmsa.ps1` brach in Teil 1 nach sechs
Minuten an einer kurzen Dateisperre auf seinem Protokoll ab, SmartBugs lief
weiter. Ein Ersatz-Kostenwächter mit denselben Preissätzen stoppte den Lauf
nach 26 fertigen Contracts bei geschätzten 8,16 USD; tatsächlich abgebucht
waren 4,00 USD, weil die Preissätze des Runners den Cache-Rabatt des Anbieters
nicht kennen. Die restlichen 11 Contracts liefen anschließend unter derselben
`runid` mit dem inzwischen gehärteten Runner. Alle 37 Task-Ordner liegen in
einem Laufordner; die Ergebnisse sind von der Teilung nicht berührt.

## Wie die Dateien entstanden sind

```
python analysis_tools/build_eval.py llmsa_mwefixed_v2_ctx1m
```

`findings.jsonl`, `run_meta.json` und `summary.md` sind Generatorausgabe. Der
Block `invocation` in `run_meta.json` wird seit dem 24.09.2026 aus den Quellen
gelesen statt fest hinterlegt: `timeout_s` und `main` aus dem Entrypoint in
jeder `smartbugs.json`, Modell und Anbieter aus der Info-Zeile des Werkzeugs in
`result.json`, `processes`, `LLM_CONTEXT_TOKENS` und die Image-ID aus den
Runner-Protokollen unter `eval/_runlogs/`, die diese `runid` nennen. Für diesen
Lauf nennen drei Protokolle die `runid`: der am Speicher gescheiterte erste
Versuch mit 4 Prozessen (15:20 Uhr, keine Ergebnisse übernommen) und die beiden
Teile mit 2 Prozessen. Weil sich die Protokolle bei `processes` widersprechen,
steht dort `null` mit dem Vermerk `Quellen widersprechen sich (2, 4)`; die
Einzelwerte stehen unter `protocols`. `LLM_CONTEXT_TOKENS=1000000` und die
Image-ID `7c111aa6b366…` sind eindeutig belegt. Das Feld `parser_version` in
`run_meta.json` ist weiterhin eine Konstante des Skripts (Stand 15.08.2026);
maßgeblich ist die Parser-Version `2026/09/21` in jeder `result.json`.

## Der zentrale Befund

**Alle 37 Contracts wurden vollständig analysiert.** Kein Kontextabbruch, kein
`fail`, kein `error`, kein Timeout; jeder Task lief durch alle 41 Detektoren
(44 LLM-Aufrufe je Contract wie bei den durchgelaufenen Contracts des
Hauptlaufs).

| | Hauptlauf `llmsa_mwefixed_v2`, dieselben 37 Contracts | dieser Nachlauf |
|---|---:|---:|
| analysiert | 0 | **37** |
| Findings | – | 317 (2 bis 19 je Contract, Median 9) |
| verschiedene Kategorien | – | 34 von 41 |
| LLM-Aufrufe | 37 (je einer bis zum Abbruch) | 1 625 |
| Prompt-Token | – | 100,3 Mio. (Mittel 61 700 je Aufruf) |
| Completion-Token | – | 6,3 Mio. |
| Container-Zeit | – | 35 028 s (9,7 h), Median 954 s, Maximum 1 249 s |
| Kosten | – | geschätzt 11,42 USD (Preissätze des Runners), abgebucht 5,55 USD (Kontostand 13,69 → 8,14 USD) |

Zum Vergleich der Größenordnung: Die 59 im Hauptlauf analysierten Contracts
brauchten im Mittel 20 900 Prompt-Token je Aufruf, diese 37 rund 61 700. Die
Grenze von 65 536 lag also genau in dem Bereich, in dem die Konversation
dieser Contracts nach dem ersten Aufruf ankommt.

## Was man daraus schließen darf

* Die 37 Contracts scheiterten im August an der werkzeuginternen Konstante,
  nicht am Modell und nicht an der API. Mit angehobener Grenze analysiert
  LLMSmartAudit den gesamten DeFi-Korpus (59 + 37 = 96 Contracts, in zwei
  Läufen mit verschiedenen Modellständen).
* Was das Werkzeug auf großen, geflatteten DeFi-Contracts kostet: rund 0,15
  USD und rund 16 Minuten je Contract bei zwei parallelen Prozessen.

## Was man daraus nicht schließen darf

1. **Nicht in den Hauptlauf einmischen.** Anderer Modellstand (V4.1-Flash
   gegen V4-Flash), andere Grenze, sechs Wochen Abstand. `build_eval.py
   llmsa_mwefixed_v2 --merge-run llmsa_mwefixed_v2_ctx1m` wäre technisch
   möglich, ergäbe aber eine Mischung aus zwei Bedingungen; die Kennzahlen des
   Hauptlaufs in `eval/llmsa_mwefixed_v2/` bleiben deshalb unverändert.
2. **Kein Vergleich der Findingzahlen mit den 59 des Hauptlaufs.** Größere
   Contracts, anderes Modell, andere Anzahl; 317 gegen 437 sagt nichts über
   Qualität.
3. **Kosten sind Näherung.** Die 5,55 USD sind die Differenz zweier
   Kontostände desselben Kontos, auf dem sonst nichts lief; die 11,42 USD sind
   die Schätzung mit den Preissätzen aus `run_retry_llmsa.ps1`, die keinen
   Cache-Rabatt kennen.
4. **Nicht bitgleich wiederholbar.** Ein neuer Lauf ergäbe andere Findings;
   die Streuung von LLMSmartAudit liegt bei 61,4 % Übereinstimmung zwischen
   zwei Läufen (`docs/BA-WERKZEUGE-IM-VERGLEICH.md`, Abschnitt 4.4).

## Dateien

| Datei | Inhalt |
|---|---|
| `findings.jsonl` | eine Zeile je Finding, Felder wie in `eval/llmsa_mwefixed_v2/` |
| `run_meta.json` | Zustände, Token, Kosten (Schätzung); `invocation` siehe oben |
| `summary.md` | Findings je Kategorie und je Contract |
