<#
.SYNOPSIS
  Volllauf LLMSmartAudit ueber beide Korpora: smartbugs-curated (143) und
  mwevariety_fixed (96). Ausschliesslich ueber SmartBugs.

.DESCRIPTION
  Eigene Datei, NICHT run_curated.ps1 (bleibt unangetastet) und nicht
  run_full_v2.ps1 -- letztere entsteht parallel fuer den GPTScan-Lauf und kann
  dieses Skript spaeter einziehen. Der Altlauf curated_v1_20260705 wird nicht
  beruehrt.

  INTERPRETER: Die aufgezeichneten Laeufe liefen auf einem Rechner mit
  smartbugs\venv; der Pfad ist seit 24.09.2026 an README und die uebrigen
  Runner angeglichen (smartbugs\.venv).

  KEIN --main. Begruendung, gemessen am 2026-08-15:
  SmartBugs setzt --main selbst beim Einsammeln der Tasks durch
  (sb/smartbugs.py:124, exakter Vergleich Dateiname == Contractname) und bricht
  den Lauf ab, wenn es nicht passt. Bestanden haben diese Pruefung 4 von 143
  curated- und 0 von 96 mwevariety-Dateien. Die AP6-Umsetzung in den beiden
  Entrypoints wird dadurch nie erreicht. Entscheidung des Betreuers: AP6 fuer
  diesen Lauf fallenlassen, beide Korpora wie den Altlauf fahren. Der
  AP6-Code bleibt liegen und ist bei MAIN=0 wirkungslos.

  KONTEXTGRENZE, gemessen im Smoke-Test:
  Ein Contract mit 1.447 Zeilen laeuft durch (44 Calls), einer mit 2.470 Zeilen
  bricht nach dem ersten Call ab. Ursache ist nicht der Quelltext allein,
  sondern die ueber die Runden wachsende Multi-Agenten-Konversation gegen die
  in camel/utils.py fuer ModelType.DEEPSEEK_CHAT fest verdrahtete Grenze von
  65.536 Tokens, die LLM_CONTEXT_TOKENS damals nicht anhob. Betroffen sind 26
  bis 52 der 96 mwevariety-Contracts (im Lauf dann 37). Sie liefern kein
  Ergebnis und erscheinen als eigener Zustand "context window exceeded" im
  Parser -- ausdruecklich NICHT als "keine Findings". Seit 24.09.2026 liest
  camel/utils.py die Grenze aus LLM_CONTEXT_TOKENS (Default 65.536); ein
  danach gebautes Image nimmt -ContextTokens also auch fuer die Agentengrenze.

  TIMEOUT: Dieser Lauf (15./16.08.2026) entstand vor AP5; damals griff nur
  der Docker-Abschuss. Seit 18.08.2026 wirkt --timeout auch im Container
  (docs/BA-AP5-ABSCHLUSSBERICHT.md).

  KOSTENBREMSE: das Werkzeug hat keine. chatdev/statistics.py::prompt_cost
  kennt deepseek-v4-flash nicht und meldet durchgehend $0,0000, die
  toolseitige Kostenangabe ist also unbrauchbar. Dieses Skript rechnet die
  Kosten selbst aus den Tokenzahlen in den result.log und haelt den Lauf an,
  wenn die laufende Summe CostCeiling ueberschreitet.

.PARAMETER Corpus
  'both' (Default), 'curated' oder 'mwefixed'.

.PARAMETER Processes
  Parallele SmartBugs-Prozesse. Default 3 -- im Altlauf ueber ~580 Live-Calls
  rate-limit-frei belegt.

.PARAMETER CostCeiling
  Harte Abbruchschwelle in USD auf die laufende Summe. Default 21.00, also
  50 % ueber der aus dem Smoke-Test hochgerechneten Erwartung von ~$14.

.PARAMETER RunSuffix
  Suffix der runids. Default 'v2'.
