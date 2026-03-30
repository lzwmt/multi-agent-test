#!/bin/bash
# Script Development Skill - 自动写脚本 + 审查
# Usage: ./dev.sh "需求描述" [输出路径]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="/root/.openclaw/workspace"
TIMESTAMP=$(date +%s)

# 参数检查
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"脚本需求描述\" [输出路径]"
    echo "Example: $0 \"备份目录到/tmp，保留7天\" ./backup.sh"
    exit 1
fi

REQUIREMENT="$1"
OUTPUT_PATH="${2:-$WORKSPACE/generated-script-${TIMESTAMP}.sh}"

echo "========================================"
echo "🚀 Script Development Skill"
echo "========================================"
echo "需求: $REQUIREMENT"
echo "输出: $OUTPUT_PATH"
echo ""

# Step 1: devops-automator 写脚本
echo "📋 Step 1: 编写脚本 (devops-automator)"
echo "----------------------------------------"

TEAM_NAME="script-dev-${TIMESTAMP}"

# 创建团队
clawteam team spawn-team "${TEAM_NAME}" -d "${REQUIREMENT}" -n devops-automator

# 创建任务
clawteam task create "${TEAM_NAME}" "编写脚本: ${REQUIREMENT}" -o devops-automator

# 启动代理
clawteam spawn -t "${TEAM_NAME}" -n devops-automator \
    --task "${REQUIREMENT}。保存脚本到: ${OUTPUT_PATH}"

echo "⏳ 等待脚本生成..."


# 等待脚本生成
MAX_WAIT=180
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if [ -f "${OUTPUT_PATH}" ]; then
        echo "✅ 脚本已生成: ${OUTPUT_PATH}"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "  等待中... ${WAITED}s"
done

if [ ! -f "${OUTPUT_PATH}" ]; then
    echo "❌ 脚本生成超时"
    exit 1
fi

echo ""

# Step 2: code-reviewer 审查
echo "📋 Step 2: 代码审查 (code-reviewer)"
echo "----------------------------------------"

REVIEW_TEAM="script-review-${TIMESTAMP}"
REVIEW_REPORT="${OUTPUT_PATH}.review.md"

# 创建审查团队
clawteam team spawn-team "${REVIEW_TEAM}" -d "审查 ${OUTPUT_PATH}" -n code-reviewer

# 创建审查任务
clawteam task create "${REVIEW_TEAM}" "审查 ${OUTPUT_PATH}" -o code-reviewer

# 启动审查代理
clawteam spawn -t "${REVIEW_TEAM}" -n code-reviewer \
    --task "审查 ${OUTPUT_PATH}，检查语法、安全、错误处理、可维护性、最佳实践。输出审查报告。"

echo "⏳ 等待审查完成..."

# 等待审查完成
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    # 检查 tmux 输出
    if tmux has-session -t "clawteam-${REVIEW_TEAM}:code-reviewer" 2>/dev/null; then
        OUTPUT=$(tmux capture-pane -t "clawteam-${REVIEW_TEAM}:code-reviewer" -p 2>/dev/null | grep -E "总体评级|Summary|审查完成" | head -1)
        if [ -n "$OUTPUT" ]; then
            echo "✅ 审查完成"
            break
        fi
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "  等待中... ${WAITED}s"
done

# 获取审查结果
echo ""
echo "========================================"
echo "📊 审查报告"
echo "========================================"

if tmux has-session -t "clawteam-${REVIEW_TEAM}:code-reviewer" 2>/dev/null; then
    tmux capture-pane -t "clawteam-${REVIEW_TEAM}:code-reviewer" -p 2>/dev/null | tail -100
fi

echo ""
echo "========================================"
echo "✅ Script Development 完成"
echo "========================================"
echo "脚本: ${OUTPUT_PATH}"
echo "审查: ${REVIEW_REPORT}"
echo ""
echo "💡 使用脚本:"
echo "  chmod +x ${OUTPUT_PATH}"
echo "  ${OUTPUT_PATH} --help"
