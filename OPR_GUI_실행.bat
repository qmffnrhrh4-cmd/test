@echo off
chcp 65001 > nul
title OPR 자동 채점 시스템 GUI

echo ========================================
echo  OPR 자동 채점 시스템 GUI 실행
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"
python opr_gui.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo  오류가 발생했습니다!
    echo ========================================
    pause
)
