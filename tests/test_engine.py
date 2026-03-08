"""
Unit tests for the sequence-matching logic in KeyEngine.
Run with:  python3 -m pytest tests/ -v
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.mapping_manager import MappingManager
from engine.key_engine import KeyEngine, _key_to_char
from pynput.keyboard import KeyCode, Key


class FakeMappingManager(MappingManager):
    """Minimal stand-in that returns a fixed mapping dict without file I/O."""
    def __init__(self, mappings: dict):
        self._profiles = {"test": {"mappings": mappings}}
        self._active = ["test"]
        self._overrides = {}

    def load_all(self): pass


class TestKeyToChar(unittest.TestCase):
    def test_regular_char(self):
        self.assertEqual(_key_to_char(KeyCode(char="a")), "a")

    def test_special_key_returns_none(self):
        self.assertIsNone(_key_to_char(Key.enter))
        self.assertIsNone(_key_to_char(Key.space))
        self.assertIsNone(_key_to_char(Key.backspace))

    def test_none_key(self):
        self.assertIsNone(_key_to_char(None))


class TestEngineSequenceMatching(unittest.TestCase):
    def _make_engine(self, mappings):
        return KeyEngine(FakeMappingManager(mappings))

    def test_two_char_match(self):
        engine = self._make_engine({"ae": "æ"})
        # Simulate typing 'a', 'e'
        engine._buffer = list("ae")
        seq, rep = engine._find_match()
        self.assertEqual(seq, "ae")
        self.assertEqual(rep, "æ")

    def test_no_match(self):
        engine = self._make_engine({"ae": "æ"})
        engine._buffer = list("bc")
        seq, rep = engine._find_match()
        self.assertIsNone(seq)
        self.assertIsNone(rep)

    def test_longest_match_wins(self):
        engine = self._make_engine({"--": "–", "---": "—"})
        # Buffer has three dashes — longest match (---) should win.
        engine._buffer = list("---")
        seq, rep = engine._find_match()
        self.assertEqual(seq, "---")
        self.assertEqual(rep, "—")

    def test_suffix_match(self):
        # Buffer has extra leading chars but the suffix matches.
        engine = self._make_engine({"ae": "æ"})
        engine._buffer = list("xyzae")
        seq, rep = engine._find_match()
        self.assertEqual(seq, "ae")
        self.assertEqual(rep, "æ")

    def test_buffer_flush_on_special_key(self):
        engine = self._make_engine({"ae": "æ"})
        # Suppress the actual replacement thread.
        with patch.object(engine, "_apply_replacement"):
            engine._buffer = ["a"]
            engine._on_press(Key.enter)
            self.assertEqual(engine._buffer, [])

    def test_enable_disable(self):
        engine = self._make_engine({"ae": "æ"})
        self.assertTrue(engine.is_enabled)
        engine.disable()
        self.assertFalse(engine.is_enabled)
        engine.enable()
        self.assertTrue(engine.is_enabled)

    def test_disabled_engine_ignores_input(self):
        engine = self._make_engine({"ae": "æ"})
        engine.disable()
        engine._on_press(KeyCode(char="a"))
        engine._on_press(KeyCode(char="e"))
        self.assertEqual(engine._buffer, [])


class TestMappingManager(unittest.TestCase):
    def test_override_priority(self):
        manager = FakeMappingManager({"ae": "æ"})
        manager._overrides = {"ae": "X"}   # override shadows profile
        self.assertEqual(manager.active_mappings()["ae"], "X")

    def test_multi_profile_priority(self):
        manager = MappingManager.__new__(MappingManager)
        manager._profiles = {
            "A": {"mappings": {"x": "1", "y": "2"}},
            "B": {"mappings": {"x": "9", "z": "3"}},
        }
        manager._active = ["A", "B"]   # A takes priority
        manager._overrides = {}
        merged = manager.active_mappings()
        self.assertEqual(merged["x"], "1")  # A wins over B
        self.assertEqual(merged["y"], "2")  # only in A
        self.assertEqual(merged["z"], "3")  # only in B


if __name__ == "__main__":
    unittest.main(verbosity=2)
