#!/usr/bin/env python3
"""切图脚本：将78张牌大图切成单独的牌面图片"""
from PIL import Image
import os

img = Image.open("/root/.hermes/image_cache/img_d0a172aca490.png")
w, h = img.size
print(f"Image: {w}x{h}")

cols = 9
rows = 7  # 7 rows visible (last row may be partial)
card_w = w // cols
card_h = h // rows

output_dir = "/root/.openclaw/workspace/ai-tarot/frontend/src/assets/cards"
os.makedirs(output_dir, exist_ok=True)

# Card order based on vision analysis of the grid
# Row 1 (0-8): Fool(0) to Chariot(7) + start of Strength(8)
# Row 2 (9-17): Strength(8) to Devil(15) + Tower(16) start
# Row 3 (18-26): Tower(16) to World(21) + Wands_Ace + Wands_Two + Wands_Three start
# Row 4 (27-35): Wands_Three to Wands_Page
# Row 5 (36-44): Wands_Knight to Cups_Six
# Row 6 (45-53): Cups_Seven to Swords_Ace/Two
# Row 7 (54-62): Swords_Knight to Pentacles_Five (partial)

all_names = [
    # Row 1 (9 cards)
    "00_The_Fool", "01_The_Magician", "02_The_High_Priestess", "03_The_Empress",
    "04_The_Emperor", "05_The_Hierophant", "06_The_Lovers", "07_The_Chariot",
    "08_Strength",
    # Row 2 (9 cards)
    "09_The_Hermit", "10_Wheel_of_Fortune", "11_Justice", "12_The_Hanged_Man",
    "13_Death", "14_Temperance", "15_The_Devil", "16_The_Tower",
    "17_The_Star",
    # Row 3 (9 cards)
    "18_The_Moon", "19_The_Sun", "20_Judgment", "21_The_World",
    "Wands_Ace", "Wands_Two", "Wands_Three", "Wands_Four",
    "Wands_Five",
    # Row 4 (9 cards)
    "Wands_Six", "Wands_Seven", "Wands_Eight", "Wands_Nine",
    "Wands_Ten", "Wands_Page", "Wands_Knight", "Wands_Queen",
    "Wands_King",
    # Row 5 (9 cards)
    "Cups_Ace", "Cups_Two", "Cups_Three", "Cups_Four",
    "Cups_Five", "Cups_Six", "Cups_Seven", "Cups_Eight",
    "Cups_Nine",
    # Row 6 (9 cards)
    "Cups_Ten", "Cups_Page", "Cups_Knight", "Cups_Queen",
    "Cups_King", "Swords_Ace", "Swords_Two", "Swords_Three",
    "Swords_Four",
    # Row 7 (9 cards, may be partial)
    "Swords_Five", "Swords_Six", "Swords_Seven", "Swords_Eight",
    "Swords_Nine", "Swords_Ten", "Swords_Page", "Swords_Knight",
    "Swords_Queen",
]

count = 0
for row in range(rows):
    for col in range(cols):
        idx = row * cols + col
        if idx >= len(all_names):
            break
        x1 = col * card_w
        y1 = row * card_h
        x2 = x1 + card_w
        y2 = y1 + card_h
        card = img.crop((x1, y1, x2, y2))
        name = all_names[idx]
        path = os.path.join(output_dir, f"{name}.png")
        card.save(path)
        count += 1
        print(f"  [{row},{col}] {name}.png ({card_w}x{card_h})")

print(f"\nDone: {count} cards saved to {output_dir}")
print(f"Missing: Swords_King, Pentacles_Ace through Pentacles_King (15 cards)")
print("Need a second image with the bottom portion of the deck.")
