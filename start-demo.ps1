$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:APP_MODE = 'demo'
$env:HOST = '127.0.0.1'
$env:PORT = '8080'
$bundledPython = Join-Path $env:USERPROFILE '.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
if (Test-Path $bundledPython) {
    & $bundledPython server.py
} else {
    python server.py
}
