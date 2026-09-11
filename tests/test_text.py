import unittest

from voxtype.text import polish


class PolishTests(unittest.TestCase):
    def test_spacing_and_trailing_space(self):
        self.assertEqual(polish("  Hello   world. "), "Hello world. ")

    def test_voice_commands(self):
        self.assertEqual(
            polish("First paragraph new paragraph Second line new line third"),
            "First paragraph\n\nSecond line\nthird ",
        )

    def test_commands_can_be_disabled(self):
        self.assertEqual(polish("new line", voice_commands=False), "new line ")


if __name__ == "__main__":
    unittest.main()
