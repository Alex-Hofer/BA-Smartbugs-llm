# AP5 Vorprüfung: `timeout`-Kommando in den Docker-Images

> Datierte Momentaufnahme · aktueller Stand im Überblick: [`BA-ARBEIT.md`](BA-ARBEIT.md)

Bevor wir AP5 (Timeout-Mechanismus für die LLM-gestützten Analysewerkzeuge)
gebaut haben, mussten wir eines wissen: Ist das POSIX-Kommando `timeout` in
beiden Tool-Images überhaupt vorhanden, und mit welchem Exit-Code meldet es bei
Ablauf? Davon hängen unsere späteren Aufgaben 4 und 8 ab.

**Datum der Messung:** 2026-08-17
**Host:** Docker Desktop, Server 29.0.1 (Windows)
**Geprüfte Images:** `smartbugs/gptscan:1.0`, `smartbugs/llmsmartaudit:1.0`

> **Datierte Messung.** Beide Images wurden seither neu gebaut (GPTScan am
> 18.08.2026, LLMSmartAudit zuletzt am 24.09.2026; `README.md`, „Die vier
> Images“). Die Messung wurde an den Neubauten nicht wiederholt; der
> Mechanismus aus AP5 läuft mit ihnen (`BA-DURCHFUEHRUNGSPROTOKOLL.md` 4.5.6).

## Schritt 1: Vorhandensein prüfen

```bash
docker run --rm --entrypoint sh smartbugs/gptscan:1.0 -c \
  'command -v timeout || echo MISSING; timeout --version 2>&1 | head -1'
docker run --rm --entrypoint sh smartbugs/llmsmartaudit:1.0 -c \
  'command -v timeout || echo MISSING; timeout --version 2>&1 | head -1'
```

Ausgabe `smartbugs/gptscan:1.0`:

```
/usr/bin/timeout
timeout (GNU coreutils) 9.1
```

Ausgabe `smartbugs/llmsmartaudit:1.0`:

```
/usr/bin/timeout
timeout (GNU coreutils) 9.7
```

## Schritt 2: Exit-Code bei Ablauf messen

```bash
docker run --rm --entrypoint sh smartbugs/gptscan:1.0 -c \
  'timeout 1 sleep 5; echo "RC=$?"'
docker run --rm --entrypoint sh smartbugs/llmsmartaudit:1.0 -c \
  'timeout 1 sleep 5; echo "RC=$?"'
```

Ausgabe `smartbugs/gptscan:1.0`: `RC=124`
Ausgabe `smartbugs/llmsmartaudit:1.0`: `RC=124`

## Befund

| Image | `timeout` vorhanden | Variante | Exit-Code bei Ablauf |
|---|---|---|---|
| `smartbugs/gptscan:1.0` | ja, `/usr/bin/timeout` | GNU coreutils 9.1 | `124` |
| `smartbugs/llmsmartaudit:1.0` | ja, `/usr/bin/timeout` | GNU coreutils 9.7 | `124` |

Beide Images enthalten GNU-coreutils-`timeout` und melden bei Ablauf
`RC=124` — kein `MISSING`-Fall, kein BusyBox-Verhalten (`RC=143`). Die in
Aufgaben 4 und 8 vorgesehene Ersatzlösung (Hintergrundprozess mit `kill`)
wird damit nicht benötigt; beide Aufgaben können direkt auf `timeout`
aufbauen.
