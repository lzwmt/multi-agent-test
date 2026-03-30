#!/bin/bash
# 清理超过7天的分析报告
REPORT_BASE="/root/.openclaw/workspace/analysis-reports"

find "$REPORT_BASE" -maxdepth 1 -type d -name "my-stocks-*" -mtime +7 -exec rm -rf {} \; 2>/dev/null

echo "$(date): 已清理超过7天的分析报告"
