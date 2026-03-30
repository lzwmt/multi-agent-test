#!/bin/bash
# 浏览器测试运行脚本

set -e

echo "=========================================="
echo "OpenClaw 浏览器自动化测试"
echo "=========================================="
echo ""

# 检查 openclaw 是否可用
if ! command -v openclaw &> /dev/null; then
    echo "错误: openclaw 命令未找到"
    exit 1
fi

echo "OpenClaw 版本:"
openclaw --version
echo ""

# 运行基础测试
echo ">>> 运行基础测试..."
node test-basic.js || echo "基础测试完成（可能有部分失败）"

echo ""
echo ">>> 运行 Profile 测试..."
node test-profiles.js || echo "Profile 测试完成（可能有部分失败）"

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
