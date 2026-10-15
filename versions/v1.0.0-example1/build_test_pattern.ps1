param([string]$TdHome = 'C:\APP2\ALTD', [string]$WorkDir)
$ErrorActionPreference = 'Stop'
if (!$WorkDir) { $WorkDir = Join-Path $PSScriptRoot 'pattern_work' }
$taskPatternWork = [System.IO.Path]::GetFullPath($WorkDir)
if (Test-Path -LiteralPath $taskPatternWork) {
    throw 'WorkDir must be a new directory; choose another path to retain earlier builds.'
}
if ($taskPatternWork.Length -gt 110) {
    throw 'TD has Windows path-length limits. Select a shorter writable WorkDir.'
}
New-Item -ItemType Directory -Path $taskPatternWork | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'user_source') -Destination $taskPatternWork -Recurse
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'td_project') -Destination $taskPatternWork -Recurse
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'build.ps1') -Destination $taskPatternWork
$taskTop = Join-Path $taskPatternWork 'user_source/hdl_source/design_top_wrapper.v'
$taskText = Get-Content -LiteralPath $taskTop -Raw -Encoding utf8
if (![regex]::IsMatch($taskText, 'parameter DISPLAY_TEST_PATTERN = 0')) {
    throw 'Expected camera-mode top parameter was not found.'
}
$taskText.Replace('parameter DISPLAY_TEST_PATTERN = 0', 'parameter DISPLAY_TEST_PATTERN = 1') |
    Set-Content -LiteralPath $taskTop -Encoding utf8
& (Join-Path $taskPatternWork 'build.ps1') -TdHome $TdHome
foreach ($taskSuffix in @('', '_compress')) {
    Copy-Item -LiteralPath (Join-Path $taskPatternWork "DSI_SC500_7inch_v2${taskSuffix}.bit") `
        -Destination (Join-Path $PSScriptRoot "DSI_TEST_PATTERN${taskSuffix}.bit") -Force
}
Write-Host 'Test-pattern images generated; camera project sources were retained.'
