@echo off
chcp 65001 > nul
title OPR 자동 채점 시스템 - 통합 메뉴

:MENU
cls
echo ========================================
echo  OPR 자동 채점 시스템
echo ========================================
echo.
echo  [V2 버전 - AI 기반]
echo  1. V2 GUI 실행 (Claude API, 추천!)
echo  2. 설치 및 설정
echo.
echo  [V1 버전 - 기본]
echo  3. V1 GUI 실행
echo  4. 명령줄 버전 실행
echo.
echo  [데모]
echo  5. 자동 채점 데모
echo  6. 문제 생성 데모
echo  7. 공부 가이드 데모
echo.
echo  0. 종료
echo.
echo ========================================

set /p choice="선택하세요 (0-7): "

if "%choice%"=="1" goto GUIV2
if "%choice%"=="2" goto SETUP
if "%choice%"=="3" goto GUIV1
if "%choice%"=="4" goto CMD
if "%choice%"=="5" goto GRADE
if "%choice%"=="6" goto EXAM
if "%choice%"=="7" goto GUIDE
if "%choice%"=="0" goto END

echo 잘못된 입력입니다.
timeout /t 2 > nul
goto MENU

:GUIV2
cls
echo V2 GUI 버전을 실행합니다 (AI 기반)...
cd /d "C:\Users\USER\Desktop\test"
python opr_gui_v2.py
goto MENU

:SETUP
cls
echo 설치 및 설정을 실행합니다...
cd /d "C:\Users\USER\Desktop\test"
call 설치_및_설정.bat
goto MENU

:GUIV1
cls
echo V1 GUI 버전을 실행합니다...
cd /d "C:\Users\USER\Desktop\test"
python opr_gui.py
goto MENU

:CMD
cls
echo 명령줄 버전을 실행합니다...
cd /d "C:\Users\USER\Desktop\test"
python opr_system.py
goto MENU

:GRADE
cls
echo 자동 채점 데모를 실행합니다...
cd /d "C:\Users\USER\Desktop\test"
python auto_grading_system.py
pause
goto MENU

:EXAM
cls
echo 문제 생성 데모를 실행합니다...
cd /d "C:\Users\USER\Desktop\test"
python exam_generator.py
pause
goto MENU

:GUIDE
cls
echo 공부 가이드 데모를 실행합니다...
cd /d "C:\Users\USER\Desktop\test"
python study_guide.py
pause
goto MENU

:END
echo 프로그램을 종료합니다.
timeout /t 1 > nul
exit
