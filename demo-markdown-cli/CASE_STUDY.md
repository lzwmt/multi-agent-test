# CLI-Anything 案例演示：Markdown 文档处理器

## 项目概述

本案例演示如何使用 CLI-Anything 方法论为 Markdown 文档处理创建一个完整的 CLI 工具。

## 项目结构

```
demo-markdown-cli/
└── agent-harness/
    ├── setup.py                          # Python 包配置
    └── cli_anything/
        └── mdproc/                       # 主包
            ├── __init__.py
            ├── __main__.py
            ├── mdproc_cli.py             # CLI 入口
            ├── README.md                 # 使用文档
            ├── core/                     # 核心模块
            │   ├── project.py            # 项目管理
            │   ├── session.py            # 会话管理 (撤销/重做)
            │   └── export.py             # 导出功能
            ├── utils/
            │   └── repl_skin.py          # 统一 REPL 界面
            ├── skills/
            │   └── SKILL.md              # AI Agent 技能定义
            └── tests/
                ├── TEST.md               # 测试计划和结果
                ├── test_core.py          # 单元测试 (15 个)
                └── test_full_e2e.py      # E2E 测试 (11 个)
```

## 安装

```bash
cd /root/.openclaw/workspace/demo-markdown-cli/agent-harness
pip install -e . --break-system-packages
```

## 使用示例

### 1. 创建新项目

```bash
cli-anything-mdproc new -n tutorial -t "OpenClaw 使用教程" -a "拼好猫" -o tutorial.json
```

输出：
```
✓ Created project: tutorial
```

### 2. 添加内容

```bash
# 添加标题
cli-anything-mdproc -p tutorial.json heading "第一章：安装"

# 添加段落
cli-anything-mdproc -p tutorial.json paragraph "OpenClaw 是一个强大的 AI 代理框架。"

# 添加代码块
cli-anything-mdproc -p tutorial.json code "npm install -g openclaw" -l bash

# 添加列表
cli-anything-mdproc -p tutorial.json list-items "安装 Node.js" "安装 OpenClaw" "配置 API"

# 添加引用
cli-anything-mdproc -p tutorial.json quote "Text > Brain 📝"
```

### 3. 预览内容

```bash
cli-anything-mdproc -p tutorial.json preview
```

输出：
```markdown
# OpenClaw 使用教程

*Author: 拼好猫*

# 第一章：安装

OpenClaw 是一个强大的 AI 代理框架。

```bash
npm install -g openclaw
```

- 安装 Node.js
- 安装 OpenClaw
- 配置 API

> Text > Brain 📝
```

### 4. 查看项目信息

```bash
cli-anything-mdproc -p tutorial.json info
```

输出：
```
╔════════════════════════════════════════════╗
║            cli-anything-mdproc             ║
║                   v1.0.0                   ║
╚════════════════════════════════════════════╝

  Name: tutorial
  Title: OpenClaw 使用教程
  Author: 拼好猫
  Elements: 6
  Path: tutorial.json
```

### 5. 导出文档

```bash
# 导出为 Markdown
cli-anything-mdproc -p tutorial.json export tutorial.md

# 导出为 HTML
cli-anything-mdproc -p tutorial.json export tutorial.html --format html
```

## 核心功能

### 元素类型

| 类型 | 命令 | 示例 |
|------|------|------|
| 标题 | `heading` | `heading "标题" -l 2` |
| 段落 | `paragraph` | `paragraph "内容"` |
| 代码 | `code` | `code "print()" -l python` |
| 列表 | `list-items` | `list-items "a" "b" "c"` |
| 引用 | `quote` | `quote "引用内容"` |
| 表格 | `table` | `table "A" "B" -r "1,2"` |
| 分割线 | `hr` | `hr` |

### 导出格式

- **Markdown** (.md) - 源代码格式
- **HTML** (.html) - 带样式的网页
- **PDF** (.pdf) - 需要 weasyprint

## 测试结果

```
============================== 26 passed in 1.36s ==============================
```

- 单元测试：15 个 (Project + Session)
- E2E 测试：11 个 (工作流 + CLI 子进程)

## 关键设计

### 1. 文件基础状态管理

每个命令独立加载/保存项目文件，确保子进程模式下状态一致。

### 2. 统一 REPL 界面

使用 `ReplSkin` 提供一致的交互体验，自动检测并显示 SKILL.md 路径。

### 3. AI Agent 友好

- 所有命令支持 `--json` 标志
- 结构化输出便于解析
- SKILL.md 提供完整的 API 文档

### 4. 真实后端集成

导出功能使用真实的转换库：
- Markdown → 使用 `markdown` 库
- HTML → 使用 `markdown` + 自定义模板
- PDF → 使用 `weasyprint`

## 扩展方法

### 添加新元素类型

1. 在 `core/project.py` 的 `Project._render_element()` 添加渲染逻辑
2. 在 `mdproc_cli.py` 添加新命令
3. 在 `test_core.py` 添加单元测试

### 添加新导出格式

1. 在 `core/export.py` 添加导出函数
2. 在 `export` 命令中添加新格式选项
3. 在 `test_full_e2e.py` 添加测试

## 总结

这个案例展示了 CLI-Anything 方法论的核心原则：

1. ✅ **真实后端集成** - 使用真实的转换库
2. ✅ **结构化 CLI** - Click + JSON 输出
3. ✅ **状态管理** - 文件持久化 + 会话状态
4. ✅ **统一界面** - ReplSkin 提供一致体验
5. ✅ **完整测试** - 单元测试 + E2E 测试
6. ✅ **Agent 友好** - SKILL.md + JSON 模式

---

*案例完成时间：2026-03-20*
*测试通过率：100% (26/26)*
