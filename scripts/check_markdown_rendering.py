#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "tmp" / "md-format-regression.md"
OUTPUT = ROOT / "tmp" / "md-format-regression.generated.html"


def run_converter() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "local_md_to_wechat.py"),
            str(INPUT),
            "-o",
            str(OUTPUT),
            "--theme",
            "minimal",
        ],
        check=True,
    )


def assert_contains(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise AssertionError(message)


def main() -> int:
    run_converter()
    html = OUTPUT.read_text(encoding="utf-8")

    assert_contains(
        html,
        '<li style="margin: 6px 0;">第二项<ul',
        "nested unordered list should stay nested inside the parent list item",
    )
    assert_contains(
        html,
        '<li style="margin: 6px 0;">第二步<ol',
        "nested ordered list should stay nested inside the parent list item",
    )
    assert_contains(
        html,
        '<li style="margin: 6px 0;">有序父项<ul',
        "mixed list should render child unordered items as a nested list",
    )
    assert_contains(
        html,
        'type="checkbox"',
        "task list items should render as checkbox inputs",
    )
    assert_contains(
        html,
        '<del>删除线</del>',
        "strikethrough syntax should render as <del>",
    )
    assert_contains(
        html,
        '<div class="footnote"',
        "footnotes should render with a footnote block",
    )
    assert_contains(
        html,
        '<dl ',
        "definition lists should render as <dl>",
    )
    assert_contains(
        html,
        '==高亮文本==',
        "unsupported highlight syntax should remain literal instead of breaking output",
    )
    assert_contains(
        html,
        'H~2~O 和 2^10^',
        "unsupported subscript and superscript syntax should remain literal",
    )
    assert_contains(
        html,
        '<div class="callout"',
        "inline HTML blocks should survive conversion",
    )


if __name__ == "__main__":
    raise SystemExit(main())
