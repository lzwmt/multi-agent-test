#!/bin/bash
# 股票分析团队启动脚本 - 使用 ClawTeam hedge-fund 模板
# hedge-fund 模板包含 7 个子代理：
#   - portfolio-manager (leader): 协调分析并做出最终投资决策
#   - buffett-analyst: 价值投资分析（巴菲特风格）
#   - growth-analyst: 增长/颠覆性分析
#   - technical-analyst: 技术指标分析
#   - fundamentals-analyst: 基本面和财务指标分析
#   - sentiment-analyst: 新闻和内部人情绪分析
#   - risk-manager: 整合信号并评估投资组合风险

set -euo pipefail  # 启用严格模式

SYMBOL=${1:-}
DAYS=${2:-7}

# 检查参数
if [ $# -eq 0 ] || [ -z "$SYMBOL" ]; then
    echo "Usage: run.sh <股票代码> [天数]"
    echo "Example: run.sh 002514 7"
    exit 1
fi

# 验证股票代码格式（6位数字）
if ! [[ "$SYMBOL" =~ ^[0-9]{6}$ ]]; then
    echo "⚠️  警告: 股票代码应为6位数字，当前: $SYMBOL"
fi

TEAM_NAME="stock-${SYMBOL}-$(date +%s)"
WORKSPACE="/tmp/stock-analysis-${SYMBOL}-$(date +%s)"

# 确保目录存在
mkdir -p /root/.openclaw/workspace/reports
mkdir -p "$WORKSPACE"

echo "🚀 启动股票分析团队: $SYMBOL"
echo "========================================"
echo "📊 团队模板: hedge-fund (7个子代理)"
echo "📁 工作目录: $WORKSPACE"
echo "👥 团队名称: $TEAM_NAME"
echo "⏱️  分析天数: $DAYS"
echo ""

# 检查依赖
echo "🔍 检查依赖..."

# 检查 Lightpanda
if ! docker ps | grep -q "lightpanda"; then
    echo "⚠️  Lightpanda 未运行"
    if docker ps -a | grep -q "lightpanda"; then
        echo "   启动现有容器..."
        docker start lightpanda 2>/dev/null || true
    else
        echo "   创建新容器..."
        docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly 2>/dev/null || {
            echo "   ⚠️  Lightpanda 启动失败，将继续使用 Tavily 搜索"
        }
    fi
    sleep 2
fi

# 检查 ClawTeam
if ! command -v clawteam &>/dev/null; then
    echo "❌ 错误: ClawTeam 未安装"
    exit 1
fi

echo "✅ 依赖检查完成"
echo ""

# 构建强制使用智能搜索的 goal
GOAL="分析股票 $SYMBOL。

【强制要求 - 搜索工具】
❌ 绝对禁止使用 web_search 工具
✅ 必须使用智能搜索脚本：
   node /root/.openclaw/workspace/scripts/smart-search.js \"查询内容\" --count 10

【搜索要点】
1. 实时股价和涨跌幅
2. 最新财报数据（2025年三季报或年报）
3. 近期重大新闻、公告、证监会调查等
4. 主营业务和所属概念板块
5. 行业趋势和竞争分析
6. 分析师评级和机构持仓

【输出要求】
每个分析师必须基于搜索数据进行分析，并在报告中注明数据来源。
生成报告文件保存到 /root/.openclaw/workspace/ 目录，命名格式：
- stock_analysis_${SYMBOL}_<分析师类型>.md"

echo "🎯 启动 hedge-fund 分析团队..."
echo ""

# 启动团队
clawteam launch hedge-fund \
    --goal "$GOAL" \
    --team-name "$TEAM_NAME" || {
    echo "❌ 团队启动失败"
    exit 1
}

echo ""
echo "✅ 分析团队已启动: $TEAM_NAME"
echo ""
echo "📋 团队成员:"
echo "   1. portfolio-manager (队长) - 协调分析并做出最终投资决策"
echo "   2. buffett-analyst - 价值投资分析（巴菲特风格）"
echo "   3. growth-analyst - 增长/颠覆性分析"
echo "   4. technical-analyst - 技术指标分析"
echo "   5. fundamentals-analyst - 基本面和财务指标分析"
echo "   6. sentiment-analyst - 新闻和内部人情绪分析"
echo "   7. risk-manager - 整合信号并评估投资组合风险"
echo ""
echo "⏳ 分析进行中，请等待团队完成..."
echo ""
echo "💡 查看团队状态: clawteam team status --team-name $TEAM_NAME"
echo "💡 查看看板: clawteam board --team-name $TEAM_NAME"
echo ""
echo "📁 分析完成后，报告将自动收集并发送"
echo "========================================"

# 后台启动报告收集脚本
COLLECT_LOG="/tmp/collect-${TEAM_NAME}.log"

echo "🔄 启动报告收集进程..."
nohup bash -c "
    set -e
    echo \"⏳ 等待团队分析完成...\" 
    echo \"团队: ${TEAM_NAME}\"
    echo \"股票: ${SYMBOL}\"
    echo \"开始时间: \$(date)\"
    echo \"\"
    
    # 等待团队真正完成（最多等待30分钟）
    MAX_WAIT=1800
    WAITED=0
    
    while [ \$WAITED -lt \$MAX_WAIT ]; do
        BOARD_OUTPUT=\$(clawteam board show '${TEAM_NAME}' 2>&1 || true)
        
        # 检查是否全部完成
        if echo \"\$BOARD_OUTPUT\" | grep -q 'COMPLETED (7)' && echo \"\$BOARD_OUTPUT\" | grep -q 'IN PROGRESS (0)'; then
            echo \"✅ 团队分析完成！\"
            echo \"完成时间: \$(date)\"
            break
        fi
        
        # 显示进度
        COMPLETED=\$(echo \"\$BOARD_OUTPUT\" | grep 'COMPLETED' | head -1 | grep -oE '[0-9]+' | head -1 || echo '0')
        echo \"进度: \${COMPLETED}/7 完成 (\$((\$WAITED/60))分钟)\"
        
        sleep 30
        WAITED=\$((WAITED + 30))
    done
    
    if [ \$WAITED -ge \$MAX_WAIT ]; then
        echo \"⚠️ 等待超时，继续收集已有报告...\"
        fi
    
    echo \"\"
    echo \"📊 开始收集报告...\"
    cd /root/.openclaw/workspace/skills/stock-analysis
    bash ./collect-and-send.sh '${TEAM_NAME}' '${SYMBOL}'
        fi
    done
" > "$COLLECT_LOG" 2>&1 &

COLLECT_PID=$!
echo "✅ 报告收集进程已启动 (PID: $COLLECT_PID)"
echo "   日志: $COLLECT_LOG"
echo ""
echo "💡 实时监控日志: tail -f $COLLECT_LOG"
