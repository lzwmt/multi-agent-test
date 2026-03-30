---
name: cli-anything-mdproc
description: Markdown 文档处理器 CLI，支持创建、编辑、导出 Markdown 文档，具有状态管理和撤销/重做功能
---

# CLI-Anything Markdown Processor

用于创建和管理 Markdown 文档的状态化 CLI 工具。

## 安装

```bash
pip install -e /root/.openclaw/workspace/demo-markdown-cli/agent-harness
```

## 基本用法

### 创建项目
```bash
cli-anything-mdproc new -n mydoc -t "文档标题" -a "作者" -o mydoc.json
```

### 添加内容
```bash
cli-anything-mdproc -p mydoc.json heading "章节标题"
cli-anything-mdproc -p mydoc.json paragraph "段落内容"
cli-anything-mdproc -p mydoc.json code "print('hello')" -l python
cli-anything-mdproc -p mydoc.json list "项目 1" "项目 2" "项目 3"
cli-anything-mdproc -p mydoc.json quote "引用内容"
```

### 导出文档
```bash
cli-anything-mdproc -p mydoc.json export output.md
cli-anything-mdproc -p mydoc.json export output.html --format html
```

### JSON 输出模式（供 Agent 使用）
```bash
cli-anything-mdproc --json -p mydoc.json info
# 输出：{"name": "mydoc", "title": "...", "elements": 5, ...}
```

## 命令组

| 命令 | 说明 | 示例 |
|------|------|------|
| `new` | 创建新项目 | `new -n name -t "Title" -o path.json` |
| `open` | 打开现有项目 | `open -p path.json` |
| `save` | 保存当前项目 | `save` |
| `heading` | 添加标题 | `heading "标题" -l 2` |
| `paragraph` | 添加段落 | `paragraph "内容"` |
| `code` | 添加代码块 | `code "print()" -l python` |
| `list` | 添加列表 | `list "a" "b" "c"` |
| `quote` | 添加引用 | `quote "引用"` |
| `table` | 添加表格 | `table "A" "B" -r "1,2" -r "3,4"` |
| `export` | 导出文件 | `export output.md` |
| `info` | 显示项目信息 | `info` |
| `preview` | 预览 Markdown | `preview` |
| `undo` | 撤销 | `undo` |
| `redo` | 重做 | `redo` |

## Agent 使用指南

1. **始终使用 `--json` 标志**获取机器可读输出
2. **先创建项目**，再进行其他操作
3. **使用 `-p` 指定项目文件**保持状态
4. **导出前使用 `info` 检查**项目状态

## 错误处理

- 项目未加载时操作会返回 `{"success": false, "error": "No project is currently open"}`
- 文件已存在时导出需要 `--overwrite` 标志
