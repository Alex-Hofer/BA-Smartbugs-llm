<#
.SYNOPSIS
  Massentest der beiden KI-Scanner (GPTScan, LLMSmartAudit) ueber den
  smartbugs-curated-Datensatz (143 Solidity-Contracts) via SmartBugs.

.DESCRIPTION
  Validiert durch Smoke-Test am 2026-07-05 (runids smoke1_*/smoke2_live):
    - GPTScan:       deepseek/deepseek-v4-flash, $0.50-Kostenbremse pro Contract.
                     Gemessen: Median ~$0.0009/Contract, laengster Task 600 s.
    - LLMSmartAudit: Host-Env LLM_MODEL=deepseek-v4-flash ist PFLICHT (das Image
                     hat das abgeschaltete "deepseek-chat" eingebrannt -> HTTP 400).
                     Gemessen: ~366 s/Contract (max 559 s). KEINE Kostenbremse im Tool!
    - Keine Rate-Limits ueber ~580 Live-Calls bei processes=3 -> keine Delays noetig.

  Schaetzung fuer den Volllauf (143 Contracts, --processes 4, sequenziell):
    GPTScan:       ~15-38 min,  Kosten realistisch < $0.50 gesamt
    LLMSmartAudit: ~3.5-4.5 h,  Kosten typisch ~$1.5-3, Sicherheits-Ceiling ~$8-10
    Gesamt:        ~4-5 h

  Die beiden Tool-Laeufe laufen bewusst SEQUENZIELL (erst GPTScan, dann LLMSA),
  um API-Concurrency auf demselben Key und CPU-Druck zu begrenzen.

  Nach dem GPTScan-Lauf werden zwei Manifeste erzeugt:
    - curated_compile_failures_*.csv: Compile-Fehler/Timeouts. Diese Contracts
      zaehlen NICHT als 'clean' (GPTScans result.json ist dort still-unvollstaendig).
    - curated_review_candidates_*.csv: Contracts, bei denen die Static-Stufe
      LLM-Kandidaten verworfen hat. Das ist MEIST GPTScans normales False-
      Positive-Filtering (bestimmungsgemaess!) - Liste fuer manuelle Nachpruefung,
      KEIN automatischer Ausschluss fuer die Benchmark-Auswertung.

.PARAMETER Tool
  gptscan | llmsmartaudit | both (Default: both)
.PARAMETER Processes
  Parallele SmartBugs-Tasks (Default 4; nicht ohne Test erhoehen).
