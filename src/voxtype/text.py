from __future__ import annotations

import re

VOICE_COMMANDS = (
    (r"\bnew\s+paragraph\b", "\n\n"),
    (r"\bnew\s+line\b", "\n"),
    (r"\bopen\s+parenthes(?:is|es)\b", "("),
    (r"\bclose\s+parenthes(?:is|es)\b", ")"),
    (r"\bopen\s+quote\b", "\u201c"),
    (r"\bclose\s+quote\b", "\u201d"),
)


def polish(text: str, voice_commands: bool = True, trailing_space: bool = True) -> str:
    result = re.sub(r"\s+", " ", text).strip()
    if voice_commands:
        for pattern, replacement in VOICE_COMMANDS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        result = re.sub(r" *\n *", "\n", result)
    if result and trailing_space and not result.endswith(("\n", " ")):
        result += " "
    return result
