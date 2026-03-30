#!/usr/bin/env python3
"""
会话总结生成器
检测会话结束信号，自动生成总结并写入 memory
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path

WORKSPACE_DIR = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE_DIR / "memory"

# 会话结束信号词
END_SIGNALS = [
    r"bye\b", r"结束", r"先这样", r"明天见", r"晚安",
    r"下次再聊", r"\/new", r"\/reset", r"走了", r"下线"
]

# 关键操作关键词（用于提取）
ACTION_KEYWORDS = [
    r"创建", r"修改", r"更新", r"删除", r"配置",
    r"优化", r"实现", r"完成", r"部署", r"测试"
]

# 技术关键词（用于提取主题）
TECH_KEYWORDS = [
    r"cron", r"缓存", r"脚本", r"配置", r"数据库",
    r"api", r"嵌入", r"memory", r"优化", r"搜索"
]


def is_session_end(user_input: str) -> bool:
    """检测会话结束信号"""
    text = user_input.lower()
    for signal in END_SIGNALS:
        if re.search(signal, text, re.I):
            return True
    return False


def extract_topics(messages: list) -> list:
    """从消息中提取主题"""
    topics = set()
    all_text = " ".join([m.get("content", "") for m in messages])
    
    for keyword in TECH_KEYWORDS:
        if re.search(keyword, all_text, re.I):
            # 简化提取，直接使用关键词
            clean = keyword.replace(r'\b', '').strip()
            if len(clean) > 2:
                topics.add(clean)
    
    return list(topics)[:5]  # 最多5个主题


def extract_actions(messages: list) -> list:
    """提取关键操作"""
    actions = []
    
    for msg in messages:
        content = msg.get("content", "")
        for keyword in ACTION_KEYWORDS:
            if re.search(keyword, content, re.I):
                # 提取整句或关键片段
                sentences = re.split(r'[。！？\n]', content)
                for sent in sentences:
                    if re.search(keyword, sent, re.I) and len(sent) > 10:
                        actions.append(sent.strip()[:100])
                        break
                break
    
    # 去重并限制
    seen = set()
    unique = []
    for a in actions:
        key = a[:30]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    
    return unique[:5]


def generate_summary(messages: list) -> dict:
    """生成会话总结"""
    return {
        "timestamp": datetime.now().strftime("%H:%M"),
        "topics": extract_topics(messages),
        "actions": extract_actions(messages),
        "message_count": len(messages),
        "date": datetime.now().strftime("%Y-%m-%d")
    }


def format_summary(summary: dict) -> str:
    """格式化总结为 Markdown"""
    lines = [
        f"## 会话总结 [{summary['timestamp']}]",
        "",
        f"**消息数**: {summary['message_count']}",
        ""
    ]
    
    if summary['topics']:
        lines.append("### 讨论主题")
        for topic in summary['topics']:
            lines.append(f"- {topic}")
        lines.append("")
    
    if summary['actions']:
        lines.append("### 关键操作")
        for action in summary['actions']:
            lines.append(f"- {action}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


def write_to_memory(summary: dict):
    """写入 memory 文件"""
    memory_file = MEMORY_DIR / f"{summary['date']}.md"
    
    # 确保目录存在
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    # 如果文件不存在，创建基础模板
    if not memory_file.exists():
        template = f"""# {summary['date']}

## 今日进展

### [项目/任务名称]
- 

### 关键发现
- 

## 技术笔记
- 

## 待办事项
- [ ] 

## 文件记录
- 

## 自动记录

## 会话总结

"""
        memory_file.write_text(template, encoding='utf-8')
    
    # 追加总结
    formatted = format_summary(summary)
    with open(memory_file, 'a', encoding='utf-8') as f:
        f.write(formatted)
    
    return str(memory_file)


def save_session_data(messages: list, output_path: Path = None):
    """保存会话数据到文件（供下次读取）"""
    if output_path is None:
        output_path = WORKSPACE_DIR / ".cache" / "last_session.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    session_data = {
        "ended_at": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": messages[-50:]  # 保留最近50条
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    return str(output_path)


def load_session_data(input_path: Path = None) -> list:
    """加载上次会话数据"""
    if input_path is None:
        input_path = WORKSPACE_DIR / ".cache" / "last_session.json"
    
    if not input_path.exists():
        return []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("messages", [])


def process_end_session(user_input: str, messages: list = None):
    """
    处理会话结束
    主入口函数
    """
    if not is_session_end(user_input):
        return {"ended": False}
    
    # 生成总结
    if messages is None:
        messages = []  # 实际使用时传入会话历史
    
    summary = generate_summary(messages)
    memory_path = write_to_memory(summary)
    
    # 保存会话数据
    session_path = save_session_data(messages)
    
    return {
        "ended": True,
        "summary": summary,
        "memory_file": memory_path,
        "session_data": session_path
    }


def test_detection():
    """测试结束信号检测"""
    test_cases = [
        ("bye", True),
        ("先这样，明天聊", True),
        ("结束今天的会话", True),
        ("晚安", True),
        ("继续优化这个", False),
        ("查一下天气", False),
    ]
    
    print("=" * 60)
    print("会话结束信号检测测试")
    print("=" * 60)
    
    for text, expected in test_cases:
        result = is_session_end(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' → {'结束' if result else '继续'}")
    
    print("=" * 60)


def test_summary_generation():
    """测试总结生成"""
    print("\n测试总结生成...")
    
    mock_messages = [
        {"role": "user", "content": "优化 memory search"},
        {"role": "assistant", "content": "创建了 embedding_cache.py"},
        {"role": "user", "content": "修改 cron 任务"},
        {"role": "assistant", "content": "已更新 daily-memory-file"},
        {"role": "user", "content": "实现自动记录"},
        {"role": "assistant", "content": "创建了 auto_memory_logger.py"},
    ]
    
    summary = generate_summary(mock_messages)
    print(f"\n生成总结:")
    print(f"  时间: {summary['timestamp']}")
    print(f"  消息数: {summary['message_count']}")
    print(f"  主题: {summary['topics']}")
    print(f"  操作: {summary['actions']}")
    
    formatted = format_summary(summary)
    print(f"\n格式化输出:\n{formatted}")
    
    # 测试写入
    memory_path = write_to_memory(summary)
    print(f"✅ 已写入: {memory_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_detection()
        test_summary_generation()
    else:
        print("用法: python3 session_summary.py --test")
