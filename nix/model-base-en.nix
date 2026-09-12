{ fetchurl, runCommand }:

let
  metadata = (builtins.fromJSON (builtins.readFile ../packaging/models.json))."base.en";
  model = fetchurl {
    inherit (metadata) url sha256;
  };
in
runCommand "voxtype-whisper-cpp-base.en-model" { } ''
  mkdir -p "$out"
  ln -s ${model} "$out/${metadata.filename}"
''
