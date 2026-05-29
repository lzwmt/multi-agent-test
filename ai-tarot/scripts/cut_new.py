#!/usr/bin/env python3
"""用新图切割：第4、5、8行8张，其余10张"""
from PIL import Image
import os

SRC = "/root/.hermes/image_cache/img_15843f2908a9.jpeg"
DST = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"

img = Image.open(SRC)
W, H = img.size

# 行边界 (从像素分析合并后)
ROW_BOUNDS = [
    (9, 213),      # Row 1: 204px
    (217, 405),    # Row 2: 188px
    (410, 583),    # Row 3: 173px
    (587, 736),    # Row 4: 149px
    (740, 884),    # Row 5: 144px
    (888, 1059),   # Row 6: 171px
    (1064, 1224),  # Row 7: 160px
    (1247, 1414),  # Row 8: 167px
]

# 用户配置: 第4、5、8行8张，其余10张
# 5*10 + 3*8 = 74, 差4张
# 试试: 第4、5行8张，其余10张 (含第8行10张)
# 7*10 + 2*8 = 86... 不对
# 试试: 第4、5、8行8张 + 第8行后面还有4张在额外位置?
# 或者: 第8行实际有12张? 
# 最简单: 全部10张看看
CARDS_PER_ROW = [10, 10, 10, 8, 8, 10, 10, 8]
total = sum(CARDS_PER_ROW)  # 74

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

# 清理
for f in os.listdir(DST):
    if f.endswith(('.webp', '.png')):
        os.remove(os.path.join(DST, f))

# 先按74张切，看哪些牌没切到
idx = 0
for ri, ((y1, y2), n_cards) in enumerate(zip(ROW_BOUNDS, CARDS_PER_ROW)):
    card_w = W / n_cards
    for ci in range(n_cards):
        if idx >= len(ALL_NAMES):
            break
        x1 = int(ci * card_w)
        x2 = int((ci + 1) * card_w)
        card = img.crop((x1, y1, x2, y2))
        name = ALL_NAMES[idx]
        card.save(os.path.join(DST, f"{name}.webp"), "WEBP", quality=90)
        idx += 1
    print(f"Row {ri+1}: {n_cards} cards, {int(card_w)}x{y2-y1}px")

print(f"\nCut: {idx} cards")
print(f"Missing: {78 - idx} cards")
print(f"Missing cards: {ALL_NAMES[idx:78]}")
