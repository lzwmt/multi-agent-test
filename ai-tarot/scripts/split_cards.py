#!/usr/bin/env python3
"""
切图工具：将AI生成的塔罗牌大图切割成单独的牌面图片。

用法：
  python3 split_cards.py <大图路径> <每行几张> <共几行> [输出目录]

示例：
  # 一张大图里有 6列×4行=24张牌
  python3 split_cards.py major_24.png 6 4

  # 指定输出目录
  python3 split_cards.py wands_14.png 7 2 ./output/wands
"""

import sys
import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("需要安装 Pillow: pip3 install Pillow")
    sys.exit(1)


def split_image(image_path: str, cols: int, rows: int, output_dir: str = None):
    """将大图切割成 cols×rows 张小图"""
    img = Image.open(image_path)
    w, h = img.size
    card_w = w // cols
    card_h = h // rows

    # 输出目录
    if output_dir is None:
        stem = Path(image_path).stem
        output_dir = str(Path(image_path).parent / f"{stem}_cards")
    os.makedirs(output_dir, exist_ok=True)

    count = 0
    for row in range(rows):
        for col in range(cols):
            x1 = col * card_w
            y1 = row * card_h
            x2 = x1 + card_w
            y2 = y1 + card_h
            card = img.crop((x1, y1, x2, y2))
            # 命名：row_col.png (0-indexed)
            filename = f"{row}_{col}.png"
            card.save(os.path.join(output_dir, filename))
            count += 1

    print(f"✅ 切割完成: {count} 张牌面 → {output_dir}/")
    print(f"   原图: {w}×{h}px → 每张: {card_w}×{card_h}px")
    return output_dir


def batch_split(image_path: str, total_cards: int, cols: int, output_dir: str = None):
    """自动计算行数并切割"""
    import math
    rows = math.ceil(total_cards / cols)
    return split_image(image_path, cols, rows, output_dir)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    image_path = sys.argv[1]
    cols = int(sys.argv[2])
    rows = int(sys.argv[3])
    output_dir = sys.argv[4] if len(sys.argv) > 4 else None

    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        sys.exit(1)

    split_image(image_path, cols, rows, output_dir)
