#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "tmp" / "md2wechat-safe-modules.md"
OUTPUT = ROOT / "tmp" / "md2wechat-safe-modules.generated.html"


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

    assert_true('class="callout"' in html, "callout block missing")
    assert_true('data-tone="info"' in html, "info callout tone missing")
    assert_true('data-tone="warn"' in html, "warn callout tone missing")
    assert_true('class="verdict"' in html, "verdict block missing")
    assert_true('class="steps"' in html, "steps wrapper missing")
    assert_true('class="step"' in html, "step block missing")
    assert_true('class="cards"' in html, "cards wrapper missing")
    assert_true('class="card"' in html, "card block missing")
    assert_true('border-left: 4px solid #3b82f6' in html, "callout should have styled left border")
    assert_true('结论：本地 fallback 版已经具备稳定发稿能力。' in html, "verdict content missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
