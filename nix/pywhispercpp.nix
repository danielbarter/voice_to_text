{
  lib,
  python3Packages,
  cmake,
  ninja,
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

  nativeBuildInputs = [ cmake ninja ];
  dontUseCmakeConfigure = true;

  dependencies = with python3Packages; [
    numpy
    platformdirs
    requests
    tqdm
  ];

  env = {
    CMAKE_ARGS = "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON -DCMAKE_INSTALL_RPATH=$ORIGIN";
    NO_REPAIR = "1";
    PYWHISPERCPP_VERSION = version;
  };

  pythonImportsCheck = [ "pywhispercpp" ];

  meta = {
    description = "Python bindings for whisper.cpp";
    homepage = "https://github.com/absadiki/pywhispercpp";
    license = lib.licenses.mit;
  };
}
