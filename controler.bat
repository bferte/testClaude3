@echo off
chcp 65001 >nul
REM Glisser-deposer : 1er fichier = catalogue a controler, 2e fichier (optionnel) = version precedente
set "DOSSIER=%~dp0"
if "%~1"=="" (
  echo Glissez un fichier CSV sur ce script pour le controler.
  pause
  exit /b 1
)
if not exist "%DOSSIER%.venv\Scripts\python.exe" (
  echo Lancez d abord lancer.bat une fois pour installer l outil.
  pause
  exit /b 1
)
set "PREC="
if not "%~2"=="" set PREC=--precedent "%~2"
pushd "%DOSSIER%"
".venv\Scripts\python.exe" -m catalogue_qc.cli "%~1" %PREC% --html "%~dpn1_controle.html" --excel "%~dpn1_controle.xlsx"
popd
start "" "%~dpn1_controle.html"
pause