.PARAMETER FilePattern
  SmartBugs-Dateimuster "ROOT:GLOB" relativ zum smartbugs\-Verzeichnis.
  Default: ..\smartbugs-curated\dataset:**/*.sol
  ACHTUNG: genau EIN Doppelpunkt erlaubt (kein Laufwerksbuchstabe!).
.PARAMETER GptscanDry
  GPTScan im Dry-Run (0 API-Calls, $0); LLMSmartAudit wird uebersprungen
  (das Tool hat keinen Dry-Modus). Fuer Pipeline-Tests.
.PARAMETER SkipClone
  Datensatz-Clone ueberspringen (z.B. wenn -FilePattern auf samples\ zeigt).
.PARAMETER RunIdSuffix
  Suffix fuer Ergebnisordner results\<tool>\curated_<suffix>\ (Default: Zeitstempel).
  Gleicher Suffix + vorhandene Ergebnisse: bestehende Task-Ordner werden nicht
  ueberschrieben (kein --overwrite) - neuer Suffix = frischer Lauf.
.PARAMETER Provider
  LLM-Anbieter fuer BEIDE Werkzeuge: deepseek | openai | custom (Default: deepseek).
  Bestimmt zugleich, welcher Schluessel aus GPTScan\.env gebraucht wird:
  deepseek -> DEEPSEEK_API_KEY, openai -> OPENAI_API_KEY,
  custom -> GPTSCAN_API_KEY (GPTScan) bzw. OPENAI_API_KEY (LLMSmartAudit).
.PARAMETER Model
  Modell-ID fuer beide Werkzeuge (Default: deepseek-v4-flash). Der Wert geht
  unveraendert als --model an das jeweilige Werkzeug und von dort an die API.
  Fuer LLMSmartAudit ist eine explizite Angabe PFLICHT - das Image hat das
  abgeschaltete "deepseek-chat" eingebrannt.
.PARAMETER GptscanModel
  Abweichende Modell-ID nur fuer GPTScan (Default: Wert von -Model).
.PARAMETER LlmModel
  Abweichende Modell-ID nur fuer LLMSmartAudit (Default: Wert von -Model).
.PARAMETER BaseUrl
  OpenAI-kompatibler Endpunkt. Nur noetig (und nur wirksam) bei -Provider custom.
  Wird als GPTSCAN_BASE_URL bzw. LLM_BASE_URL gesetzt.
.PARAMETER ContextTokens
  Kontextfenster in Token fuer LLMSmartAudit (Default: 65536). Rueckfallwert fuer
  Modell-IDs, die camel/model_backend.py nicht kennt.
.PARAMETER MaxCompletionTokens
  Obergrenze fuer die Antwortlaenge je Aufruf (LLMSmartAudit). 0 = nicht setzen.

.EXAMPLE
  .\run_curated.ps1                                   # Volllauf beide Tools
.EXAMPLE
  .\run_curated.ps1 -Tool gptscan                     # nur GPTScan
.EXAMPLE
  .\run_curated.ps1 -Tool gptscan -GptscanDry -SkipClone -FilePattern 'samples:gptscan/Vault.sol'
                                                      # 1-Datei-Pipelinetest, $0
.EXAMPLE
  .\run_curated.ps1 -Model deepseek-v4-pro -RunIdSuffix v4pro
                                                      # anderes Modell, gleicher Anbieter
.EXAMPLE
  .\run_curated.ps1 -Provider openai -Model gpt-4o -RunIdSuffix openai
                                                      # anderer Anbieter (OPENAI_API_KEY noetig)
.EXAMPLE
  .\run_curated.ps1 -Tool gptscan -Provider custom -Model custom-cheap `
      -BaseUrl 'http://host.docker.internal:8000/v1' -SkipClone `
      -FilePattern 'samples:gptscan/Vault.sol' -RunIdSuffix pruefstand
                                                      # lokaler Pruefstand, $0

  Voraussetzungen: Docker Desktop laeuft; Images smartbugs/gptscan:1.0 und
  smartbugs/llmsmartaudit:1.0 lokal gebaut; der zum Anbieter passende Schluessel
  in GPTScan\.env.

  ACHTUNG fuer die Auswertung: Die aufgezeichneten Laeufe dieser Arbeit sind
  saemtlich mit deepseek/deepseek-v4-flash entstanden. Ein Lauf mit anderen
  Werten ist nicht mit ihnen vergleichbar - dafuer immer einen eigenen
  -RunIdSuffix vergeben.
#>
[CmdletBinding()]
param(
    [ValidateSet('gptscan', 'llmsmartaudit', 'both')]
    [string]$Tool = 'both',
    [int]$Processes = 4,
    [string]$FilePattern = '..\smartbugs-curated\dataset:**/*.sol',
    [switch]$GptscanDry,
    [switch]$SkipClone,
    [string]$RunIdSuffix = (Get-Date -Format 'yyyyMMdd_HHmm'),
    [ValidateSet('deepseek', 'openai', 'custom')]
    [string]$Provider = 'deepseek',
    [string]$Model = 'deepseek-v4-flash',
    [string]$GptscanModel = '',
    [string]$LlmModel = '',
    [string]$BaseUrl = '',
    [int]$ContextTokens = 65536,
    [int]$MaxCompletionTokens = 0
)

# Werkzeugspezifische Modelle fallen auf -Model zurueck.
if (-not $GptscanModel) { $GptscanModel = $Model }
if (-not $LlmModel)     { $LlmModel     = $Model }

