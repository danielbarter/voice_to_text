from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = """# VoxType settings. Restart the service after editing.

[transcription]
# base.en is a strong speed/accuracy balance for this 4-core Intel laptop.
# Try small.en for greater accuracy, or tiny.en for minimum latency.
engine = "auto"
model = "base.en"
language = "en"
compute_type = "int8"
beam_size = 5
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


def _xdg_dir(variable: str, fallback: str) -> Path:
    return Path(os.environ.get(variable, str(Path.home() / fallback))).expanduser()


def config_path() -> Path:
    return _xdg_dir("XDG_CONFIG_HOME", ".config") / "voxtype" / "config.toml"


def load_config_path() -> Path:
    user_path = config_path()
    if user_path.exists():
        return user_path
    for directory in os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg").split(":"):
        candidate = Path(directory) / "voxtype" / "config.toml"
        if candidate.exists():
            return candidate
    return ensure_config()


def cache_dir() -> Path:
    return _xdg_dir("XDG_CACHE_HOME", ".cache") / "voxtype"


def data_dir() -> Path:
    return _xdg_dir("XDG_DATA_HOME", ".local/share") / "voxtype"


def runtime_dir() -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/voxtype-{os.getuid()}"))
    return base / "voxtype"


@dataclass(frozen=True)
class Config:
    engine: str = "auto"
    model: str = "base.en"
    language: str | None = "en"
    compute_type: str = "int8"
    beam_size: int = 5
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
            engine=os.environ.get(
                "VOXTYPE_ENGINE", str(transcription.get("engine", "auto"))
            ),
            model=os.environ.get(
                "VOXTYPE_MODEL", str(transcription.get("model", "base.en"))
            ),
            language=language,
            compute_type=str(transcription.get("compute_type", "int8")),
            beam_size=max(1, int(transcription.get("beam_size", 5))),
            hotwords=str(transcription.get("hotwords", "")),
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
