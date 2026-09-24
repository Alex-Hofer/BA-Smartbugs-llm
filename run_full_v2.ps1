<#
.SYNOPSIS
  GPTScan-Volllauf ueber den DeFi-Korpus mwevariety_fixed (96 Contracts),
  ausschliesslich ueber SmartBugs, mit aktivem MAIN-Parameter (AP6).

.DESCRIPTION
  WOZU DIESE DATEI DA IST
  Sie fuehrt den ersten GPTScan-Lauf, der --main setzt. Alle 17 Altlaeufe unter
  smartbugs\results\gptscan\ sind ohne --main entstanden (nachpruefbar: der
  Docker-Entrypoint in smartbugs.json endet dort auf '0'). Der Vergleich
  Alt gegen Neu ist damit ein Vergleich MAIN=0 gegen MAIN=1 auf demselben
  Korpus, demselben Image und demselben Modell.

  WORIN SIE SICH VON run_curated.ps1 UNTERSCHEIDET
  run_curated.ps1 bleibt unveraendert -- es dokumentiert die bisherigen Laeufe
  und wird von dieser Datei nicht ersetzt, sondern ergaenzt. Unterschiede:
    1. --main wird gesetzt (der eigentliche Zweck; AP6).
    2. Nur GPTScan. LLMSmartAudit laeuft hier nicht mit.
    3. Korpus ist samples\gptscan\mwevariety_fixed (96 .sol), nicht
       smartbugs-curated (143). Kein git clone noetig.
    4. -Mode dry|smoke|full statt getrennter Schalter. smoke faehrt genau die
       drei in -SmokeFiles genannten Contracts live.
    5. --mem-limit wird gesetzt und, wie --timeout und --processes, ins
       Laufprotokoll geschrieben.
    6. Am Ende entsteht ein Laufprotokoll unter eval\<runid>\run_params.json;
       die SmartBugs-Rohergebnisse bleiben unangetastet.

  WELCHE LAEUFE DAMIT ENTSTANDEN SIND
    2026-08-15  gptscan_mwefixed_v2_dry    -Mode dry    96 Contracts, 0 API-Calls
    2026-08-15  gptscan_mwefixed_v2_smoke  -Mode smoke   3 Contracts live
    2026-08-15  gptscan_mwefixed_v2_main   -Mode full   96 Contracts live, --main

  BEKANNTE EIGENHEITEN, die hier bewusst nicht "repariert" werden
  * Modell ist deepseek-v4-flash. deepseek-chat ist von DeepSeek abgeschaltet
    und liefert HTTP 400 -- niemals setzen.
  * Provider/Modell/Base-URL sind NICHT im Image eingebrannt, sondern werden
    zur Laufzeit ueber Umgebungsvariablen gewaehlt (config.yaml: env-Liste).
    Ein Modellwechsel braucht deshalb keinen Rebuild.
  * Die GPTScan-Keyword-Falle (Pfade mit external/openzeppelin/uniswap/
    pancakeswap/legacy/test liefern still leeren Output) ist in
    tools\gptscan\scripts\do_solidity.sh geloest: die Datei wird nach
    /work/input kopiert, der SmartBugs-Mount /sb wird nicht analysiert.
  * --timeout wirkt seit AP5 innerhalb des Containers (Bremse bei GPTScan,
    Netz als letzte Stufe bei beiden Werkzeugen); der aeussere Docker-Abschuss
    bleibt zusaetzlich als letzte Instanz bestehen. Der Wert steht im
    Protokoll.
  * --continue-on-errors ist bei --main auf diesem Korpus PFLICHT, nicht Kuer.
    sb\smartbugs.py:119 bildet den erwarteten Contract-Namen als Dateiname ohne
    Endung -- also MIT dem Zahlpraefix ("106_NFTLoanFacilitator"). Ein solcher
    Bezeichner ist in Solidity nicht bildbar, also meldet SmartBugs fuer ALLE 96
    Dateien "Contract '<name>' not found" als Kompositionsfehler. Ohne
    --continue-on-errors wuerde daraufhin kein einziger Task laufen. Die
    tatsaechliche Contract-Auswahl trifft ohnehin nicht SmartBugs, sondern
    main_contract.py im Container, das das Praefix abschneidet. Die Meldung ist
    damit folgenlos und erscheint nicht in den result.json der Tasks --
    nachgewiesen im Lauf gptscan_mwefixed_v2_dry: 96/96 Tasks mit MAIN='1'
    ausgefuehrt, kein Task traegt diesen Fehler.
  * Unter --main scheitern auf diesem Korpus drei Contracts mit Exit 127
    (31_veCVXStrategy, 62_Locke, 8_NFTXEligiblityManager): ihr Dateiname
    benennt keinen enthaltenen Contract. SmartBugs fuehrt das als fail mit
    Klartext, nicht als "keine Findings" -- siehe sb\parse_utils.py.
    -MainFallback faehrt genau diese Faelle anschliessend ohne --main nach,
    in einen eigenen Ergebnisordner <runid>_nomain.

