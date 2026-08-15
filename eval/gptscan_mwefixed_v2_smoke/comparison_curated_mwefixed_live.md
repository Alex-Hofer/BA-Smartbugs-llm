# `gptscan_mwefixed_v2_smoke` gegen `curated_mwefixed_live`

Verglichen wird auf dem Paar **(Contract, MWE-Regel)**, nicht auf Zeilennummern: unter `--main` zaehlen GPTScans Zeilen in der reduzierten Datei und sind mit denen eines Laufs ohne `--main` nicht vergleichbar.

Beide Laeufe bleiben erhalten. Roh: `smartbugs/results/gptscan/<runid>/`.

## Bilanz

| | |
|---|---:|
| Findings neu (`gptscan_mwefixed_v2_smoke`) | 0 |
| Findings Referenz (`curated_mwefixed_live`) | 2 |
| deckungsgleich | 0 |
| neu hinzugekommen | 0 |
| verschwunden | 2 |
| verglichene Contracts | 3 |
| Contracts mit Findings (neu / Referenz) | 0 / 1 |

## Reproduzierbarkeit (AP4)

- Anteil der Referenz-Findings, die wieder auftauchen: **0.0 %** (0/2)
- Lauf leer
- Jaccard ueber (Contract, Regel)-Paare: 0.0
- Contracts mit gleichem Befund-Ja/Nein: 2/3

Der dokumentierte Referenzbefund lautet: bei Wiederholung trotz `temperature=0` waren nur 74 % der Findings identisch. Die Zahlen oben sind mit dieser Angabe nur dann vergleichbar, wenn dort dieselbe Zaehlweise zugrunde lag -- die Definition steht hier ausdruecklich dabei, damit der Vergleich nachpruefbar bleibt. Dieser Lauf unterscheidet sich von der Referenz zusaetzlich durch `--main`, ist also keine reine Wiederholung.

## Verschwunden

| Contract | Regel | Anzahl |
|---|---|---:|
| `14_IdleYieldSource` | MWE-200 | 2 |
