# `gptscan_mwefixed_v2_dry` gegen `curated_mwefixed_live`

Verglichen wird auf dem Paar **(Contract, MWE-Regel)**, nicht auf Zeilennummern: unter `--main` zaehlen GPTScans Zeilen in der reduzierten Datei und sind mit denen eines Laufs ohne `--main` nicht vergleichbar.

Beide Laeufe bleiben erhalten. Roh: `smartbugs/results/gptscan/<runid>/`.

## Bilanz

| | |
|---|---:|
| Findings neu (`gptscan_mwefixed_v2_dry`) | 5 |
| Findings Referenz (`curated_mwefixed_live`) | 77 |
| deckungsgleich | 4 |
| neu hinzugekommen | 1 |
| verschwunden | 73 |
| verglichene Contracts | 96 |
| Contracts mit Findings (neu / Referenz) | 5 / 40 |

## Reproduzierbarkeit (AP4)

- Anteil der Referenz-Findings, die wieder auftauchen: **5.2 %** (4/77)
- Anteil der neuen Findings, die schon vorher da waren: **80.0 %** (4/5)
- Jaccard ueber (Contract, Regel)-Paare: 0.0769
- Contracts mit gleichem Befund-Ja/Nein: 61/96

Der dokumentierte Referenzbefund lautet: bei Wiederholung trotz `temperature=0` waren nur 74 % der Findings identisch. Die Zahlen oben sind mit dieser Angabe nur dann vergleichbar, wenn dort dieselbe Zaehlweise zugrunde lag -- die Definition steht hier ausdruecklich dabei, damit der Vergleich nachpruefbar bleibt. Dieser Lauf unterscheidet sich von der Referenz zusaetzlich durch `--main`, ist also keine reine Wiederholung.

## Neu hinzugekommen

| Contract | Regel | Anzahl |
|---|---|---:|
| `32_LendingPair` | MWE-205 | 1 |

## Verschwunden

| Contract | Regel | Anzahl |
|---|---|---:|
| `106_NFTLoanFacilitator` | MWE-209 | 1 |
| `107_yVault` | MWE-200 | 1 |
| `10_Visor` | MWE-203 | 1 |
| `14_BadgerYieldSource` | MWE-200 | 1 |
| `14_IdleYieldSource` | MWE-200 | 2 |
| `14_PrizePool` | MWE-207 | 1 |
| `14_PrizePool` | MWE-209 | 2 |
| `14_SushiYieldSource` | MWE-200 | 1 |
| `14_YieldSourcePrizePool` | MWE-209 | 1 |
| `16_TracerPerpetualSwaps` | MWE-209 | 1 |
| `18_LendingPair` | MWE-209 | 1 |
| `192_Position` | MWE-203 | 1 |
| `193_Pair` | MWE-200 | 2 |
| `19_TransactionManager` | MWE-203 | 1 |
| `20_Pool` | MWE-200 | 1 |
| `20_Pool` | MWE-206 | 1 |
| `20_Synth` | MWE-200 | 4 |
| `20_Synth` | MWE-206 | 1 |
| `22_LongShort` | MWE-200 | 1 |
| `25_CompoundMultiOracle` | MWE-200 | 1 |
| `29_HybridPool` | MWE-200 | 2 |
| `29_HybridPool` | MWE-207 | 2 |
| `29_IndexPool` | MWE-200 | 3 |
| `30_Vault` | MWE-200 | 2 |
| `32_LendingPair` | MWE-200 | 3 |
| `36_Basket` | MWE-200 | 1 |
| `37_TempusController` | MWE-200 | 1 |
| `39_VaultTracker` | MWE-207 | 1 |
| `3_MarginRouter` | MWE-209 | 1 |
| `43_DelegatedStaking` | MWE-200 | 2 |
| `5_DAO` | MWE-201 | 4 |
| `5_Pools` | MWE-200 | 1 |
| `5_Pools` | MWE-206 | 3 |
| `5_Router` | MWE-200 | 2 |
| `5_Router` | MWE-206 | 1 |
| `5_USDV` | MWE-200 | 1 |
| `5_Vader` | MWE-200 | 1 |
| `66_sYETIToken` | MWE-200 | 1 |
| `67_Vault` | MWE-203 | 1 |
| `68_BasketFacet` | MWE-200 | 3 |
| `69_NFTXMarketplaceZap` | MWE-202 | 1 |
| `70_VaderPoolV2` | MWE-200 | 2 |
| `70_VaderPoolV2` | MWE-203 | 1 |
| `70_VaderPoolV2` | MWE-206 | 1 |
| `71_IndexTemplate` | MWE-200 | 2 |
| `71_PoolTemplate` | MWE-200 | 3 |
| `75_XDEFIDistribution` | MWE-203 | 1 |
