#!/usr/bin/env python3
"""
GitHub Trending Daily + Discord 通知
执行 trending 抓取并通过 Discord 消息发送结果
"""

import subprocess
import json
import os
import sys
from datetime import datetime

# Discord 配置
DISCORD_CHANNEL = "1479313637167595542"

def run_trending_script():
    """执行 trending 脚本并获取输出"""
    script_path = "/root/.openclaw/workspace/skills/github-trending-daily/scripts/github-trending-daily.py"
    
    result = subprocess.run(
        [sys.executable, script_path, "--top", "10", "--days", "14", "--output", "/tmp/github-trending-result.json"],
        capture_output=True,
        text=True,
        cwd="/root/.openclaw/workspace"
    )
    
    if result.returncode != 0:
        print(f"❌ 脚本执行失败: {result.stderr}")
        return None
    
    # 读取 JSON 结果
    try:
        with open("/tmp/github-trending-result.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取结果失败: {e}")
        return None

def format_message(data):
    """格式化 Discord 消息"""
    date_str = datetime.now().strftime("%Y年%m月%d日")
    top_repos = data.get("top_repos", [])
    continuing = data.get("continuing_repos", [])
    
    # 构建新上榜项目列表
    new_projects_text = []
    for i, repo in enumerate(top_repos[:5], 1):  # 只显示前5个
        name = repo.get("full_name", "")
        stars = repo.get("total_stars", 0)
        forks = repo.get("total_forks", 0)
        lang = repo.get("language") or "N/A"
        summary = repo.get("summary", "")
        url = repo.get("url", "")
        
        new_projects_text.append(
            f"{i}. **{name}**\n"
            f"⭐ {stars:,} | 🔀 {forks:,} | 🔧 {lang}\n"
            f"📝 {summary}\n"
            f"🔗 {url}"
        )
    
    # 持续飙升项目数量
    continuing_count = len(continuing)
    continuing_names = ", ".join(continuing[:3]) + (" 等" if continuing_count > 3 else "") if continuing else "无"
    
    time_str = datetime.now().strftime("%H:%M")
    new_projects_joined = "\n\n".join(new_projects_text)
    message = f"""📊 **GitHub Trending 日报** - {date_str}

🏆 **新上榜项目**（Top {len(top_repos)}）：

{new_projects_joined}

📈 **持续飙升项目**（{continuing_count}个）：{continuing_names}

⏱️ 数据获取时间：{time_str}"""
    
    return message

def send_to_discord(message):
    """输出 Discord 消息（供外部发送）"""
    print("\n" + "="*50)
    print("DISCORD_MESSAGE_START")
    print(json.dumps({
        "channel": "discord",
        "to": DISCORD_CHANNEL,
        "message": message
    }, ensure_ascii=False))
    print("DISCORD_MESSAGE_END")
    print("="*50)
    return True

def main():
    print("🔍 开始获取 GitHub Trending...")
    
    # 执行 trending 脚本
    data = run_trending_script()
    if not data:
        # 发送错误通知
        send_to_discord("❌ GitHub Trending 获取失败，请检查日志")
        return 1
    
    # 格式化消息
    message = format_message(data)
    
    # 发送到 Discord
    print("📤 发送 Discord 通知...")
    if send_to_discord(message):
        print("✅ 任务完成")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
