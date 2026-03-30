#!/bin/bash
# 代码审查脚本 - 自动检查代码质量和逻辑

set -euo pipefail

SCRIPT_PATH="${1:-}"
SCRIPT_NAME=$(basename "$SCRIPT_PATH" 2>/dev/null || echo "unknown")
REVIEW_DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 检查参数
if [ -z "$SCRIPT_PATH" ]; then
    echo "Usage: review.sh <脚本路径>"
    echo "Example: review.sh ../stock-analysis/run.sh"
    exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 错误: 文件不存在: $SCRIPT_PATH"
    exit 1
fi

echo "========================================"
echo "🔍 代码审查开始"
echo "========================================"
echo "文件: $SCRIPT_PATH"
echo "时间: $REVIEW_DATE"
echo ""

# 统计信息
TOTAL_LINES=$(wc -l < "$SCRIPT_PATH")
echo "📊 文件统计:"
echo "   总行数: $TOTAL_LINES"
echo ""

# 检查文件类型
FILE_EXT="${SCRIPT_NAME##*.}"
echo "📁 文件类型: $FILE_EXT"
echo ""

# 初始化问题计数
CRITICAL=0
WARNING=0
SUGGESTION=0

# ============ 检查1: 语法检查 ============
echo "✅ 检查1: 语法检查"

case "$FILE_EXT" in
    sh|bash)
        if bash -n "$SCRIPT_PATH" 2>/dev/null; then
            echo "   ✅ Bash 语法正确"
        else
            echo "   🔴 Bash 语法错误"
            CRITICAL=$((CRITICAL + 1))
        fi
        
        # 检查 shellcheck (如果可用)
        if command -v shellcheck &>/dev/null; then
            SHELLCHECK_OUTPUT=$(shellcheck "$SCRIPT_PATH" 2>/dev/null || true)
            if [ -n "$SHELLCHECK_OUTPUT" ]; then
                echo "   🟠 Shellcheck 警告:"
                echo "$SHELLCHECK_OUTPUT" | head -5 | sed 's/^/      /'
                WARNING=$((WARNING + 1))
            else
                echo "   ✅ Shellcheck 通过"
            fi
        fi
        ;;
    py|python)
        if python3 -m py_compile "$SCRIPT_PATH" 2>/dev/null; then
            echo "   ✅ Python 语法正确"
        else
            echo "   🔴 Python 语法错误"
            CRITICAL=$((CRITICAL + 1))
        fi
        ;;
    js|json)
        if node --check "$SCRIPT_PATH" 2>/dev/null; then
            echo "   ✅ JavaScript 语法正确"
        else
            echo "   🔴 JavaScript 语法错误"
            CRITICAL=$((CRITICAL + 1))
        fi
        ;;
    *)
        echo "   🟡 未知文件类型，跳过语法检查"
        ;;
esac
echo ""

# ============ 检查2: 错误处理 ============
echo "✅ 检查2: 错误处理"

if grep -q "set -e" "$SCRIPT_PATH" || grep -q "set -o errexit" "$SCRIPT_PATH"; then
    echo "   ✅ 已启用 errexit 模式"
else
    echo "   🟠 建议添加 'set -e' 启用严格错误处理"
    SUGGESTION=$((SUGGESTION + 1))
fi

if grep -q "set -u" "$SCRIPT_PATH" || grep -q "set -o nounset" "$SCRIPT_PATH"; then
    echo "   ✅ 已启用 nounset 模式"
else
    echo "   🟠 建议添加 'set -u' 检查未定义变量"
    SUGGESTION=$((SUGGESTION + 1))
fi

if grep -q "set -o pipefail" "$SCRIPT_PATH"; then
    echo "   ✅ 已启用 pipefail 模式"
else
    echo "   🟠 建议添加 'set -o pipefail' 处理管道错误"
    SUGGESTION=$((SUGGESTION + 1))
fi
echo ""

# ============ 检查3: 变量使用 ============
echo "✅ 检查3: 变量使用"

# 检查未引用的变量 (简单检查)
UNQUOTED_VARS=$(grep -n '\$[A-Za-z_][A-Za-z0-9_]*' "$SCRIPT_PATH" | grep -v '"' | grep -v "'" | head -5)
if [ -n "$UNQUOTED_VARS" ]; then
    echo "   🟠 发现未引用的变量 (可能导致空格问题):"
    echo "$UNQUOTED_VARS" | sed 's/^/      /'
    WARNING=$((WARNING + 1))
else
    echo "   ✅ 变量引用规范"
fi

# 检查未定义的变量 (简单模式匹配)
UNDEFINED=$(grep -o '\${[A-Za-z_][A-Za-z0-9_]*:-' "$SCRIPT_PATH" | sed 's/\${\(.*\):-/\1/' | sort -u)
if [ -n "$UNDEFINED" ]; then
    echo "   ✅ 发现默认值设置 (良好实践):"
    echo "$UNDEFINED" | sed 's/^/      /'
fi
echo ""

# ============ 检查4: 安全漏洞 ============
echo "✅ 检查4: 安全漏洞"

