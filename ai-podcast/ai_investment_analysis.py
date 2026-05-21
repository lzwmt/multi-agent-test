#!/usr/bin/env python3
"""
AI 投资分析脚本
用 GPT 分析投资标的，生成分析结论供播客使用。

用法：
  python3 ai_investment_analysis.py --topic "英伟达财报"
  python3 ai_investment_analysis.py --ticker NVDA
  python3 ai_investment_analysis.py --news "特斯拉宣布FSD入华"

输出：JSON 格式的分析结果
"""

import json
import os
import sys
import requests
from datetime import datetime

# === 配置 ===
LLM_API_URL = os.getenv("AINAIBA_API_URL", "https://api-xai.ainaibahub.com/v1")
LLM_API_KEY = os.getenv("AINAIBA_API_KEY", "")
LLM_MODEL = "gpt-4.1"  # 用更强的模型做分析

OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/ai-podcast/output/analysis")


def analyze_topic(topic: str, context: str = "") -> dict:
    """用 AI 分析投资话题"""
    
    prompt = f"""你是一个用 AI 研究投资的程序员。请分析以下投资话题，生成播客脚本素材。

话题：{topic}
{f"背景信息：{context}" if context else ""}

请从以下角度分析：

1. **话题背景**（200字）
   - 这件事的来龙去脉
   - 为什么值得关注

2. **AI 分析过程**（300字）
   - 你会用什么 AI 工具来分析
   - 分析的具体步骤
   - 关键数据点

3. **核心发现**（200字）
   - 最重要的 2-3 个发现
   - 数据支撑

4. **个人观点**（200字）
   - 你的判断（有依据）
   - 风险提示

5. **可执行建议**（100字）
   - 听众听完能做什么
   - 具体行动步骤

6. **一句话总结**（50字）
   - 适合做节目金句

请用 JSON 格式输出，包含以上 6 个字段。"""

    if not LLM_API_KEY:
        print("❌ 未设置 AINAIBA_API_KEY", file=sys.stderr)
        return None
    
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
                "max_tokens": 2000,
                "temperature": 0.7
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # 尝试解析 JSON
            try:
                # 提取 JSON 部分（可能被 markdown 代码块包裹）
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                # 如果 JSON 解析失败，返回原始文本
                return {
                    "raw_text": content,
                    "parse_error": "JSON 解析失败，返回原始文本"
                }
        else:
            print(f"❌ API 请求失败: {response.status_code}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"❌ 分析失败: {e}", file=sys.stderr)
        return None


def analyze_ticker(ticker: str) -> dict:
    """分析具体股票/基金"""
    topic = f"分析股票/基金：{ticker}"
    context = f"请分析 {ticker} 的投资价值，包括基本面、技术面、风险点。"
    return analyze_topic(topic, context)


def analyze_news(news: str) -> dict:
    """分析新闻事件的投资影响"""
    topic = f"新闻事件：{news}"
    context = "请分析这条新闻对投资市场的影响，包括受益/受损板块、投资机会、风险点。"
    return analyze_topic(topic, context)


def save_analysis(analysis: dict, topic: str) -> str:
    """保存分析结果"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = topic[:30].replace("/", "_").replace(" ", "_")
    filename = f"{timestamp}_{safe_topic}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    return filepath


def format_for_podcast(analysis: dict) -> str:
    """将分析结果格式化为播客脚本片段"""
    if "raw_text" in analysis:
        return analysis["raw_text"]
    
    script = ""
    
    if "话题背景" in analysis:
        script += f"【话题背景】\n{analysis['话题背景']}\n\n"
    
    if "AI分析过程" in analysis:
        script += f"【AI分析过程】\n{analysis['AI分析过程']}\n\n"
    
    if "核心发现" in analysis:
        script += f"【核心发现】\n{analysis['核心发现']}\n\n"
    
    if "个人观点" in analysis:
        script += f"【个人观点】\n{analysis['个人观点']}\n\n"
    
    if "可执行建议" in analysis:
        script += f"【可执行建议】\n{analysis['可执行建议']}\n\n"
    
    if "一句话总结" in analysis:
        script += f"【一句话总结】\n{analysis['一句话总结']}\n"
    
    return script


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AI 投资分析")
    parser.add_argument("--topic", "-t", help="分析话题")
    parser.add_argument("--ticker", help="分析具体股票/基金代码")
    parser.add_argument("--news", "-n", help="分析新闻事件")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="输出格式")
    args = parser.parse_args()
    
    if not any([args.topic, args.ticker, args.news]):
        parser.print_help()
        sys.exit(1)
    
    # 执行分析
    if args.ticker:
        analysis = analyze_ticker(args.ticker)
        topic = args.ticker
    elif args.news:
        analysis = analyze_news(args.news)
        topic = args.news
    else:
        analysis = analyze_topic(args.topic)
        topic = args.topic
    
    if not analysis:
        sys.exit(1)
    
    # 保存结果
    filepath = save_analysis(analysis, topic)
    print(f"✅ 分析结果已保存: {filepath}", file=sys.stderr)
    
    # 输出
    if args.format == "text":
        print(format_for_podcast(analysis))
    else:
        print(json.dumps(analysis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
