#!/bin/bash
# Memory Usage Monitor - 监控 Gemini Embedding 用量

DB_PATH="/root/.openclaw/memory/main.sqlite"
LOG_FILE="/root/.openclaw/workspace/logs/memory_usage.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 获取当前 chunks 数量（估算 embedding 调用次数）
CHUNKS_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM chunks;" 2>/dev/null || echo "0")

# 获取今日新增 chunks（通过 updated_at 时间戳）
TODAY=$(date '+%Y-%m-%d')
TODAY_START=$(date -d "$TODAY 00:00:00" '+%s' 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$TODAY 00:00:00" '+%s' 2>/dev/null || echo "0")
TODAY_CHUNKS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM chunks WHERE updated_at >= $TODAY_START;" 2>/dev/null || echo "0")

# 获取 embedding cache 数量
CACHE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM embedding_cache;" 2>/dev/null || echo "0")

# 计算估算用量（假设每次搜索调用 1 次 embedding，每天 100 轮对话）
# 实际用量 = 索引调用 + 搜索调用
ESTIMATED_DAILY_USAGE=$((TODAY_CHUNKS + 100))

# 写入日志
echo "[$DATE] Chunks: $CHUNKS_COUNT | Today New: $TODAY_CHUNKS | Cache: $CACHE_COUNT | Est. Daily: $ESTIMATED_DAILY_USAGE" >> "$LOG_FILE"

# 检查是否接近限额（1500/day）
if [ "$ESTIMATED_DAILY_USAGE" -gt 1200 ]; then
    echo "[$DATE] ⚠️ WARNING: Approaching Gemini limit! ($ESTIMATED_DAILY_USAGE/1500)" >> "$LOG_FILE"
fi

if [ "$ESTIMATED_DAILY_USAGE" -gt 1400 ]; then
    echo "[$DATE] 🚨 ALERT: Near Gemini limit! ($ESTIMATED_DAILY_USAGE/1500)" >> "$LOG_FILE"
fi

# 输出当前状态
echo "Memory Usage Report:"
echo "  Total Chunks: $CHUNKS_COUNT"
echo "  Today New: $TODAY_CHUNKS"
echo "  Cache Entries: $CACHE_COUNT"
echo "  Est. Daily Usage: $ESTIMATED_DAILY_USAGE/1500"
echo "  Log: $LOG_FILE"
