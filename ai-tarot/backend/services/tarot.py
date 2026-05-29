"""
Tarot Engine - Core tarot reading logic.

Handles card loading, drawing, spread management, and full reading assembly.
Compatible with both INTEGRATION.md spreads format and backend/data format.
"""

import json
import random
from pathlib import Path
from typing import Any

_SERVICES_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SERVICES_DIR.parent / "data"
_ROOT_DIR = _SERVICES_DIR.parent.parent  # ai-tarot/


class TarotEngine:
    """Core tarot engine that manages cards, spreads, and readings."""

    def __init__(self) -> None:
        self._cards: list[dict[str, Any]] = []
        self._spreads: dict[str, dict[str, Any]] = {}

    def load_cards(self, path: str | Path | None = None) -> list[dict[str, Any]]:
        if path is None:
            path = _DATA_DIR / "cards.json"
        path = Path(path)
        with path.open("r", encoding="utf-8") as fh:
            self._cards = json.load(fh)
        return self._cards

    def load_spreads(self, path: str | Path | None = None) -> dict[str, dict[str, Any]]:
        if path is None:
            # Prefer root spreads.json (richer, from INTEGRATION.md)
            root_path = _ROOT_DIR / "spreads.json"
            path = root_path if root_path.exists() else _DATA_DIR / "spreads.json"
        path = Path(path)

        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)

        # Normalize: support both formats
        # Format A (backend/data): {"id", "name_cn", "name_en", "card_count", "positions": [{index, name, description}]}
        # Format B (root/INTEGRATION): {"name", "cards", "use", "positions": {"1": "pos_name", ...}}
        normalized = {}
        for key, spread in raw.items():
            if "card_count" in spread:
                # Format A - already normalized
                normalized[key] = spread
            else:
                # Format B - normalize
                card_count = spread.get("cards", 1)
                raw_positions = spread.get("positions", {})
                positions = []
                for i in range(1, card_count + 1):
                    pos_str = raw_positions.get(str(i), f"位置{i}")
                    positions.append({
                        "index": i - 1,
                        "name": pos_str,
                        "description": spread.get("use", ""),
                    })
                # Build position details from knowledge base
                pos_details = []
                for k, v in raw_positions.items():
                    if k not in ("center",):
                        pos_details.append({"pos": k, "meaning": v})
                    else:
                        pos_details.insert(0, {"pos": k, "meaning": v})

                normalized[key] = {
                    "id": key,
                    "name_cn": spread.get("name", key),
                    "name_en": key.replace("_", " ").title(),
                    "description": spread.get("use", ""),
                    "card_count": card_count,
                    "positions": positions,
                    "use": spread.get("use", ""),
                    "steps": spread.get("steps", []),
                    "tips": spread.get("tips", []),
                    "note": spread.get("note", ""),
                    "answer_logic": spread.get("answer_logic", ""),
                    "layout": spread.get("layout", ""),
                    "position_details": pos_details,
                }

        # Load special spreads from spread_details.json
        detail_path = _ROOT_DIR / "spread_details.json"
        if detail_path.exists():
            with detail_path.open("r", encoding="utf-8") as fh:
                detail_data = json.load(fh)
            for sp in detail_data.get("spreads", []):
                name = sp.get("name", "")
                if not name:
                    continue
                key = "special_" + name.replace("（", "").replace("）", "").replace("(", "").replace(")", "")
                card_count = sp.get("number_of_cards", sp.get("cards", 3))
                raw_positions = sp.get("positions", [])
                positions = []
                pos_details = []
                for pos in raw_positions:
                    idx = pos.get("position", 0) - 1
                    pos_name = pos.get("name", f"位置{pos.get('position', '?')}")
                    pos_meaning = pos.get("meaning", "")
                    positions.append({
                        "index": idx,
                        "name": pos_name,
                        "description": pos_meaning,
                    })
                    pos_details.append({"pos": str(pos.get("position", "?")), "meaning": pos_meaning})
                normalized[key] = {
                    "id": key,
                    "name_cn": name,
                    "name_en": key.replace("_", " ").title(),
                    "description": sp.get("purpose", ""),
                    "card_count": card_count,
                    "positions": positions,
                    "use": sp.get("purpose", ""),
                    "steps": [],
                    "tips": [],
                    "note": sp.get("mythological_background", ""),
                    "answer_logic": sp.get("interpretation_method", ""),
                    "layout": sp.get("layout_shape", ""),
                    "position_details": pos_details,
                }

        self._spreads = normalized
        return self._spreads

    def draw_cards(self, count: int, allow_reversed: bool = True) -> list[dict[str, Any]]:
        if not self._cards:
            raise RuntimeError("No cards loaded. Call load_cards() before drawing.")

        drawn: list[dict[str, Any]] = []
        available = list(self._cards)

        for idx in range(min(count, len(available))):
            card = random.choice(available)
            available.remove(card)
            card_copy = dict(card)
            if allow_reversed:
                card_copy["orientation"] = random.choice(["upright", "reversed"])
            else:
                card_copy["orientation"] = "upright"
            card_copy["drawn_id"] = idx + 1
            drawn.append(card_copy)

        return drawn

    def get_spread(self, name: str) -> dict[str, Any]:
        if not self._spreads:
            raise RuntimeError("No spreads loaded. Call load_spreads() before looking up a spread.")

        if name not in self._spreads:
            available = ", ".join(sorted(self._spreads.keys()))
            raise KeyError(f"Unknown spread '{name}'. Available spreads: {available}")

        return self._spreads[name]

    def do_reading(self, spread_name: str, allow_reversed: bool = True) -> dict[str, Any]:
        spread = self.get_spread(spread_name)
        cards = self.draw_cards(
            count=spread["card_count"],
            allow_reversed=allow_reversed,
        )

        positions = spread["positions"]

        reading_cards: list[dict[str, Any]] = []
        for card, pos_info in zip(cards, positions):
            reading_cards.append({
                **card,
                "position_name": pos_info["name"],
                "position_description": pos_info.get("description", ""),
                "position_index": pos_info["index"],
            })

        return {
            "spread": {
                "id": spread["id"],
                "name_cn": spread["name_cn"],
                "name_en": spread["name_en"],
                "description": spread.get("description", ""),
            },
            "cards": reading_cards,
        }
