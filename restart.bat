@echo off
REM Force kill the process with the specified window title
taskkill /F /FI "WINDOWTITLE eq discordbot"

REM Perform a Git pull to update the codebase
git pull

REM Start the Python script with the specified window title
start "discordbot" python main.py
