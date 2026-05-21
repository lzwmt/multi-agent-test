#!/usr/bin/env python3
"""
播客内容审核脚本
AI 生成内容后，推送给用户审核确认。

用法：
  python3 review_workflow.py --generate    # 生成今日内容（AI自动）
  python3 review_workflow.py --review      # 审核今日内容（你来）
  python3 review_workflow.py --approve     # 确认发布
  python3 review_workflow.py --reject      # 拒绝，重新生成

流程：
  1. AI 自动：抓取新闻 → 分析 → 生成脚本
  2. 你来审核：看选题 → 看脚本 → 加个人观点 → 确认
  3. AI 自动：TTS → 音频处理 → 发布
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# === 配置 ===
WORKSPACE = os.path.expanduser("~/.openclaw/workspace/ai-podcast")
OUTPUT_DIR = os.path.join(WORKSPACE, "output")
REVIEW_DIR = os.path.join(WORKSPACE, "review")

# 脚本路径
FETCH_SCRIPT = os.path.join(WORKSPACE, "fetch_podcast_news.py")
ANALYSIS_SCRIPT = os.path.join(WORKSPACE, "ai_investment_analysis.py")
PIPELINE_SCRIPT = os.path.join(WORKSPACE, "podcast_pipeline.py")


def generate_today_content():
    """AI 自动生成今日内容"""
    print("📰 Step 1: 抓取今日新闻...")
    
    # 1. 抓取新闻
    result = subprocess.run(
        ["python3", FETCH_SCRIPT, "--count", "5"],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        print(f"❌ 新闻抓取失败: {result.stderr}", file=sys.stderr)
        return False
    
    # 读取新闻
    news_file = os.path.join(OUTPUT_DIR, "today_news.json")
    if not os.path.exists(news_file):
        print("❌ 新闻文件不存在", file=sys.stderr)
        return False
    
    with open(news_file) as f:
        news = json.load(f)
    
    if not news:
        print("❌ 没有抓到新闻", file=sys.stderr)
        return False
    
    print(f"✅ 抓取到 {len(news)} 条新闻")
    
    # 2. 选择最佳选题
    best_topic = news[0]  # 分数最高的
    print(f"\n🎯 推荐选题: {best_topic['title']}")
    print(f"   来源: {best_topic['source']}")
    print(f"   分数: {best_topic['score']}")
    
    # 3. AI 分析选题
    print(f"\n🤖 Step 2: AI 分析选题...")
    
    result = subprocess.run(
        ["python3", ANALYSIS_SCRIPT, "--topic", best_topic['title'], "--output", "json"],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        print(f"⚠️ AI 分析失败，使用原始新闻", file=sys.stderr)
        analysis = {"raw_text": best_topic.get("summary", "")}
    else:
        try:
            analysis = json.loads(result.stdout)
        except json.JSONDecodeError:
            analysis = {"raw_text": result.stdout}
    
    # 4. 保存待审核内容
    os.makedirs(REVIEW_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    review_file = os.path.join(REVIEW_DIR, f"{today}_pending.json")
    
    review_data = {
        "date": today,
        "status": "pending",
        "news": news,
        "selected_topic": best_topic,
        "analysis": analysis,
        "created_at": datetime.now().isoformat(),
        "user_comments": "",
        "user_approved": False
    }
    
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(review_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 待审核内容已保存: {review_file}")
    print("\n" + "="*50)
    print("📋 请审核今日内容:")
    print("="*50)
    print(f"\n选题: {best_topic['title']}")
    print(f"来源: {best_topic['source']}")
    print(f"摘要: {best_topic.get('summary', '无')[:200]}...")
    
    if "raw_text" in analysis:
        print(f"\nAI 分析:\n{analysis['raw_text'][:500]}...")
    elif "话题背景" in analysis:
        print(f"\nAI 分析:")
        print(f"  背景: {analysis.get('话题背景', '无')[:100]}...")
        print(f"  发现: {analysis.get('核心发现', '无')[:100]}...")
        print(f"  建议: {analysis.get('可执行建议', '无')[:100]}...")
    
    print("\n" + "="*50)
    print("下一步:")
    print("  python3 review_workflow.py --review    # 查看完整内容")
    print("  python3 review_workflow.py --approve   # 确认发布")
    print("  python3 review_workflow.py --reject    # 拒绝重新生成")
    print("="*50)
    
    return True


def review_today_content():
    """查看今日待审核内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    review_file = os.path.join(REVIEW_DIR, f"{today}_pending.json")
    
    if not os.path.exists(review_file):
        print("❌ 今日没有待审核内容")
        print("   请先运行: python3 review_workflow.py --generate")
        return False
    
    with open(review_file) as f:
        data = json.load(f)
    
    print("="*50)
    print(f"📋 今日内容审核 - {data['date']}")
    print("="*50)
    
    # 显示选题
    print(f"\n🎯 选题:")
    print(f"   标题: {data['selected_topic']['title']}")
    print(f"   来源: {data['selected_topic']['source']}")
    print(f"   分数: {data['selected_topic']['score']}")
    
    # 显示分析
    print(f"\n🤖 AI 分析:")
    analysis = data['analysis']
    if "raw_text" in analysis:
        print(analysis['raw_text'])
    else:
        for key in ['话题背景', 'AI分析过程', '核心发现', '个人观点', '可执行建议', '一句话总结']:
            if key in analysis:
                print(f"\n【{key}】")
                print(analysis[key])
    
    # 显示用户评论
    if data.get('user_comments'):
        print(f"\n💬 你的评论:")
        print(data['user_comments'])
    
    # 显示状态
    status = "✅ 已确认" if data.get('user_approved') else "⏳ 待确认"
    print(f"\n状态: {status}")
    
    print("\n" + "="*50)
    print("下一步:")
    print("  python3 review_workflow.py --approve   # 确认发布")
    print("  python3 review_workflow.py --reject    # 拒绝重新生成")
    print("="*50)
    
    return True


