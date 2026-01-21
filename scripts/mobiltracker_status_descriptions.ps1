# Caminho: C:\Users\vlula\OneDrive\Área de Trabalho\Projetos Backup\gerenciador-ativos\scripts\mobiltracker_status_descriptions.ps1
# Último recode: 2026-01-21 19:20 (America/Maceio)
# Motivo: Baixar JSONs do Mobiltracker, aplicar patch para status faltantes (ex.: BAT=100, CUT=OFF, MOVEMENT=STOPPED/UNDEFINED) e gerar relatório de mapeamentos ausentes.

param(
  [Parameter(Mandatory = $true)]
  [int]$TrackerId,

  [string]$OutDir = ".",

  [switch]$OpenNotepad
)

$ErrorActionPreference = "Stop"

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

  # ----------------------------
  # MOVEMENT: faltavam STOPPED e UNDEFINED (aparece em trackers/status)
  # ----------------------------
  if ($sd.PSObject.Properties.Name -contains "MOVEMENT") {
    $mv = $sd.MOVEMENT
    if (-not $mv.values) {
      $mv | Add-Member -MemberType NoteProperty -Name values -Value ([pscustomobject]@{}) -Force
    }

    if (-not ($mv.values.PSObject.Properties.Name -contains "STOPPED")) {
      $mv.values | Add-Member -MemberType NoteProperty -Name "STOPPED" -Value ([pscustomobject]@{
        summary     = "Parado"
        severity    = "success"
        description = "Seu rastreador está parado"
        icon        = $null
        unit        = $null
      }) -Force
    }

    if (-not ($mv.values.PSObject.Properties.Name -contains "UNDEFINED")) {
      $mv.values | Add-Member -MemberType NoteProperty -Name "UNDEFINED" -Value ([pscustomobject]@{
        summary     = "Movimento indefinido"
        severity    = "warning"
        description = "Não foi possível determinar o estado de movimento"
        icon        = $null
        unit        = $null
      }) -Force
    }
  }

  # ----------------------------
  # CUT: faltava OFF (aparece em trackers/status)
  # ----------------------------
  if ($sd.PSObject.Properties.Name -contains "CUT") {
    $cut = $sd.CUT
    if (-not $cut.values) {
      $cut | Add-Member -MemberType NoteProperty -Name values -Value ([pscustomobject]@{}) -Force
    }

    if (-not ($cut.values.PSObject.Properties.Name -contains "OFF")) {
      $cut.values | Add-Member -MemberType NoteProperty -Name "OFF" -Value ([pscustomobject]@{
        summary     = "Desbloqueado"
        severity    = "success"
        description = "Veículo desbloqueado"
        icon        = $null
        unit        = $null
      }) -Force
    }

    if (-not ($cut.values.PSObject.Properties.Name -contains "False")) {
      # alguns devices/integrações podem trazer booleano
      $cut.values | Add-Member -MemberType NoteProperty -Name "False" -Value $cut.values.OFF -Force
    }
  }

  # ----------------------------
  # BAT: aparece 100 nos rastreadores e não existia key 100, nem range até 100
  # ----------------------------
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
      # Ajusta o último range para incluir 100 (se existir o range 80..99)
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
    $cands.Add($val) | Out-Null
    $cands.Add($val.ToUpperInvariant()) | Out-Null
    $cands.Add($val.ToLowerInvariant()) | Out-Null

    if ($val -eq "true") { $cands.Add("True") | Out-Null; $cands.Add("TRUE") | Out-Null }
    if ($val -eq "false") { $cands.Add("False") | Out-Null; $cands.Add("FALSE") | Out-Null }
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
        $missing += [pscustomobject]@{
          name   = $name
          status = $val
          reason = "categoria não existe no status-descriptions"
        }
        continue
      }

      $cat = $sd.$name
      $type = [string]$cat.type

      # NUMBER com ranges: considera OK se valor cair em algum range
      if ($type -eq "NUMBER" -and $cat.rangesDescriptions) {
        $num = $null
        if ([double]::TryParse($val, [ref]$num)) {
          $ok = $false
          foreach ($r in $cat.rangesDescriptions) {
            if ($num -ge [double]$r.minValue -and $num -le [double]$r.maxValue) {
              $ok = $true
              break
            }
          }
          if (-not $ok) {
            $missing += [pscustomobject]@{ name=$name; status=$val; reason="fora dos rangesDescriptions" }
          }
        } else {
          $missing += [pscustomobject]@{ name=$name; status=$val; reason="não é número (type=NUMBER)" }
        }
        continue
      }

      # LITERAL (ou NUMBER sem ranges): precisa existir key em values
      $hasValues = $cat.values -ne $null
      if (-not $hasValues) {
        $missing += [pscustomobject]@{ name=$name; status=$val; reason="sem values (e sem ranges aplicáveis)" }
        continue
      }

      $valueKeys = $cat.values.PSObject.Properties.Name
      $cands = Get-ValueKeyCandidates $val

      $found = $false
      foreach ($cand in $cands) {
        if ($valueKeys -contains $cand) { $found = $true; break }
      }

      if (-not $found) {
        $missing += [pscustomobject]@{ name=$name; status=$val; reason="não existe key em values" }
      }
    }
  }

  return $missing | Sort-Object name, status -Unique
}

