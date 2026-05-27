# AI塔罗项目 — 知识库对接文档 v3.0

> 本文档供 AI Agent 直接执行，完成知识库与 LLM 的对接。
> 知识库路径：`~/.openclaw/workspace/ai-tarot/`
> 来源：8本塔罗书籍结构化提取 | 18个JSON文件 | 621KB

---

## 1. 文件清单

### 核心牌义（78张）
| 文件 | 内容 | 大小 |
|------|------|------|
| `wands.json` | 权杖14张（火元素） | 11KB |
| `cups.json` | 圣杯14张（水元素） | 12KB |
| `swords.json` | 宝剑14张（空气元素） | 11KB |
| `pentacles.json` | 五角星14张（土元素） | 11KB |
| `major_arcana.json` | 大阿尔克纳22张 | 17KB |

### 进阶知识（新增）
| 文件 | 内容 | 大小 |
|------|------|------|
| `cross_matrix.json` | 22×22大牌交叉解读矩阵（968条组合） | 430KB |
| `reversed_detail.json` | 22张大牌四层逆位分析（图示/负面/相反/经典） | 70KB |
| `waite_symbolism.json` | 牌重复出现规则+大牌深层符号象征 | 21KB |
| `celtic_pairs.json` | 凯尔特十字位置配对解读+关键词拓展词 | 5KB |
| `thoth_deck.json` | 克劳力托特牌系结构+解读框架 | 5KB |
| `spread_details.json` | 9种特殊牌阵详细摆法+传说背景 | 13KB |

### 参考框架
| 文件 | 内容 | 大小 |
|------|------|------|
| `spreads.json` | 8种基础牌阵 | 4KB |
| `additional_spreads.json` | 补充牌阵索引 | 2KB |
| `combinations.json` | 17组牌义组合规则 | 3KB |
| `reversed_methods.json` | 逆位解读方法论（6理论+7原则） | 3KB |
| `reading_frameworks.json` | 解读框架（三层模型+9维+心理学） | 5KB |
| `reading_guide.json` | 基础解牌指南（元素/星座/程序） | 3KB |
| `index.json` | 元数据索引 | 1KB |

---

## 2. 数据结构

### 2.1 单张牌结构（wands/cups/swords/pentacles/major_arcana）

```json
{
  "cards": {
    "ace": {
      "name": "权杖王牌",
      "number": 1,
      "upright": {
        "general": "大体意义",
        "relationship": "两性关系意义",
        "keywords": ["关键词1", "关键词2"]
      },
      "reversed": {
        "general": "倒立意义",
        "relationship": "倒立关系意义",
        "keywords": ["关键词1"]
      }
    }
  }
}
```

大阿尔卡纳 key 为字符串数字 "0"-"21"，另有 `english` 字段。

### 2.2 交叉解读矩阵（cross_matrix.json）⭐ 核心差异化

```json
{
  "matrix": {
    "0": {
      "1": {
        "upright": "愚人+魔术师正位解读",
        "reversed": "愚人+魔术师逆位解读",
        "advice": "告诫"
      },
      "2": { ... }
    }
  }
}
```

用法：当两张大阿尔卡纳同时出现时，查询 `matrix[cardA_id][cardB_id]` 获取组合解读。

### 2.3 四层逆位分析（reversed_detail.json）

```json
{
  "cards": {
    "0": {
      "name": "愚人",
      "upright_keywords": ["关键词"],
      "visual": "图示联想法分析",
      "negative": "负面意义法分析",
      "opposite": "相反意义法分析",
      "classical": "其他经典牌义"
    }
  }
}
```

### 2.4 牌重复规则（waite_symbolism.json）

```json
{
  "card_recurrence_rules": {
    "kings": {
      "4_kings": "四张国王牌含义",
      "3_kings": "三张国王牌含义",
      "2_kings": "两张国王牌含义"
    }
  },
  "major_arcana_symbolism": {
    "0": {
      "name": "愚人",
      "symbols": ["白玫瑰", "悬崖", "小狗", "行囊"],
      "deep_meaning": "深层象征解读"
    }
  }
}
```

### 2.5 凯尔特十字配对（celtic_pairs.json）

