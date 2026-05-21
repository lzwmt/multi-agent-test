#!/usr/bin/env python3
"""
AI 播客新闻抓取器
从中文科技/财经 RSS 源抓取今日新闻，输出格式化列表供 script-writer 使用。

用法：
  python3 fetch_podcast_news.py [--output news.json] [--count 10]

输出：JSON 文件，每条包含 title、summary、source、url
"""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import unescape
import time
import email.utils
import requests


# === 配置 ===
MAX_AGE_HOURS = 48  # 只保留最近 48 小时的新闻
MAX_RETRIES = 3     # RSS 抓取最大重试次数
RETRY_DELAY = 2     # 重试间隔秒数
# LLM 打分配置
LLM_SCORING_ENABLED = os.getenv("PODCAST_LLM_SCORING", "false").lower() == "true"
LLM_API_URL = os.getenv("AINAIBA_API_URL", "https://api-xai.ainaibahub.com/v1")
LLM_API_KEY = os.getenv("AINAIBA_API_KEY", "")
LLM_MODEL = "gpt-4.1-mini"  # 使用便宜的模型做打分


def parse_rss_date(date_str: str) -> datetime | None:
    """解析 RSS 日期格式，返回 datetime 对象"""
    if not date_str:
        return None
    
    # 常见 RSS 日期格式
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 2822: Tue, 20 May 2026 07:00:00 +0800
        "%a, %d %b %Y %H:%M:%S %Z",       # RFC 2822 with timezone name
        "%Y-%m-%dT%H:%M:%S%z",            # ISO 8601: 2026-05-20T07:00:00+08:00
        "%Y-%m-%dT%H:%M:%SZ",             # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",              # Simple format
    ]
    
    # 先尝试 email.utils 解析（RFC 2822 标准）
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed
    except (ValueError, TypeError):
        pass
    
    # 尝试各种格式
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def is_recent(date_str: str, max_hours: int = MAX_AGE_HOURS) -> bool:
    """检查日期是否在最近 max_hours 小时内"""
    if not date_str:
        return True  # 没有日期信息时保留（宁多勿少）
    
    pub_date = parse_rss_date(date_str)
    if not pub_date:
        return True  # 解析失败时保留
    
    # 确保有时区信息
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    age = now - pub_date
    return age < timedelta(hours=max_hours)

# === RSS 源配置 ===
FEEDS = [
    # AI 原生 / 高优先级
    {"name": "36氪-AI", "url": "https://36kr.com/feed", "priority": 3, "category": "ai"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "priority": 3, "category": "ai"},
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "priority": 3, "category": "ai"},
    # 科技综合
    {"name": "虎嗅", "url": "https://www.huxiu.com/rss/0.xml", "priority": 2, "category": "tech"},
    {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "priority": 2, "category": "tech"},
    {"name": "少数派", "url": "https://sspai.com/feed", "priority": 1, "category": "tech"},
    # 英文 AI 源（作为补充）
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "priority": 2, "category": "ai"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "priority": 2, "category": "ai"},
    # P1-5: 财经/投资源
    {"name": "雪球热帖", "url": "https://xueqiu.com/hots/topic/rss", "priority": 3, "category": "invest"},
    {"name": "第一财经", "url": "https://www.yicai.com/rss", "priority": 2, "category": "invest"},
    {"name": "华尔街见闻", "url": "https://wallstreetcn.com/rss", "priority": 2, "category": "invest"},
    {"name": "格隆汇", "url": "https://www.gelonghui.com/rss", "priority": 2, "category": "invest"},
    {"name": "金十数据", "url": "https://www.jin10.com/rss", "priority": 2, "category": "invest"},
    # 科技 + 投资交叉
    {"name": "极客公园", "url": "https://www.geekpark.net/rss", "priority": 2, "category": "tech"},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/rss", "priority": 2, "category": "tech"},
]

