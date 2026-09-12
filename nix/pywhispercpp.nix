{
  lib,
  python3Packages,
  cmake,
  ninja,
  shaderc,
  vulkan-headers,
  vulkan-loader,
}:

python3Packages.buildPythonPackage rec {
  pname = "pywhispercpp";
  version = "1.4.0";
  pyproject = true;

  src = python3Packages.fetchPypi {
    inherit pname version;
    hash = "sha256-uP3Txu6S5tiJDaVKBwRCp3sVyvXH/7Xdj5xCZ1Hqki8=";
  };

  postPatch = ''
    substituteInPlace pyproject.toml --replace-fail '    "cmake>=3.12",' ""
    substituteInPlace pyproject.toml --replace-fail '    "repairwheel",' ""
  '';

  build-system = [
    python3Packages.ninja
    python3Packages.setuptools
    python3Packages.setuptools-scm
    python3Packages.wheel
  ];

  nativeBuildInputs = [
    cmake
    ninja
    (lib.getBin shaderc)
  ];
  dontUseCmakeConfigure = true;

  buildInputs = [
    shaderc
    vulkan-headers
    vulkan-loader
  ];

  dependencies = with python3Packages; [
    numpy
    platformdirs
    requests
    tqdm
  ];

  env = {
    CMAKE_ARGS = "-DGGML_VULKAN=ON -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON -DCMAKE_INSTALL_RPATH=$ORIGIN";
    NO_REPAIR = "1";
    PYWHISPERCPP_VERSION = version;
  };

  postInstall = ''
    test -e "$out/${python3Packages.python.sitePackages}/libggml-vulkan.so"
  '';

  pythonImportsCheck = [ "pywhispercpp" ];

  meta = {
    description = "Python bindings for whisper.cpp";
    homepage = "https://github.com/absadiki/pywhispercpp";
    license = lib.licenses.mit;
  };
}
