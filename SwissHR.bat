@echo off
REM ==============================================================
REM  Swiss HR Local AI Toolbox - lanceur Windows
REM  Double-cliquez sur ce fichier pour lancer l'application.
REM ==============================================================

cd /d "%~dp0"

REM Choix de l'interpréteur Python : on prend l'exécutable virtuel
REM si un venv est present, sinon le python systeme.
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

"%PY%" run.py
if errorlevel 1 (
    echo.
    echo [!] Une erreur est survenue au lancement.
    echo     Consultez le dossier Logs\ pour plus de details.
    pause
)