#>
[CmdletBinding()]
param(
    [ValidateSet('both', 'curated', 'mwefixed')][string]$Corpus = 'both',
    [int]$Processes = 3,
    [double]$CostCeiling = 21.00,
    [string]$RunSuffix = 'v2',
    # Backend zur Laufzeit waehlbar. Die Defaults entsprechen den aufgezeichneten
    # Laeufen; ein abweichender Lauf gehoert unter einen eigenen -RunSuffix.
    #   deepseek -> DEEPSEEK_API_KEY, openai/custom -> OPENAI_API_KEY
    #   custom   -> zusaetzlich -BaseUrl und eine explizite -Model-Angabe
    [ValidateSet('deepseek', 'openai', 'custom')]
    [string]$Provider = 'deepseek',
    [string]$Model = 'deepseek-v4-flash',
    [string]$BaseUrl = '',
    [int]$ContextTokens = 65536,
    [int]$MaxCompletionTokens = 0
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SbDir    = Join-Path $RepoRoot 'smartbugs'
$Py       = Join-Path $SbDir '.venv\Scripts\python.exe'
$LogDir   = Join-Path $RepoRoot 'eval\_runlogs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp    = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile  = Join-Path $LogDir "llmsa_full_$Stamp.log"

function Write-Log {
    param([string]$Message)
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

# --- Preise -----------------------------------------------------------------
# deepseek-v4-flash steht in keiner Preistabelle des Werkzeugs. Diese Saetze
# sind aus dem Altlauf curated_v1_20260705 zurueckgerechnet ($2,44 bei
# 12,55 Mio Prompt- und 3,52 Mio Completion-Tokens), unter Uebernahme des
# Input/Output-Verhaeltnisses 1:4,07 der veroeffentlichten deepseek-chat-Preise.
# Naeherung fuer die Bremse -- die verbindliche Zahl kommt aus der
# DeepSeek-Abrechnung und gehoert so in run_meta.json.
$PricePromptPerM     = 0.0908
$PriceCompletionPerM = 0.3695

function Get-RunCost {
    param([string[]]$RunIds)
    $prompt = 0L; $completion = 0L; $tasks = 0
    foreach ($id in $RunIds) {
        $dir = Join-Path $SbDir "results\llmsmartaudit\$id"
        if (-not (Test-Path $dir)) { continue }
        foreach ($log in Get-ChildItem -Path $dir -Filter 'result.log' -Recurse -ErrorAction SilentlyContinue) {
            $tasks++
            foreach ($m in [regex]::Matches((Get-Content $log.FullName -Raw), 'prompt_tokens: (\d+)\s*\ncompletion_tokens: (\d+)')) {
                $prompt     += [long]$m.Groups[1].Value
                $completion += [long]$m.Groups[2].Value
            }
        }
    }
    $cost = ($prompt / 1e6) * $PricePromptPerM + ($completion / 1e6) * $PriceCompletionPerM
    [PSCustomObject]@{ Tasks = $tasks; Prompt = $prompt; Completion = $completion; Cost = $cost }
}

# --- Umgebung ---------------------------------------------------------------
if (-not (Test-Path $Py)) { throw "SmartBugs-venv fehlt: $Py. Erst 'python -m venv smartbugs\venv' und Abhaengigkeiten installieren." }

$EnvFile = Join-Path $RepoRoot 'GPTScan\.env'
if (-not (Test-Path $EnvFile)) { throw "GPTScan\.env fehlt -- ohne DEEPSEEK_API_KEY laeuft nichts. Key niemals hier hartkodieren." }
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $name = $Matches[1]; $value = $Matches[2].Trim().Trim('"').Trim("'")
        if ($value) { Set-Item -Path "Env:$name" -Value $value }
    }
}
# ------------------------------------ Rangfolge: Parameter > .env > Standard
# Ohne diese Aufloesung ueberschrieb der Runner jeden .env-Eintrag mit seinem
# eigenen Standardwert - ein dort eingetragenes Modell blieb wirkungslos.
$fromEnv = New-Object System.Collections.Generic.List[string]
if (-not $PSBoundParameters.ContainsKey('Provider') -and $env:LLM_PROVIDER) {
    $Provider = $env:LLM_PROVIDER; $fromEnv.Add("Provider=$Provider")
}
if (-not $PSBoundParameters.ContainsKey('Model') -and $env:LLM_MODEL) {
    $Model = $env:LLM_MODEL; $fromEnv.Add("Model=$Model")
}
if (-not $PSBoundParameters.ContainsKey('BaseUrl') -and $env:LLM_BASE_URL) {
    $BaseUrl = $env:LLM_BASE_URL; $fromEnv.Add("BaseUrl=$BaseUrl")
}
if (-not $PSBoundParameters.ContainsKey('ContextTokens') -and $env:LLM_CONTEXT_TOKENS) {
    $ContextTokens = [int]$env:LLM_CONTEXT_TOKENS; $fromEnv.Add("ContextTokens=$ContextTokens")
}
if (-not $PSBoundParameters.ContainsKey('MaxCompletionTokens') -and $env:LLM_MAX_COMPLETION_TOKENS) {
    $MaxCompletionTokens = [int]$env:LLM_MAX_COMPLETION_TOKENS
    $fromEnv.Add("MaxCompletionTokens=$MaxCompletionTokens")
}