.PARAMETER Mode
  dry   : GPTSCAN_DRY_RUN=1 ueber den ganzen Korpus. Kostet nichts.
  smoke : die drei Contracts aus -SmokeFiles live. Fuer die Kostenhochrechnung.
  full  : der ganze Korpus live.
.PARAMETER Processes
  Parallele SmartBugs-Tasks. Default 4 (im Altlauf ohne Rate-Limits bestaetigt).
.PARAMETER TimeoutSec
  Docker-Timeout je Task. Default 1800 (laengster Altlauf-Task: 658 s).
.PARAMETER MemLimit
  Docker-Speichergrenze je Container, z.B. '4g'.
.PARAMETER RunId
  SmartBugs-Laufkennung. Default je Mode, siehe oben. Ergebnisse landen unter
  smartbugs\results\gptscan\<RunId>\. Ohne --overwrite bleiben vorhandene
  Task-Ordner stehen -- fuer einen frischen Lauf eine neue RunId waehlen.
.PARAMETER Main
  --main setzen. Default $true. Mit -Main:$false wird der Altlauf-Modus gefahren.
.PARAMETER MainFallback
  Nach dem Lauf die mit Exit 127 gescheiterten Contracts ohne --main nachfahren.
.PARAMETER Corpus
  SmartBugs-Dateimuster 'ROOT:GLOB' relativ zu smartbugs\. Genau EIN Doppelpunkt.

.EXAMPLE
  .\run_full_v2.ps1 -Mode dry
.EXAMPLE
  .\run_full_v2.ps1 -Mode smoke
.EXAMPLE
  .\run_full_v2.ps1 -Mode full -MainFallback

  Voraussetzungen: Docker Desktop laeuft; Image smartbugs/gptscan:1.0 lokal
  gebaut (docker build -t smartbugs/gptscan:1.0 .\GPTScan); DEEPSEEK_API_KEY in
  GPTScan\.env (git-ignoriert, wird nie ausgegeben; sb\docker.py redigiert ihn
  zusaetzlich vor dem Protokollieren).
#>
[CmdletBinding()]
param(
    [ValidateSet('dry', 'smoke', 'full')]
    [string]$Mode = 'dry',
    [int]$Processes = 4,
    [int]$TimeoutSec = 1800,
    [string]$MemLimit = '4g',
    [string]$RunId = '',
    [bool]$Main = $true,
    [switch]$MainFallback,
    [string]$Corpus = 'samples:gptscan/mwevariety_fixed/**/*.sol',
    [string[]]$SmokeFiles = @('25_CTokenInterface.sol', '14_IdleYieldSource.sol', '23_nTokenAction.sol'),
    # Backend zur Laufzeit waehlbar. Die Defaults entsprechen den aufgezeichneten
    # Laeufen; ein abweichender Lauf gehoert unter eine eigene -RunId.
    #   deepseek -> DEEPSEEK_API_KEY, openai -> OPENAI_API_KEY,
    #   custom   -> GPTSCAN_API_KEY + -BaseUrl (nur dort wertet GPTScan sie aus)
    [ValidateSet('deepseek', 'openai', 'custom')]
    [string]$Provider = 'deepseek',
    [string]$Model = 'deepseek-v4-flash',
    [string]$BaseUrl = ''
)

