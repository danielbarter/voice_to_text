from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time

from . import __version__
from .config import Config, ensure_config
from .daemon import VoxTypeDaemon, send_command
from .history import recent
from .transcriber import load_transcriber


def _send(command: str) -> dict:
    try:
        return send_command(command)
    except (TimeoutError, FileNotFoundError, ConnectionRefusedError):
        if shutil.which("systemctl"):
            subprocess.run(
                ["systemctl", "--user", "start", "voxtype.service"], check=False
            )
            for _ in range(20):
                time.sleep(0.1)
                try:
                    return send_command(command)
                except (TimeoutError, FileNotFoundError, ConnectionRefusedError):
                    pass
        raise RuntimeError(
            "VoxType service is not running; try: systemctl --user restart voxtype"
        )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="voxtype", description="Private voice typing for COSMIC"
    )
    result.add_argument("--version", action="version", version=f"VoxType {__version__}")
    commands = result.add_subparsers(dest="command")
    commands.add_parser("toggle", help="start or finish a dictation")
    commands.add_parser("status", help="show daemon state")
    commands.add_parser("daemon", help=argparse.SUPPRESS)
    commands.add_parser("prepare", help="download the configured model for offline use")
    commands.add_parser("settings", help="open VoxType configuration")
    commands.add_parser("shortcuts", help="open COSMIC keyboard settings")
    history = commands.add_parser("history", help="show recent dictations")
    history.add_argument("-n", "--limit", type=int, default=20)
    return result


def main() -> None:
    args = parser().parse_args()
    command = args.command or "toggle"
    if command == "daemon":
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
        )
        VoxTypeDaemon(Config.load()).serve()
    elif command == "prepare":
        config = Config.load()
        print(f"Preparing {config.model} for offline dictation…", flush=True)
        load_transcriber(config, allow_download=True)
        print(f"Ready: {config.model}")
    elif command in {"toggle", "status"}:
        try:
            response = _send(command)
        except RuntimeError as exc:
            print(f"voxtype: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        if command == "status" or sys.stdout.isatty():
            print(json.dumps(response, indent=2))
    elif command == "settings":
        path = ensure_config()
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if editor:
            raise SystemExit(subprocess.call([*editor.split(), str(path)]))
        opener = shutil.which("cosmic-edit") or shutil.which("xdg-open")
        if opener:
            subprocess.Popen(
                [opener, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            print(path)
    elif command == "shortcuts":
        settings = shutil.which("cosmic-settings")
        if settings:
            subprocess.Popen(
                [settings, "keyboard"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            print(
                "Open your desktop's custom keyboard shortcut settings.",
                file=sys.stderr,
            )
    elif command == "history":
        for record in recent(max(1, args.limit)):
            print(f"{record.get('time', '')}  {record.get('text', '')}")


if __name__ == "__main__":
    main()
