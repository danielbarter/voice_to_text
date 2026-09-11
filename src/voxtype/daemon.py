from __future__ import annotations

import json
import logging
import math
import os
import signal
import socket
import subprocess
import threading
import time
import wave
from array import array
from pathlib import Path

from .config import Config, cache_dir, runtime_dir
from .feedback import Feedback
from .history import append
from .indicator import StatusIndicator
from .inject import InjectionError, inject
from .text import polish
from .transcriber import load_transcriber

LOG = logging.getLogger("voxtype")


class VoxTypeDaemon:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.feedback = Feedback(config.notifications, config.sounds)
        self.state = "loading"
        self.state_lock = threading.Lock()
        self.recorder: subprocess.Popen | None = None
        self.started_at = 0.0
        self.audio_path: Path | None = None
        self.model = None
        self.shutdown_event = threading.Event()
        self.indicator = StatusIndicator(self.toggle)

    def _set_state(self, state: str) -> None:
        with self.state_lock:
            self.state = state
        self.indicator.set_state(state)

    def load_model(self) -> None:
        try:
            LOG.info("Loading Whisper model %s", self.config.model)
            model = load_transcriber(self.config, allow_download=False)
            with self.state_lock:
                self.model = model
            self._set_state("idle")
            LOG.info("VoxType is ready")
        except Exception:
            LOG.exception("Could not load model")
            self._set_state("error")
            self.feedback.error(
                f"Could not load {self.config.model}; run: voxtype prepare"
            )

    def status(self) -> dict:
        with self.state_lock:
            return {"state": self.state, "model": self.config.model}

    def toggle(self) -> dict:
        with self.state_lock:
            state = self.state
        if state == "idle":
            self.start_recording()
        elif state == "recording":
            self.stop_recording()
        elif state == "loading":
            self.feedback.notify(
                "VoxType is warming up",
                f"Loading {self.config.model} for the first time…",
                "content-loading-symbolic",
            )
        elif state == "transcribing":
            self.feedback.notify(
                "VoxType is still transcribing",
                "Your dictation will appear in a moment",
                "content-loading-symbolic",
            )
        else:
            self.feedback.error(
                "The local model failed to load; check: journalctl --user -u voxtype"
            )
        return self.status()

    def start_recording(self) -> None:
        cache_dir().mkdir(parents=True, exist_ok=True)
        path = cache_dir() / "recording.wav"
        args = ["pw-record", "--rate", "16000", "--channels", "1", "--format", "s16"]
        if self.config.audio_source:
            args.extend(["--target", self.config.audio_source])
        args.append(str(path))
        try:
            recorder = subprocess.Popen(
                args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except OSError as exc:
            self.feedback.error(f"Could not open the microphone: {exc}")
            return
        with self.state_lock:
            self.recorder = recorder
            self.audio_path = path
            self.started_at = time.monotonic()
        self._set_state("recording")
        self.feedback.recording()
        threading.Thread(target=self._recording_watchdog, daemon=True).start()

    def _recording_watchdog(self) -> None:
        deadline = self.started_at + self.config.max_seconds
        while not self.shutdown_event.wait(0.25):
            with self.state_lock:
                if self.state != "recording":
                    return
            if time.monotonic() >= deadline:
                self.stop_recording()
                return

    def stop_recording(self) -> None:
        with self.state_lock:
            if self.state != "recording" or self.recorder is None:
                return
            recorder = self.recorder
            path = self.audio_path
            duration = time.monotonic() - self.started_at
            self.recorder = None
        self._set_state("transcribing")
        recorder.send_signal(signal.SIGINT)
        try:
            recorder.wait(timeout=3)
        except subprocess.TimeoutExpired:
            recorder.terminate()
            recorder.wait(timeout=2)
        self.feedback.processing()
        threading.Thread(
            target=self._transcribe, args=(path, duration), daemon=True
        ).start()

    @staticmethod
    def _audio_rms(path: Path) -> float:
        try:
            with wave.open(str(path), "rb") as wav:
                samples = array("h", wav.readframes(wav.getnframes()))
            if not samples:
                return 0.0
            return math.sqrt(sum(value * value for value in samples) / len(samples))
        except (OSError, wave.Error):
            return 0.0

    def _transcribe(self, path: Path | None, duration: float) -> None:
        try:
            if path is None or not path.exists() or duration < 0.35:
                raise RuntimeError("That was too quick—hold the key a little longer")
            if self._audio_rms(path) < 45:
                raise RuntimeError(
                    "I couldn't hear speech; check the selected microphone"
                )
            raw, language = self.model.transcribe(path)
            text = polish(raw, self.config.voice_commands, self.config.trailing_space)
            if not text:
                raise RuntimeError("No speech was detected")
            inject(text, self.config.key_delay_ms)
            append(text, duration, language)
            self.feedback.success(text.rstrip())
            LOG.info("Inserted %d characters from %.1fs of audio", len(text), duration)
        except (RuntimeError, InjectionError) as exc:
            LOG.warning("Dictation failed: %s", exc)
            self.feedback.error(str(exc))
        except Exception as exc:
            LOG.exception("Unexpected transcription failure")
            self.feedback.error(f"Transcription failed: {exc}")
        finally:
            if path is not None:
                path.unlink(missing_ok=True)
            with self.state_lock:
                is_transcribing = self.state == "transcribing"
            if is_transcribing:
                self._set_state("idle")

    def serve(self) -> None:
        run_dir = runtime_dir()
        run_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        socket_path = run_dir / "control.sock"
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        server.listen(4)
        server.settimeout(1)
        self.indicator.start()
        threading.Thread(target=self.load_model, daemon=True).start()
        try:
            while not self.shutdown_event.is_set():
                try:
                    connection, _ = server.accept()
                except TimeoutError:
                    continue
                with connection:
                    try:
                        request = json.loads(connection.recv(4096).decode() or "{}")
                        command = request.get("command", "status")
                        response = (
                            self.toggle() if command == "toggle" else self.status()
                        )
                    except Exception as exc:  # noqa: BLE001 - keep the control daemon alive
                        response = {"error": str(exc)}
                    try:
                        connection.sendall((json.dumps(response) + "\n").encode())
                    except (BrokenPipeError, ConnectionResetError):
                        pass
        finally:
            self.shutdown_event.set()
            server.close()
            try:
                socket_path.unlink()
            except FileNotFoundError:
                pass


def send_command(command: str, timeout: float = 2.0) -> dict:
    path = runtime_dir() / "control.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(path))
        client.sendall((json.dumps({"command": command}) + "\n").encode())
        return json.loads(client.recv(4096).decode())
