@echo off
cd /d "%~dp0"

:: Ollama starten falls nicht aktiv
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if errorlevel 1 (
    echo Starte Ollama...
    start /min "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >NUL
)

"%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app.py
pause
