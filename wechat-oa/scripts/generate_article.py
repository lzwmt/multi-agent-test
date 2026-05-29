#!/usr/bin/env python3
"""
历史冷知识公众号 - 文章生成器
用法: python3 generate_article.py [--topic "自定义主题"] [--output-dir /path]
"""

import json
import os
import sys
import random
import argparse
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
TOPICS_DB = BASE_DIR / "topics" / "topics_db.json"
OUTPUT_DIR = BASE_DIR / "output" / "articles"
TEMPLATE_DIR = BASE_DIR / "templates"

def load_topics():
    """加载选题库"""
    with open(TOPICS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_topics(data):
    """保存选题库（标记已用）"""
    with open(TOPICS_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pick_topic(data, custom_topic=None):
    """选题：随机选一个未用过的，或使用自定义主题"""
    if custom_topic:
        return custom_topic, "自定义"
    
    # 收集所有未用过的题目
    available = []
    for cat in data['categories']:
        for topic in cat['topics']:
            if topic not in data.get('used_topics', []):
                available.append((topic, cat['name']))
    
    if not available:
        # 所有题目都用过了，重置
        data['used_topics'] = []
        save_topics(data)
        available = [(t, c['name']) for c in data['categories'] for t in c['topics']]
    
    chosen = random.choice(available)
    return chosen[0], chosen[1]

def generate_article_prompt(topic, category):
    """生成文章的 AI prompt"""
    return f"""你是一个专业的历史冷知识公众号作者。请围绕以下主题写一篇公众号文章：

主题：{topic}
分类：{category}

要求：
1. 标题要有悬念感和好奇心，让人忍不住点进来（不超过30个字）
2. 开头用一句引人深思的话或反常识的观点吸引读者
3. 正文分2-3个小节，每节有小标题
4. 语言通俗易懂，像讲故事一样，不要学术腔
5. 每个小节之间用 "· · ·" 分隔
6. 结尾要有一个"冷知识彩蛋"或让人意想不到的结论
7. 全文800-1200字
8. 适当加入emoji增加可读性，但不要过多
9. 不要用"首先"、"其次"、"最后"这种刻板连接词
10. 要有真实的历史细节和数据，不能编造

请直接输出文章内容，格式如下：

标题: <标题>
引言: <一句引人深思的话，20字以内>

<正文内容，包含小标题和分节>

冷知识: <一个相关的冷知识彩蛋，30字以内>
"""

def generate_article(topic, category):
    """调用 AI 生成文章"""
    prompt = generate_article_prompt(topic, category)
    
    # 使用 hermes 的 AI 能力（通过文件传递 prompt）
    prompt_file = BASE_DIR / "output" / ".tmp_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # 调用 AI 生成
    import subprocess
    result = subprocess.run(
        ['python3', '-c', f'''
import sys
sys.path.insert(0, "/root/.hermes")
from hermes_tools import read_file, write_file

prompt = read_file("{prompt_file}")
# 这里通过 hermes 的 session 来调用 AI
# 实际上我们在主脚本中通过 hermes agent 来处理
'''],
        capture_output=True, text=True, timeout=30
    )
    
    return prompt  # 返回 prompt，由 hermes agent 处理

def format_article_markdown(title, quote, content, cold_fact):
    """格式化为 Markdown"""
    md = f"""# {title}

> {quote}

{content}

---

🧊 **冷知识彩蛋**：{cold_fact}

---

📌 关注我，每天带你读一段你不知道的历史
"""
    return md

def main():
    parser = argparse.ArgumentParser(description='历史冷知识公众号文章生成器')
    parser.add_argument('--topic', type=str, help='自定义主题（不选则随机）')
    parser.add_argument('--output-dir', type=str, help='输出目录')
    args = parser.parse_args()
    
    # 加载选题库
    data = load_topics()
    
    # 选题
    topic, category = pick_topic(data, args.topic)
    print(f"📌 选题: [{category}] {topic}")
    
    # 输出 prompt 供 hermes agent 使用
    prompt = generate_article_prompt(topic, category)
    prompt_file = BASE_DIR / "output" / ".current_prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # 记录当前选题信息
    info = {
        "topic": topic,
        "category": category,
        "prompt_file": str(prompt_file),
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    info_file = BASE_DIR / "output" / ".current_topic.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    
    # 标记为已用
    if 'used_topics' not in data:
        data['used_topics'] = []
    if args.topic is None:  # 自定义主题不标记
        data['used_topics'].append(topic)
        save_topics(data)
    
    print(f"📂 Prompt 已保存: {prompt_file}")
    print(f"📝 请让 AI 根据 prompt 生成文章")
    
    return info

if __name__ == "__main__":
    main()
