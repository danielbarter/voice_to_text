import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from voxtype.shortcut import _entries, install_shortcut


class ShortcutParserTests(unittest.TestCase):
    def test_split_ron_map_entries(self):
        body = """
        (modifiers: [Super], key: "a"): Disable,
        (modifiers: [], key: "Insert", description: Some("Hi, there")): Spawn("thing"),
        """
        entries = _entries(body)
        self.assertEqual(len(entries), 2)
        self.assertIn('key: "a"', entries[0])
        self.assertIn('Some("Hi, there")', entries[1])

    def test_install_preserves_existing_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "custom"
            path.write_text('{(modifiers: [Super], key: "a"): Disable,}\n')
            with patch("voxtype.shortcut.SHORTCUT_PATH", path):
                install_shortcut("/home/test/.local/bin/voxtype")
                install_shortcut("/home/test/.local/bin/voxtype")
            rendered = path.read_text()
            self.assertIn('key: "a"', rendered)
            self.assertEqual(rendered.count('key: "Insert"'), 1)
            self.assertEqual(rendered.count("VoxType"), 1)

    def test_install_refuses_to_steal_a_key(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "custom"
            path.write_text('{(modifiers: [], key: "Insert"): Spawn("mine"),}\n')
            with (
                patch("voxtype.shortcut.SHORTCUT_PATH", path),
                self.assertRaisesRegex(RuntimeError, "already has"),
            ):
                install_shortcut("/home/test/.local/bin/voxtype")


if __name__ == "__main__":
    unittest.main()
