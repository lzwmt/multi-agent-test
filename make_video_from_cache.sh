#!/bin/bash

TEMP_DIR=$(mktemp -d)
OUTPUT_DIR="/root/.openclaw/workspace/output"
mkdir -p "$OUTPUT_DIR"

# 配置 - 调整时长
NEWS_COUNT=20
DURATION_PER_NEWS=3.5  # 每条新闻3.5秒
FRAME_DURATION=0.14   # 每帧0.14秒

echo "📥 从缓存读取新闻..."
python3 -c "
import json
with open('/root/.openclaw/workspace/news_cache.json', 'r') as f:
    news = json.load(f)
for i, item in enumerate(news[:$NEWS_COUNT]):
    title = item.get('title', '无标题')[:30]
    summary = item.get('summary', '')[:100]
    # 估算标题行数（每行约20字，更准确）
    title_lines = (len(title) + 19) // 20
    if title_lines >= 2:
        # 两行标题：absolute位置更低
        use_absolute = 'yes_2lines'
    else:
        # 1行标题：absolute标准位置
        use_absolute = 'yes'
    print(f'{i}|{title}|{summary}|{use_absolute}')
" > "$TEMP_DIR/summaries.txt"

count=$(wc -l < "$TEMP_DIR/summaries.txt")
echo "✅ 读取 $count 条新闻"

# 下载 BGM
if [ ! -f "$TEMP_DIR/bgm.mp3" ]; then
    curl -fsSL "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3" -o "$TEMP_DIR/bgm.mp3" 2>/dev/null || touch "$TEMP_DIR/bgm.mp3"
fi

echo "🎨 生成图片卡片..."

# HTML 模板 - 科技感背景
cat > "$TEMP_DIR/card_template.html" << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: sans-serif;
            width: 1080px; height: 1920px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 50%, #1a0a2e 100%);
            color: white;
            overflow: hidden;
            padding: 100px 0;
            position: relative;
        }
        /* 网格线 */
        body::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(0, 245, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 245, 255, 0.05) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
        }
        /* 右上角光晕 */
        body::after {
            content: '';
            position: absolute;
            top: -200px;
            right: -200px;
            width: 700px;
            height: 700px;
            background: radial-gradient(circle, rgba(0, 245, 255, 0.2) 0%, rgba(138, 43, 226, 0.1) 40%, transparent 70%);
            pointer-events: none;
        }
        /* 左下角光晕 */
        .glow-bottom-left {
            position: absolute;
            bottom: -200px;
            left: -200px;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(138, 43, 226, 0.25) 0%, rgba(0, 255, 148, 0.1) 40%, transparent 70%);
            pointer-events: none;
        }
        /* 扫描线效果 */
        .scanline {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.3), transparent);
            animation: scan 3s linear infinite;
            pointer-events: none;
        }
        @keyframes scan {
            0% { top: -4px; }
            100% { top: 1924px; }
        }
        /* 底部渐变遮罩 */
        .bottom-gradient {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 300px;
            background: linear-gradient(to top, rgba(10, 10, 26, 0.9), transparent);
            pointer-events: none;
        }
        .header-title {
            position: absolute;
            top: 60px;
            text-align: center;
            font-size: 100px;
            font-weight: 900;
            letter-spacing: 12px;
            background: linear-gradient(90deg, #00F5FF, #00FF94, #8A2BE2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(0, 245, 255, 0.5);
            z-index: 10;
        }
        .title {
            position: absolute;
            top: 240px;
            font-weight: 900;
            letter-spacing: 8px;
            font-size: 58px;
            color: white;
            line-height: 1.5;
            margin: 0; 
            padding-left: 80px;
            z-index: 10;
        }
        .summary {
            font-size: 56px;
            line-height: 2;
            max-width: 1100px;
            margin: 30px 40px 0 80px;
            white-space: pre-wrap;
            text-indent: 1em;
            z-index: 10;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="glow-bottom-left"></div>
    <div class="scanline"></div>
    <div class="bottom-gradient"></div>
    <div class="header-title">DATE AI早报</div>
    <div class="title">TITLE</div>
    <div class="summary">SUMMARY</div>
</body>
</html>
HTMLEOF

# 生成卡片图片
idx=1
while IFS='|' read -r num title summary use_absolute; do
    [ -z "$title" ] && continue
    
    current_date=$(date +"%m月%d日")
    
    # 生成卡片
    sed -e "s|DATE|$current_date|" \
        -e "s|TITLE|$title|g" \
        -e "s|SUMMARY|$summary|g" \
        "$TEMP_DIR/card_template.html" > "$TEMP_DIR/card_$idx.html"
    
    # 使用 playwright
    if command -v node &>/dev/null && node -e "require('playwright')" 2>/dev/null; then
        node -e "
        const { chromium } = require('playwright');
        (async () => {
            const browser = await chromium.launch();
            const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
            await page.goto('file://$TEMP_DIR/card_$idx.html', { waitUntil: 'networkidle' });
            for (let i = 0; i < 25; i++) {
                await page.waitForTimeout(140);
                await page.screenshot({ path: '$TEMP_DIR/card_${idx}_' + i + '.png' });
            }
            await browser.close();
        })();
        " 2>/dev/null || {
            convert -size 1080x1920 xc:"#0a0a1a" "$TEMP_DIR/card_${idx}_0.png"
        }
    else
        convert -size 1080x1920 xc:"#0a0a1a" "$TEMP_DIR/card_${idx}_0.png"
    fi
    
    idx=$((idx+1))
done < "$TEMP_DIR/summaries.txt"

echo "✅ 图片生成完成"

# 合成视频
echo "🎬 合成视频..."

> "$TEMP_DIR/frames.txt"
for i in $(seq 1 $count); do
    for f in $(seq 0 24); do
        if [ -f "$TEMP_DIR/card_${i}_${f}.png" ]; then
            echo "file '$TEMP_DIR/card_${i}_${f}.png'" >> "$TEMP_DIR/frames.txt"
            echo "duration $FRAME_DURATION" >> "$TEMP_DIR/frames.txt"
        fi
    done
done

ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/frames.txt" \
    -vsync vfr -pix_fmt yuv420p \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
    "$TEMP_DIR/video_no_audio.mp4" 2>/dev/null || {
    echo "❌ 视频合成失败"
    exit 1
}

# 添加 BGM
output_file="$OUTPUT_DIR/ai_news_$(date +%Y%m%d_%H%M%S).mp4"
if [ -f "$TEMP_DIR/bgm.mp3" ] && [ -s "$TEMP_DIR/bgm.mp3" ]; then
    ffmpeg -y -i "$TEMP_DIR/video_no_audio.mp4" -i "$TEMP_DIR/bgm.mp3" \
        -c:v copy -c:a aac -b:a 192k -map 0:v -map 1:a -shortest \
        "$output_file" 2>/dev/null || cp "$TEMP_DIR/video_no_audio.mp4" "$output_file"
else
    cp "$TEMP_DIR/video_no_audio.mp4" "$output_file"
fi

echo "✅ 视频生成完成: $output_file"
ls -lh "$output_file"

# 清理
rm -rf "$TEMP_DIR"