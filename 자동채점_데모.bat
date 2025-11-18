@echo off
chcp 65001 > nul
title 자동 채점 시스템 데모

echo ========================================
echo  자동 채점 시스템 데모
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"
python auto_grading_system.py

pause
