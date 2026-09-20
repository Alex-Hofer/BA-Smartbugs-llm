# Rekonstruktion eines kompilierbaren Zieldomänen-Korpus für GPTScan

**Von 1/96 zu 94/96 analysierbaren DeFi-Contracts** · Anhang zur Bachelorarbeit
**Durchführung:** 21.07.2026

Der in der Evaluation genutzte GPTScan-Zieldomänen-Korpus `mwevariety`
(96 DeFi-Contracts) war zu **95/96 nicht kompilierbar**; GPTScan lief dort nur im
degradierten LLM-only-Modus ohne statische Bestätigung. Dieses Dokument beschreibt
die vollständige, reproduzierbare Rekonstruktion eines kompilierbaren Korpus
`mwevariety_fixed` aus den Originalquellen des Web3Bugs-Benchmarks. Ergebnis:
**96/96** Contracts kompilieren nativ, **94/96** kompilieren *und* parsen in
GPTScans echter Analyse-Toolchain, und die statische Bestätigungsstufe — GPTScans
Präzisions-Schutzmechanismus — ist erstmals auf diesem Korpus aktiv.

---

## 1. Motivation: Warum der alte Korpus GPTScan blockierte

Im Durchführungsprotokoll (Fehler #12) waren **95 von 96** mwevariety-Contracts
`InvalidCompilation`; 22 lösten tool-interne Python-Crashes aus. GPTScan besteht
aus zwei Stufen: einer LLM-Stufe, die Schwachstellen-*Kandidaten* vorschlägt, und
einer **statischen Bestätigungsstufe**, die diese Kandidaten am kompilierten
Daten- und Kontrollfluss gegenprüft und False Positives verwirft. Die zweite Stufe
**setzt eine erfolgreiche Kompilierung voraus.** War die Kompilierung nicht
möglich, degradierte GPTScan auf LLM-only — ohne Präzisionsfilter. Die im Protokoll
berichteten 11 mwevariety-Findings entstanden praktisch alle in diesem degradierten
Modus. Ziel war daher, den Korpus so zu reparieren, dass GPTScans *vollständige*
Pipeline läuft.

## 2. Ursachenanalyse

Die Diagnose (Werkzeug `corpus_tools/build_fixed.py`) ergab zwei kombinierte
Defekte:

1. **Fehlender Dependency-Baum.** Die Dateien sind einzeln aus größeren
   Wettbewerbsprojekten extrahierte Fragmente. Ihre `import`-Ziele — Interfaces,
   Basis-Contracts, Libraries und npm-Pakete (OpenZeppelin, solmate, prb-math …) —
   liegen nicht bei, sodass `solc` die Imports nicht auflösen kann. Ein
   Import-Closure-Scan über alle 96 Dateien fand 62 Samples mit Lücken, darunter
   245 unaufgelöste Referenzen auf `@openzeppelin/contracts` sowie zahlreiche
   projekteigene Interfaces (Aufschlüsselung im Anhang unten).
2. **Zerstörte Integrität.** Der Extraktor entfernte Kommentare und Zeilenumbrüche
   und schnitt viele Dateien mitten im Code ab (Truncation). Für die Kompilierung
   ist das irrelevant, weil ausschließlich die *vollständigen Originale* verwendet
   werden — es erklärt aber, warum der Zuordnungsnachweis (Abschnitt 4) mehrstufig
   sein muss.

## 3. Herkunft der Originale

Die mwevariety-Contracts stammen aus **Web3Bugs**
(<https://github.com/ZhangZhuoSJTU/Web3Bugs>), dem im GPTScan-Paper verwendeten
Benchmark. Die Verzeichnis-Präfixe der Samples (`5_`, `13_`, `106_` …) sind die
Web3Bugs-**Contest-IDs**: 96 Dateien aus 49 Contests.

### Rekonstruktions-Pipeline

| Schritt | Zweck | Ergebnis |
|---|---|---|
| `map` | Original je Sample lokalisieren und Byte-Abgleich *beweisen* | 96/96 |
| `scan` | Import-Closure auflösen, fehlende Pakete/Dateien listen | Lückenliste |
| `vendor` | npm-Pakete je (Contest, Solidity-Ära) laden (Lockfile → Fallback) | `vendor/` |
| `fetch` | Dateien holen, die selbst das Snapshot nicht enthält | Gap-Füllung |
| `flatten` | Import-Closure zu *einer* selbstständigen Datei je Sample | `mwevariety_fixed/` |
| `check` | jede geflattete Datei mit pragma-passendem `solc` kompilieren | 96/96 |

Sechsstufige Pipeline in `build_fixed.py`. Insgesamt wurden 1 279
Dependency-Dateien aufgelöst und eingebettet.

## 4. Zuordnungs-Beweis: Ist das rekonstruierte File wirklich *dieses* Sample?

Ein Sample gilt nur als zugeordnet, wenn sein **kommentar- und
whitespace-normalisierter** Bytestrom mit dem des Originals übereinstimmt. Drei
abgestufte Nachweise (Feld `verified` in `corpus_tools/mapping.json`):

| Stufe | Dateien | Bedeutung |
|---|---:|---|
| `equal` | 33 | Normalform *identisch* — eindeutig dieselbe Datei. |
| `truncated-prefix` | 50 | Das Sample ist ein exakter *Präfix* des Originals (der Extraktor hat abgeschnitten); im Mittel enthielt das Sample noch ≈ 14 % des Originals. |
| `header-prefix` | 13 | Zusätzliche Korruption im Sample-Rumpf; es matcht der gemeinsame Header (≥ 200 B: Pragma, Imports, Contract-Kopf). Basename und Contest-ID fixieren die Identität zusätzlich. |

In allen Fällen wird das *vollständige, unbeschädigte Original* eingesetzt — die
Rekonstruktion ist also nicht nur kompilierbar, sondern auch *inhaltlich
vollständiger* als das Sample.

## 5. Nicht-triviale Fälle (Transparenz)

* **Contest-ID-Korrekturen.** Zwei IDs waren im Extrakt um 1 verschoben:
  Trident-Contracts (`34_*`) liegen in Web3Bugs unter Contest 35,
  `46_WrappedIbbtcEth` unter 47 — per Baum-Suche verifiziert.
* **Gap-Quellen.** Das Web3Bugs-Snapshot verflachte den Verzeichnisbaum einiger
  Contests, wodurch Interfaces fehlten. Nachgeladen aus dem LLM4SMAPR-Spiegel
  desselben Datensatzes, den PoolTogether-Protokoll-Repos und npm.
* **Eine rekonstruierte Datei.** `17/.../IChainlinkAggregator.sol` existiert in
  *keiner* Quelle (auch nicht upstream). Rekonstruiert aus der in `Buoy3Pool.sol`
  verwendeten Aufrufform (`latestAnswer()`); entspricht Chainlinks
  Legacy-`AggregatorInterface` und ist als einzige nicht-originale Datei im
  Dateikopf gekennzeichnet.
* **Zwei Kompilier-Repairs.** `8_NFTXEligiblityManager`: `pragma experimental
  ABIEncoderV2;` injiziert (das Projekt aktivierte ABIEncoderV2 global in der
  Build-Config, nicht per Quell-Pragma). `58_UniV3Vault`: benötigt `--optimize`
  (Uniswap-V3-Inline-Assembly, „stack too deep").

## 6. Flattening-Regeln

* Genau **ein** exaktes `pragma solidity <version>;` — die maximale Version, die
  alle Quell-Constraints erfüllt (identisch zu SmartBugs' Auswahlstrategie). Ein
  geflattetes File darf nur ein Versions-Pragma tragen.
* `abicoder`/`experimental`-Pragmas dedupliziert erhalten, `SMTChecker` verworfen.
* **Content-Dedup:** dieselbe Quelldatei, über mehrere Pfade erreichbar (Snapshot
  + nachgeladene Kopie), wird nur *einmal* eingebettet — sonst „Identifier already
  declared".
* Genau *eine* SPDX-Zeile im Kopf; alle weiteren SPDX-Tags (auch in
  Blockkommentaren) neutralisiert.

## 7. Ergebnis I: Kompilierbarkeit

| | alt (`mwevariety`) | neu (`mwevariety_fixed`) |
|---|---|---|
| `solc` nativ kompilierbar | 1 / 96 | **96 / 96** |
| in GPTScans Toolchain kompiliert + geparst | 1 / 96 | **94 / 96** |
| Statische Bestätigungsstufe | inaktiv (degradiert) | **aktiv** |

Die zwei verbleibenden Fälle sind *tool-intern*, kein Korpus-Defekt; sie träfen
die Originalquellen gleichermaßen:

* `58_UniV3Vault` — crytic-compile (GPTScans Compiler-Frontend) setzt kein
  `--optimize`, daher „stack too deep" in Uniswap-V3-Inline-Assembly.
* `19_TransactionManager` — `ContractSolcParsing` im Falcon/Slither-IR-Parser;
  `solc` selbst kompiliert die Datei fehlerfrei.

## 8. Ergebnis II: Die statische Bestätigungsstufe läuft wieder

Der entscheidende Nachweis stammt aus GPTScans Lauf-Metadaten (`GPTSCAN_META` im
`result.log` jedes Tasks): Die statische Stufe reduziert die Zahl der
LLM-Kandidaten *nachweislich* — genau das war auf dem kaputten Korpus unmöglich.

| Contract | LLM-Kandidaten | nach Static | Vuln vor → nach |
|---|---:|---:|---|
| `14_BadgerYieldSource` | 2 | 1 | 2 → 1 |
| `14_SushiYieldSource` | 2 | 1 | 2 → 1 |
| `14_YieldSourcePrizePool` | 7 | 1 | 6 → 1 |

Auszug aus dem Lauf `curated_mwefixed_live`. „LLM-Kandidaten" und „nach Static"
sind die Felder `functions_after_step_2` und `functions_after_static`, die letzte
Spalte `vul_before_static` → `vul_after_static`. `vul_before_static >
vul_after_static` belegt: der Präzisions-Schutzmechanismus arbeitet.

## 9. Ergebnis III: Findings auf reparierter Zieldomäne

Der Live-Lauf über alle 96 Contracts (`--processes 4`, DeepSeek
`deepseek-v4-flash`) lief 36:45 min für ≈ $0.28. Alle Findings sind
*static-bestätigt* (wo die statische Stufe lief) — im Gegensatz zu den
ungefilterten LLM-only-Ausgaben des alten Laufs.

| | alt (degradiert) | neu (`_fixed`) |
|---|---|---|
| Findings gesamt | 11 | **77** |
| Contracts mit Findings | 7 | **40** |
| Verschiedene MWE-Regeln | 4 | **8** |
| Contracts mit aktiver Static-Stufe | 0 | **56** |
| Contracts, deren Kandidaten Static verwarf | 0 | **39** |
| Kosten / Laufzeit | $0.046 / 13 min | $0.28 / 37 min |
| Statische Bestätigung | inaktiv | aktiv |

Alle 77 Findings haben Severity *high*. „Contracts mit aktiver Static-Stufe"
zählt die Contracts, für die die LLM-Stufe überhaupt Kandidaten an die statische
Stufe übergab (`vul_before_static > 0`).

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
| **Gesamt** (auf 40 Contracts, alle Severity *high*) | | **77** |

Der reparierte Korpus aktiviert **8** statt 4 Regeltypen. Alle Regelnamen stammen
unmittelbar aus GPTScans eigener Ausgabe (`name`-Feld je Finding).

**Einordnung (wissenschaftliche Ehrlichkeit).** Der Anstieg von 11 auf 77 Findings
misst *nicht*, dass GPTScan „besser" wurde, sondern dass seine Pipeline erstmals
vollständig läuft: mehr Contracts passieren den Compile-Gate, und die geflatteten
Dateien enthalten den vollen Kontext, den die LLM-Stufe auswerten kann.
Entscheidend ist die *Qualität*: die 77 Findings sind static-bestätigt, während
die alten 11 ungefiltert aus dem degradierten Modus stammten. Die 39 Contracts mit
verworfenen Kandidaten belegen, dass der Präzisionsfilter tatsächlich greift.

## 10. Limitationen

1. **Keine vendorte Ground Truth.** mwevariety besitzt keinen annotierten
   Referenzstand; die Auswertung bleibt deskriptiv/qualitativ (kein
   Recall/Precision).
2. **Compiler-Version.** Contracts mit offenem Pragma (`^0.8.0`) werden mit der
   neuesten kompatiblen `solc`-Version gebaut (wie in SmartBugs); die Analyse
   erfolgt am Quelltext, die Kompilierung dient der statischen Bestätigung.
3. **Zwei tool-interne Grenzfälle** (`58_UniV3Vault`, `19_TransactionManager`)
   bleiben bestehen und sind dokumentiert.
4. **Nicht-Determinismus** LLM-basierter Scanner bleibt bestehen (im Protokoll mit
   74 % Lauf-zu-Lauf-Übereinstimmung quantifiziert).

## 11. Reproduktion

```
# Voraussetzung: git, gh (authentifiziert), Web3Bugs sparse unter ~/w3b
python corpus_tools/build_fixed.py map      # Zuordnung + Beweis
python corpus_tools/build_fixed.py vendor   # npm-Pakete je Contest/Aera
python corpus_tools/build_fixed.py fetch    # fehlende Dateien aus Gap-Quellen
python corpus_tools/build_fixed.py flatten  # -> smartbugs/samples/gptscan/mwevariety_fixed/
python corpus_tools/build_fixed.py check    # 96/96 kompilieren
```

```powershell
# GPTScan auf dem reparierten Korpus (dry = $0, live = ~$0.4):
.\run_curated.ps1 -Tool gptscan -SkipClone -GptscanDry `
    -FilePattern 'samples:gptscan/mwevariety_fixed/**/*.sol' -RunIdSuffix mwefixed_dry
.\run_curated.ps1 -Tool gptscan -SkipClone `
    -FilePattern 'samples:gptscan/mwevariety_fixed/**/*.sol' -RunIdSuffix mwefixed_live
python corpus_tools/analyze_run.py smartbugs/results/gptscan/curated_mwefixed_live
```

**Artefakte:** `corpus_tools/{build_fixed.py, README.md, mapping.json,
flatten_stats.json, check_results.json, BUILD_REPORT.json}`; reparierter Korpus
unter `smartbugs/samples/gptscan/mwevariety_fixed/`.

---

## Nachprüfung am Repository (20.09.2026)

Diese Fassung ersetzt die frühere `.tex`/`.pdf`-Ausarbeitung gleichen Namens. Alle
Kennzahlen wurden dabei gegen die im Repository liegenden Artefakte gegengeprüft.

| Angabe | Beleg | Ergebnis |
|---|---|---|
| 33 / 50 / 13 Nachweisstufen | `corpus_tools/mapping.json`, Feld `verified` | bestätigt |
| 96/96 nativ kompilierbar, 1 279 eingebettete Dateien | `corpus_tools/BUILD_REPORT.json` (`compiled_ok`, `total_flattened_files`) | bestätigt |
| 49 Contests | Präfixe in `corpus_tools/mapping.json` | bestätigt |
| 94/96 in GPTScans Toolchain | `result.json`/`result.log` von `58_UniV3Vault` (InvalidCompilation) und `19_TransactionManager` (ContractSolcParsing) im Lauf `curated_mwefixed_live` | bestätigt |
| 77 Findings auf 40 Contracts, 8 Regeln, alle *high* | alle `result.json` in `smartbugs/results/gptscan/curated_mwefixed_live/` | bestätigt |
| 56 mit aktiver Static-Stufe, 39 mit verworfenen Kandidaten | `eval/per_contract/curated_mwefixed_live__gptscan.csv`, Spalten `vul_before_static`, `vul_after_static` | bestätigt |
| $0.28 / 36:45 min | ebd., Spalten `cost_usd` ($0,2769) und `start_unix` + `duration_s` (36,7 min Wanduhr) | bestätigt |
| Static-Auszug 2→1, 2→1, 6→1 | `GPTSCAN_META` in den jeweiligen `result.log` | bestätigt |
| 245 fehlende OpenZeppelin-Referenzen | `corpus_tools/build_fixed.py`, Schritt `scan` — nachgerechnet mit auf ein leeres Verzeichnis gesetztem `VENDOR` | bestätigt (siehe Anmerkung unten) |

**Anmerkung zu den 245.** `corpus_tools/scan_missing.json` ist git-ignoriert und
enthält heute `{}` — das ist kein Datenverlust, sondern der Zustand *nach* der
Reparatur: Mit den vendorten Paketen daneben löst sich jeder Import auf. Die 245
stammen aus dem Zustand *davor*. Setzt man `VENDOR` im `scan`-Schritt auf ein
leeres Verzeichnis, stellt sich dieser Zustand wieder her; die Zählung ergibt
dann:

| Paket | fehlende Referenzen |
|---|---:|
| `@openzeppelin/contracts` | **245** |
| `@openzeppelin/contracts-upgradeable` | 43 |
| `prb-math` | 33 |
| `hardhat` | 20 |
| `solmate` | 7 |
| übrige (PoolTogether, Uniswap, Chainlink, …) | je ≤ 4 |

Vollständig auflösbar waren in diesem Zustand 34 von 96 Closures, 62 hatten
Lücken. Gezählt wird wie in `cmd_scan`: je Sample die *verschiedenen*
unaufgelösten Import-Spezifikationen.
