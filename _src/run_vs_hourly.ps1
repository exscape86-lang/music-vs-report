# Hourly VS report build + GitHub Pages push
# Runs after collect_woody_isarang.py has refreshed data (Task Scheduler trigger at HH:10)
$ErrorActionPreference = 'Continue'
$base = 'C:\Users\wizsr\music_data_vs_compare'
$logDir = Join-Path $base 'logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = Join-Path $logDir "vs_run_$stamp.log"

function Log($msg) {
  $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
  Add-Content -Path $log -Value $line -Encoding utf8
  Write-Output $line
}

Log "=== VS hourly run start ==="

# 1. Rebuild HTML from latest CSV snapshots (no stderr redirect on native exe)
Log "Step 1: build_vs_report.py"
$buildOut = & python "$base\build_vs_report.py" 2>&1 | Out-String
Add-Content -Path $log -Value $buildOut -Encoding utf8
if ($LASTEXITCODE -ne 0) { Log "ERROR: build failed exit=$LASTEXITCODE"; exit 1 }

# 2. Copy index.html into the git working tree
Log "Step 2: copy index.html into pages_repo"
Copy-Item "$base\repo\index.html" "$base\pages_repo\index.html" -Force

# 3. Commit + push if changed
Log "Step 3: git commit + push"
Set-Location "$base\pages_repo"
$addOut = & git add index.html 2>&1 | Out-String
Add-Content -Path $log -Value $addOut -Encoding utf8
& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Log "No changes to commit; skipping push"
} else {
  $msg = "Hourly update $(Get-Date -Format 'yyyy-MM-dd HH:mm KST')"
  $commitOut = & git commit -m $msg 2>&1 | Out-String
  Add-Content -Path $log -Value $commitOut -Encoding utf8
  $pushOut = & git push origin main 2>&1 | Out-String
  Add-Content -Path $log -Value $pushOut -Encoding utf8
  if ($LASTEXITCODE -ne 0) { Log "ERROR: git push failed exit=$LASTEXITCODE"; exit 2 }
  Log "Pushed successfully"
}

Log "=== VS hourly run done ==="
exit 0
