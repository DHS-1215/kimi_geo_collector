@echo off
chcp 65001 >nul
title KIMI GEO Collection Pipeline

cd /d "%~dp0"

echo ============================================================
echo KIMI GEO Collection Pipeline
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 1. 检查虚拟环境
REM ------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 未找到虚拟环境：
    echo %CD%\.venv
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM 2. 正式运行时清除测试题目限制
REM ------------------------------------------------------------
set KIMI_QUESTION_LIMIT=

echo [OK] Python virtual environment
echo [MODE] Production
echo.

REM ------------------------------------------------------------
REM 3. 检查 KIMI Chrome CDP 9224
REM ------------------------------------------------------------
powershell -NoProfile -Command ^
    "try { Invoke-RestMethod 'http://127.0.0.1:9224/json/version' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"

if %errorlevel%==0 (
    echo [OK] KIMI Chrome CDP :9224 already running
) else (
    echo [INFO] KIMI Chrome 未启动，正在启动...

    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
        --remote-debugging-port=9224 ^
        --user-data-dir="D:\kimi_profiles\profile_002" ^
        "https://www.kimi.com/"

    echo [INFO] 等待 Chrome CDP 就绪...

    powershell -NoProfile -Command ^
        "$ok=$false; for($i=0;$i -lt 20;$i++){ try { Invoke-RestMethod 'http://127.0.0.1:9224/json/version' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if(-not $ok){ exit 1 }"

    if errorlevel 1 (
        echo.
        echo [ERROR] Chrome CDP :9224 启动失败
        echo 请检查 Chrome 路径或 KIMI Profile。
        echo.
        pause
        exit /b 1
    )

    echo [OK] KIMI Chrome CDP :9224 ready
)

echo.
echo ============================================================
echo Starting Pipeline
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 4. 启动正式采集
REM ------------------------------------------------------------
".venv\Scripts\python.exe" -m scripts.run_kimi_pipeline

set EXIT_CODE=%errorlevel%

echo.
echo ============================================================

if "%EXIT_CODE%"=="0" (
    echo Pipeline 已结束
) else (
    echo Pipeline 异常退出，Exit Code: %EXIT_CODE%
)

echo ============================================================
echo.
pause