#!/usr/bin/env python3
"""
历史冷知识公众号 - 全自动每日生成脚本
由 hermes cron 调用，完成：选题 → AI生成 → 保存MD → 生成封面

输出: JSON 格式的任务信息，供 hermes agent 后续处理排版和发布
"""

import json
import os
import sys
import random
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(os.path.expanduser("~/.openclaw/workspace/wechat-oa"))
TOPICS_DB = BASE_DIR / "topics" / "topics_db.json"
ARTICLES_DIR = BASE_DIR / "output" / "articles"
COVERS_DIR = BASE_DIR / "output" / "covers"

def load_topics():
    with open(TOPICS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_topics(data):
    with open(TOPICS_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pick_topic(data):
    available = []
    for cat in data['categories']:
        for topic in cat['topics']:
            if topic not in data.get('used_topics', []):
                available.append((topic, cat['name']))
    if not available:
        data['used_topics'] = []
        save_topics(data)
        available = [(t, c['name']) for c in data['categories'] for t in c['topics']]
    return random.choice(available)

def generate_cover(topic, output_path):
    """用 AiNaiBa gpt-image-2 生成封面图，失败时降级到 Pollinations"""
    prompt = f"Chinese historical dramatic scene, {topic}, cinematic painting style, warm golden tones, ancient Chinese architecture or historical setting, dramatic lighting, no text, no watermarks"
    
    # 使用 image_gen.py 脚本（AiNaiBa 优先，Pollinations 备用）
    script_path = Path(os.path.expanduser("~/.hermes/scripts/image_gen.py"))
    if not script_path.exists():
        print(f"封面生成脚本不存在: {script_path}", file=sys.stderr)
        return False
    
    try:
        # 调用 image_gen.py 脚本
        result = subprocess.run(
            ["python3", str(script_path), prompt, str(output_path), "1536x1024"],
            capture_output=True,
            text=True,
            timeout=660
        )
        
        if result.returncode == 0:
            # 检查输出文件是否存在且大小合理
            if output_path.exists() and output_path.stat().st_size > 10000:
                print(f"封面生成成功: {output_path}", file=sys.stderr)
                return True
            else:
                print(f"封面文件异常: {output_path}", file=sys.stderr)
                return False
        else:
            print(f"封面生成失败: {result.stderr}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("封面生成超时", file=sys.stderr)
        return False
    except Exception as e:
        print(f"封面生成异常: {e}", file=sys.stderr)
        return False

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. 选题
    data = load_topics()
    topic, category = pick_topic(data)
    
    # 标记已用
    if 'used_topics' not in data:
        data['used_topics'] = []
    data['used_topics'].append(topic)
    save_topics(data)
    
    # 2. 文件名
    safe_name = topic[:15].replace(' ', '_').replace('/', '_').replace('？', '').replace('?', '')
    filename_base = f"{today}_{safe_name}"
    md_path = ARTICLES_DIR / f"{filename_base}.md"
    cover_path = COVERS_DIR / f"{filename_base}.jpg"
    
    # 3. 生成封面
    print(f"🎨 生成封面: {topic}", file=sys.stderr)
    cover_ok = generate_cover(topic, cover_path)
    
    # 4. 输出结果（JSON，供 hermes agent 读取）
    result = {
        "status": "ready",
        "topic": topic,
        "category": category,
        "date": today,
        "md_path": str(md_path),
        "cover_path": str(cover_path) if cover_ok else None,
        "filename_base": filename_base,
        "instructions": (
            f"请为以下主题生成一篇公众号文章，保存到 {md_path}：\n"
            f"主题：{topic}\n"
            f"分类：{category}\n\n"
            f"写作风格要求（卡兹克风格）：\n"
            f"1. 4000-8000字长文，段落要短，一句话一段很常见\n"
            f"2. 不加小标题，靠口语化转场句自然衔接（'说到这个'、'回到xxx这块'）\n"
            f"3. 从一个具体的、当下的事件/场景切入，禁止宏大叙事开头\n"
            f"4. 像跟朋友聊天，句子时长时短，用逗号制造口语化停顿\n"
            f"5. 知识是「聊着聊着顺手掏出来」的，不是「下面我来科普」\n"
            f"6. 结尾有冷知识彩蛋，连接到更大的文化/哲学/历史参照物\n\n"
            f"绝对禁区：\n"
            f"- 禁用冒号、破折号、双引号（用「」替代）\n"
            f"- 禁用'说白了'、'意味着什么'、'本质上'、'换句话说'、'不可否认'\n"
            f"- 禁用'首先...其次...最后'、'综上所述'、'值得注意的是'\n"
            f"- 禁用bullet point罗列观点，不大量加粗\n"
            f"- 禁止假设性例子，要用真实细节\n\n"
            f"推荐口语化表达：\n"
            f"- 转场：坦率的讲、说真的、我是真的觉得、怎么说呢、其实吧\n"
            f"- 判断：我有时候觉得、我一直觉得、我自己的感受是\n"
            f"- 自嘲：说实话我也不确定、我自己也还在摸索、愚钝如我\n"
            f"- 情绪：这种感觉太爽了、我当时就愣住了、太离谱了\n\n"
            f"格式：直接输出 Markdown，标题用 # 开头，引用用 > ，分节用 ## "
        )
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
