#!/usr/bin/env python3
import argparse
import html
import pathlib
import re
import sys
from collections import defaultdict
from typing import Any
from html.parser import HTMLParser

import markdown
import yaml


CALL_OUT_LABELS = {
    "info": "提示",
    "warn": "注意",
    "success": "建议",
    "danger": "风险",
}


THEMES = {
    "minimal": {
        "base_container": "max-width: 860px; margin: 0 auto; padding: 32px 14px; background-color: #f7f7f5;",
        "article": "background: #ffffff; border: 1px solid #e8e8e8; border-radius: 16px; padding: 28px 22px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;",
        "paragraph": "color: #2f2f2f; font-size: 16px; line-height: 1.8; margin: 16px 0;",
        "list": "color: #2f2f2f; font-size: 16px; line-height: 1.8; padding-left: 1.4em; margin: 14px 0;",
        "blockquote": "margin: 18px 0; padding: 12px 16px; background: #f8fafc; border-left: 4px solid #3b82f6; color: #334155;",
        "pre": "background: #0f172a; color: #e2e8f0; padding: 14px 16px; border-radius: 10px; overflow-x: auto; font-size: 14px; line-height: 1.6; margin: 18px 0;",
        "code": "background: #f1f5f9; color: #0f172a; padding: 2px 6px; border-radius: 6px; font-size: 0.92em;",
        "hr": "border: none; border-top: 1px solid #e5e7eb; margin: 28px 0;",
        "table": "width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 15px; line-height: 1.7;",
        "th": "border: 1px solid #e5e7eb; background: #f8fafc; padding: 10px 12px; text-align: left;",
        "td": "border: 1px solid #e5e7eb; padding: 10px 12px; text-align: left; color: #374151;",
        "meta": "font-size: 13px; color: #6b7280; line-height: 1.7; margin: 0 0 18px;",
        "image": "max-width: 100%; height: auto; border-radius: 10px; display: block; margin: 20px auto;",
        "modules": {
            "callout": {
                "base": "margin: 14px 0; padding: 12px 14px; border-radius: 10px; color: #334155;",
                "tones": {
                    "info": "background: #eff6ff; border-left: 4px solid #3b82f6;",
                    "warn": "background: #fff7ed; border-left: 4px solid #f97316;",
                    "success": "background: #ecfdf5; border-left: 4px solid #10b981;",
                    "danger": "background: #fef2f2; border-left: 4px solid #ef4444;",
                },
            },
            "verdict": "margin: 16px 0; padding: 12px 14px; border-radius: 12px; background: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #111827; color: #1f2937; font-weight: 600;",
            "module_label": "display: inline-block; margin: 0 0 8px; padding: 2px 8px; border-radius: 999px; background: #111827; color: #ffffff; font-size: 12px; line-height: 1.5; font-weight: 700;",
            "callout_label": "display: inline-block; margin: 0 0 8px; font-size: 12px; line-height: 1.5; font-weight: 700;",
            "steps": "margin: 16px 0; display: flex; flex-direction: column; gap: 10px;",
            "step": "margin: 0; padding: 10px 12px; border: 1px solid #dbe3ec; border-radius: 10px; background: #fbfdff; display: flex; gap: 10px; align-items: flex-start;",
            "step_index": "display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; border-radius: 999px; background: #111827; color: #ffffff; font-size: 12px; line-height: 1; font-weight: 700; flex-shrink: 0;",
            "step_body": "flex: 1; min-width: 0;",
            "cards": "margin: 16px 0; display: flex; flex-direction: column; gap: 8px;",
            "card": "margin: 0; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff; box-shadow: none;",
        },
        "headings": {
            "h1": "font-size: 30px; line-height: 1.35; color: #111827; margin: 8px 0 20px;",
            "h2": "font-size: 24px; line-height: 1.45; color: #1f2937; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #e5e7eb;",
            "h3": "font-size: 20px; line-height: 1.5; color: #1f2937; margin: 22px 0 10px;",
            "h4": "font-size: 18px; line-height: 1.5; color: #1f2937; margin: 20px 0 8px;",
            "h5": "font-size: 16px; line-height: 1.5; color: #1f2937; margin: 18px 0 8px;",
            "h6": "font-size: 15px; line-height: 1.5; color: #4b5563; margin: 18px 0 8px;",
        },
    },
    "warm": {
        "base_container": "max-width: 860px; margin: 0 auto; padding: 34px 14px; background: #faf7f2;",
        "article": "background: #fffdf9; border: 1px solid #f0dfd1; border-radius: 18px; padding: 30px 24px; box-shadow: 0 12px 28px rgba(181, 111, 68, 0.08); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;",
        "paragraph": "color: #4a413d; font-size: 16px; line-height: 1.85; margin: 16px 0;",
        "list": "color: #4a413d; font-size: 16px; line-height: 1.85; padding-left: 1.4em; margin: 14px 0;",
        "blockquote": "margin: 18px 0; padding: 14px 16px; background: #fdf1e6; border-left: 4px solid #d97758; color: #6f4e37;",
        "pre": "background: #3b2f2a; color: #f8ede3; padding: 14px 16px; border-radius: 10px; overflow-x: auto; font-size: 14px; line-height: 1.6; margin: 18px 0;",
        "code": "background: #f8e8dc; color: #9a3412; padding: 2px 6px; border-radius: 6px; font-size: 0.92em;",
        "hr": "border: none; border-top: 1px solid #ead3c2; margin: 28px 0;",
        "table": "width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 15px; line-height: 1.7;",
        "th": "border: 1px solid #ead3c2; background: #fcf3ea; padding: 10px 12px; text-align: left;",
        "td": "border: 1px solid #ead3c2; padding: 10px 12px; text-align: left; color: #5b4636;",
        "meta": "font-size: 13px; color: #9a7b67; line-height: 1.7; margin: 0 0 18px;",
        "image": "max-width: 100%; height: auto; border-radius: 12px; display: block; margin: 20px auto;",
        "modules": {
            "callout": {
                "base": "margin: 14px 0; padding: 12px 14px; border-radius: 12px; color: #6f4e37;",
                "tones": {
                    "info": "background: #fff4eb; border-left: 4px solid #d97758;",
                    "warn": "background: #fff3e8; border-left: 4px solid #ea580c;",
                    "success": "background: #eefbf3; border-left: 4px solid #16a34a;",
                    "danger": "background: #fff1f2; border-left: 4px solid #e11d48;",
                },
            },
            "verdict": "margin: 16px 0; padding: 12px 14px; border-radius: 14px; background: #fdf1e6; border: 1px solid #f0dfd1; border-left: 5px solid #9a3412; color: #7c2d12; font-weight: 600;",
            "module_label": "display: inline-block; margin: 0 0 8px; padding: 2px 8px; border-radius: 999px; background: #9a3412; color: #ffffff; font-size: 12px; line-height: 1.5; font-weight: 700;",
            "callout_label": "display: inline-block; margin: 0 0 8px; font-size: 12px; line-height: 1.5; font-weight: 700; color: #9a3412;",
            "steps": "margin: 16px 0; display: flex; flex-direction: column; gap: 10px;",
            "step": "margin: 0; padding: 10px 12px; border: 1px solid #ead3c2; border-radius: 10px; background: #fffcf8; display: flex; gap: 10px; align-items: flex-start;",
            "step_index": "display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; border-radius: 999px; background: #9a3412; color: #ffffff; font-size: 12px; line-height: 1; font-weight: 700; flex-shrink: 0;",
            "step_body": "flex: 1; min-width: 0;",
            "cards": "margin: 16px 0; display: flex; flex-direction: column; gap: 8px;",
            "card": "margin: 0; padding: 10px 12px; border: 1px solid #ead3c2; border-radius: 12px; background: #fffaf5; box-shadow: none;",
        },
        "headings": {
            "h1": "font-size: 30px; line-height: 1.35; color: #7c2d12; margin: 8px 0 20px;",
            "h2": "font-size: 24px; line-height: 1.45; color: #9a3412; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px dashed #e7c6ae;",
            "h3": "font-size: 20px; line-height: 1.5; color: #b45309; margin: 22px 0 10px;",
            "h4": "font-size: 18px; line-height: 1.5; color: #b45309; margin: 20px 0 8px;",
            "h5": "font-size: 16px; line-height: 1.5; color: #b45309; margin: 18px 0 8px;",
            "h6": "font-size: 15px; line-height: 1.5; color: #9a7b67; margin: 18px 0 8px;",
        },
    },
    "dark-blue": {
        "base_container": "max-width: 860px; margin: 0 auto; padding: 34px 14px; background: #eef4f8;",
        "article": "background: #ffffff; border: 1px solid #d8e3ee; border-radius: 18px; padding: 30px 24px; box-shadow: 0 12px 28px rgba(74, 124, 155, 0.10); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;",
        "paragraph": "color: #334155; font-size: 16px; line-height: 1.85; margin: 16px 0;",
        "list": "color: #334155; font-size: 16px; line-height: 1.85; padding-left: 1.4em; margin: 14px 0;",
        "blockquote": "margin: 18px 0; padding: 14px 16px; background: #edf4fb; border-left: 4px solid #4a7c9b; color: #35556c;",
        "pre": "background: #0f172a; color: #dbeafe; padding: 14px 16px; border-radius: 10px; overflow-x: auto; font-size: 14px; line-height: 1.6; margin: 18px 0;",
        "code": "background: #e8f1f8; color: #1d4ed8; padding: 2px 6px; border-radius: 6px; font-size: 0.92em;",
        "hr": "border: none; border-top: 1px solid #d8e3ee; margin: 28px 0;",
        "table": "width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 15px; line-height: 1.7;",
        "th": "border: 1px solid #d8e3ee; background: #f4f8fb; padding: 10px 12px; text-align: left;",
        "td": "border: 1px solid #d8e3ee; padding: 10px 12px; text-align: left; color: #334155;",
        "meta": "font-size: 13px; color: #64819a; line-height: 1.7; margin: 0 0 18px;",
        "image": "max-width: 100%; height: auto; border-radius: 12px; display: block; margin: 20px auto;",
        "modules": {
            "callout": {
                "base": "margin: 14px 0; padding: 12px 14px; border-radius: 12px; color: #35556c;",
                "tones": {
                    "info": "background: #edf4fb; border-left: 4px solid #4a7c9b;",
                    "warn": "background: #fef3e8; border-left: 4px solid #ea580c;",
                    "success": "background: #ecfdf5; border-left: 4px solid #10b981;",
                    "danger": "background: #fef2f2; border-left: 4px solid #ef4444;",
                },
            },
            "verdict": "margin: 16px 0; padding: 12px 14px; border-radius: 14px; background: #edf4fb; border: 1px solid #d8e3ee; border-left: 5px solid #1e3a5f; color: #1e3a5f; font-weight: 600;",
            "module_label": "display: inline-block; margin: 0 0 8px; padding: 2px 8px; border-radius: 999px; background: #1e3a5f; color: #ffffff; font-size: 12px; line-height: 1.5; font-weight: 700;",
            "callout_label": "display: inline-block; margin: 0 0 8px; font-size: 12px; line-height: 1.5; font-weight: 700; color: #1e3a5f;",
            "steps": "margin: 16px 0; display: flex; flex-direction: column; gap: 10px;",
            "step": "margin: 0; padding: 10px 12px; border: 1px solid #d8e3ee; border-radius: 10px; background: #f9fcff; display: flex; gap: 10px; align-items: flex-start;",
            "step_index": "display: inline-flex; align-items: center; justify-content: center; min-width: 24px; height: 24px; border-radius: 999px; background: #1e3a5f; color: #ffffff; font-size: 12px; line-height: 1; font-weight: 700; flex-shrink: 0;",
            "step_body": "flex: 1; min-width: 0;",
            "cards": "margin: 16px 0; display: flex; flex-direction: column; gap: 8px;",
            "card": "margin: 0; padding: 10px 12px; border: 1px solid #d8e3ee; border-radius: 12px; background: #f8fbfe; box-shadow: none;",
        },
        "headings": {
            "h1": "font-size: 30px; line-height: 1.35; color: #1e3a5f; margin: 8px 0 20px;",
            "h2": "font-size: 24px; line-height: 1.45; color: #2f5f7b; margin: 28px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #d8e3ee;",
            "h3": "font-size: 20px; line-height: 1.5; color: #2f5f7b; margin: 22px 0 10px;",
            "h4": "font-size: 18px; line-height: 1.5; color: #2f5f7b; margin: 20px 0 8px;",
            "h5": "font-size: 16px; line-height: 1.5; color: #2f5f7b; margin: 18px 0 8px;",
            "h6": "font-size: 15px; line-height: 1.5; color: #64819a; margin: 18px 0 8px;",
        },
    },
}


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    raw_meta = parts[0][4:]
    body = parts[1]
    try:
        data = yaml.safe_load(raw_meta) or {}
        if not isinstance(data, dict):
            data = {}
    except yaml.YAMLError:
        data = {}
    return data, body


