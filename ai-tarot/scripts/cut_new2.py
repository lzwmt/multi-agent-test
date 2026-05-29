#!/usr/bin/env python3
"""新图全部按10列切，取前78张"""
from PIL import Image
import os

SRC = "/root/.hermes/image_cache/img_15843f2908a9.jpeg"
DST = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"

img = Image.open(SRC)
W, H = img.size

# 行边界
ROW_BOUNDS = [
    (9, 213), (217, 405), (410, 583),
    (587, 736), (740, 884), (888, 1059),
    (1064, 1224), (1247, 1414),
]

MAJOR = [
    "00-TheFool", "01-TheMagician", "02-TheHighPriestess", "03-TheEmpress",
    "04-TheEmperor", "05-TheHierophant", "06-TheLovers", "07-TheChariot",
    "08-Strength", "09-TheHermit", "10-WheelOfFortune", "11-Justice",
    "12-TheHangedMan", "13-Death", "14-Temperance", "15-TheDevil",
    "16-TheTower", "17-TheStar", "18-TheMoon", "19-TheSun",
    "20-Judgment", "21-TheWorld"
]
RANKS = ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Page","Knight","Queen","King"]
MINOR = [f"{s}-{r}" for s in ["Wands","Cups","Swords","Pentacles"] for r in RANKS]
ALL_NAMES = MAJOR + MINOR

for f in os.listdir(DST):
    if f.endswith(('.webp', '.png')):
        os.remove(os.path.join(DST, f))

COLS = 10
idx = 0
for ri, (y1, y2) in enumerate(ROW_BOUNDS):
    cw = W / COLS
    for ci in range(COLS):
        if idx >= 78:
            break
        x1 = int(ci * cw)
        x2 = int((ci + 1) * cw)
        card = img.crop((x1, y1, x2, y2))
        name = ALL_NAMES[idx]
        card.save(os.path.join(DST, f"{name}.webp"), "WEBP", quality=90)
        idx += 1
    print(f"Row {ri+1}: {COLS} cards, {int(cw)}x{y2-y1}px")

print(f"\nDone: {idx} cards")
