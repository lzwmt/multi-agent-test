# AI塔罗项目 — 知识库对接文档

> 本文档供 AI Agent 直接执行，完成知识库与 LLM 的对接。
> 知识库路径：`~/.openclaw/workspace/ai-tarot/`

---

## 1. 项目目标

构建一个 AI 塔罗占卜应用，用户选择牌阵 → 系统随机抽牌 → LLM 基于知识库生成解读。

## 2. 知识库文件清单

```
~/.openclaw/workspace/ai-tarot/
├── index.json              # 元数据索引
├── wands.json              # 权杖牌组 14张 (火元素)
├── cups.json               # 圣杯牌组 14张 (水元素)
├── swords.json             # 宝剑牌组 14张 (空气元素)
├── pentacles.json          # 五角星牌组 14张 (土元素)
├── major_arcana.json       # 大阿尔克纳 22张
├── spreads.json            # 8种基础牌阵
├── additional_spreads.json # 补充牌阵
├── combinations.json       # 牌义组合规则 (金钱/婚姻/旅行等)
├── reversed_methods.json   # 逆位解读方法论
├── reading_frameworks.json # 解读框架 (三层模型/9维画面/心理学)
└── reading_guide.json      # 基础解牌指南 (元素/星座/程序)
```

总大小: 86.2KB, 78张牌, 每张含正位/逆位 x 大体/关系 = 4维解读。

## 3. 数据结构定义

### 3.1 牌的数据结构 (以 wands.json 为例)

```json
{
  "suit": "权杖",
  "element": "火",
  "theme": "热情、行动、创造力、事业、挑战",
  "keywords": ["行动", "热情", "挑战", "事业", "旅行", "精力"],
  "astrological_signs": ["白羊座", "狮子座", "射手座"],
  "cards": {
    "ace": {
      "name": "权杖王牌",
      "number": 1,
      "upright": {
        "general": "大体意义文本",
        "relationship": "两性关系意义文本",
        "keywords": ["关键词1", "关键词2"]
      },
      "reversed": {
        "general": "倒立大体意义文本",
        "relationship": "倒立两性关系意义文本",
        "keywords": ["关键词1", "关键词2"]
      }
    }
  }
}
```

### 3.2 大阿尔卡纳结构 (major_arcana.json)

```json
{
  "cards": {
    "0": {
      "name": "愚人",
      "english": "The Fool",
      "upright": { "general": "...", "relationship": "...", "keywords": [...] },
      "reversed": { "general": "...", "relationship": "...", "keywords": [...] }
    }
  }
}
```

key 是字符串数字 "0"-"21"。

### 3.3 牌阵结构 (spreads.json)

```json
{
  "seven_card": {
    "name": "七张牌牌形",
    "cards": 7,
    "use": "大体上的分析，或回答特定问题",
    "positions": {
      "1": "过去 (可追溯18个月前)",
      "2": "目前状况 (前后4星期)",
      "3": "最近结果 (约3个月)",
      "4": "当事人/问题的答案",
      "5": "环绕的能量/围绕问题的能量",
      "6": "希望及恐惧",
      "7": "结果 (24个月内)"
    }
  }
}
```

### 3.4 组合规则结构 (combinations.json)

```json
{
  "marriage": {
    "name": "结婚",
    "cards": ["圣杯二", "圣杯十", "圣杯三", "正义", "权杖六"]
  },
  "money_earned": {
    "name": "赚来的钱",
    "cards": ["五角星六", "五角星八", "五角星九"]
  }
}
```

---

## 4. 需要实现的模块

### 模块 A: 抽牌引擎

功能: 从78张牌中随机抽取 N 张不重复的牌, 随机决定正位/逆位。

```python
import json
import random
from pathlib import Path

KB_DIR = Path("~/.openclaw/workspace/ai-tarot").expanduser()

def load_all_cards():
    """Load all 78 cards into a flat dict {card_name: card_data}"""
    all_cards = {}

    # Minor Arcana
    for suit_file in ["wands", "cups", "swords", "pentacles"]:
        with open(KB_DIR / f"{suit_file}.json") as f:
            data = json.load(f)
            for key, card in data["cards"].items():
                card["suit"] = data["suit"]
                card["element"] = data["element"]
                all_cards[card["name"]] = card

    # Major Arcana
    with open(KB_DIR / "major_arcana.json") as f:
        data = json.load(f)
        for key, card in data["cards"].items():
            card["suit"] = "大阿尔克纳"
            card["element"] = None
            all_cards[card["name"]] = card

    return all_cards

def draw_cards(n, all_cards):
    """Draw n unique cards, each randomly upright or reversed."""
    names = random.sample(list(all_cards.keys()), n)
    result = []
    for name in names:
        card = all_cards[name].copy()
        card["orientation"] = random.choice(["upright", "reversed"])
        result.append(card)
    return result
```

