#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null; then
    echo "VoxType needs uv (https://docs.astral.sh/uv/)" >&2
    exit 1
fi

echo "Installing VoxType and its private Python environment…"
uv tool install --python 3.12 --editable "${project_dir}[faster]" --force

echo "Building the instant hotkey client…"
cargo build --release --manifest-path "$project_dir/native/voxtype-ctl/Cargo.toml"
install -m 0755 "$project_dir/native/voxtype-ctl/target/release/voxtype-ctl" "$HOME/.local/bin/voxtype-ctl"

if ! command -v wrtype >/dev/null; then
    echo "Building the small Wayland typing helper…"
    if command -v toolbox >/dev/null && toolbox list 2>/dev/null | grep -q fedora-toolbox-43; then
        toolbox run -c fedora-toolbox-43 cargo install wrtype --version 0.1.0 --locked --root "$HOME/.local"
    else
        cargo install wrtype --version 0.1.0 --locked --root "$HOME/.local"
    fi
fi

mkdir -p "$HOME/.config/systemd/user"
install -m 0644 "$project_dir/systemd/voxtype.service" "$HOME/.config/systemd/user/voxtype.service"
mkdir -p "$HOME/.local/share/applications"
install -m 0644 "$project_dir/data/dev.voxtype.VoxType.desktop" "$HOME/.local/share/applications/dev.voxtype.VoxType.desktop"
systemctl --user daemon-reload

"$HOME/.local/bin/voxtype" install-shortcut --key Insert --executable "$HOME/.local/bin/voxtype-ctl"

echo "Downloading the local Whisper model (first install only)…"
"$HOME/.local/bin/voxtype" prepare
systemctl --user enable voxtype.service
systemctl --user restart voxtype.service

echo
echo "VoxType is installed. Press Insert, speak, then press Insert again."
echo "Settings: voxtype settings"
echo "Shortcut: voxtype shortcuts"
echo "Logs:     journalctl --user -u voxtype -f"
