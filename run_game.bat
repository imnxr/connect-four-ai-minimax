@echo off
title Connect Four AI

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not added to PATH.
    echo Please install Python first, then run this file again.
    pause
    exit /b 1
)

python -m pip show pygame-ce >nul 2>&1
if errorlevel 1 (
    echo pygame-ce was not found. Installing it now...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Failed to install required packages.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
)

python connect_four.py

if errorlevel 1 (
    echo.
    echo The game closed with an error.
    pause
    exit /b 1
)

pause
