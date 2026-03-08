"""
任务管理模块 - 管理待办事项
"""
from datetime import datetime
from typing import List, Dict, Optional
from storage import load_json, save_json, generate_id


TASKS_FILE = "tasks.json"

# 优先级映射
PRIORITY_LEVELS = {
    'high': 3,
    'medium': 2,
    'low': 1
}


def add_task(title: str, priority: str = "medium") -> bool:
    """
    添加新任务
    
    Args:
        title: 任务标题
        priority: 优先级 (high/medium/low)
        
    Returns:
        是否添加成功
    """
    if not title or not title.strip():
        print("错误: 任务标题不能为空")
        return False
    
    # 标准化优先级
    priority = priority.lower()
    if priority not in PRIORITY_LEVELS:
        priority = "medium"
    
    tasks = load_json(TASKS_FILE, [])
    
    new_task = {
        "id": generate_id(tasks),
        "title": title.strip(),
        "priority": priority,
        "completed": False,
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }
    
    tasks.append(new_task)
    
    if save_json(TASKS_FILE, tasks):
        print(f"✓ 任务已添加 [#{new_task['id']}] {title}")
        return True
    return False


def list_tasks(show_all: bool = False) -> List[Dict]:
    """
    列出任务
    
    Args:
        show_all: 是否显示所有任务（包括已完成）
        
    Returns:
        任务列表
    """
    tasks = load_json(TASKS_FILE, [])
    
    if not tasks:
        print("暂无任务")
        return []
    
    # 筛选未完成任务
    if not show_all:
        tasks = [t for t in tasks if not t.get('completed', False)]
    
    if not tasks:
        print("暂无未完成任务" if not show_all else "暂无任务")
        return []
    
    # 按优先级排序
    tasks.sort(key=lambda x: PRIORITY_LEVELS.get(x.get('priority', 'medium'), 2), reverse=True)
    
    print(f"\n{'ID':<6}{'状态':<6}{'优先级':<8}{'标题'}")
    print("-" * 50)
    
    for task in tasks:
        status = "✓" if task.get('completed') else "○"
        priority = task.get('priority', 'medium')
        priority_display = {'high': '高', 'medium': '中', 'low': '低'}.get(priority, '中')
        title = task.get('title', '')
        
        print(f"{task['id']:<6}{status:<6}{priority_display:<8}{title}")
    
    print()
    return tasks


def complete_task(task_id: int) -> bool:
    """
    标记任务为已完成
    
    Args:
        task_id: 任务 ID
        
    Returns:
        是否操作成功
    """
    tasks = load_json(TASKS_FILE, [])
    
    for task in tasks:
        if task.get('id') == task_id:
            if task.get('completed'):
                print(f"任务 #{task_id} 已经完成")
                return False
            
            task['completed'] = True
            task['completed_at'] = datetime.now().isoformat()
            
            if save_json(TASKS_FILE, tasks):
                print(f"✓ 任务完成 [#{task_id}] {task.get('title', '')}")
                return True
            return False
    
    print(f"错误: 找不到任务 #{task_id}")
    return False


def delete_task(task_id: int) -> bool:
    """
    删除任务
    
    Args:
        task_id: 任务 ID
        
    Returns:
        是否删除成功
    """
    tasks = load_json(TASKS_FILE, [])
    
    original_count = len(tasks)
    tasks = [t for t in tasks if t.get('id') != task_id]
    
    if len(tasks) == original_count:
        print(f"错误: 找不到任务 #{task_id}")
        return False
    
    if save_json(TASKS_FILE, tasks):
        print(f"✓ 任务已删除 [#{task_id}]")
        return True
    return False


def get_task_stats() -> Dict:
    """获取任务统计信息"""
    tasks = load_json(TASKS_FILE, [])
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get('completed'))
    pending = total - completed
    
    return {
        "total": total,
        "completed": completed,
        "pending": pending
    }
