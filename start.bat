@echo off
REM Käynnistää Discord-botin ja web-dashboardin (Windows)
REM Käyttö: Kaksoisklikkaa start.bat tai: start.bat

cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel% equ 0 (
    python run.py
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        python3 run.py
    ) else (
        echo Virhe: Python ei löydy. Asenna Python 3.8+ ja varmista että se on PATHissa.
        pause
        exit /b 1
    )
)
