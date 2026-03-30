#!/usr/bin/env python3
"""
Convert agency-agents markdown files to OpenClaw SKILL.md format
"""

import os
import re
import yaml
from pathlib import Path

AGENCY_DIR = Path.home() / ".openclaw/skills/agency-agents"
OUTPUT_DIR = Path("/root/.openclaw/workspace/skills/agency-agents-converted")

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return fm, body
            except yaml.YAMLError:
                pass
    return None, content

def extract_system_prompt(body, agent_name):
    """Extract system prompt content - everything from 'You are...' or ## Identity to end of document"""
    lines = body.split('\n')
    start_idx = -1
    
    # Find the line starting with "You are"
    for i, line in enumerate(lines):
        if line.strip().startswith('You are'):
            start_idx = i
            break
    
    if start_idx >= 0:
        # Return everything from that line to the end
        return '\n'.join(lines[start_idx:]).strip()
    
    # Fallback 1: Find ## Identity or ## Identity & Memory
    for i, line in enumerate(lines):
        if re.match(r'^##\s+(Identity|Identity & Memory)', line, re.IGNORECASE):
            start_idx = i
            break
    
    if start_idx >= 0:
        return '\n'.join(lines[start_idx:]).strip()
    
    # Fallback 2: Find ## Core Mission
    for i, line in enumerate(lines):
        if re.match(r'^##\s+Core Mission', line, re.IGNORECASE):
            start_idx = i
            break
    
    if start_idx >= 0:
        return '\n'.join(lines[start_idx:]).strip()
    
    # Fallback 3: return everything after first heading
    for i, line in enumerate(lines):
        if line.startswith('#') and not line.startswith('##'):
            if i < len(lines) - 1:
                return '\n'.join(lines[i+1:]).strip()
    
    return body.strip()

def generate_when_to_use(frontmatter, body):
    """Generate 'When to use this skill' bullet points"""
    vibe = frontmatter.get('vibe', '')
    description = frontmatter.get('description', '')
    bullets = []
    
    # Extract from vibe - split carefully avoiding splitting compound terms
    if vibe:
        # Don't split on dashes within words, only on em-dash or spaced dash
        parts = re.split(r'\s*[—–]\s*', vibe)
        for part in parts:
            part = part.strip()
            if part and len(part) > 5:
                bullets.append(part)
    
    # Try to extract from Core Mission section
    if "## 🎯 Your Core Mission" in body or "## Your Core Mission" in body:
        mission_match = re.search(r'##.*Core Mission.*?(?=##|$)', body, re.DOTALL)
        if mission_match:
            mission_text = mission_match.group(0)
            mission_bullets = re.findall(r'^[\s]*[-•]\s*(.+)$', mission_text, re.MULTILINE)
            for b in mission_bullets[:4]:
                if b not in bullets:
                    bullets.append(b)
    
    # Fallback to description
    if not bullets and description:
        bullets.append(description)
    
    # Ensure we have at least one bullet
    if not bullets:
        bullets.append(f"Tasks requiring {frontmatter.get('name', 'specialized')} expertise")
    
    return "\n".join([f"- {b}" for b in bullets[:6]])

def generate_skill_md(frontmatter, body):
    """Generate SKILL.md content"""
    name = frontmatter.get('name', 'Unknown')
    description = frontmatter.get('description', '')
    vibe = frontmatter.get('vibe', '')
    emoji = frontmatter.get('emoji', '🤖')

    system_prompt = extract_system_prompt(body, name)
    usage_section = generate_when_to_use(frontmatter, body)

    skill_content = f"""# {name}

> {description}

## Description

{vibe}

**When to use this skill:**
{usage_section}

## System Prompt

{system_prompt}

## Usage

Activate this skill when you need assistance with {name.lower()} related tasks, architecture decisions, or implementation guidance.
"""

    return skill_content

def convert_file(input_path, category):
    """Convert a single agency agent file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)
    if not frontmatter:
        print(f"  ⚠️  No frontmatter: {input_path.name}")
        return False

    name = frontmatter.get('name', input_path.stem)
    # Create safe directory name
    safe_name = re.sub(r'[^\w\-]+', '-', name.lower()).strip('-')

    output_category_dir = OUTPUT_DIR / category / safe_name
    output_category_dir.mkdir(parents=True, exist_ok=True)

    skill_content = generate_skill_md(frontmatter, body)

    output_path = output_category_dir / "SKILL.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(skill_content)

    print(f"  ✅ {name}")
    return True

def main():
    print("Converting agency-agents to OpenClaw Skills...")
    print(f"Input: {AGENCY_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    converted = 0
    categories = []

    for category_dir in AGENCY_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        if category_dir.name in ['.git', 'scripts', 'examples', 'integrations']:
            continue

        category = category_dir.name
        md_files = list(category_dir.glob("*.md"))

        if not md_files:
            continue

        print(f"📁 {category}/")
        categories.append(category)

        for md_file in md_files:
            total += 1
            if convert_file(md_file, category):
                converted += 1

    print()
    print(f"✅ Done: {converted}/{total} files converted")
    print(f"Categories: {', '.join(categories)}")

if __name__ == "__main__":
    main()