$keyVar = switch ($Provider) {
    'deepseek' { 'DEEPSEEK_API_KEY' }
    default    { 'OPENAI_API_KEY' }   # openai und custom lesen beide OPENAI_API_KEY
}
if (-not (Get-Item -Path "Env:$keyVar" -ErrorAction SilentlyContinue)) {
    throw "$keyVar fehlt in $EnvFile - wird fuer -Provider $Provider gebraucht."
}
if ($Provider -eq 'custom' -and -not $BaseUrl) {
    throw "-Provider custom verlangt -BaseUrl (OpenAI-kompatibler Endpunkt)."
}

$env:LLM_PROVIDER       = $Provider
$env:LLM_MODEL          = $Model            # PFLICHT: ueberschreibt das tote deepseek-chat im Image
$env:LLM_CONTEXT_TOKENS = "$ContextTokens"  # Agent-Grenze nur mit Image ab 24.09.2026, siehe Kopfkommentar
if ($BaseUrl) { $env:LLM_BASE_URL = $BaseUrl }
else { Remove-Item Env:LLM_BASE_URL -ErrorAction SilentlyContinue }
if ($MaxCompletionTokens -gt 0) { $env:LLM_MAX_COMPLETION_TOKENS = "$MaxCompletionTokens" }
else { Remove-Item Env:LLM_MAX_COMPLETION_TOKENS -ErrorAction SilentlyContinue }

# Schluessel, die dieser Lauf nicht braucht, wieder aus der Prozessumgebung
# nehmen; die Allowlist (env: in config.yaml) reicht sonst jeden gesetzten
# Schluessel in den Container.
$dropKeys = if ($Provider -eq 'deepseek') { @('OPENAI_API_KEY', 'GPTSCAN_API_KEY') }
            else { @('DEEPSEEK_API_KEY', 'GPTSCAN_API_KEY') }
$dropped = @($dropKeys | Where-Object { Test-Path "Env:$_" })
foreach ($k in $dropped) { Remove-Item "Env:$k" }

Write-Log "Volllauf LLMSmartAudit, Korpus=$Corpus, Processes=$Processes, Kostendeckel=`$$CostCeiling"
if ($dropped.Count) {
    Write-Log ("Nicht benoetigte Schluessel aus der Umgebung entfernt: " + ($dropped -join ', '))
}
if ($fromEnv.Count) {
    Write-Log ("Aus $EnvFile uebernommen: " + ($fromEnv -join ', ') +
               " (ein ausdruecklicher Parameter haette Vorrang).")
}
Write-Log "Backend: provider=$($env:LLM_PROVIDER) model=$($env:LLM_MODEL) context=$($env:LLM_CONTEXT_TOKENS)$(if ($BaseUrl) { " base_url=$BaseUrl" })"
# Image-ID festhalten: der Tag bleibt bei einem Neubau gleich, die ID nicht.
$imageId = @(cmd /c 'docker image inspect --format "{{.Id}}" smartbugs/llmsmartaudit:1.0 2>nul') | Select-Object -First 1
Write-Log "Image: smartbugs/llmsmartaudit:1.0 $imageId"
Write-Log "API-Key gesetzt: ja, $keyVar ($((Get-Item -Path ""Env:$keyVar"").Value.Length) Zeichen, Wert wird nicht protokolliert)"
Write-Log "MAIN: nicht gesetzt (siehe Kopfkommentar)"

