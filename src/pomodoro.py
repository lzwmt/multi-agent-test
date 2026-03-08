"""
番茄钟模块 - 专注时间管理
"""
import time
import signal
import sys
from datetime import datetime, date
from typing import Optional
from storage import load_json, save_json


POMODORO_FILE = "pomodoro_stats.json"

# 全局变量用于处理中断
_running = False
_start_time = None
_duration = 0


def format_time(seconds: int) -> str:
    """将秒数格式化为 MM:SS"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def signal_handler(signum, frame):
    """处理 Ctrl+C 中断"""
    global _running
    if _running:
        print("\n\n⚠ 番茄钟已取消")
        _running = False
        sys.exit(0)


def start_pomodoro(minutes: int = 25) -> bool:
    """
    开始番茄钟计时
    
    Args:
        minutes: 专注时长(分钟), 默认 25 分钟
        
    Returns:
        是否成功完成
    """
    global _running, _start_time, _duration
    
    if minutes < 1:
        print("错误: 时长至少为 1 分钟")
        return False
    
    if minutes > 120:
        print("警告: 建议单次专注不超过 2 小时")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    total_seconds = minutes * 60
    _duration = minutes
    _start_time = datetime.now()
    _running = True
    
    print(f"\n🍅 番茄钟开始 - {minutes} 分钟")
    print("专注中... (按 Ctrl+C 取消)\n")
    
    try:
        for remaining in range(total_seconds, 0, -1):
            if not _running:
                return False
            
            # 显示进度
            elapsed = total_seconds - remaining
            progress = elapsed / total_seconds
            bar_length = 30
            filled = int(bar_length * progress)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            print(f"\r[{bar}] {format_time(remaining)} 剩余", end="", flush=True)
            time.sleep(1)
        
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ 番茄钟已取消")
        _running = False
        return False
    
    _running = False
    
    # 记录完成
    _record_completion(minutes)
    
    print("✓ 番茄钟完成！休息一下吧 ☕")
    return True


def _record_completion(minutes: int) -> None:
    """记录完成的番茄钟"""
    stats = load_json(POMODORO_FILE, {})
    
    today = date.today().isoformat()
    
    if today not in stats:
        stats[today] = {
            "count": 0,
            "total_minutes": 0,
            "sessions": []
        }
    
    session = {
        "start_time": _start_time.isoformat() if _start_time else datetime.now().isoformat(),
        "duration": minutes,
        "completed_at": datetime.now().isoformat()
    }
    
    stats[today]["count"] += 1
    stats[today]["total_minutes"] += minutes
    stats[today]["sessions"].append(session)
    
    save_json(POMODORO_FILE, stats)


def show_stats() -> None:
    """显示今日番茄钟统计"""
    stats = load_json(POMODORO_FILE, {})
    
    today = date.today().isoformat()
    
    print("\n📊 番茄钟统计")
    print("-" * 40)
    
    # 今日统计
    if today in stats:
        today_stats = stats[today]
        count = today_stats.get("count", 0)
        total_minutes = today_stats.get("total_minutes", 0)
        hours = total_minutes // 60
        mins = total_minutes % 60
        
        print(f"\n今日 ({today}):")
        print(f"  完成番茄钟: {count} 个")
        print(f"  专注时长: {hours}小时 {mins}分钟")
    else:
        print(f"\n今日 ({today}): 暂无记录")
    
    # 本周统计
    week_count = 0
    week_minutes = 0
    
    for day, day_stats in stats.items():
        try:
            day_date = datetime.fromisoformat(day).date()
            # 简单计算：本周（最近7天）
            if (date.today() - day_date).days < 7:
                week_count += day_stats.get("count", 0)
                week_minutes += day_stats.get("total_minutes", 0)
        except:
            continue
    
    week_hours = week_minutes // 60
    week_mins = week_minutes % 60
    
    print(f"\n本周 (最近7天):")
    print(f"  完成番茄钟: {week_count} 个")
    print(f"  专注时长: {week_hours}小时 {week_mins}分钟")
    
    # 历史总计
    total_count = sum(s.get("count", 0) for s in stats.values())
    total_minutes = sum(s.get("total_minutes", 0) for s in stats.values())
    total_hours = total_minutes // 60
    
    print(f"\n历史总计:")
    print(f"  完成番茄钟: {total_count} 个")
    print(f"  专注时长: {total_hours}小时")
    print()
