{
  lib,
  makeWrapper,
  python3Packages,
  pipewire,
  wtype,
  libcanberra-gtk3,
  libnotify,
  modelPackage,
  pywhispercpp,
  src,
  version,
}:

python3Packages.buildPythonApplication {
  pname = "voxtype";
  inherit version;
  pyproject = true;
  inherit src;

  build-system = [ python3Packages.hatchling ];

  dependencies = with python3Packages; [
    dbus-next
    pywhispercpp
  ];

  nativeBuildInputs = [ makeWrapper ];

  postInstall = ''
    install -Dpm0644 data/dev.voxtype.VoxType.desktop \
      "$out/share/applications/dev.voxtype.VoxType.desktop"
  '';

  postFixup = ''
    wrapProgram "$out/bin/voxtype" \
      --set-default VOXTYPE_MODEL "${modelPackage}/ggml-base.en.bin" \
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