def first_heading(markdown_text: str) -> str | None:
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def normalize_list_indentation(body_md: str) -> str:
    normalized_lines: list[str] = []
    list_stack: list[tuple[int, str]] = []
    list_pattern = re.compile(r"^(\s*)([-*+] |\d+\. )(.*)$")

    for line in body_md.splitlines():
        match = list_pattern.match(line)
        if not match:
            normalized_lines.append(line)
            continue

        raw_indent = len(match.group(1).replace("\t", "    "))
        marker = match.group(2)
        content = match.group(3)
        list_type = "ol" if re.match(r"\d+\. ", marker) else "ul"

        while list_stack and raw_indent < list_stack[-1][0]:
            list_stack.pop()

        if not list_stack:
            indent_level = 0
            list_stack = [(raw_indent, list_type)]
        elif raw_indent > list_stack[-1][0]:
            indent_level = len(list_stack)
            list_stack.append((raw_indent, list_type))
        else:
            current_level = next((idx for idx in range(len(list_stack) - 1, -1, -1) if list_stack[idx][0] == raw_indent), None)
            if current_level is None:
                current_level = len(list_stack) - 1
            list_stack = list_stack[: current_level + 1]
            list_stack[-1] = (raw_indent, list_type)
            indent_level = current_level

        normalized_lines.append(f"{'    ' * indent_level}{marker}{content}")

    return "\n".join(normalized_lines)


