# VoxType

Private, local voice typing built for the COSMIC desktop.

Press **Insert**, speak, and press **Insert** again. VoxType records through the
PipeWire microphone selected in COSMIC Settings, transcribes locally with
Whisper, and types the result into the window that already had focus.

## Why it feels native

- COSMIC owns the global shortcut—no keylogger and no `input`-group access.
- Text is injected through COSMIC's Wayland virtual-keyboard protocol.
- The model stays warm in a user service, avoiding startup cost on every phrase.
- A live COSMIC status-area icon turns red while listening and amber while transcribing.
- The native hotkey client reaches the warm daemon in a few milliseconds.
- Audio is local and temporary. No API key, account, or cloud request is used.
- Say “new line”, “new paragraph”, “open quote”, or “close quote” for formatting.
- Recent successful dictations are recoverable with `voxtype history`.

## Install

```bash
./install.sh
```

Fedora RPM and Nix/NixOS packaging is documented in
[`packaging/README.md`](packaging/README.md).

The installer does not modify COSMIC's keyboard shortcuts. The first run
downloads the `base.en` model (roughly 150 MB). On this machine the Logitech
C920 selected in COSMIC Settings is used automatically.

Add the shortcut manually under **COSMIC Settings → Input Devices → Keyboard →
View and customize shortcuts → Custom**:

```text
Name:     VoxType
Command:  voxtype-ctl
Shortcut: Insert (or any key you prefer)
```

## Use

```text
Insert      start listening
Insert      stop, transcribe, and insert
```

The panel microphone turns red immediately while recording, then amber while
Whisper is working. You can also click that panel icon to start or stop.

The key is a normal COSMIC custom shortcut, so it can be changed or removed
entirely from the same settings page.

Useful commands:

```bash
voxtype status
voxtype settings
voxtype shortcuts
voxtype history
voxtype prepare  # download a newly configured model
journalctl --user -u voxtype -f
```

After changing `voxtype settings`, reload with:

```bash
systemctl --user restart voxtype
```

Models are cached under `~/.cache/voxtype/models`; history is stored at
`~/.local/share/voxtype/history.jsonl`. Temporary microphone audio is deleted
immediately after each transcription attempt.

## Development

```bash
uv run --python 3.12 --with faster-whisper python -m unittest discover -s tests
```
