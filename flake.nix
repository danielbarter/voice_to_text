{
  description = "VoxType — private local voice typing for COSMIC and Wayland";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      version = builtins.head (builtins.match
        ''.*__version__ = "([^"]+)".*''
        (builtins.readFile ./src/voxtype/__init__.py));
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          source = nixpkgs.lib.cleanSourceWith {
            src = ./.;
            filter = path: type:
              let base = baseNameOf path; in
              !(base == "target" || base == "dist" || base == "rpmbuild" || base == ".git");
          };
        in
        rec {
          pywhispercpp = pkgs.callPackage ./nix/pywhispercpp.nix { };
          model-base-en = pkgs.callPackage ./nix/model-base-en.nix { };
          voxtype = pkgs.callPackage ./nix/package.nix {
            inherit pywhispercpp version;
            modelPackage = model-base-en;
            src = source;
          };
          default = voxtype;
        });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3.withPackages (pythonPackages: with pythonPackages; [
            dbus-next
            hatchling
            pytest
          ] ++ [ self.packages.${system}.pywhispercpp ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.pipewire
              pkgs.wtype
              pkgs.libcanberra-gtk3
              pkgs.libnotify
            ];

            shellHook = ''
              export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
            '';
          };
        });

      overlays.default = final: _prev: {
        voxtype = self.packages.${final.stdenv.hostPlatform.system}.voxtype;
        voxtype-model-base-en = self.packages.${final.stdenv.hostPlatform.system}.model-base-en;
      };

      nixosModules.default = import ./nix/nixos-module.nix { inherit self; };
    };
}