### 模块 B: 知识检索

功能: 根据抽到的牌, 从知识库中检索相关知识片段, 组装成 LLM 的 context。

```python
def load_combinations():
    with open(KB_DIR / "combinations.json") as f:
        return json.load(f)

def load_spread(spread_name):
    """Load a specific spread by name."""
    with open(KB_DIR / "spreads.json") as f:
        spreads = json.load(f)
    if spread_name in spreads:
        return spreads[spread_name]
    with open(KB_DIR / "additional_spreads.json") as f:
        extra = json.load(f)
    return extra.get("spreads", {}).get(spread_name, {})

def load_reversed_methods():
    with open(KB_DIR / "reversed_methods.json") as f:
        return json.load(f)

def load_reading_guide():
    with open(KB_DIR / "reading_guide.json") as f:
        return json.load(f)

def check_combinations(drawn_card_names, combinations):
    """Check if drawn cards match any combination rules."""
    matched = []
    for key, combo in combinations.items():
        combo_cards = set(combo.get("cards", []))
        drawn_set = set(drawn_card_names)
        if combo_cards & drawn_set:
            matched.append({
                "rule": combo["name"],
                "matched_cards": list(combo_cards & drawn_set)
            })
    return matched

def build_context(drawn_cards, spread, question=""):
    """Assemble knowledge context for the LLM."""
    combinations = load_combinations()
    reversed_methods = load_reversed_methods()
    guide = load_reading_guide()

    parts = []

    # 1. Card meanings
    parts.append("## 牌义参考")
    for i, card in enumerate(drawn_cards):
        pos_name = spread.get("positions", {}).get(str(i + 1), f"位置{i+1}")
        orientation = card["orientation"]
        meaning = card[orientation]
        orient_label = "正位" if orientation == "upright" else "逆位"
        parts.append(f"""
### {pos_name}: {card['name']} ({orient_label})
- 元素: {card.get('element', '无')}
- 大体意义: {meaning['general']}
- 关系意义: {meaning['relationship']}
- 关键词: {', '.join(meaning['keywords'])}
""")

    # 2. Combination rules
    card_names = [c["name"] for c in drawn_cards]
    matched_combos = check_combinations(card_names, combinations)
    if matched_combos:
        parts.append("## 命中的组合规则")
        for combo in matched_combos:
            parts.append(f"- {combo['rule']}: 命中牌 [{', '.join(combo['matched_cards'])}]")

    # 3. Reversed rules (if any reversed cards)
    reversed_cards = [c for c in drawn_cards if c["orientation"] == "reversed"]
    if reversed_cards:
        parts.append("## 逆位解读原则")
        principles = reversed_methods.get("seven_derivation_principles", {})
        for key, desc in principles.items():
            if key != "title":
                parts.append(f"- {desc}")
        specials = reversed_methods.get("special_findings", {})
        if specials:
            parts.append("### 特殊规则")
            for k, v in specials.items():
                parts.append(f"- {v}")

    return "\n".join(parts)
```

### 模块 C: Prompt 组装

功能: 将上下文、牌阵、用户问题组装成最终发给 LLM 的 prompt。

```python
SYSTEM_PROMPT = """你是一位温暖、有洞察力的塔罗分析师。

## 解读风格
- 用温暖自然的语言, 不要机械地复述牌义
- 结合牌面故事和位置含义做综合解读
- 先解读每张牌, 再做整体串联
- 最后给出具体、可操作的建议
- 如果有逆位牌, 不要简单说"不好", 用"需要注意"或"需要调整"的语气

## 解读结构
1. 【整体印象】用1-2句话概括牌面传递的核心信息
2. 【逐张解读】结合位置含义解读每张牌
3. 【牌面串联】把牌连成一个完整的故事
4. 【组合提示】如果命中组合规则, 特别说明
5. 【建议】给出2-3条具体建议
6. 【互动】问用户一个引导性问题, 促进对话

## 重要提醒
- 不要做出绝对化的预测 ("一定会"、"肯定不会")
- 强调塔罗是自我探索的工具, 不是命运判决
- 用"目前的能量显示"、"牌面暗示"等柔性表达
"""

def build_prompt(drawn_cards, spread, question="", topic="general"):
    """Build the final message list for the LLM."""

    # Card display
    card_lines = []
    for i, card in enumerate(drawn_cards):
        pos = spread.get("positions", {}).get(str(i + 1), f"位置{i+1}")
        orient = "正位" if card["orientation"] == "upright" else "逆位"
        card_lines.append(f"位置{i+1} ({pos}): {card['name']} [{orient}]")

    card_display = "\n".join(card_lines)

    # Topic hint
    topic_hint = ""
    if topic == "love":
        topic_hint = "\n用户关注的是感情问题, 请重点解读两性关系方面的意义。"
    elif topic == "career":
        topic_hint = "\n用户关注的是事业问题, 请重点解读事业和金钱方面的意义。"
    elif topic == "health":
        topic_hint = "\n用户关注的是健康问题, 请结合牌义给出健康方面的建议。"

    # Knowledge context
    context = build_context(drawn_cards, spread, question)

    user_message = f"""牌阵: {spread['name']} ({spread.get('use', '')})

用户问题: {question if question else '请做一次整体分析'}
{topic_hint}

抽到的牌:
{card_display}

---
以下是知识库中的参考资料, 请在解读时参考但不要直接复制:

{context}"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
```

