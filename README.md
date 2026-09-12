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
- The lightweight hotkey client reaches the warm daemon without loading the UI stack.
- Audio is local and temporary. No API key, account, or cloud request is used.
- Say “new line”, “new paragraph”, “open quote”, or “close quote” for formatting.
- Recent successful dictations are recoverable with `voxtype history`.

## Install

Install VoxType using the Fedora RPM or Nix/NixOS packages documented in
[`packaging/README.md`](packaging/README.md).

The packages do not modify COSMIC's keyboard shortcuts. The microphone selected
in COSMIC Settings is used automatically.

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
journalctl --user -u voxtype -f
```

After changing `voxtype settings`, reload with:

```bash
systemctl --user restart voxtype
```

The Fedora and Nix packages both install the same checksum-verified, pinned
whisper.cpp model. History is stored at `~/.local/share/voxtype/history.jsonl`.
Temporary microphone audio is deleted immediately after each transcription
attempt.

## Development

```bash
nix develop
pytest
```
