from __future__ import annotations

import os
from pathlib import Path

from .config import Config


def _resolve_model(model: str) -> Path:
    configured_path = Path(model).expanduser()
    if configured_path.is_file():
        return configured_path
    raise RuntimeError(
        f"GGML model file not found: {configured_path}; install the VoxType model package"
    )


class Transcriber:
    name = "whisper.cpp"

    def __init__(self, config: Config) -> None:
        from pywhispercpp.model import Model

        model = _resolve_model(config.model)

        parameters = {
            "n_threads": max(1, min(6, os.cpu_count() or 4)),
            "language": config.language or "",
            "no_context": True,
            "print_progress": False,
            "print_realtime": False,
            "print_timestamps": False,
        }
        # This is deliberately empty unless the user configured it.
        if config.hotwords:
            parameters["initial_prompt"] = config.hotwords
        self.config = config
        self.model = Model(
            str(model),
            redirect_whispercpp_logs_to=None,
            **parameters,
        )

    def transcribe(self, path: Path) -> tuple[str, str | None]:
        segments = self.model.transcribe(str(path))
        text = " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        )
        return text, self.config.language
