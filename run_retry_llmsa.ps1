<#
.SYNOPSIS
  Nachlauf LLMSmartAudit fuer die Tasks, die im Hauptlauf llmsa_mwefixed_v2
  ohne Ergebnis blieben, WEIL DAS GUTHABEN AUSGING -- nicht, weil das Werkzeug
  oder der Contract ein Problem hatte.

.DESCRIPTION
  Befund vom 2026-09-15, abgelesen an den result.log der vier Tasks:

      openai.APIStatusError: Error code: 402 -
      {'error': {'message': 'Insufficient Balance', ...}}

  Alle vier brachen mit demselben HTTP 402 ab, drei davon rund 31 Sekunden nach
  dem Start, 43_DelegatedStaking nach 1.221 Sekunden produktiver Arbeit. Das
  DeepSeek-Konto lief gegen Ende des Hauptlaufs (16.08.2026, 13:10-13:12 Uhr)
  auf null. Der Parser fuehrt sie als "kein Report"; das ist die richtige
  Einordnung, aber die Ursache liegt ausserhalb des Werkzeugs und ausserhalb
  des Contracts.

  ABGRENZUNG zu den 38 Tasks mit "Kontext ueberschritten": die sind NICHT
  Gegenstand dieses Skripts. Deren Abbruch (max_tokens_exceeded_by_camel,
  num_tokens > 65.536) ist das echte Kontextfenster von deepseek-chat, das in
  camel/utils.py:134 und camel/model_backend.py:139 steht, weil die DeepSeek-API
  nicht mehr annimmt. Ein Wiederholungslauf ohne Aenderung am Verfahren wuerde
  dort dasselbe Ergebnis und echte Kosten erzeugen.

  AUSSICHT: alle vier Contracts liegen mit 445 bis 1.355 Zeilen unterhalb der
  im Smoke-Test gemessenen Grenze von rund 1.447 Zeilen, ab der die wachsende
  Multi-Agenten-Konversation das Fenster sprengt. Ein Durchlauf ist also
  plausibel, aber nicht garantiert.

  EIGENER RUNID. Der Hauptlauf llmsa_mwefixed_v2 wird nicht angefasst, weder
  ueberschrieben noch geloescht -- eval/README.md haelt das so fest. Die
  Zusammenfuehrung uebernimmt analysis_tools/build_eval.py --merge-run, analog
  zum GPTScan-Nachlauf gptscan_mwefixed_v2_main_nomain.

  NEU gegenueber run_full_v2_llmsa.ps1: Guthabenpruefung vor dem Start. Genau
  diese Pruefung haette den Datenverlust im Hauptlauf sichtbar gemacht, bevor
  vier Tasks ins Leere liefen.

.PARAMETER Files
  Zu wiederholende Contracts ohne .sol. Default sind die vier 402-Faelle.

.PARAMETER Processes
  Parallele SmartBugs-Prozesse. Default 3, wie im Hauptlauf rate-limit-frei belegt.

.PARAMETER CostCeiling
  Harte Abbruchschwelle in USD auf die laufende Summe dieses Nachlaufs.

.PARAMETER RunId
  Ziel-runid. Default 'llmsa_mwefixed_v2_retry'.
