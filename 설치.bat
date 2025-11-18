@echo off
chcp 65001 > nul
title OPR 시스템 - 필수 패키지 설치

echo ========================================
echo  OPR 시스템 - 필수 패키지 설치
echo ========================================
echo.
echo  AI 기능을 사용하기 위해 필수 패키지를 설치합니다.
echo.

cd /d "C:\Users\USER\Desktop\test"

echo [1/3] Python 버전 확인...
python --version
if errorlevel 1 (
    echo.
    echo ❌ Python이 설치되어 있지 않습니다!
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
echo.

echo [2/3] pip 업그레이드...
python -m pip install --upgrade pip
echo.

echo [3/3] 필수 패키지 설치...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ========================================
    echo  설치 중 오류가 발생했습니다!
    echo ========================================
    echo.
    echo  다음 명령을 직접 실행해보세요:
    echo  python -m pip install google-generativeai PyPDF2 python-docx
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  ✅ 설치 완료!
echo ========================================
echo.
echo  이제 OPR_실행.bat을 실행하세요.
echo.
pause
