#!/bin/bash
# 收集并发送股票分析报告

TEAM_NAME=$1
SYMBOL=$2
CHANNEL_ID=$3

if [ -z "$TEAM_NAME" ] || [ -z "$SYMBOL" ]; then
    echo "Usage: collect-reports.sh <团队名称> <股票代码> [频道ID]"
    exit 1
fi

# 默认频道ID
if [ -z "$CHANNEL_ID" ]; then
    CHANNEL_ID="1478597566236201083"
fi

REPORT_DIR="/root/.openclaw/workspace/reports"
mkdir -p "$REPORT_DIR"

echo "📁 收集团队报告: $TEAM_NAME"
echo "========================================"

# 等待团队完成
echo "⏳ 等待分析完成..."
while true; do
    # 检查团队状态
    BOARD_OUTPUT=$(clawteam board show "$TEAM_NAME" 2>&1)
    
    # 检查是否全部完成
    COMPLETED_COUNT=$(echo "$BOARD_OUTPUT" | grep -c "COMPLETED")
    IN_PROGRESS=$(echo "$BOARD_OUTPUT" | grep "IN PROGRESS" | grep -v "(none)")
    
    if echo "$BOARD_OUTPUT" | grep -q "COMPLETED (7)" && [ -z "$IN_PROGRESS" ]; then
        echo "✅ 所有分析已完成！"
        break
    fi
    
    echo "   等待中...$(echo "$BOARD_OUTPUT" | grep "COMPLETED" | head -1)"
    sleep 10
done

# 获取团队工作目录
WORKSPACE=$(find /tmp -name "*stock*${SYMBOL}*" -type d 2>/dev/null | head -1)

echo ""
echo "📊 收集报告文件..."
echo "========================================"

# 收集所有生成的报告文件
REPORT_FILES=()

# 1. 检查工作目录中的报告
if [ -n "$WORKSPACE" ] && [ -d "$WORKSPACE" ]; then
    echo "📁 检查工作目录: $WORKSPACE"
    for file in "$WORKSPACE"/*.md "$WORKSPACE"/*.txt "$WORKSPACE"/*.json 2>/dev/null; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            cp "$file" "$REPORT_DIR/${TEAM_NAME}_${filename}"
            REPORT_FILES+=("$REPORT_DIR/${TEAM_NAME}_${filename}")
            echo "   ✅ 找到: $filename"
        fi
    done
fi

# 2. 检查workspace根目录中的相关报告
echo "📁 检查workspace目录..."
for file in /root/.openclaw/workspace/*${SYMBOL}*.md 2>/dev/null; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        # 如果文件不在reports目录，复制过去
        if [ ! -f "$REPORT_DIR/${filename}" ]; then
            cp "$file" "$REPORT_DIR/${filename}"
        fi
        REPORT_FILES+=("$REPORT_DIR/${filename}")
        echo "   ✅ 找到: $filename"
    fi
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

## 团队成员报告列表

EOF

# 添加所有找到的报告文件
for file in "${REPORT_FILES[@]}"; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "- ${filename}" >> "$TEAM_REPORT"
    fi
done

echo "" >> "$TEAM_REPORT"
echo "---" >> "$TEAM_REPORT"
echo "" >> "$TEAM_REPORT"
echo "## 团队看板最终状态" >> "$TEAM_REPORT"
echo "" >> "$TEAM_REPORT"
echo '```' >> "$TEAM_REPORT"
clawteam board show "$TEAM_NAME" 2>&1 >> "$TEAM_REPORT"
echo '```' >> "$TEAM_REPORT"

REPORT_FILES+=("$TEAM_REPORT")

echo ""
echo "📤 发送报告文件..."
echo "========================================"

# 发送所有报告文件
for file in "${REPORT_FILES[@]}"; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "📄 发送: $filename"
        
        # 使用OpenClaw消息工具发送文件
        # 注意：这里需要调用外部命令或使用API
        echo "   文件路径: $file"
    fi
done

echo ""
echo "✅ 报告收集完成！"
echo "📁 报告目录: $REPORT_DIR"
echo ""
echo "找到的报告文件:"
ls -lh "${REPORT_FILES[@]}" 2>/dev/null

# 输出文件列表供调用者使用
printf '%s\n' "${REPORT_FILES[@]}"
