# Arbeitsbericht 2026-08-02

Was in dieser Sitzung tatsächlich getan wurde, in der Reihenfolge der Ausführung.
Ergebnis: fünf Commits auf dem Initial-Commit `f85946e`.

```
9551734  Docstrings fuer die verbliebenen Einstiegspunkte des eigenen Codes
98e63aa  Secret-Scan als pre-commit-Hook, gitignore-Durchsicht, WareHouse-Reste entfernt
c827d35  README, LICENSE und Dokumentation des Eigenanteils
9d8bee8  Errors und Fails getrennt ausweisen
990e855  Parser-Audit, GPTScan-Silent-Failure behoben, Regressionstests
f85946e  Initialer Stand (unverändert)
```

---

## 1. Bestandsaufnahme (nur lesend)

* 19 Läufe / **930 Task-Verzeichnisse** unter `smartbugs/results/` inventarisiert
  (gptscan 640, llmsmartaudit 147, slither 143).
* Den GPTScan-Silent-Failure an `phase6_live/74_TimeswapPair.sol` reproduziert:
  solc bricht ab (`Expected ',' but got identifier`, Zeile 51), GPTScan fängt das
  ab, läuft ohne Falcon-IR weiter, beendet sich mit **Exit-Code 0** und schreibt
  `{"success": true, "results": []}`. Der Parser meldete weder error noch fail.
