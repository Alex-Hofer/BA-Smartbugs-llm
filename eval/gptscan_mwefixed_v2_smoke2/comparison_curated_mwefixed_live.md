# `gptscan_mwefixed_v2_smoke2` gegen `curated_mwefixed_live`

Verglichen wird auf dem Paar **(Contract, MWE-Regel)**, nicht auf Zeilennummern: unter `--main` zaehlen GPTScans Zeilen in der reduzierten Datei und sind mit denen eines Laufs ohne `--main` nicht vergleichbar.

Beide Laeufe bleiben erhalten. Roh: `smartbugs/results/gptscan/<runid>/`.

## Bilanz

| | |
|---|---:|
| Findings neu (`gptscan_mwefixed_v2_smoke2`) | 6 |
| Findings Referenz (`curated_mwefixed_live`) | 6 |
| deckungsgleich | 5 |
| neu hinzugekommen | 1 |
| verschwunden | 1 |
| verglichene Contracts | 3 |
| Contracts mit Findings (neu / Referenz) | 2 / 3 |

## Reproduzierbarkeit (AP4)

- Anteil der Referenz-Findings, die wieder auftauchen: **83.3 %** (5/6)
- Anteil der neuen Findings, die schon vorher da waren: **83.3 %** (5/6)
- Jaccard ueber (Contract, Regel)-Paare: 0.75
- Contracts mit gleichem Befund-Ja/Nein: 2/3

Der dokumentierte Referenzbefund lautet: bei Wiederholung trotz `temperature=0` waren nur 74 % der Findings identisch. Die Zahlen oben sind mit dieser Angabe nur dann vergleichbar, wenn dort dieselbe Zaehlweise zugrunde lag -- die Definition steht hier ausdruecklich dabei, damit der Vergleich nachpruefbar bleibt. Dieser Lauf unterscheidet sich von der Referenz zusaetzlich durch `--main`, ist also keine reine Wiederholung.

## Neu hinzugekommen

| Contract | Regel | Anzahl |
|---|---|---:|
| `71_IndexTemplate` | MWE-200 | 1 |

## Verschwunden

| Contract | Regel | Anzahl |
|---|---|---:|
| `14_BadgerYieldSource` | MWE-200 | 1 |
