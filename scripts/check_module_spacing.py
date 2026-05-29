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
    assert_true('class="cards"' in html, "cards block missing")
    assert_true('class="steps"' in html, "steps block missing")
    assert_true('class="callout"' in html, "callout block missing")
    assert_true('margin: 0;' in html, "module inner paragraphs/headings should be compacted to margin 0")
    assert_true('gap: 10px' in html, "cards/steps wrapper should use compact vertical gap")
    assert_true('padding: 12px 14px' in html, "module cards should use tighter padding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
