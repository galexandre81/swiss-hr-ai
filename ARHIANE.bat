@echo off
REM ==============================================================
REM  ARHIANE - L'IA qui remet les RH au centre - lanceur Windows
REM  Double-cliquez sur ce fichier pour lancer l'application.
REM ==============================================================

cd /d "%~dp0"

REM Choix de l'interpreteur Python : on prend l'executable virtuel
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
