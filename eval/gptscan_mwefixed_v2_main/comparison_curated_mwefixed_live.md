# `gptscan_mwefixed_v2_main` gegen `curated_mwefixed_live`

Verglichen wird auf dem Paar **(Contract, MWE-Regel)**, nicht auf Zeilennummern: unter `--main` zaehlen GPTScans Zeilen in der reduzierten Datei und sind mit denen eines Laufs ohne `--main` nicht vergleichbar.

Beide Laeufe bleiben erhalten. Roh: `smartbugs/results/gptscan/<runid>/`.

## Bilanz

| | |
|---|---:|
| Findings neu (`gptscan_mwefixed_v2_main`) | 74 |
| Findings Referenz (`curated_mwefixed_live`) | 77 |
| deckungsgleich | 58 |
| neu hinzugekommen | 16 |
| verschwunden | 19 |
| verglichene Contracts | 96 |
| Contracts mit Findings (neu / Referenz) | 37 / 40 |

## Reproduzierbarkeit (AP4)

- Anteil der Referenz-Findings, die wieder auftauchen: **75.3 %** (58/77)
- Anteil der neuen Findings, die schon vorher da waren: **78.4 %** (58/74)
- Jaccard ueber (Contract, Regel)-Paare: 0.6949
- Contracts mit gleichem Befund-Ja/Nein: 87/96

Der dokumentierte Referenzbefund lautet: bei Wiederholung trotz `temperature=0` waren nur 74 % der Findings identisch. Die Zahlen oben sind mit dieser Angabe nur dann vergleichbar, wenn dort dieselbe Zaehlweise zugrunde lag -- die Definition steht hier ausdruecklich dabei, damit der Vergleich nachpruefbar bleibt. Dieser Lauf unterscheidet sich von der Referenz zusaetzlich durch `--main`, ist also keine reine Wiederholung.

## Neu hinzugekommen

| Contract | Regel | Anzahl |
|---|---|---:|
| `10_Visor` | MWE-203 | 1 |
| `13_RCMarket` | MWE-203 | 1 |
| `14_YieldSourcePrizePool` | MWE-200 | 1 |
| `14_YieldSourcePrizePool` | MWE-209 | 1 |
| `18_LendingPair` | MWE-209 | 1 |
| `20_Pool` | MWE-200 | 1 |
| `20_Pool` | MWE-206 | 1 |
| `20_Synth` | MWE-207 | 1 |
| `31_veCVXStrategy` | MWE-200 | 1 |
| `34_ConcentratedLiquidityPosition` | MWE-207 | 1 |
| `39_VaultTracker` | MWE-200 | 1 |
| `43_DelegatedStaking` | MWE-209 | 1 |
| `68_BasketFacet` | MWE-200 | 1 |
| `69_NFTXMarketplaceZap` | MWE-200 | 1 |
| `70_VaderPoolV2` | MWE-206 | 1 |
| `71_PoolTemplate` | MWE-200 | 1 |

## Verschwunden

| Contract | Regel | Anzahl |
|---|---|---:|
| `13_RCTreasury` | MWE-205 | 1 |
| `14_IdleYieldSource` | MWE-200 | 2 |
| `14_PrizePool` | MWE-207 | 1 |
| `14_PrizePool` | MWE-209 | 2 |
| `14_SushiYieldSource` | MWE-200 | 1 |
| `16_TracerPerpetualSwaps` | MWE-209 | 1 |
| `29_HybridPool` | MWE-207 | 1 |
| `30_Vault` | MWE-200 | 1 |
| `39_VaultTracker` | MWE-207 | 1 |
| `3_MarginRouter` | MWE-209 | 1 |
| `43_DelegatedStaking` | MWE-200 | 2 |
| `5_Pools` | MWE-200 | 1 |
| `5_Pools` | MWE-206 | 1 |
| `5_Router` | MWE-200 | 1 |
| `70_VaderPoolV2` | MWE-200 | 1 |
| `71_IndexTemplate` | MWE-200 | 1 |
