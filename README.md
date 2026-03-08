# 个人效率工具集

一个简洁的命令行效率工具，包含任务管理、番茄钟和笔记功能。

## 功能

- **任务管理**: 添加、列出、完成、删除待办事项
- **番茄钟**: 专注计时，支持自定义时长和统计
- **笔记**: 快速记录想法，支持标签和搜索

## 安装

无需安装，确保 Python 3.7+ 即可：

```bash
cd multi-agent-test/src
```

## 使用

### 任务管理

```bash
# 添加任务
python main.py task add "完成报告" --priority high

# 列出未完成任务
python main.py task list

# 列出所有任务（包括已完成）
python main.py task list --all

# 标记任务完成
python main.py task done 1

# 删除任务
python main.py task delete 1
```

优先级: `high` (高) / `medium` (中) / `low` (低)

### 番茄钟

```bash
# 开始 25 分钟番茄钟（默认）
python main.py pomodoro start

# 开始 45 分钟番茄钟
python main.py pomodoro start --minutes 45

# 查看统计
python main.py pomodoro stats
```

- 专注时显示进度条和倒计时
- 按 `Ctrl+C` 可取消计时
- 自动记录完成历史

### 笔记

```bash
# 添加笔记
python main.py note add "会议要点..." --tags work,meeting

# 列出所有笔记
python main.py note list

# 按标签筛选
python main.py note list --tag work

# 搜索笔记
python main.py note search "会议"

# 查看笔记详情
python main.py note show 1

# 删除笔记
python main.py note delete 1
```

## 数据存储

所有数据保存在 `data/` 目录下的 JSON 文件中：

- `tasks.json` - 任务数据
- `pomodoro_stats.json` - 番茄钟统计
- `notes.json` - 笔记数据

## 帮助

查看各模块详细帮助：

```bash
python main.py --help
python main.py task --help
python main.py pomodoro --help
python main.py note --help
```
