#!/usr/bin/env python3
"""全部按10列切割，9行"""
from PIL import Image
import os

SRC = "/root/.hermes/image_cache/img_d0a172aca490.png"
DST = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"

img = Image.open(SRC)
W, H = img.size

ROW_BOUNDS = [
    (4, 221), (225, 440), (444, 645),
    (649, 806), (809, 970), (973, 1137),
    (1140, 1290), (1294, 1451), (1455, 1535),
]

COLS = 10

# 78张牌名
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

# 清理旧文件
for f in os.listdir(DST):
    if f.endswith(('.webp', '.png')):
        os.remove(os.path.join(DST, f))

idx = 0
for ri, (y1, y2) in enumerate(ROW_BOUNDS):
    row_h = y2 - y1
    card_w = W / COLS
    for ci in range(COLS):
        if idx >= 78:
            break
        x1 = int(ci * card_w)
        x2 = int((ci + 1) * card_w)
        card = img.crop((x1, y1, x2, y2))
        name = ALL_NAMES[idx]
        out = os.path.join(DST, f"{name}.webp")
        card.save(out, "WEBP", quality=90)
        idx += 1
    print(f"Row {ri+1}: {min(COLS, 78 - (ri)*COLS)} cards, {int(card_w)}x{row_h}px")

print(f"\nDone: {idx} cards → {DST}")
