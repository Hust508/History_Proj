param([string]$VivadoBin = 'C:/APP2/VIVADO/2025.1/Vivado/bin')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskRun = Join-Path $PSScriptRoot 'sim_work'
New-Item -ItemType Directory -Force -Path $taskRun | Out-Null
Push-Location -LiteralPath $taskRun
try {
    & (Join-Path $VivadoBin 'xvlog.bat') -sv `
        (Join-Path $taskRoot 'user_source/hdl_source/isp/edge_detect_96.v') `
        (Join-Path $taskRoot 'user_source/hdl_source/data_96bit_to_128bit.v') `
        (Join-Path $taskRoot 'user_source/hdl_source/video_out.v') `
        (Join-Path $PSScriptRoot 'edge_pipeline_tb.sv') `
        (Join-Path $PSScriptRoot 'crop_tb.sv') *> compile.log
    if ($LASTEXITCODE -ne 0) { throw 'RTL compile failed; see sim_work/compile.log' }
    foreach ($taskTop in @('edge_small_tb','edge_720p_tb','crop_tb')) {
        & (Join-Path $VivadoBin 'xelab.bat') $taskTop -s $taskTop --timescale 1ns/1ps *> "${taskTop}_elab.log"
        if ($LASTEXITCODE -ne 0) { throw "Elaboration failed: $taskTop" }
        & (Join-Path $VivadoBin 'xsim.bat') $taskTop -R *> "${taskTop}_run.log"
        if ($LASTEXITCODE -ne 0) { throw "Simulation failed: $taskTop" }
        if (!(Select-String -LiteralPath "${taskTop}_run.log" -Pattern '^PASS' -Quiet)) {
            throw "No PASS result: $taskTop"
        }
        Select-String -LiteralPath "${taskTop}_run.log" -Pattern '^PASS' | ForEach-Object { $_.Line }
    }
} finally { Pop-Location }
