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

        user_content = (
            f"## 我的问题\n{user_question}{topic_hint}\n\n"
            f"## 牌阵：{spread.get('name_cn', '')}\n"
            f"{spread.get('description', '')}\n\n"
            f"## 各牌位解读\n\n{cards_text}"
            f"{combo_context}"
            f"{reversed_context}"
            f"请综合所有牌面，给出完整的解读。"
            f"先用1-2句话概括整体印象，再逐一解读各牌位，串联牌面故事，"
            f"如果有组合规则命中请特别强调，最后给出2-3条具体建议和一个引导性问题。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return await self._chat(messages)
