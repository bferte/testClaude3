@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo Glisser-deposer le fichier Excel des URL sur ce fichier.
  pause
  exit /b 1
)
python -c "import playwright, pandas, openpyxl, tqdm" 2>nul || (
  echo Installation des dependances...
  python -m pip install -r requirements.txt || goto :erreur
  python -m playwright install chromium || goto :erreur
)
python verifier_doctolib.py "%~1" %2 %3 %4 %5 %6 %7 %8 %9
pause
exit /b 0
:erreur
echo Echec de l'installation.
pause
exit /b 1
