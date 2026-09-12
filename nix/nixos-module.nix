{ self }:
{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.services.voxtype;
  system = pkgs.stdenv.hostPlatform.system;
  defaultPackage = self.packages.${system}.voxtype;
  defaultModel = self.packages.${system}.model-base-en;
in
{
  options.services.voxtype = {
    enable = lib.mkEnableOption "VoxType local voice dictation";

    package = lib.mkOption {
      type = lib.types.package;
      default = defaultPackage;
      description = "VoxType package to run.";
    };

    modelPackage = lib.mkOption {
      type = lib.types.package;
      default = defaultModel;
      description = "Offline whisper.cpp model package.";
    };

    hotwords = lib.mkOption {
      type = lib.types.str;
      default = "";
      example = "NixOS, PostgreSQL";
      description = "Optional comma-separated decoder vocabulary hints.";
    };

  };

  config = lib.mkIf cfg.enable {
    hardware.graphics.enable = true;

    environment.systemPackages = [ cfg.package ];

    systemd.user.services.voxtype = {
      description = "VoxType local voice dictation";
      wantedBy = [ "graphical-session.target" ];
      partOf = [ "graphical-session.target" ];
      after = [ "graphical-session.target" "pipewire.service" ];
      environment = {
        VOXTYPE_MODEL = "${cfg.modelPackage}/ggml-base.en.bin";
        VOXTYPE_HOTWORDS = cfg.hotwords;
      };
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/voxtype daemon";
        Restart = "on-failure";
        RestartSec = 2;
      };
    };
  };
}
