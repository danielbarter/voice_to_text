# Distribution packages

## Fedora 43+

Build the binary and source RPMs in the existing Fedora 43 toolbox:

```bash
./packaging/fedora/build-rpm.sh
```

Install both generated packages, then enable the user service:

```bash
sudo dnf install \
  packaging/fedora/rpmbuild/RPMS/current/voxtype.rpm \
  packaging/fedora/rpmbuild/RPMS/current/voxtype-model-base-en.rpm
systemctl --user enable --now voxtype.service
```

Each user adds a custom shortcut manually in COSMIC Settings with the command
`voxtype-ctl` and their preferred key (for example, `Insert`).

On Fedora COSMIC Atomic, layer the same two RPMs and reboot into the new
deployment first:

```bash
sudo rpm-ostree install \
  packaging/fedora/rpmbuild/RPMS/current/voxtype.rpm \
  packaging/fedora/rpmbuild/RPMS/current/voxtype-model-base-en.rpm
systemctl reboot
```

When replacing an earlier locally layered VoxType build, remove the old local
requests in the same transaction:

```bash
sudo rpm-ostree install \
  --uninstall=voxtype \
  --uninstall=voxtype-model-base-en \
  packaging/fedora/rpmbuild/RPMS/current/voxtype.rpm \
  packaging/fedora/rpmbuild/RPMS/current/voxtype-model-base-en.rpm
systemctl reboot
```

Then enable the per-user service and add the COSMIC shortcut manually after
logging back in.

The RPM uses Fedora's `python3-pywhispercpp`, `python3-dbus-next`, `wtype`, and
PipeWire packages. The model subpackage contains the checksum-verified, pinned
whisper.cpp `base.en` model shared with the Nix package and enables fully
offline startup.

## NixOS

Try the package without changing the system:

```bash
nix run .#voxtype -- --version
```

Or add the flake and module to a NixOS configuration:

```nix
{
  inputs.voxtype.url = "path:/path/to/voice_to_text";

  outputs = { nixpkgs, voxtype, ... }: {
    nixosConfigurations.my-host = nixpkgs.lib.nixosSystem {
      modules = [
        voxtype.nixosModules.default
        {
          services.voxtype.enable = true;
          # Optional; empty by default and never used as a forced replacement.
          services.voxtype.hotwords = "NixOS";
        }
      ];
    };
  };
}
```

After the rebuild, each COSMIC user adds a custom shortcut manually. Set its
command to `voxtype-ctl` and choose any preferred key.

The NixOS module enables the user service and points it at the same pinned
whisper.cpp model used by Fedora, stored in the Nix store; normal use performs
no network access. The Nix package builds whisper.cpp with Vulkan acceleration,
and the module enables NixOS graphics support so the service can use the system
GPU driver.
