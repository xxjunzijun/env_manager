@echo off
REM build.bat - Windows 构建脚本
REM 双击运行或从命令行执行

echo =========================================
echo env_manager 构建脚本 (Windows)
echo =========================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未安装 Python
    echo 请从 https://python.org 下载安装 Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
echo.
echo [1/3] 安装依赖...
pip install -r requirements.txt

REM 构建
echo.
echo [2/3] 构建 Windows 应用...
flet build windows

echo.
echo =========================================
echo 构建完成！
echo 输出目录: dist\
echo =========================================
pause
