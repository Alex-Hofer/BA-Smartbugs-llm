# BA-Kontext: KI-gestützte Smart-Contract-Scanner in SmartBugs

**Zweck dieses Dokuments:** Kontext-Briefing für Claude Code. Es beschreibt den Projektstand,
wie er im Deck `BA-Arbeitsfortschritt.pptx` (Stand **Juli 2026**, 5 Folien) dokumentiert ist.

**Wichtige Lesevorschrift für den Agenten:**

- Abschnitte 1–6 sind **belegte Fakten aus dem Deck**. Sie dürfen als gegeben behandelt werden.
- Abschnitt 7 listet **explizit Unbelegtes**. Nichts davon annehmen, raten oder erfinden —
  erst im Repo verifizieren.
- Vor jeder Code-Änderung gilt das **Phase-0-Prinzip**: erst lesen und den Ist-Zustand im
  Repo belegen (Datei + Zeile), dann Plan vorlegen, dann erst schreiben. Keine Flags,
  Env-Variablen, Pfade oder Config-Keys erfinden, die nicht im Code nachgewiesen wurden.

---

## 1. Projekt in einem Absatz

Bachelorarbeit an der TU Wien. Kernbeitrag ist die **Integration zweier LLM-basierter
Smart-Contract-Auditing-Tools in das SmartBugs-Framework**:

| Tool | Rolle im Projekt |
|---|---|
| **LLMSmartAudit** | Erkennt klassische / generische Code-Defekte |
| **GPTScan** | Erkennt DeFi-spezifische Logik-Schwachstellen |

Beide Tools laufen über die SmartBugs-Integration und sind als Container eingebunden.
Als LLM-Backend wird standardmäßig **DeepSeek** verwendet (Kostengründe).

---

## 2. Integrationsstand (Folie 2)

| Tool | Status | Details |
|---|---|---|
| **LLMSmartAudit** | ✅ **Integriert & getestet** | In SmartBugs eingebunden. **Massenlauf abgeschlossen.** Läuft stabil. **Keine offenen Blocker.** |
| **GPTScan** | ⚠️ **Integration läuft — noch zu fixen** | Grundsätzlich eingebunden und lauffähig. Aber: **häufige Compile-Fehler → Rückfall in den LLM-only-Modus**, dadurch **statische Bestätigungsstufe inaktiv**. |

**Wörtlich benannter nächster Schritt:** Kompilierung stabilisieren, damit die volle
GPTScan-Pipeline läuft.

---

## 3. Fachliche Abgrenzung der Tools (Folie 3)

| | LLMSmartAudit | GPTScan |
|---|---|---|
| Zielklasse | Klassische / „normale" Bugs | DeFi-Logik-Schwachstellen |
| Beispiele | Reentrancy, Arithmetik, Access Control, unchecked calls, bad randomness | Contract ist technisch korrekt, aber das beabsichtigte Verhalten ist ökonomisch ausnutzbar |
| Taxonomie | Generische Code-Defekte (SWC-/DASP-Klassen) | Kein „kaputter" Befehl — semantische, contract-spezifische Fehler |

**Begründung, warum hier ein LLM nötig ist (Argumentation der Arbeit):**

- DeFi-Contracts (Swaps, Kredite, Staking, Liquidity Pools, LP-Token) bewegen unmittelbar Werte.
- Ihre typischen Fehler sind **contract-spezifisch und semantisch**: Man muss verstehen, *was*
  der Contract erreichen will und wie sein ökonomisches Modell funktioniert — nicht nur,
  welche Opcodes vorkommen.
- Rein statische Werkzeuge können das nicht leisten.
- Deshalb koppelt GPTScan ein **LLM** (erschließt die Absicht aus Code, Bezeichnern, Kommentaren)
  mit einer **statischen Bestätigungsstufe**, die den Verdacht am Datenfluss gegenprüft und
  False Positives verwirft.

> **Konsequenz für den aktuellen Blocker:** Genau diese statische Bestätigungsstufe ist
> derzeit inaktiv. GPTScan ist damit auf einen reinen Prompt-Scanner reduziert — der
> methodische Kernbeitrag des Tools fehlt im aktuellen Lauf.

---

## 4. Compiler-Verhalten (Folie 4)

| Tool | Kompiliert? | Solidity-Versionen |
|---|---|---|
| LLMSmartAudit | **nie** | alle — versionsagnostisch, **keine `solc`-Abhängigkeit** |
| GPTScan | **ja — Pflicht für volle Pipeline** | dynamisch pro Contract per Pragma; Range **0.4–0.8** via **`solc-select`** |

**Praktischer Haken (wörtlich im Deck):** GPTScans volle Pipeline läuft nur bei erfolgreicher
Kompilierung. Schlägt sie fehl, fällt das Tool in den LLM-only-Modus zurück.

**Konkrete Messung:** Im `mwevariety`-Lauf waren **95 von 96 Contracts nicht kompilierbar**
(≈ 99 % Fehlerquote). Der GPTScan-Massenlauf ist damit faktisch nicht auswertbar.

---

## 5. Modell-/Provider-Switching (Folie 5)

Modell-Switching ist bei **beiden** Tools integriert — **zur Laufzeit, ohne Rebuild**.
Provider & Modell werden über **Host-Umgebungsvariablen** gewählt, die **SmartBugs in den
Container weiterreicht**.

