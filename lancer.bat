@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Premiere utilisation : installation des composants, quelques minutes...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 (
    echo Python 3.10 ou plus recent est requis : https://www.python.org/downloads/
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo Ouverture de l application dans le navigateur. Fermez cette fenetre pour arreter.
".venv\Scripts\python.exe" -m streamlit run app.py
