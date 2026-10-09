@echo off
rem Lance un petit serveur local (le micro exige localhost ou HTTPS) et ouvre le POC
cd /d "%~dp0"
start "" http://localhost:8000/
python -m http.server 8000
