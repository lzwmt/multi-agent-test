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
STRICT_AI_ONLY="${STRICT_AI_ONLY:-1}"
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
    CACHE_FILE="$CACHE_FILE" NEWS_COUNT="$NEWS_COUNT" STRICT_AI_ONLY="$STRICT_AI_ONLY" python3 <<'PY'
import html
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

cache_file = Path(os.environ["CACHE_FILE"])
news_count = int(os.environ["NEWS_COUNT"])
strict_ai_only = os.environ.get("STRICT_AI_ONLY", "1") == "1"
feeds = [
    ("OpenAI", "https://openai.com/news/rss.xml", True),
    ("Google AI", "https://blog.google/technology/ai/rss/", True),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml", True),
    ("MarkTechPost", "https://www.marktechpost.com/feed/", True),
    ("36氪", "https://36kr.com/feed", False),
    ("爱范儿", "https://www.ifanr.com/feed", False),
    ("虎嗅", "https://rss.huxiu.com/", False),
    ("少数派", "https://sspai.com/feed", False),
]
ai_keywords = [
    "ai", "人工智能", "aigc", "大模型", "gpt", "claude", "deepseek", "openai", "机器学习", "llm",
    "智能体", "agent", "sora", "copilot", "kimi", "豆包", "通义", "文心", "智谱", "机器人",
    "芯片", "半导体", "算力", "gpu", "云计算", "量子", "腾讯", "阿里", "字节", "百度", "华为",
    "微软", "谷歌", "meta", "anthropic", "英伟达", "nvidia", "tesla", "spacex", "自动驾驶",
    "推理", "模型", "foundation model", "diffusion", "transformer", "token", "inference", "agentic"
]
tech_keywords = ai_keywords + [
    "科技", "互联网", "软件", "硬件", "算法", "saas", "开发者", "编程", "开源", "数据库", "搜索引擎"
]
blocked_keywords = [
    "音乐", "专辑", "征文", "写作", "随笔", "摄影", "电影", "电视剧", "综艺", "游戏攻略", "读书", "旅行", "送货", "兼职",
    "时尚", "穿搭", "美妆", "测评", "家居", "好物", "购物", "餐厅", "咖啡", "耳机", "音箱", "汽车评测"
]
priority_source_bonus = {
    "OpenAI": 30,
    "Google AI": 22,
    "Hugging Face": 20,
    "MarkTechPost": 18,
    "36氪": 8,
    "爱范儿": 6,
    "虎嗅": 4,
    "少数派": 1,
}

cn_tz = timezone(timedelta(hours=8))
today = datetime.now(cn_tz).date()


def get_text(elem, name):
    child = elem.find(name)
    return child.text.strip() if child is not None and child.text else ""


def clean_html(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def score_keywords(text, keywords):
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword in lowered)


def is_blocked_item(item):
    text = f"{item['title']} {item.get('desc', '')}".lower()
    return any(keyword in text for keyword in blocked_keywords)


def normalize_url(url):
    return (url or "").split("#", 1)[0].rstrip("/")


all_news = []
seen_titles = set()
seen_urls = set()
for source_name, feed_url, ai_native in feeds:
    try:
        result = subprocess.run(
            ["curl", "-fsSL", "--max-time", "20", feed_url],
            capture_output=True,
            timeout=25,
            check=True,
        )
        xml_text = result.stdout.decode("utf-8", errors="ignore")
        root = ET.fromstring(xml_text)
    except Exception as exc:
        print(f"⚠️ {source_name} 抓取失败: {exc}", file=sys.stderr)
        continue

    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall(".//item")
    added = 0
    for item in items:
        title = clean_html(get_text(item, "title"))
        link = get_text(item, "link")
        desc = clean_html(get_text(item, "description"))
        pub_date = get_text(item, "pubDate") or get_text(item, "published")
        normalized_url = normalize_url(link)
        if not title or title in seen_titles or normalized_url in seen_urls or not is_today(pub_date):
            continue
        candidate = {"title": title, "desc": desc}
        if is_blocked_item(candidate):
            continue

        ai_score = score_keywords(f"{title} {desc}", ai_keywords)
        tech_score = score_keywords(f"{title} {desc}", tech_keywords)
        if strict_ai_only and not ai_native and ai_score == 0:
            continue
        if not strict_ai_only and tech_score == 0:
            continue

        seen_titles.add(title)
        if normalized_url:
            seen_urls.add(normalized_url)
        all_news.append({
            "title": title,
            "summary": desc[:220] or title[:120],
            "url": link,
            "source": source_name,
            "ai_score": ai_score,
            "tech_score": tech_score,
            "source_bonus": priority_source_bonus.get(source_name, 0),
            "ai_native": ai_native,
        })
        added += 1
    print(f"✅ {source_name}: {added} 条候选新闻", file=sys.stderr)

if not all_news:
    raise SystemExit("没有抓到可用新闻")

selected = sorted(
    all_news,
    key=lambda item: (
        item["ai_native"],
        item["ai_score"],
        item["tech_score"],
        item["source_bonus"],
        len(item.get("summary", "")),
    ),
    reverse=True,
)[:news_count]

if not selected:
    raise SystemExit("没有筛出可用的 AI/科技新闻")

