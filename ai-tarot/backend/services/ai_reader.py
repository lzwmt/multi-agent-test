"""
AI Reader - Generates tarot card interpretations via an OpenAI-compatible API.

Integrates rich knowledge base: 4-dimensional card meanings, combination rules,
reversed interpretation methods, topic classification, and reading frameworks.
"""

import json
import os
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # ai-tarot/
_KB_DIR = _ROOT_DIR  # knowledge base at project root
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
_DEFAULT_BASE_URL = "https://api-xai.ainaibahub.com/v1"
_DEFAULT_MODEL = "gpt-4.1-mini"
_TEMPERATURE = 0.8
_MAX_TOKENS = 2000


class AIReader:
    """Reads tarot cards and full spreads using an LLM, enriched with knowledge base."""

    def __init__(self) -> None:
        self._base_url: str = os.getenv(
            "TAROT_AI_BASE_URL",
            os.getenv("OPENAI_BASE_URL", _DEFAULT_BASE_URL),
        )
        self._api_key: str = os.getenv(
            "TAROT_AI_API_KEY",
            os.getenv("OPENAI_API_KEY", ""),
        )
        self._model: str = os.getenv("TAROT_AI_MODEL", _DEFAULT_MODEL)

        self._system_template: str = self._load_file(_PROMPTS_DIR / "system.md")
        raw_personas = self._load_json(_PROMPTS_DIR / "personas.json")
        self._personas: dict[str, dict[str, Any]] = {}
        for p in raw_personas.get("personas", []):
            self._personas[p["id"]] = p
            self._personas[p["name"]] = p

        # Load knowledge base
        self._kb_cards: dict[str, Any] = {}
        self._kb_combinations: dict[str, Any] = {}
        self._kb_reversed_methods: dict[str, Any] = {}
        self._kb_frameworks: dict[str, Any] = {}
        # v3.0 new knowledge base
        self._kb_cross_matrix: dict[str, Any] = {}
        self._kb_reversed_detail: dict[str, Any] = {}
        self._kb_symbolism: dict[str, Any] = {}
        self._kb_celtic_pairs: dict[str, Any] = {}
        self._kb_reversed_minor: dict[str, Any] = {}  # v3.2: 56小牌逆位
        self._kb_enhanced: dict[str, Any] = {}  # v3.2: 78张牌扩展牌义
        self._load_knowledge_base()

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_file(path: Path) -> str:
        with path.open("r", encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    def _load_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _load_knowledge_base(self) -> None:
        """Load all knowledge base files for enriched readings."""
        # Load all 78 cards into a flat dict keyed by Chinese name
        for suit_file in ["wands", "cups", "swords", "pentacles"]:
            path = _KB_DIR / f"{suit_file}.json"
            if path.exists():
                data = self._load_json(path)
                suit_name = data.get("suit", "")
                element = data.get("element", "")
                for key, card in data.get("cards", {}).items():
                    card["suit"] = suit_name
                    card["element"] = element
                    self._kb_cards[card["name"]] = card

        # Major Arcana
        path = _KB_DIR / "major_arcana.json"
        if path.exists():
            data = self._load_json(path)
            for key, card in data.get("cards", {}).items():
                card["suit"] = "大阿尔卡纳"
                self._kb_cards[card["name"]] = card

        # Combinations
        path = _KB_DIR / "combinations.json"
        if path.exists():
            self._kb_combinations = self._load_json(path)

        # Reversed methods
        path = _KB_DIR / "reversed_methods.json"
        if path.exists():
            self._kb_reversed_methods = self._load_json(path)

        # Reading frameworks
        path = _KB_DIR / "reading_frameworks.json"
        if path.exists():
            self._kb_frameworks = self._load_json(path)

        # v3.0: Cross matrix (22x22 Major Arcana combinations)
        path = _KB_DIR / "cross_matrix.json"
        if path.exists():
            self._kb_cross_matrix = self._load_json(path).get("matrix", {})

        # v3.0: Reversed detail (4-layer reverse analysis) - index by name
        path = _KB_DIR / "reversed_detail.json"
        if path.exists():
            raw_detail = self._load_json(path).get("cards", {})
            # Keys are "0_愚者", "I_魔术师" etc. Index by card name.
            self._kb_reversed_detail = {}
            for k, v in raw_detail.items():
                name = k.split("_", 1)[1] if "_" in k else k
                self._kb_reversed_detail[name] = v
                # Also index by number for API endpoint
                num = k.split("_")[0] if "_" in k else k
                self._kb_reversed_detail[num] = v

        # v3.2: Reversed minor arcana (56 cards 4-layer reverse analysis)
        # Index by Chinese card name for fast lookup
        path = _KB_DIR / "reversed_minor.json"
        if path.exists():
            raw_minor = self._load_json(path).get("cards", {})
            # Name normalization: book uses 钱币/A/侍者, KB uses 五角星/王牌/侍卫
            _suit_map = {"钱币": "五角星"}
            _rank_map = {" A": "王牌", "侍者": "侍卫"}
            self._kb_reversed_minor = {}
            for key, data in raw_minor.items():
                # Direct key storage for API endpoint
                self._kb_reversed_minor[key] = data
                # Build KB-compatible Chinese name
                book_name = data.get("name", "")
                kb_name = book_name
                for old, new in _suit_map.items():
                    kb_name = kb_name.replace(old, new)
                for old, new in _rank_map.items():
                    kb_name = kb_name.replace(old, new)
                if kb_name:
                    self._kb_reversed_minor[kb_name] = data

        # v3.2: Enhanced meanings (78 cards detailed interpretations)
        path = _KB_DIR / "enhanced_meanings.json"
        if path.exists():
            raw_enhanced = self._load_json(path).get("cards", {})
            self._kb_enhanced = raw_enhanced

        # v3.0: Waite symbolism (recurrence rules + deep symbols) - index by name
        path = _KB_DIR / "waite_symbolism.json"
        if path.exists():
            raw_sym = self._load_json(path)
            sym_data = raw_sym.get("major_arcana_symbolism", {})
            # Build name-indexed version
            self._kb_symbolism = dict(raw_sym)
            self._kb_symbolism["_by_name"] = {}
            for k, v in sym_data.items():
                name = k.split("_", 1)[1] if "_" in k else k
                self._kb_symbolism["_by_name"][name] = v
                num = k.split("_")[0] if "_" in k else k
                self._kb_symbolism["_by_name"][num] = v

        # v3.0: Celtic pairs (position pairings)
        path = _KB_DIR / "celtic_pairs.json"
        if path.exists():
            self._kb_celtic_pairs = self._load_json(path)

        # v3.1: Topic scenarios (78 cards × 4 topics)
        path = _KB_DIR / "topic_scenarios.json"
        if path.exists():
            self._kb_topic_scenarios = self._load_json(path).get("scenarios", {})
        else:
            self._kb_topic_scenarios = {}

    # ------------------------------------------------------------------
    # Persona
    # ------------------------------------------------------------------

    def get_persona(self, name: str) -> dict[str, Any]:
        if name in self._personas:
            return self._personas[name]
        return self._personas.get("gentle_sister", {
            "id": "gentle_sister", "name": "温柔姐姐", "description": "温暖治愈的解牌师。",
        })

    def list_personas(self) -> list[dict[str, Any]]:
        seen = set()
        result = []
        for p in self._personas.values():
            if p["id"] not in seen:
                seen.add(p["id"])
                result.append({
                    "id": p["id"], "name": p["name"],
                    "description": p.get("description", ""),
                    "style_keywords": p.get("style_keywords", []),
                })
        return result

    def _build_system_prompt(self, persona: dict[str, Any]) -> str:
        return self._system_template.format(
            persona_name=persona["name"],
            persona_description=persona.get("description", ""),
        )

    # ------------------------------------------------------------------
    # Knowledge enrichment
    # ------------------------------------------------------------------

    def _enrich_card_context(self, card: dict[str, Any]) -> str:
        """Build rich context for a single card from knowledge base."""
        card_name = card.get("name_cn", card.get("name", ""))
        orientation = card.get("orientation", "upright")
        orient_label = "正位" if orientation == "upright" else "逆位"

        parts = []

        # Try to find in knowledge base for richer meanings
        kb_card = self._kb_cards.get(card_name)
        if kb_card and orientation in kb_card:
            kb_meaning = kb_card[orientation]
            parts.append(f"- 大体意义: {kb_meaning.get('general', '')}")
            parts.append(f"- 关系意义: {kb_meaning.get('relationship', '')}")
            kw = kb_meaning.get("keywords", [])
            if kw:
                parts.append(f"- 关键词: {'、'.join(kw)}")
        else:
            # Fallback to cards.json data
            if orientation == "upright":
                meaning = card.get("upright_meaning", "")
                keywords = card.get("upright_keywords", [])
            else:
                meaning = card.get("reversed_meaning", "")
                keywords = card.get("reversed_keywords", [])
            if meaning:
                parts.append(f"- 牌义参考: {meaning}")
            if keywords:
                parts.append(f"- 关键词: {'、'.join(keywords)}")

        # Element info
        element = card.get("element") or (kb_card.get("element") if kb_card else "")
        if element:
            parts.append(f"- 元素: {element}")

        # v3.2: Enhanced meanings from 《塔罗全书》
        enhanced = self._kb_enhanced.get(card_name, {})
        if enhanced:
            if orientation == "upright":
                if enhanced.get("general"):
                    parts.append(f"- 详细解读: {enhanced['general'][:200]}")
            else:
                if enhanced.get("reversed"):
                    parts.append(f"- 逆位详解: {enhanced['reversed'][:200]}")

        return "\n".join(parts)

    def _check_combinations(self, card_names: list[str]) -> list[str]:
        """Check if drawn cards match any combination rules."""
        matched = []
        drawn_set = set(card_names)
        for key, combo in self._kb_combinations.items():
            combo_cards = set(combo.get("cards", []))
            if combo_cards & drawn_set:
                matched.append(f"- {combo['name']}: 命中牌 [{', '.join(combo_cards & drawn_set)}]")
        return matched

    def _get_reversed_context(self, has_reversed: bool) -> str:
        """Get reversed interpretation principles if any card is reversed."""
        if not has_reversed or not self._kb_reversed_methods:
            return ""
        parts = ["## 逆位解读原则"]
        principles = self._kb_reversed_methods.get("seven_derivation_principles", {})
        for key, desc in principles.items():
            if key != "title" and isinstance(desc, str):
                parts.append(f"- {desc}")
        specials = self._kb_reversed_methods.get("special_findings", {})
        if specials:
            parts.append("### 特殊规则")
            for k, v in specials.items():
                if isinstance(v, str):
                    parts.append(f"- {v}")
        return "\n".join(parts)

    def _get_cross_matrix_context(self, cards: list[dict[str, Any]]) -> str:
        """Query cross matrix when 2+ Major Arcana appear together."""
        if not self._kb_cross_matrix:
            return ""
        major_cards = []
        for c in cards:
            name = c.get("name_cn", c.get("name", ""))
            kb = self._kb_cards.get(name)
            if kb and kb.get("suit") == "大阿尔卡纳":
                major_cards.append({"name": name, "number": kb.get("number", c.get("id", "")), "card": c})
        if len(major_cards) < 2:
            return ""
        parts = ["## 大牌交叉解读矩阵"]
        for i in range(len(major_cards)):
            for j in range(i + 1, len(major_cards)):
                id_a = str(major_cards[i]["number"])
                id_b = str(major_cards[j]["number"])
                entry = self._kb_cross_matrix.get(id_a, {}).get(id_b, {})
                if not entry:
                    entry = self._kb_cross_matrix.get(id_b, {}).get(id_a, {})
                if entry:
                    orient_a = "正位" if major_cards[i]["card"].get("orientation") == "upright" else "逆位"
                    orient_b = "正位" if major_cards[j]["card"].get("orientation") == "upright" else "逆位"
                    key = "upright" if orient_a == "正位" and orient_b == "正位" else "reversed"
                    reading = entry.get(key, entry.get("upright", ""))
                    advice = entry.get("advice", "")
                    parts.append(f"- {major_cards[i]['name']}({orient_a}) + {major_cards[j]['name']}({orient_b}): {reading}")
                    if advice:
                        parts.append(f"  告诫: {advice}")
        return "\n".join(parts) if len(parts) > 1 else ""

    def _get_reversed_detail_context(self, cards: list[dict[str, Any]]) -> str:
        """Get 4-layer reverse analysis for reversed Major Arcana."""
        if not self._kb_reversed_detail:
            return ""
        parts = []
        for c in cards:
            if c.get("orientation") != "reversed":
                continue
            name = c.get("name_cn", c.get("name", ""))
            kb = self._kb_cards.get(name)
            if not kb or kb.get("suit") != "大阿尔卡纳":
                continue
            detail = self._kb_reversed_detail.get(name)
            if not detail:
                detail = self._kb_reversed_detail.get(str(kb.get("number", "")))
            if detail:
                parts.append(f"### {name}逆位深度分析")
                if detail.get("visual"):
                    parts.append(f"- 图示联想法: {detail['visual']}")
                if detail.get("negative"):
                    parts.append(f"- 负面意义法: {detail['negative']}")
                if detail.get("opposite"):
                    parts.append(f"- 相反意义法: {detail['opposite']}")
                if detail.get("classical"):
                    parts.append(f"- 经典牌义: {detail['classical']}")
        if parts:
            parts.insert(0, "## 逆位深度分析（四层）")
            return "\n".join(parts)
        return ""

    def _get_reversed_minor_context(self, cards: list[dict[str, Any]]) -> str:
        """Get 4-layer reverse analysis for reversed Minor Arcana (56 cards)."""
        if not self._kb_reversed_minor:
            return ""
        parts = []
        for c in cards:
            if c.get("orientation") != "reversed":
                continue
            name = c.get("name_cn", c.get("name", ""))
            kb = self._kb_cards.get(name)
            # Skip Major Arcana (handled by _get_reversed_detail_context)
            if not kb or kb.get("suit") == "大阿尔卡纳":
                continue
            detail = self._kb_reversed_minor.get(name)
            if detail:
                parts.append(f"### {name}逆位深度分析")
                if detail.get("keywords"):
                    parts.append(f"- 正位关键词: {detail['keywords']}")
                if detail.get("visual_association"):
                    parts.append(f"- 图示联想法: {detail['visual_association'][:200]}")
                if detail.get("negative_meaning"):
                    parts.append(f"- 负面意义法: {detail['negative_meaning'][:200]}")
                if detail.get("opposite_meaning"):
                    parts.append(f"- 相反意义法: {detail['opposite_meaning'][:200]}")
                if detail.get("classic_meanings"):
                    parts.append(f"- 经典牌义: {detail['classic_meanings'][:200]}")
                if detail.get("character_traits"):
                    parts.append(f"- 人物特质: {detail['character_traits'][:200]}")
        if parts:
            parts.insert(0, "## 小牌逆位深度分析")
            return "\n".join(parts)
        return ""

    def _get_symbolism_context(self, cards: list[dict[str, Any]]) -> str:
        """Get deep symbol meanings for Major Arcana + check recurrence rules."""
        if not self._kb_symbolism:
            return ""
        parts = []
        # Check card recurrence rules (same number/suit)
        recurrence = self._kb_symbolism.get("card_recurrence_rules", {})
        all_names = [c.get("name_cn", c.get("name", "")) for c in cards]
        # Count suits and numbers
        suit_counts: dict[str, int] = {}
        number_counts: dict[str, list[str]] = {}
        for c in cards:
            name = c.get("name_cn", c.get("name", ""))
            kb = self._kb_cards.get(name)
            if kb:
                suit = kb.get("suit", "")
                suit_counts[suit] = suit_counts.get(suit, 0) + 1
                num = str(kb.get("number", ""))
                if num:
                    number_counts.setdefault(num, []).append(name)
        # Check kings recurrence
        king_names = [n for n in all_names if "国王" in n or "King" in n]
        if len(king_names) >= 2:
            rule_key = f"{len(king_names)}_kings"
            kings_rules = recurrence.get("kings", {})
            if rule_key in kings_rules:
                parts.append(f"- {len(king_names)}张国王牌: {kings_rules[rule_key]}")
        # Check queens recurrence
        queen_names = [n for n in all_names if "王后" in n or "Queen" in n]
        if len(queen_names) >= 2:
            rule_key = f"{len(queen_names)}_queens"
            queens_rules = recurrence.get("queens", {})
            if rule_key in queens_rules:
                parts.append(f"- {len(queen_names)}张王后牌: {queens_rules[rule_key]}")
        # Deep symbolism for Major Arcana
        sym_by_name = self._kb_symbolism.get("_by_name", {})
        for c in cards:
            name = c.get("name_cn", c.get("name", ""))
            kb = self._kb_cards.get(name)
            if kb and kb.get("suit") == "大阿尔卡纳":
                sym = sym_by_name.get(name)
                if not sym:
                    sym = sym_by_name.get(str(kb.get("number", "")))
                if sym and sym.get("deep_meaning"):
                    parts.append(f"- {name}深层象征: {sym['deep_meaning']}")
        if parts:
            parts.insert(0, "## 符号象征与牌重复规则")
            return "\n".join(parts)
        return ""

    def _get_celtic_pairs_context(self, cards: list[dict[str, Any]], spread_name: str) -> str:
        """Get Celtic Cross position pairings if applicable."""
        if not self._kb_celtic_pairs or "凯尔特" not in spread_name:
            return ""
        pairings = self._kb_celtic_pairs.get("position_pairings", {})
        if not pairings:
            return ""
        parts = ["## 凯尔特十字位置配对"]
        for key, pairing in pairings.items():
            positions = pairing.get("positions", [])
            meaning = pairing.get("meaning", "")
            if positions and meaning:
                parts.append(f"- 位置{positions[0]}+{positions[1]}: {meaning}")
        return "\n".join(parts) if len(parts) > 1 else ""

    def _get_topic_scenario_context(self, cards: list[dict[str, Any]], topic: str) -> str:
        """Get topic-specific scenario interpretations for each card."""
        if not self._kb_topic_scenarios or topic not in ("love", "career", "wealth", "health"):
            return ""
        topic_data = self._kb_topic_scenarios.get(topic, {})
        if not topic_data:
            return ""
        topic_labels = {"love": "感情", "career": "事业", "wealth": "财运", "health": "健康"}
        parts = [f"## {topic_labels.get(topic, topic)}话题场景解读"]
        for c in cards:
            name = c.get("name_cn", c.get("name", ""))
            orientation = c.get("orientation", "upright")
            orient_label = "正位" if orientation == "upright" else "逆位"
            # Build key: major_0, wands_ace, cups_two, etc.
            kb = self._kb_cards.get(name)
            card_key = ""
            if kb:
                suit = kb.get("suit", "")
                num = kb.get("number")
                if suit == "大阿尔卡纳" and num is not None:
                    card_key = f"major_{num}"
                elif suit == "权杖":
                    card_key = f"wands_{self._num_to_word(num)}"
                elif suit == "圣杯":
                    card_key = f"cups_{self._num_to_word(num)}"
                elif suit == "宝剑":
                    card_key = f"swords_{self._num_to_word(num)}"
                elif suit == "五角星":
                    card_key = f"pentacles_{self._num_to_word(num)}"
            entry = topic_data.get(card_key, {})
            if entry:
                parts.append(f"- {name}({orient_label}): {entry.get(orientation, '')}")
        return "\n".join(parts) if len(parts) > 1 else ""

    @staticmethod
    def _num_to_word(num: int) -> str:
        """Convert card number to word for key lookup."""
        words = {1: "ace", 2: "two", 3: "three", 4: "four", 5: "five",
                 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
                 11: "page", 12: "knight", 13: "queen", 14: "king"}
        return words.get(num, str(num))

    def _detect_topic(self, question: str) -> str:
        """Detect the topic category from user's question."""
        if not question:
            return "general"
        topic_focus = self._kb_frameworks.get("topic_focus", {})
        for topic_key, topic_data in topic_focus.items():
            keywords = topic_data.get("keywords", [])
            for kw in keywords:
                if kw in question:
                    return topic_key
        return "general"

    def _get_topic_hint(self, topic: str) -> str:
        """Get topic-specific reading hint."""
        topic_focus = self._kb_frameworks.get("topic_focus", {})
        if topic in topic_focus:
            t = topic_focus[topic]
            return f"\n用户关注的是{t['name']}问题，{t.get('focus', '')}。{t.get('advice_style', '')}"
        return ""

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    async def _chat(self, messages: list[dict[str, str]]) -> str:
        url = f"{self._base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": _TEMPERATURE,
            "max_tokens": _MAX_TOKENS,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()

        data = resp.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        if not content and msg.get("reasoning_content"):
            content = msg["reasoning_content"]
        return content or "（解牌师正在思考中，请稍后再试）"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def read_card(
        self,
        persona_name: str,
        card: dict[str, Any],
        position: str,
        user_question: str,
    ) -> str:
        """Interpret a single drawn card with full knowledge base enrichment."""
        persona = self.get_persona(persona_name)
        system_prompt = self._build_system_prompt(persona)

        card_name = card.get("name_cn", card.get("name", "未知牌"))
        card_name_en = card.get("name_en", "")
        orientation = card.get("orientation", "upright")
        orient_label = "正位" if orientation == "upright" else "逆位"

        # Enriched context from knowledge base
        card_context = self._enrich_card_context(card)

        # Topic detection
        topic = self._detect_topic(user_question)
        topic_hint = self._get_topic_hint(topic)

        # Combination check
        combo_context = ""
        combos = self._check_combinations([card_name])
        if combos:
            combo_context = "\n## 命中的组合规则\n" + "\n".join(combos)

        # Reversed methods
        reversed_context = self._get_reversed_context(orientation == "reversed")

        user_content = (
            f"## 我的问题\n{user_question}\n{topic_hint}\n\n"
            f"## 抽到的牌\n"
            f"- 牌名：{card_name}（{card_name_en}）\n"
            f"- 正逆位：{orient_label}\n"
            f"- 牌位：{position}\n"
            f"{card_context}\n"
            f"{combo_context}\n"
            f"{reversed_context}\n\n"
            f"请结合我的问题和这张牌的含义，给出你的解读。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return await self._chat(messages)

    async def full_reading(
        self,
        persona_name: str,
        spread_result: dict[str, Any],
        user_question: str,
    ) -> str:
        """Generate a comprehensive reading enriched with full knowledge base."""
        persona = self.get_persona(persona_name)
        system_prompt = self._build_system_prompt(persona)

        spread = spread_result.get("spread", {})
        cards = spread_result.get("cards", [])

        # Topic detection
        topic = self._detect_topic(user_question)
        topic_hint = self._get_topic_hint(topic)

        # Build enriched card context
        cards_text = ""
        all_card_names = []
        has_reversed = False

        for c in cards:
            orientation = c.get("orientation", "upright")
            orient_label = "正位" if orientation == "upright" else "逆位"
            if orientation == "reversed":
                has_reversed = True

            card_name = c.get("name_cn", c.get("name", "?"))
            all_card_names.append(card_name)

            card_context = self._enrich_card_context(c)

            cards_text += (
                f"### 第{c.get('drawn_id', '?')}张：{c.get('position_name', '?')}\n"
                f"- 牌名：{card_name}（{c.get('name_en', '')}）\n"
                f"- 正逆位：{orient_label}\n"
                f"{card_context}\n\n"
            )

        # Combination rules
        combo_lines = self._check_combinations(all_card_names)
        combo_context = ""
        if combo_lines:
            combo_context = "## 命中的组合规则\n" + "\n".join(combo_lines) + "\n\n"

        # Reversed methods
        reversed_context = self._get_reversed_context(has_reversed)
        if reversed_context:
            reversed_context += "\n\n"

        # v3.0: Cross matrix (2+ Major Arcana)
        cross_context = self._get_cross_matrix_context(cards)
        if cross_context:
            cross_context += "\n\n"

        # v3.0: Reversed detail (4-layer for reversed Major Arcana)
        reversed_detail_context = self._get_reversed_detail_context(cards)
        if reversed_detail_context:
            reversed_detail_context += "\n\n"

        # v3.2: Reversed minor arcana (4-layer for reversed Minor Arcana)
        reversed_minor_context = self._get_reversed_minor_context(cards)
        if reversed_minor_context:
            reversed_minor_context += "\n\n"

        # v3.0: Symbolism + recurrence rules
        symbolism_context = self._get_symbolism_context(cards)
        if symbolism_context:
            symbolism_context += "\n\n"

        # v3.0: Celtic pairs (if applicable)
        spread_name = spread.get("name_cn", "")
        celtic_context = self._get_celtic_pairs_context(cards, spread_name)
        if celtic_context:
            celtic_context += "\n\n"

        # v3.1: Topic scenarios (love/career/wealth/health)
        topic_scenario_context = self._get_topic_scenario_context(cards, topic)
        if topic_scenario_context:
            topic_scenario_context += "\n\n"

        user_content = (
            f"## 我的问题\n{user_question}{topic_hint}\n\n"
            f"## 牌阵：{spread_name}\n"
            f"{spread.get('description', '')}\n\n"
            f"## 各牌位解读\n\n{cards_text}"
            f"{combo_context}"
            f"{reversed_context}"
            f"{cross_context}"
            f"{reversed_detail_context}"
            f"{reversed_minor_context}"
            f"{symbolism_context}"
            f"{celtic_context}"
            f"{topic_scenario_context}"
            f"请综合所有牌面，给出完整的解读。"
            f"先用1-2句话概括整体印象，再逐一解读各牌位，串联牌面故事，"
            f"如果有组合规则或大牌交叉矩阵命中请特别强调，"
            f"如果有逆位深度分析请综合四层解读，"
            f"最后给出2-3条具体建议和一个引导性问题。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return await self._chat(messages)