# AI/投资关键词
AI_KEYWORDS = [
    "AI", "人工智能", "大模型", "GPT", "LLM", "机器学习", "深度学习",
    "OpenAI", "Google", "谷歌", "百度", "文心", "通义", "Claude",
    "芯片", "GPU", "算力", "训练", "推理", "Agent", "智能体",
    "开源模型", "Llama", "DeepSeek", "千问", "智谱", "Anthropic",
    "机器人", "自动驾驶", "多模态", "Transformer", " diffusion",
]

INVEST_KEYWORDS = [
    "投资", "基金", "股票", "理财", "收益", "亏损", "牛市", "熊市",
    "纳斯达克", "标普", "A股", "港股", "美股", "定投", "ETF",
    "估值", "融资", "IPO", "上市", "市值", "财报", "盈利",
    "央行", "利率", "通胀", "GDP", "监管", "政策",
]


def fetch_feed(feed_info: dict) -> list:
    """抓取单个 RSS 源"""
    name = feed_info["name"]
    url = feed_info["url"]

    # P0-4: 带重试的抓取
    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                ["curl", "-sS", "--max-time", "15", "-L", url],
                capture_output=True, timeout=20
            )
            if result.returncode != 0:
                if attempt < MAX_RETRIES - 1:
                    print(f"  ⚠️ {name}: curl 失败，{RETRY_DELAY}s 后重试 ({attempt+1}/{MAX_RETRIES})", file=sys.stderr)
                    time.sleep(RETRY_DELAY)
                    continue
                print(f"  ❌ {name}: curl 失败，已重试 {MAX_RETRIES} 次", file=sys.stderr)
                return []

            raw = result.stdout.decode("utf-8", errors="ignore")
            root = ET.fromstring(raw)

            items = []
            # 支持 RSS 2.0 和 Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            # RSS 2.0
            for item in root.findall(".//item"):
                title = item.findtext("title", "").strip()
                desc = item.findtext("description", "").strip()
                link = item.findtext("link", "").strip()
                # P0-3: 提取发布日期
                pub_date = item.findtext("pubDate", "") or item.findtext("dc:date", "")
                if title and is_recent(pub_date):
                    items.append({
                        "title": unescape(title),
                        "summary": clean_html(unescape(desc))[:300],
                        "url": link,
                        "source": name,
                        "category": feed_info["category"],
                        "priority": feed_info["priority"],
                        "pub_date": pub_date,
                    })

            # Atom
            if not items:
                for entry in root.findall(".//atom:entry", ns):
                    title = entry.findtext("atom:title", "", ns).strip()
                    summary = entry.findtext("atom:summary", "", ns).strip()
                    link_el = entry.find("atom:link", ns)
                    link = link_el.get("href", "") if link_el is not None else ""
                    # P0-3: 提取发布日期
                    pub_date = entry.findtext("atom:updated", "", ns) or entry.findtext("atom:published", "", ns)
                    if title and is_recent(pub_date):
                        items.append({
                            "title": unescape(title),
                            "summary": clean_html(unescape(summary))[:300],
                            "url": link,
                            "source": name,
                            "category": feed_info["category"],
                            "priority": feed_info["priority"],
                            "pub_date": pub_date,
                        })

            print(f"  ✅ {name}: {len(items)} 条", file=sys.stderr)
            return items

        except ET.ParseError as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠️ {name}: XML 解析错误，重试 ({attempt+1}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(RETRY_DELAY)
                continue
            print(f"  ❌ {name}: XML 解析失败: {e}", file=sys.stderr)
            return []
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠️ {name}: {e}，重试 ({attempt+1}/{MAX_RETRIES})", file=sys.stderr)
                time.sleep(RETRY_DELAY)
                continue
            print(f"  ❌ {name}: {e}", file=sys.stderr)
            return []
    
    return []


def clean_html(text: str) -> str:
    """清理 HTML 标签和无用内容"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(点击查看|阅读原文|查看全文|了解更多).*?$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_item(item: dict) -> float:
    """给新闻打分：AI 相关 > 投资相关 > 通用科技"""
    text = item["title"] + " " + item["summary"]
    score = item["priority"] * 10  # 基础分

    # AI 关键词命中
    ai_hits = sum(1 for kw in AI_KEYWORDS if kw.lower() in text.lower())
    score += ai_hits * 5

    # 投资关键词命中
    invest_hits = sum(1 for kw in INVEST_KEYWORDS if kw.lower() in text.lower())
    score += invest_hits * 3

    # AI 原生源加分
    if item["category"] == "ai":
        score += 15

    # P1-6: LLM 辅助打分
    if LLM_SCORING_ENABLED and LLM_API_KEY:
        llm_score = llm_score_item(item)
        score += llm_score * 2  # LLM 分数权重 x2

    return score


def llm_score_item(item: dict) -> float:
    """P1-6: 用 LLM 辅助打分，评估新闻的相关性、新颖度、深度"""
    prompt = f"""你是一个AI播客的选题编辑。请评估以下新闻对于"AI × 投资"主题播客的价值。

新闻标题：{item['title']}
新闻摘要：{item['summary'][:200]}
来源：{item['source']}

请从1-10打分，考虑：
1. 与AI/投资主题的相关性（权重40%）
2. 新颖度/时效性（权重30%）
3. 深度/可讨论性（权重30%）

只返回数字分数，不要解释。"""
    
    try:
        response = requests.post(
            f"{LLM_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,
                "temperature": 0.3
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            # 提取数字
            match = re.search(r'\d+', content)
            if match:
                score = int(match.group())
                return min(max(score, 1), 10)  # 限制在 1-10
    except Exception as e:
        print(f"  ⚠️ LLM 打分失败: {e}", file=sys.stderr)
    
    return 0


def deduplicate(items: list) -> list:
    """按标题去重"""
    seen_titles = set()
    result = []
    for item in items:
        # 简单去重：标题前 20 字符
        key = item["title"][:20].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            result.append(item)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI 播客新闻抓取器")
    parser.add_argument("--output", "-o", default="/root/.openclaw/workspace/ai-podcast/output/today_news.json")
    parser.add_argument("--count", "-n", type=int, default=8)
    args = parser.parse_args()

    print("📰 开始抓取新闻源...", file=sys.stderr)
    all_items = []
    for feed in FEEDS:
        items = fetch_feed(feed)
        all_items.extend(items)

    print(f"\n📊 总计 {len(all_items)} 条原始新闻", file=sys.stderr)

    # 去重
    all_items = deduplicate(all_items)
    print(f"📊 去重后 {len(all_items)} 条", file=sys.stderr)

    # 打分排序
    for item in all_items:
        item["score"] = score_item(item)
    all_items.sort(key=lambda x: x["score"], reverse=True)

    # 取 top N
    top_items = all_items[:args.count]

    # 输出格式化列表（给 script-writer 用）
    print(f"\n🎯 Top {len(top_items)} 条:", file=sys.stderr)
    for i, item in enumerate(top_items):
        print(f"  {i+1}. [{item['source']}] {item['title'][:60]} (score: {item['score']:.0f})", file=sys.stderr)

    # 写入 JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(top_items, f, ensure_ascii=False, indent=2)

    # 同时输出纯文本格式（方便直接喂给 script-writer）
    text_output = args.output.replace(".json", ".txt")
    with open(text_output, "w", encoding="utf-8") as f:
        for i, item in enumerate(top_items):
            f.write(f"{i+1}. [{item['source']}] {item['title']}\n")
            if item["summary"]:
                f.write(f"   摘要: {item['summary'][:150]}\n")
            f.write("\n")

    print(f"\n✅ 输出: {args.output}", file=sys.stderr)
    print(f"✅ 文本: {text_output}", file=sys.stderr)

    # 同时输出到 stdout（方便管道使用）
    print(json.dumps(top_items, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
