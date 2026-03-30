# Lightpanda Search Skill

使用 Lightpanda 浏览器执行网页搜索，替代传统 API 搜索。

## 配置

确保 Lightpanda 容器在运行：
```bash
docker run -d --name lightpanda -p 9222:9222 lightpanda/browser:nightly
```

## 使用

### 命令行
```bash
node scripts/lightpanda-search.js "search query" [count]
```

### 在 OpenClaw 中

当用户请求搜索时，优先使用此技能：

```javascript
import { search } from './lightpanda-search.js';

const results = await search("query", { count: 10 });
```

## 特性

- ✅ 无需 API key
- ✅ 内存占用极低（~12MB vs ~140MB Chrome）
- ✅ 速度快（2 倍于 Chrome）
- ✅ 支持 JavaScript 渲染的页面
- ✅ 可扩展为支持更多搜索引擎

## 限制

- 依赖 DuckDuckGo Lite（无 JS 版本）
- 不支持高级搜索语法
- 无搜索结果缓存