# 检查命令注入风险
if grep -q 'eval\s' "$SCRIPT_PATH"; then
    echo "   🔴 发现 eval 使用，可能存在命令注入风险"
    CRITICAL=$((CRITICAL + 1))
fi

if grep -q 'exec\s' "$SCRIPT_PATH"; then
    echo "   🟠 发现 exec 使用，注意参数验证"
    WARNING=$((WARNING + 1))
fi

# 检查临时文件安全
if grep -q '/tmp/' "$SCRIPT_PATH" && ! grep -q 'mktemp' "$SCRIPT_PATH"; then
    echo "   🟠 使用 /tmp/ 路径但未使用 mktemp，可能存在竞态条件"
    WARNING=$((WARNING + 1))
fi

if [ $CRITICAL -eq 0 ] && [ $WARNING -eq 0 ]; then
    echo "   ✅ 未发现明显安全漏洞"
fi
echo ""

# ============ 检查5: 代码质量 ============
echo "✅ 检查5: 代码质量"

# 检查注释
COMMENT_LINES=$(grep -c '^\s*#' "$SCRIPT_PATH" || echo 0)
COMMENT_RATIO=$(awk "BEGIN {printf \"%.1f\", ($COMMENT_LINES/$TOTAL_LINES)*100}")
if [ "$COMMENT_RATIO" \< 5 ]; then
    echo "   🟠 注释比例较低 (${COMMENT_RATIO}%)，建议添加更多注释"
    SUGGESTION=$((SUGGESTION + 1))
else
    echo "   ✅ 注释比例良好 (${COMMENT_RATIO}%)"
fi

# 检查函数定义
FUNC_COUNT=$(grep -c '^[a-zA-Z_][a-zA-Z0-9_]*\s*()' "$SCRIPT_PATH" || echo 0)
if [ $FUNC_COUNT -gt 0 ]; then
    echo "   ✅ 发现 $FUNC_COUNT 个函数定义"
else
    echo "   🟡 未发现函数定义，建议模块化代码"
    SUGGESTION=$((SUGGESTION + 1))
fi

# 检查硬编码值
HARDCODED=$(grep -n 'http://\|https://\|/tmp/\|/root/\|/home/' "$SCRIPT_PATH" | grep -v '^\s*#' | head -3)
if [ -n "$HARDCODED" ]; then
    echo "   🟠 发现硬编码路径/URL:"
    echo "$HARDCODED" | sed 's/^/      /'
    SUGGESTION=$((SUGGESTION + 1))
fi
echo ""

# ============ 检查6: 可执行权限 ============
echo "✅ 检查6: 文件权限"

if [ -x "$SCRIPT_PATH" ]; then
    echo "   ✅ 文件具有可执行权限"
else
    echo "   🟠 文件缺少可执行权限，建议: chmod +x $SCRIPT_NAME"
    WARNING=$((WARNING + 1))
fi
echo ""

# ============ 生成报告 ============
echo "========================================"
echo "📊 审查报告摘要"
echo "========================================"

if [ $CRITICAL -gt 0 ]; then
    echo "🔴 严重问题: $CRITICAL 个"
fi
if [ $WARNING -gt 0 ]; then
    echo "🟠 警告: $WARNING 个"
fi
if [ $SUGGESTION -gt 0 ]; then
    echo "🟡 建议: $SUGGESTION 个"
fi

if [ $CRITICAL -eq 0 ] && [ $WARNING -eq 0 ] && [ $SUGGESTION -eq 0 ]; then
    echo "✅ 代码质量良好，未发现明显问题"
fi

echo ""

# 评分
SCORE=100
SCORE=$((SCORE - CRITICAL * 20 - WARNING * 10 - SUGGESTION * 5))
if [ $SCORE -lt 0 ]; then
    SCORE=0
fi

echo "📈 代码质量评分: $SCORE/100"

if [ $SCORE -ge 90 ]; then
    echo "   ✅ 优秀"
elif [ $SCORE -ge 70 ]; then
    echo "   🟡 良好"
elif [ $ge 50 ]; then
    echo "   🟠 一般"
else
    echo "   🔴 需要改进"
fi

echo ""
echo "💡 建议操作:"
if [ $CRITICAL -gt 0 ]; then
    echo "   - 优先修复严重问题"
fi
if [ $WARNING -gt 0 ]; then
    echo "   - 处理警告事项"
fi
if [ $SUGGESTION -gt 0 ]; then
    echo "   - 考虑采纳改进建议"
fi

echo ""
echo "✅ 审查完成"
echo "========================================"

# 保存审查记录
REVIEW_LOG="/root/.openclaw/workspace/.cache/code-reviews/${SCRIPT_NAME}-$(date +%s).log"
mkdir -p "$(dirname "$REVIEW_LOG")"
{
    echo "# 代码审查记录"
    echo "文件: $SCRIPT_PATH"
    echo "时间: $REVIEW_DATE"
    echo "评分: $SCORE/100"
    echo "严重: $CRITICAL, 警告: $WARNING, 建议: $SUGGESTION"
} > "$REVIEW_LOG"

exit 0
