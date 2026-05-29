#!/usr/bin/env python3
"""
历史冷知识公众号 - 主流程脚本
由 hermes agent 调用，完成：选题 → 生成文章 → 保存

用法: python3 pipeline.py [--topic "自定义主题"]
"""

import json
import os
import sys
import random
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TOPICS_DB = BASE_DIR / "topics" / "topics_db.json"
OUTPUT_DIR = BASE_DIR / "output" / "articles"

def load_topics():
    with open(TOPICS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_topics(data):
    with open(TOPICS_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pick_topic(data, custom=None):
    if custom:
        return custom, "自定义"
    available = []
    for cat in data['categories']:
        for topic in cat['topics']:
            if topic not in data.get('used_topics', []):
                available.append((topic, cat['name']))
    if not available:
        data['used_topics'] = []
        save_topics(data)
        available = [(t, c['name']) for c in data['categories'] for t in c['topics']]
    chosen = random.choice(available)
    return chosen[0], chosen[1]

def main():
    custom_topic = None
    if len(sys.argv) > 2 and sys.argv[1] == '--topic':
        custom_topic = sys.argv[2]
    
    data = load_topics()
    topic, category = pick_topic(data, custom_topic)
    
    # 标记已用
    if custom_topic is None:
        if 'used_topics' not in data:
            data['used_topics'] = []
        data['used_topics'].append(topic)
        save_topics(data)
    
    # 日期和文件名
    today = datetime.now().strftime("%Y-%m-%d")
    safe_name = topic[:20].replace(' ', '_').replace('/', '_')
    filename = f"{today}_{safe_name}"
    
    # 输出 JSON 信息供 hermes 使用
    result = {
        "topic": topic,
        "category": category,
        "date": today,
        "filename": filename,
        "output_dir": str(OUTPUT_DIR),
        "template_path": str(BASE_DIR / "templates" / "article_template.html"),
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
