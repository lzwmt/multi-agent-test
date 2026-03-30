# 子代理搜索配置

## 默认搜索方式

**禁止使用 `web_search` 工具**（Brave API）

**必须使用智能搜索脚本**：
```bash
node /root/.openclaw/workspace/scripts/smart-search.js "查询内容" --count 10
```

## 智能搜索路由规则

- 普通查询 → 自动使用 Tavily
- 实时/动态内容（价格、股价等）→ 自动使用 Lightpanda
- 引擎失败 → 自动回退

## 使用示例

```javascript
import { execSync } from 'child_process';

const result = execSync(
  'node /root/.openclaw/workspace/scripts/smart-search.js "查询内容" --count 5',
  { encoding: 'utf8' }
);

const data = JSON.parse(result);
// data.results 包含搜索结果
```

## 依赖检查

执行搜索前确认：
1. Lightpanda 容器运行中（端口 9222）
2. Tavily API key 已配置

## 输出格式

```json
{
  "success": true,
  "query": "...",
  "results": [
    { "title": "...", "url": "...", "description": "..." }
  ],
  "engine": "tavily|lightpanda",
  "total_time": "1.5s"
}
```
