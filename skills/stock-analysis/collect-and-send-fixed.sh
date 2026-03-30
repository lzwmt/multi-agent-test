#!/bin/bash
# 收集并发送股票分析报告

set -euo pipefail

TEAM_NAME=${1:-}
SYMBOL=${2:-}

# 检查参数
if [ $# -lt 2 ] || [ -z "$TEAM_NAME" ] || [ -z "$SYMBOL" ]; then
    echo "Usage: collect-and-send.sh <团队名称> <股票代码>"
    echo "Example: collect-and-send.sh stock-002640-1234567890 002640"
    exit 1
fi

REPORT_DIR="/root/.openclaw/workspace/reports"
mkdir -p "$REPORT_DIR"

echo "📁 收集团队报告"
echo "========================================"
echo "团队名称: $TEAM_NAME"
echo "股票代码: $SYMBOL"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 收集所有生成的报告文件
echo "📊 扫描报告文件..."
echo "========================================"

# 报告文件列表
declare -a REPORT_FILES=()

# 1. 查找workspace中所有相关报告文件
echo "📁 检查 workspace 目录..."

# 使用 find 命令更可靠地查找文件
while IFS= read -r file; do
    if [ -f "$file" ]; then
        # 检查是否已在列表中
        found=0
        for existing in "${REPORT_FILES[@]}"; do
            if [ "$existing" = "$file" ]; then
                found=1
                break
            fi
        done
        
        if [ $found -eq 0 ]; then
            REPORT_FILES+=("$file")
            echo "   ✅ $(basename "$file")"
        fi
    fi
done < <(find /root/.openclaw/workspace -maxdepth 1 -type f -name "*${SYMBOL}*.md" 2>/dev/null | sort -u)

# 2. 查找以股票代码命名的报告
for pattern in "stock_analysis_${SYMBOL}_" "${SYMBOL}_analysis_" "${SYMBOL}_report_"; do
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            found=0
            for existing in "${REPORT_FILES[@]}"; do
                if [ "$existing" = "$file" ]; then
                    found=1
                    break
                fi
            done
            
            if [ $found -eq 0 ]; then
                REPORT_FILES+=("$file")
                echo "   ✅ $(basename "$file")"
            fi
        fi
    done < <(find /root/.openclaw/workspace -maxdepth 1 -type f -name "${pattern}*.md" 2>/dev/null)
done

# 3. 生成团队综合报告
echo ""
echo "📝 生成团队综合报告..."

TEAM_REPORT="$REPORT_DIR/${TEAM_NAME}_team_summary.md"

cat > "$TEAM_REPORT" << EOF
# 股票 ${SYMBOL} 团队分析报告汇总

**团队名称:** ${TEAM_NAME}  
**股票代码:** ${SYMBOL}  
**生成时间:** $(date '+%Y-%m-%d %H:%M:%S')  
**分析状态:** 已完成

---

## 团队成员

1. **portfolio-manager** (队长) - 协调分析并做出最终投资决策
2. **buffett-analyst** - 价值投资分析（巴菲特风格）
3. **growth-analyst** - 增长/颠覆性分析
4. **technical-analyst** - 技术指标分析
5. **fundamentals-analyst** - 基本面和财务指标分析
6. **sentiment-analyst** - 新闻和内部人情绪分析
7. **risk-manager** - 整合信号并评估投资组合风险

---

## 收集的报告文件

EOF

# 添加所有找到的报告文件
if [ ${#REPORT_FILES[@]} -eq 0 ]; then
    echo "⚠️ 未找到单独的报告文件" >> "$TEAM_REPORT"
    echo "   注意: 子代理可能未生成独立报告文件" >> "$TEAM_REPORT"
else
    for file in "${REPORT_FILES[@]}"; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            echo "- ${filename}" >> "$TEAM_REPORT"
        fi
    done
fi

echo "" >> "$TEAM_REPORT"
echo "---" >> "$TEAM_REPORT"
echo "" >> "$TEAM_REPORT"
echo "## 团队看板最终状态" >> "$TEAM_REPORT"
echo "" >> "$TEAM_REPORT"
echo '```' >> "$TEAM_REPORT"
clawteam board show "$TEAM_NAME" 2>&1 >> "$TEAM_REPORT" || echo "无法获取看板状态" >> "$TEAM_REPORT"
echo '```' >> "$TEAM_REPORT"

REPORT_FILES+=("$TEAM_REPORT")

echo ""
echo "📋 报告收集完成"
echo "========================================"
echo "共找到 ${#REPORT_FILES[@]} 个报告文件:"
for file in "${REPORT_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" 2>/dev/null | cut -f1)
        echo "   📄 $(basename "$file") ($size)"
    fi
done

echo ""
echo "✅ 报告收集完成！"
echo "📁 报告目录: $REPORT_DIR"
echo ""
echo "💡 手动发送命令:"
echo "   for f in ${REPORT_FILES[*]}; do message send --target 1478597566236201083 --file \"\$f\"; done"
