# Caminho: C:\Users\vlula\OneDrive\Área de Trabalho\Projetos Backup\gerenciador-ativos\mobiltracker_status_descriptions.ps1
# Último recode: 2026-01-21 09:37:47 (America/Maceio)
# Motivo: Corrigir Authorization (AuthDevice) e salvar o JSON bruto do /status-descriptions sem limite de Depth do ConvertTo-Json.

$ErrorActionPreference = "Stop"

# Força TLS 1.2 (ajuda em alguns ambientes Windows)
try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {}

# =========================
# CHAVE (troque depois)
# =========================
$KEY = "5247359a1d7a48d3a5f35ac386e1a8b1"

# Header correto (igual ao /trackers/status)
$headers = @{
  Authorization = "AuthDevice $KEY"
}

$url = "https://api.mobiltracker.com.br/status-descriptions"
$outFile = Join-Path $PSScriptRoot "status-descriptions.json"

try {
  Write-Host "Baixando: $url"

  # Pega o JSON bruto (sem serializar) — evita erro de Depth
  $respWeb = Invoke-WebRequest -Uri $url -Headers $headers -Method Get -UseBasicParsing
  $rawJson = $respWeb.Content

  if ([string]::IsNullOrWhiteSpace($rawJson)) {
    throw "Resposta vazia do endpoint."
  }

  # Valida se é JSON de verdade (se falhar aqui, você vê o erro real)
  $null = $rawJson | ConvertFrom-Json -ErrorAction Stop

  # Salva exatamente como veio
  $rawJson | Set-Content -Path $outFile -Encoding UTF8

  Write-Host "OK: JSON salvo em $outFile"
  notepad $outFile

} catch {
  Write-Host "ERRO ao chamar /status-descriptions" -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  throw
}