def approve_today_content():
    """确认发布今日内容"""
    today = datetime.now().strftime("%Y-%m-%d")
    review_file = os.path.join(REVIEW_DIR, f"{today}_pending.json")
    
    if not os.path.exists(review_file):
        print("❌ 今日没有待审核内容")
        return False
    
    with open(review_file) as f:
        data = json.load(f)
    
    # 更新状态
    data['status'] = 'approved'
    data['user_approved'] = True
    data['approved_at'] = datetime.now().isoformat()
    
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ 内容已确认，准备生成音频...")
    
    # TODO: 调用 podcast_pipeline.py 生成音频
    # 这里需要先生成脚本文件
    
    print("\n下一步:")
    print("  1. 生成播客脚本")
    print("  2. TTS 生成音频")
    print("  3. 音频后处理")
    print("  4. 更新 RSS")
    
    return True


def reject_today_content():
    """拒绝今日内容，重新生成"""
    today = datetime.now().strftime("%Y-%m-%d")
    review_file = os.path.join(REVIEW_DIR, f"{today}_pending.json")
    
    if not os.path.exists(review_file):
        print("❌ 今日没有待审核内容")
        return False
    
    # 读取用户评论
    print("💬 请输入拒绝原因（可选，帮助 AI 改进）:")
    print("   （直接回车跳过）")
    comments = input("> ").strip()
    
    # 更新状态
    with open(review_file) as f:
        data = json.load(f)
    
    data['status'] = 'rejected'
    data['user_approved'] = False
    data['user_comments'] = comments
    data['rejected_at'] = datetime.now().isoformat()
    
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n🔄 内容已拒绝，重新生成...")
    
    # 重新生成
    return generate_today_content()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="播客内容审核流程")
    parser.add_argument("--generate", action="store_true", help="生成今日内容")
    parser.add_argument("--review", action="store_true", help="查看待审核内容")
    parser.add_argument("--approve", action="store_true", help="确认发布")
    parser.add_argument("--reject", action="store_true", help="拒绝重新生成")
    args = parser.parse_args()
    
    if args.generate:
        generate_today_content()
    elif args.review:
        review_today_content()
    elif args.approve:
        approve_today_content()
    elif args.reject:
        reject_today_content()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
