{
  lib,
  makeWrapper,
  python3Packages,
  rustc,
  cargo,
  pipewire,
  wtype,
  libcanberra-gtk3,
  libnotify,
  src,
}:

python3Packages.buildPythonApplication rec {
  pname = "voxtype";
  version = "0.2.0";
  pyproject = true;
  inherit src;

  build-system = [ python3Packages.hatchling ];

  dependencies = with python3Packages; [
    dbus-next
    faster-whisper
  ];

  nativeBuildInputs = [
    cargo
    makeWrapper
    rustc
  ];

  postBuild = ''
    cargo build --release --locked --offline \
      --manifest-path native/voxtype-ctl/Cargo.toml
  '';

  postInstall = ''
    install -Dpm0755 native/voxtype-ctl/target/release/voxtype-ctl \
      "$out/bin/voxtype-ctl"
    install -Dpm0644 data/dev.voxtype.VoxType.desktop \
      "$out/share/applications/dev.voxtype.VoxType.desktop"
  '';

  postFixup = ''
    wrapProgram "$out/bin/voxtype" \
      --prefix PATH : ${lib.makeBinPath [ pipewire wtype libcanberra-gtk3 libnotify ]}
  '';

  nativeCheckInputs = [ python3Packages.dbus-next ];
  checkPhase = ''
    runHook preCheck
    python -m unittest discover -s tests -v
    runHook postCheck
  '';
  pythonImportsCheck = [ "voxtype" ];

  meta = {
    description = "Private local voice typing for COSMIC and Wayland";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
    mainProgram = "voxtype";
  };
}
