#!/usr/bin/env python3
"""Extract the 22x22 Major Arcana cross-interpretation matrix from 塔罗全书."""

import json
import re

# Card mapping: number -> Chinese name
CARD_NAMES = {
    0: "愚人", 1: "魔术师", 2: "女教主", 3: "皇后", 4: "皇帝",
    5: "教主", 6: "恋人", 7: "战车", 8: "力量", 9: "隐士",
    10: "命运之轮", 11: "正义", 12: "吊人", 13: "死神", 14: "节制",
    15: "魔鬼", 16: "塔", 17: "星辰", 18: "月亮", 19: "太阳",
    20: "审判", 21: "世界"
}

# Card header line numbers (0-indexed)
CARD_HEADER_LINES = {
    0: 996, 1: 1968, 2: 2926, 3: 3871, 4: 4784,
    5: 5702, 6: 6625, 7: 7577, 8: 8494, 9: 9391,
    10: 10268, 11: 11140, 12: 12002, 13: 12781, 14: 13658,
    15: 14502, 16: 15328,
}

# Source card number lookup from header text
HEADER_SOURCE_NUMS = {
    "愚人": 0, "魔术师": 1, "女教主": 2, "皇后": 3, "皇帝": 4,
    "教主": 5, "恋人": 6, "战车": 7, "力量": 8, "隐士": 9,
    "命运之轮": 10, "正义": 11, "吊人": 12, "死神": 13, "节制": 14,
    "魔鬼": 15, "塔": 16, "星辰": 17, "月亮": 18, "太阳": 19,
    "审判": 20, "世界": 21
}


def clean_text(text):
    """Clean extracted text of extra whitespace."""
    text = text.replace('\f', '')
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()
    return text


def find_source_num(name):
    """Find card number by Chinese name."""
    for cname, cnum in HEADER_SOURCE_NUMS.items():
        if cname in name:
            return cnum
    return None


def find_entry_boundaries(lines, section_start, section_end):
    """Find all cross-interpretation entry boundaries within a section."""
    entries = []
    
    for i in range(section_start, section_end):
        line = lines[i].strip()
        
        # Pattern 1a: "N. Name的自我启示（ENG）" - self interpretation
        match_self1 = re.search(
            r'(\d+)\.\s*(.+?)的自我启示[（(]([^）)]+)[）)]',
            line
        )
        # Pattern 1b: "N. Name自我的启示（ENG）" - self interpretation (alt)
        match_self2 = re.search(
            r'(\d+)\.\s*(.+?)自我的启示[（(]([^）)]+)[）)]',
            line
        )
        if match_self1 or match_self2:
            # Self interpretation - source = target (determined by section)
            entries.append((None, i, "self"))  # None means self
            continue
        
        # Pattern 2: "N. Name对Target的启示（ENG）" - cross interpretation
        match_cross = re.search(
            r'(\d+)\.\s*(.+?)对(.+?)的启示[（(]([^）)]+)[）)]',
            line
        )
        if match_cross:
            source_num_str = match_cross.group(1)
            source_name = match_cross.group(2).strip()
            target_name = match_cross.group(3).strip()
            
            # Find source card number
            source_num = find_source_num(source_name)
            if source_num is None:
                source_num = int(source_num_str)
            
            entries.append((source_num, i, "cross"))
            continue
    
    return entries


