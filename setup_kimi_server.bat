@echo off
chcp 65001 >nul
title KIMI GEO Server Setup

cd /d "%~dp0"

echo ============================================================
echo KIMI GEO Collector - Server Setup
echo ============================================================
echo.
echo [PROJECT] %CD%
echo.

REM ============================================================
REM 1. 查找 Python 3.11
REM ============================================================

set "PYTHON_CMD="

py -3.11 -c "import sys; exit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.11"
)

if not defined PYTHON_CMD (
    python -c "import sys; exit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1

    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo [ERROR] 未找到 Python 3.11
    echo.
    echo 请先安装 Python 3.11。
    echo 安装时建议勾选：
    echo Add Python to PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Python
%PYTHON_CMD% --version
echo.

REM ============================================================
REM 2. 检查 requirements.txt
REM ============================================================

if not exist "requirements.txt" (
    echo [ERROR] 未找到 requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] requirements.txt
echo.

REM ============================================================
REM 3. 创建虚拟环境
REM ============================================================

if exist ".venv\Scripts\python.exe" (
    echo [OK] .venv 已存在
) else (
    echo [INFO] 正在创建 .venv...
    echo.

    %PYTHON_CMD% -m venv .venv

    if errorlevel 1 (
        echo.
        echo [ERROR] 创建 .venv 失败
        echo.
        pause
        exit /b 1
    )

    echo [OK] .venv 创建完成
)

echo.

REM ============================================================
REM 4. 升级 pip
REM ============================================================

echo [INFO] 正在升级 pip...
echo.

".venv\Scripts\python.exe" -m pip install --upgrade pip

if errorlevel 1 (
    echo.
    echo [ERROR] pip 升级失败
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] pip
echo.

REM ============================================================
REM 5. 安装 Python 依赖
REM ============================================================

echo [INFO] 正在安装项目依赖...
echo.

".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] requirements.txt 安装失败
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Python Dependencies
echo.

REM ============================================================
REM 6. 验证 Playwright
REM ============================================================

".venv\Scripts\python.exe" -c "from playwright.sync_api import sync_playwright; print('[OK] Playwright import PASS')"

if errorlevel 1 (
    echo.
    echo [ERROR] Playwright 导入失败
    echo.
    pause
    exit /b 1
)

echo.

REM ============================================================
REM 7. Python 编译检查
REM ============================================================

echo [INFO] 运行 compileall...
echo.

".venv\Scripts\python.exe" -m compileall .\app .\scripts

if errorlevel 1 (
    echo.
    echo [ERROR] Python 编译检查失败
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Compile Check
echo.

REM ============================================================
REM 8. 自动化测试
REM ============================================================

echo [INFO] 运行自动化测试...
echo.

".venv\Scripts\python.exe" -m pytest -v

if errorlevel 1 (
    echo.
    echo [ERROR] 自动化测试失败
    echo.
    echo 请先处理测试问题，再进行正式采集。
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Automated Tests
echo.

REM ============================================================
REM 9. 自动查找 Google Chrome
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
    echo [WARNING] 未检测到 Google Chrome
    echo.
    echo Python 环境已经部署完成，
    echo 但正式运行 KIMI 前必须安装 Google Chrome。
    echo.
) else (
    echo [OK] Google Chrome
    echo %CHROME_EXE%
    echo.
)

REM ============================================================
REM 10. 完成
REM ============================================================

echo ============================================================
echo KIMI GEO Server Setup Finished
echo ============================================================
echo.
echo [OK] 项目环境准备完成
echo.
echo 日常正式运行：
echo.
echo     双击 start_kimi.bat
echo.
echo 第一次运行会创建：
echo.
echo     %CD%\.chrome-profile
echo.
echo 并等待你人工登录 KIMI。
echo.
echo 后续登录状态会自动复用。
echo.
echo 注意：
echo 本项目通过 CDP 连接 Google Chrome，
echo 不需要执行 playwright install chromium。
echo.
echo ============================================================
echo.

pause