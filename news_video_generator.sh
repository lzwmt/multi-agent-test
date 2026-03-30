#!/bin/bash
#
# 每日AI新闻短视频生成脚本
# 技术栈: mcporter + TrendRadar + Canvas + Remotion + Edge-TTS
# 输出: 9:16 竖屏 MP4 (抖音/视频号)
#

set -euo pipefail

# ========== 配置 (可自定义) ==========
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/output}"
TEMP_DIR="${TEMP_DIR:-/tmp/news_video_$$}"
export TEMP_DIR
PROJECT_DIR="$TEMP_DIR/remotion-project"

# 视频参数
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920  # 9:16 竖屏
DURATION_PER_NEWS=5  # 每条新闻展示秒数
NEWS_COUNT=10        # 选取新闻数量
BGM_VOLUME=0.15      # 背景音乐音量（有配音时更低）
AUDIO_FORMAT="mp3"  # 配音格式

# 颜色配置
PRIMARY_COLOR="#6366F1"
TEXT_COLOR="#FFFFFF"
BG_GRADIENT_START="#1E1B4B"
BG_GRADIENT_END="#312E81"

# 背景音乐URL (免费版权)
BGM_URL="https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3"  # Pixabay 免费音乐

# ========== 依赖检查 ==========
check_dependencies() {
    echo "🔍 检查依赖..."
    
    local missing=()
    
    # 检查必需命令
    for cmd in mcporter ffmpeg python3; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "❌ 缺少依赖: ${missing[*]}"
        echo "请安装: brew install ${missing[*]} (macOS) 或 apt-get install ${missing[*]} (Linux)"
        exit 1
    fi
    
    # 可选依赖
    if ! command -v edge-tts &>/dev/null; then
        echo "⚠️ edge-tts 未安装，尝试 pip 安装..."
        pip install edge-tts &>/dev/null || true
    fi
    
    if ! command -v node &>/dev/null; then
        echo "⚠️ node 未安装，图片生成将使用备用方案"
        USE_PLAYWRIGHT=false
    else
        USE_PLAYWRIGHT=true
    fi
    
    echo "✅ 依赖检查通过"
}

# ========== 初始化 ==========
init() {
    echo "📁 初始化项目目录..."
    mkdir -p "$OUTPUT_DIR" "$TEMP_DIR" "$PROJECT_DIR"
    
    # 下载背景音乐
    if [ ! -f "$TEMP_DIR/bgm.mp3" ]; then
        echo "🎵 下载背景音乐..."
        if curl -fsSL "$BGM_URL" -o "$TEMP_DIR/bgm.mp3" 2>/dev/null; then
            echo "✅ 背景音乐下载完成"
        else
            echo "⚠️ 背景音乐下载失败，将使用静音"
            touch "$TEMP_DIR/bgm.mp3"
        fi
    fi
    
    echo "✅ 初始化完成"
}

