# Distribution packages

## Fedora 43+

Build the binary and source RPMs in the existing Fedora 43 toolbox:

```bash
./packaging/fedora/build-rpm.sh
```

Install both generated binary packages, then enable the user service and add
the per-user COSMIC shortcut:

```bash
sudo dnf install \
  packaging/fedora/rpmbuild/RPMS/x86_64/voxtype-[0-9]*.rpm \
  packaging/fedora/rpmbuild/RPMS/noarch/voxtype-model-base-en-*.rpm
systemctl --user enable --now voxtype.service
voxtype install-shortcut --key Insert
```

On Fedora COSMIC Atomic, layer the same two RPMs and reboot into the new
deployment first:

```bash
sudo rpm-ostree install \
  packaging/fedora/rpmbuild/RPMS/x86_64/voxtype-[0-9]*.rpm \
  packaging/fedora/rpmbuild/RPMS/noarch/voxtype-model-base-en-*.rpm
systemctl reboot
```

Then run the two per-user `systemctl` and `voxtype install-shortcut` commands
above after logging back in.

The RPM uses Fedora's `python3-pywhispercpp`, `python3-dbus-next`, `wtype`, and
PipeWire packages. The model subpackage contains a checksum-verified, pinned
`base.en` model and enables fully offline startup.

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

After the rebuild, each COSMIC user registers their own shortcut once:

```bash
voxtype install-shortcut --key Insert
```

The NixOS module enables the user service and points it at a pinned model in
the Nix store; normal use performs no network access.
