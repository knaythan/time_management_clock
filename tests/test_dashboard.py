# tests/test_dashboard.py
import unittest
from tkinter import Tk
from clock.dashboard import ProductivityDashboard

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.dashboard = ProductivityDashboard(self.root)

    def test_dashboard_display(self):
        self.dashboard.display()
        self.assertIsNotNone(self.dashboard.tree)
