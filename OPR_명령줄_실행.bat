@echo off
chcp 65001 > nul
title OPR 자동 채점 시스템 (명령줄)

echo ========================================
echo  OPR 자동 채점 시스템 명령줄 버전
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"
python opr_system.py

pause
