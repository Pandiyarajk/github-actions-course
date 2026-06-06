# Resolve which test IDs a self-hosted QA run should execute.
#
# Priority:
#   1. If -RerunFailures is "true" and failures/failed-tests.json exists -> use those IDs.
#   2. Else if -BatchFile is given -> use .github/test-batches/<BatchFile>.json.
#   3. Else -> empty string, which the workflow treats as "run the full suite".
#
# Writes `test_ids=<comma-separated>` to the GitHub step output so a later
# step can branch with `if: steps.<id>.outputs.test_ids != ''`.
param(
    [string]$RerunFailures = "false",
    [string]$BatchFile = ""
)

$ids = @()

if ($RerunFailures -eq "true" -and (Test-Path "failures/failed-tests.json")) {
    $ids = Get-Content "failures/failed-tests.json" -Raw | ConvertFrom-Json
}
elseif ($BatchFile -ne "") {
    $batchPath = ".github/test-batches/$BatchFile.json"
    if (Test-Path $batchPath) {
        $ids = Get-Content $batchPath -Raw | ConvertFrom-Json
    }
}

$joined = ($ids -join ",")
Write-Host "Resolved test IDs: '$joined'"
"test_ids=$joined" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
