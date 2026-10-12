param([string]$DbUrl = $env:DATABASE_URL, [string]$OutDir = "./backups")
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $OutDir "palmistry-$stamp.sql"
pg_dump $DbUrl -f $out
Write-Host "backup: $out"
