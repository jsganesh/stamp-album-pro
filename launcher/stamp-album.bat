@echo off
REM StampAlbum Pro Launcher for Windows
REM Double-click this file to start the app.

cd /d "%~dp0.."
call venv\Scripts\activate.bat
python -m stamp_album.serve
pause
