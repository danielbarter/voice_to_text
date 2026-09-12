import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voxtype.config import Config


class ConfigTests(unittest.TestCase):
    def test_packaging_environment_overrides_model_and_hotwords(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            config.write_text("[transcription]\nhotwords = 'local'\n", encoding="utf-8")
            environment = {
                "VOXTYPE_MODEL": "/models/ggml-base.en.bin",
                "VOXTYPE_HOTWORDS": "NixOS, PostgreSQL",
            }
            with (
                patch("voxtype.config.load_config_path", return_value=config),
                patch.dict(os.environ, environment),
            ):
                loaded = Config.load()

        self.assertEqual(loaded.model, environment["VOXTYPE_MODEL"])
        self.assertEqual(loaded.hotwords, environment["VOXTYPE_HOTWORDS"])


if __name__ == "__main__":
    unittest.main()
