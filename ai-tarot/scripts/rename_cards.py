#!/usr/bin/env python3
"""
重命名工具：将切割后的牌面图片按牌名重命名。

用法：
  python3 rename_cards.py <图片目录> <牌名列表>

牌名列表格式（每行一个）：
  0_The_Fool
  01_The_Magician
  ...

示例：
  # 重命名大阿尔卡纳
  python3 rename_cards.py ./major_cards/ major_arcana.txt

  # 重命名权杖
  python3 rename_cards.py ./wands_cards/ wands.txt
"""

import sys
import os
from pathlib import Path

# 预定义的牌名列表
MAJOR_ARCANA = [
    "00_The_Fool", "01_The_Magician", "02_The_High_Priestess", "03_The_Empress",
    "04_The_Emperor", "05_The_Hierophant", "06_The_Lovers", "07_The_Chariot",
    "08_Strength", "09_The_Hermit", "10_Wheel_of_Fortune", "11_Justice",
    "12_The_Hanged_Man", "13_Death", "14_Temperance", "15_The_Devil",
    "16_The_Tower", "17_The_Star", "18_The_Moon", "19_The_Sun",
    "20_Judgment", "21_The_World"
]

WANDS = [
    "Wands_Ace", "Wands_Two", "Wands_Three", "Wands_Four", "Wands_Five",
    "Wands_Six", "Wands_Seven", "Wands_Eight", "Wands_Nine", "Wands_Ten",
    "Wands_Page", "Wands_Knight", "Wands_Queen", "Wands_King"
]

CUPS = [
    "Cups_Ace", "Cups_Two", "Cups_Three", "Cups_Four", "Cups_Five",
    "Cups_Six", "Cups_Seven", "Cups_Eight", "Cups_Nine", "Cups_Ten",
    "Cups_Page", "Cups_Knight", "Cups_Queen", "Cups_King"
]

SWORDS = [
    "Swords_Ace", "Swords_Two", "Swords_Three", "Swords_Four", "Swords_Five",
    "Swords_Six", "Swords_Seven", "Swords_Eight", "Swords_Nine", "Swords_Ten",
    "Swords_Page", "Swords_Knight", "Swords_Queen", "Swords_King"
]

PENTACLES = [
    "Pentacles_Ace", "Pentacles_Two", "Pentacles_Three", "Pentacles_Four", "Pentacles_Five",
    "Pentacles_Six", "Pentacles_Seven", "Pentacles_Eight", "Pentacles_Nine", "Pentacles_Ten",
    "Pentacles_Page", "Pentacles_Knight", "Pentacles_Queen", "Pentacles_King"
]

ALL_CARDS = MAJOR_ARCANA + WANDS + CUPS + SWORDS + PENTACLES


def rename_cards(image_dir: str, card_names: list = None, prefix: str = ""):
    """将目录中的图片按顺序重命名为牌名"""
    # 获取所有图片文件
    files = sorted([
        f for f in os.listdir(image_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ])

    if not card_names:
        # 默认使用所有78张牌名
        card_names = ALL_CARDS

    if len(files) != len(card_names):
        print(f"⚠️  文件数({len(files)})与牌名数({len(card_names)})不匹配")
        print(f"   文件: {files[:5]}...")
        print(f"   牌名: {card_names[:5]}...")
        # 继续处理，取最小值
        count = min(len(files), len(card_names))
    else:
        count = len(files)

    for i in range(count):
        old_path = os.path.join(image_dir, files[i])
        ext = Path(files[i]).suffix
        new_name = f"{prefix}{card_names[i]}{ext}"
        new_path = os.path.join(image_dir, new_name)
        os.rename(old_path, new_path)
        print(f"  {files[i]} → {new_name}")

    print(f"\n✅ 重命名完成: {count} 张牌面")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n预定义牌名:")
        print(f"  MAJOR_ARCANA ({len(MAJOR_ARCANA)}张): {' '.join(MAJOR_ARCANA[:3])}...")
        print(f"  WANDS ({len(WANDS)}张): {' '.join(WANDS[:3])}...")
        print(f"  CUPS ({len(CUPS)}张): {' '.join(CUPS[:3])}...")
        print(f"  SWORDS ({len(SWORDS)}张): {' '.join(SWORDS[:3])}...")
        print(f"  PENTACLES ({len(PENTACLES)}张): {' '.join(PENTACLES[:3])}...")
        print(f"  ALL_CARDS ({len(ALL_CARDS)}张)")
        sys.exit(1)

    image_dir = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.path.isdir(image_dir):
        print(f"❌ 目录不存在: {image_dir}")
        sys.exit(1)

    # 根据目录名或文件数自动选择牌名列表
    dir_name = Path(image_dir).name.lower()
    if "major" in dir_name:
        names = MAJOR_ARCANA
    elif "wand" in dir_name:
        names = WANDS
    elif "cup" in dir_name:
        names = CUPS
    elif "sword" in dir_name:
        names = SWORDS
    elif "penta" in dir_name or "coin" in dir_name:
        names = PENTACLES
    else:
        names = None  # 使用所有78张

    rename_cards(image_dir, names, prefix)
