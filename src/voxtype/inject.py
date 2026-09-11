from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class InjectionError(RuntimeError):
    pass


def inject(text: str, delay_ms: int = 0) -> None:
    """Type Unicode text through COSMIC's virtual-keyboard Wayland protocol."""
    binary = shutil.which("wrtype") or shutil.which("wtype")
    if binary is None:
        for candidate in (
            Path.home() / ".local/bin/wrtype",
            Path.home() / ".cargo/bin/wrtype",
        ):
            if candidate.is_file():
                binary = str(candidate)
                break
    if binary is None:
        raise InjectionError("wrtype is not installed; run ./install.sh again")
    if Path(binary).name == "wtype":
        args = [binary]
        if delay_ms:
            args.extend(["-d", str(delay_ms)])
        args.extend(["--", text])
        input_text = None
    else:
        args = [binary, "--stdin"]
        if delay_ms:
            args.extend(["-d", str(delay_ms)])
        input_text = text
    result = subprocess.run(
        args, input=input_text, text=True, capture_output=True, timeout=30, check=False
    )
    if result.returncode:
        detail = (
            result.stderr.strip() or f"wrtype exited with status {result.returncode}"
        )
        raise InjectionError(detail)
