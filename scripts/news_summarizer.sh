#!/bin/bash
# 新闻摘要生成脚本

NEWS_URLS_FILE="/root/.openclaw/workspace/news_urls.json"
NEWS_CACHE_FILE="/root/.openclaw/workspace/news_cache.json"
GEMINI_API_KEY="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"
API_URL="https://openrouter.ai/api/v1/chat/completions"

echo "=================================================="
echo "   新闻摘要自动生成工具"
echo "=================================================="

if [ ! -f "$NEWS_URLS_FILE" ]; then
    echo "❌ 找不到 $NEWS_URLS_FILE"
    exit 1
fi

# 读取新闻数量
count=$(jq length "$NEWS_URLS_FILE")
echo "📥 开始处理 $count 条新闻..."

# 初始化结果数组
echo "[]" > "$NEWS_CACHE_FILE"

for ((i=0; i<count; i++)); do
    title=$(jq -r ".[$i].title" "$NEWS_URLS_FILE")
    url=$(jq -r ".[$i].url" "$NEWS_URLS_FILE")
    
    echo ""
    echo "[$((i+1))/$count] ${title:0:30}..."
    
    # 获取文章内容 (用 36kr 的 article-content 类)
    content=$(curl -s -A "Mozilla/5.0" --connect-timeout 10 -m 20 "$url" | \
        pup '.article-content text{}' 2>/dev/null | \
        head -c 6000 | tr '\n' ' ' | sed 's/  */ /g')
    
    if [ -z "$content" ]; then
        # 尝试 markdown-body
        content=$(curl -s -A "Mozilla/5.0" --connect-timeout 10 -m 20 "$url" | \
            pup '.markdown-body text{}' 2>/dev/null | \
            head -c 6000 | tr '\n' ' ' | sed 's/  */ /g')
    fi
    
    if [ -z "$content" ]; then
        echo "   ❌ 内容获取失败"
        summary="获取失败"
    else
        echo "   内容长度：${#content}"
        
        # 生成摘要
        prompt="请为以下新闻生成一个 2-3 句话的精简摘要（50字以内）：新闻标题：$title，新闻内容：$content。要求：直接输出，不要多余解释"
        
        jq -n --arg p "$prompt" '{"model":"google/gemini-2.0-flash-001","messages":[{"role":"user","content":$p}],"max_tokens":200}' > /tmp/payload.json
        
        response=$(curl -s --connect-timeout 10 -m 60 -X POST "$API_URL" \
            -H "Authorization: Bearer $GEMINI_API_KEY" \
            -H "Content-Type: application/json" \
            -d @/tmp/payload.json)
        
        summary=$(echo "$response" | jq -r '.choices[0].message.content // "LLM 失败"')
        
        if [ "$summary" != "LLM 失败" ] && [ -n "$summary" ]; then
            echo "   ✅ 摘要：${summary:0:50}..."
        else
            echo "   ❌ 摘要生成失败"
            echo "   API 响应：${response:0:100}"
            summary="LLM 失败"
        fi
    fi
    
    # 添加到结果
    tmp=$(mktemp)
    jq --arg t "$title" --arg s "$summary" '. + [{"title":$t,"summary":$s}]' "$NEWS_CACHE_FILE" > "$tmp" && mv "$tmp" "$NEWS_CACHE_FILE"
    
    sleep 2
done

echo ""
echo "✅ 完成！已保存到：$NEWS_CACHE_FILE"
