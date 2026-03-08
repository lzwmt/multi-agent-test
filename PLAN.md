# 多 Agent 协作测试项目：个人效率工具集

## 目标
30 分钟内完成一个可运行的「个人效率工具集」——包含任务管理 + 番茄钟 + 笔记速记功能。

## Agent 分工

| Agent | 职责 | 输出物 |
|-------|------|--------|
| main | 主控协调、架构设计、最终整合 | PLAN.md、架构方案、总结报告 |
| creative | 品牌创意 | 工具集名称 + slogan |
| coder | 技术实现 | 可运行的代码 |
| writer | 文档撰写 | README.md、使用说明 |

## 执行流程

```
Phase 1 (并行):
  - main: 输出技术架构设计 → /workspace/multi-agent-test/architecture.md
  - creative: 输出品牌方案 → /workspace/multi-agent-test/branding.md

Phase 2 (串行):
  - coder: 基于架构实现代码 → /workspace/multi-agent-test/src/

Phase 3 (并行):
  - writer: 基于代码写文档 → /workspace/multi-agent-test/README.md
  - main: 测试代码、准备总结

Phase 4:
  - main: 整合输出、生成测试报告
```

## 技术约束
- 语言：Python 3.10+
- 形式：CLI 工具或简单 Web 应用
- 数据存储：本地 JSON 文件
- 依赖：尽量使用标准库，第三方库需说明

## 功能需求
1. 任务管理：添加、完成、列出、删除任务
2. 番茄钟：25 分钟计时、休息提醒、统计
3. 笔记速记：快速记录、查看、搜索笔记

## 成功标准
- [ ] 代码可运行无报错
- [ ] 三个功能都可用
- [ ] 有完整的 README
- [ ] 有品牌名称和 slogan
