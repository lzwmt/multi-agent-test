#!/usr/bin/env python3
"""Split 78-card tarot grid."""
import os
from PIL import Image

SRC = "/root/.hermes/image_cache/img_c1f71f3c6565.png"
OUT = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"
os.makedirs(OUT, exist_ok=True)

img = Image.open(SRC)

# Shifted down 10px
ROW_Y = [9, 204, 409, 588, 740, 892, 1064, 1244, 1418]

COL_BOUNDS_10 = [0, 116, 226, 333, 433, 541, 643, 748, 856, 964, 1074]
COL_BOUNDS_8  = [0, 138, 273, 407, 540, 676, 813, 946, 1077]

CARDS = [
    "00-TheFool","01-TheMagician","02-TheHighPriestess","03-TheEmpress",
    "04-TheEmperor","05-TheHierophant","06-TheLovers","07-TheChariot",
    "08-Strength","09-TheHermit",
    "10-WheelOfFortune","11-Justice","12-TheHangedMan","13-Death",
    "14-Temperance","15-TheDevil","16-TheTower","17-TheStar",
    "18-TheMoon","19-TheSun",
    "20-Judgement","21-TheWorld",
    "Wands-Ace","Wands-2","Wands-3","Wands-4","Wands-5","Wands-6","Wands-7","Wands-8",
    "Wands-9","Wands-10","Wands-Page","Wands-Knight","Wands-Queen","Wands-King",
    "Cups-Ace","Cups-2","Cups-3","Cups-4","Cups-5","Cups-6","Cups-7","Cups-8",
    "Cups-9","Cups-10","Cups-Page","Cups-Knight","Cups-Queen","Cups-King",
    "Swords-Ace","Swords-2","Swords-3","Swords-4","Swords-5","Swords-6",
    "Swords-7","Swords-8","Swords-9","Swords-10",
    "Swords-Page","Swords-Knight","Swords-Queen","Swords-King",
    "Pentacles-Ace","Pentacles-2","Pentacles-3","Pentacles-4",
    "Pentacles-5","Pentacles-6","Pentacles-7","Pentacles-8",
    "Pentacles-9","Pentacles-10","Pentacles-Page","Pentacles-Knight",
    "Pentacles-Queen","Pentacles-King",
]
for f in os.listdir(OUT):
    if f.endswith('.webp'): os.remove(os.path.join(OUT, f))
idx = 0
for row in range(8):
    y1, y2 = ROW_Y[row], ROW_Y[row + 1]
    is_8col = row in (3, 4, 7)
    col_bounds = COL_BOUNDS_8 if is_8col else COL_BOUNDS_10
    n_cols = 8 if is_8col else 10
    for col in range(n_cols):
        x1, x2 = col_bounds[col], col_bounds[col + 1]
        img.crop((x1, y1, x2, y2)).save(os.path.join(OUT, f"{CARDS[idx]}.webp"), "WEBP", quality=90)
        idx += 1
print(f"Done: {idx} cards")
