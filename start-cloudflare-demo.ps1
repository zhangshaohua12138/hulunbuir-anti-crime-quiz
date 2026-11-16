#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

$port = 8080
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    throw "端口 $port 已被占用。请先停止已有演示服务（可能是上一次启动的 server.py），再运行本脚本。"
}

$cloudflared = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cloudflared) {
    throw "未找到 cloudflared。请先执行：winget install --id Cloudflare.cloudflared -e"
}

$python = Join-Path $env:USERPROFILE '.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path $python)) {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $python) {
    throw "未找到 Python。请安装 Python 3.11+，或使用项目自带的 Python 环境。"
}

$dataDir = Join-Path $root 'data'
New-Item -ItemType Directory -Force $dataDir | Out-Null
$tunnelLog = Join-Path $dataDir 'cloudflared-demo.log'
$tunnelOut = Join-Path $dataDir 'cloudflared-demo.out.log'
Remove-Item $tunnelLog, $tunnelOut -Force -ErrorAction SilentlyContinue

Write-Host '正在创建 Cloudflare 临时隧道...' -ForegroundColor Cyan
$tunnel = Start-Process -FilePath $cloudflared `
    -ArgumentList @('tunnel', '--url', "http://127.0.0.1:$port", '--no-autoupdate') `
    -RedirectStandardError $tunnelLog -RedirectStandardOutput $tunnelOut `
    -WindowStyle Hidden -PassThru

$url = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Path $tunnelLog) {
        $match = Select-String -Path $tunnelLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -AllMatches |
            Select-Object -First 1
        if ($match) {
            $url = $match.Matches[0].Value
            break
        }
    }
}

if (-not $url) {
    Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
    throw "隧道创建失败，请查看日志：$tunnelLog"
}

$env:APP_MODE = 'demo'
$env:HOST = '127.0.0.1'
$env:PORT = "$port"
$env:PUBLIC_URL = $url
$env:ADMIN_PASSWORD = if ($env:ADMIN_PASSWORD) { $env:ADMIN_PASSWORD } else { '123456' }
$env:DATABASE_PATH = Join-Path $dataDir 'customer-demo.db'

Write-Host '正在启动答题系统...' -ForegroundColor Cyan
$server = Start-Process -FilePath $python `
    -ArgumentList @('server.py') -WorkingDirectory $root `
    -NoNewWindow -PassThru

$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$port/api/health" -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $healthy = $true; break }
    } catch { }
}

if (-not $healthy) {
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
    throw '服务启动失败，请检查 server.py 输出。'
}

Write-Host ''
Write-Host '========================================' -ForegroundColor Green
Write-Host ' 本地演示已启动' -ForegroundColor Green
Write-Host " 活动页：$url" -ForegroundColor White
Write-Host " 后台：  $url/#admin" -ForegroundColor White
Write-Host " 后台密码：$env:ADMIN_PASSWORD" -ForegroundColor White
Write-Host '========================================' -ForegroundColor Green
Write-Host '按 Ctrl+C 停止演示。' -ForegroundColor DarkGray

try {
    Wait-Process -Id $server.Id
} finally {
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
    Write-Host '演示已停止。' -ForegroundColor Yellow
}