```json
{
  "position_pairings": {
    "1_2": { "positions": [1, 2], "meaning": "核心组含义" },
    "3_5": { "positions": [3, 5], "meaning": "意识组含义" }
  },
  "keywords_expansion_examples": {
    "圣杯七": { "keywords": ["充满期待"], "expansion": ["自我蒙蔽"] }
  }
}
```

### 2.6 牌阵详情（spread_details.json）

```json
{
  "spreads": {
    "海伦阵": {
      "cards": 3,
      "purpose": "爱情咨询",
      "layout": "纵向排列",
      "positions": { "1": "位置含义", "2": "...", "3": "..." },
      "background": "传说背景"
    }
  }
}
```

### 2.7 托特牌系（thoth_deck.json）

```json
{
  "deck_structure": {
    "suits": { "wands": "...", "swords": "...", "cups": "...", "disks": "..." },
    "court": { "knight": "...", "queen": "...", "prince": "...", "princess": "..." }
  }
}
```

注意：托特牌义因源PDF文本不完整，仅含牌系结构和解读框架，不含78张完整牌义。

---

## 3. 实现模块

### 模块 A：加载全部牌

```python
import json
from pathlib import Path

KB_DIR = Path("~/.openclaw/workspace/ai-tarot").expanduser()

def load_json(name):
    with open(KB_DIR / name) as f:
        return json.load(f)

def load_all_cards():
    """Load all 78 cards as flat dict {name: card_data}"""
    all_cards = {}
    for suit_file in ["wands", "cups", "swords", "pentacles"]:
        data = load_json(f"{suit_file}.json")
        for key, card in data["cards"].items():
            card["suit"] = data["suit"]
            card["element"] = data["element"]
            all_cards[card["name"]] = card
    data = load_json("major_arcana.json")
    for key, card in data["cards"].items():
        card["suit"] = "大阿尔克纳"
        card["element"] = None
        all_cards[card["name"]] = card
    return all_cards
```

### 模块 B：抽牌引擎

```python
import random

def draw_cards(n, all_cards):
    """Draw n unique cards with random orientation."""
    names = random.sample(list(all_cards.keys()), n)
    result = []
    for name in names:
        card = all_cards[name].copy()
        card["orientation"] = random.choice(["upright", "reversed"])
        result.append(card)
    return result
```

### 模块 C：知识检索（增强版）

```python
def build_context(drawn_cards, spread, question=""):
    """Build enhanced knowledge context for LLM."""
    parts = []

    # 1. Card meanings
    parts.append("## 牌义参考")
    for i, card in enumerate(drawn_cards):
        pos = spread.get("positions", {}).get(str(i+1), f"位置{i+1}")
        orient = card["orientation"]
        meaning = card[orient]
        orient_label = "正位" if orient == "upright" else "逆位"
        parts.append(f"### {pos}: {card['name']} ({orient_label})")
        parts.append(f"- 大体: {meaning['general']}")
        parts.append(f"- 关系: {meaning['relationship']}")
        parts.append(f"- 关键词: {', '.join(meaning['keywords'])}")

    # 2. Cross matrix (if 2+ Major Arcana)
    major_drawn = [c for c in drawn_cards if c.get("suit") == "大阿尔克纳"]
    if len(major_drawn) >= 2:
        matrix = load_json("cross_matrix.json")["matrix"]
        parts.append("## 大牌交叉解读")
        for i in range(len(major_drawn)):
            for j in range(i+1, len(major_drawn)):
                id_a = str(major_drawn[i].get("number", ""))
                id_b = str(major_drawn[j].get("number", ""))
                entry = matrix.get(id_a, {}).get(id_b, {})
                if entry:
                    parts.append(f"- {major_drawn[i]['name']}+{major_drawn[j]['name']}: {entry.get('upright', '')}")

    # 3. Reversed detail (for Major Arcana reversed)
    reversed_major = [c for c in major_drawn if c["orientation"] == "reversed"]
    if reversed_major:
        detail = load_json("reversed_detail.json")
        parts.append("## 逆位深度分析")
        for c in reversed_major:
            card_detail = detail.get("cards", {}).get(str(c["number"]), {})
            if card_detail:
                parts.append(f"### {c['name']}逆位")
                parts.append(f"- 图示联想: {card_detail.get('visual', '')}")
                parts.append(f"- 负面意义: {card_detail.get('negative', '')}")

    # 4. Combination rules
    combos = load_json("combinations.json")
    card_names = [c["name"] for c in drawn_cards]
    matched = []
    for key, combo in combos.items():
        if isinstance(combo, dict) and "cards" in combo:
            if set(combo["cards"]) & set(card_names):
                matched.append(combo["name"])
    if matched:
        parts.append("## 命中组合规则")
        for m in matched:
            parts.append(f"- {m}")

    # 5. Reversed principles
    reversed_cards = [c for c in drawn_cards if c["orientation"] == "reversed"]
    if reversed_cards:
        methods = load_json("reversed_methods.json")
        parts.append("## 逆位解读原则")
        for k, v in methods.get("seven_derivation_principles", {}).items():
            parts.append(f"- {v}")

    return "\n".join(parts)
```

