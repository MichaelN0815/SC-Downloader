@echo off
title Scalable Capital PDF Downloader 
color 0B

echo ==================================================
echo   Scalable Capital PDF Downloader - Poweruser
echo ==================================================
echo.

:: Prüfe ob eine virtuelle Umgebung vorhanden ist
if exist venv\Scripts\activate (
    echo [INFO] Virtuelle Umgebung gefunden. Aktiviere...
    call venv\Scripts\activate
) else (
    echo [INFO] Nutze globales Python.
)

echo [START] Starte Skript ...
echo.

:: Führe das Skript aus
python downloader.py

echo.
echo ==================================================
echo   Vorgang abgeschlossen.
echo ==================================================
pause