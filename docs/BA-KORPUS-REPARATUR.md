# Rekonstruktion eines kompilierbaren DeFi-Korpus für GPTScan

> Teil der Bachelorarbeit · zurück zum Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

**Von 1 zu 94 analysierbaren DeFi-Contracts** · durchgeführt am 21.07.2026

GPTScans Zieldomänen-Korpus `mwevariety` (96 DeFi-Contracts) war zu **95 von
96 nicht kompilierbar**; GPTScan lief dort nur im LLM-only-Modus ohne statische
Bestätigung. Hier beschreiben wir, wie wir daraus `mwevariety_fixed` aus den
Originalquellen des Web3Bugs-Benchmarks rekonstruiert haben. Ergebnis: **96 von
96** kompilieren mit `solc`, **94 von 96** laufen durch GPTScans eigene
Toolchain, und die statische Bestätigungsstufe ist auf diesem Korpus erstmals
aktiv.

---

## 1. Warum der alte Korpus GPTScan blockierte

95 von 96 Contracts endeten mit `InvalidCompilation`, 22 davon zusätzlich mit
Python-Crashes im Werkzeug ([`BA-DURCHFUEHRUNGSPROTOKOLL.md`](BA-DURCHFUEHRUNGSPROTOKOLL.md),
Fehler #12). GPTScan hat zwei Stufen: Das LLM schlägt Kandidaten vor, eine
**statische Stufe** prüft sie am kompilierten Daten- und Kontrollfluss und
verwirft False Positives. Die zweite Stufe **braucht ein Compilat**. Ohne
Compilat bleibt ein reiner Prompt-Scanner ohne Präzisionsfilter — und genau so
entstanden die 11 Findings des ersten DeFi-Laufs. Unser Ziel war deshalb, dass
GPTScans *vollständige* Pipeline läuft.

## 2. Ursachen

Die Diagnose mit `corpus_tools/build_fixed.py` ergab zwei Defekte:

1. **Fehlende Abhängigkeiten.** Die Dateien sind einzeln aus größeren
   Projekten herausgelöst. Ihre Importe (Interfaces, Basis-Contracts, Libraries,
   npm-Pakete wie OpenZeppelin, solmate, prb-math) fehlen. 62 Dateien hatten
   Lücken, darunter 245 unaufgelöste Verweise auf `@openzeppelin/contracts`
   (Aufschlüsselung im Anhang).
2. **Beschädigte Dateien.** Der Extraktor hatte Kommentare und Zeilenumbrüche
   entfernt und viele Dateien mitten im Code abgeschnitten. Für die
   Kompilierung ist das egal, weil wir die vollständigen Originale nehmen — es
   erklärt aber, warum die Zuordnung (Abschnitt 4) mehrstufig sein muss.

## 3. Herkunft und Pipeline

Die Contracts stammen aus **Web3Bugs** (<https://github.com/ZhangZhuoSJTU/Web3Bugs>),
dem Benchmark des GPTScan-Papers. Die Präfixe (`5_`, `13_`, `106_` …) sind
Web3Bugs-**Contest-IDs**: 96 Dateien aus 49 Contests.

| Schritt | Zweck | Ergebnis |
|---|---|---|
| `map` | Original je Datei finden und per Byte-Abgleich belegen | 96/96 |
| `scan` | Importe auflösen, Lücken auflisten | Lückenliste |
| `vendor` | npm-Pakete je Contest und Solidity-Ära laden | `vendor/` |
| `fetch` | Dateien holen, die im Snapshot fehlen | Lücken gefüllt |
| `flatten` | alle Importe zu *einer* Datei je Contract zusammenführen | `mwevariety_fixed/` |
| `check` | jede Datei mit passendem `solc` kompilieren | 96/96 |

Insgesamt haben wir 1 279 Abhängigkeiten aufgelöst und eingebettet.

## 4. Ist die rekonstruierte Datei wirklich *dieses* Sample?

Eine Datei gilt als zugeordnet, wenn ihr kommentar- und whitespace-bereinigter
Bytestrom zum Original passt. Drei Stufen (Feld `verified` in
`corpus_tools/mapping.json`):

| Stufe | Dateien | Bedeutung |
|---|---:|---|
| `equal` | 33 | identisch |
| `truncated-prefix` | 50 | exakter *Präfix* des Originals (abgeschnitten; im Mittel noch ≈ 14 % des Originals) |
| `header-prefix` | 13 | Rumpf zusätzlich beschädigt; Übereinstimmung im Kopf (≥ 200 Byte: Pragma, Importe, Contract-Kopf), dazu Dateiname und Contest-ID |

Eingesetzt wird immer das vollständige Original — die Rekonstruktion ist also
nicht nur kompilierbar, sondern auch inhaltlich vollständiger als das Sample.

## 5. Sonderfälle

* **Contest-IDs korrigiert.** Trident (`34_*`) liegt in Web3Bugs unter Contest
  35, `46_WrappedIbbtcEth` unter 47.
* **Lückenquellen.** Das Web3Bugs-Snapshot hat bei einigen Contests den
  Verzeichnisbaum flachgeklopft, Interfaces fehlten. Nachgeladen aus dem
  LLM4SMAPR-Spiegel, den PoolTogether-Repos und npm.
* **Eine nachgebaute Datei.** `17/.../IChainlinkAggregator.sol` gibt es in
  keiner Quelle. Wir haben sie aus der Aufrufform in `Buoy3Pool.sol`
  (`latestAnswer()`) rekonstruiert; sie entspricht Chainlinks
  Legacy-`AggregatorInterface` und ist als einzige nicht originale Datei im Kopf
  gekennzeichnet.
* **Zwei Eingriffe für die Kompilierung.** `8_NFTXEligiblityManager` bekam
  `pragma experimental ABIEncoderV2;` (das Projekt hatte es global in der
  Build-Konfiguration). `58_UniV3Vault` braucht `--optimize` („stack too deep“).

## 6. Regeln fürs Flattening

* Genau **ein** `pragma solidity <version>;` — die höchste Version, die alle
  Quellen erfüllt (wie SmartBugs auswählt).
* `abicoder`/`experimental`-Pragmas dedupliziert behalten, `SMTChecker` raus.
* Dieselbe Quelldatei, über mehrere Pfade erreichbar, wird nur einmal
  eingebettet — sonst „Identifier already declared“.
* Genau eine SPDX-Zeile im Kopf; alle weiteren werden neutralisiert.

## 7. Ergebnis I: Kompilierbarkeit

| | alt (`mwevariety`) | neu (`mwevariety_fixed`) |
|---|---|---|
| mit `solc` kompilierbar | 1 / 96 | **96 / 96** |
| in GPTScans Toolchain kompiliert und geparst | 1 / 96 | **94 / 96** |
| statische Bestätigung | inaktiv | **aktiv** |

Die zwei Restfälle liegen im Werkzeug, nicht im Korpus, und träfen die
Originale genauso:

* `58_UniV3Vault` — crytic-compile setzt kein `--optimize`, daher „stack too
  deep“.
* `19_TransactionManager` — `ContractSolcParsing` im Falcon/Slither-IR-Parser;
  `solc` selbst kompiliert fehlerfrei.

## 8. Ergebnis II: Die statische Stufe arbeitet

Beleg aus GPTScans Metadaten (`GPTSCAN_META` im `result.log`): Die statische
Stufe reduziert die LLM-Kandidaten — auf dem alten Korpus war das unmöglich.

| Contract | LLM-Kandidaten | nach Static | Vuln vor → nach |
|---|---:|---:|---|
| `14_BadgerYieldSource` | 2 | 1 | 2 → 1 |
| `14_SushiYieldSource` | 2 | 1 | 2 → 1 |
| `14_YieldSourcePrizePool` | 7 | 1 | 6 → 1 |

(Lauf `curated_mwefixed_live`; Felder `functions_after_step_2`,
`functions_after_static`, `vul_before_static` → `vul_after_static`.)

## 9. Ergebnis III: Findings auf dem reparierten Korpus

Live-Lauf über alle 96 Contracts (4 Prozesse, `deepseek-v4-flash`): 36:45 min,
≈ $0,28.

| | alt (degradiert) | neu |
|---|---|---|
| Findings | 11 | **77** |
| Contracts mit Findings | 7 | **40** |
| verschiedene Regeln | 4 | **8** |
| Contracts mit Kandidaten für die statische Stufe | 0 | **56** |
| … davon mit verworfenen Kandidaten | 0 | **39** |
| Kosten / Laufzeit | $0,046 / 13 min | $0,28 / 37 min |

| Regel | Beschreibung | Findings |
|---|---|---:|
| `MWE-200` | Insecure LP Token Value Calculation | 44 |
| `MWE-209` | Wrong Order for Interest or ExchangeRate | 7 |
| `MWE-206` | No Slippage Limit Check | 7 |
| `MWE-203` | Approval Not Revoked | 6 |
| `MWE-205` | Front Running | 4 |
| `MWE-207` | Unauthorized Transfer | 4 |
| `MWE-201` | Insecure Vote Calculation | 4 |
| `MWE-202` | Insecure Token Buying Behavior | 1 |
| **Gesamt** (40 Contracts, alle *high*) | | **77** |

**Einordnung.** Der Sprung von 11 auf 77 heißt nicht, dass GPTScan besser
wurde, sondern dass seine Pipeline erstmals vollständig läuft: Mehr Contracts
kommen durch die Kompilierung, und die geflatteten Dateien geben der LLM-Stufe
den vollen Kontext. Wichtiger als die Menge ist die Qualität: Die 77 Findings
sind statisch bestätigt, die alten 11 kamen ungefiltert aus dem degradierten
Modus. Die 39 Contracts mit verworfenen Kandidaten zeigen, dass der Filter
greift.

## 10. Grenzen

1. **Keine Ground Truth** — die Auswertung bleibt beschreibend.
2. **Compiler-Version.** Offene Pragmas (`^0.8.0`) bauen wir wie SmartBugs mit
   der neuesten passenden `solc`-Version.
3. **Zwei werkzeuginterne Restfälle** (Abschnitt 7).
4. **Nichtdeterminismus** bleibt (74 % Lauf-zu-Lauf-Übereinstimmung auf dem
   alten Korpus).

## 11. Selbst nachbauen

```
# Voraussetzung: git, gh (angemeldet), Web3Bugs sparse unter ~/w3b
python corpus_tools/build_fixed.py map      # Zuordnung + Nachweis
python corpus_tools/build_fixed.py vendor   # npm-Pakete je Contest/Ära
python corpus_tools/build_fixed.py fetch    # fehlende Dateien nachladen
python corpus_tools/build_fixed.py flatten  # -> smartbugs/samples/gptscan/mwevariety_fixed/
python corpus_tools/build_fixed.py check    # 96/96 kompilieren
```

```powershell
# GPTScan auf dem reparierten Korpus (dry = $0, live ≈ $0,40)
.\run_curated.ps1 -Tool gptscan -SkipClone -GptscanDry `
    -FilePattern 'samples:gptscan/mwevariety_fixed/**/*.sol' -RunIdSuffix mwefixed_dry
.\run_curated.ps1 -Tool gptscan -SkipClone `
    -FilePattern 'samples:gptscan/mwevariety_fixed/**/*.sol' -RunIdSuffix mwefixed_live
python corpus_tools/analyze_run.py smartbugs/results/gptscan/curated_mwefixed_live
```

Artefakte: `corpus_tools/{build_fixed.py, README.md, mapping.json,
flatten_stats.json, check_results.json, BUILD_REPORT.json}`
([`../corpus_tools/README.md`](../corpus_tools/README.md)).

---

## Anhang: Belege (geprüft am 20.09.2026)

| Angabe | Beleg | Ergebnis |
|---|---|---|
| 33 / 50 / 13 Nachweisstufen | `mapping.json`, Feld `verified` | bestätigt |
| 96/96 kompilierbar, 1 279 eingebettete Dateien | `BUILD_REPORT.json` | bestätigt |
| 49 Contests | Präfixe in `mapping.json` | bestätigt |
| 94/96 in GPTScans Toolchain | `result.json`/`result.log` der beiden Restfälle in `curated_mwefixed_live` | bestätigt |
| 77 Findings, 40 Contracts, 8 Regeln | alle `result.json` des Laufs | bestätigt |
| 56 / 39 Contracts mit Static-Stufe / Verwurf | `eval/per_contract/curated_mwefixed_live__gptscan.csv` | bestätigt |
| $0,2769, 36,7 min | ebd., `cost_usd`, `start_unix` + `duration_s` | bestätigt |
| Static-Auszug 2→1, 2→1, 6→1 | `GPTSCAN_META` | bestätigt |
| 245 fehlende OpenZeppelin-Verweise | Schritt `scan` mit leerem `VENDOR` nachgerechnet | bestätigt |

`corpus_tools/scan_missing.json` ist git-ignoriert und enthält heute `{}` — der
Zustand *nach* der Reparatur. Mit leerem `VENDOR` stellt sich der Zustand davor
wieder her:

| Paket | fehlende Verweise |
|---|---:|
| `@openzeppelin/contracts` | **245** |
| `@openzeppelin/contracts-upgradeable` | 43 |
| `prb-math` | 33 |
| `hardhat` | 20 |
| `solmate` | 7 |
| übrige (PoolTogether, Uniswap, Chainlink …) | je ≤ 4 |

34 von 96 Dateien waren in diesem Zustand vollständig auflösbar, 62 hatten
Lücken (gezählt je Datei die *verschiedenen* unaufgelösten Importe).
