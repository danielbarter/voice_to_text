import tempfile
import unittest
from pathlib import Path

from voxtype.transcriber import _resolve_model


class ModelResolutionTests(unittest.TestCase):
    def test_explicit_model_path_is_used_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "custom.bin"
            model.write_bytes(b"user-provided weights")

            self.assertEqual(_resolve_model(str(model)), model)

    def test_missing_model_must_be_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.bin"
            with self.assertRaisesRegex(RuntimeError, "install.*model package"):
                _resolve_model(str(missing))


if __name__ == "__main__":
    unittest.main()
