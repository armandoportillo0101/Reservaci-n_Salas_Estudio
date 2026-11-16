#!/usr/bin/env bash
set -euo pipefail

if [ -x ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
    COVERAGE=".venv/Scripts/coverage.exe"
    FLAKE8=".venv/Scripts/flake8.exe"
    RADON=".venv/Scripts/radon.exe"
elif [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    COVERAGE=".venv/bin/coverage"
    FLAKE8=".venv/bin/flake8"
    RADON=".venv/bin/radon"
else
    PYTHON="python"
    COVERAGE="coverage"
    FLAKE8="flake8"
    RADON="radon"
fi

echo "=== 1/4 Ejecutando suite de pruebas ==="
"$PYTHON" manage.py test

echo "=== 2/4 Ejecutando cobertura (meta 100%) ==="
"$COVERAGE" run manage.py test
"$COVERAGE" report -m --fail-under=100
"$COVERAGE" html

echo "=== 3/4 Ejecutando revision PEP 8 con flake8 ==="
"$FLAKE8" . --exclude=.venv,migrations

echo "=== 4/4 Ejecutando analisis de complejidad ciclomatica con radon ==="
"$RADON" cc . -s -a
COMPLEX_BLOCKS=$("$RADON" cc . -n C -s)
if [ -n "$COMPLEX_BLOCKS" ]; then
    echo "Error: existen bloques con complejidad > 10:"
    echo "$COMPLEX_BLOCKS"
    exit 1
fi

echo "=== Todas las verificaciones finalizaron exitosamente ==="
