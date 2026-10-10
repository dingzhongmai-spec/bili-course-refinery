param([switch]$NoLaunch, [switch]$Refresh, [switch]$PortableTools)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskRuntime = Join-Path $taskRoot '.runtime'
New-Item -ItemType Directory -Path $taskRuntime -Force | Out-Null
$taskPython = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $taskCandidate = & py -3 -c 'import sys; print(sys.executable)' 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $taskCandidate)) { $taskPython = $taskCandidate }
}
if (-not $taskPython) {
    $taskLocalPython = Join-Path $taskRuntime 'python/python.exe'
    if (Test-Path -LiteralPath $taskLocalPython) { $taskPython = $taskLocalPython }
}
if (-not $taskPython -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $taskCandidate = & python -c 'import sys; print(sys.executable)' 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $taskCandidate)) { $taskPython = $taskCandidate }
}
if (-not $taskPython) {
    Write-Host 'Installing signed Python from python.org / 安装官方签名Python'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $taskInstaller = Join-Path $taskRuntime 'python-installer.exe'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe' -OutFile $taskInstaller
    $taskSignature = Get-AuthenticodeSignature -LiteralPath $taskInstaller
    if ($taskSignature.Status -ne 'Valid' -or $taskSignature.SignerCertificate.Subject -notlike '*Python Software Foundation*') { throw 'Python installer signature check failed' }
    $taskTarget = Join-Path $taskRuntime 'python'
    $taskProcess = Start-Process -FilePath $taskInstaller -ArgumentList @('/quiet','InstallAllUsers=0','Include_pip=1','Include_test=0','PrependPath=0',('TargetDir="' + $taskTarget + '"')) -WindowStyle Hidden -Wait -PassThru
    if ($taskProcess.ExitCode -notin @(0,3010)) { throw ('Python installer exit code ' + $taskProcess.ExitCode) }
    $taskPython = Join-Path $taskTarget 'python.exe'
}
$taskArgs = @('-X','utf8',(Join-Path $taskRoot 'install.py'))
if ($NoLaunch) { $taskArgs += '--no-launch' }
if ($Refresh) { $taskArgs += '--refresh' }
if ($PortableTools) { $taskArgs += '--portable-tools' }
& $taskPython @taskArgs
if ($LASTEXITCODE -ne 0) { throw ('Setup failed. See .runtime/install.log. Exit code ' + $LASTEXITCODE) }
