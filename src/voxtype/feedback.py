from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SOUND_DIRS = (
    Path("/usr/share/sounds/freedesktop/stereo"),
    Path("/usr/share/sounds/ocean/stereo"),
)


class Feedback:
    def __init__(self, notifications: bool, sounds: bool) -> None:
        self.notifications = notifications and shutil.which("notify-send") is not None
        self.sounds = sounds and shutil.which("canberra-gtk-play") is not None

    def notify(
        self, title: str, body: str, icon: str = "audio-input-microphone-symbolic"
    ) -> None:
        if not self.notifications:
            return
        subprocess.Popen(
            [
                "notify-send",
                "--app-name=VoxType",
                "--replace-id=8675309",
                "--icon",
                icon,
                "--expire-time=1800",
                title,
                body,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def sound(self, event: str) -> None:
        if not self.sounds:
            return
        subprocess.Popen(
            ["canberra-gtk-play", "--id", event, "--description", "VoxType"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def recording(self) -> None:
        self.sound("message-new-instant")
        self.notify(
            "VoxType is listening",
            "Speak naturally · use your VoxType shortcut again to finish",
        )

    def processing(self) -> None:
        self.sound("button-pressed")
        self.notify(
            "VoxType is transcribing",
            "Local Whisper model · audio never leaves this computer",
            "content-loading-symbolic",
        )

    def success(self, text: str) -> None:
        preview = text if len(text) <= 90 else text[:87] + "…"
        self.sound("complete")
        self.notify("Dictation inserted", preview, "emblem-ok-symbolic")

    def error(self, message: str) -> None:
        self.sound("dialog-warning")
        self.notify("VoxType needs attention", message, "dialog-warning-symbolic")
