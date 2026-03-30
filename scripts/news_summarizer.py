#!/usr/bin/env python3
"""
新闻摘要生成脚本
Python 抓取网页 + os.popen 调用 API
"""

import json
import os
import sys
import time
import requests
from bs4 import BeautifulSoup

NEWS_URLS_FILE = "/root/.openclaw/workspace/news_urls.json"
NEWS_CACHE_FILE = "/root/.openclaw/workspace/news_cache.json"

def fetch_article(url):
    """获取文章内容"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = 'utf-8'
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        article = soup.select_one('.article-content') or soup.select_one('.markdown-body')
        
        if article:
            for tag in article.find_all(['script', 'style']):
                tag.decompose()
            text = article.get_text(separator=' ', strip=True)
            return text[:6000]
        return None
    except Exception as e:
        print(f"  获取失败：{e}")
        return None

def summarize_with_llm(title, content):
    """用 os.popen 调用 Bailian API"""
    prompt = f"请为以下新闻生成一个 50-80 字的摘要：新闻标题：{title}，新闻内容：{content[:5000]}。要求：50-80 字，直接输出"
    
    payload_file = "/tmp/bailian_payload.json"
    with open(payload_file, 'w', encoding='utf-8') as f:
        json.dump({
            "model": "qwen3.5-plus",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150
        }, f, ensure_ascii=False)
    
    cmd = 'curl -s --connect-timeout 10 -m 90 -X POST https://coding.dashscope.aliyuncs.com/v1/chat/completions -H "Authorization: Bearer sk-sp-464beb4134c346e7bfedde1f78049feb" -H "Content-Type: application/json" -d @/tmp/bailian_payload.json'
    
    try:
        output = os.popen(cmd).read()
        if output:
            resp = json.loads(output)
            if "choices" in resp and resp["choices"]:
                return resp["choices"][0]["message"]["content"].strip()
            elif "error" in resp:
                print(f"  API 错误：{resp['error'].get('message', '')}")
        else:
            print("  无响应")
    except Exception as e:
        print(f"  失败：{e}")
    
    return None

def main():
    print("=" * 50)
    print("   新闻摘要自动生成工具")
    print("=" * 50)
    
    if not os.path.exists(NEWS_URLS_FILE):
        print(f"\n❌ 找不到 {NEWS_URLS_FILE}")
        sys.exit(1)
    
    with open(NEWS_URLS_FILE, 'r') as f:
        news_list = json.load(f)
    
    print(f"\n📥 开始处理 {len(news_list)} 条新闻...")
    
    results = []
    for i, news in enumerate(news_list):
        title = news['title']
        url = news['url']
        
        print(f"\n[{i+1}/{len(news_list)}] {title[:30]}...")
        
        content = fetch_article(url)
        if content:
            print(f"   内容：{len(content)} 字")
            summary = summarize_with_llm(title, content)
            if summary:
                print(f"   ✅ 摘要：{summary[:50]}...")
            else:
                summary = "LLM 失败"
                print(f"   ❌ 摘要生成失败")
        else:
            summary = "获取失败"
            print(f"   ❌ 内容获取失败")
        
        results.append({"title": title, "summary": summary})
        
        # 每条新闻后等待 30 秒避免限流
        if i < len(news_list) - 1:
            print("   ⏳ 等待 30 秒避免限流...")
            time.sleep(30)
    
    with open(NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成！已保存到：{NEWS_CACHE_FILE}")

if __name__ == "__main__":
    main()