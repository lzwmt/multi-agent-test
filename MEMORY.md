# MEMORY.md - Long-Term Memory

> 共享协议同步于 2026-04-01 | Your curated memories. Distill from daily notes. Remove when outdated.

---

## 共享协议 (Shared Protocol)

### 核心身份
高效执行助手

### 语气风格
简洁、技术化、直奔主题

### 安全边界
- 修改.env或credentials/文件夹前必须经过用户的二次确认
- 个人身份信息(PII)发送给外部API前必须脱敏
- 单笔超过$50的操作必须在Telegram里获得用户的"Y"确认
            
### 禁止事项
- 不要说"我很乐意帮助"、"好问题"等客套话
- 不要在没有明确指令的情况下删除文件
- 不要在用户睡觉时间（23:00-07:00）发送非紧急通知

### 沟通风格
direct + 关键解释

---

## About 老板 (lzwmt)

### Key Context
- **职业**: 程序员
- **当前目标**: 学习新技能、优化工作流程
- **1年愿景**: 掌握技术、换行业、被动收入
- **理想生活**: 时间自由、远程工作、财务自由

### Preferences Learned
- **高效时段**: 下午
- **沟通偏好**: 实时、直接
- **信息需求**: direct + 关键解释
- **子代理工具调用**: 允许工具，但需设置限制（最多3次调用，失败时停止重试，避免浏览器死循环）
- **代码审查**: 自动使用 agency-agents-converted/code-reviewer 代理，我负责监控进度
- **脚本开发**: 自动使用 script-dev skill，devops-automator 写 + code-reviewer 审

### Important Dates
[Birthdays, anniversaries, deadlines they care about]

### Accounts
- **GitHub**: 290980025@qq.com

---

## 当前项目: AI新闻短视频生成器

### 脚本
- `make_video_from_cache.sh` - 从缓存生成视频
- `news_video_generator.sh` - 完整流程(需修复)

### 素材缓存
- `/root/.openclaw/workspace/news_cache.json` - 新闻数据(避免重复调用API)

### 技术栈
- 36氪新闻源 → Summarize(Gemini) → 摘要 → Playwright动态截图 → ffmpeg合成 → BGM → 视频

### 待调试
- 摘要显示完整度
- 分类切换(AI/财经)

---

## Skills

### script-dev
**位置**: `skills/script-dev/`
**功能**: 自动脚本开发（写+审）
**触发**: "写脚本"、"开发脚本"、"创建脚本"
**流程**:
1. devops-automator 编写脚本
2. code-reviewer 自动审查
3. 输出审查报告

### stock-analyzer
**位置**: `~/.openclaw/skills/stock-analyzer/`
**功能**: 股票实时技术分析、AI预测、自动盯盘
**触发**: "分析股票"、"股票分析"、"看看xxx股"、"xxx股票"
**流程**:
1. 直接执行 `python3 ~/.openclaw/skills/stock-analyzer/stock_analysis_v2.py`
2. 或调用 `realtime_data.py` 获取实时数据
3. 输出技术分析报告（价格、均线、RSI、MACD等）
**注意**: 股票分析时必须**主动使用此技能**，不要浏览器爬取

### clawteam
**位置**: `~/.openclaw/workspace/skills/clawteam/SKILL.md`
**功能**: 多代理团队协调，并行分析股票
**触发**: "启动团队分析股票"、"用clawteam分析"、"7个子代理分析"
**流程**:
1. 使用 `clawteam` CLI 创建团队和任务
2. 并行 spawn 多个子代理（每个代理分析一个维度）
3. 监控进度，处理超时
4. 汇总结果给用户
**注意**: 子代理默认超时1分钟太短，需要在任务中设置更长超时或分阶段执行

---

## Lessons Learned

### 2026-03-31 - CLIProxyAPI + OpenAI Codex 深度调试
- **免费 tier OpenAI 账号无法走 REST API**，只能通过 Codex CLI 协议
- **Codex CLI 需要 session cookie**（`__Secure-next-auth.session-token`），不只是 OAuth access_token
- **注册脚本失效原因**：OpenAI 改了 `/api/auth/session`，不再返回 `accessToken` 字段
- **CLIProxyAPI 架构**：auth 文件 → conductor 选账号 → codex_executor 发请求到 `chatgpt.com/backend-api/codex/responses`
- **结论**：免费 tier + 无 session cookie = Codex CLI 401 无解。需要转向 Claude OAuth 路径

---

## Ongoing Context

### Active Projects
- **CLIProxyAPI**: 已部署在 `119.28.106.55:8317`，101 个 Codex auth 文件（免费 tier）
- **CLIProxyAPI 编译**: `/home/cpa/CLIProxyAPI_src`（Go 环境需 `export PATH=/usr/local/go/bin:$PATH`）
- **OpenAI 注册**: 脚本在 `openai_register/`，能注册但 token 提取失败（OpenAI API 变更）

### Key Decisions Made
- **OpenAI 免费 tier 不支持 REST API** — 只能通过 Codex CLI WebSocket 协议，但还需要 session cookie
- **auth 文件需要 session_token** — 当前只有 access_token/refresh_token，缺 ChatGPT 登录 Cookie
- **注册脚本 token 提取失效** — OpenAI 改了 `/api/auth/session`，不再返回 accessToken
- **建议转向 Claude** — OAuth token 直接能用，不需要 session cookie

### Things to Remember
- CLIProxyAPI auth 文件格式：需要 `account_id`、`client_id` 字段（已批量修复）
- CLIProxyAPI 调试模式：`debug: true` 在 config.yaml 中，可看到详细认证日志
- `missing_end_user_auth` = 缺 session cookie，不是 token 过期
- 代理 7890 端口在用户本地电脑上，需要用户开启
- 用户已多次尝试手动登录 Claude Code，都卡在邮箱验证码（临时邮箱无法收码）

---

## Relationships & People

### [Person Name]
[Who they are, relationship to human, relevant context]

---

*Review and update periodically. Daily notes are raw; this is curated.*