def render_wechat_safe_lists(body_md: str, theme: dict[str, Any]) -> str:
    list_pattern = re.compile(r"^(\s*)([-*+] |\d+\. )(.*)$")
    lines = body_md.splitlines()
    index = 0
    rendered: list[str] = []
    ordered_counters: dict[int, int] = defaultdict(int)

    while index < len(lines):
        match = list_pattern.match(lines[index])
        if not match:
            rendered.append(lines[index])
            index += 1
            continue

        raw_indent = len(match.group(1).replace("\t", "    "))
        marker = match.group(2)
        content = match.group(3).strip()
        level = raw_indent // 4
        is_ordered = bool(re.match(r"\d+\. ", marker))

        if level == 0:
            ordered_counters.clear()
        if is_ordered:
            ordered_counters[level] += 1
            for key in list(ordered_counters.keys()):
                if key > level:
                    del ordered_counters[key]
            bullet = f"{ordered_counters[level]}."
        else:
            ordered_counters[level] = 0
            for key in list(ordered_counters.keys()):
                if key > level:
                    del ordered_counters[key]
            bullet = "•"

        indent_px = 18 * level
        rendered.append(
            f'<p style="{theme["paragraph"]}; margin-left: {indent_px}px;">'
            f'<span style="display: inline-block; min-width: 1.6em;">{bullet}</span>'
            f'<span>{content}</span>'
            f'</p>'
        )
        index += 1

    return "\n".join(rendered)


