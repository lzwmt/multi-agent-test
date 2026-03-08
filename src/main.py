#!/usr/bin/env python3
"""
个人效率工具集 - 命令行入口

功能：
- 任务管理：添加、列出、完成、删除任务
- 番茄钟：专注计时、统计
- 笔记：添加、列出、搜索笔记

用法：
    python main.py task add "任务标题" --priority high
    python main.py pomodoro start --minutes 25
    python main.py note add "笔记内容" --tags work
"""
import argparse
import sys
from typing import List

# 导入各模块
from tasks import add_task, list_tasks, complete_task, delete_task
from pomodoro import start_pomodoro, show_stats
from notes import add_note, list_notes, search_notes, show_note, delete_note


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='productivity-toolkit',
        description='个人效率工具集 - 任务管理、番茄钟、笔记',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 任务管理
  python main.py task add "完成报告" --priority high
  python main.py task list
  python main.py task done 1
  python main.py task delete 1

  # 番茄钟
  python main.py pomodoro start
  python main.py pomodoro start --minutes 45
  python main.py pomodoro stats

  # 笔记
  python main.py note add "会议要点..." --tags work,meeting
  python main.py note list
  python main.py note search "会议"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # ========== 任务管理 ==========
    task_parser = subparsers.add_parser('task', help='任务管理')
    task_subparsers = task_parser.add_subparsers(dest='task_action', help='任务操作')
    
    # task add
    task_add = task_subparsers.add_parser('add', help='添加任务')
    task_add.add_argument('title', help='任务标题')
    task_add.add_argument('--priority', '-p', choices=['high', 'medium', 'low'],
                          default='medium', help='优先级 (默认: medium)')
    
    # task list
    task_list = task_subparsers.add_parser('list', help='列出任务')
    task_list.add_argument('--all', '-a', action='store_true',
                           help='显示所有任务（包括已完成）')
    
    # task done
    task_done = task_subparsers.add_parser('done', help='标记任务完成')
    task_done.add_argument('task_id', type=int, help='任务ID')
    
    # task delete
    task_delete = task_subparsers.add_parser('delete', help='删除任务')
    task_delete.add_argument('task_id', type=int, help='任务ID')
    
    # ========== 番茄钟 ==========
    pomodoro_parser = subparsers.add_parser('pomodoro', help='番茄钟')
    pomodoro_subparsers = pomodoro_parser.add_subparsers(dest='pomodoro_action',
                                                          help='番茄钟操作')
    
    # pomodoro start
    pomodoro_start = pomodoro_subparsers.add_parser('start', help='开始番茄钟')
    pomodoro_start.add_argument('--minutes', '-m', type=int, default=25,
                                help='专注时长（分钟，默认: 25）')
    
    # pomodoro stats
    pomodoro_subparsers.add_parser('stats', help='显示统计')
    
    # ========== 笔记 ==========
    note_parser = subparsers.add_parser('note', help='笔记管理')
    note_subparsers = note_parser.add_subparsers(dest='note_action', help='笔记操作')
    
    # note add
    note_add = note_subparsers.add_parser('add', help='添加笔记')
    note_add.add_argument('content', help='笔记内容')
    note_add.add_argument('--tags', '-t', help='标签（逗号分隔，如: work,meeting）')
    
    # note list
    note_list = note_subparsers.add_parser('list', help='列出笔记')
    note_list.add_argument('--tag', help='按标签筛选')
    
    # note search
    note_search = note_subparsers.add_parser('search', help='搜索笔记')
    note_search.add_argument('keyword', help='搜索关键词')
    
    # note show
    note_show = note_subparsers.add_parser('show', help='显示笔记详情')
    note_show.add_argument('note_id', type=int, help='笔记ID')
    
    # note delete
    note_delete = note_subparsers.add_parser('delete', help='删除笔记')
    note_delete.add_argument('note_id', type=int, help='笔记ID')
    
    return parser


def handle_task(args) -> int:
    """处理任务管理命令"""
    action = args.task_action
    
    if action == 'add':
        add_task(args.title, args.priority)
    elif action == 'list':
        list_tasks(show_all=args.all)
    elif action == 'done':
        complete_task(args.task_id)
    elif action == 'delete':
        delete_task(args.task_id)
    else:
        print("请指定操作: add, list, done, delete")
        print("使用: python main.py task --help")
        return 1
    
    return 0


def handle_pomodoro(args) -> int:
    """处理番茄钟命令"""
    action = args.pomodoro_action
    
    if action == 'start':
        start_pomodoro(args.minutes)
    elif action == 'stats':
        show_stats()
    else:
        print("请指定操作: start, stats")
        print("使用: python main.py pomodoro --help")
        return 1
    
    return 0


def handle_note(args) -> int:
    """处理笔记命令"""
    action = args.note_action
    
    if action == 'add':
        tags = args.tags.split(',') if args.tags else []
        add_note(args.content, tags)
    elif action == 'list':
        list_notes(tag=args.tag)
    elif action == 'search':
        search_notes(args.keyword)
    elif action == 'show':
        show_note(args.note_id)
    elif action == 'delete':
        delete_note(args.note_id)
    else:
        print("请指定操作: add, list, search, show, delete")
        print("使用: python main.py note --help")
        return 1
    
    return 0


def main(argv: List[str] = None) -> int:
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == 'task':
            return handle_task(args)
        elif args.command == 'pomodoro':
            return handle_pomodoro(args)
        elif args.command == 'note':
            return handle_note(args)
        else:
            parser.print_help()
            return 0
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 130
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
