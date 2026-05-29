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

    assert_true('class="cards"' in html, "cards block missing")
    assert_true('class="card"' in html, "card block missing")
    assert_true('gap: 8px' in html, "cards wrapper should use tighter vertical gap")
    assert_true('padding: 10px 12px' in html, "cards should use tighter padding")
    assert_true('border-radius: 12px' in html, "cards should use slightly tighter corner radius")
    assert_true('box-shadow: none' in html, "cards should drop heavy shadow for summary-card feel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
