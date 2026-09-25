<#
.SYNOPSIS
  Nachlauf LLMSmartAudit fuer die Tasks, die im Hauptlauf llmsa_mwefixed_v2
  ohne Ergebnis blieben, WEIL DAS GUTHABEN AUSGING -- nicht, weil das Werkzeug
  oder der Contract ein Problem hatte.

  INTERPRETER: Der aufgezeichnete Nachlauf lief auf einem Rechner mit
  smartbugs\venv; der Pfad ist seit 24.09.2026 an README und die uebrigen
  Runner angeglichen (smartbugs\.venv).

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

  ABGRENZUNG zu den 37 Tasks mit "Kontext ueberschritten": die sind NICHT
  Gegenstand dieses Skripts. Deren Abbruch (max_tokens_exceeded_by_camel,
  num_tokens > 65.536) ist die in camel/utils.py:134 fest eingetragene Grenze
  von 65.536 Token, die camel vor dem Aufruf selbst prueft; ob die API mehr
  annaehme, ist nicht geprueft. Ein Wiederholungslauf ohne Aenderung am
  Verfahren wuerde dort dasselbe Ergebnis und echte Kosten erzeugen.

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

.PARAMETER Corpus
  Verzeichnis unter smartbugs\, aus dem die Dateien kommen; Default der
  reparierte Korpus. Fuer MAIN-Laeufe der von corpus_tools\make_main_corpus.py
  erzeugte Ordner samples/gptscan/mwevariety_fixed_main; die Dateien heissen
  dort <contest>/<Hauptcontract>, also z. B. -Files '13/RCOrderbook'.

.PARAMETER Main
  Uebergibt --main an SmartBugs: der Entrypoint reduziert die Datei vor der
  Analyse auf den Contract, nach dem sie heisst (scripts/main_contract.py).
  SmartBugs verlangt dafuer Dateiname == Contractname, siehe -Corpus. Der
  Ergebnispfad enthaelt dann ${RELDIR}, weil Hauptcontracts mehrfach vorkommen.

  Seit 24.09.2026 dient das Skript ueber die vier 402-Faelle hinaus als
  allgemeiner Nachlauf-Runner fuer eine Dateiliste (Laeufe
  llmsa_mwefixed_v2_ctx1m und llmsa_mwefixed_v2_main37).

.EXAMPLE
  .\run_retry_llmsa.ps1

  Die vier 402-Faelle (12_Witch, 25_CompositeMultiOracle, 43_DelegatedStaking,
  62_Locke) aus samples/gptscan/mwevariety_fixed unter der runid
  llmsa_mwefixed_v2_retry, Deckel 3 USD -- der Nachlauf vom 15.09.2026.

.EXAMPLE
  .\run_retry_llmsa.ps1 -Files 29_HybridPool,30_Vault,10_Visor -RunId llmsa_mwefixed_v2_ctx1m -ContextTokens 1000000 -Processes 4 -CostCeiling 8

  Eine Dateiliste mit angehobener Kontextgrenze unter eigener runid, wie beim
  Nachlauf llmsa_mwefixed_v2_ctx1m vom 24.09.2026 (37 Contracts,
  context=1000000). Der Deckel muss dafuer ueber dem Default von 3 USD liegen.

.EXAMPLE
  .\run_retry_llmsa.ps1 -Main -Corpus samples/gptscan/mwevariety_fixed_main -Files '13/RCOrderbook','30/Vault' -RunId llmsa_mwefixed_v2_main37

  MAIN-Lauf auf dem von corpus_tools\make_main_corpus.py erzeugten Ordner; die
  Dateien heissen dort <contest>/<Hauptcontract>. SmartBugs bekommt --main und
  --results results/${TOOL}/<RunId>/${RELDIR}/${FILENAME}.

.OUTPUTS
  Keine Pipeline-Objekte. Das Skript schreibt:
  - smartbugs\results\llmsmartaudit\<RunId>\<Datei>.sol\  je Task
    smartbugs.json, result.log, result.tar und nach dem Reparse result.json;
    mit -Main stattdessen <RunId>\<contest>\<Hauptcontract>.sol\;
  - eval\_runlogs\llmsa_retry_<Zeitstempel>.log  das Protokoll dieses Laufs
    (Guthaben vor und nach, Backend, Image-ID, Kostenzwischenstaende).
  Zusammengefuehrt wird mit dem Hauptlauf durch
  python analysis_tools\build_eval.py llmsa_mwefixed_v2 --merge-run <RunId>,
  das nach eval\llmsa_mwefixed_v2\ schreibt.
