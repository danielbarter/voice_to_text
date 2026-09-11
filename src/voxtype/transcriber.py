from __future__ import annotations

import logging
import os
from pathlib import Path

from .config import Config, cache_dir

LOG = logging.getLogger("voxtype.transcriber")


class FasterWhisperTranscriber:
    name = "faster-whisper"

    def __init__(self, config: Config, *, allow_download: bool) -> None:
        from faster_whisper import WhisperModel

        model_root = cache_dir() / "models"
        model_root.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.model = WhisperModel(
            config.model,
            device="cpu",
            compute_type=config.compute_type,
            cpu_threads=max(1, min(6, os.cpu_count() or 4)),
            num_workers=1,
            download_root=str(model_root),
            local_files_only=not allow_download,
        )

    def transcribe(self, path: Path) -> tuple[str, str | None]:
        segments, info = self.model.transcribe(
            str(path),
            language=self.config.language,
            beam_size=self.config.beam_size,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
            condition_on_previous_text=False,
            without_timestamps=True,
            hotwords=self.config.hotwords or None,
        )
        text = " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        )
        return text, getattr(info, "language", self.config.language)


class PyWhisperCppTranscriber:
    name = "pywhispercpp"

    def __init__(self, config: Config, *, allow_download: bool) -> None:
        from pywhispercpp.model import Model

        model_root = cache_dir() / "models-whispercpp"
        model_root.mkdir(parents=True, exist_ok=True)
        model = config.model
        configured_path = Path(model).expanduser()
        cached_path = model_root / f"ggml-{model}.bin"
        if configured_path.is_file():
            model = str(configured_path)
        elif cached_path.is_file():
            model = str(cached_path)
        elif not allow_download:
            raise RuntimeError(
                f"Model {config.model} is not cached; run: voxtype prepare"
            )

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
            model,
            models_dir=str(model_root),
            redirect_whispercpp_logs_to=None,
            **parameters,
        )

    def transcribe(self, path: Path) -> tuple[str, str | None]:
        segments = self.model.transcribe(str(path))
        text = " ".join(
            segment.text.strip() for segment in segments if segment.text.strip()
        )
        return text, self.config.language


def load_transcriber(config: Config, *, allow_download: bool):
    engines = (
        ("faster-whisper", FasterWhisperTranscriber),
        ("pywhispercpp", PyWhisperCppTranscriber),
    )
    requested = config.engine.strip().lower()
    errors = []
    for name, implementation in engines:
        if requested not in {"", "auto", name}:
            continue
        try:
            transcriber = implementation(config, allow_download=allow_download)
            LOG.info("Using %s speech engine", name)
            return transcriber
        except ImportError as exc:
            errors.append(f"{name}: {exc}")
            if requested == name:
                break
    if requested not in {"", "auto", *(name for name, _ in engines)}:
        raise RuntimeError(f"Unknown speech engine: {config.engine}")
    raise RuntimeError(
        "No supported speech engine is installed (" + "; ".join(errors) + ")"
    )
