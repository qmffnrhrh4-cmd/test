@echo off
chcp 65001 > nul
title 문제 생성기 데모

echo ========================================
echo  문제 생성기 데모
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"
python exam_generator.py

pause
