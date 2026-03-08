"""
存储模块 - 提供统一的 JSON 文件读写接口
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List


# 数据目录路径
DATA_DIR = Path(__file__).parent / "data"


def ensure_data_dir() -> None:
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_file_path(filename: str) -> Path:
    """获取数据文件的完整路径"""
    ensure_data_dir()
    return DATA_DIR / filename


def load_json(filename: str, default: Any = None) -> Any:
    """
    从 JSON 文件加载数据
    
    Args:
        filename: 文件名
        default: 文件不存在时的默认值
        
    Returns:
        解析后的数据，或默认值
    """
    filepath = get_file_path(filename)
    if not filepath.exists():
        return default if default is not None else []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"警告: {filename} 格式错误，使用默认值")
        return default if default is not None else []
    except Exception as e:
        print(f"读取 {filename} 失败: {e}")
        return default if default is not None else []


def save_json(filename: str, data: Any) -> bool:
    """
    保存数据到 JSON 文件
    
    Args:
        filename: 文件名
        data: 要保存的数据
        
    Returns:
        是否保存成功
    """
    filepath = get_file_path(filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存 {filename} 失败: {e}")
        return False


def generate_id(items: List[Dict]) -> int:
    """
    生成新的唯一 ID
    
    Args:
        items: 现有项目列表
        
    Returns:
        新的唯一 ID
    """
    if not items:
        return 1
    return max(item.get('id', 0) for item in items) + 1