#>
[CmdletBinding()]
param(
    [string[]]$Files = @('12_Witch', '25_CompositeMultiOracle', '43_DelegatedStaking', '62_Locke'),
    [int]$Processes = 3,
    [double]$CostCeiling = 3.00,
    [string]$RunId = 'llmsa_mwefixed_v2_retry'
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SbDir    = Join-Path $RepoRoot 'smartbugs'
$Py       = Join-Path $SbDir 'venv\Scripts\python.exe'
$LogDir   = Join-Path $RepoRoot 'eval\_runlogs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp    = Get-Date -Format 'yyyyMMdd-HHmmss'
$LogFile  = Join-Path $LogDir "llmsa_retry_$Stamp.log"

function Write-Log {
    param([string]$Message)
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

# Preise wie in run_full_v2_llmsa.ps1 und analysis_tools/build_eval.py.
# Naeherung fuer die Bremse; verbindlich ist die DeepSeek-Abrechnung.
$PricePromptPerM     = 0.0908
$PriceCompletionPerM = 0.3695

function Get-RunCost {
    param([string]$Id)
    $prompt = 0L; $completion = 0L; $tasks = 0
    $dir = Join-Path $SbDir "results\llmsmartaudit\$Id"
    if (Test-Path $dir) {
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
if (-not (Test-Path $Py)) { throw "SmartBugs-venv fehlt: $Py." }

$EnvFile = Join-Path $RepoRoot 'GPTScan\.env'
if (-not (Test-Path $EnvFile)) { throw "GPTScan\.env fehlt -- ohne DEEPSEEK_API_KEY laeuft nichts. Key niemals hier hartkodieren." }
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        $name = $Matches[1]
        $value = $Matches[2].Trim()
        $value = $value.Trim([char]34).Trim([char]39)
        if ($value) { Set-Item -Path "Env:$name" -Value $value }
    }
}
if (-not $env:DEEPSEEK_API_KEY) { throw "DEEPSEEK_API_KEY ist leer." }

$env:LLM_PROVIDER       = 'deepseek'
$env:LLM_MODEL          = 'deepseek-v4-flash'
$env:LLM_CONTEXT_TOKENS = '65536'

# --- Guthabenpruefung -------------------------------------------------------
# Der Grund fuer diesen Nachlauf. Ohne gedecktes Konto antwortet die API mit
# HTTP 402, das Werkzeug verbraucht sein tenacity-Budget und liefert nichts.
Write-Log "Pruefe DeepSeek-Guthaben vor dem Start"
try {
    $bal = Invoke-RestMethod -Uri 'https://api.deepseek.com/user/balance' -Headers @{ Authorization = "Bearer $($env:DEEPSEEK_API_KEY)" } -Method Get
} catch {
    throw "Guthabenabfrage fehlgeschlagen: $($_.Exception.Message). Ohne diese Auskunft wird nicht gestartet."
}
$usd = ($bal.balance_infos | Where-Object { $_.currency -eq 'USD' } | Select-Object -First 1).total_balance
Write-Log "Guthaben: is_available=$($bal.is_available), USD=$usd"
if (-not $bal.is_available) { throw "DeepSeek meldet is_available=false -- Konto nicht gedeckt. Kein Start; genau daran sind die vier Tasks im Hauptlauf gescheitert." }
if ([double]$usd -lt $CostCeiling) { throw "Guthaben $usd USD liegt unter dem Kostendeckel $CostCeiling USD. Erst aufladen." }

Write-Log "Nachlauf LLMSmartAudit, runid=$RunId, Contracts=$($Files -join ', ')"
Write-Log "Backend: provider=$($env:LLM_PROVIDER) model=$($env:LLM_MODEL) context=$($env:LLM_CONTEXT_TOKENS)"
Write-Log "MAIN: nicht gesetzt, wie im Hauptlauf"

$patterns = $Files | ForEach-Object { "samples/gptscan/mwevariety_fixed:$_.sol" }

Push-Location $SbDir
try {
    # Kein --results: der Default results/${TOOL}/${RUNID}/${FILENAME} ist gewollt.
    $sbArgs = @('-m', 'sb', '-t', 'llmsmartaudit', '-f') + $patterns +
              @('--timeout', 7200, '--processes', $Processes, '--runid', $RunId)
    Write-Log "Aufruf: python $($sbArgs -join ' ')"
    $proc = Start-Process -FilePath $Py -ArgumentList $sbArgs -NoNewWindow -PassThru

    while (-not $proc.HasExited) {
        Start-Sleep -Seconds 120
        $c = Get-RunCost -Id $RunId
        Write-Log ("Zwischenstand: {0} Tasks, {1:N0} Prompt-, {2:N0} Completion-Tokens, ~{3:N2} USD" -f $c.Tasks, $c.Prompt, $c.Completion, $c.Cost)
        if ($c.Cost -gt $CostCeiling) {
            Write-Log "ABBRUCH: laufende Summe ueber dem Deckel $CostCeiling USD."
            try { $proc.Kill() } catch {}
            throw "Kostendeckel ueberschritten."
        }
    }
    Write-Log "=== Ende, ExitCode=$($proc.ExitCode)"

    $dir = "results\llmsmartaudit\$RunId"
    if (Test-Path $dir) {
        Write-Log "Reparse $dir"
        & $Py -m sb.reparse $dir --processes $Processes
    }
}
finally {
    Pop-Location
}

$final = Get-RunCost -Id $RunId
Write-Log ("FERTIG: {0} Tasks, {1:N0} Prompt-, {2:N0} Completion-Tokens, geschaetzt ~{3:N2} USD" -f $final.Tasks, $final.Prompt, $final.Completion, $final.Cost)
Write-Log "Protokoll: $LogFile"
Write-Log "Naechster Schritt: python analysis_tools\build_eval.py llmsa_mwefixed_v2 --merge-run $RunId"
