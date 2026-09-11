{
  description = "VoxType — private local voice typing for COSMIC and Wayland";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
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
          voxtype = pkgs.callPackage ./nix/package.nix { src = source; };
          model-base-en = pkgs.callPackage ./nix/model-base-en.nix { };
          default = voxtype;
        });

      overlays.default = final: _prev: {
        voxtype = self.packages.${final.stdenv.hostPlatform.system}.voxtype;
        voxtype-model-base-en = self.packages.${final.stdenv.hostPlatform.system}.model-base-en;
      };

      nixosModules.default = import ./nix/nixos-module.nix { inherit self; };
    };
}

