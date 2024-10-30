@echo off
echo Starting MindPilot...
cd %~dp0
mindpilot.exe
echo.
echo Program exited with code %errorlevel%
pause