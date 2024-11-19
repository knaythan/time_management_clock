# tests/test_app_monitor.py
import unittest
from clock.app_monitor import AppMonitor

class TestAppMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = AppMonitor()

    def test_initialization(self):
        self.assertEqual(self.monitor.app_times, {})

    def test_monitoring(self):
        self.monitor._update_app_time("test_app")
        self.assertIn("test_app", self.monitor.app_times)
        self.assertEqual(self.monitor.app_times["test_app"], 1)