### 模块 D：Prompt 组装

```python
SYSTEM_PROMPT = """你是一位温暖、有洞察力的塔罗分析师。

## 解读风格
- 用温暖自然的语言，不要机械地复述牌义
- 结合牌面故事和位置含义做综合解读
- 先解读每张牌，再做整体串联
- 最后给出具体、可操作的建议
- 如果有逆位牌，不要简单说"不好"，用"需要注意"或"需要调整"的语气

## 解读结构
1. 【整体印象】用1-2句话概括牌面传递的核心信息
2. 【逐张解读】结合位置含义解读每张牌
3. 【牌面串联】把牌连成一个完整的故事
4. 【组合提示】如果命中组合规则或大牌交叉矩阵，特别说明
5. 【建议】给出2-3条具体建议
6. 【互动】问用户一个引导性问题

## 重要提醒
- 不要做出绝对化的预测
- 强调塔罗是自我探索的工具，不是命运判决
- 用"目前的能量显示"、"牌面暗示"等柔性表达
"""

def build_prompt(drawn_cards, spread, question="", topic="general"):
    card_lines = []
    for i, card in enumerate(drawn_cards):
        pos = spread.get("positions", {}).get(str(i+1), f"位置{i+1}")
        orient = "正位" if card["orientation"] == "upright" else "逆位"
        card_lines.append(f"位置{i+1} ({pos}): {card['name']} [{orient}]")

    topic_hint = {"love": "感情问题", "career": "事业问题", "health": "健康问题"}.get(topic, "")
    if topic_hint:
        topic_hint = f"\n用户关注的是{topic_hint}，请重点解读相关方面的意义。"

    context = build_context(drawn_cards, spread, question)

    user_msg = f"""牌阵: {spread['name']}
用户问题: {question or '请做一次整体分析'}
{topic_hint}

抽到的牌:
{chr(10).join(card_lines)}

---
知识库参考资料:
{context}"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]
```

### 模块 E：主流程

```python
async def do_reading(spread_name="seven_card", question="", topic="general"):
    all_cards = load_all_cards()
    spread = load_json("spreads.json").get(spread_name)
    if not spread:
        extra = load_json("additional_spreads.json")
        spread = extra.get("spreads", {}).get(spread_name)
    if not spread:
        return {"error": f"未找到牌阵: {spread_name}"}

    drawn = draw_cards(spread["cards"], all_cards)
    messages = build_prompt(drawn, spread, question, topic)

    # Call your LLM here
    interpretation = await call_llm(messages)

    return {
        "cards": [{"name": c["name"], "orientation": c["orientation"],
                   "position": spread.get("positions", {}).get(str(i+1), "")}
                  for i, c in enumerate(drawn)],
        "interpretation": interpretation,
        "spread": spread["name"]
    }
```

---

## 4. API 接口（FastAPI）

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI Tarot API v3")

class ReadingRequest(BaseModel):
    spread: str = "seven_card"
    question: str = ""
    topic: str = "general"  # love/career/health/general

@app.get("/api/spreads")
async def list_spreads():
    basic = load_json("spreads.json")
    extra = load_json("additional_spreads.json")
    detail = load_json("spread_details.json")
    result = {}
    for k, v in basic.items():
        result[k] = {"name": v["name"], "cards": v["cards"], "use": v.get("use", "")}
    for k, v in extra.get("spreads", {}).items():
        result[k] = {"name": v.get("name", k), "cards": v.get("cards", 0)}
    for k, v in detail.get("spreads", {}).items():
        result[k] = {"name": k, "cards": v.get("cards", 0), "purpose": v.get("purpose", "")}
    return result