def render_module_labels(body_md: str) -> str:
    body_md = re.sub(
        r'(?s)<div class="verdict">\s*<p>(.*?)</p>\s*</div>',
        r'<div class="verdict"><div class="module-label">核心结论</div><p>\1</p></div>',
        body_md,
    )
    body_md = re.sub(
        r'(?s)<div class="callout" data-tone="(info|warn|success|danger)">\s*<p>(.*?)</p>\s*</div>',
        lambda m: (
            f'<div class="callout" data-tone="{m.group(1)}">'
            f'<div class="callout-label">{CALL_OUT_LABELS[m.group(1)]}</div>'
            f'<p>{m.group(2)}</p></div>'
        ),
        body_md,
    )
    body_md = re.sub(
        r'(?s)<div class="step">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
        lambda m: (
            '<div class="step">'
            f'<div class="step-index">{extract_step_index(m.group(1))}</div>'
            '<div class="step-body">'
            f'<h3>{m.group(1)}</h3>'
            f'<p>{m.group(2)}</p>'
            '</div></div>'
        ),
        body_md,
    )
    return body_md


def extract_step_index(title_text: str) -> str:
    match = re.match(r"第([一二三四五六七八九十0-9]+)层", title_text)
    if match:
        return match.group(1)
    return "•"


