# Test Plan - CLI-Anything Markdown Processor

## 测试清单

- `test_core.py`: 15 个单元测试
- `test_full_e2e.py`: 10 个端到端测试
- `test_cli_subprocess.py`: 8 个子进程测试

**总计**: 33 个测试

## 单元测试计划

### test_core.py

测试 `core/project.py` 和 `core/session.py` 的核心功能：

1. **Project 创建** - 测试基本项目创建
2. **Project 序列化** - 测试 to_dict/from_dict
3. **添加元素** - 测试各种元素类型（标题、段落、代码、列表等）
4. **Markdown 渲染** - 测试 to_markdown() 输出
5. **保存/加载** - 测试文件持久化
6. **Session 撤销** - 测试 undo 功能
7. **Session 重做** - 测试 redo 功能
8. **Session 历史** - 测试历史记录

## E2E 测试计划

### test_full_e2e.py

真实场景测试：

1. **完整文档创建流程** - 创建→添加内容→导出
2. **Markdown 导出验证** - 验证输出的 MD 文件
3. **HTML 导出验证** - 验证 HTML 结构和内容
4. **多元素文档** - 测试复杂文档结构
5. **撤销/重做工作流** - 测试状态管理

## 子进程测试计划

### test_full_e2e.py - CLI Subprocess

测试安装的 CLI 命令：

1. **--help 输出** - 验证命令帮助
2. **项目创建** - 创建新项目
3. **info 命令** - 显示项目信息
4. **添加标题** - heading 命令
5. **添加段落** - paragraph 命令
6. **导出 Markdown** - export 命令
7. **预览** - preview 命令

---

## 测试结果

```
============================== 26 passed in 1.36s ==============================
```

### 单元测试 (15 个)
- TestProject: 11 个测试 - 全部通过
- TestSession: 4 个测试 - 全部通过

### E2E 测试 (11 个)
- TestE2EWorkflow: 4 个测试 - 全部通过
- TestCLISubprocess: 7 个测试 - 全部通过

**总计**: 26/26 通过 (100%)
