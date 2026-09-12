from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .paths import config_path

DEFAULT_CONFIG = """# VoxType settings. Restart the service after editing.

[transcription]
# base.en is a strong speed/accuracy balance for this 4-core Intel laptop.
model = "base.en"
language = "en"
# Optional decoder hints for unusual names, separated by commas. No words are
# built in.
hotwords = ""

[audio]
# Leave blank to follow the microphone selected in COSMIC Settings.
source = ""
max_seconds = 120

[typing]
trailing_space = true
voice_commands = true
key_delay_ms = 0

[feedback]
notifications = false
sounds = true
"""


def load_config_path() -> Path:
    user_path = config_path()
    if user_path.exists():
        return user_path
    for directory in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":"):
        candidate = Path(directory) / "voxtype" / "config.toml"
        if candidate.exists():
            return candidate
    return ensure_config()


@dataclass(frozen=True)
class Config:
    model: str = "base.en"
    language: str | None = "en"
    hotwords: str = ""
    audio_source: str = ""
    max_seconds: int = 120
    trailing_space: bool = True
    voice_commands: bool = True
    key_delay_ms: int = 0
    notifications: bool = False
    sounds: bool = True

    @classmethod
    def load(cls) -> Config:
        with load_config_path().open("rb") as handle:
            raw = tomllib.load(handle)
        transcription = raw.get("transcription", {})
        audio = raw.get("audio", {})
        typing = raw.get("typing", {})
        feedback = raw.get("feedback", {})
        language = transcription.get("language", "en")
        if language in ("", "auto", None):
            language = None
        return cls(
            model=os.environ.get(
                "VOXTYPE_MODEL", str(transcription.get("model", "base.en"))
            ),
            language=language,
            hotwords=os.environ.get(
                "VOXTYPE_HOTWORDS", str(transcription.get("hotwords", ""))
            ),
            audio_source=str(audio.get("source", "")),
            max_seconds=max(1, int(audio.get("max_seconds", 120))),
            trailing_space=bool(typing.get("trailing_space", True)),
            voice_commands=bool(typing.get("voice_commands", True)),
            key_delay_ms=max(0, int(typing.get("key_delay_ms", 0))),
            notifications=bool(feedback.get("notifications", False)),
            sounds=bool(feedback.get("sounds", True)),
        )


def ensure_config() -> Path:
    path = config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return path
