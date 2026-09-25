# eval/slither_mwefixed_v2/ — Slither 0.11.3 über `mwevariety_fixed` (glibc-Image)

Die statische Baseline auf dem DeFi-Korpus. Der Lauf ist die Spalte „Slither
0.11.3 (glibc-Image)“ in `docs/BA-WERKZEUGE-IM-VERGLEICH.md`, Abschnitt 4.2;
dieser Ordner macht seine Einzelergebnisse je Contract versioniert nachlesbar.

## Woher die Daten stammen

| | |
|---|---|
| Lauf | `slither_mwefixed_v2` |
| Werkzeug | Slither 0.11.3 im eigenen Image `smartbugs/slither:0.11.3-glibc` (ID `a7a63792a158`), Werkzeugverzeichnis `smartbugs/tools/slither-0.11.3-glibc/` |
| Korpus | `smartbugs/samples/gptscan/mwevariety_fixed/`, 96 DeFi-Contracts |
| Parameter | `--timeout 600`, 4 Prozesse, MAIN nicht gesetzt |
| Durchführung | 24.09.2026, 23:11 bis 23:14 Uhr (2:48 min Wanduhr, 646,6 s Container-Zeit) |
| Rohergebnisse | `smartbugs/results/slither-0.11.3-glibc/slither_mwefixed_v2/` (`result.json` und `smartbugs.json` je Task versioniert; Logs und Archive im Release-Zip, siehe README „Wo die Ergebnisse liegen“) |
| Vorlauf | `slither_mwefixed_v1` mit dem Upstream-Image (Alpine): 51 von 96 Contracts, Ursache in `docs/BA-BETRIEB.md`, Fallstrick 10; nur als `eval/per_contract/slither_mwefixed_v1__slither-0.11.3.csv` versioniert |

## Wie die Datei entstanden ist

```powershell
cd smartbugs
.venv\Scripts\python.exe -m sb.results2csv results\slither-0.11.3-glibc\slither_mwefixed_v2 > ..\eval\slither_mwefixed_v2\results2csv.csv
```

`sb.results2csv` ist SmartBugs' eigener Export (unverändert, Upstream). Er
liest nur `result.json` und `smartbugs.json` je Task und setzt keinen
Docker- oder API-Aufruf ab. Die `eval/`-Generatoren dieser Arbeit
(`curated_eval.py`, `build_eval.py`, `gptscan_eval.py`) sind an ein Werkzeug
oder an die curated-Ground-Truth gebunden und erzeugen für Slither außerhalb
von `smartbugs-curated` keinen Ordner; deshalb hier das Upstream-Format.

## Was in der Datei steht

`results2csv.csv`: eine Zeile je Task (96), Spalten wie von SmartBugs
vorgegeben.

| Spalte | Bedeutung |
|---|---|
| `filename`, `basename` | Pfad und Dateiname des Contracts im Container |
| `toolid`, `toolmode` | `slither-0.11.3-glibc`, `solidity` |
| `parser_version` | Versionsstempel des Parsers (Upstream-Kopie, `2025/09/14`) |
| `runid` | `slither_mwefixed_v2` |
| `start`, `duration` | Startzeitpunkt (Unix-Sekunden) und Containerlaufzeit in Sekunden |
| `exit_code` | Exit-Code von Slither: `255` heißt „Findings gemeldet“, `0` heißt „keine Findings“, `1` heißt Abbruch |
| `findings` | Liste der Detektornamen, ein Eintrag je Finding (mehrfach, wenn ein Detektor mehrfach anschlug) |
| `infos`, `errors`, `fails` | Zusatzmeldungen des Parsers nach `docs/BA-ERRORS-VS-FAILS.md` |

Je Contract mit Zustand, Findingzahl und Laufzeit: `eval/per_contract/slither_mwefixed_v2__slither-0.11.3-glibc.csv`.

## Kernzahlen

| | |
|---|---:|
| Contracts | 96 |
| davon analysiert | 95 (94 mit Findings, 1 ohne) |
| nicht analysiert | 1: `58_UniV3Vault.sol`, solc `Stack too deep when compiling inline assembly` (der Korpusbau hatte die Datei nur mit `--optimize` übersetzt bekommen) |
| Findings | 7 096 aus 48 Detektoren |
| nach Slithers Impact-Stufe | 4 858 Informational, 112 Optimization, 1 254 Low, 748 Medium, 124 High |
| häufigste Detektoren | `too-many-digits` (2 020), `naming-convention` (1 886) |
| Median je analysiertem Contract | 55 Findings (Spanne 0 bis 349) |

Herleitung der Impact-Verteilung: `docs/BA-DURCHFUEHRUNGSPROTOKOLL.md`,
Nachtrag 4.8; `docs/BA-VERIFIKATIONSBERICHT-20260924.md`, Abschnitt 4.1.

## Was man daraus schließen darf

* Wie viele und welche Detektoren Slither auf geflatteten DeFi-Contracts
  auslöst, je Contract nachlesbar.
* Dass die statische Baseline auf diesem Korpus fast vollständig läuft, sobald
  der Compiler startet (95 von 96), und dass ihre Ausgabe von Stilhinweisen
  dominiert ist.
* Für die 51 Contracts, die schon der Vorlauf `slither_mwefixed_v1` erreichte,
  sind Findingzahl und Detektorverteilung in beiden Läufen identisch: Slither
  ist deterministisch.

## Was man daraus nicht schließen darf

1. **Keine Ground Truth.** `mwevariety_fixed` hat keinen annotierten
   Referenzstand; Recall und Precision lassen sich nicht bilden. Der Vergleich
   mit GPTScan (77 Findings) und LLMSmartAudit (437) auf demselben Korpus ist
   ein Mengen-, kein Qualitätsvergleich.
2. **Detektorname ist kein Schweregrad.** Die Impact-Stufe steht nicht in
   dieser CSV, sondern in der `result.json` je Task (versioniert); die
   Verteilung oben ist daraus gerechnet.
3. **`58_UniV3Vault.sol` ist kein Slither-Befund.** Der Contract scheiterte am
   Compiler, nicht am Werkzeug; ein Lauf mit `--solc-args --optimize` wäre der
   nächste Schritt und steht aus.
4. **Kein Vergleich mit dem curated-Lauf.** Dort lief das Upstream-Image
   `smartbugs/slither:0.11.3`; dieselbe Slither-Version, aber Solidity 0.4 statt
   0.6 bis 0.8 und ein anderer Korpus.
