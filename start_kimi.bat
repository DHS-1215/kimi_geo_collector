@echo off
chcp 65001 >nul
title KIMI GEO Collection Pipeline

cd /d "%~dp0"

echo ============================================================
echo KIMI GEO Collection Pipeline
echo ============================================================
echo.

REM ============================================================
REM 1. 检查项目虚拟环境
REM ============================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 未找到项目虚拟环境：
    echo %CD%\.venv
    echo.
    pause
    exit /b 1
)

echo [OK] Virtual Environment
echo.

REM ============================================================
REM 2. 正式运行模式
REM ============================================================

REM 清除测试题目限制，防止误跑测试模式
set KIMI_QUESTION_LIMIT=

REM Python UTF-8
set PYTHONUTF8=1

echo [MODE] Production
echo.

REM ============================================================
REM 3. 自动查找 Google Chrome
REM ============================================================

set "CHROME_EXE="

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME_EXE (
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_EXE (
    if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_EXE (
    echo [ERROR] 未找到 Google Chrome
    echo.
    echo 请先在当前服务器安装 Google Chrome。
    echo.
    pause
    exit /b 1
)

echo [OK] Chrome:
echo %CHROME_EXE%
echo.

REM ============================================================
REM 4. 项目内部 KIMI 独立浏览器 Profile
REM ============================================================

set "KIMI_PROFILE=%~dp0.chrome-profile"

set "FIRST_RUN=0"

if not exist "%KIMI_PROFILE%" (
    set "FIRST_RUN=1"
)

echo [PROFILE] %KIMI_PROFILE%
echo.

REM ============================================================
REM 5. 检查 KIMI Chrome CDP 9224
REM ============================================================

powershell -NoProfile -Command ^
    "try { Invoke-RestMethod 'http://127.0.0.1:9224/json/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"

if errorlevel 1 (
    echo [INFO] KIMI Chrome 未启动
    echo [INFO] 正在启动 Chrome CDP :9224...
    echo.

    start "" "%CHROME_EXE%" ^
        --remote-debugging-port=9224 ^
        --user-data-dir="%KIMI_PROFILE%" ^
        "https://www.kimi.com/"

    echo [INFO] 等待 Chrome CDP 就绪...
    echo.

    powershell -NoProfile -Command ^
        "$ok=$false; for($i=0;$i -lt 30;$i++){ try { Invoke-RestMethod 'http://127.0.0.1:9224/json/version' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){ exit 0 } else { exit 1 }"

    if errorlevel 1 (
        echo.
        echo [ERROR] Chrome CDP :9224 启动失败
        echo.
        echo 请检查：
        echo 1. Chrome 是否正常安装
        echo 2. 9224 端口是否被其他程序占用
        echo 3. 当前用户是否有权限启动 Chrome
        echo.
        pause
        exit /b 1
    )

        echo [OK] KIMI Chrome CDP :9224 Ready

) else (
    echo [OK] KIMI Chrome CDP :9224 Running
)

REM ============================================================
REM 6. 首次运行时等待人工登录 KIMI
REM ============================================================

if "%FIRST_RUN%"=="1" (
    echo.
    echo ============================================================
    echo KIMI 首次登录
    echo ============================================================
    echo.
    echo 已为当前项目创建独立 Chrome Profile。
    echo.
    echo 请在 Chrome 中：
    echo.
    echo 1. 打开 KIMI
    echo 2. 完成人工登录
    echo 3. 确认已经进入正常聊天页面
    echo.
    echo 完成后回到此窗口。
    echo.
    pause
)
    echo [OK] KIMI Chrome CDP :9224 Running
)

echo.

REM ============================================================
REM 7. 启动 KIMI GEO 正式 Pipeline
REM ============================================================

echo ============================================================
echo Starting KIMI GEO Pipeline
echo ============================================================
echo.

".venv\Scripts\python.exe" -m scripts.run_kimi_pipeline

set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================

if "%EXIT_CODE%"=="0" (
    echo KIMI GEO Pipeline 已结束
) else (
    echo KIMI GEO Pipeline 异常退出
    echo Exit Code: %EXIT_CODE%
)

echo ============================================================
echo.
pause

exit /b %EXIT_CODE%