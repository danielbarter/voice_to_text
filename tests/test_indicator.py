import unittest

from voxtype.indicator import SIZE, StatusItem, _icon


class IndicatorTests(unittest.TestCase):
    def test_every_state_is_a_complete_argb_pixmap(self):
        for state in ("idle", "recording", "transcribing", "loading", "error"):
            with self.subTest(state=state):
                width, height, pixels = _icon(state)[0]
                self.assertEqual((width, height), (SIZE, SIZE))
                self.assertEqual(len(pixels), SIZE * SIZE * 4)

    def test_active_states_are_visually_distinct(self):
        idle = _icon("idle")[0][2]
        recording = _icon("recording")[0][2]
        transcribing = _icon("transcribing")[0][2]
        self.assertNotEqual(idle, recording)
        self.assertNotEqual(recording, transcribing)

    def test_no_context_menu_uses_standard_sentinel_path(self):
        item = StatusItem(lambda: None)
        self.assertEqual(item.Menu, "/NO_DBUSMENU")


if __name__ == "__main__":
    unittest.main()
