#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "tmp" / "md-common-format-showcase.md"
OUTPUT = ROOT / "tmp" / "md-common-format-showcase.generated.html"


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


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    run_converter()
    html = OUTPUT.read_text(encoding="utf-8")

    assert_true('<ul ' not in html, "wechat-safe output should not use native unordered list tags")
    assert_true('<ol ' not in html, "wechat-safe output should not use native ordered list tags")
    assert_true('>•</span><span>一级项目 A</span>' in html, "unordered list should render as bullet plus inline text")
    assert_true('>•</span><span>二级项目 A-1</span>' in html, "nested unordered list should render as bullet plus inline text")
    assert_true('>1.</span><span>第一步</span>' in html, "ordered list should render as number plus inline text")
    assert_true('>1.</span><span>第一步的子步骤 1</span>' in html, "nested ordered list should render as number plus inline text")
    assert_true('margin-left: 18px' in html, "nested list indentation should be preserved")
    assert_true('type="checkbox"' in html, "task list checkboxes missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