for item in selected:
    item.pop("ai_score", None)
    item.pop("tech_score", None)
    item.pop("source_bonus", None)
    item.pop("ai_native", None)

cache_file.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"💾 已写入缓存: {cache_file}")
PY
}

prepare_items() {
    log "🧾 读取新闻数据..."
    CACHE_FILE="$CACHE_FILE" NEWS_COUNT="$NEWS_COUNT" ENABLE_AI_SUMMARY="$ENABLE_AI_SUMMARY" python3 <<'PY'
import html
import json
import os
import re
from pathlib import Path

cache_file = Path(os.environ["CACHE_FILE"])
out_file = Path(os.environ["TEMP_DIR"]) / "items.tsv"
news_count = int(os.environ["NEWS_COUNT"])
enable_ai_summary = os.environ.get("ENABLE_AI_SUMMARY", "0") == "1"
items = json.loads(cache_file.read_text(encoding="utf-8"))
items = items[:news_count]

boilerplate_patterns = [
    r"查看全文.*$",
    r"阅读原文.*$",
    r"本文来自.*$",
    r"编者按[:：]?.*$",
    r"编者注[:：]?.*$",
    r"题图[:：]?.*$",
]
summary_splitters = ["。", "；", "！", "？", ";", "!", "?", "，", ",", "、", ":", "："]


def clean_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip()
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return text


def normalize_title(title):
    title = clean_text(title)
    title = re.sub(r"^[^\u4e00-\u9fa5A-Za-z0-9]+", "", title)
    title = re.sub(r"[|｜:：].*$", "", title).strip()
    return title


def split_segments(text):
    segments = [text]
    for splitter in summary_splitters:
        refined = []
        for segment in segments:
            parts = [part.strip() for part in segment.split(splitter) if part.strip()]
            refined.extend(parts or [segment])
        segments = refined
    return [segment for segment in segments if segment]


keywords = [
    "AI", "人工智能", "大模型", "模型", "芯片", "GPU", "Agent", "智能体", "机器人", "算力", "开源", "发布", "上线",
    "推出", "升级", "融资", "收购", "合作", "平台", "系统", "应用", "工具", "开发", "语音", "视频", "搜索", "云",
    "微软", "谷歌", "OpenAI", "Anthropic", "Meta", "苹果", "腾讯", "阿里", "字节", "华为", "百度", "特斯拉"
]


def score_segment(segment, title):
    score = 0
    combined = f"{title} {segment}".lower()
    for keyword in keywords:
        if keyword.lower() in combined:
            score += 3
    if any(ch.isdigit() for ch in segment):
        score += 1
    if 18 <= len(segment) <= 48:
        score += 2
    if len(segment) > 70:
        score -= 1
    return score


def local_summarize(title, summary):
    normalized_title = normalize_title(title)
    summary = clean_text(summary)
    if not summary:
        return normalized_title[:70]

    segments = split_segments(summary)
    ranked = sorted(segments, key=lambda seg: (score_segment(seg, normalized_title), -abs(len(seg) - 30)), reverse=True)
    chosen = []
    total_len = 0
    for segment in ranked:
        segment = segment.strip("，。；;:：、 ")
        if not segment or segment in chosen:
            continue
        if normalized_title and segment in normalized_title:
            continue
        if len(segment) < 8:
            continue
        next_len = total_len + len(segment)
        if chosen and next_len > 68:
            continue
        chosen.append(segment)
        total_len = next_len
        if total_len >= 36:
            break

    lead = normalized_title[:22].rstrip("，。；;:：、 ")
    if not chosen:
        compact = summary[:52].rstrip("，。；;:：、 ")
        if compact and compact != lead:
            return f"{lead}：{compact}"[:68].rstrip("，。；;:：、 ") if lead else compact
        return compact or lead

    body = "，".join(chosen).strip("，。；;:：、 ")
    if lead and body and body not in lead:
        result = f"{lead}：{body}"
    else:
        result = body or lead
    return result[:68].rstrip("，。；;:：、 ")


with out_file.open("w", encoding="utf-8") as f:
    for idx, item in enumerate(items):
        title = clean_text((item.get("title") or "无标题").replace("\t", " ").replace("\n", " "))
        raw_summary = clean_text((item.get("summary") or title).replace("\t", " ").replace("\n", " "))
        summary = local_summarize(title, raw_summary)
        url = clean_text((item.get("url") or "").replace("\t", " "))
        source = clean_text((item.get("source") or "").replace("\t", " "))
        f.write(f"{idx}\t{title[:48]}\t{summary[:140]}\t{url}\t{source}\n")
print(len(items))
if enable_ai_summary:
    print("⚠️ 已忽略 --ai-summary，当前改为本地摘要策略", file=os.sys.stderr)
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
  --ai-summary      保留兼容参数，当前固定使用本地摘要策略
  --voiceover       启用 edge-tts 中文配音
  --strict-ai-only  严格 AI 模式，仅保留 AI 原生源或命中 AI 关键词的内容（默认）
  --mixed-tech      放宽为科技模式，允许更广泛科技新闻
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
            --strict-ai-only) STRICT_AI_ONLY=1 ;;
            --mixed-tech) STRICT_AI_ONLY=0 ;;
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
