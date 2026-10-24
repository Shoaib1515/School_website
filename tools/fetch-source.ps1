$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$cache = Join-Path $root "source-cache"
$pages = Get-Content -Raw (Join-Path $PSScriptRoot "pages.json") | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path $cache | Out-Null

foreach ($page in $pages) {
  $suffix = if ($page.path) { "/$($page.path)" } else { "" }
  $uri = "https://www.nordangliaeducation.com/bisc-south-loop$suffix"
  $destination = Join-Path $cache "$($page.name).html"
  Write-Host "Fetching $uri"
  Invoke-WebRequest -UseBasicParsing -Uri $uri -OutFile $destination
}