### GPTScan

| Variable | Werte / Bedeutung |
|---|---|
| `GPTSCAN_PROVIDER` | `deepseek` (Default) oder `openai` |
| `GPTSCAN_MODEL` | Modell-ID; ungesetzt = Default |
| `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` | API-Key je nach Provider |
| `GPTSCAN_DRY_RUN=1` | $0-Tests ohne API-Kosten |

### LLMSmartAudit

| Variable | Werte / Bedeutung |
|---|---|
| `LLM_PROVIDER` | `deepseek` (Default) \| `openai` \| `custom` |
| `LLM_MODEL` | Modell-ID zur Laufzeit |
| Key | über die jeweilige Provider-Umgebungsvariable |

---

## 6. Offene Punkte, priorisiert

| Prio | Punkt | Warum kritisch |
|---|---|---|
| **P0** | **GPTScan-Kompilierung stabilisieren** | Einziger Pfad, der das Projekt weiterbringt. Ohne Fix keine verwertbaren GPTScan-Daten. |
| **P0** | Statische Bestätigungsstufe reaktivieren (Folge von P0.1) | Ohne sie fehlt die False-Positive-Filterung — der Kernbeitrag von GPTScan |
| **P1** | GPTScan-Massenlauf nachziehen | Gegenstück zum bereits abgeschlossenen LLMSmartAudit-Lauf |
| **P2** | Evaluation/Auswertung überhaupt beginnen | Im Deck existiert bislang **keine einzige Ergebniszahl** |

### Ansatzpunkte für die Compile-Diagnose (Hypothesen — im Repo zu verifizieren)

Diese Liste ist **nicht** aus dem Deck belegt, sondern eine Suchheuristik. Jeder Punkt
muss am Code oder an Logs nachgewiesen werden, bevor er als Ursache behandelt wird:

1. Wird das Pragma pro Contract korrekt geparst (Ranges `^`, `>=`, mehrere Pragmas, Kommentare)?
2. Ist die passende `solc`-Version im Container tatsächlich installiert, oder scheitert
   `solc-select install` offline / hinter der Netzwerkbeschränkung?
3. Fehlen Imports/Dependencies (OpenZeppelin, Interfaces), weil der Contract im Datensatz
   als Einzeldatei ohne Remappings vorliegt?
4. Liegt es an Contracts unterhalb 0.4 oder oberhalb 0.8 (außerhalb der unterstützten Range)?
5. Wird der Compile-Fehler geloggt und ist die Fehlermeldung überhaupt ausgewertet worden,
   oder wird nur der Fallback ausgelöst?

**Erster sinnvoller Schritt:** Die 95 fehlgeschlagenen Fälle nach Fehlermeldung
gruppieren. Ohne diese Verteilung ist jeder Fix Raten.

---

## 7. Nicht im Deck belegt — vor Annahmen verifizieren

Der Agent darf zu keinem dieser Punkte etwas behaupten, ohne es im Repo geprüft zu haben:

| Thema | Was fehlt |
|---|---|
| **Ergebnisse** | Keine Findings-Zahlen, kein TP/FP, keine Precision/Recall/F1 |
| **Dataset** | `mwevariety` wird genannt, aber ohne Größe, Herkunft, Labeling, Ground Truth |
| **Baseline-Vergleich** | Kein Gegenüberstellen mit klassischen SmartBugs-Tools (Slither, Mythril, …) |
| **Kosten & Laufzeit** | Keine Messung, obwohl DeepSeek explizit aus Kostengründen gewählt wurde |
| **Reproduzierbarkeit** | Nichts zu Temperature, Seeds, Mehrfachläufen, Nichtdeterminismus |
| **Methodische Deviation** | Der Override von `openai.api_base` auf DeepSeek ist auf den Folien nicht als methodische Abweichung dokumentiert |
| **Schreibstand** | Unklar, welche Kapitel des LaTeX-Texts stehen |
| **Zeitplan** | Keine Meilensteine, keine Restaufwandsschätzung |
| **Sprechernotizen** | Alle 5 Folien haben leere Notes |

---

## 8. Arbeitsregeln für den Agenten

1. **Phase 0 zuerst.** Vor jedem Vorschlag: relevante Dateien lesen und den Ist-Zustand mit
   Datei + Zeilennummer belegen. Erst danach Plan, erst danach Code.
2. **Keine erfundenen Flags.** Env-Variablen, CLI-Flags, Config-Keys und Pfade nur verwenden,
   wenn sie im Code nachgewiesen sind. Die Liste in Abschnitt 5 stammt aus einer Präsentation,
   nicht aus dem Code — sie ist gegenzuprüfen.
3. **Scope halten.** Nur die Dateien anfassen, die für die konkrete Aufgabe nötig sind.
   Keine Umbauten an nicht beauftragten Modulen.
4. **Fehler nicht wegfallbacken.** Der LLM-only-Fallback ist genau das Problem. Compile-Fehler
   sollen sichtbar geloggt und klassifiziert werden, nicht stillschweigend übersprungen.
5. **Kosten beachten.** Für Testläufe `GPTSCAN_DRY_RUN=1` verwenden, solange nicht ausdrücklich
   ein echter Lauf beauftragt ist.
6. **Unsicherheit benennen.** Wenn etwas nicht aus dem Repo belegt werden kann: sagen, nicht
   plausibel klingend füllen.
