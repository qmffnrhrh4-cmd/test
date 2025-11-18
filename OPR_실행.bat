@echo off
chcp 65001 > nul
title OPR 자동 채점 시스템

echo ========================================
echo  OPR 자동 채점 시스템
echo ========================================
echo.
echo  모든 기능이 하나로 통합되었습니다!
echo  - 답안 자동 채점
echo  - 연습 문제 생성
echo  - 공부 노하우
echo  - 학습 계획
echo  - 체크리스트
echo.
echo  추가 설치 불필요! 바로 실행됩니다.
echo.
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"
python "OPR_시스템.py"

if errorlevel 1 (
    echo.
    echo ========================================
    echo  오류가 발생했습니다!
    echo ========================================
    echo.
    echo  Python이 설치되어 있는지 확인하세요.
    echo  https://www.python.org/downloads/
    echo.
    pause
)
