#!/bin/bash
# Stable AI/tech news short-video generator.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/output}"
CACHE_FILE="${CACHE_FILE:-$SCRIPT_DIR/news_cache.json}"
TEMP_PARENT="${TEMP_PARENT:-/tmp}"
TEMP_DIR="$(mktemp -d "$TEMP_PARENT/news_video_v2.XXXXXX")"
export TEMP_DIR

NEWS_COUNT="${NEWS_COUNT:-10}"
FRAME_DURATION="${FRAME_DURATION:-0.14}"
FRAMES_PER_CARD="${FRAMES_PER_CARD:-25}"
CARD_WIDTH=1080
CARD_HEIGHT=1920
BGM_URL="${BGM_URL:-https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3}"
TITLE_PREFIX="${TITLE_PREFIX:-AI科技早报}"
ENABLE_AI_SUMMARY="${ENABLE_AI_SUMMARY:-0}"
ENABLE_VOICEOVER="${ENABLE_VOICEOVER:-0}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.0-flash}"
TTS_VOICE="${TTS_VOICE:-zh-CN-XiaoxiaoNeural}"

cleanup() {
    if [ "${KEEP_TEMP:-0}" != "1" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

log() {
    printf '%s\n' "$*"
}

require_cmd() {
    local missing=0
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log "❌ 缺少依赖: $cmd"
            missing=1
        fi
    done
    [ "$missing" -eq 0 ] || exit 1
}

init() {
    require_cmd python3 ffmpeg curl
    if [ "$ENABLE_VOICEOVER" = "1" ]; then
        require_cmd edge-tts
    fi
    mkdir -p "$OUTPUT_DIR" "$TEMP_DIR"

    if [ ! -s "$TEMP_DIR/bgm.mp3" ]; then
        curl -fsSL "$BGM_URL" -o "$TEMP_DIR/bgm.mp3" 2>/dev/null || touch "$TEMP_DIR/bgm.mp3"
    fi
}

fetch_news() {
    if [ -f "$CACHE_FILE" ] && [ -s "$CACHE_FILE" ] && [ "${REFRESH_CACHE:-0}" != "1" ]; then
        log "📦 使用现有缓存: $CACHE_FILE"
        return
    fi

    log "📰 抓取 RSS 新闻..."
    CACHE_FILE="$CACHE_FILE" NEWS_COUNT="$NEWS_COUNT" python3 <<'PY'
import json
import re
import subprocess
import sys
import html
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

import os

cache_file = Path(os.environ["CACHE_FILE"])
news_count = int(os.environ["NEWS_COUNT"])
feeds = [
    ("虎嗅", "https://rss.huxiu.com/"),
    ("少数派", "https://sspai.com/feed"),
]
ai_keywords = [
    "AI", "人工智能", "大模型", "GPT", "Claude", "DeepSeek", "OpenAI", "机器学习", "LLM",
    "智能体", "Agent", "Sora", "Copilot", "Kimi", "豆包", "通义", "文心", "智谱", "自动驾驶",
    "机器人", "芯片", "半导体", "量子", "腾讯", "阿里", "字节", "百度", "华为", "微软", "谷歌", "Meta", "Anthropic"
]
tech_keywords = ai_keywords + [
    "科技", "互联网", "软件", "硬件", "算法", "云", "SaaS", "手机", "电脑", "产品", "App", "应用",
    "5G", "新能源", "电商", "支付", "安全", "iPhone", "Android", "Windows", "Mac", "Linux", "Tesla", "YouTube", "TikTok"
]

cn_tz = timezone(timedelta(hours=8))
today = datetime.now(cn_tz).date()


def get_text(elem, name):
    child = elem.find(name)
    return child.text.strip() if child is not None and child.text else ""


def is_today(pub_date):
    if not pub_date:
        return True
    try:
        dt = parsedate_to_datetime(pub_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(cn_tz).date() == today
    except Exception:
        return True


def match_keywords(item, keywords):
    text = f"{item['title']} {item.get('desc', '')}".lower()
    return any(k.lower() in text for k in keywords)


all_news = []
seen = set()
for source_name, feed_url in feeds:
    try:
        result = subprocess.run([
            "curl", "-fsSL", "--max-time", "20", feed_url
        ], capture_output=True, text=True, timeout=25)
        root = ET.fromstring(result.stdout)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
    except Exception as exc:
        print(f"⚠️ {source_name} 抓取失败: {exc}", file=sys.stderr)
        continue

    added = 0
    for item in items:
        title = html.unescape(get_text(item, "title"))
        link = get_text(item, "link")
        desc = html.unescape(get_text(item, "description"))
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        pub_date = get_text(item, "pubDate")
        if not title or title in seen or not is_today(pub_date):
            continue
        seen.add(title)
        all_news.append({
            "title": title,
            "summary": desc[:120] or title[:120],
            "url": link,
            "source": source_name,
        })
        added += 1
    print(f"✅ {source_name}: {added} 条今日新闻", file=sys.stderr)

if not all_news:
    raise SystemExit("没有抓到可用新闻")

ai_news = [n for n in all_news if match_keywords(n, ai_keywords)]
tech_news = [n for n in all_news if n not in ai_news and match_keywords(n, tech_keywords)]
other_news = [n for n in all_news if n not in ai_news and n not in tech_news]
selected = (ai_news + tech_news + other_news)[:news_count]
cache_file.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"💾 已写入缓存: {cache_file}")
PY
}

prepare_items() {
    log "🧾 读取新闻数据..."
    CACHE_FILE="$CACHE_FILE" NEWS_COUNT="$NEWS_COUNT" ENABLE_AI_SUMMARY="$ENABLE_AI_SUMMARY" GEMINI_MODEL="$GEMINI_MODEL" python3 <<'PY'
import json
import os
import time
from pathlib import Path

import requests

cache_file = Path(os.environ["CACHE_FILE"])
out_file = Path(os.environ["TEMP_DIR"]) / "items.tsv"
news_count = int(os.environ["NEWS_COUNT"])
enable_ai_summary = os.environ.get("ENABLE_AI_SUMMARY", "0") == "1"
gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
api_key = os.environ.get("GOOGLE_GEMINI_API_KEY", "")
items = json.loads(cache_file.read_text(encoding="utf-8"))
items = items[:news_count]


def ai_summarize(title, summary):
    if not enable_ai_summary or not api_key:
        return summary
    prompt = (
        "你是科技新闻编辑。请把下面新闻压缩成一段中文短摘要，"
        "要求 45 到 70 个汉字，保留关键信息，不要使用项目符号，不要加入臆测。\n\n"
        f"标题：{title}\n"
        f"原摘要：{summary}\n"
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    last_error = None
    for _ in range(3):
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                text = " ".join(text.split())
                return text[:120] or summary
            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            if response.status_code in {429, 503}:
                time.sleep(2)
                continue
            break
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    print(f"⚠️ AI 摘要失败，回退原摘要: {last_error}", file=os.sys.stderr)
    return summary


with out_file.open("w", encoding="utf-8") as f:
    for idx, item in enumerate(items):
        title = (item.get("title") or "无标题").replace("\t", " ").replace("\n", " ").strip()
        summary = (item.get("summary") or title).replace("\t", " ").replace("\n", " ").strip()
        summary = ai_summarize(title, summary)
        url = (item.get("url") or "").replace("\t", " ").strip()
        source = (item.get("source") or "").replace("\t", " ").strip()
        f.write(f"{idx}\t{title[:48]}\t{summary[:140]}\t{url}\t{source}\n")
print(len(items))
PY
}

render_cards() {
    log "🎨 生成卡片图片..."
    TEMP_DIR="$TEMP_DIR" FRAMES_PER_CARD="$FRAMES_PER_CARD" FRAME_DURATION="$FRAME_DURATION" TITLE_PREFIX="$TITLE_PREFIX" python3 <<'PY'
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

items = (Path(os.environ["TEMP_DIR"]) / "items.tsv").read_text(encoding="utf-8").splitlines()
out_dir = Path(os.environ["TEMP_DIR"])
width = 1080
height = 1920
frames_per_card = int(os.environ["FRAMES_PER_CARD"])
title_prefix = os.environ["TITLE_PREFIX"]

font_candidates = [
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
font_path = next((p for p in font_candidates if Path(p).exists()), None)
if font_path is None:
    raise SystemExit("没有可用字体，无法渲染卡片")

header_font = ImageFont.truetype(font_path, 84)
title_font = ImageFont.truetype(font_path, 58)
summary_font = ImageFont.truetype(font_path, 42)
meta_font = ImageFont.truetype(font_path, 28)

def wrap(draw, text, font, max_width):
    chars = []
    line = ""
    for ch in text:
        test = line + ch
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            if line:
                chars.append(line)
            line = ch
    if line:
        chars.append(line)
    return chars

for raw in items:
    idx, title, summary, url, source = raw.split("\t")
    idx_int = int(idx)
    for frame in range(frames_per_card):
        img = Image.new("RGB", (width, height), "#0b1020")
        draw = ImageDraw.Draw(img)

        # Basic gradient-like bands to keep visuals stable without browser rendering.
        for y in range(height):
            ratio = y / height
            r = int(10 + ratio * 16)
            g = int(16 + ratio * 18)
            b = int(32 + ratio * 40)
            draw.line((0, y, width, y), fill=(r, g, b))

        alpha = min(1.0, (frame + 1) / 8.0)
        title_y = 260 + max(0, 30 - frame * 4)
        summary_y = 700 + max(0, 40 - frame * 5)

        date_text = datetime.now().strftime("%m月%d日")
        draw.text((90, 90), f"{date_text} {title_prefix}", font=header_font, fill=(0, 245, 255))
        draw.rounded_rectangle((72, 210, width - 72, height - 180), radius=36, outline=(90, 120, 255), width=3)
        draw.text((100, 1900 - 120), f"NO.{idx_int + 1:02d}", font=meta_font, fill=(180, 190, 255))
        meta_text = source or "RSS"
        draw.text((width - 250, 1900 - 120), meta_text, font=meta_font, fill=(180, 190, 255))

        title_lines = wrap(draw, title, title_font, width - 220)[:3]
        for line_no, line in enumerate(title_lines):
            draw.text((110, title_y + line_no * 84), line, font=title_font, fill=(255, 255, 255))

        summary_lines = wrap(draw, summary, summary_font, width - 220)[:5]
        for line_no, line in enumerate(summary_lines):
            draw.text((110, summary_y + line_no * 64), line, font=summary_font, fill=(210, 220, 255))

        out = out_dir / f"card_{idx_int}_{frame}.png"
        img.save(out)
PY
}

compose_video() {
    log "🎬 合成视频..."
    : > "$TEMP_DIR/frames.txt"

    local count
    count=$(wc -l < "$TEMP_DIR/items.tsv")
    if [ "$count" -eq 0 ]; then
        log "❌ 没有可用新闻条目"
        exit 1
    fi

    for i in $(seq 0 $((count - 1))); do
        for f in $(seq 0 $((FRAMES_PER_CARD - 1))); do
            echo "file '$TEMP_DIR/card_${i}_${f}.png'" >> "$TEMP_DIR/frames.txt"
            echo "duration $FRAME_DURATION" >> "$TEMP_DIR/frames.txt"
        done
    done
    echo "file '$TEMP_DIR/card_$((count - 1))_$((FRAMES_PER_CARD - 1)).png'" >> "$TEMP_DIR/frames.txt"

    ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/frames.txt" \
        -vsync vfr -pix_fmt yuv420p \
        -vf "scale=${CARD_WIDTH}:${CARD_HEIGHT}:force_original_aspect_ratio=decrease,pad=${CARD_WIDTH}:${CARD_HEIGHT}:(ow-iw)/2:(oh-ih)/2" \
        "$TEMP_DIR/video_no_audio.mp4" >/dev/null 2>&1

    if [ "$ENABLE_VOICEOVER" = "1" ]; then
        log "🎙️ 生成配音..."
        TEMP_DIR="$TEMP_DIR" TTS_VOICE="$TTS_VOICE" python3 <<'PY'
import os
from pathlib import Path

items = (Path(os.environ["TEMP_DIR"]) / "items.tsv").read_text(encoding="utf-8").splitlines()
parts = []
for raw in items:
    _, title, summary, _, source = raw.split("\t")
    source_text = f"来源{source}。" if source else ""
    parts.append(f"{title}。{summary}。{source_text}")
script = "接下来是今日 AI 科技新闻。" + " ".join(parts)
(Path(os.environ["TEMP_DIR"]) / "voiceover.txt").write_text(script, encoding="utf-8")
PY
        edge-tts --voice "$TTS_VOICE" --file "$TEMP_DIR/voiceover.txt" --write-media "$TEMP_DIR/voiceover.mp3" >/dev/null 2>&1 || true
    fi

    local output_file="$OUTPUT_DIR/ai_news_v2_$(date +%Y%m%d_%H%M%S).mp4"
    if [ -s "$TEMP_DIR/voiceover.mp3" ] && [ -s "$TEMP_DIR/bgm.mp3" ]; then
        ffmpeg -y -i "$TEMP_DIR/voiceover.mp3" -stream_loop -1 -i "$TEMP_DIR/bgm.mp3" \
            -filter_complex "[1:a]volume=0.12[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]" \
            -i "$TEMP_DIR/video_no_audio.mp4" -map 2:v -map "[aout]" -shortest -c:v copy -c:a aac -b:a 192k \
            "$output_file" >/dev/null 2>&1 || cp "$TEMP_DIR/video_no_audio.mp4" "$output_file"
    elif [ -s "$TEMP_DIR/voiceover.mp3" ]; then
        ffmpeg -y -i "$TEMP_DIR/voiceover.mp3" -i "$TEMP_DIR/video_no_audio.mp4" \
            -map 1:v -map 0:a -shortest -c:v copy -c:a aac -b:a 192k \
            "$output_file" >/dev/null 2>&1 || cp "$TEMP_DIR/video_no_audio.mp4" "$output_file"
    elif [ -s "$TEMP_DIR/bgm.mp3" ]; then
        ffmpeg -y -stream_loop -1 -i "$TEMP_DIR/bgm.mp3" -i "$TEMP_DIR/video_no_audio.mp4" \
            -map 0:a -map 1:v -shortest -c:v copy -c:a aac -b:a 192k \
            "$output_file" >/dev/null 2>&1 || cp "$TEMP_DIR/video_no_audio.mp4" "$output_file"
    else
        cp "$TEMP_DIR/video_no_audio.mp4" "$output_file"
    fi

    log "✅ 视频生成完成: $output_file"
    ls -lh "$output_file"
}

usage() {
    cat <<EOF
用法: $0 [选项]

选项:
  --refresh-cache   强制重新抓取 RSS
  --keep            保留临时目录
  --news-count N    新闻数量，默认 10
  --title TEXT      顶部标题，默认 AI科技早报
  --ai-summary      启用 Gemini AI 摘要，不可用时自动回退
  --voiceover       启用 edge-tts 中文配音
  --help            显示帮助
EOF
}

main() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --refresh-cache) REFRESH_CACHE=1 ;;
            --keep) KEEP_TEMP=1 ;;
            --news-count) NEWS_COUNT="$2"; shift ;;
            --title) TITLE_PREFIX="$2"; shift ;;
            --ai-summary) ENABLE_AI_SUMMARY=1 ;;
            --voiceover) ENABLE_VOICEOVER=1 ;;
            --help) usage; exit 0 ;;
            *) log "未知参数: $1"; usage; exit 1 ;;
        esac
        shift
    done

    log "========================================"
    log "   稳定版 AI/科技新闻短视频生成器"
    log "========================================"

    init
    fetch_news
    prepare_items
    local item_count
    item_count=$(wc -l < "$TEMP_DIR/items.tsv")
    log "✅ 共处理 ${item_count} 条新闻"
    render_cards
    compose_video
    log "✨ 全部完成"
}

main "$@"
