import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from avatar import Avatar, ASSETS, STATES

class AvatarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.avatar = Avatar()
        if not self.avatar.images:
            # When run in a repository clone without bundled assets,
            # populate dummy 1x1 pixmaps so state machine & logic can be tested.
            self.avatar.images = {s: QPixmap(1, 1) for s in STATES}

    def tearDown(self):
        self.avatar.timer.stop()
        self.avatar.close()

    def test_bundled_atlas(self):
        if not (ASSETS / 'kubo-atlas.png').is_file():
            self.skipTest('Thiếu dữ liệu assets/kubo-atlas.png (xem docs/ASSETS.md)')
        avatar = Avatar()
        self.assertEqual(set(avatar.images), set(STATES))
        self.assertTrue(all(not image.isNull() for image in avatar.images.values()))

    def test_selected_emotions_survive_speech_and_blink(self):
        for emotion in ('happy', 'sad', 'angry', 'shy', 'surprised'):
            self.avatar.emotion = emotion
            self.assertEqual(self.avatar.frame_name(4.6, .8), emotion)

    def test_neutral_animation(self):
        self.assertEqual(self.avatar.frame_name(0, .8), 'talk')
        self.assertEqual(self.avatar.frame_name(.2, .8), 'idle')
        self.assertEqual(self.avatar.frame_name(4.6, 0), 'blink')
        self.assertEqual(self.avatar.frame_name(1, 0), 'idle')

    def test_invalid_custom_folder_keeps_current_images(self):
        image = self.avatar.images['idle'].cacheKey()
        self.assertFalse(self.avatar.load_images(ASSETS / 'not-present'))
        self.assertEqual(self.avatar.images['idle'].cacheKey(), image)
