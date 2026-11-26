# O'quv maqsadidagi RPS-asosli autoscaler.
# Alohida PowerShell oynasida: .\autoscale.ps1
# Tugatish: Ctrl+C
param(
    [int]$MinReplicas = 1,
    [int]$MaxReplicas = 4,
    [int]$WindowSeconds = 10,
    [int]$UpThreshold = 60,
    [int]$DownThreshold = 5,
    [int]$CooldownSeconds = 20
)
$ErrorActionPreference = 'Stop'
$quietWindows = 0
$lastScale = [datetime]::MinValue

Write-Host 'Autoscaler ishga tushdi (HTTP /api so`rovlari bo`yicha).' -ForegroundColor Cyan
Write-Host "Chegaralar: $UpThreshold / $WindowSeconds s (oshirish), $DownThreshold / $WindowSeconds s (kamaytirish)"
Write-Host 'To`xtatish: Ctrl+C'

while ($true) {
    Start-Sleep -Seconds $WindowSeconds
    $ids = @(docker compose ps --status running -q app | Where-Object { $_.Trim() -ne '' })
    if ($LASTEXITCODE -ne 0) { Write-Host 'Compose holatini tekshirishda xato.'; break }
    $replicas = $ids.Count
    if ($replicas -eq 0) { Write-Host 'app xizmati ishlamayapti. Avval docker compose up -d --build bajaring.'; continue }

    $since = "${WindowSeconds}s"
    $logs = @(docker compose logs --no-log-prefix --since $since proxy 2>$null)
    $requests = @($logs | Where-Object { $_ -match '"GET /api(?:[? ])' }).Count
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Oxirgi ${WindowSeconds}s: $requests so'rov; app konteynerlar: $replicas"
    if ($requests -lt $DownThreshold) { $quietWindows += 1 } else { $quietWindows = 0 }

    if (((Get-Date) - $lastScale).TotalSeconds -lt $CooldownSeconds) { continue }
    $target = $replicas
    if ($requests -ge $UpThreshold -and $replicas -lt $MaxReplicas) {
        $target = $replicas + 1
    } elseif ($quietWindows -ge 3 -and $replicas -gt $MinReplicas) {
        $target = $replicas - 1
    }

    if ($target -ne $replicas) {
        Write-Host "Masshtablash: $replicas -> $target" -ForegroundColor Yellow
        docker compose up -d --no-deps --scale "app=$target" app
        if ($LASTEXITCODE -ne 0) { Write-Host 'Masshtablashda xato.' -ForegroundColor Red; continue }
        $lastScale = Get-Date
        $quietWindows = 0
    }
}
