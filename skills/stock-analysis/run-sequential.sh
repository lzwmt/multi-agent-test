#!/bin/bash
# 股票分析团队启动脚本 - 顺序执行模式（内存优化版）
# 7个子代理顺序执行，避免内存峰值

set -euo pipefail

SYMBOL=${1:-}
DAYS=${2:-7}

if [ $# -eq 0 ] || [ -z "$SYMBOL" ]; then
    echo "Usage: run-sequential.sh <股票代码> [天数]"
    echo "Example: run-sequential.sh 002514 7"
    exit 1
fi

TEAM_NAME="stock-${SYMBOL}-$(date +%s)"
WORKSPACE="/tmp/stock-analysis-${SYMBOL}-$(date +%s)"

mkdir -p /root/.openclaw/workspace/reports
mkdir -p "$WORKSPACE"

echo "🚀 启动股票分析团队（顺序执行模式）: $SYMBOL"
echo "========================================"
echo "📊 策略: 7个子代理顺序执行，降低内存峰值"
echo "📁 工作目录: $WORKSPACE"
echo "👥 团队名称: $TEAM_NAME"
echo ""

# 检查 Lightpanda
if ! docker ps | grep -q "lightpanda"; then
    echo "🔧 启动 Lightpanda..."
    docker start lightpanda 2>/dev/null || docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly
    sleep 2
fi

echo "✅ 依赖检查完成"
echo ""

# 定义分析器列表（按优先级排序）
ANALYZERS=(
    "fundamentals-analyst:基本面分析"
    "technical-analyst:技术分析"
    "sentiment-analyst:情绪分析"
    "buffett-analyst:价值投资分析"
    "growth-analyst:增长分析"
    "risk-manager:风险评估"
    "portfolio-manager:投资组合决策"
)

# 顺序执行分析器
for analyzer_info in "${ANALYZERS[@]}"; do
    IFS=':' read -r analyzer_name analyzer_desc <<< "$analyzer_info"
    
    echo "🔄 启动: $analyzer_desc ($analyzer_name)"
    echo "💾 当前内存: $(free -m | awk 'NR==2{printf "%.0f%%", $3*100/$2}')"
    
    # 启动单个分析器
    clawteam launch single-agent \
        --name "$analyzer_name" \
        --type general-purpose \
        --workspace "$WORKSPACE/$analyzer_name" \
        --goal "分析股票 $SYMBOL 的$analyzer_desc。使用智能搜索获取实时数据，生成分析报告保存到 $WORKSPACE/${analyzer_name}-report.md" \
        2>&1 | tail -5
    
    # 等待分析器完成（最多5分钟）
    echo "⏳ 等待分析完成..."
    for i in {1..30}; do
        sleep 10
        if [ -f "$WORKSPACE/${analyzer_name}-report.md" ]; then
            echo "✅ $analyzer_desc 完成"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "⚠️ $analyzer_desc 超时，继续下一个"
        fi
    done
    
    # 强制清理内存
    echo "🧹 清理资源..."
    sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    
    echo ""
done

# 汇总报告
echo "========================================"
echo "📊 生成汇总报告..."

SUMMARY_FILE="/root/.openclaw/workspace/reports/${SYMBOL}-analysis-$(date +%Y%m%d-%H%M%S).md"

cat > "$SUMMARY_FILE" << EOF
# 股票分析报告: $SYMBOL

**分析时间**: $(date '+%Y-%m-%d %H:%M:%S')
**股票代码**: $SYMBOL

## 分析模块

EOF

for analyzer_info in "${ANALYZERS[@]}"; do
    IFS=':' read -r analyzer_name analyzer_desc <<< "$analyzer_info"
    report_file="$WORKSPACE/${analyzer_name}-report.md"
    
    if [ -f "$report_file" ]; then
        echo "### $analyzer_desc" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
        cat "$report_file" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
    else
        echo "### $analyzer_desc" >> "$SUMMARY_FILE"
        echo "⚠️ 分析报告未生成" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
    fi
done

echo "✅ 汇总报告: $SUMMARY_FILE"
echo ""
echo "📁 所有报告位置:"
ls -la "$WORKSPACE"/*.md 2>/dev/null || echo "无单独报告文件"
echo ""

# 清理
echo "🧹 清理临时文件..."
rm -rf "$WORKSPACE"

echo "========================================"
echo "🎉 分析完成!"
echo "💾 最终内存: $(free -m | awk 'NR==2{printf "%.0f%%", $3*100/$2}')"
