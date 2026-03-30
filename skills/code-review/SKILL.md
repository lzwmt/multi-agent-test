# Code Review Skill

代码审查与测试技能，用于自动检查脚本代码质量、逻辑正确性和潜在问题。

## 功能

- 语法检查 (bash/python/js)
- 变量使用检查
- 错误处理检查
- 安全漏洞扫描
- 逻辑测试（dry-run 模式）
- 生成审查报告

## 使用方式

### 命令行
```bash
cd /root/.openclaw/workspace/skills/code-review
./review.sh <脚本路径>

# 示例
./review.sh ../stock-analysis/run.sh
```

### OpenClaw 中
```
审查代码: /path/to/script.sh
测试脚本: /path/to/script.sh
检查代码质量: /path/to/script.py
```

## 审查项目

| 检查项 | 说明 | 严重程度 |
|--------|------|----------|
| 语法错误 | 脚本是否能正常解析 | 🔴 高 |
| 未定义变量 | 使用未定义的变量 | 🔴 高 |
| 错误处理 | 是否有 `set -e` 或错误检查 | 🟠 中 |
| 硬编码值 | 魔法数字/字符串 | 🟡 低 |
| 代码注释 | 关键逻辑是否有注释 | 🟡 低 |
| 安全漏洞 | 命令注入、路径遍历等 | 🔴 高 |

## 输出格式

```markdown
# 代码审查报告

## 文件: script.sh

### 🔴 严重问题
- [ ] 第15行: 未定义变量 `$UNDEFINED_VAR`
- [ ] 第23行: 缺少错误处理

### 🟠 中等问题
- [ ] 第10行: 硬编码路径 `/tmp/fixed-path`

### 🟡 建议改进
- [ ] 添加函数注释
- [ ] 使用配置文件替代硬编码值

### ✅ 通过检查
- 语法正确
- 变量命名规范
- 权限设置正确
```

## 依赖

- shellcheck (bash脚本检查)
- python3 (python代码检查)
- node (js代码检查)