* Repo-weiter Secret-Scan: der DeepSeek-Key lag in **62** Dateien, nicht 65 — die
  drei übrigen Treffer waren SPDX-Lizenz-IDs und die CSS-Klasse `.task-list-item`
  (das `sk-` steckt in „ta**sk-**list"). Fundstelle jeweils exakt ein Feld:
  `.docker.environment.DEEPSEEK_API_KEY` in `smartbugs.json`.

## 2. Backup vor dem ersten Eingriff

`smartbugs/results/` vollständig gesichert nach
`…\BACHELORARBEIT\BA-results-raw-backup-20260802\` — **4.461 Dateien, 258,40 MB,
0 Fehler**. Diese Kopie enthält auch die *Prä-Fix-`result.json`* und ist damit die
Grundlage, auf der der Vorher/Nachher-Vergleich unter identischen Regeln
gerechnet werden konnte.

## 3. Audit-Werkzeug gebaut

`analysis_tools/parser_audit.py` liest je Task das Rohmaterial (`result.log`,
`result.tar`, `smartbugs.json`, Exit-Code), extrahiert jede Meldung und prüft, ob
sie im Parser-Output wieder auftaucht.

Zwei bewusste Entwurfsentscheidungen:

* **Eigene Detektoren, kein geteilter Code mit den Parsern.** Ein Audit, das die
  Sicht des Parsers wiederverwendet, kann nur bestätigen, dass der Parser mit
  sich selbst übereinstimmt.
* **Erkennung auf whitespace-freiem Text.** Damit sind Treffer immun gegen die
  Zeilenumbrüche, die `rich` einfügt.

Während des Baus behoben:

| Problem | Wirkung |
|---|---|
| `_RICH_SRC` war am Zeilenende verankert, scannte aber jede Startposition — quadratisch auf den sehr langen LLMSmartAudit-Zeilen | Laufzeit **428 s → 11 s** für den LLMSmartAudit-Lauf |
| `log_records` baute Records per String-Konkatenation auf | quadratisch auf dem 25-MB-Log |
| unbegrenztes `(.+)$` in der ERROR-Regex | Minuten auf Mehrfach-Megabyte-Records |
| `_FINAL_EXC` ohne atomare Gruppe | exponentielles Backtracking auf Solidity-Ketten wie `pool.state.reserves.asset` |

Gesamtlaufzeit über alle 19 Läufe danach: **23 s**.

Drei Fehlklassifikationen im Detektor gefunden und korrigiert, bevor sie in den
Bericht wanderten:

1. **slither Exit-Code 255** wurde als Fehler gewertet (140 Tasks). Slither nutzt
   ihn als Ergebniskanal; `tools/slither-0.11.3/parser.py:126` verwirft ihn
   ausdrücklich. Der Detektor kennt jetzt tool-spezifisch gutartige Exit-Codes.
2. **`Warning:`/`Error:` als Compile-Kriterium** ist unzuverlässig: mit
   `--combined-json` schreibt älteres solc Warnungen nach stdout, zerstört damit
   das JSON und lässt crytic-compile abbrechen — ein Contract kann an einer
   Meldung sterben, die nur „Warning: SPDX license identifier not provided" lautet.
   Maßgeblich ist jetzt die geworfene Exception.
3. **`ContractSolcParsing` ist kein Compile-Fehler.** Bei
   `19_TransactionManager.sol` übersetzte der Contract, Falcon verlor nur *eine*
   Funktion an einen IR-Konvertierungsfehler — GPTScan lieferte trotzdem ein
   Finding. Aus der Liste der Compile-Exceptions entfernt.

## 4. Lückenbericht

**1368 von 1464 Rohmeldungen gingen verloren — restlos alle im GPTScan-Parser.**
slither und LLMSmartAudit: null Lücken.

| Signaltyp | Verlorene Meldungen |
|---|---:|
| `LOG_ERROR` | 708 |
| `TRACEBACK` | 334 |
| `COMPILE_ERROR` | 246 |
| `OUTPUT_UNSUCCESSFUL` | 44 |
| `STATIC_SKIPPED` | 36 |

Belegt in `docs/parser-audit-vorher.md`.

## 5. Redaktion der 62 Task-Logs

`analysis_tools/redact_results.py` — Dry-Run als Standard, `--apply` nötig,
verweigert das Schreiben, wenn sich mehr als das eine Feld ändern würde, gibt nie
einen Wert aus. Serialisiert über denselben `json.dumps(..., sort_keys=True,
indent=4)`-Aufruf wie `sb.io.write_json`, damit die Dateien byte-gleich zu dem
bleiben, was SmartBugs selbst schreiben würde.

Nachkontrolle: **alle 930 Task-Logs** gegen das Backup verglichen — identisch bis
auf das redigierte Feld. Der echte Key existiert danach nur noch in der
git-ignorierten `GPTScan/.env`.

## 6. Parser repariert

### `tools/gptscan/parser.py`

* **De-Wrapper für `rich`-Logs.** `parse_utils.exceptions()` sucht eine Zeile,
  die auf `Traceback (most recent call last):` *endet*, gefolgt von einer nicht
  eingerückten Zeile. Ein `rich`-gerendertes Traceback erfüllt beides nie — die
  erste Zeile trägt rechtsbündig `tasks.py:177`, jede Folgezeile ist eingerückt.
  Das ist die mechanische Ursache des Silent Failure.
* **Das Rendering liefert die errors/fails-Trennung**, statt sie zu erfinden:
  `rich`-gerendert heißt vom Tool geloggt und abgefangen → **error**; rohes
  stderr heißt entkommen → **fail**, weiter bei `parse_utils`. Am Material
  abgelesen: die 44 Tasks mit Exit-Code 1 tragen ihr Traceback roh.
* Neu gemeldet: Compile-Fehler, **die solc-Diagnose als eigene Meldung** (nicht
  nur im truncierten Inneren der FalconError-Zeile), übersprungene Static-Stufe,
  die `ERROR`-Records des Tools, `success: false`, fehlendes `GPTSCAN_META` trotz
  Exit-Code 0, Kostenbremse.
* Neu als **info**: „analysis degraded … inconclusive, not clean" bei
  gescheitertem Compilat, und das normale Static-Filtering mit Zahlen — damit es
  sichtbar ist, ohne als Fehler zu gelten.

### `tools/llmsmartaudit/parser.py`

Das Audit fand hier keine Lücke. Ergänzt wurde Fehlertreue: fehlendes tar,
fehlendes `output.json` und kaputtes JSON sind jetzt drei verschiedene Meldungen
statt einer. Neu als error: „checked 0 of 41 detector categories".

### Nachweis der Reparatur

Nach `reparse --sarif --processes 4` über alle 930 Tasks: **0 Lücken**.

## 7. Auswirkung gemessen

| Prüfung | Ergebnis |
|---|---|
| `evaluate_curated.py` vorher/nachher | **byte-identisch** |
| Spalte `findings` | für **alle 930 Tasks unverändert** |
| Spalte `errors` | +341 Tasks |
| Spalte `infos` | +377 Tasks |
| Spalte `fails` | 0 Änderungen |

Der Grund ist strukturell: `evaluate_curated.py` liest ausschließlich das Feld
`findings`. Die Reparatur berührt nur `errors`/`infos`. Belegt in
`docs/parser-fix-vorher-nachher.md` — dafür entstand `analysis_tools/compare_csv.py`.

## 8. Regressionstests

**41 pytest-Tests**, Fixtures sind unveränderte Rohdaten echter Läufe
(Herkunft in `tests/fixtures/MANIFEST.json`, vor Verwendung auf Secrets geprüft,
LLMSmartAudit-Transkripte verlustfrei gzip-komprimiert → 198 KB statt 649 KB).

**Gegenprobe:** die Parser aus `f85946e` eingespielt → **17 der 41 Tests fallen
durch**. Ein Test, der auch gegen die kaputte Version besteht, wäre wertlos.

Fälle ohne echtes Vorkommen (Timeout, leeres Archiv, kaputtes JSON) sind
synthetisch und tragen `synthetic` im Testnamen.

## 9. Errors/Fails-Auswertung

`analysis_tools/errors_fails_report.py` — je Lauf und Werkzeug: Errors, Fails,
betroffene Contracts, Meldung **im Wortlaut**, sauber durchgelaufene Tasks.
Ausgabe als CSV und Markdown.

Bilanz über alle 19 Läufe: **930 Tasks — 586 sauber, 344 mit Errors, 50 mit
Fails, 246 mit gescheitertem Compilat.**

Zusätzliche Spalte `classification` (`root_cause` / `consequence` /
`independent`) ordnet Ursache und Folgefehler ein — **ohne** eine Meldung zu
ersetzen oder zu verwerfen.

`run_curated.ps1` ruft den Report am Ende jedes Massenlaufs auf und delegiert
dabei an das Python-Skript, statt die Einordnung ein zweites Mal in PowerShell zu
implementieren.

`docs/BA-ERRORS-VS-FAILS.md` leitet die Semantik aus `sb/parse_utils.py` her:
Exit-Code-Tabelle, warum ein beliebiger Exit-Code ≠ 0 als *error* gilt, warum
slither deshalb `EXIT_CODE_255` verwirft, und die drei Beobachtungen, die wie
Defekte aussehen und keine sind.

## 10. Dokumentation

Neu: `README.md`, `LICENSE`, `docs/BA-EIGENANTEIL.md`, `docs/BA-BETRIEB.md`.

Für `BA-EIGENANTEIL.md` wurden die **echten Upstream-Stände geklont und per
Datei-Hash abgeglichen** — nicht geschätzt:

| Komponente | unverändert | geändert | neu |
|---|---:|---:|---:|
| GPTScan | 38 | **7** | 22 |
| LLMSmartAuditTool | 212 | **9** | 36 |
| SmartBugs | — | **1** (`sb/docker.py`) | 2 Tool-Verzeichnisse |

Jede der 17 geänderten Dateien mit *was* und *warum*.

Dabei gefunden:

* `tools/llmsmartaudit/config.yaml` nannte `LLMSmartAudit/LLMSmartAuditTool` als
  `origin` — **diese URL existiert nicht**. Korrekt ist `LLMAudit/…`. Behoben.
* **GPTScan steht unter AGPL-3.0** (Copyleft), und der Baum enthält Änderungen am
  GPTScan-Quellcode. Für ein privates Repo folgenlos, bei Veröffentlichung
  bindend. In `LICENSE` und `BA-EIGENANTEIL.md` festgehalten.
* SmartBugs widerspricht sich selbst: `LICENSE` sagt Apache-2.0,
  `pyproject.toml` sagt MIT. Festgehalten statt eine Variante zu behaupten.

Der tote Verweis auf `docs/BA-AGENT-WORKFLOW.md` ist in `.md` **und** `.tex`
gestrichen — nach deiner Vorgabe: Verweis weg, Hinweissatz bleibt. Ein
Link-Check über alle Dokumente fand danach keinen weiteren toten Verweis.

## 11. Cleanup und Sicherheit

* `analysis_tools/secret_scan.py` — Hook-Modus (gestagte Dateien), `--all`,
  `--install`. Gegengeprüft in beide Richtungen: **1121 Dateien ohne
  Falschtreffer**, ein eingeschleuster Test-Key wird gefunden und blockiert den
  Commit. Der Wert wird nie ausgegeben, nur Datei, Zeile, Mustername.
  Der Hook lief bei den letzten drei Commits live mit.
* `.gitignore`: `.pytest_cache/` wurde bisher **nur** durch die `.gitignore`
  ignoriert, die pytest sich selbst schreibt — das greift erst nach dem ersten
  Testlauf. Ergänzt um `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`,
  `.coverage`, `htmlcov/`, `*.egg-info/`, `.venv/` sowie die generierten
  Audit-CSVs.
* `WareHouse/VaultDS`–`VaultDS4` entfernt (≈3,4 MB Reste eigener
  Integrationstests mitten im Fremdcode). Beispielreport `VaultDS5` bleibt.
  Extern gesichert und über `f85946e` weiterhin herstellbar.

## 12. Abschließende Verifikation

| Prüfung | Ergebnis |
|---|---|
| `pytest tests -q` | **41 passed** |
| `parser_audit.py` | 930 Tasks, 1464 Meldungen, **0 Lücken** |
| `errors_fails_report.py` | 930 Tasks: 586 sauber / 344 Errors / 50 Fails / 246 nicht übersetzt |
| `secret_scan.py --all` | 1121 Dateien, **kein Fund** |
| `redact_results.py` | **0 von 930** — nichts mehr zu redigieren |
| `evaluate_curated.py` | Ausgabe unverändert gegenüber dem Stand vor allen Änderungen |
