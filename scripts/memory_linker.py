#!/usr/bin/env python3
"""
Memory 文件关联工具
自动识别相关文件，添加双向链接
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

WORKSPACE_DIR = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE_DIR / "memory"

# 关键词权重配置
KEYWORD_WEIGHTS = {
    "航班": 5,
    "监控": 3,
    "缓存": 5,
    "嵌入": 3,
    "embedding": 3,
    "cron": 4,
    "定时": 3,
    "memory": 3,
    "优化": 3,
    "脚本": 3,
    "配置": 3,
    "Git": 3,
    "总结": 2,
    "记录": 2,
    "自动": 2,
}


def extract_keywords(content: str, min_length: int = 2) -> dict:
    """提取关键词及其权重"""
    keywords = defaultdict(int)
    
    # 提取中文词汇
    chinese_words = re.findall(r'[\u4e00-\u9fff]{' + str(min_length) + r',}', content)
    for word in chinese_words:
        if len(word) >= min_length:
            weight = KEYWORD_WEIGHTS.get(word, 1)
            keywords[word] += weight
    
    # 提取英文单词
    english_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', content)
    for word in english_words:
        word_lower = word.lower()
        weight = KEYWORD_WEIGHTS.get(word_lower, 1)
        keywords[word_lower] += weight
    
    return dict(keywords)


def get_memory_files(days: int = 30) -> list:
    """获取最近 N 天的 memory 文件"""
    files = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for filepath in MEMORY_DIR.glob("*.md"):
        try:
            # 从文件名解析日期
            date_str = filepath.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date >= cutoff:
                files.append((file_date, filepath))
        except ValueError:
            continue
    
    # 按日期排序
    files.sort(key=lambda x: x[0], reverse=True)
    return [f[1] for f in files]


def analyze_file(filepath: Path) -> dict:
    """分析单个文件内容"""
    content = filepath.read_text(encoding='utf-8')
    
    return {
        "path": filepath,
        "name": filepath.stem,
        "content": content,
        "keywords": extract_keywords(content),
        "links": extract_existing_links(content),
        "headers": extract_headers(content)
    }


def extract_existing_links(content: str) -> list:
    """提取已有的链接"""
    # Wiki 风格链接: [[filename|title]]
    wiki_links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    # Markdown 链接: [title](filename.md)
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
    
    return wiki_links + [link[1] for link in md_links]


def extract_headers(content: str) -> list:
    """提取标题"""
    headers = re.findall(r'^#{1,3}\s+(.+)$', content, re.M)
    return headers[:5]  # 前5个标题


def calculate_similarity(file1: dict, file2: dict) -> float:
    """计算两个文件的相似度"""
    keywords1 = set(file1["keywords"].keys())
    keywords2 = set(file2["keywords"].keys())
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Jaccard 相似度
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    
    # 加权交集
    weighted_intersection = sum(
        file1["keywords"].get(k, 0) + file2["keywords"].get(k, 0)
        for k in intersection
    )
    weighted_union = sum(file1["keywords"].values()) + sum(file2["keywords"].values())
    
    if weighted_union == 0:
        return 0.0
    
    return weighted_intersection / weighted_union


def find_related_files(files_data: list, target_file: dict, top_n: int = 3) -> list:
    """找到与目标文件最相关的其他文件"""
    similarities = []
    
    for file_data in files_data:
        if file_data["path"] == target_file["path"]:
            continue
        
        sim = calculate_similarity(target_file, file_data)
        if sim > 0.1:  # 阈值
            similarities.append((file_data, sim))
    
    # 按相似度排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]


def generate_link_section(related: list) -> str:
    """生成链接章节"""
    if not related:
        return ""
    
    lines = ["\n## 相关文件\n"]
    
    for file_data, score in related:
        date = file_data["name"]
        headers = file_data["headers"]
        title = headers[0] if headers else date
        
        lines.append(f"- [[{date}.md|{title}]] (相关度: {score:.2f})")
    
    lines.append("")
    return "\n".join(lines)


def add_links_to_file(filepath: Path, link_section: str):
    """添加链接到文件"""
    content = filepath.read_text(encoding='utf-8')
    
    # 检查是否已有相关文件章节
    if "## 相关文件" in content:
        # 替换旧章节
        content = re.sub(r'\n## 相关文件\n.*?\n(?=##|$)', link_section, content, flags=re.S)
    else:
        # 在文件末尾添加
        content = content.rstrip() + link_section
    
    filepath.write_text(content, encoding='utf-8')
    return True


def process_all_files(days: int = 30):
    """处理所有文件"""
    files = get_memory_files(days)
    
    if len(files) < 2:
        return {"success": False, "message": "Not enough files to link"}
    
    # 分析所有文件
    files_data = [analyze_file(f) for f in files]
    
    results = []
    for target in files_data:
        related = find_related_files(files_data, target, top_n=3)
        
        if related:
            link_section = generate_link_section(related)
            success = add_links_to_file(target["path"], link_section)
            
            results.append({
                "file": target["name"],
                "links_added": len(related),
                "success": success
            })
    
    return {
        "success": True,
        "processed": len(results),
        "results": results
    }


def test():
    """测试功能"""
    print("=" * 60)
    print("Memory 文件关联测试")
    print("=" * 60)
    
    # 1. 获取文件
    print("\n1. 获取 memory 文件...")
    files = get_memory_files(days=30)
    print(f"   找到 {len(files)} 个文件")
    for f in files[:5]:
        print(f"      - {f.name}")
    
    if len(files) < 2:
        print("   文件不足，无法测试关联")
        return
    
    # 2. 分析文件
    print("\n2. 分析文件内容...")
    files_data = [analyze_file(f) for f in files[:3]]
    
    for fd in files_data:
        print(f"\n   {fd['name']}:")
        print(f"      关键词: {list(fd['keywords'].keys())[:5]}")
        print(f"      标题: {fd['headers'][:2]}")
    
    # 3. 计算相似度
    print("\n3. 计算文件相似度...")
    for i in range(len(files_data)):
        for j in range(i+1, len(files_data)):
            sim = calculate_similarity(files_data[i], files_data[j])
            print(f"   {files_data[i]['name']} <-> {files_data[j]['name']}: {sim:.3f}")
    
    # 4. 生成链接
    print("\n4. 生成链接章节...")
    target = files_data[0]
    related = find_related_files(files_data, target, top_n=2)
    
    if related:
        link_section = generate_link_section(related)
        print(f"   为 {target['name']} 生成链接:")
        print(link_section)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test()
    elif len(sys.argv) > 1 and sys.argv[1] == "--link":
        result = process_all_files()
        print(f"处理完成: {result}")
    else:
        print("用法:")
        print("  python3 memory_linker.py --test   # 测试")
        print("  python3 memory_linker.py --link   # 执行关联")