# --- Laeufe -----------------------------------------------------------------
$runs = @()
if ($Corpus -in @('both', 'curated')) {
    $runs += [PSCustomObject]@{
        RunId   = "llmsa_curated_$RunSuffix"
        Pattern = @('../smartbugs-curated/dataset:**/*.sol')
        Timeout = 3600
        Label   = 'curated (143)'
    }
}
if ($Corpus -in @('both', 'mwefixed')) {
    $runs += [PSCustomObject]@{
        RunId   = "llmsa_mwefixed_$RunSuffix"
        Pattern = @('samples/gptscan/mwevariety_fixed:*.sol')
        Timeout = 7200   # groessere Dateien, mehr Runden je Detektor
        Label   = 'mwevariety_fixed (96)'
    }
}
$allRunIds = $runs.RunId

Push-Location $SbDir
try {
    foreach ($run in $runs) {
        Write-Log "=== Start $($run.Label), runid=$($run.RunId), timeout=$($run.Timeout)s"
        # Kein --results: der Default ist das Muster
        # results/${TOOL}/${RUNID}/${FILENAME}. Ein blosses '--results results'
        # ersetzt das MUSTER durch den festen Namen 'results', wodurch jeder
        # Task auf dasselbe Verzeichnis zeigt und SmartBugs 142 Kollisionen zu
        # results_1, results_2, ... aufloest. Am 2026-08-15 einmal passiert und
        # nach fuenf Minuten abgebrochen.
        $args = @('-m', 'sb', '-t', 'llmsmartaudit', '-f') + $run.Pattern +
                @('--timeout', $run.Timeout, '--processes', $Processes,
                  '--runid', $run.RunId)
        $proc = Start-Process -FilePath $Py -ArgumentList $args -NoNewWindow -PassThru

        # Kostenwaechter: prueft die laufende Summe, solange der Lauf laeuft.
        while (-not $proc.HasExited) {
            Start-Sleep -Seconds 300
            $c = Get-RunCost -RunIds $allRunIds
            Write-Log ("Zwischenstand: {0} Tasks fertig, {1:N0} Prompt-, {2:N0} Completion-Tokens, ~`${3:N2}" -f $c.Tasks, $c.Prompt, $c.Completion, $c.Cost)
            if ($c.Cost -gt $CostCeiling) {
                Write-Log "ABBRUCH: laufende Summe ~`$$([math]::Round($c.Cost,2)) ueber dem Deckel `$$CostCeiling. Lauf wird angehalten."
                try { $proc.Kill() } catch {}
                throw "Kostendeckel ueberschritten -- Ruecksprache noetig, bevor weitergefahren wird."
            }
        }
        Write-Log "=== Ende $($run.Label), ExitCode=$($proc.ExitCode)"
    }

    # Rohausgabe in result.json ueberfuehren, damit Schritt 4 darauf aufsetzen kann.
    foreach ($id in $allRunIds) {
        $dir = "results\llmsmartaudit\$id"
        if (Test-Path $dir) {
            Write-Log "Reparse $dir"
            & $Py -m sb.reparse $dir --processes $Processes
        }
    }
}
finally {
    Pop-Location
}

$final = Get-RunCost -RunIds $allRunIds
Write-Log ("FERTIG: {0} Tasks, {1:N0} Prompt-, {2:N0} Completion-Tokens, geschaetzt ~`${3:N2}" -f $final.Tasks, $final.Prompt, $final.Completion, $final.Cost)
Write-Log "Protokoll: $LogFile"
