# CLI-Anything Markdown Processor

一个用于 Markdown 文档的状态化 CLI 工具。

## 安装

### 1. 安装 Python 依赖

```bash
cd /root/.openclaw/workspace/demo-markdown-cli/agent-harness
pip install -e .
```

### 2. 验证安装

```bash
which cli-anything-mdproc
cli-anything-mdproc --help
```

## 快速开始

### 创建新项目

```bash
cli-anything-mdproc new -n mydoc -t "我的文档" -a "作者" -o mydoc.json
```

### 进入 REPL 交互模式

```bash
cli-anything-mdproc -p mydoc.json
```

### 使用子命令（非交互模式）

```bash
# 创建项目
cli-anything-mdproc new -n tutorial -t "教程" -o tutorial.json

# 添加内容
cli-anything-mdproc -p tutorial.json heading "第一章"
cli-anything-mdproc -p tutorial.json paragraph "这是正文内容"
cli-anything-mdproc -p tutorial.json code "print('Hello')" -l python
cli-anything-mdproc -p tutorial.json list "项目 1" "项目 2" "项目 3"

# 导出
cli-anything-mdproc -p tutorial.json export output.md
cli-anything-mdproc -p tutorial.json export output.html --format html
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `new` | 创建新项目 |
| `open` | 打开现有项目 |
| `save` | 保存当前项目 |
| `heading` | 添加标题 |
| `paragraph` | 添加段落 |
| `code` | 添加代码块 |
| `list` | 添加列表 |
| `quote` | 添加引用 |
| `table` | 添加表格 |
| `hr` | 添加分割线 |
| `export` | 导出文件 |
| `info` | 显示项目信息 |
| `preview` | 预览 Markdown |
| `undo` | 撤销 |
| `redo` | 重做 |
| `history` | 显示历史 |

## JSON 输出模式

所有命令支持 `--json` 标志，输出机器可读的 JSON：

```bash
cli-anything-mdproc --json new -n test -o test.json
cli-anything-mdproc --json -p test.json info
```

## 测试

```bash
cd /root/.openclaw/workspace/demo-markdown-cli/agent-harness
python -m pytest cli_anything/mdproc/tests/ -v
```
