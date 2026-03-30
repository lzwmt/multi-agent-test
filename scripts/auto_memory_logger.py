#!/usr/bin/env python3
"""
自动记忆记录器
检测关键操作并自动写入当日 memory 文件
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE_DIR = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE_DIR / "memory"

# 关键操作触发词
TRIGGER_PATTERNS = {
    "cron": {
        "patterns": [r"cron", r"定时任务", r"schedule", r"每.*小时", r"每天.*点"],
        "description": "Cron 任务配置"
    },
    "script": {
        "patterns": [r"创建.*脚本", r"修改.*脚本", r"写完", r"生成.*py", r"\.py$"],
        "description": "脚本创建/修改"
    },
    "config": {
        "patterns": [r"config", r"配置", r"\.env", r"修改.*配置"],
        "description": "配置变更"
    },
    "milestone": {
        "patterns": [r"测试通过", r"完成", r"搞定", r"部署", r"上线", r"发布"],
        "description": "项目里程碑"
    },
    "optimization": {
        "patterns": [r"优化", r"改进", r"缓存", r"性能"],
        "description": "系统优化"
    }
}


def detect_operation_type(user_input: str, my_response: str) -> tuple:
    """
    检测操作类型
    返回: (是否关键操作, 操作类型, 描述)
    """
    combined = f"{user_input} {my_response}".lower()
    
    for op_type, config in TRIGGER_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, combined, re.I):
                return True, op_type, config["description"]
    
    return False, None, None


def get_today_memory_file() -> Path:
    """获取今日 memory 文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    return MEMORY_DIR / f"{today}.md"


def ensure_memory_file_exists(filepath: Path):
    """确保 memory 文件存在（使用模板）"""
    if not filepath.exists():
        template = f"""# {filepath.stem}

## 今日进展

### [项目/任务名称]
- 关键进展1
- 关键进展2

### 关键发现
- 发现1
- 发现2

## 技术笔记
- 技术点1
- 技术点2

## 待办事项
- [ ] 待办1
- [ ] 待办2

## 文件记录
- 创建的文件/路径

## 自动记录
"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(template, encoding='utf-8')


def append_auto_log(filepath: Path, operation_type: str, description: str, 
                    user_input: str = "", my_response: str = ""):
    """追加自动记录到 memory 文件"""
    
    timestamp = datetime.now().strftime("%H:%M")
    
    log_entry = f"""
### {timestamp} - {description}

**操作**: {operation_type}

**触发**: {user_input[:100]}{'...' if len(user_input) > 100 else ''}

**结果**: {my_response[:200]}{'...' if len(my_response) > 200 else ''}

---
"""
    
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    return True


def should_auto_log(user_input: str, my_response: str) -> dict:
    """
    主函数：判断是否应该自动记录
    返回 dict 包含记录信息或空
    """
    is_key_op, op_type, description = detect_operation_type(user_input, my_response)
    
    if not is_key_op:
        return {"should_log": False}
    
    # 获取今日文件
    memory_file = get_today_memory_file()
    ensure_memory_file_exists(memory_file)
    
    # 追加记录
    success = append_auto_log(memory_file, op_type, description, user_input, my_response)
    
    return {
        "should_log": True,
        "operation_type": op_type,
        "description": description,
        "file": str(memory_file),
        "success": success
    }


def test_detection():
    """测试检测逻辑"""
    test_cases = [
        ("修改 cron 任务", "已更新", True, "cron"),
        ("创建脚本 test.py", "写完", True, "script"),
        ("测试通过", "✅ 完成", True, "milestone"),
        ("查一下天气", "今天晴天", False, None),
        ("优化嵌入缓存", "已更新", True, "optimization"),
    ]
    
    print("=" * 60)
    print("自动记录检测测试")
    print("=" * 60)
    
    for user_input, response, expected, expected_type in test_cases:
        is_key, op_type, desc = detect_operation_type(user_input, response)
        status = "✅" if is_key == expected else "❌"
        type_match = "✅" if (not expected) or (op_type == expected_type) else "❌"
        
        print(f"\n{status} 输入: {user_input[:30]}")
        print(f"   检测: {'关键操作' if is_key else '普通操作'} ({op_type or 'N/A'})")
        print(f"   预期: {'关键操作' if expected else '普通操作'} ({expected_type or 'N/A'})")
        print(f"   类型匹配: {type_match}")
    
    print("\n" + "=" * 60)


def test_append():
    """测试追加记录"""
    print("\n测试追加记录...")
    
    result = should_auto_log(
        "修改 cron 任务，每天 0 点执行",
        "✅ 已更新 daily-memory-file 任务，每天 00:00 自动创建记忆文件"
    )
    
    if result["should_log"]:
        print(f"✅ 已记录到: {result['file']}")
        print(f"   操作类型: {result['operation_type']}")
        print(f"   描述: {result['description']}")
    else:
        print("❌ 未触发记录")
    
    # 显示文件内容
    memory_file = get_today_memory_file()
    if memory_file.exists():
        print(f"\n文件内容预览:")
        content = memory_file.read_text(encoding='utf-8')
        print(content[-500:] if len(content) > 500 else content)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_detection()
        test_append()
    else:
        print("用法: python3 auto_memory_logger.py --test")