# ============================================================
# 1) Preparar diretório de saída
# ============================================================
Ensure-Dir $OutDir

# ============================================================
# 2) Headers e URLs
# ============================================================
$token = $env:MOBILTRACKER_KEY
if (-not $token) { throw "Defina o token antes: `$env:MOBILTRACKER_KEY = '...'`" }

$headers = @{
  Accept        = "application/json"
  Authorization = "Bearer $token"
}

$statusDescUrl = "https://api.mobiltracker.com.br/status-descriptions"
$trackersUrl   = "https://api.mobiltracker.com.br/trackers/status"
$lastLocUrl    = "https://api.mobiltracker.com.br/trackers/$TrackerId/last-location"

$statusDescFile = Join-Path $OutDir "status-descriptions.json"
$trackersFile   = Join-Path $OutDir "trackers-status.json"
$lastLocFile    = Join-Path $OutDir ("tracker-$TrackerId-last-location.json")

$patchedDescFile = Join-Path $OutDir "status-descriptions.merged.json"
$missingFile     = Join-Path $OutDir "missing-status-mappings.json"

# ============================================================
# 3) GET: status-descriptions
# ============================================================
try {
  $sdRaw = Invoke-RestMethod -Uri $statusDescUrl -Headers $headers -Method Get
  Safe-WriteJson $sdRaw $statusDescFile 50
  Write-Host "OK: baixou status-descriptions -> $statusDescFile"
} catch {
  Write-Host "ERRO no GET: $statusDescUrl" -ForegroundColor Red
  throw
}

# ============================================================
# 4) GET: trackers/status
# ============================================================
try {
  $tsRaw = Invoke-RestMethod -Uri $trackersUrl -Headers $headers -Method Get
  Safe-WriteJson $tsRaw $trackersFile 50
  Write-Host "OK: baixou trackers-status -> $trackersFile"
} catch {
  Write-Host "ERRO no GET: $trackersUrl" -ForegroundColor Red
  throw
}

# ============================================================
# 5) GET: last-location
# ============================================================
try {
  $llRaw = Invoke-RestMethod -Uri $lastLocUrl -Headers $headers -Method Get
  Safe-WriteJson $llRaw $lastLocFile 50
  Write-Host "OK: baixou last-location -> $lastLocFile"
} catch {
  Write-Host "ERRO no GET: $lastLocUrl" -ForegroundColor Red
  throw
}

# ============================================================
# 6) Patch + Missing report
# ============================================================
$sd = Get-Content -LiteralPath $statusDescFile -Raw | ConvertFrom-Json
$sd = Apply-StatusPatch $sd
Safe-WriteJson $sd $patchedDescFile 80
Write-Host "OK: gerou status-descriptions.merged -> $patchedDescFile"

$ts = Get-Content -LiteralPath $trackersFile -Raw | ConvertFrom-Json
$tsValue = @()
if ($ts -and $ts.PSObject.Properties.Name -contains "value") {
  $tsValue = @($ts.value)
}

if ($tsValue.Count -gt 0) {
  $missing = Resolve-StatusMissing $sd $tsValue

  Safe-WriteJson $missing $missingFile 10

  if ($missing.Count -gt 0) {
    Write-Host ("ATENÇÃO: faltam {0} mapeamentos (ver arquivo): {1}" -f $missing.Count, $missingFile) -ForegroundColor Yellow
    $missing | Format-Table -AutoSize | Out-String | Write-Host
  } else {
    Write-Host "OK: nenhum mapeamento faltando (com o merged)."
  }
} else {
  Write-Host "AVISO: trackers-status não tem .value para validar mapeamentos." -ForegroundColor Yellow
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
