{ fetchurl, runCommand }:

let
  revision = "3d3d5dee26484f91867d81cb899cfcf72b96be6c";
  baseUrl = "https://huggingface.co/Systran/faster-whisper-base.en/resolve/${revision}";
  config = fetchurl {
    url = "${baseUrl}/config.json";
    hash = "sha256-87w4Ien8dqJ7rlOOEa5bZ33N01K0YAQpznlR05hWmus=";
  };
  model = fetchurl {
    url = "${baseUrl}/model.bin";
    hash = "sha256-KhZpJVOaFgBfFP8yg1n5ua253E+2Mbs7InUmhi6T4u8=";
  };
  tokenizer = fetchurl {
    url = "${baseUrl}/tokenizer.json";
    hash = "sha256-kpxSUkCUNtzhs4p10au8teEy0XDY4yTk4E7ZFfotIt8=";
  };
  vocabulary = fetchurl {
    url = "${baseUrl}/vocabulary.txt";
    hash = "sha256-/3dYh0bTolldMqtbaf/XuVziRBrFdTPLZvw+tXWhFc8=";
  };
in
runCommand "voxtype-faster-whisper-base.en-model" { } ''
  mkdir -p "$out"
  ln -s ${config} "$out/config.json"
  ln -s ${model} "$out/model.bin"
  ln -s ${tokenizer} "$out/tokenizer.json"
  ln -s ${vocabulary} "$out/vocabulary.txt"
''