### 模块 D: 主流程串联

```python
async def do_reading(spread_name="seven_card", question="", topic="general"):
    """Complete reading flow."""

    # 1. Load cards
    all_cards = load_all_cards()

    # 2. Load spread
    spread = load_spread(spread_name)
    if not spread:
        return f"未找到牌阵: {spread_name}"

    # 3. Draw cards
    n = spread["cards"]
    drawn = draw_cards(n, all_cards)

    # 4. Build prompt
    messages = build_prompt(drawn, spread, question, topic)

    # 5. Call LLM (choose one method below)

    # Method A: OpenAI-compatible API
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://your-api-endpoint/v1/chat/completions",
            headers={"Authorization": "Bearer YOUR_KEY"},
            json={
                "model": "gpt-4o",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 2000
            },
            timeout=60
        )
        result = resp.json()
        return result["choices"][0]["message"]["content"]

    # Method B: openai library
    # from openai import AsyncOpenAI
    # client = AsyncOpenAI(api_key="...", base_url="...")
    # resp = await client.chat.completions.create(
    #     model="gpt-4o", messages=messages, temperature=0.8
    # )
    # return resp.choices[0].message.content
```

---

## 5. API 接口设计 (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI Tarot API")

class ReadingRequest(BaseModel):
    spread: str = "seven_card"       # Spread name
    question: str = ""                # User question
    topic: str = "general"            # love/career/health/general

class ReadingResponse(BaseModel):
    cards: list[dict]                 # Drawn cards with orientation
    interpretation: str               # LLM generated reading
    spread_name: str                  # Spread used

@app.get("/api/spreads")
async def list_spreads():
    """Get all available spreads."""
    with open(KB_DIR / "spreads.json") as f:
        basic = json.load(f)
    with open(KB_DIR / "additional_spreads.json") as f:
        extra = json.load(f)
    result = {}
    for k, v in basic.items():
        result[k] = {"name": v["name"], "cards": v["cards"], "use": v.get("use", "")}
    for k, v in extra.get("spreads", {}).items():
        result[k] = {"name": v.get("name", k), "cards": v.get("cards", 0)}
    return result

@app.post("/api/reading", response_model=ReadingResponse)
async def create_reading(req: ReadingRequest):
    """Execute a reading."""
    all_cards = load_all_cards()
    spread = load_spread(req.spread)
    if not spread:
        return {"error": f"未找到牌阵: {req.spread}"}

    drawn = draw_cards(spread["cards"], all_cards)
    messages = build_prompt(drawn, spread, req.question, req.topic)

    interpretation = await call_llm(messages)

    return {
        "cards": [
            {"name": c["name"], "orientation": c["orientation"],
             "position": spread.get("positions", {}).get(str(i+1), "")}
            for i, c in enumerate(drawn)
        ],
        "interpretation": interpretation,
        "spread_name": spread["name"]
    }

@app.get("/api/cards")
async def list_cards():
    """Get all 78 cards."""
    all_cards = load_all_cards()
    return [
        {"name": name, "suit": card.get("suit", ""), "element": card.get("element", "")}
        for name, card in all_cards.items()
    ]
```

---

## 6. RAG 向量检索方案 (进阶, 可选)

如果想让解读更精准, 可以用向量检索替代全量注入。

```python
# pip install chromadb openai

import chromadb
from openai import OpenAI

client = chromadb.PersistentClient(path="./tarot_vectordb")
openai_client = OpenAI()

def embed(text):
    resp = openai_client.embeddings.create(
        model="text-embedding-3-small", input=text
    )
    return resp.data[0].embedding