@app.get("/api/cards")
async def list_cards():
    return [{"name": n, "suit": c.get("suit",""), "element": c.get("element","")}
            for n, c in load_all_cards().items()]

@app.get("/api/cross/{card_a}/{card_b}")
async def get_cross_reading(card_a: str, card_b: str):
    """查询两张大牌的交叉解读"""
    matrix = load_json("cross_matrix.json")["matrix"]
    entry = matrix.get(card_a, {}).get(card_b, {})
    if not entry:
        entry = matrix.get(card_b, {}).get(card_a, {})
    return entry or {"error": "未找到交叉解读"}

@app.get("/api/reversed-detail/{card_id}")
async def get_reversed_detail(card_id: str):
    """查询大牌的四层逆位分析"""
    detail = load_json("reversed_detail.json")
    return detail.get("cards", {}).get(card_id, {"error": "未找到"})

@app.get("/api/symbolism/{card_id}")
async def get_symbolism(card_id: str):
    """查询大牌的深层符号象征"""
    sym = load_json("waite_symbolism.json")
    return sym.get("major_arcana_symbolism", {}).get(card_id, {"error": "未找到"})

@app.post("/api/reading")
async def create_reading(req: ReadingRequest):
    result = await do_reading(req.spread, req.question, req.topic)
    return result
```

---

## 5. 可用牌阵

### 基础牌阵（spreads.json）
| key | 名称 | 牌数 | 用途 |
|-----|------|------|------|
| `single_card` | 单张牌 | 1 | 是/否问题 |
| `seven_card` | 七张牌 | 7 | 整体分析（推荐默认） |
| `spiritual_direction` | 精神方向 | 5 | 理解精神方向 |
| `five_card_lesson` | 课题牌形 | 5 | 了解困境原因 |
| `statement` | 陈述性 | 5 | 看控制了什么 |
| `four_aspects` | 四个面向 | 4 | 身体/感情/心智/精神 |
| `four_elements` | 四元素 | 4 | 能量分析 |
| `karma` | 因果循环 | 8 | 优缺点分析 |

### 特殊牌阵（spread_details.json）
| 名称 | 牌数 | 用途 |
|------|------|------|
| 海伦阵 | 3 | 爱情咨询 |
| 圣三角阵 | 3 | 事业启示 |
| 凯特尔十字阵 | 5 | 财运 |
| 炼金术狮子牌阵 | 4 | 寻找财富 |
| 荷罗斯兄弟牌阵 | 3 | 职业困扰 |
| 图特摩斯牌阵 | 5 | 友谊与团队 |
| 沙卡乌牌阵 | 4 | 家族幸福 |
| 基沙金字塔牌阵 | 3 | 学习启示 |
| 维纳斯阵 | 4 | 爱情婚姻 |
| 凯尔特十字（韦特原版）| 10 | 全面深度分析 |

---

## 6. 快速启动清单

- [ ] `load_all_cards()` 验证返回78张牌
- [ ] `draw_cards()` 抽牌逻辑
- [ ] `build_context()` 知识检索（含交叉矩阵+逆位深度）
- [ ] `build_prompt()` Prompt组装
- [ ] 对接 LLM API
- [ ] 实现 API 接口
- [ ] 前端页面
- [ ] 牌面图片资源

---

## 7. 关键提示

1. **交叉矩阵是最强差异化** — 两张大牌同时出现时一定要查 cross_matrix.json
2. **逆位不要说"不好"** — 用 reversed_detail.json 的四层分析，给出建设性解读
3. **牌重复规则** — 同数字/同花色出现2/3/4张时查 waite_symbolism.json
4. **凯尔特十字配对** — 使用最广泛的牌阵，查 celtic_pairs.json 的位置配对
5. **温度0.7-0.9** — 太低死板太高胡说
6. **免责声明** — 前端加上"塔罗是自我探索工具"

---

*文档版本: 3.0 | 8本书 | 18个JSON | 621KB | 78牌 × 4维 + 968条交叉解读*
