# tests/test_focus_mode.py
import unittest
from tkinter import Tk
from clock.focus_mode import FocusMode

class TestFocusMode(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.focus_mode = FocusMode(self.root)

    def test_focus_mode_toggle(self):
        self.focus_mode.activate()
        self.assertTrue(self.focus_mode.is_active)
        self.focus_mode.deactivate()
        self.assertFalse(self.focus_mode.is_active)
