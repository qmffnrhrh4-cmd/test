@echo off
chcp 65001 > nul
title OPR 자동 채점 시스템 - AI 버전

echo ========================================
echo  OPR 자동 채점 시스템 - AI 버전
echo ========================================
echo.
echo  Gemini AI 기반 스마트 채점!
echo  - PDF/HWP/TXT 파일 첨부 가능
echo  - 상세한 피드백 (잘한점/부족한점/보완방법)
echo  - 실전 문제 생성
echo  - 공부 노하우
echo.
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"

:: 패키지 확인
python -c "import google.generativeai" 2>nul
if errorlevel 1 (
    echo ⚠️  Gemini API 패키지가 설치되지 않았습니다.
    echo.
    echo 설치하시겠습니까? ^(Y/N^)
    set /p install="입력: "

    if /i "%install%"=="Y" (
        echo.
        echo 설치 중...
        python -m pip install google-generativeai PyPDF2
        echo.
    )
)

python "OPR_시스템_AI.py"

if errorlevel 1 (
    echo.
    echo ========================================
    echo  오류가 발생했습니다!
    echo ========================================
    echo.
    pause
)
