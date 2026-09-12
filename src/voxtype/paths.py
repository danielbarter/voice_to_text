from __future__ import annotations

import os
from pathlib import Path


def _xdg_dir(variable: str, fallback: str) -> Path:
    return Path(os.environ.get(variable, str(Path.home() / fallback))).expanduser()


def config_path() -> Path:
    return _xdg_dir("XDG_CONFIG_HOME", ".config") / "voxtype" / "config.toml"


def cache_dir() -> Path:
    return _xdg_dir("XDG_CACHE_HOME", ".cache") / "voxtype"


def data_dir() -> Path:
    return _xdg_dir("XDG_DATA_HOME", ".local/share") / "voxtype"


def runtime_dir() -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/voxtype-{os.getuid()}"))
    return base / "voxtype"
