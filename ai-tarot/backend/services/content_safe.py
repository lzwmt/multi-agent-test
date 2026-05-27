"""
Content Safety - Input/output filtering for sensitive topics.

Checks user input for crisis-related keywords (suicide, self-harm, etc.)
and validates AI-generated output for safety.
"""

from __future__ import annotations

import re
from typing import NamedTuple


class SafetyResult(NamedTuple):
    """Result of a safety check."""

    is_safe: bool
    reason: str


# ---------------------------------------------------------------------------
# Sensitive topic keyword groups
# ---------------------------------------------------------------------------
# Each group is (label, patterns) where patterns is a list of regex patterns
# (case-insensitive).  The check matches any of these.

_INPUT_KEYWORD_GROUPS: list[tuple[str, list[str]]] = [
    (
        "自杀/轻生",
        [
            r"自杀|自\s*杀",
            r"轻\s*生",
            r"不想活|活不下[去了]",
            r"结束生命",
            r"割腕|上吊|跳楼|跳[河湖江海]",
            r"服药.*自杀|吞药",
            r"去死|想死|找死",
            r"一了百了",
        ],
    ),
    (
        "自残/自伤",
        [
            r"自残|自\s*伤",
            r"伤害自己",
            r"割自己",
            r"弄伤自己",
        ],
    ),
    (
        "暴力/伤害他人",
        [
            r"杀人|杀害|谋杀",
            r"伤害他人",
            r"报复.*杀",
            r"砍人|捅人|打人.*死",
        ],
    ),
    (
        "药物滥用",
        [
            r"吸毒|贩毒|制毒",
            r"注射.*毒品",
            r"过量用药",
        ],
    ),
    (
        "严重精神危机",
        [
            r"精神崩溃",
            r"世界末日",
            r"绝望.*无路",
            r"活.*没意思",
            r"人生.*没有意义",
            r"所有人.*都.*讨厌",
        ],
    ),
]

# Patterns that indicate the AI output itself may be unsafe.
_OUTPUT_KEYWORD_GROUPS: list[tuple[str, list[str]]] = [
    (
        "鼓励自残/自杀",
        [
            r"自杀.*方法|怎么.*死",
            r"割.*[腕脖]|用.*刀.*划",
            r"推荐.*药.*量|吃.*片.*",
            r"鼓励.*自杀|支持.*轻生",
            r"死亡.*是.*解脱|死.*好了",
        ],
    ),
    (
        "泄露个人隐私建议",
        [
            r"分享.*身份证|告诉.*密码",
            r"给.*转账|汇款.*给",
        ],
    ),
    (
        "提供危险操作指导",
        [
            r"如何.*制作.*炸|制造.*武器",
            r"如何.*伤害.*自己",
        ],
    ),
]


class ContentSafety:
    """Lightweight content safety checker for tarot applications."""

    def __init__(self) -> None:
        # Pre-compile regex patterns for performance
        self._input_rules = self._compile_groups(_INPUT_KEYWORD_GROUPS)
        self._output_rules = self._compile_groups(_OUTPUT_KEYWORD_GROUPS)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compile_groups(
        groups: list[tuple[str, list[str]]],
    ) -> list[tuple[str, re.Pattern[str]]]:
        compiled: list[tuple[str, re.Pattern[str]]] = []
        for label, patterns in groups:
            combined = "|".join(f"({p})" for p in patterns)
            compiled.append((label, re.compile(combined, re.IGNORECASE)))
        return compiled

    def _check(
        self,
        text: str,
        rules: list[tuple[str, re.Pattern[str]]],
    ) -> SafetyResult:
        """Run all rule groups against *text*.

        Returns the first violation found, or (True, "") if safe.
        """
        if not text or not text.strip():
            return SafetyResult(is_safe=True, reason="")

        for label, pattern in rules:
            match = pattern.search(text)
            if match:
                return SafetyResult(
                    is_safe=False,
                    reason=f"检测到敏感内容（{label}）：「{match.group()}」",
                )

        return SafetyResult(is_safe=True, reason="")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_input(self, text: str) -> SafetyResult:
        """Check user input for sensitive / crisis-related content.

        Args:
            text: The raw user input string.

        Returns:
            A ``SafetyResult``.  ``is_safe`` is False when a sensitive
            topic is detected and ``reason`` explains which group was matched.
        """
        return self._check(text, self._input_rules)

    def check_output(self, text: str) -> SafetyResult:
        """Check AI-generated output for potentially harmful content.

        Args:
            text: The AI response string.

        Returns:
            A ``SafetyResult``.  ``is_safe`` is False when potentially
            harmful output is detected.
        """
        return self._check(text, self._output_rules)