$ErrorActionPreference = 'Stop'
$RepoRoot     = $PSScriptRoot
$SmartBugsDir = Join-Path $RepoRoot 'smartbugs'
$Python       = Join-Path $SmartBugsDir '.venv\Scripts\python.exe'
$EnvFile      = Join-Path $RepoRoot 'GPTScan\.env'
$EvalRoot     = Join-Path $RepoRoot 'eval'

function Write-Log([string]$Msg) {
    Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $Msg)
}

function Invoke-SbRun {
    # Pattern ist bewusst [string[]]: SmartBugs nimmt mehrere -f Muster. Sie
    # muessen als EINZELNE Argumente ankommen -- in ein Array-Literal gelegt
    # wuerde PowerShell sie zu einem Argument mit Leerzeichen verketten, und
    # SmartBugs bricht dann mit "contains more than one colon" ab.
    param([string[]]$Pattern, [string]$RunIdent, [bool]$UseMain)
    $sbArgs = @('-m', 'sb', '-t', 'gptscan', '-f')
    $sbArgs += $Pattern
    $sbArgs += @(
        '--json', '--sarif',
        '--timeout', $TimeoutSec,
        '--processes', $Processes,
        '--mem-limit', $MemLimit,
        '--continue-on-errors',
        '--results', ('results/${TOOL}/' + $RunIdent + '/${RELDIR}/${FILENAME}'),
        '--runid', $RunIdent
    )
    if ($UseMain) { $sbArgs += '--main' }

    Push-Location $SmartBugsDir
    try {
        Write-Log ("sb-Aufruf: python -m sb " + (($sbArgs | Select-Object -Skip 2) -join ' '))
        & $Python $sbArgs | Out-Host
        return $LASTEXITCODE
    }
    finally { Pop-Location }
}

