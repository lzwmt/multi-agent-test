# Script Development Skill

> 自动化脚本开发流程 - 写脚本 + 代码审查一站式完成

## Description

使用 devops-automator 代理编写脚本，然后使用 code-reviewer 代理自动审查，确保代码质量。

**工作流程：**
1. devops-automator 根据需求编写脚本
2. code-reviewer 自动审查代码
3. 输出审查报告和改进建议

## Usage

### 交互式使用

直接描述需求：
```
写一个备份脚本，功能：...
```

### 命令行使用

```bash
./dev.sh "脚本需求描述" [输出路径]
```

示例：
```bash
./dev.sh "备份指定目录到/tmp/backup，保留7天" ./backup.sh
```

## 输出

- 生成的脚本文件
- 代码审查报告（包含 🔴🟡💭 评级）
- 改进建议

## 代理分工

| 代理 | 职责 |
|------|------|
| devops-automator | 编写脚本，实现功能需求 |
| code-reviewer | 审查代码，检查安全/质量/最佳实践 |

## 审查维度

- ✅ 语法正确性
- 🔴 安全性（注入、遍历等）
- ⚠️ 错误处理完整性
- 💭 可维护性
- 💭 最佳实践
