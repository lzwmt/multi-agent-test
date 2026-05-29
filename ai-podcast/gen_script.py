#!/usr/bin/env python3
"""Generate podcast script using AiNaiBa API - v2 with longer content"""
import json, urllib.request, sys

with open('/tmp/.ainaba_key') as f:
    api_key = f.read().strip()

prompt = """你是播客「代码与财富」的脚本写手。请生成一期完整口播脚本。

节目定位:
- 口号: 用代码理解世界，用AI管好钱包
- 人设: 一个用AI研究投资的程序员（真实、务实、技术派）
- 总时长15-20分钟，总字数3000-4000字

今日素材:
1. 高盛英伟达财报点评：AI算力资本支出浪潮尚未触顶
2. 对冲基金对大涨芯片股获利了结，半导体板块被净卖出最多
3. 理财产品费率降至0%，降费潮

输出格式: JSON数组，每段 {"type":"xxx","text":"xxx","pause_after_ms":N}

结构要求（按顺序7段）:
- intro(~200字): 固定开场"大家好，欢迎收听「代码与财富」。我是你们的老朋友，一个每天用AI写代码也用AI研究投资的程序员。今天的口号是：用代码理解世界，用AI管好钱包。"然后引出话题
- topic段1(~500字): 事件背景，详细展开高盛说了什么、英伟达财报数据
- topic段2(~500字): 用AI工具分析的过程和发现，必须有"我用XX工具分析了XX"
- topic段3(~500字): 个人观点和判断，有依据的分析
- topic段4(~500字): 可执行建议，普通人怎么做
- tool_rec(~500字): AI工具实测推荐，详细使用体验
- outro(~100字): 一句话建议 + 固定结尾"这只是我的个人操作，不构成投资建议。如果你觉得有收获，欢迎订阅分享。我们下期再见，拜拜！"

关键: 每段必须达到指定字数！口语化，像朋友聊天。只输出JSON数组。"""

payload = json.dumps({
    "model": "gpt-4.1",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.8,
    "max_tokens": 8000
}).encode()

req = urllib.request.Request(
    "https://api-xai.ainaibahub.com/v1/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    script = json.loads(content)

    with open("/root/.openclaw/workspace/ai-podcast/output/ep02_script.json", "w") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    total = sum(len(s["text"]) for s in script)
    print(f"OK:{len(script)} segments, {total} chars")
    for i, s in enumerate(script):
        print(f"  [{i+1}] {s['type']}: {len(s['text'])}字")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
