$ErrorActionPreference = "Stop"

$Python = ".\.venv\Scripts\python.exe"
$Coverage = ".\.venv\Scripts\coverage.exe"
$Flake8 = ".\.venv\Scripts\flake8.exe"
$Radon = ".\.venv\Scripts\radon.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
    $Coverage = "coverage"
    $Flake8 = "flake8"
    $Radon = "radon"
}

Write-Host "=== 1/4 Ejecutando suite de pruebas ==="
& $Python manage.py test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== 2/4 Ejecutando cobertura (meta 100%) ==="
& $Coverage run manage.py test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Coverage report -m --fail-under=100
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Coverage html
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== 3/4 Ejecutando revision PEP 8 con flake8 ==="
& $Flake8 . --exclude=.venv,migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== 4/4 Ejecutando analisis de complejidad ciclomatica con radon ==="
$radonOutput = & $Radon cc . -s -a
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$radonOutput | Write-Host

$bloquesComplejos = & $Radon cc . -n C -s
if ($bloquesComplejos) {
    Write-Error "Se detectaron bloques con complejidad ciclomatica > 10:`n$bloquesComplejos"
    exit 1
}

Write-Host "=== Todas las verificaciones finalizaron exitosamente ==="
exit 0
