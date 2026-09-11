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
  toml = pkgs.formats.toml { };
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
      type = lib.types.nullOr lib.types.package;
      default = defaultModel;
      description = "Offline faster-whisper model directory, or null to use the user cache.";
    };

    hotwords = lib.mkOption {
      type = lib.types.str;
      default = "";
      example = "NixOS, PostgreSQL";
      description = "Optional comma-separated decoder vocabulary hints.";
    };

  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ];

    environment.etc."xdg/voxtype/config.toml".source = toml.generate "voxtype-config.toml" {
      transcription = {
        engine = "faster-whisper";
        model = "base.en";
        language = "en";
        compute_type = "int8";
        beam_size = 5;
        inherit (cfg) hotwords;
      };
      audio = {
        source = "";
        max_seconds = 120;
      };
      typing = {
        trailing_space = true;
        voice_commands = true;
        key_delay_ms = 0;
      };
      feedback = {
        notifications = false;
        sounds = true;
      };
    };

    systemd.user.services.voxtype = {
      description = "VoxType local voice dictation";
      wantedBy = [ "graphical-session.target" ];
      partOf = [ "graphical-session.target" ];
      after = [ "graphical-session.target" "pipewire.service" ];
      environment = {
        VOXTYPE_ENGINE = "faster-whisper";
      } // lib.optionalAttrs (cfg.modelPackage != null) {
        VOXTYPE_MODEL = toString cfg.modelPackage;
      };
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/voxtype daemon";
        Restart = "on-failure";
        RestartSec = 2;
      };
    };
  };
}
