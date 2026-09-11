from __future__ import annotations

import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

SHORTCUT_PATH = (
    Path.home() / ".config/cosmic/com.system76.CosmicSettings.Shortcuts/v1/custom"
)


def _entries(body: str) -> list[str]:
    entries: list[str] = []
    start = 0
    parens = brackets = 0
    quoted = escaped = False
    for index, char in enumerate(body):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
        elif char == "[":
            brackets += 1
        elif char == "]":
            brackets -= 1
        elif char == "," and parens == brackets == 0:
            entry = body[start:index].strip()
            if entry:
                entries.append(entry)
            start = index + 1
    tail = body[start:].strip()
    if tail:
        entries.append(tail)
    return entries


def install_shortcut(executable: str, key: str = "Insert") -> tuple[Path, Path | None]:
    path = SHORTCUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text(encoding="utf-8") if path.exists() else "{}\n"
    stripped = original.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        raise RuntimeError(f"Unexpected COSMIC shortcut format in {path}")
    current = _entries(stripped[1:-1])
    current = [entry for entry in current if "VoxType" not in entry]
    key_pattern = re.compile(rf'key:\s*"{re.escape(key)}"\s*[,)]')
    if any(key_pattern.search(entry) for entry in current):
        raise RuntimeError(
            f"{key} already has a COSMIC shortcut; choose another key in COSMIC Settings"
        )
    new_entry = f'''(
        modifiers: [],
        key: "{key}",
        description: Some("VoxType — Start or stop dictation"),
    ): Spawn("{executable}")'''
    current.append(new_entry)
    rendered = (
        "{\n    "
        + ",\n    ".join(entry.replace("\n", "\n    ") for entry in current)
        + ",\n}\n"
    )
    backup = None
    if path.exists():
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        backup = path.with_name(f"custom.voxtype-backup-{stamp}")
        shutil.copy2(path, backup)
    path.write_text(rendered, encoding="utf-8")
    return path, backup
