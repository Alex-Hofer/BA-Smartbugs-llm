# mwevariety_fixed — Rekonstruktion eines kompilierbaren GPTScan-Korpus

## Problem

Der vendorte Korpus `smartbugs/samples/gptscan/mwevariety/` (96 `.sol`) ist für
GPTScan **weitgehend unbrauchbar**: im Durchführungsprotokoll (Fehler #12) waren
**95/96 `InvalidCompilation`**, 22/96 lösten Folge-Crashes aus. GPTScan lief dort
nur im **degradierten LLM-only-Modus** — die statische Bestätigungsstufe (der
Präzisions-Filter) war inaktiv.

Ursachenanalyse (`build_fixed.py`) zeigte: Die Dateien sind **einzeln aus
größeren Wettbewerbs-Projekten extrahierte Fragmente**, denen zweierlei fehlt:

1. **der Import-/Dependency-Baum** — Interfaces, Basis-Contracts, Libraries,
   npm-Pakete (OpenZeppelin, solmate …) liegen nicht bei → `solc` findet die
   `import`-Ziele nicht.
2. **Integrität** — der Extraktor hat Kommentare entfernt und Zeilenumbrüche
   zerstört; viele Dateien sind zusätzlich **mitten im Code abgeschnitten**
   (Truncation). Für die Kompilierung ist das irrelevant, weil wir ohnehin die
   **vollständigen Originale** verwenden — aber es erklärt, warum der Byte-Abgleich
   mehrstufig sein muss.

## Herkunft der Originale

Die mwevariety-Contracts stammen aus **Web3Bugs**
(`github.com/ZhangZhuoSJTU/Web3Bugs`, `contracts/<contest>/…`), dem
Benchmark-Datensatz des GPTScan-Papers (dort als „mwevariety" referenziert). Die
Verzeichnis-Präfixe (`5_`, `13_`, `106_` …) sind die Web3Bugs-**Contest-IDs**
(49 Contests, 96 Dateien).

## Pipeline (`build_fixed.py`)

| Schritt | Zweck | Ergebnis |
|--------|-------|----------|
| `map`     | Jedes Sample seinem Original zuordnen und den **Byte-Abgleich beweisen** | `mapping.json` — 96/96 |
| `scan`    | Import-Closure jedes Originals auflösen, fehlende Pakete/Dateien listen | Lückenliste |
| `vendor`  | npm-Pakete pro (Contest, Solidity-Ära) laden — Version aus Lockfile, sonst Ära-Fallback | `vendor/<contest>@<era>/` |
| `fetch`   | Dateien, die selbst das Web3Bugs-Snapshot nicht enthält, aus Gap-Quellen holen | siehe unten |
| `flatten` | Import-Closure (DFS post-order) zu **einer selbstständigen Datei** je Sample zusammenführen | `../smartbugs/samples/gptscan/mwevariety_fixed/` |
| `check`   | Jede geflattete Datei mit pragma-passendem `solc` **kompilieren** | `check_results.json` |

Reproduktion (Voraussetzung: `git`, `gh` authentifiziert, Web3Bugs unter `~/w3b`):
```
python corpus_tools/build_fixed.py map
python corpus_tools/build_fixed.py vendor
python corpus_tools/build_fixed.py fetch
python corpus_tools/build_fixed.py flatten
python corpus_tools/build_fixed.py check
```

## Wie der Zuordnungs-Beweis funktioniert (`map`)

Ein Sample gilt nur als zugeordnet, wenn sein **kommentar- und
whitespace-normalisierter** Bytestrom mit dem des Originals übereinstimmt.
Drei Stufen (`verified`-Feld in `mapping.json`):

- **`equal`** (33): Normalform identisch — eindeutig dasselbe File.
- **`truncated-prefix`** (50): Sample ist ein **Präfix** des Originals (der
  Extraktor hat abgeschnitten). `sample_coverage_pct` gibt an, wie viel des
  Originals das Sample noch enthielt (Median ~14 %).
- **`header-prefix`** (13): Extra-Korruption im Sample-Rumpf; es matcht nur der
  gemeinsame Header (≥200 B: Pragma + Imports + Contract-Kopf). Basename +
  Contest fixieren die Identität zusätzlich.

In allen Fällen wird das **vollständige, unbeschädigte Original** verwendet.

## Nicht-triviale Fälle (dokumentiert für die BA)

- **Contest-ID-Korrekturen** (`CONTEST_OVERRIDE`): Der Extraktor hat zwei IDs
  um 1 verschoben — Trident-Contracts (`34_*`) liegen in Web3Bugs unter Contest
  **35**, `46_WrappedIbbtcEth` unter **47**. Per Baum-Suche verifiziert.
- **Gap-Quellen** (`GAP_SOURCES`): Das Web3Bugs-Snapshot hat den Verzeichnisbaum
  einiger Contests verflacht, wodurch Interfaces fehlen. Nachgeladen aus:
  dem LLM4SMAPR-Spiegel desselben Datensatzes (`CheWang09/LLM4SMAPR`), den
  PoolTogether-Protokoll-Repos (badger-/sushi-/idle-yield-source) und npm.
- **1 rekonstruierte Datei**: `17/contracts/interfaces/IChainlinkAggregator.sol`
  existiert in **keiner** Quelle (auch nicht upstream). Rekonstruiert aus der
  in `Buoy3Pool.sol` verwendeten Aufrufform (`latestAnswer()`), entspricht
  Chainlinks Legacy-`AggregatorInterface`. Als einzige nicht-originale Datei
  im Kopf gekennzeichnet.
- **2 Kompilier-Repairs** (`check`):
  - `8_NFTXEligiblityManager`: `pragma experimental ABIEncoderV2;` injiziert —
    das Original-Projekt aktivierte ABIEncoderV2 global in der Build-Config, nicht
    per Quell-Pragma.
  - `58_UniV3Vault`: braucht `--optimize` (Uniswap-V3-Inline-Assembly,
    „stack too deep").

## Flattening-Regeln

- **Ein** exaktes `pragma solidity <version>;` (die maximale Version, die alle
  Quell-Constraints erfüllt — identisch zu SmartBugs' Auswahlstrategie). Ein
  geflattetes File darf nur ein Versions-Pragma haben.
- `abicoder`/`experimental`-Pragmas dedupliziert erhalten; `SMTChecker` verworfen.
- **Content-Dedup**: Dieselbe Quelldatei, über mehrere Pfade erreichbar
  (Snapshot + nachgeladene Kopie), wird nur **einmal** eingebettet — sonst
  „Identifier already declared".
- Genau **eine** SPDX-Zeile im Kopf; alle weiteren SPDX-Tags (auch in
  Blockkommentaren) neutralisiert.

## Ergebnis

- **96/96** kompilieren nativ (pragma-passendes `solc`, `check_results.json`).
- **94/96** kompilieren **und** parsen in GPTScans echter Toolchain
  (crytic-compile/falcon; Dry-Lauf `curated_mwefixed_dry`). Die 2 Ausnahmen sind
  **tool-intern**, kein Korpus-Defekt:
  - `58_UniV3Vault` — crytic-compile setzt kein `--optimize` → „stack too deep".
  - `19_TransactionManager` — `ContractSolcParsing` (Falcon/Slither-IR-Bug);
    `solc` selbst kompiliert die Datei fehlerfrei.

Beide Grenzfälle beträfen die Originalquellen gleichermaßen.

## Artefakte

```
corpus_tools/
  build_fixed.py        Pipeline (map/scan/vendor/fetch/flatten/check)
  mapping.json          Sample -> Original + Verifikationsstufe
  flatten_stats.json    je Sample: #Dateien, solc-Version, Pragmas
  check_results.json    je Sample: Kompilierstatus (+ Repair-Notiz)
  BUILD_REPORT.json     Gesamtbilanz
  vendor/               nachgeladene npm-Pakete (git-ignoriert)
  make_main_corpus.py   Kopie des Korpus mit Hauptcontract-Namen für SmartBugs' --main
                        (Zielordner mwevariety_fixed_main/, git-ignoriert, seit 24.09.2026)
smartbugs/samples/gptscan/mwevariety_fixed/   96 selbstständige .sol
```