try {
    # ---------------------------------------------------------------- Prechecks
    Write-Log "Prechecks..."
    if (-not (Test-Path $Python)) { throw "SmartBugs-venv fehlt: $Python" }

    # cmd uebernimmt die Umleitung: vermeidet PS5.1-NativeCommandError bei stderr
    cmd /c "docker info >nul 2>&1"
    if ($LASTEXITCODE -ne 0) { throw "Docker-Daemon nicht erreichbar - Docker Desktop starten." }
    if (-not (docker images -q smartbugs/gptscan:1.0)) {
        throw "Image smartbugs/gptscan:1.0 fehlt. Bauen: docker build -t smartbugs/gptscan:1.0 .\GPTScan"
    }

    if (-not $RunId) {
        $RunId = switch ($Mode) {
            'dry'   { 'gptscan_mwefixed_v2_dry' }
            'smoke' { 'gptscan_mwefixed_v2_smoke' }
            'full'  { 'gptscan_mwefixed_v2_main' }
        }
    }

    # ---------------------------------------------------------------- API-Key
    # Nur bei live-Laeufen noetig; im Dry-Run wird kein Call abgesetzt.
    if (-not (Test-Path $EnvFile)) { throw "Key-Datei fehlt: $EnvFile" }
    $loaded = New-Object System.Collections.Generic.List[string]
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $name  = $Matches[1]
            $value = $Matches[2].Trim().Trim([char]34).Trim([char]39)
            if ($value) { Set-Item -Path "Env:$name" -Value $value; $loaded.Add($name) }
        }
    }
    Write-Log ("Aus $EnvFile geladen: " + ($loaded -join ', ') + " (Werte werden nie ausgegeben).")

    # ------------------------------------ Rangfolge: Parameter > .env > Standard
    # Ohne diese Aufloesung ueberschrieb der Runner jeden .env-Eintrag mit seinem
    # eigenen Standardwert - ein dort eingetragenes Modell blieb wirkungslos.
    $fromEnv = New-Object System.Collections.Generic.List[string]
    if (-not $PSBoundParameters.ContainsKey('Provider') -and $env:GPTSCAN_PROVIDER) {
        $Provider = $env:GPTSCAN_PROVIDER; $fromEnv.Add("Provider=$Provider")
    }
    if (-not $PSBoundParameters.ContainsKey('Model') -and $env:GPTSCAN_MODEL) {
        $Model = $env:GPTSCAN_MODEL; $fromEnv.Add("Model=$Model")
    }
    if (-not $PSBoundParameters.ContainsKey('BaseUrl') -and $env:GPTSCAN_BASE_URL) {
        $BaseUrl = $env:GPTSCAN_BASE_URL; $fromEnv.Add("BaseUrl=$BaseUrl")
    }
    if ($fromEnv.Count) {
        Write-Log ("Aus $EnvFile uebernommen: " + ($fromEnv -join ', ') +
                   " (ein ausdruecklicher Parameter haette Vorrang).")
    }

    $keyVar = switch ($Provider) {
        'deepseek' { 'DEEPSEEK_API_KEY' }
        'openai'   { 'OPENAI_API_KEY' }
        'custom'   { 'GPTSCAN_API_KEY' }
    }
    if ($Mode -ne 'dry') {
        if (-not (Get-Item -Path "Env:$keyVar" -ErrorAction SilentlyContinue)) {
            throw "$keyVar fehlt in $EnvFile - wird fuer -Provider $Provider gebraucht."
        }
        if ($Provider -eq 'custom' -and -not $BaseUrl) {
            throw "-Provider custom verlangt -BaseUrl (OpenAI-kompatibler Endpunkt)."
        }
    }

    # ---------------------------------------------------------------- Backend
    $env:GPTSCAN_PROVIDER = $Provider
    $env:GPTSCAN_MODEL    = $Model   # Default deepseek-v4-flash; deepseek-chat ist abgeschaltet (HTTP 400)
    # GPTSCAN_BASE_URL wertet GPTScan nur bei provider=custom aus
    # (src/llm_backend.py:base_url); ausserhalb bleibt die Variable ungesetzt.
    if ($Provider -eq 'custom' -and $BaseUrl) { $env:GPTSCAN_BASE_URL = $BaseUrl }
    else { Remove-Item Env:GPTSCAN_BASE_URL -ErrorAction SilentlyContinue }
    Write-Log "Backend: provider=$Provider model=$Model$(if ($BaseUrl) { " base_url=$BaseUrl" })"
    # Image-ID festhalten (auch in run_params.json): der Tag bleibt bei einem
    # Neubau gleich, die ID nicht.
    $imageId = @(cmd /c 'docker image inspect --format "{{.Id}}" smartbugs/gptscan:1.0 2>nul') | Select-Object -First 1
    Write-Log "Image: smartbugs/gptscan:1.0 $imageId"
    if ($Mode -eq 'dry') { $env:GPTSCAN_DRY_RUN = '1' }
    else { Remove-Item Env:GPTSCAN_DRY_RUN -ErrorAction SilentlyContinue }

    # Schluessel, die dieser Lauf nicht braucht, wieder aus der Prozessumgebung
    # nehmen; die Allowlist (env: in config.yaml) reicht sonst jeden gesetzten
    # Schluessel in den Container. Im Dry-Run braucht es gar keinen.
    $dropKeys = switch ($Provider) {
        'deepseek' { @('OPENAI_API_KEY', 'GPTSCAN_API_KEY') }
        'openai'   { @('DEEPSEEK_API_KEY', 'GPTSCAN_API_KEY') }
        'custom'   { @('DEEPSEEK_API_KEY', 'OPENAI_API_KEY') }
    }
    if ($Mode -eq 'dry') { $dropKeys = @('DEEPSEEK_API_KEY', 'OPENAI_API_KEY', 'GPTSCAN_API_KEY') }
    $dropped = @($dropKeys | Where-Object { Test-Path "Env:$_" })
    foreach ($k in $dropped) { Remove-Item "Env:$k" }
    if ($dropped.Count) {
        Write-Log ("Nicht benoetigte Schluessel aus der Umgebung entfernt: " + ($dropped -join ', '))
    }

    # ---------------------------------------------------------------- Muster
    $pattern = $Corpus
    if ($Mode -eq 'smoke') {
        # SmartBugs nimmt mehrere -f Muster; hier eines je Smoke-Contract.
        $pattern = @($SmokeFiles | ForEach-Object { "samples:gptscan/mwevariety_fixed/$_" })
    }

    $corpusDir = Join-Path $SmartBugsDir 'samples\gptscan\mwevariety_fixed'
    $nSol = (Get-ChildItem -Path $corpusDir -Recurse -Filter *.sol | Measure-Object).Count
    Write-Log "Korpus: $corpusDir ($nSol .sol-Dateien)"
    Write-Log ("Mode={0} RunId={1} MAIN={2} processes={3} timeout={4}s mem-limit={5}" -f `
               $Mode, $RunId, $Main, $Processes, $TimeoutSec, $MemLimit)
    if ($Mode -ne 'dry') { Write-Log "LIVE-Lauf: es werden kostenpflichtige API-Calls abgesetzt." }
    Write-Log "Hinweis: --timeout wirkt seit AP5 im Container (Bremse bei GPTScan, Netz als letzte Stufe); Docker bleibt zusaetzlich als aeusserer Abschuss bestehen."

    # ---------------------------------------------------------------- Lauf
    $started = Get-Date
    $exit = Invoke-SbRun -Pattern $pattern -RunIdent $RunId -UseMain $Main
    $ended = Get-Date
    Write-Log ("Lauf beendet, ExitCode={0}, Wanduhr {1:N1} min (Log: smartbugs\results\logs\$RunId.log)" -f `
               $exit, ($ended - $started).TotalMinutes)
    if ($exit -ne 0) { Write-Log "WARNUNG: ExitCode != 0 - Einzelfehler wurden gesammelt (--continue-on-errors), Details im Log." }

    # ------------------------------------------- Exit-127-Nachlauf (ohne --main)
    $resultDir = Join-Path $SmartBugsDir "results\gptscan\$RunId"
    $exit127 = @()
    if ($Main -and (Test-Path $resultDir)) {
        foreach ($sbj in Get-ChildItem -Path $resultDir -Recurse -Filter 'smartbugs.json') {
            $d = Get-Content -Raw $sbj.FullName | ConvertFrom-Json
            if ($d.result.exit_code -eq 127) { $exit127 += $sbj.Directory.Name }
        }
        if ($exit127.Count -gt 0) {
            Write-Log ("Exit 127 (Dateiname benennt keinen enthaltenen Contract): {0} -> {1}" -f `
                       $exit127.Count, ($exit127 -join ', '))
            if ($MainFallback) {
                $fbRunId = "${RunId}_nomain"
                Write-Log "Nachlauf dieser Contracts OHNE --main, runid=$fbRunId"
                $fbPattern = @($exit127 | ForEach-Object { "samples:gptscan/mwevariety_fixed/$_" })
                $fbExit = Invoke-SbRun -Pattern $fbPattern -RunIdent $fbRunId -UseMain $false
                Write-Log "Nachlauf beendet, ExitCode=$fbExit"
            }
            else {
                Write-Log "HINWEIS: -MainFallback nicht gesetzt - diese Contracts bleiben unanalysiert."
            }
        }
    }

    # ---------------------------------------------------------------- Protokoll
    $evalDir = Join-Path $EvalRoot $RunId
    New-Item -ItemType Directory -Force -Path $evalDir | Out-Null
    # sb.cfg.SB_VERSION (nicht VERSION). Aufruf ueber cmd, damit ein Fehlschlag
    # nicht als PS5.1-NativeCommandError den ganzen Lauf abbricht.
    Push-Location $SmartBugsDir
    $sbVersion = (cmd /c """$Python"" -c ""import sb.cfg;print(sb.cfg.SB_VERSION)"" 2>nul")
    Pop-Location
    if (-not $sbVersion) { $sbVersion = 'unbekannt' }
    $params = [ordered]@{
        run_id            = $RunId
        mode              = $Mode
        started_utc       = $started.ToUniversalTime().ToString('o')
        ended_utc         = $ended.ToUniversalTime().ToString('o')
        wallclock_seconds = [math]::Round(($ended - $started).TotalSeconds, 1)
        smartbugs_version = $sbVersion
        docker_image      = 'smartbugs/gptscan:1.0'
        docker_image_id   = "$imageId"
        provider          = $env:GPTSCAN_PROVIDER
        model             = $env:GPTSCAN_MODEL
        dry_run           = ($Mode -eq 'dry')
        main              = $Main
        processes         = $Processes
        timeout_sec       = $TimeoutSec
        timeout_enforced_by = 'in-container (AP5: GPTScan brake + net) plus docker as outer fallback'
        mem_limit         = $MemLimit
        file_pattern      = @($pattern)
        corpus_dir        = 'smartbugs/samples/gptscan/mwevariety_fixed'
        corpus_files      = $nSol
        sb_exit_code      = $exit
        exit_127          = @($exit127)
        main_fallback     = [bool]$MainFallback
        results_dir       = "smartbugs/results/gptscan/$RunId"
        tool_yaml_sha1    = (Get-FileHash (Join-Path $SmartBugsDir 'tools\gptscan\config.yaml') -Algorithm SHA1).Hash
        findings_yaml_sha1= (Get-FileHash (Join-Path $SmartBugsDir 'tools\gptscan\findings.yaml') -Algorithm SHA1).Hash
        parser_sha1       = (Get-FileHash (Join-Path $SmartBugsDir 'tools\gptscan\parser.py') -Algorithm SHA1).Hash
        entrypoint_sha1   = (Get-FileHash (Join-Path $SmartBugsDir 'tools\gptscan\scripts\do_solidity.sh') -Algorithm SHA1).Hash
        main_contract_sha1= (Get-FileHash (Join-Path $SmartBugsDir 'tools\gptscan\scripts\main_contract.py') -Algorithm SHA1).Hash
        git_commit        = (cmd /c "git -C ""$RepoRoot"" rev-parse HEAD 2>nul")
        script            = 'run_full_v2.ps1'
    }
    $paramFile = Join-Path $evalDir 'run_params.json'
    $params | ConvertTo-Json -Depth 5 | Out-File -FilePath $paramFile -Encoding utf8
    Write-Log "Laufparameter: $paramFile"

    # ---------------------------------------------------------------- Bilanz
    if (Test-Path $resultDir) {
        Write-Log "Kennzahlen des Laufs:"
        & $Python (Join-Path $RepoRoot 'analysis_tools\gptscan_run_stats.py') $resultDir | Out-Host
    }
    Write-Log "Auswertung erzeugen: python analysis_tools\gptscan_eval.py $RunId"
    Write-Log "Fertig."
}
finally {
    Remove-Item Env:GPTSCAN_DRY_RUN, Env:GPTSCAN_PROVIDER, Env:GPTSCAN_MODEL, `
                Env:GPTSCAN_BASE_URL, Env:GPTSCAN_API_KEY, `
                Env:DEEPSEEK_API_KEY, Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
}