def build_vectordb():
    """One-time vector DB construction."""
    collection = client.get_or_create_collection("tarot")

    all_cards = load_all_cards()
    for name, card in all_cards.items():
        for orient in ["upright", "reversed"]:
            meaning = card[orient]
            orient_label = "正位" if orient == "upright" else "逆位"
            text = f"{name} ({orient_label})\n"
            text += f"大体: {meaning['general']}\n"
            text += f"关系: {meaning['relationship']}\n"
            text += f"关键词: {', '.join(meaning['keywords'])}"

            doc_id = f"{name}_{orient}"
            collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[{
                    "card_name": name,
                    "orientation": orient,
                    "suit": card.get("suit", ""),
                    "type": "card_meaning"
                }],
                embeddings=[embed(text)]
            )

    # Combination rules
    combos = load_combinations()
    for key, combo in combos.items():
        text = f"组合规则: {combo['name']}\n涉及牌: {', '.join(combo['cards'])}"
        collection.add(
            ids=[f"combo_{key}"],
            documents=[text],
            metadatas=[{"type": "combination", "rule_name": combo["name"]}],
            embeddings=[embed(text)]
        )

def search_relevant(query, n_results=5):
    """Search for relevant knowledge snippets."""
    collection = client.get_collection("tarot")
    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=n_results
    )
    return results["documents"][0]
```

---

## 7. 可用牌阵清单

以下 key 可直接传给 `spread` 参数:

| key | 名称 | 牌数 | 用途 |
|-----|------|------|------|
| `single_card` | 单张牌 | 1 | 是/否问题, 快速洞察 |
| `seven_card` | 七张牌牌形 | 7 | 整体分析 (推荐默认) |
| `spiritual_direction` | 精神方向 | 5 | 理解精神方向 |
| `five_card_lesson` | 课题牌形 | 5 | 了解为何陷于窘境 |
| `statement` | 陈述性牌形 | 5 | 看控制了什么 |
| `four_aspects` | 四个面向 | 4 | 身体/感情/心智/精神 |
| `four_elements` | 四元素 | 4 | 能量受阻/流动分析 |
| `karma` | 因果循环 | 8 | 优缺点和精神平衡 |

---

## 8. 话题分类

`topic` 参数影响解读侧重点:

| topic | 含义 | 推荐牌阵 |
|-------|------|----------|
| `general` | 整体分析 | seven_card |
| `love` | 感情问题 | seven_card, four_aspects |
| `career` | 事业/金钱 | four_elements, five_card_lesson |
| `health` | 健康 | spiritual_direction |
| `spiritual` | 灵性成长 | karma, spiritual_direction |

---

## 9. 前端展示建议

抽牌结果可这样展示:

```
+-------------------------------------+
|         * 七张牌牌形 *              |
|                                     |
|  +------+  +------+  +------+      |
|  | 过去  |  | 现在  |  | 近期  |      |
|  | 权杖三 |  | 圣杯五 |  | 太阳  |      |
|  | [正位] |  | [逆位] |  | [正位] |      |
|  +------+  +------+  +------+      |
|                                     |
|         +------+                    |
|         | 答案  |                    |
|         | 命运之轮|                    |
|         | [正位] |                    |
|         +------+                    |
|                                     |
|  +------+  +------+  +------+      |
|  | 能量  |  | 希望恐惧| | 结果  |      |
|  | 宝剑八 |  | 女皇  |  | 星星  |      |
|  | [逆位] |  | [正位] |  | [正位] |      |
|  +------+  +------+  +------+      |
|                                     |
|  [解读内容...]                       |
+-------------------------------------+
```

---

## 10. 快速启动清单

- [ ] 读取全部 JSON 文件, 验证 `load_all_cards()` 返回 78 张牌
- [ ] 实现 `draw_cards()` 抽牌逻辑
- [ ] 实现 `build_context()` 知识检索
- [ ] 实现 `build_prompt()` Prompt 组装
- [ ] 对接 LLM API (OpenAI/国产/本地)
- [ ] 实现 API 接口 (可选 FastAPI)
- [ ] 前端页面 (可选)
- [ ] 牌面图片资源 (可选)

---

## 11. 关键注意事项

1. **温度参数**: 建议 0.7-0.9, 太低会死板, 太高会胡说
2. **max_tokens**: 建议 1500-2500, 解读太短没深度, 太长用户不看
3. **逆位处理**: 不要简单说"不好", 知识库里有7种逆位推衍原则
4. **组合规则**: 命中时要特别强调, 这是差异化竞争力
5. **随机性**: 同一问题多次抽牌结果不同, 要在UI上说明这是正常的
6. **免责声明**: 前端加上"塔罗是自我探索工具, 不是命运判决"

---

*文档版本: 2.0 | 基于 8 本塔罗书籍提取 | 78张牌 x 4维解读*
