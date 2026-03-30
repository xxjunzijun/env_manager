#!/bin/bash
# build.sh - 构建脚本
# 用于 Linux/macOS 构建，Windows 用户直接运行 flet build windows

set -e

echo "========================================="
echo "env_manager 构建脚本"
echo "========================================="

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 安装依赖
echo ""
echo "[1/3] 安装依赖..."
pip install -r requirements.txt

# 开发模式测试
echo ""
echo "[2/3] 测试运行 (按 Ctrl+C 退出)..."
timeout 5 python3 main.py || true

# 构建
echo ""
echo "[3/3] 构建 Windows 应用..."
flet build windows

echo ""
echo "========================================="
echo "构建完成！"
echo "输出目录: dist/"
echo "========================================="
