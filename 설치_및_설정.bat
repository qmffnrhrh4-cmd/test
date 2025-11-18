@echo off
chcp 65001 > nul
title OPR 시스템 설치 및 설정

echo ========================================
echo  OPR 자동 채점 시스템 설치 및 설정
echo ========================================
echo.

cd /d "C:\Users\USER\Desktop\test"

echo [1/3] Python 버전 확인...
python --version
if errorlevel 1 (
    echo.
    echo ❌ Python이 설치되어 있지 않습니다!
    echo Python 3.8 이상을 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python 확인 완료
echo.

echo [2/3] 필요한 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ❌ 패키지 설치 실패!
    pause
    exit /b 1
)
echo ✅ 패키지 설치 완료
echo.

echo [3/3] API 키 설정 확인...
python -c "import os; exit(0 if os.getenv('ANTHROPIC_API_KEY') else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo ⚠️ Claude API 키가 설정되지 않았습니다.
    echo.
    echo API 키를 설정하시겠습니까? (Y/N)
    set /p setup_api="입력: "

    if /i "%setup_api%"=="Y" (
        echo.
        echo API 키 발급 방법:
        echo 1. https://console.anthropic.com/ 접속
        echo 2. 로그인 또는 회원가입
        echo 3. API Keys 메뉴에서 새 키 생성
        echo.
        echo API 키를 발급받으셨으면 아래에 입력하세요:
        set /p api_key="API 키: "

        if not "!api_key!"=="" (
            setx ANTHROPIC_API_KEY "!api_key!"
            echo.
            echo ✅ API 키가 저장되었습니다!
            echo 시스템을 다시 시작하거나 새 명령 프롬프트를 열어주세요.
        ) else (
            echo.
            echo ⚠️ API 키가 입력되지 않았습니다.
            echo 나중에 '⚙️ API 키 설정' 메뉴에서 설정할 수 있습니다.
        )
    ) else (
        echo.
        echo ℹ️ API 키 없이도 기본 기능은 사용 가능합니다.
        echo 나중에 '⚙️ API 키 설정' 메뉴에서 설정할 수 있습니다.
    )
) else (
    echo ✅ API 키가 설정되어 있습니다!
)

echo.
echo ========================================
echo  설치 및 설정이 완료되었습니다!
echo ========================================
echo.
echo 이제 다음 파일을 실행하세요:
echo  - OPR_GUI_V2_실행.bat (AI 기반 V2, 추천!)
echo  - OPR_GUI_실행.bat (기본 V1)
echo  - 통합실행메뉴.bat (모든 기능)
echo.
pause