#>
[CmdletBinding()]
param(
    [string[]]$Files = @('12_Witch', '25_CompositeMultiOracle', '43_DelegatedStaking', '62_Locke'),
    [int]$Processes = 3,
    [double]$CostCeiling = 3.00,
    [string]$RunId = 'llmsa_mwefixed_v2_retry',
    [string]$Corpus = 'samples/gptscan/mwevariety_fixed',
    [switch]$Main,
    # Backend zur Laufzeit waehlbar. Die Defaults entsprechen dem Hauptlauf;
    # ein Nachlauf mit anderem Backend ersetzt keine Tasks des Hauptlaufs,
    # sondern gehoert unter eine eigene -RunId.
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
$LogFile  = Join-Path $LogDir "llmsa_retry_$Stamp.log"

function Write-Log {
    param([string]$Message)
    $line = "[{0:yyyy-MM-dd HH:mm:ss}] {1}" -f (Get-Date), $Message
    Write-Host $line
    # Eine kurz von einem anderen Prozess gehaltene Datei (Editor, Virenscanner,
    # git) darf den Lauf nicht beenden: am 24.09.2026 warf Add-Content hier eine
    # IOException, der Runner starb und SmartBugs lief ohne Kostenwaechter weiter.
    for ($try = 1; $try -le 5; $try++) {
        try { Add-Content -Path $LogFile -Value $line -Encoding utf8 -ErrorAction Stop; return }
        catch [System.IO.IOException] { Start-Sleep -Milliseconds (200 * $try) }
    }
    Write-Host "  (Protokollzeile konnte nicht geschrieben werden: $LogFile ist gesperrt)"
}

# Preise wie in run_full_v2_llmsa.ps1 und analysis_tools/build_eval.py.
# Naeherung fuer die Bremse; verbindlich ist die DeepSeek-Abrechnung.
# Gemessen am 24.09.2026 (Nachlauf llmsa_mwefixed_v2_ctx1m): Schaetzung nach
# diesen Saetzen 11,42 USD, abgebucht 5,55 USD (Faktor 2,06), weil der Anbieter
# Cache-Treffer im Prompt mit einem Bruchteil des Satzes abrechnet. Die Saetze
# bleiben bewusst so: der Deckel soll zu frueh greifen, nie zu spaet. Die
# tatsaechliche Abbuchung steht seitdem als Kontostand-Differenz im Protokoll.
$PricePromptPerM     = 0.0908
$PriceCompletionPerM = 0.3695


function Get-DeepSeekBalanceUsd {
    # Kontostand in USD laut https://api.deepseek.com/user/balance; $null, wenn
    # kein Schluessel gesetzt ist oder die Abfrage scheitert. Der Schluessel
    # wird nicht protokolliert. Zweck: die tatsaechliche Abbuchung eines Laufs
    # als Differenz vor/nach festhalten, neben der Schaetzung aus den Tokens.
    if (-not $env:DEEPSEEK_API_KEY) { return $null }
    try {
        $bal = Invoke-RestMethod -Uri 'https://api.deepseek.com/user/balance' -Headers @{ Authorization = "Bearer $($env:DEEPSEEK_API_KEY)" } -Method Get
        $usd = ($bal.balance_infos | Where-Object { $_.currency -eq 'USD' } | Select-Object -First 1).total_balance
        if ($null -eq $usd) { return $null }
        return [double]$usd
    } catch { return $null }
}

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
$env:LLM_MODEL          = $Model
$env:LLM_CONTEXT_TOKENS = "$ContextTokens"
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
if ($dropped.Count) {
    Write-Log ("Nicht benoetigte Schluessel aus der Umgebung entfernt: " + ($dropped -join ', '))
}

# --- Guthabenpruefung -------------------------------------------------------
# Der Grund fuer diesen Nachlauf. Ohne gedecktes Konto antwortet die API mit
# HTTP 402, das Werkzeug verbraucht sein tenacity-Budget und liefert nichts.
# Die Abfrage ist DeepSeek-spezifisch; fuer andere Anbieter gibt es hier keine
# entsprechende Auskunft, deshalb entfaellt sie dort.
if ($Provider -eq 'deepseek') {
    Write-Log "Pruefe DeepSeek-Guthaben vor dem Start"
    try {
        $bal = Invoke-RestMethod -Uri 'https://api.deepseek.com/user/balance' -Headers @{ Authorization = "Bearer $($env:DEEPSEEK_API_KEY)" } -Method Get
    } catch {
        throw "Guthabenabfrage fehlgeschlagen: $($_.Exception.Message). Ohne diese Auskunft wird nicht gestartet."
    }
    $usd = ($bal.balance_infos | Where-Object { $_.currency -eq 'USD' } | Select-Object -First 1).total_balance
    Write-Log "Guthaben: is_available=$($bal.is_available), USD=$usd"
    $balanceBefore = [double]$usd
    if (-not $bal.is_available) { throw "DeepSeek meldet is_available=false -- Konto nicht gedeckt. Kein Start; genau daran sind die vier Tasks im Hauptlauf gescheitert." }
    if ([double]$usd -lt $CostCeiling) { throw "Guthaben $usd USD liegt unter dem Kostendeckel $CostCeiling USD. Erst aufladen." }
}
else {
    Write-Log "Guthabenpruefung uebersprungen: nur fuer -Provider deepseek verfuegbar."
}

Write-Log "Nachlauf LLMSmartAudit, runid=$RunId, Contracts=$($Files -join ', ')"
if ($fromEnv.Count) {
    Write-Log ("Aus $EnvFile uebernommen: " + ($fromEnv -join ', ') +
               " (ein ausdruecklicher Parameter haette Vorrang).")
}
Write-Log "Backend: provider=$($env:LLM_PROVIDER) model=$($env:LLM_MODEL) context=$($env:LLM_CONTEXT_TOKENS)$(if ($BaseUrl) { " base_url=$BaseUrl" })"
# Image-ID festhalten: der Tag smartbugs/llmsmartaudit:1.0 bleibt bei einem
# Neubau gleich, die ID nicht (24.09.2026: e72f37d07212 -> 7c111aa6b366).
$imageId = @(cmd /c 'docker image inspect --format "{{.Id}}" smartbugs/llmsmartaudit:1.0 2>nul') | Select-Object -First 1
Write-Log "Image: smartbugs/llmsmartaudit:1.0 $imageId"
if ($Main) { Write-Log "MAIN: gesetzt (--main), Korpus $Corpus" }
else { Write-Log "MAIN: nicht gesetzt, wie im Hauptlauf" }

$patterns = $Files | ForEach-Object { "${Corpus}:$_.sol" }

Push-Location $SbDir
try {
    # Ohne MAIN kein --results: der Default results/${TOOL}/${RUNID}/${FILENAME}
    # ist gewollt. Mit MAIN liegen die Dateien in Contest-Unterordnern und
    # gleichnamige Hauptcontracts brauchen ${RELDIR} im Pfad.
    $sbArgs = @('-m', 'sb', '-t', 'llmsmartaudit', '-f') + $patterns +
              @('--timeout', 7200, '--processes', $Processes, '--runid', $RunId)
    if ($Main) {
        $sbArgs += @('--main', '--results', ('results/${TOOL}/' + $RunId + '/${RELDIR}/${FILENAME}'))
    }
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
# Tatsaechliche Abbuchung: Kontostand nach dem Lauf gegen den vor dem Start.
# Die Schaetzung oben liegt nach der Messung vom 24.09.2026 um etwa Faktor 2
# zu hoch (Cache-Rabatt des Anbieters); massgeblich ist die Differenz hier.
if ($Provider -eq 'deepseek' -and $null -ne $balanceBefore) {
    $balanceAfter = Get-DeepSeekBalanceUsd
    if ($null -ne $balanceAfter) {
        Write-Log ("Guthaben nach Ende: {0:N2} USD; abgebucht {1:N2} USD (Schaetzung {2:N2} USD)" -f $balanceAfter, ($balanceBefore - $balanceAfter), $final.Cost)
    }
    else { Write-Log "Guthaben nach Ende: Abfrage fehlgeschlagen, Abbuchung nicht ermittelt." }
}
Write-Log "Protokoll: $LogFile"
Write-Log "Naechster Schritt: python analysis_tools\build_eval.py llmsa_mwefixed_v2 --merge-run $RunId"
