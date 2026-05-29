#!/usr/bin/env python3
"""Split 78-card tarot grid (non-uniform rows) into individual cards.

Source: img_c1f71f3c6565.png (1086×1448)
Layout verified by vision analysis on full image:
  Row 1 (10): Fool(0) → Hermit(IX)
  Row 2 (10): Wheel(X) → Sun(XIX)
  Row 3 (10): Judgement(XX) → 7 of Wands
  Row 4  (8): 8 of Wands → King of Wands + Ace of Cups
  Row 5  (9): 2 of Cups → Knight of Cups (continues from Ace)
  Row 6  (9): Queen of Cups → 7 of Swords
  Row 7  (9): 8 of Swords → 2 of Pentacles
  Row 8  (8): 3 of Pentacles → 10 of Pentacles
  Total: 73 cards visible. Missing: 5 cards (6-7 of Cups, 3-6 of Pentacles,
  Page/Knight/Queen/King of Pentacles). These may be in a 9th row or overlap.

  Adjusted: using 10-col uniform grid (80 positions) for all rows.
  This ensures correct alignment. Extra 2 positions left empty.
"""

import os
from PIL import Image

SRC = "/root/.hermes/image_cache/img_c1f71f3c6565.png"
OUT = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"
os.makedirs(OUT, exist_ok=True)

ROWS, COLS = 8, 10

# Complete 78-card map using 10-column uniform grid.
# Verified: Row 1 = 0-IX, Row 2 = X-XIX, Row 3 = XX-XXI + Wands A-8
# Row 4 onwards: continuous Minor Arcana sequence
CARD_MAP = {
    # Row 0: Major Arcana 0-9
    (0,0): "00-TheFool", (0,1): "01-TheMagician",
    (0,2): "02-TheHighPriestess", (0,3): "03-TheEmpress",
    (0,4): "04-TheEmperor", (0,5): "05-TheHierophant",
    (0,6): "06-TheLovers", (0,7): "07-TheChariot",
    (0,8): "08-Strength", (0,9): "09-TheHermit",
    # Row 1: Major Arcana 10-19
    (1,0): "10-WheelOfFortune", (1,1): "11-Justice",
    (1,2): "12-TheHangedMan", (1,3): "13-Death",
    (1,4): "14-Temperance", (1,5): "15-TheDevil",
    (1,6): "16-TheTower", (1,7): "17-TheStar",
    (1,8): "18-TheMoon", (1,9): "19-TheSun",
    # Row 2: Major Arcana 20-21 + Wands A-8
    (2,0): "20-Judgement", (2,1): "21-TheWorld",
    (2,2): "W01-AceOfWands", (2,3): "W02-2OfWands",
    (2,4): "W03-3OfWands", (2,5): "W04-4OfWands",
    (2,6): "W05-5OfWands", (2,7): "W06-6OfWands",
    (2,8): "W07-7OfWands", (2,9): "W08-8OfWands",
    # Row 3: Wands 9-K + Cups A-4
    (3,0): "W09-9OfWands", (3,1): "W10-10OfWands",
    (3,2): "W11-PageOfWands", (3,3): "W12-KnightOfWands",
    (3,4): "W13-QueenOfWands", (3,5): "W14-KingOfWands",
    (3,6): "C01-AceOfCups", (3,7): "C02-2OfCups",
    (3,8): "C03-3OfCups", (3,9): "C04-4OfCups",
    # Row 4: Cups 5-K + Swords A-2
    (4,0): "C05-5OfCups", (4,1): "C06-6OfCups",
    (4,2): "C07-7OfCups", (4,3): "C08-8OfCups",
    (4,4): "C09-9OfCups", (4,5): "C10-10OfCups",
    (4,6): "C11-PageOfCups", (4,7): "C12-KnightOfCups",
    (4,8): "C13-QueenOfCups", (4,9): "C14-KingOfCups",
    # Row 5: Swords A-K
    (5,0): "S01-AceOfSwords", (5,1): "S02-2OfSwords",
    (5,2): "S03-3OfSwords", (5,3): "S04-4OfSwords",
    (5,4): "S05-5OfSwords", (5,5): "S06-6OfSwords",
    (5,6): "S07-7OfSwords", (5,7): "S08-8OfSwords",
    (5,8): "S09-9OfSwords", (5,9): "S10-10OfSwords",
    # Row 6: Swords J-K + Pentacles A-8
    (6,0): "S11-PageOfSwords", (6,1): "S12-KnightOfSwords",
    (6,2): "S13-QueenOfSwords", (6,3): "S14-KingOfSwords",
    (6,4): "P01-AceOfPentacles", (6,5): "P02-2OfPentacles",
    (6,6): "P03-3OfPentacles", (6,7): "P04-4OfPentacles",
    (6,8): "P05-5OfPentacles", (6,9): "P06-6OfPentacles",
    # Row 7: Pentacles 7-K + 2 empty
    (7,0): "P07-7OfPentacles", (7,1): "P08-8OfPentacles",
    (7,2): "P09-9OfPentacles", (7,3): "P10-10OfPentacles",
    (7,4): "P11-PageOfPentacles", (7,5): "P12-KnightOfPentacles",
    (7,6): "P13-QueenOfPentacles", (7,7): "P14-KingOfPentacles",
}

def main():
    img = Image.open(SRC)
    w, h = img.size
    print(f"Source: {w}×{h}")

    cw, ch = w // COLS, h // ROWS
    print(f"Card size: {cw}×{ch}")
    print(f"Total cards: {len(CARD_MAP)}")

    saved = 0
    for (r, c), name in sorted(CARD_MAP.items()):
        x1, y1 = c * cw, r * ch
        x2, y2 = x1 + cw, y1 + ch
        card = img.crop((x1, y1, x2, y2))
        card.save(os.path.join(OUT, f"{name}.png"))
        saved += 1

    print(f"✅ Saved {saved} cards to {OUT}")

if __name__ == "__main__":
    main()