# ========== 第一步: 获取AI新闻 (虎嗅→36氪→少数派) ==========
fetch_ai_news_from_cache() {
    echo "🔍 步骤1: 获取热点新闻（AI优先，科技补充）..."
    
    local today_en=$(date +'%a, %d %b %Y')
    local today_cn=$(date +'%Y-%m-%d')
    
    local rss_feeds=(
        "https://rss.huxiu.com/"
        "https://sspai.com/feed"
    )
    
    # 逐个抓取 RSS（Python 端会过滤反爬页面）
    > "$TEMP_DIR/raw_rss.xml"
    local fetch_ok=0
    for feed_url in "${rss_feeds[@]}"; do
        local content=$(curl -sL --max-time 15 "$feed_url" 2>/dev/null)
        if [ ${#content} -gt 100 ]; then
            echo "$content" >> "$TEMP_DIR/raw_rss.xml"
            echo "" >> "$TEMP_DIR/raw_rss.xml"
            fetch_ok=1
            local domain=$(echo "$feed_url" | grep -oP '//\K[^/]+')
            echo "  ✅ $domain"
        else
            local domain=$(echo "$feed_url" | grep -oP '//\K[^/]+')
            echo "  ⚠️ $domain 无数据，跳过"
        fi
    done
    
    if [ "$fetch_ok" -eq 0 ]; then
        echo "❌ 所有 RSS 源获取失败"
        echo "NOTIFY: ⚠️ 新闻视频：所有 RSS 源获取失败，请检查网络"
        exit 1
    fi
    
    echo "✅ 获取到 RSS 数据"
    
    # 解析 RSS 提取新闻（AI优先，不够用科技补，必须凑够NEWS_COUNT条）
    python3 -c "
import re, sys, subprocess, os, html as html_mod

today_en = '$today_en'
today_cn = '$today_cn'
target_count = $NEWS_COUNT

rss_sources = [
    ('虎嗅', 'https://rss.huxiu.com/'),
    ('少数派', 'https://sspai.com/feed'),
]

ai_keywords = ['AI', 'ai', '人工智能', '大模型', 'GPT', 'Claude', 'DeepSeek', 
               'OpenAI', '机器学习', '深度学习', 'NLP', 'LLM', '具身智能', 
               'Sora', 'Copilot', 'Agent', '智能体', '文心', '通义', '豆包', 
               'Kimi', '智谱', '商汤', '旷视', '科大讯飞', '芯片', '半导体', 
               '量子', '机器人', '自动驾驶', '智能', '腾讯', '阿里', '字节', 
               '百度', '小米', '华为', '苹果', '特斯拉', '谷歌', '微软', 'Meta', 'Anthropic']

# 科技类宽松关键词（用于补充）
tech_keywords = ai_keywords + [
    '科技', '互联网', '手机', '电脑', '软件', '硬件', '算法', '数据', '云',
    'SaaS', '融资', '创业', '投资', '上市', '财报', '产品', 'App', '应用',
    '数码', '5G', '6G', '新能源', '电动车', '电商', '支付', '金融', '区块链',
    '游戏', '社交', '视频', '直播', '短视频', '内容', '版权', '隐私', '安全',
    'iPhone', 'Android', 'Windows', 'Mac', 'Linux', '三星', '索尼', '任天堂',
    'Netflix', 'Spotify', 'Uber', 'Airbnb', 'TikTok', 'YouTube', 'Twitter',
]

def parse_items(content):
    \"\"\"从 RSS XML 解析今天的新闻\"\"\"
    items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
    results = []
    for item in items:
        title_match = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item, re.DOTALL)
        link_match = re.search(r'<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>', item, re.DOTALL)
        pub_match = re.search(r'<pubDate>([^<]+)', item)
        desc_match = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
        
        if not title_match:
            continue
        
        title = html_mod.unescape(title_match.group(1).strip())
        link = link_match.group(1).strip() if link_match else ''
        desc = html_mod.unescape(desc_match.group(1).strip())[:500] if desc_match else ''
        pub_date = pub_match.group(1).strip() if pub_match else ''
        
        # 只要今天的
        is_today = (today_en in pub_date) or (today_cn in pub_date)
        if not is_today:
            continue
        
        results.append({'title': title, 'url': link, 'desc': desc})
    return results

def match_keywords(item, keywords):
    text = item['title'] + item.get('desc', '')
    return any(kw.lower() in text.lower() for kw in keywords)

# 收集所有源的今日新闻
all_today_news = []
seen_titles = set()

for source_name, feed_url in rss_sources:
    try:
        result = subprocess.run(['curl', '-sL', '--max-time', '10', feed_url], 
                              capture_output=True, text=True, timeout=15)
        content = result.stdout
        
        if '<item>' not in content:
            print(f'  ⚠️ {source_name} 被反爬或无数据', file=sys.stderr)
            continue
        
        items = parse_items(content)
        added = 0
        for item in items:
            if item['title'] in seen_titles:
                continue
            seen_titles.add(item['title'])
            item['source'] = source_name
            all_today_news.append(item)
            added += 1
        
        print(f'  ✅ {source_name}: {added} 条今日新闻', file=sys.stderr)
    except Exception as e:
        print(f'  ⚠️ {source_name} 抓取失败: {e}', file=sys.stderr)

if not all_today_news:
    print('❌ 今天没有任何新闻（RSS可能在维护）')
    sys.exit(1)

# 第一轮：AI关键词匹配
ai_news = [n for n in all_today_news if match_keywords(n, ai_keywords)]
print(f'  🤖 AI新闻: {len(ai_news)} 条', file=sys.stderr)

# 第二轮：科技关键词匹配（排除已选AI的）
tech_news = [n for n in all_today_news if n not in ai_news and match_keywords(n, tech_keywords)]
print(f'  💻 科技新闻: {len(tech_news)} 条', file=sys.stderr)

# 第三轮：剩余全部（兜底）
other_news = [n for n in all_today_news if n not in ai_news and n not in tech_news]

# 合并：AI优先 → 科技补充 → 兜底补充
final_news = ai_news[:target_count]
if len(final_news) < target_count:
    final_news += tech_news[:target_count - len(final_news)]
if len(final_news) < target_count:
    final_news += other_news[:target_count - len(final_news)]

print(f'  📰 最终选取: {len(final_news)} 条 (目标{target_count}条)', file=sys.stderr)

if not final_news:
    print('❌ 没有获取到新闻')
    sys.exit(1)

import re as _re
_td = os.environ.get('TEMP_DIR', '/tmp')

for i, item in enumerate(final_news):
    title = item['title']
    url = item['url']
    desc = item.get('desc', '')
    if len(title) > 35:
        title = title[:35] + '...'
    desc_file = os.path.join(_td, f'desc_{i}.txt')
    clean_text = _re.sub(r'<[^>]+>', ' ', desc)
    clean_text = _re.sub(r'\s+', ' ', clean_text).strip()
    with open(desc_file, 'w') as f:
        f.write(clean_text[:3000])
    print(f'{i}|{title}|{url}')
" > "$TEMP_DIR/news_titles.txt" 2>&1 || {
        echo "❌ 新闻提取失败"
        exit 1
    }
    
    sed -i '/^$/d' "$TEMP_DIR/news_titles.txt"
    
    local count=$(wc -l < "$TEMP_DIR/news_titles.txt")
    echo "✅ 提取到 $count 条新闻"
    
    [ "$count" -gt 0 ] || { echo "❌ 没有获取到新闻"; exit 1; }
}