def normalize_markdown(body_md: str, theme: dict[str, Any]) -> str:
    body_md = normalize_list_indentation(body_md)
    body_md = re.sub(r"~~(.*?)~~", r"<del>\1</del>", body_md, flags=re.DOTALL)
    body_md = re.sub(r"(?m)^- \[( |x|X)\] (.+)$", lambda m: build_task_item(bool(m.group(1).strip()), m.group(2)), body_md)
    body_md = render_module_labels(body_md)
    body_md = re.sub(r"(?m)^(>\s*)([-*+] |\d+\. )(.*)$", lambda m: f'{m.group(1)}{m.group(3)}', body_md)
    body_md = render_wechat_safe_lists(body_md, theme)
    return body_md


def build_task_item(checked: bool, text: str) -> str:
    checked_attr = ' checked="checked"' if checked else ""
    return (
        f'- <input type="checkbox" disabled="disabled"{checked_attr} /> '
        f'<span>{text}</span>'
    )


def append_style(existing: str | None, style: str) -> str:
    if not existing:
        return style
    existing = existing.strip()
    if existing.endswith(";"):
        return f"{existing} {style}"
    return f"{existing}; {style}"


class StyleHTMLParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    MODULE_CLASSES = {"callout", "verdict", "steps", "step", "cards", "card", "step-body"}

    def __init__(self, theme: dict[str, Any]) -> None:
        super().__init__(convert_charrefs=False)
        self.theme = theme
        self.parts: list[str] = []
        self.module_stack: list[set[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self._render_start_tag(tag, attrs, closed=False))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self._render_start_tag(tag, attrs, closed=True))

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.module_stack:
            self.module_stack.pop()
        if tag not in self.VOID_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def _render_start_tag(self, tag: str, attrs: list[tuple[str, str | None]], closed: bool) -> str:
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        if tag == "div":
            self.module_stack.append(classes & self.MODULE_CLASSES)
        style = self._style_for_tag(tag, attr_map)
        if style:
            attr_map["style"] = append_style(attr_map.get("style"), style)
        rendered_attrs = []
        for key, value in attr_map.items():
            if value is None:
                rendered_attrs.append(key)
            else:
                rendered_attrs.append(f'{key}="{html.escape(value, quote=True)}"')
        suffix = " /" if closed and tag in self.VOID_TAGS else ""
        attr_text = f" {' '.join(rendered_attrs)}" if rendered_attrs else ""
        return f"<{tag}{attr_text}{suffix}>"

    def _style_for_tag(self, tag: str, attrs: dict[str, str | None]) -> str | None:
        classes = set((attrs.get("class") or "").split())
        if tag in self.theme["headings"]:
            heading_style = self.theme["headings"][tag]
            if any(self.module_stack) and tag == "h3":
                return append_style(heading_style, "margin: 0 0 6px;")
            return heading_style
        if tag == "p":
            if any(self.module_stack):
                return append_style(self.theme["paragraph"], "margin: 0;")
            return self.theme["paragraph"]
        if tag in {"ul", "ol"}:
            return self.theme["list"]
        if tag == "blockquote":
            return self.theme["blockquote"]
        if tag == "pre":
            return self.theme["pre"]
        if tag == "code" and not (attrs.get("class") or "").startswith("language-"):
            return self.theme["code"]
        if tag == "hr":
            return self.theme["hr"]
        if tag == "table":
            return self.theme["table"]
        if tag == "th":
            return self.theme["th"]
        if tag == "td":
            return self.theme["td"]
        if tag == "img":
            return self.theme["image"]
        if tag == "div" and "callout" in classes:
            tone = attrs.get("data-tone") or "info"
            tone_styles = self.theme["modules"]["callout"]["tones"]
            return append_style(self.theme["modules"]["callout"]["base"], tone_styles.get(tone, tone_styles["info"]))
        if tag == "div" and "verdict" in classes:
            return self.theme["modules"]["verdict"]
        if tag == "div" and "module-label" in classes:
            return self.theme["modules"]["module_label"]
        if tag == "div" and "callout-label" in classes:
            return self.theme["modules"]["callout_label"]
        if tag == "div" and "steps" in classes:
            return self.theme["modules"]["steps"]
        if tag == "div" and "step" in classes:
            return self.theme["modules"]["step"]
        if tag == "div" and "step-index" in classes:
            return self.theme["modules"]["step_index"]
        if tag == "div" and "step-body" in classes:
            return self.theme["modules"]["step_body"]
        if tag == "div" and "cards" in classes:
            return self.theme["modules"]["cards"]
        if tag == "div" and "card" in classes:
            return self.theme["modules"]["card"]
        elif tag == "li":
            return "margin: 6px 0;"
        if tag == "input" and attrs.get("type") == "checkbox":
            return "margin-right: 8px; transform: translateY(1px);"
        if tag == "sup":
            return "font-size: 0.75em; vertical-align: super; line-height: 1;"
        if tag == "a" and (attrs.get("class") or "") in {"footnote-ref", "footnote-backref"}:
            return "color: #2563eb; text-decoration: none;"
        if tag == "dl":
            return "margin: 16px 0; color: #2f2f2f;"
        if tag == "dt":
            return "font-weight: 600; margin-top: 12px;"
        if tag == "dd":
            return "margin: 6px 0 12px 1.2em; color: #4b5563;"
        if tag == "div" and (attrs.get("class") or "") == "footnote":
            return "margin-top: 24px; font-size: 14px; color: #4b5563;"
        return None


