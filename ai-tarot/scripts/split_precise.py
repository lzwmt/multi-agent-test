#!/usr/bin/env python3
"""Split 78-card tarot grid using DETECTED row boundaries.

Row heights are NOT uniform! Detected from left-strip edge analysis:
  Row 0: y=9 to 194   (185px)
  Row 1: y=219 to 387  (168px)  
  Row 2: y=409 to 565  (156px)
  Row 3: y=588 to 731  (143px)
  Row 4: y=741 to 886  (145px)
  Row 5: y=905 to 1040 (135px)
  Row 6: y=1058 to 1220(162px)
  Row 7: y=1240 to 1418(178px)

Source: img_c1f71f3c6565.png (1086x1448)
"""

import os
from PIL import Image

SRC = "/root/.hermes/image_cache/img_c1f71f3c6565.png"
OUT = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"
os.makedirs(OUT, exist_ok=True)

img = Image.open(SRC)
w, h = img.size
print(f"Source: {w}x{h}")

# Detected row boundaries (from left-strip edge analysis)
ROW_BOUNDS = [
    (9, 194),     # Row 0: Fool-Hermit (185px)
    (219, 387),   # Row 1: Wheel-Sun (168px)
    (409, 565),   # Row 2: Judgement-Wands8 (156px)
    (588, 731),   # Row 3: Wands9-Cups4 (143px)
    (741, 886),   # Row 4: Cups5-King (145px)
    (905, 1040),  # Row 5: Swords A-10 (135px)
    (1058, 1220), # Row 6: SwordsJ-Pentacles6 (162px)
    (1240, 1418), # Row 7: Pentacles7-King (178px)
]

# Column boundaries (from vertical edge detection)
# 10 columns, using detected border positions
COL_BOUNDS = [
    (0, 115),     # Col 0
    (115, 222),   # Col 1
    (222, 331),   # Col 2
    (331, 432),   # Col 3
    (432, 545),   # Col 4
    (545, 644),   # Col 5
    (644, 749),   # Col 6
    (749, 854),   # Col 7
    (854, 962),   # Col 8
    (962, 1086),  # Col 9
]

# Card names (standard tarot order, 78 cards)
CARD_NAMES = [
    # Row 0 (10): Major Arcana 0-9
    "00-TheFool", "01-TheMagician", "02-TheHighPriestess", "03-TheEmpress",
    "04-TheEmperor", "05-TheHierophant", "06-TheLovers", "07-TheChariot",
    "08-Strength", "09-TheHermit",
    # Row 1 (10): Major Arcana 10-19
    "10-WheelOfFortune", "11-Justice", "12-TheHangedMan", "13-Death",
    "14-Temperance", "15-TheDevil", "16-TheTower", "17-TheStar",
    "18-TheMoon", "19-TheSun",
    # Row 2 (10): Major Arcana 20-21 + Wands A-8
    "20-Judgement", "21-TheWorld",
    "Wands-Ace", "Wands-2", "Wands-3", "Wands-4",
    "Wands-5", "Wands-6", "Wands-7", "Wands-8",
    # Row 3 (10): Wands 9-K + Cups A-4
    "Wands-9", "Wands-10", "Wands-Page", "Wands-Knight",
    "Wands-Queen", "Wands-King", "Cups-Ace", "Cups-2",
    "Cups-3", "Cups-4",
    # Row 4 (10): Cups 5-K
    "Cups-5", "Cups-6", "Cups-7", "Cups-8",
    "Cups-9", "Cups-10", "Cups-Page", "Cups-Knight",
    "Cups-Queen", "Cups-King",
    # Row 5 (10): Swords A-10
    "Swords-Ace", "Swords-2", "Swords-3", "Swords-4",
    "Swords-5", "Swords-6", "Swords-7", "Swords-8",
    "Swords-9", "Swords-10",
    # Row 6 (10): Swords J-K + Pentacles A-6
    "Swords-Page", "Swords-Knight", "Swords-Queen", "Swords-King",
    "Pentacles-Ace", "Pentacles-2", "Pentacles-3", "Pentacles-4",
    "Pentacles-5", "Pentacles-6",
    # Row 7 (8): Pentacles 7-K
    "Pentacles-7", "Pentacles-8", "Pentacles-9", "Pentacles-10",
    "Pentacles-Page", "Pentacles-Knight", "Pentacles-Queen", "Pentacles-King",
]

def main():
    # Clean existing files
    for f in os.listdir(OUT):
        if f.endswith('.webp'):
            os.remove(os.path.join(OUT, f))

    saved = 0
    idx = 0
    
    for row_idx, (y1, y2) in enumerate(ROW_BOUNDS):
        row_h = y2 - y1
        
        # Determine number of columns for this row
        if row_idx < 7:
            n_cols = 10
        else:
            n_cols = 8  # Last row has 8 cards
        
        for col in range(n_cols):
            if idx >= len(CARD_NAMES):
                break
            
            name = CARD_NAMES[idx]
            x1, x2 = COL_BOUNDS[col]
            
            card = img.crop((x1, y1, x2, y2))
            out_path = os.path.join(OUT, f"{name}.webp")
            card.save(out_path, "WEBP", quality=90)
            saved += 1
            idx += 1
        
        print(f"  Row {row_idx}: y={y1}-{y2} ({row_h}px), {n_cols} cards, "
              f"{CARD_NAMES[idx-n_cols]} → {CARD_NAMES[idx-1]}")
    
    print(f"\nSaved {saved} cards to {OUT}")
    webp_count = len([f for f in os.listdir(OUT) if f.endswith('.webp')])
    print(f"Total .webp files: {webp_count}")

if __name__ == "__main__":
    main()