$ErrorActionPreference = 'Stop'
$RepoRoot     = $PSScriptRoot
$SmartBugsDir = Join-Path $RepoRoot 'smartbugs'
$Python       = Join-Path $SmartBugsDir '.venv\Scripts\python.exe'
$DatasetDir   = Join-Path $RepoRoot 'smartbugs-curated'
$EnvFile      = Join-Path $RepoRoot 'GPTScan\.env'

function Write-Log([string]$Msg) {
    Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $Msg)
}

function Invoke-SbRun {
    param([string]$SbTool, [int]$TimeoutSec, [string]$ResultsTemplate, [string]$RunId)
    Push-Location $SmartBugsDir
    try {
        # stdout direkt zur Konsole durchreichen, damit NUR der ExitCode zurueckkommt
        & $Python -m sb -t $SbTool -f $FilePattern `
            --json --sarif `
            --timeout $TimeoutSec `
            --processes $Processes `
            --continue-on-errors `
            --results $ResultsTemplate `
            --runid $RunId | Out-Host
        return $LASTEXITCODE
    }
    finally { Pop-Location }
}

try {
    # ---------------------------------------------------------------- Prechecks
    Write-Log "Prechecks..."
    if (-not (Test-Path $Python)) { throw "SmartBugs-venv fehlt: $Python" }

    # cmd uebernimmt die Umleitung: vermeidet PS5.1-NativeCommandError bei stderr-WARNINGs
    cmd /c "docker info >nul 2>&1"
    if ($LASTEXITCODE -ne 0) { throw "Docker-Daemon nicht erreichbar - Docker Desktop starten." }

    $needGpt  = ($Tool -eq 'gptscan')       -or ($Tool -eq 'both')
    $needLlm  = (($Tool -eq 'llmsmartaudit') -or ($Tool -eq 'both')) -and (-not $GptscanDry)
    if ($GptscanDry -and $Tool -ne 'gptscan') {
        Write-Log "HINWEIS: -GptscanDry gesetzt -> LLMSmartAudit wird uebersprungen (kein Dry-Modus vorhanden)."
    }

    if ($needGpt) {
        if (-not (docker images -q smartbugs/gptscan:1.0)) {
            throw "Image smartbugs/gptscan:1.0 fehlt. Bauen: docker build -t smartbugs/gptscan:1.0 .\GPTScan"
        }
    }
    if ($needLlm) {
        if (-not (docker images -q smartbugs/llmsmartaudit:1.0)) {
            throw ("Image smartbugs/llmsmartaudit:1.0 fehlt. Bauen (Git Bash!): " +
                   "git archive HEAD:LLMSmartAuditTool-main/LLMSmartAuditTool-main | " +
                   "docker build -f Dockerfile.smartbugs -t smartbugs/llmsmartaudit:1.0 -")
        }
    }

    # ---------------------------------------------------------------- API-Key
    # Alle Zuweisungen aus GPTScan\.env in die Prozessumgebung uebernehmen. Frueher
    # las das Skript nur DEEPSEEK_API_KEY heraus; damit war kein anderer Anbieter
    # bedienbar. Welcher Schluessel gebraucht wird, haengt am Anbieter.
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

    # Pflichtschluessel je Anbieter - siehe GPTScan/src/config.py:PROVIDERS und
    # LLMSmartAuditTool run.py.
    $requiredKeys = @()
    switch ($Provider) {
        'deepseek' { $requiredKeys = @('DEEPSEEK_API_KEY') }
        'openai'   { $requiredKeys = @('OPENAI_API_KEY') }
        'custom'   {
            if ($needGpt) { $requiredKeys += 'GPTSCAN_API_KEY' }
            if ($needLlm) { $requiredKeys += 'OPENAI_API_KEY' }
            if (-not $BaseUrl) {
                throw "-Provider custom verlangt -BaseUrl (OpenAI-kompatibler Endpunkt)."
            }
        }
    }
    if (-not $GptscanDry) {
        foreach ($k in $requiredKeys) {
            if (-not (Get-Item -Path "Env:$k" -ErrorAction SilentlyContinue)) {
                throw "$k fehlt in $EnvFile - wird fuer -Provider $Provider gebraucht."
            }
        }
    }
    Write-Log "Backend: provider=$Provider, GPTScan-Modell=$GptscanModel, LLMSA-Modell=$LlmModel$(if ($BaseUrl) { ", base_url=$BaseUrl" })"

    # ---------------------------------------------------------------- Datensatz
    if (-not $SkipClone) {
        if (-not (Test-Path (Join-Path $DatasetDir 'dataset'))) {
            Write-Log "Klone smartbugs-curated nach $DatasetDir ..."
            cmd /c "git clone --depth 1 --quiet https://github.com/smartbugs/smartbugs-curated ""$DatasetDir"" 2>&1"
            if ($LASTEXITCODE -ne 0) { throw "git clone von smartbugs-curated fehlgeschlagen." }
        }
        $solCount = (Get-ChildItem -Path (Join-Path $DatasetDir 'dataset') -Recurse -Filter *.sol | Measure-Object).Count
        Write-Log "Datensatz bereit: $solCount .sol-Dateien unter smartbugs-curated\dataset\"
    }
    else {
        Write-Log "Clone uebersprungen (-SkipClone). FilePattern: $FilePattern"
    }

    # Template-Literale in EINFACHEN Anfuehrungszeichen halten, damit PowerShell
    # ${TOOL}/${RELDIR}/${FILENAME} nicht selbst expandiert (SmartBugs expandiert sie).
    $gptResults = 'results/${TOOL}/curated_' + $RunIdSuffix + '/${RELDIR}/${FILENAME}'
    $llmResults = $gptResults
    $gptRunId   = "curated_gptscan_$RunIdSuffix"
    $llmRunId   = "curated_llmsa_$RunIdSuffix"
    $gptExit    = $null
    $llmExit    = $null

    # ---------------------------------------------------------------- Run 1: GPTScan
    if ($needGpt) {
        $env:GPTSCAN_PROVIDER = $Provider
        $env:GPTSCAN_MODEL    = $GptscanModel
        # GPTSCAN_BASE_URL wertet GPTScan nur bei provider=custom aus
        # (src/llm_backend.py:base_url) - ein bezahltes Backend laesst sich damit
        # nicht umleiten. Ausserhalb von custom bleibt die Variable ungesetzt.
        if ($Provider -eq 'custom' -and $BaseUrl) { $env:GPTSCAN_BASE_URL = $BaseUrl }
        else { Remove-Item Env:GPTSCAN_BASE_URL -ErrorAction SilentlyContinue }
        if ($GptscanDry) { $env:GPTSCAN_DRY_RUN = '1'; Write-Log "GPTScan: DRY-RUN (0 API-Calls)" }
        else { Remove-Item Env:GPTSCAN_DRY_RUN -ErrorAction SilentlyContinue }

        Write-Log "Starte GPTScan (processes=$Processes, timeout=1800s, runid=$gptRunId)..."
        $gptExit = Invoke-SbRun -SbTool 'gptscan' -TimeoutSec 1800 -ResultsTemplate $gptResults -RunId $gptRunId
        Write-Log "GPTScan beendet, ExitCode=$gptExit (Log: smartbugs\results\logs\$gptRunId.log)"
        if ($gptExit -ne 0) { Write-Log "WARNUNG: GPTScan-ExitCode != 0 - Details im Log; es geht weiter." }
    }

    # ---------------------------------------------------------------- Run 2: LLMSmartAudit
    if ($needLlm) {
        $env:LLM_PROVIDER       = $Provider
        $env:LLM_MODEL          = $LlmModel             # PFLICHT: ueberschreibt totes deepseek-chat im Image
        $env:LLM_CONTEXT_TOKENS = "$ContextTokens"      # Versicherung gegen context_length_exceeded
        if ($BaseUrl) { $env:LLM_BASE_URL = $BaseUrl }
        else { Remove-Item Env:LLM_BASE_URL -ErrorAction SilentlyContinue }
        if ($MaxCompletionTokens -gt 0) { $env:LLM_MAX_COMPLETION_TOKENS = "$MaxCompletionTokens" }
        else { Remove-Item Env:LLM_MAX_COMPLETION_TOKENS -ErrorAction SilentlyContinue }
        Write-Log "Starte LLMSmartAudit (processes=$Processes, timeout=5400s, runid=$llmRunId)..."
        Write-Log "ACHTUNG: keine Kostenbremse im Tool - erwartete Dauer ~3.5-4.5 h fuer 143 Contracts."
        $llmExit = Invoke-SbRun -SbTool 'llmsmartaudit' -TimeoutSec 5400 -ResultsTemplate $llmResults -RunId $llmRunId
        Write-Log "LLMSmartAudit beendet, ExitCode=$llmExit (Log: smartbugs\results\logs\$llmRunId.log)"
    }

    # ------------------------------------------- Compile-Failure-/Degradations-Manifest
    $gptResultDir = Join-Path $SmartBugsDir "results\gptscan\curated_$RunIdSuffix"
    if ($needGpt -and (Test-Path $gptResultDir)) {
        Write-Log "Scanne GPTScan-Logs auf Compile-Fehler/Degradation..."
        $compileFails = New-Object System.Collections.Generic.List[object]
        $reviewCands  = New-Object System.Collections.Generic.List[object]
        $totalCost    = 0.0
        $taskLogs     = Get-ChildItem -Path $gptResultDir -Recurse -Filter 'result.log'

        foreach ($lf in $taskLogs) {
            $contract = $lf.Directory.FullName.Substring($gptResultDir.Length).TrimStart('\')
            $raw = Get-Content -Raw $lf.FullName

            if ($raw -match 'Compile failed|InvalidCompilation') {
                $ind = if ($raw -match 'InvalidCompilation') { 'InvalidCompilation' } else { 'Compile failed' }
                $compileFails.Add([pscustomobject]@{ contract = $contract; indicator = $ind })
            }

            $metaLine = ($raw -split "`r?`n" | Where-Object { $_ -match '^GPTSCAN_META\s+\{' } | Select-Object -Last 1)
            if ($metaLine) {
                try {
                    $meta = ($metaLine -replace '^GPTSCAN_META\s+', '') | ConvertFrom-Json
                    if ($null -ne $meta.estimated_cost) { $totalCost += [double]$meta.estimated_cost }
                    $staticSkipped  = ($meta.functions_after_step_2 -gt 0 -and $meta.functions_after_static -eq 0)
                    $candidateDrop  = ($meta.vul_before_static -gt $meta.vul_after_static)
                    # Im Dry-Run laeuft die Static-Bestaetigung nie -> Signatur dort bedeutungslos
                    if ((-not $meta.dry_run) -and ($staticSkipped -or $candidateDrop)) {
                        $reason = 'candidate_dropped_by_static'
                        if ($staticSkipped) { $reason = 'static_stage_skipped' }
                        $reviewCands.Add([pscustomobject]@{
                            contract              = $contract
                            reason                = $reason
                            functions_after_step2 = $meta.functions_after_step_2
                            functions_after_static= $meta.functions_after_static
                            vul_before_static     = $meta.vul_before_static
                            vul_after_static      = $meta.vul_after_static
                        })
                    }
                }
                catch { Write-Log "WARNUNG: GPTSCAN_META unlesbar in $($lf.FullName)" }
            }
            elseif ($raw -notmatch 'Compile failed|InvalidCompilation') {
                # result.log ohne META und ohne Compile-Fehler: Task-Timeout/Abbruch
                $compileFails.Add([pscustomobject]@{ contract = $contract; indicator = 'GPTSCAN_META fehlt (Timeout/Abbruch?)' })
            }
        }

        $resultsRoot = Join-Path $SmartBugsDir 'results'
        $cfCsv  = Join-Path $resultsRoot "curated_compile_failures_$RunIdSuffix.csv"
        $rcCsv  = Join-Path $resultsRoot "curated_review_candidates_$RunIdSuffix.csv"
        $compileFails | Export-Csv -Path $cfCsv -NoTypeInformation -Encoding UTF8
        $reviewCands  | Export-Csv -Path $rcCsv -NoTypeInformation -Encoding UTF8

        Write-Log ("GPTScan-Bilanz: {0} Tasks | {1} Compile-Failures/Timeouts ({2}) | {3} Review-Kandidaten ({4}) | Kosten gesamt ~`${5:N4}" -f `
            $taskLogs.Count, $compileFails.Count, (Split-Path -Leaf $cfCsv), $reviewCands.Count, (Split-Path -Leaf $rcCsv), $totalCost)
        Write-Log "Auswertung: Compile-Failures/Timeouts zaehlen NICHT als 'clean' (result.json dort still-unvollstaendig)."
        Write-Log "Review-Kandidaten sind KEIN Automatik-Ausschluss: Kandidaten-Verwurf durch die Static-Stufe ist meist GPTScans normales False-Positive-Filtering - nur manuell nachpruefen."
    }

    # ---------------------------------------------------------------- Zusammenfassung
    $runDirs = @()
    foreach ($t in @('gptscan', 'llmsmartaudit')) {
        $dir = Join-Path $SmartBugsDir "results\$t\curated_$RunIdSuffix"
        if (Test-Path $dir) {
            $runDirs += $dir
            $n = (Get-ChildItem -Path $dir -Recurse -Filter 'result.json' | Measure-Object).Count
            Write-Log ("{0}: {1} result.json unter {2}" -f $t, $n, $dir)
        }
    }

    # Errors/Fails getrennt ausweisen. SmartBugs unterscheidet:
    #   error - das Werkzeug hat das Problem bemerkt, behandelt, weitergearbeitet
    #   fail  - eine Exception ist entkommen oder der Lauf wurde abgebrochen
    # Hergeleitet aus sb/parse_utils.py::errors_fails, siehe
    # docs\BA-ERRORS-VS-FAILS.md. Die Auswertung liegt bewusst im Python-Skript
    # und wird hier nur aufgerufen - eine zweite Implementierung in PowerShell
    # koennte von der ersten abweichen.
    if ($runDirs.Count -gt 0) {
        $reportScript = Join-Path $RepoRoot 'analysis_tools\errors_fails_report.py'
        if (Test-Path $reportScript) {
            Write-Log "Errors/Fails-Bilanz:"
            & $Python $reportScript @runDirs `
                --md (Join-Path $RepoRoot "docs\errors-fails-$RunIdSuffix.md") `
                --csv (Join-Path $RepoRoot "docs\errors-fails-$RunIdSuffix.csv") | Out-Host
            Write-Log "Spalte 'nicht uebersetzt': dort ist ein leeres Finding-Ergebnis unbestimmt, NICHT sauber."
        }
        else {
            Write-Log "HINWEIS: $reportScript fehlt - Errors/Fails-Bilanz uebersprungen."
        }
    }

    Write-Log "CSV-Auswertung: cd smartbugs; .venv\Scripts\python.exe -m sb.results2csv results\gptscan\curated_$RunIdSuffix results\llmsmartaudit\curated_$RunIdSuffix > ..\curated_results.csv"
    Write-Log "Parser-Vollstaendigkeit pruefen: python analysis_tools\parser_audit.py smartbugs\results\gptscan\curated_$RunIdSuffix"
    Write-Log "Fertig."
}
finally {
    # Alles wieder aus der Prozessumgebung nehmen, was dieses Skript gesetzt hat -
    # einschliesslich der Schluessel, die aus GPTScan\.env kamen.
    Remove-Item Env:GPTSCAN_DRY_RUN, Env:GPTSCAN_PROVIDER, Env:GPTSCAN_MODEL, `
                Env:GPTSCAN_BASE_URL, Env:GPTSCAN_API_KEY, `
                Env:LLM_PROVIDER, Env:LLM_MODEL, Env:LLM_CONTEXT_TOKENS, `
                Env:LLM_BASE_URL, Env:LLM_MAX_COMPLETION_TOKENS, `
                Env:DEEPSEEK_API_KEY, Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
}
