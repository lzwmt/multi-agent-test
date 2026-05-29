#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "tmp" / "sample_wechat_article_modules.md"
OUTPUT = ROOT / "tmp" / "sample_wechat_article_modules.generated.html"


def run_converter() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "local_md_to_wechat.py"),
            str(INPUT),
            "-o",
            str(OUTPUT),
            "--theme",
            "warm",
        ],
        check=True,
    )


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    run_converter()
    html = OUTPUT.read_text(encoding="utf-8")

    assert_true('class="verdict"' in html, "verdict block missing")
    assert_true('核心结论' in html, "verdict should render a title label")
    assert_true('class="callout-label"' in html, "callout label missing")
    assert_true('提示' in html, "info callout should show label")
    assert_true('建议' in html, "success callout should show label")
    assert_true('注意' in html, "warn callout should show label")
    assert_true('class="step-index"' in html, "step index missing")
    assert_true('min-width: 24px' in html, "step index should render compact number chip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
