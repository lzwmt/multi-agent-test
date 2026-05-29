#!/usr/bin/env python3
"""
非均匀网格切割：根据每行实际牌数切割塔罗牌图片。
布局: 第4、5、8行每行8张，其余行每行10张。
"""
from PIL import Image
import os
import shutil

SRC = "/root/.hermes/image_cache/img_d0a172aca490.png"
DST = "/root/.openclaw/workspace/ai-tarot/frontend/public/cards"

img = Image.open(SRC)
W, H = img.size

# 行配置: (该行牌数, 行索引)
# 用户说: 4,5,8行一行8个，其他行一行10个
# 8行: 10+10+10+8+8+10+10+8 = 74, 不够78
# 9行: 10+10+10+8+8+10+10+8+4 = 78
# 也可能8行但最后一行不是8而是12? 不合理
# 先试9行配置
ROWS_CONFIG = [10, 10, 10, 8, 8, 10, 10, 8, 4]
N_ROWS = len(ROWS_CONFIG)
TOTAL = sum(ROWS_CONFIG)
assert TOTAL == 78, f"Total cards {TOTAL} != 78"

ROW_H = H / N_ROWS  # 每行高度

# 78张牌名（标准顺序）
MAJOR = [
    "00-TheFool", "01-TheMagician", "02-TheHighPriestess", "03-TheEmpress",
    "04-TheEmperor", "05-TheHierophant", "06-TheLovers", "07-TheChariot",
    "08-Strength", "09-TheHermit", "10-WheelOfFortune", "11-Justice",
    "12-TheHangedMan", "13-Death", "14-Temperance", "15-TheDevil",
    "16-TheTower", "17-TheStar", "18-TheMoon", "19-TheSun",
    "20-Judgment", "21-TheWorld"
]
SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
RANKS = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven",
         "Eight", "Nine", "Ten", "Page", "Knight", "Queen", "King"]
MINOR = [f"{s}-{r}" for s in SUITS for r in RANKS]
ALL_NAMES = MAJOR + MINOR  # 78 names

print(f"Source: {W}x{H}, {N_ROWS} rows, {TOTAL} cards")
print(f"Row height: {ROW_H:.1f}px")

# 清理旧文件
for f in os.listdir(DST):
    if f.endswith('.webp') or f.endswith('.png'):
        os.remove(os.path.join(DST, f))
print(f"Cleared old cards from {DST}")

idx = 0
for row_i, n_cards in enumerate(ROWS_CONFIG):
    card_w = W / n_cards  # 该行每张牌的宽度
    y1 = int(row_i * ROW_H)
    y2 = int((row_i + 1) * ROW_H)
    actual_h = y2 - y1
    
    for col in range(n_cards):
        if idx >= 78:
            break
        x1 = int(col * card_w)
        x2 = int((col + 1) * card_w)
        actual_w = x2 - x1
        
        card = img.crop((x1, y1, x2, y2))
        name = ALL_NAMES[idx]
        out_path = os.path.join(DST, f"{name}.webp")
        card.save(out_path, "WEBP", quality=90)
        
        if idx < 5 or row_i in [3, 4, 7, 8]:  # 打印前几个和特殊行
            print(f"  [{row_i},{col}] {name} ({actual_w}x{actual_h})")
        idx += 1

print(f"\nDone: {idx} cards saved to {DST}")
PYEOF
