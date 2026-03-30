# Stock Analysis Skill

股票分析团队技能，使用 ClawTeam 多代理协作，自动使用智能搜索获取实时数据。

## 团队结构 (使用 hedge-fund 模板)

| 角色 | 类型 | 职责 |
|------|------|------|
| **portfolio-manager** | leader | 协调分析并做出最终投资决策 |
| **buffett-analyst** | value-analyst | 价值投资分析（巴菲特风格） |
| **growth-analyst** | growth-analyst | 增长/颠覆性分析 |
| **technical-analyst** | technical-analyst | 技术指标分析 |
| **fundamentals-analyst** | fundamentals-analyst | 基本面和财务指标分析 |
| **sentiment-analyst** | sentiment-analyst | 新闻和内部人情绪分析 |
| **risk-manager** | risk-manager | 整合信号并评估投资组合风险 |

**共 7 个子代理协作分析**

## 搜索配置

### 默认搜索方式

**子代理使用系统默认搜索工具获取信息**
- web_search: 默认搜索工具
- 不强制使用智能搜索脚本

### 可选：智能搜索路由规则

| 场景 | 引擎 | 原因 |
|------|------|------|
| 普通查询 | **Tavily** | 速度快、结构化 |
| 实时/动态内容 | **Lightpanda** | 需要浏览器渲染 |
| 引擎失败 | **自动回退** | 保证可用性 |

### 搜索模板

```bash
# 股价查询
node scripts/smart-search.js "{股票代码} 实时股价" --count 5

# 财报查询
node scripts/smart-search.js "{股票代码} 最新财报 2025" --count 5

# 新闻查询
node scripts/smart-search.js "{股票代码} 最新消息" --count 5

# 行业分析
node scripts/smart-search.js "{行业} 行业趋势 2025" --count 5
```

### 搜索模板

```javascript
// 股价查询
node scripts/smart-search.js "{股票代码} 实时股价" --count 5

// 财报查询
node scripts/smart-search.js "{股票代码} 最新财报 2025" --count 5

// 新闻查询
node scripts/smart-search.js "{股票代码} 最新消息" --count 5

// 行业分析
node scripts/smart-search.js "{行业} 行业趋势 2025" --count 5
```

## 使用方式

### 命令行
```bash
cd /root/.openclaw/workspace/skills/stock-analysis
./run.sh <股票代码>

# 示例
./run.sh 002514
```

### OpenClaw 中
```
分析股票：002514
```

或直接调用：
```bash
cd /root/.openclaw/workspace && ./skills/stock-analysis/run.sh 002514
```

### 查看分析进度
```bash
# 查看团队状态
clawteam team status --team-name <团队名称>

# 查看看板
clawteam board --team-name <团队名称>

# 查看消息日志
clawteam inbox log --team-name <团队名称>
```

### 工作原理

1. `run.sh` 调用 `clawteam launch hedge-fund` 启动 7 子代理团队
2. `--goal` 参数强制要求所有子代理使用智能搜索脚本
3. 每个分析师并行搜索各自领域的数据
4. portfolio-manager 汇总所有分析结果，生成最终投资决策
5. **分析完成后自动收集并发送所有报告文件**

### 自动报告收集

当7个子代理全部完成分析后，系统会自动：
- 收集各分析师生成的报告文件
- 生成团队综合汇总报告
- **自动发送所有报告文件到Discord频道**

收集的报告包括：
- `*_buffett.md` - 巴菲特价值投资分析报告
- `*_growth.md` - 增长/颠覆性分析报告
- `*_fundamentals.md` - 基本面分析报告
- `*_technical.md` - 技术面分析报告
- `*_sentiment.md` - 市场情绪分析报告
- `*_risk.md` - 风险评估报告
- `*_team_summary.md` - 团队综合汇总报告

### 手动收集报告

如果需要手动收集报告：
```bash
cd /root/.openclaw/workspace/skills/stock-analysis
./collect-and-send.sh <团队名称> <股票代码>

# 示例
./collect-and-send.sh stock-002640-1774186155 002640
```

## 输出格式

```markdown
# AAPL 股票分析报告

## 基本信息
- 当前价格: $XXX
- 涨跌幅: +X.XX%
- 市值: $XXX B

## 关键指标
- P/E: XX.X
- EPS: $X.XX
- 52周高低: $XXX - $XXX

## 近期新闻
1. ...
2. ...

## 分析师观点
- 买入: X
- 持有: X
- 卖出: X

## 风险提示
...
```

## 依赖

- ClawTeam CLI
- 智能搜索脚本 (`scripts/smart-search.js`)
- Lightpanda 容器 (端口 9222)
- Tavily API Key (已配置)