def wrap_list_item_text(html_text: str) -> str:
    html_text = re.sub(
        r'(<li[^>]*>)([^<\n][^<]*?)(?=(<ul|<ol|</li>))',
        lambda m: f'{m.group(1)}<span style="display: inline;">{m.group(2).strip()}</span>',
        html_text,
    )
    return html_text


def style_element_tree(html_text: str, theme: dict[str, Any]) -> str:
    parser = StyleHTMLParser(theme)
    parser.feed(html_text)
    parser.close()
    return wrap_list_item_text("".join(parser.parts))


def build_html(title: str, author: str | None, digest: str | None, body_html: str, theme: dict[str, Any]) -> str:
    meta_html = []
    if author:
        meta_html.append(f'<p style="{theme["meta"]}; margin-right: 12px;">作者：{html.escape(author)}</p>')
    if digest:
        meta_html.append(f'<p style="{theme["meta"]}">摘要：{html.escape(digest)}</p>')
    meta_block = "".join(meta_html)

    return (
        f'<section style="{theme["article"]}">'
        f'<h1 style="{theme["headings"]["h1"]}">{html.escape(title)}</h1>'
        f'{meta_block}'
        f'{body_html}'
        f'</section>'
    )


def convert_markdown(input_path: pathlib.Path, output_path: pathlib.Path, theme_name: str) -> None:
    theme = THEMES[theme_name]
    raw_text = input_path.read_text(encoding="utf-8")
    metadata, body_md = split_frontmatter(raw_text)
    title = str(metadata.get("title") or first_heading(body_md) or input_path.stem)
    author = metadata.get("author")
    digest = metadata.get("digest") or metadata.get("summary") or metadata.get("description")
    # Auto-generate digest from first paragraph if missing
    if not digest:
        for line in body_md.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("---"):
                # Strip markdown formatting
                clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)  # links
                clean = re.sub(r'[*_~`]', '', clean)  # bold/italic/code
                digest = clean[:120]
                break

    # Avoid rendering the same H1 twice — works with or without frontmatter.
    first_h1 = first_heading(body_md)
    if first_h1 and title and first_h1.strip() == title.strip():
        lines = body_md.splitlines()
        removed = False
        kept_lines = []
        for line in lines:
            if not removed and line.startswith("# "):
                removed = True
                continue
            kept_lines.append(line)
        body_md = "\n".join(kept_lines).lstrip("\n")

    body_md = normalize_markdown(body_md, theme)
    body_html = markdown.markdown(
        body_md,
        extensions=["extra", "sane_lists", "tables", "fenced_code", "md_in_html"],
        output_format="html5",
    )
    body_html = style_element_tree(body_html, theme)
    final_html = build_html(title, str(author) if author else None, str(digest) if digest else None, body_html, theme)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown into WeChat-friendly HTML locally.")
    parser.add_argument("input", help="Input Markdown file")
    parser.add_argument("-o", "--output", help="Output HTML file")
    parser.add_argument("--theme", choices=sorted(THEMES.keys()), default="minimal", help="Local HTML theme preset")
    args = parser.parse_args()

    input_path = pathlib.Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = pathlib.Path(args.output) if args.output else input_path.with_suffix(".wechat.html")
    convert_markdown(input_path, output_path, args.theme)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
