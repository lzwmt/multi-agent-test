#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

ENABLE_AI_SUMMARY="${ENABLE_AI_SUMMARY:-0}"
ENABLE_VOICEOVER="${ENABLE_VOICEOVER:-1}"
NEWS_COUNT="${NEWS_COUNT:-5}"
TITLE_PREFIX="${TITLE_PREFIX:-AI科技早报}"

args=(--refresh-cache --news-count "$NEWS_COUNT" --title "$TITLE_PREFIX")
if [ "$ENABLE_AI_SUMMARY" = "1" ]; then
    args+=(--ai-summary)
fi
if [ "$ENABLE_VOICEOVER" = "1" ]; then
    args+=(--voiceover)
fi

exec ./news_video_generator.sh "${args[@]}"
