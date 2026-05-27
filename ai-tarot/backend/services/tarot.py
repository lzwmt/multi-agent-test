"""
Tarot Engine - Core tarot reading logic.

Handles card loading, drawing, spread management, and full reading assembly.
"""

import json
import random
from pathlib import Path
from typing import Any

# Resolve paths relative to this file's parent (services/)
_SERVICES_DIR = Path(__file__).resolve().parent
_DATA_DIR = _SERVICES_DIR.parent / "data"


class TarotEngine:
    """Core tarot engine that manages cards, spreads, and readings."""

    def __init__(self) -> None:
        self._cards: list[dict[str, Any]] = []
        self._spreads: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_cards(self, path: str | Path | None = None) -> list[dict[str, Any]]:
        """Load card definitions from a JSON file.

        Args:
            path: Optional path to cards.json.  Defaults to ``data/cards.json``.

        Returns:
            The list of card dictionaries.
        """
        if path is None:
            path = _DATA_DIR / "cards.json"
        path = Path(path)

        with path.open("r", encoding="utf-8") as fh:
            self._cards = json.load(fh)

        return self._cards

    def load_spreads(self, path: str | Path | None = None) -> dict[str, dict[str, Any]]:
        """Load spread definitions from a JSON file.

        Args:
            path: Optional path to spreads.json.  Defaults to ``data/spreads.json``.

        Returns:
            The dictionary of spread definitions keyed by spread id.
        """
        if path is None:
            path = _DATA_DIR / "spreads.json"
        path = Path(path)

        with path.open("r", encoding="utf-8") as fh:
            self._spreads = json.load(fh)

        return self._spreads

    # ------------------------------------------------------------------
    # Card operations
    # ------------------------------------------------------------------

    def draw_cards(
        self,
        count: int,
        allow_reversed: bool = True,
    ) -> list[dict[str, Any]]:
        """Draw *count* random cards from the loaded deck.

        Each drawn card gets an ``orientation`` field that is either
        ``"upright"`` or ``"reversed"`` (if *allow_reversed* is True).

        Args:
            count:            Number of cards to draw.
            allow_reversed:   Whether reversed orientations are allowed.

        Returns:
            A list of card dictionaries enriched with ``orientation`` and
            ``drawn_id`` (1-based draw order).
        """
        if not self._cards:
            raise RuntimeError(
                "No cards loaded. Call load_cards() before drawing."
            )

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

    # ------------------------------------------------------------------
    # Spread operations
    # ------------------------------------------------------------------

    def get_spread(self, name: str) -> dict[str, Any]:
        """Return the spread configuration for *name*.

        Args:
            name: The spread id (e.g. ``"three_card"``).

        Returns:
            The spread dictionary including its ``positions`` array.

        Raises:
            KeyError: If the spread name is not found.
        """
        if not self._spreads:
            raise RuntimeError(
                "No spreads loaded. Call load_spreads() before looking up a spread."
            )

        if name not in self._spreads:
            available = ", ".join(sorted(self._spreads.keys()))
            raise KeyError(
                f"Unknown spread '{name}'. Available spreads: {available}"
            )

        return self._spreads[name]

    # ------------------------------------------------------------------
    # Full reading
    # ------------------------------------------------------------------

    def do_reading(
        self,
        spread_name: str,
        allow_reversed: bool = True,
    ) -> dict[str, Any]:
        """Perform a full tarot reading: combine a spread with drawn cards.

        Args:
            spread_name:     The spread id to use (e.g. ``"celtic_cross"``).
            allow_reversed:  Whether reversed orientations are allowed.

        Returns:
            A dictionary with the spread info and a ``cards`` list where each
            entry contains the card data, its ``position`` (from the spread),
            and its ``orientation``.
        """
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
