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
import subprocess


# === 配置 ===
MAX_AGE_HOURS = 48  # 只保留最近 48 小时的新闻
MAX_RETRIES = 3     # RSS 抓取最大重试次数
RETRY_DELAY = 2     # 重试间隔秒数
# LLM 打分配置
LLM_SCORING_ENABLED = os.getenv("PODCAST_LLM_SCORING", "false").lower() == "true"
LLM_API_URL = os.getenv("AINAIBA_API_URL", "https://api-xai.ainaibahub.com/v1")
LLM_API_KEY = os.getenv("AINAIBA_API_KEY", "")
LLM_MODEL = "gpt-4.1-mini"  # 使用便宜的模型做打分
# news-aggregator 集成
NEWS_AGGREGATOR_SCRIPT = os.path.expanduser("~/.hermes/skills/news-aggregator-skill/scripts/fetch_news.py")
NEWS_AGGREGATOR_SOURCES = "36kr,wallstreetcn,weibo,github"  # 中文+投资相关源


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
    # 科技综合
    {"name": "爱范儿", "url": "https://www.ifanr.com/feed", "priority": 2, "category": "tech"},
    {"name": "少数派", "url": "https://sspai.com/feed", "priority": 1, "category": "tech"},
    {"name": "钛媒体", "url": "https://www.tmtpost.com/rss", "priority": 2, "category": "tech"},
    # 英文 AI 源（作为补充）
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "priority": 2, "category": "ai"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "priority": 2, "category": "ai"},
    # 注: 机器之心/量子位/虎嗅/雪球/第一财经/华尔街见闻/格隆汇 RSS 已失效
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


def fetch_from_news_aggregator(sources: str = NEWS_AGGREGATOR_SOURCES, limit: int = 10) -> list:
    """从 news-aggregator-skill 获取新闻数据"""
    if not os.path.exists(NEWS_AGGREGATOR_SCRIPT):
        print("  ⚠️ news-aggregator 脚本不存在，跳过", file=sys.stderr)
        return []
    
    items = []
    for source in sources.split(","):
        source = source.strip()
        if not source:
            continue
        
        try:
            result = subprocess.run(
                ["python3", NEWS_AGGREGATOR_SCRIPT, "--source", source, "--limit", str(limit), "--no-save"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                print(f"  ⚠️ news-aggregator {source} 失败: {result.stderr[:100]}", file=sys.stderr)
                continue
            
            # 解析 JSON 输出
            import json
            data = json.loads(result.stdout)
            
            for item in data:
                items.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", item.get("title", "")),  # 有些源没有摘要
                    "url": item.get("url", ""),
                    "source": f"news-agg:{item.get('source', source)}",
                    "category": "invest" if source in ["wallstreetcn"] else "ai",
                    "priority": 2,  # news-aggregator 源的默认优先级
                    "pub_date": item.get("time", ""),
                })
            
            print(f"  ✅ news-aggregator:{source}: {len(data)} 条", file=sys.stderr)
            
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ news-aggregator:{source} 超时", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"  ⚠️ news-aggregator:{source} JSON解析失败", file=sys.stderr)
        except Exception as e:
            print(f"  ❌ news-aggregator:{source}: {e}", file=sys.stderr)
    
    return items


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
    score += invest_hits * 5  # 投资关键词权重提高到 5

    # AI/投资交叉最优；纯大会通稿和泛科技新闻降权。
    if ai_hits and invest_hits:
        score += 35
    elif invest_hits:
        score += 18
    elif ai_hits:
        score += 8

    business_terms = ["营收", "利润", "亏损", "赚钱", "财报", "估值", "商业模式", "成本", "毛利", "订单", "客户", "订阅", "融资"]
    business_hits = sum(1 for kw in business_terms if kw.lower() in text.lower())
    score += business_hits * 6

    press_release_terms = ["大会", "演讲", "论坛", "分享题目", "嘉宾", "整理编辑"]
    press_hits = sum(1 for kw in press_release_terms if kw.lower() in text.lower())
    score -= press_hits * 8

    promo_terms = ["提交报道", "寻求报道", "报名活动", "媒体合作", "投稿入口"]
    promo_hits = sum(1 for kw in promo_terms if kw.lower() in text.lower())
    score -= promo_hits * 18
    if promo_hits >= 2 or "让好项目" in item["title"]:
        score -= 40

    if item["category"] == "ai" and not ai_hits and not invest_hits:
        score -= 25

    # AI 原生源加分
    if item["category"] == "ai":
        score += 10
    
    # 投资源加分（news-aggregator 的财经源）
    if item["category"] == "invest":
        score += 15  # 投资源加分提高到 15
    
    # news-aggregator 来源加分（这些源更实时）
    if item["source"].startswith("news-agg"):
        score += 8  # news-aggregator 加分提高到 8

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
    parser.add_argument("--rss-only", action="store_true", help="仅使用RSS源")
    parser.add_argument("--agg-only", action="store_true", help="仅使用news-aggregator")
    args = parser.parse_args()

    print("📰 开始抓取新闻源...", file=sys.stderr)
    all_items = []
    
    # 1. 从 news-aggregator 获取数据（财经/投资源更丰富）
    if not args.rss_only:
        print("📰 从 news-aggregator 获取...", file=sys.stderr)
        agg_items = fetch_from_news_aggregator()
        all_items.extend(agg_items)
    
    # 2. 从 RSS 源获取数据（补充AI/科技源）
    if not args.agg_only:
        print("📰 从 RSS 源获取...", file=sys.stderr)
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
