# Smart Search Skill

智能搜索技能，自动路由到最佳搜索引擎。

## 路由策略

| 场景 | 引擎 | 原因 |
|------|------|------|
| 普通查询 | Tavily | 速度快、结构化 |
| 实时/动态内容 | Lightpanda | 需要浏览器渲染 |
| 引擎失败 | 自动回退 | 保证可用性 |

## 使用方式

### 命令行
```bash
node scripts/smart-search.js "查询内容" [--count N] [--engine auto|tavily|lightpanda]
```

### 作为默认搜索
在 `.openclaw/config.json` 中添加：
```json
{
  "tools": {
    "web_search": {
      "provider": "script",
      "script": "/root/.openclaw/workspace/scripts/smart-search.js"
    }
  }
}
```

## 依赖

- Tavily API Key (已配置)
- Lightpanda 容器 (端口 9222)

## 文件

- `scripts/smart-search.js` - 主脚本
- `scripts/lightpanda-search.js` - Lightpanda 搜索
- `scripts/web_search_tavily.js` - Tavily 包装
