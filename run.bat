@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Kiem tra pygame...
py -c "import pygame" 2>nul
if errorlevel 1 (
    echo Cai dat pygame...
    py -m pip install pygame --quiet
)
echo Khoi dong MU Online Offline...
py main.py
pause