def parse_entry(lines, entry_start, section_end, is_self=False):
    """Parse a single cross-interpretation entry."""
    upright = ""
    reversed_text = ""
    advice = ""
    
    # Find the next entry boundary or section end
    next_entry_line = section_end
    for i in range(entry_start + 1, section_end):
        line = lines[i].strip()
        # Check if this starts a new entry
        if re.search(r'\d+\.\s*.+?(?:的自我|自我的|对.+?的)启示[（(]', line):
            next_entry_line = i
            break
    
    # Parse content between entry_start+1 and next_entry_line
    i = entry_start + 1
    state = "seeking"
    text_buf = []
    
    while i < next_entry_line:
        line = lines[i].strip()
        
        # Check for 正位解谶
        if re.match(r'正位解谶[：:]', line):
            if state == "upright":
                upright = clean_text("\n".join(text_buf))
            elif state == "reversed":
                reversed_text = clean_text("\n".join(text_buf))
            elif state == "advice":
                advice = clean_text("\n".join(text_buf))
            state = "upright"
            text_buf = []
            i += 1
            continue
        
        # Check for 逆位解谶
        if re.match(r'逆位解谶[：:]', line):
            if state == "upright":
                upright = clean_text("\n".join(text_buf))
            elif state == "reversed":
                reversed_text = clean_text("\n".join(text_buf))
            elif state == "advice":
                advice = clean_text("\n".join(text_buf))
            state = "reversed"
            text_buf = []
            i += 1
            continue
        
        # Check for 告诫
        gaojie_match = re.search(r'告诫[：:]', line)
        if gaojie_match:
            if state == "upright":
                upright = clean_text("\n".join(text_buf))
            elif state == "reversed":
                reversed_text = clean_text("\n".join(text_buf))
            elif state == "advice":
                advice = clean_text("\n".join(text_buf))
            
            # Check if there's text after the colon on the same line
            colon_pos = line.find("告诫")
            after = line[colon_pos:]
            colon_match = re.search(r'[：:]\s*(.+)', after)
            if colon_match:
                advice = colon_match.group(1).strip()
                text_buf = []
                i += 1
                while i < next_entry_line:
                    next_line = lines[i].strip()
                    if re.search(r'\d+\.\s*.+?(?:的自我|自我的|对.+?的)启示[（(]', next_line):
                        break
                    if next_line:
                        advice += "\n" + next_line
                    i += 1
                advice = clean_text(advice)
                break
            else:
                state = "advice"
                text_buf = []
                i += 1
                continue
        
        # Regular text
        if state != "seeking" and line:
            text_buf.append(lines[i])
        
        i += 1
    
    # Finalize
    if state == "upright":
        upright = clean_text("\n".join(text_buf))
    elif state == "reversed":
        reversed_text = clean_text("\n".join(text_buf))
    elif state == "advice":
        advice = clean_text("\n".join(text_buf))
    
    return {
        "upright": upright,
        "reversed": reversed_text,
        "advice": advice
    }


def main():
    with open("/tmp/tarot_all.txt", "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    print(f"Total lines: {len(lines)}")
    
    # Build the matrix
    matrix = {}
    for i in range(22):
        matrix[str(i)] = {}
    
    # Process each card section
    sorted_cards = sorted(CARD_HEADER_LINES.keys())
    
    for idx, card_num in enumerate(sorted_cards):
        start = CARD_HEADER_LINES[card_num]
        if idx + 1 < len(sorted_cards):
            next_card = sorted_cards[idx + 1]
            end = CARD_HEADER_LINES[next_card]
        else:
            end = len(lines)
        
        print(f"\n=== Card {card_num} ({CARD_NAMES[card_num]}): lines {start+1}-{end} ===")
        
        entries = find_entry_boundaries(lines, start, end)
        print(f"  Found {len(entries)} entries")
        
        for entry_idx, (source_num, entry_line, entry_type) in enumerate(entries):
            entry_data = parse_entry(lines, entry_line, end, is_self=(entry_type == "self"))
            
            target_key = str(card_num)
            
            if entry_type == "self":
                source_key = str(card_num)
            else:
                source_key = str(source_num)
            
            matrix[source_key][target_key] = entry_data
            
            has_content = bool(entry_data["upright"] or entry_data["reversed"] or entry_data["advice"])
            if has_content:
                print(f"  [{source_key}][{target_key}]: upright={len(entry_data['upright'])}ch, reversed={len(entry_data['reversed'])}ch, advice={len(entry_data['advice'])}ch")
            else:
                print(f"  [{source_key}][{target_key}]: EMPTY")
    
    # Build output
    output = {
        "source": "塔罗全书",
        "description": "22x22大阿尔卡纳交叉解读矩阵",
        "matrix": matrix
    }
    
    # Count stats
    total_entries = 0
    filled_entries = 0
    for source in matrix:
        for target in matrix[source]:
            total_entries += 1
            entry = matrix[source][target]
            if entry["upright"] or entry["reversed"] or entry["advice"]:
                filled_entries += 1
    
    print(f"\n=== Summary ===")
    print(f"Total entries: {total_entries}")
    print(f"Filled entries: {filled_entries}")
    print(f"Expected (22x22): 484")
    print(f"Coverage: {filled_entries}/484 ({100*filled_entries/484:.1f}%)")
    
    # Check coverage per target
    print(f"\n=== Coverage per target card ===")
    for t in range(22):
        ts = str(t)
        source_count = 0
        for s in range(22):
            ss = str(s)
            if ts in matrix.get(ss, {}):
                source_count += 1
        print(f"Target {t} ({CARD_NAMES[t]}): {source_count}/22 sources")
    
    with open("/root/.openclaw/workspace/ai-tarot/cross_matrix.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\nOutput written to /root/.openclaw/workspace/ai-tarot/cross_matrix.json")
    print(f"File size: {len(json.dumps(output, ensure_ascii=False))} chars")


if __name__ == "__main__":
    main()