# ========== 第二步: 生成AI摘要 ==========
generate_summaries() {
    echo "📝 步骤2: 生成AI摘要..."
    
    > "$TEMP_DIR/summaries.json"
    
    local idx=0
    while IFS='|' read -r num title url; do
        [ -z "$title" ] && continue
        
        echo "   正在处理: ${title:0:30}..."
        
        local summary=""
        local desc_file="$TEMP_DIR/desc_${num}.txt"
        
        # 方案1: 用 OpenRouter Gemini 生成摘要
        if [ -f "$desc_file" ] && [ "$(wc -c < "$desc_file")" -gt 50 ]; then
            local desc_text=$(cat "$desc_file" | head -c 3000)
            local or_key="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"
            local prompt="请为以下新闻生成一个 2-3 句话的精简摘要（50字以内）：新闻标题：$title，新闻内容：$desc_text。要求：直接输出，不要多余解释"
            
            for attempt in 1 2 3; do
                local payload=$(jq -n --arg p "$prompt" '{"model":"google/gemini-2.0-flash-lite-001","messages":[{"role":"user","content":$p}],"max_tokens":200}')
                local response=$(curl -s --connect-timeout 10 -m 30 -X POST "https://openrouter.ai/api/v1/chat/completions" \
                    -H "Authorization: Bearer $or_key" \
                    -H "Content-Type: application/json" \
                    -d "$payload")
                
                summary=$(echo "$response" | jq -r '.choices[0].message.content // ""')
                local error_code=$(echo "$response" | jq -r '.error.code // ""')
                
                if [ -n "$summary" ] && [ "$summary" != "" ]; then
                    echo "   ✅ 摘要成功"
                    break
                elif [ "$error_code" = "429" ]; then
                    echo "   ⏳ 限流，等待重试 ($attempt/3)..."
                    sleep $((attempt * 5))
                else
                    echo "   ⚠️ 摘要失败，使用fallback"
                    summary=""
                    break
                fi
            done
        fi
        
        # 方案2: ollama 本地模型
        if [ -z "$summary" ] && command -v ollama &>/dev/null; then
            summary=$(ollama generate --model llama3 --prompt "用60字以内总结：$title" 2>/dev/null | head -1) || true
        fi
        
        # 方案3: 截取标题
        if [ -z "$summary" ]; then
            summary="${title:0:60}"
            [ ${#title} -gt 60 ] && summary="${summary}..."
        fi
        
        echo "$idx|$title|$summary|$url" >> "$TEMP_DIR/summaries.json"
        idx=$((idx + 1))
        
    done < "$TEMP_DIR/news_titles.txt"
    
    local count=$(wc -l < "$TEMP_DIR/summaries.json")
    echo "✅ 生成摘要完成 ($count 条)"
    
    # 保存到缓存文件
    local cache_file="/root/.openclaw/workspace/news_cache.json"
    > "$cache_file"
    echo "[" >> "$cache_file"
    local first=1
    while IFS='|' read -r idx title summary url; do
        [ -z "$title" ] && continue
        [ "$first" -eq 1 ] && first=0 || echo "," >> "$cache_file"
        title_escaped=$(echo "$title" | sed 's/"/\\"/g')
        summary_escaped=$(echo "$summary" | sed 's/"/\\"/g')
        printf '  {"title": "%s", "summary": "%s", "url": "%s"}' "$title_escaped" "$summary_escaped" "$url" >> "$cache_file"
    done < "$TEMP_DIR/summaries.json"
    echo "" >> "$cache_file"
    echo "]" >> "$cache_file"
    echo "💾 已保存到缓存: $cache_file"
}

# ========== 第三步: 生成图片卡片 ==========
generate_images() {
    echo "🖼️ 步骤3: 生成封面和内容卡片..."
    
    # HTML 模板 (淡入淡出动画效果 + 大标题)
    cat > "$TEMP_DIR/card_template.html" << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', sans-serif;
            width: 1080px; height: 1920px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 50%, #1a0a2e 100%);
            color: white;
            overflow: hidden;
            padding-top: 180px;
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
        /* 扫描线 */
        .scanline {
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.3), transparent);
            animation: scan 3s linear infinite;
            pointer-events: none;
        }
        @keyframes scan {
            0% { top: -4px; }
            100% { top: 1924px; }
        }
        /* 底部渐变 */
        .bottom-gradient {
            position: absolute;
            bottom: 0; left: 0; right: 0;
            height: 300px;
            background: linear-gradient(to top, rgba(10, 10, 26, 0.9), transparent);
            pointer-events: none;
        }
        .header-title {
            text-align: center;
            font-size: 90px;
            font-weight: 900;
            letter-spacing: 12px;
            background: linear-gradient(90deg, #00F5FF, #00FF94, #8A2BE2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(0, 245, 255, 0.5);
            z-index: 10;
        }
        .container {
            text-align: center;
            padding: 60px;
            width: 100%;
            margin-top: 80px;
            z-index: 10;
        }
        .title {
            font-size: 64px;
            font-weight: bold;
            line-height: 1.3;
            margin: 80px 0 50px;
            max-width: 900px;
            opacity: 0;
            transform: translateY(30px);
            animation: fadeInUp 1s ease-out 0.5s forwards;
        }
        .summary {
            font-size: 48px;
            line-height: 1.6;
            max-width: 850px;
            margin: 40px auto 0;
            opacity: 0;
            transform: translateY(30px);
            animation: fadeInUp 1s ease-out 1.5s forwards;
            white-space: pre-line;
        }
        .footer {
            display: none;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
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
    <div class="header-title">DATE TYPE早报</div>
    <div class="container">
        <div class="title">TITLE</div>
        <div class="summary">SUMMARY</div>
    </div>
    <div class="footer">AI News Daily</div>
</body>
</html>
HTMLEOF
    
    local idx=0
    while IFS='|' read -r num title summary url; do
        [ -z "$title" ] && continue
        
        local safe_title="${title:0:35}"
        local safe_summary="${summary:0:120}"
        
        # 获取当前日期
        local current_date
        current_date=$(date +"%m月%d日")
        
        # 用 Python 做模板替换（避免 sed 特殊字符问题）
        echo "$safe_title" > "$TEMP_DIR/_title.txt"
        echo "$safe_summary" > "$TEMP_DIR/_summary.txt"
        python3 - "$TEMP_DIR" "$BG_GRADIENT_START" "$BG_GRADIENT_END" "$current_date" "$idx" << 'PYEOF'
import sys
td, bg_start, bg_end, date_str, idx = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
with open(f"{td}/card_template.html") as f:
    tpl = f.read()
with open(f"{td}/_title.txt") as f:
    title = f.read().strip()
with open(f"{td}/_summary.txt") as f:
    summary = f.read().strip()
tpl = tpl.replace("BG_START", bg_start)
tpl = tpl.replace("BG_END", bg_end)
tpl = tpl.replace("DATE", date_str)
tpl = tpl.replace("TYPE", "AI")
tpl = tpl.replace("TITLE", title, 1)
tpl = tpl.replace("SUMMARY", summary, 1)
with open(f"{td}/card_{idx}.html", "w") as f:
    f.write(tpl)
PYEOF
        
        # 使用 playwright 截取多帧 (带动画效果)
        if command -v node &>/dev/null && node -e "require('playwright')" 2>/dev/null; then
            echo "   📸 Playwright 截取 $idx ..."
            node -e "
            const { chromium } = require('playwright');
            (async () => {
                const browser = await chromium.launch();
                const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
                const htmlPath = '$TEMP_DIR/card_$idx.html';
                await page.goto('file://' + htmlPath, { waitUntil: 'networkidle', timeout: 30000 });
                
                for (let i = 0; i < 25; i++) {
                    await page.waitForTimeout(200);
                    await page.screenshot({ path: '$TEMP_DIR/card_${idx}_' + i + '.png' });
                }
                
                await browser.close();
                console.log('Done: $idx');
            })().catch(e => { console.error(e); process.exit(1); });
            " && echo "   ✅ $idx 多帧完成" || {
                echo "   ⚠️ $idx 多帧失败，使用单帧"
                generate_fallback_image "$idx"
            }
        else
            generate_fallback_image "$idx"
        fi
        
        idx=$((idx + 1))
    done < "$TEMP_DIR/summaries.json"
    
    echo "✅ 生成图片卡片完成"
}

# 使用 ImageMagick 生成漂亮卡片
generate_fallback_image() {
    local idx=$1
    echo "   🎨 生成卡片 $idx (ImageMagick)..."
    
    local title summary url
    read -r _ title summary url < <(sed -n "${idx}p" "$TEMP_DIR/summaries.json")
    
    [ -z "$title" ] && title="AI News"
    [ -z "$summary" ] && summary=""
    
    # 创建渐变背景
    convert -size 1080x1920 gradient:"$BG_GRADIENT_START-$BG_GRADIENT_END" \
        "$TEMP_DIR/card_${idx}_bg.png"
    
    # 添加标题 (使用 pango 渲染，透明背景)
    convert "$TEMP_DIR/card_${idx}_bg.png" \
        -gravity center -pointsize 60 -fill white \
        -annotate +0-300 "$title" \
        "$TEMP_DIR/card_${idx}_tmp1.png"
    
    # 添加摘要
    convert "$TEMP_DIR/card_${idx}_tmp1.png" \
        -gravity center -pointsize 36 -fill "#A5B4FC" \
        -annotate +0+50 "$summary" \
        "$TEMP_DIR/card_${idx}_tmp2.png"
    
    # 添加编号
    convert "$TEMP_DIR/card_${idx}_tmp2.png" \
        -gravity northwest -pointsize 32 -fill "#A5B4FC" \
        -annotate +40+40 "NO.$idx" \
        "$TEMP_DIR/card_${idx}_tmp3.png"
    
    # 添加角标
    convert "$TEMP_DIR/card_${idx}_tmp3.png" \
        -gravity southeast -pointsize 24 -fill white \
        -annotate +40+40 "AI News Daily" \
        "$TEMP_DIR/card_$idx.png"
    
    # 清理临时文件
    rm -f "$TEMP_DIR/card_${idx}_bg.png" "$TEMP_DIR/card_${idx}_tmp1.png" "$TEMP_DIR/card_${idx}_tmp2.png" "$TEMP_DIR/card_${idx}_tmp3.png"
}

# ========== 第四步: 生成配音 (可选) ==========
generate_voiceover() {
    echo "🎙️ 步骤4: 使用 Kokoro TTS 生成配音..."
    
    # 检查 python 和 kokoro
    if ! python3 -c "import kokoro" 2>/dev/null; then
        echo "⚠️ kokoro 未安装，跳过配音"
        return
    fi
    
    local voice="zm_yunyang"
    local total_duration=0
    
    # 为每条新闻生成配音
    local idx=0
    while IFS='|' read -r num title summary url; do
        [ -z "$title" ] && continue
        
        echo "   合成 [$((idx+1))]: ${title:0:20}..."
        
        # 拼接标题+摘要作为配音文本
        local speak_text="${title}。${summary}"
        
        # 限制长度避免太长
        if [ ${#speak_text} -gt 150 ]; then
            speak_text="${speak_text:0:150}"
        fi
        
        # 用 Python 调用 Kokoro
        python3 - "$speak_text" "$voice" "$TEMP_DIR/voice_${idx}.wav" << 'PYEOF'
import sys, soundfile as sf
from kokoro import KPipeline

text = sys.argv[1]
voice = sys.argv[2]
out_path = sys.argv[3]

pipeline = KPipeline(lang_code='z', repo_id='hexgrad/Kokoro-82M')
generator = pipeline(text, voice=voice)

for i, (gs, ps, audio) in enumerate(generator):
    if i == 0:
        sf.write(out_path, audio, 24000)
    else:
        # 追加后续片段
        import numpy as np
        prev, sr = sf.read(out_path)
        combined = np.concatenate([prev, audio])
        sf.write(out_path, combined, 24000)
PYEOF
        
        if [ -f "$TEMP_DIR/voice_${idx}.wav" ]; then
            local dur_raw=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_DIR/voice_${idx}.wav" 2>/dev/null)
                dur=${dur_raw%.*}
                # 向上取整：如果有小数部分就+1
                if [[ "$dur_raw" == *"."* ]]; then dur=$((dur + 1)); fi
            total_duration=$((total_duration + dur))
            echo "   ✅ ${dur}s"
        else
            echo "   ⚠️ 合成失败"
        fi
        
        idx=$((idx + 1))
    done < "$TEMP_DIR/summaries.json"
    
    local count=$(ls -1 "$TEMP_DIR"/voice_*.wav 2>/dev/null | wc -l)
    echo "✅ 配音完成: $count 条, 总时长 ${total_duration}s"
}

# ========== 第五步: 合成视频 ==========
compose_video() {
    echo "🎬 步骤5: 合成视频 (配音同步)..."
    
    if ! command -v ffmpeg &>/dev/null; then
        echo "❌ ffmpeg 未安装"
        exit 1
    fi
    
    local multi_frames=$(ls -1 "$TEMP_DIR"/card_*_0.png 2>/dev/null | wc -l)
    
    if [ "$multi_frames" -gt 0 ]; then
        local news_count=$multi_frames
        
        # 创建图片序列：每张图片持续时间 = 配音时长（单次 ffmpeg 调用，避免 MP4 拼接时间戳漂移）
        > "$TEMP_DIR/img_list.txt"
        for idx in $(seq 0 $((news_count - 1))); do
            local dur=5
            if [ -f "$TEMP_DIR/voice_${idx}.wav" ]; then
                dur_raw=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_DIR/voice_${idx}.wav" 2>/dev/null)
                dur=${dur_raw%.*}
                # 向上取整：如果有小数部分就+1
                if [[ "$dur_raw" == *"."* ]]; then dur=$((dur + 1)); fi
                [ -z "$dur" ] || [ "$dur" -lt 3 ] && dur=5
            fi
            
            local last_frame=24
            [ ! -f "$TEMP_DIR/card_${idx}_${last_frame}.png" ] && last_frame=0
            
            echo "   新闻$((idx+1)): ${dur}s"
            echo "file '$TEMP_DIR/card_${idx}_${last_frame}.png'" >> "$TEMP_DIR/img_list.txt"
            echo "duration $dur" >> "$TEMP_DIR/img_list.txt"
        done
        
        # 末尾多停2秒
        local last_idx=$((news_count - 1))
        local last_frame=24
        [ ! -f "$TEMP_DIR/card_${last_idx}_${last_frame}.png" ] && last_frame=0
        echo "file '$TEMP_DIR/card_${last_idx}_${last_frame}.png'" >> "$TEMP_DIR/img_list.txt"
        echo "duration 2" >> "$TEMP_DIR/img_list.txt"
        
        # 用 concat demuxer 图片模式一次性生成（不会有 MP4 时间戳问题）
        ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/img_list.txt"             -vsync vfr -c:v libx264 -pix_fmt yuv420p -r 25             -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"             "$TEMP_DIR/video_no_audio.mp4" 2>/dev/null || {
            echo "❌ 视频合成失败"
            exit 1
        }
        
        local vid_dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_DIR/video_no_audio.mp4" 2>/dev/null | cut -d. -f1)
        echo "✅ 视频合成完成 (${vid_dur}s)"
    else
        # 备用：单帧图片 + 淡入淡出
        local cards=($(ls -1 "$TEMP_DIR"/card_*.png 2>/dev/null | sort -V || true))
        local fade_duration=1
        local idx=0
        
        for card in "${cards[@]}"; do
            ffmpeg -y -loop 1 -i "$card"                 -vf "fade=t=in:st=0:d=$fade_duration,fade=t=out:st=$((DURATION_PER_NEWS - fade_duration)):d=$fade_duration,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"                 -t "$DURATION_PER_NEWS" -c:v libx264 -pix_fmt yuv420p -crf 23                 "$TEMP_DIR/card_${idx}.mp4" 2>/dev/null
            idx=$((idx + 1))
        done
        
        > "$TEMP_DIR/concat.txt"
        for i in $(seq 0 $((idx - 1))); do
            echo "file '$TEMP_DIR/card_${i}.mp4'" >> "$TEMP_DIR/concat.txt"
        done
        
        ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/concat.txt" -c copy "$TEMP_DIR/video_no_audio.mp4" 2>/dev/null
    fi
    
    echo "✅ 视频合成完成"
}

# ========== 第六步: 添加背景音乐和配音 ==========
add_audio() {
    echo "🎵 步骤6: 添加配音和背景音乐..."
    
    local input_video="$TEMP_DIR/video_no_audio.mp4"
    local output_video="$OUTPUT_DIR/ai_news_$(date +%Y%m%d_%H%M%S).mp4"
    
    # 获取视频时长
    local video_duration
    video_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_video" 2>/dev/null | cut -d. -f1) || video_duration=40
    
    # 检查是否有配音文件
    local voice_files=($(ls -1 "$TEMP_DIR"/voice_*.wav 2>/dev/null | sort -V))
    local has_voiceover=0
    
    if [ ${#voice_files[@]} -gt 0 ]; then
        echo "   拼接 ${#voice_files[@]} 条配音..."
        
        # 拼接所有配音
        > "$TEMP_DIR/voice_concat.txt"
        for vf in "${voice_files[@]}"; do
            echo "file '$vf'" >> "$TEMP_DIR/voice_concat.txt"
        done
        
        ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/voice_concat.txt" \
            -c:a pcm_s16le "$TEMP_DIR/voice_all.wav" 2>/dev/null && has_voiceover=1
        
        if [ "$has_voiceover" -eq 1 ]; then
            local voice_dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_DIR/voice_all.wav" 2>/dev/null | cut -d. -f1)
            echo "   ✅ 配音总时长: ${voice_dur}s"
        fi
    fi
    
    if [ "$has_voiceover" -eq 1 ]; then
        # 配音 + BGM 混合
        if [ -f "$TEMP_DIR/bgm.mp3" ] && [ -s "$TEMP_DIR/bgm.mp3" ]; then
            echo "   混合配音 + BGM (BGM音量: ${BGM_VOLUME})..."
            
            local bgm_duration
            bgm_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_DIR/bgm.mp3" 2>/dev/null | cut -d. -f1) || bgm_duration=30
            local loop_count=$(((video_duration + bgm_duration - 1) / bgm_duration))
            
            # 方案: 视频 + 配音(主) + BGM(低音量)
            ffmpeg -y \
                -i "$input_video" \
                -i "$TEMP_DIR/voice_all.wav" \
                -stream_loop $loop_count -i "$TEMP_DIR/bgm.mp3" \
                -filter_complex "[1:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[voice];[2:a]volume=${BGM_VOLUME}[bgm];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]" \
                -map 0:v -map "[aout]" \
                -c:v copy -c:a aac -b:a 192k \
                "$output_video" 2>&1 | tail -3 || {
                echo "   ⚠️ 混合失败，仅使用配音"
                ffmpeg -y -i "$input_video" -i "$TEMP_DIR/voice_all.wav" \
                    -c:v copy -c:a aac -b:a 192k -shortest "$output_video" 2>/dev/null
            }
        else
            echo "   仅配音，无BGM..."
            ffmpeg -y -i "$input_video" -i "$TEMP_DIR/voice_all.wav" \
                -c:v copy -c:a aac -b:a 192k -shortest "$output_video" 2>/dev/null
        fi
    else
        # 无配音，仅 BGM
        if [ -f "$TEMP_DIR/bgm.mp3" ] && [ -s "$TEMP_DIR/bgm.mp3" ]; then
            echo "   仅BGM (无配音)..."
            local bgm_duration
            bgm_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_DIR/bgm.mp3" 2>/dev/null | cut -d. -f1) || bgm_duration=30
            local loop_count=$(((video_duration + bgm_duration - 1) / bgm_duration))
            
            ffmpeg -y -stream_loop $loop_count -i "$TEMP_DIR/bgm.mp3" \
                -i "$input_video" \
                -c:v copy -c:a aac -b:a 192k \
                -map 0:a -map 1:v \
                -shortest "$output_video" 2>&1 | tail -3 || {
                cp "$input_video" "$output_video"
            }
        else
            cp "$input_video" "$output_video"
        fi
    fi
    
    echo "✅ 音频处理完成"
}

# ========== 第七步: 清理和输出 ==========
finish() {
    echo "📤 步骤7: 输出最终视频..."
    
    local output_file
    output_file=$(ls -1t "$OUTPUT_DIR"/ai_news_*.mp4 2>/dev/null | head -1)
    
    if [ -n "$output_file" ] && [ -f "$output_file" ]; then
        local size
        size=$(du -h "$output_file" | cut -f1)
        
        echo ""
        echo "🎉 视频生成完成！"
        echo "📁 输出文件: $output_file"
        echo "📊 文件大小: $size"
    else
        echo "❌ 视频生成失败"
        exit 1
    fi
    
    # 清理临时文件
    if [ "$1" != "keep" ]; then
        echo "🧹 清理临时文件..."
        rm -rf "$TEMP_DIR"
    fi
}

# ========== 帮助信息 ==========
usage() {
    cat << EOF
用法: $0 [选项]

选项:
    --help          显示帮助
    --keep          保留临时文件
    --news-count N  新闻数量 (默认: 5)
    --duration N    每条新闻秒数 (默认: 8)

示例:
    $0 --news-count 10 --duration 6
EOF
}

# ========== 主流程 ==========
main() {
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help) usage; exit 0 ;;
            --keep) KEEP_TEMP=1 ;;
            --news-count) NEWS_COUNT="$2"; shift ;;
            --duration) DURATION_PER_NEWS="$2"; shift ;;
            *) echo "未知选项: $1"; usage; exit 1 ;;
        esac
        shift
    done
    
    echo "========================================"
    echo "   每日AI新闻短视频生成器"
    echo "   输出: 9:16 竖屏视频 (抖音/视频号)"
    echo "========================================"
    echo ""
    
    # 执行
    check_dependencies
    init
    fetch_ai_news_from_cache
    generate_summaries
    generate_images
    generate_voiceover
    compose_video
    add_audio
    finish "${KEEP_TEMP:-}"
    
    echo ""
    echo "✨ 全部完成！"
}

main "$@"