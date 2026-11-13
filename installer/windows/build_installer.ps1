# Builds dist\RiotOffice-Setup-<version>.exe
#
#   powershell -ExecutionPolicy Bypass -File installer\windows\build_installer.ps1
#
# Downloads (and checks the SHA-256 of) everything pinned in installer\versions.json:
# the LibreOffice MSI and help packs, a portable CPython with tkinter, the Carlito and Caladea
# fonts. Then stages Riot Office and compiles the setup with Inno Setup 6.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Invoke-WebRequest is very slow with the progress bar
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$build = Join-Path $root "build\windows"
$stage = Join-Path $build "stage"
$cache = Join-Path $root "build\cache"
$dist = Join-Path $root "dist"
$versions = Get-Content (Join-Path $root "installer\versions.json") -Raw | ConvertFrom-Json

$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
          "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 not found: winget install JRSoftware.InnoSetup" }

function Step($text) { Write-Host "`n== $text" -ForegroundColor Magenta }

function Get-Pinned($url, $sha256, $dest) {
    # Download once into the cache, always verify the hash.
    if (-not (Test-Path $dest)) {
        Write-Host "   downloading $(Split-Path $dest -Leaf)"
        Invoke-WebRequest -Uri $url -OutFile "$dest.part" -UseBasicParsing
        Move-Item "$dest.part" $dest
    }
    $hash = (Get-FileHash $dest -Algorithm SHA256).Hash.ToLower()
    if ($hash -ne $sha256) { Remove-Item $dest; throw "SHA-256 mismatch for $(Split-Path $dest -Leaf): $hash" }
}

function Copy-Utf8Bom($src, $dest) {
    # Inno Setup reads .iss and .txt files as UTF-8 only when they start with a BOM.
    $text = [IO.File]::ReadAllText($src, [Text.Encoding]::UTF8)
    [IO.File]::WriteAllText($dest, $text, (New-Object Text.UTF8Encoding $true))
}

$version = (Select-String -Path (Join-Path $root "riot_office\__init__.py") -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
$loVersion = $versions.libreoffice.version
Step "Riot Office $version with LibreOffice $loVersion"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $stage, $cache, $dist, "$stage\libreoffice", "$stage\fonts" | Out-Null

Step "LibreOffice MSI and help packs"
foreach ($file in $versions.libreoffice.files.PSObject.Properties) {
    $dest = Join-Path $cache $file.Name
    Get-Pinned "$($versions.libreoffice.base_url)/$($file.Name)" $file.Value $dest
    Copy-Item $dest "$stage\libreoffice"
}

Step "Fonts (Carlito, Caladea; SIL Open Font License)"
foreach ($family in $versions.fonts.PSObject.Properties) {
    foreach ($file in $family.Value.files.PSObject.Properties) {
        $name = if ($file.Name -eq "OFL.txt") { "OFL-$($family.Name).txt" } else { $file.Name }
        $dest = Join-Path $cache $name
        Get-Pinned "$($family.Value.base_url)/$($file.Name)" $file.Value $dest
        Copy-Item $dest "$stage\fonts\$name"
    }
}

Step "Portable Python (python-build-standalone, with tkinter)"
$tgz = Join-Path $cache "python-runtime.tar.gz"
Get-Pinned $versions.python.url $versions.python.sha256 $tgz
tar -xzf $tgz -C $stage
if ($LASTEXITCODE) { throw "could not extract the Python runtime" }
Rename-Item (Join-Path $stage "python") "runtime"
& "$stage\runtime\python.exe" -m pip install --quiet --no-warn-script-location @($versions.python.packages)
if ($LASTEXITCODE) { throw "pip install failed" }
# A ._pth file fixes sys.path and isolates the runtime from any other Python on the PC;
# ".." (the install folder) makes the riot_office package importable.
[IO.File]::WriteAllText("$stage\runtime\python312._pth", "python312.zip`r`nDLLs`r`nLib`r`nLib\site-packages`r`n..`r`n")

Step "Riot Office: program, configuration, artwork, documentation"
New-Item -ItemType Directory -Force "$stage\riot_office", "$stage\config", "$stage\assets", "$stage\docs" | Out-Null
Copy-Item "$root\riot_office\*.py" "$stage\riot_office"
Copy-Item "$root\config\riot-office*.xcd" "$stage\config"
Copy-Item "$root\assets\icon.ico", "$root\assets\icon.png", "$root\assets\wizard_side.bmp", "$root\assets\wizard_small.bmp" "$stage\assets"
Copy-Item "$root\docs\Guide.html" "$stage\docs"
Copy-Utf8Bom "$root\LICENSE.txt" "$stage\LICENSE.txt"
Copy-Utf8Bom "$root\installer\THIRD-PARTY-NOTICES.txt" "$stage\THIRD-PARTY-NOTICES.txt"

Step "Compiling the setup (Inno Setup)"
Copy-Utf8Bom "$PSScriptRoot\setup.iss" "$build\setup.iss"
& $iscc "/DAppVersion=$version" "/DLoVersion=$loVersion" "/DStage=$stage" "/O$dist" "$build\setup.iss"
if ($LASTEXITCODE) { throw "ISCC failed" }
$exe = Get-Item (Join-Path $dist "RiotOffice-Setup-$version.exe")
Write-Host ("`nReady: {0} ({1:N0} MB)" -f $exe.FullName, ($exe.Length / 1MB)) -ForegroundColor Cyan
