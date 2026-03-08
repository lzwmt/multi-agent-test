# 技术架构设计

## 整体架构

```
productivity-toolkit/
├── main.py              # 入口文件，命令行解析
├── tasks.py             # 任务管理模块
├── pomodoro.py          # 番茄钟模块
├── notes.py             # 笔记模块
├── storage.py           # 数据存储模块
└── data/                # 数据目录
    ├── tasks.json
    ├── pomodoro_stats.json
    └── notes.json
```

## 模块设计

### 1. main.py
- 使用 argparse 处理命令行参数
- 子命令：task, pomodoro, note

### 2. tasks.py
- `add_task(title, priority)` - 添加任务
- `list_tasks()` - 列出未完成任务
- `complete_task(task_id)` - 标记完成
- `delete_task(task_id)` - 删除任务

### 3. pomodoro.py
- `start_pomodoro(minutes=25)` - 开始计时
- `show_stats()` - 显示今日番茄统计
- 支持 Ctrl+C 中断处理

### 4. notes.py
- `add_note(content, tags=[])` - 添加笔记
- `list_notes()` - 列出笔记
- `search_notes(keyword)` - 搜索笔记

### 5. storage.py
- 统一的 JSON 文件读写接口
- 自动创建 data 目录

## 命令行接口设计

```bash
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
```
