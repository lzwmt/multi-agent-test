#!/usr/bin/env python3
"""非均匀网格切割 v3: 用实际行边界 + 用户指定的每行牌数"""
from PIL import Image
import os

SRC = "/root/.hermes/image_cache/img_d0a172aca490.png"
DST = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"

img = Image.open(SRC)
W, H = img.size

# 实际行边界 (从像素分析得到)
ROW_BOUNDS = [
    (4, 221),      # Row 1: 218px
    (225, 440),    # Row 2: 216px
    (444, 645),    # Row 3: 202px
    (649, 806),    # Row 4: 158px
    (809, 970),    # Row 5: 162px
    (973, 1137),   # Row 6: 165px
    (1140, 1290),  # Row 7: 151px
    (1294, 1451),  # Row 8: 158px
    (1455, 1535),  # Row 9: 81px (partial)
]

# 用户说: 第4、5、8行每行8个，其他行每行10个
# 10+10+10+8+8+10+10+8+? = 74+? = 78 → 第9行=4
CARDS_PER_ROW = [10, 10, 10, 8, 8, 10, 10, 8, 4]
TOTAL = sum(CARDS_PER_ROW)
assert TOTAL == 78, f"Total {TOTAL} != 78"

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

print(f"Source: {W}x{H}")
print(f"Rows: {len(ROW_BOUNDS)}, Cards: {TOTAL}")
print()

idx = 0
for ri, ((y1, y2), n_cards) in enumerate(zip(ROW_BOUNDS, CARDS_PER_ROW)):
    card_w = W / n_cards
    row_h = y2 - y1
    for col in range(n_cards):
        if idx >= 78:
            break
        x1 = int(col * card_w)
        x2 = int((col + 1) * card_w)
        card = img.crop((x1, y1, x2, y2))
        name = ALL_NAMES[idx]
        out = os.path.join(DST, f"{name}.webp")
        card.save(out, "WEBP", quality=90)
        idx += 1
    print(f"  Row {ri+1}: {n_cards} cards, {int(card_w)}x{row_h}px")

print(f"\nDone: {idx} cards → {DST}")
