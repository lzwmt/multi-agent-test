"""
笔记模块 - 管理个人笔记
"""
from datetime import datetime
from typing import List, Dict, Optional
from storage import load_json, save_json, generate_id


NOTES_FILE = "notes.json"


def add_note(content: str, tags: List[str] = None) -> bool:
    """
    添加新笔记
    
    Args:
        content: 笔记内容
        tags: 标签列表
        
    Returns:
        是否添加成功
    """
    if not content or not content.strip():
        print("错误: 笔记内容不能为空")
        return False
    
    # 处理标签
    if tags is None:
        tags = []
    
    # 如果是字符串（逗号分隔），转换为列表
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    
    notes = load_json(NOTES_FILE, [])
    
    new_note = {
        "id": generate_id(notes),
        "content": content.strip(),
        "tags": tags,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    notes.append(new_note)
    
    if save_json(NOTES_FILE, notes):
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        print(f"✓ 笔记已添加 [#{new_note['id']}]{tag_str}")
        # 显示内容预览
        preview = content.strip()[:50] + "..." if len(content) > 50 else content.strip()
        print(f"  {preview}")
        return True
    return False


def list_notes(tag: Optional[str] = None) -> List[Dict]:
    """
    列出笔记
    
    Args:
        tag: 按标签筛选（可选）
        
    Returns:
        笔记列表
    """
    notes = load_json(NOTES_FILE, [])
    
    if not notes:
        print("暂无笔记")
        return []
    
    # 按标签筛选
    if tag:
        notes = [n for n in notes if tag.lower() in [t.lower() for t in n.get('tags', [])]]
        if not notes:
            print(f'暂无标签为 "{tag}" 的笔记')
            return []
    
    # 按时间倒序
    notes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    print(f"\n{'ID':<6}{'时间':<20}{'标签':<15}{'内容预览'}")
    print("-" * 70)
    
    for note in notes:
        note_id = note.get('id', 0)
        created = note.get('created_at', '')
        # 简化时间显示
        if created:
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime("%m-%d %H:%M")
            except:
                created = created[:16]
        
        tags = note.get('tags', [])
        tag_str = ', '.join(tags[:2]) if tags else '-'
        if len(tags) > 2:
            tag_str += '...'
        
        content = note.get('content', '')
        preview = content[:30] + "..." if len(content) > 30 else content
        
        print(f"{note_id:<6}{created:<20}{tag_str:<15}{preview}")
    
    print(f"\n共 {len(notes)} 条笔记")
    return notes


def show_note(note_id: int) -> Optional[Dict]:
    """
    显示单条笔记详情
    
    Args:
        note_id: 笔记 ID
        
    Returns:
        笔记数据，找不到返回 None
    """
    notes = load_json(NOTES_FILE, [])
    
    for note in notes:
        if note.get('id') == note_id:
            print(f"\n{'='*50}")
            print(f"笔记 #{note_id}")
            print(f"{'='*50}")
            
            created = note.get('created_at', '')
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    created = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            print(f"创建时间: {created}")
            
            tags = note.get('tags', [])
            if tags:
                print(f"标签: {', '.join(tags)}")
            
            print(f"\n{note.get('content', '')}")
            print(f"{'='*50}\n")
            
            return note
    
    print(f"错误: 找不到笔记 #{note_id}")
    return None


def search_notes(keyword: str) -> List[Dict]:
    """
    搜索笔记
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的笔记列表
    """
    if not keyword or not keyword.strip():
        print("错误: 搜索关键词不能为空")
        return []
    
    notes = load_json(NOTES_FILE, [])
    keyword_lower = keyword.lower().strip()
    
    results = []
    for note in notes:
        # 搜索内容
        if keyword_lower in note.get('content', '').lower():
            results.append(note)
            continue
        
        # 搜索标签
        tags = note.get('tags', [])
        if any(keyword_lower in tag.lower() for tag in tags):
            results.append(note)
            continue
    
    if not results:
        print(f'未找到包含 "{keyword}" 的笔记')
        return []
    
    print(f'\n找到 {len(results)} 条包含 "{keyword}" 的笔记:\n')
    
    print(f"{'ID':<6}{'时间':<20}{'标签':<15}{'内容预览'}")
    print("-" * 70)
    
    for note in results:
        note_id = note.get('id', 0)
        created = note.get('created_at', '')
        if created:
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime("%m-%d %H:%M")
            except:
                created = created[:16]
        
        tags = note.get('tags', [])
        tag_str = ', '.join(tags[:2]) if tags else '-'
        
        content = note.get('content', '')
        preview = content[:30] + "..." if len(content) > 30 else content
        
        print(f"{note_id:<6}{created:<20}{tag_str:<15}{preview}")
    
    print()
    return results


def delete_note(note_id: int) -> bool:
    """
    删除笔记
    
    Args:
        note_id: 笔记 ID
        
    Returns:
        是否删除成功
    """
    notes = load_json(NOTES_FILE, [])
    
    original_count = len(notes)
    notes = [n for n in notes if n.get('id') != note_id]
    
    if len(notes) == original_count:
        print(f"错误: 找不到笔记 #{note_id}")
        return False
    
    if save_json(NOTES_FILE, notes):
        print(f"✓ 笔记已删除 [#{note_id}]")
        return True
    return False
