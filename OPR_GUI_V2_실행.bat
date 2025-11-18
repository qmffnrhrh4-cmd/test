@echo off
chcp 65001 > nul
title OPR 자동 채점 시스템 V2 (AI 기반)

echo ========================================
echo  OPR 자동 채점 시스템 V2 (AI 기반)
echo ========================================
echo.
echo  Claude API를 사용한 정확한 채점!
echo.

cd /d "C:\Users\USER\Desktop\test"

:: Python 패키지 확인
echo 필요한 패키지를 확인하는 중...
python -c "import anthropic, PyPDF2" 2>nul
if errorlevel 1 (
    echo.
    echo 필요한 패키지를 설치합니다...
    pip install -r requirements.txt
    echo.
)

:: API 키 확인
python -c "import os; exit(0 if os.getenv('ANTHROPIC_API_KEY') else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo ========================================
    echo  경고: Claude API 키가 설정되지 않았습니다!
    echo ========================================
    echo.
    echo V2의 모든 기능을 사용하려면 API 키가 필요합니다.
    echo.
    echo API 키 설정 방법:
    echo 1. https://console.anthropic.com/ 에서 API 키 발급
    echo 2. 시스템 환경변수 ANTHROPIC_API_KEY 설정
    echo 3. 또는 프로그램 내에서 '⚙️ API 키 설정' 메뉴 사용
    echo.
    echo API 키 없이도 기본 기능은 사용 가능합니다.
    echo.
    pause
)

echo.
echo V2 GUI를 실행합니다...
python opr_gui_v2.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo  오류가 발생했습니다!
    echo ========================================
    pause
)
