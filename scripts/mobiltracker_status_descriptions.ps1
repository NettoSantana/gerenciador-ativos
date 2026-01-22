# Caminho: C:\Users\vlula\OneDrive\Área de Trabalho\Projetos Backup\gerenciador-ativos\scripts\mobiltracker_status_descriptions.ps1
# Último recode: 2026-01-21 20:05 (America/Maceio)
# Motivo: Corrigir erro de parse e padronizar autenticação (AuthDevice) para baixar status-descriptions, trackers/status e last-location, gerar patch e relatório de mapeamentos.

param(
  [Parameter(Mandatory = $true)]
  [int]$TrackerId,

  [string]$OutDir = ".",

  [switch]$OpenNotepad
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Ensure-Dir([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return }
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Safe-WriteJson([object]$Obj, [string]$Path, [int]$Depth = 50) {
  $json = $Obj | ConvertTo-Json -Depth $Depth
  $json | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Apply-StatusPatch([pscustomobject]$sd) {
  if (-not $sd) { return $sd }

  # MOVEMENT: adicionar STOPPED e UNDEFINED (aparece em trackers/status)
  if ($sd.PSObject.Properties.Name -contains "MOVEMENT") {
    $mv = $sd.MOVEMENT
    if (-not $mv.values) {
      $mv | Add-Member -MemberType NoteProperty -Name values -Value ([pscustomobject]@{}) -Force
    }

    if (-not ($mv.values.PSObject.Properties.Name -contains "STOPPED")) {
      $mv.values | Add-Member -MemberType NoteProperty -Name "STOPPED" -Value ([pscustomobject]@{
        summary     = "Parado"
        severity    = "success"
        description = "Seu rastreador esta parado"
        icon        = $null
        unit        = $null
      }) -Force
    }

    if (-not ($mv.values.PSObject.Properties.Name -contains "UNDEFINED")) {
      $mv.values | Add-Member -MemberType NoteProperty -Name "UNDEFINED" -Value ([pscustomobject]@{
        summary     = "Indefinido"
        severity    = "warning"
        description = "Nao foi possivel determinar o estado de movimento"
        icon        = $null
        unit        = $null
      }) -Force
    }
  }

  # CUT: adicionar OFF (aparece em trackers/status)
  if ($sd.PSObject.Properties.Name -contains "CUT") {
    $cut = $sd.CUT
    if (-not $cut.values) {
      $cut | Add-Member -MemberType NoteProperty -Name values -Value ([pscustomobject]@{}) -Force
    }

    if (-not ($cut.values.PSObject.Properties.Name -contains "OFF")) {
      $cut.values | Add-Member -MemberType NoteProperty -Name "OFF" -Value ([pscustomobject]@{
        summary     = "Desbloqueado"
        severity    = "success"
        description = "Veiculo desbloqueado"
        icon        = $null
        unit        = $null
      }) -Force
    }

    # booleanos (quando vier False)
    if (-not ($cut.values.PSObject.Properties.Name -contains "False")) {
      $cut.values | Add-Member -MemberType NoteProperty -Name "False" -Value $cut.values.OFF -Force
    }
  }

  # BAT: adicionar key 100 e estender range 80..99 -> 80..100
  if ($sd.PSObject.Properties.Name -contains "BAT") {
    $bat = $sd.BAT
    if (-not $bat.values) {
      $bat | Add-Member -MemberType NoteProperty -Name values -Value ([pscustomobject]@{}) -Force
    }

    if (-not ($bat.values.PSObject.Properties.Name -contains "100")) {
      $bat.values | Add-Member -MemberType NoteProperty -Name "100" -Value ([pscustomobject]@{
        summary     = "100%"
        severity    = "success"
        description = $null
        icon        = "battery-4"
        unit        = $null
      }) -Force
    }

    if ($bat.rangesDescriptions) {
      foreach ($r in $bat.rangesDescriptions) {
        if ($r.minValue -eq 80 -and $r.maxValue -eq 99) {
          $r.maxValue = 100
        }
      }
    }
  }

  return $sd
}

function Get-ValueKeyCandidates([string]$val) {
  $cands = New-Object System.Collections.Generic.HashSet[string]
  if (-not [string]::IsNullOrWhiteSpace($val)) {
    [void]$cands.Add($val)
    [void]$cands.Add($val.ToUpperInvariant())
    [void]$cands.Add($val.ToLowerInvariant())

    if ($val -eq "true")  { [void]$cands.Add("True");  [void]$cands.Add("TRUE") }
    if ($val -eq "false") { [void]$cands.Add("False"); [void]$cands.Add("FALSE") }
  }
  return $cands
}

function Resolve-StatusMissing([pscustomobject]$sd, [object[]]$trackersStatus) {
  $missing = @()

  foreach ($t in $trackersStatus) {
    foreach ($s in $t.statuses) {
      $name = [string]$s.name
      $val  = [string]$s.status

      if (-not ($sd.PSObject.Properties.Name -contains $name)) {
        $missing += [pscustomobject]@{ name=$name; status=$val; reason="categoria nao existe no status-descriptions" }
        continue
      }

      $cat  = $sd.$name
      $type = [string]$cat.type

      # NUMBER com ranges: ok se cair em algum range
      if ($type -eq "NUMBER" -and $cat.rangesDescriptions) {
        $num = $null
        if ([double]::TryParse($val, [ref]$num)) {
          $ok = $false
          foreach ($r in $cat.rangesDescriptions) {
            if ($num -ge [double]$r.minValue -and $num -le [double]$r.maxValue) { $ok = $true; break }
          }
          if (-not $ok) {
            $missing += [pscustomobject]@{ name=$name; status=$val; reason="fora dos rangesDescriptions" }
          }
        } else {
          $missing += [pscustomobject]@{ name=$name; status=$val; reason="nao e numero (type=NUMBER)" }
        }
        continue
      }

      # LITERAL (ou NUMBER sem ranges): precisa existir key em values
      if (-not $cat.values) {
        $missing += [pscustomobject]@{ name=$name; status=$val; reason="sem values (e sem ranges aplicaveis)" }
        continue
      }

      $valueKeys = $cat.values.PSObject.Properties.Name
      $cands = Get-ValueKeyCandidates $val

      $found = $false
      foreach ($cand in $cands) {
        if ($valueKeys -contains $cand) { $found = $true; break }
      }

      if (-not $found) {
        $missing += [pscustomobject]@{ name=$name; status=$val; reason="nao existe key em values" }
      }
    }
  }

  return $missing | Sort-Object name, status -Unique
}

# ============================================================
# 1) Preparar diretorio de saida
# ============================================================
Ensure-Dir $OutDir

# ============================================================
# 2) Headers e URLs
#    OBS: Mobiltracker usa Authorization: AuthDevice <CHAVE>
# ============================================================
$token = $env:MOBILTRACKER_KEY
if (-not $token) { throw 'Defina o token antes: $env:MOBILTRACKER_KEY = "..."' }

$headers = @{
  Accept        = "application/json"
  Authorization = "AuthDevice $token"
}

$statusDescUrl = "https://api.mobiltracker.com.br/status-descriptions"
$trackersUrl   = "https://api.mobiltracker.com.br/trackers/status"
$lastLocUrl    = "https://api.mobiltracker.com.br/trackers/$TrackerId/last-location"

$statusDescFile  = Join-Path $OutDir "status-descriptions.json"
$trackersFile    = Join-Path $OutDir "trackers-status.json"
$lastLocFile     = Join-Path $OutDir ("tracker-$TrackerId-last-location.json")
$patchedDescFile = Join-Path $OutDir "status-descriptions.merged.json"
$missingFile     = Join-Path $OutDir "missing-status-mappings.json"

# ============================================================
# 3) GET: status-descriptions
# ============================================================
$sdRaw = Invoke-RestMethod -Uri $statusDescUrl -Headers $headers -Method Get
Safe-WriteJson $sdRaw $statusDescFile 50
Write-Host "OK: baixou status-descriptions -> $statusDescFile"

# ============================================================
# 4) GET: trackers/status
# ============================================================
$tsRaw = Invoke-RestMethod -Uri $trackersUrl -Headers $headers -Method Get
Safe-WriteJson $tsRaw $trackersFile 50
Write-Host "OK: baixou trackers-status -> $trackersFile"

# ============================================================
# 5) GET: last-location (do tracker informado)
# ============================================================
$llRaw = Invoke-RestMethod -Uri $lastLocUrl -Headers $headers -Method Get
Safe-WriteJson $llRaw $lastLocFile 50
Write-Host "OK: baixou last-location -> $lastLocFile"

# ============================================================
# 6) Patch + Missing report
# ============================================================
$sd = Get-Content -LiteralPath $statusDescFile -Raw | ConvertFrom-Json
$sd = Apply-StatusPatch $sd
Safe-WriteJson $sd $patchedDescFile 80
Write-Host "OK: gerou status-descriptions.merged -> $patchedDescFile"

$ts = Get-Content -LiteralPath $trackersFile -Raw | ConvertFrom-Json
$tsValue = @()
if ($ts -and ($ts.PSObject.Properties.Name -contains "value")) {
  $tsValue = @($ts.value)
}

if ($tsValue.Count -gt 0) {
  $missing = Resolve-StatusMissing $sd $tsValue
  Safe-WriteJson $missing $missingFile 10

  if ($missing.Count -gt 0) {
    Write-Host ("ATENCAO: faltam {0} mapeamentos (ver arquivo): {1}" -f $missing.Count, $missingFile) -ForegroundColor Yellow
    $missing | Format-Table -AutoSize | Out-String | Write-Host
  } else {
    Write-Host "OK: nenhum mapeamento faltando (com o merged)."
  }
} else {
  Write-Host "AVISO: trackers-status nao tem .value para validar mapeamentos." -ForegroundColor Yellow
}

# ============================================================
# 7) Abrir arquivos no Notepad (opcional)
# ============================================================
if ($OpenNotepad) {
  notepad $statusDescFile
  notepad $trackersFile
  notepad $lastLocFile
  notepad $patchedDescFile
  if (Test-Path -LiteralPath $missingFile) { notepad $missingFile }
}
