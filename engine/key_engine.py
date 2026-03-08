"""
Core key interception engine.

How it works:
  - A pynput Listener captures every key press.
  - Printable characters are accumulated in a buffer.
  - After each character, the buffer is checked against the active mapping trie.
  - If the buffer matches a known sequence exactly, the engine:
      1. Suppresses the just-typed character (via the return-False suppression).
      2. Sends (len(sequence) - 1) backspace keys to erase the already-committed
         earlier characters.
      3. Types the replacement Unicode character.
  - Any non-printable key (space, enter, arrow, etc.) flushes the buffer because
    the sequence is broken.
  - The engine is disabled/enabled via a threading.Event so the tray can toggle it.

Platform notes:
  - macOS  : requires Accessibility permissions for the process.
  - Windows: works out-of-the-box (uses the Windows low-level keyboard hook).
  - Linux  : requires either root or membership in the `input` group (uinput).
"""

from __future__ import annotations

import threading
from typing import Callable

from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode

from engine.mapping_manager import MappingManager


# Maximum sequence length we ever need to look back.
# Derived dynamically from the loaded mappings.
_DEFAULT_MAX_SEQ = 5


class KeyEngine:
    def __init__(self, manager: MappingManager) -> None:
        self._manager = manager
        self._controller = Controller()
        self._buffer: list[str] = []
        self._enabled = threading.Event()
        self._enabled.set()          # start enabled
        self._listener: keyboard.Listener | None = None
        self._lock = threading.Lock()
        self._on_replacement: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_on_replacement(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback invoked as callback(sequence, replacement)."""
        self._on_replacement = callback

    def enable(self) -> None:
        self._enabled.set()

    def disable(self) -> None:
        self._enabled.clear()
        with self._lock:
            self._buffer.clear()

    @property
    def is_enabled(self) -> bool:
        return self._enabled.is_set()

    def start(self) -> None:
        """Start the background listener thread."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            suppress=False,          # we handle suppression selectively below
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _max_seq_len(self) -> int:
        mappings = self._manager.active_mappings()
        if not mappings:
            return _DEFAULT_MAX_SEQ
        return max((len(k) for k in mappings), default=_DEFAULT_MAX_SEQ)

    def _on_press(self, key: Key | KeyCode | None) -> bool | None:
        """
        pynput callback. Called in the listener thread.
        Returning False would suppress the key globally — we avoid suppression
        here and instead use backspaces + typed replacement to stay compatible
        with all platforms (suppression requires elevated rights on some setups).
        """
        if not self._enabled.is_set():
            return None

        ch = _key_to_char(key)

        with self._lock:
            if ch is None:
                # Non-printable key — break the sequence buffer.
                self._buffer.clear()
                return None

            self._buffer.append(ch)

            # Keep buffer length bounded.
            max_len = self._max_seq_len()
            if len(self._buffer) > max_len:
                self._buffer.pop(0)

            # Check for a match, longest first.
            matched_seq, replacement = self._find_match()
            if matched_seq and replacement:
                # We need to erase (len-1) previously committed chars and then
                # type the replacement instead of the last char that just landed.
                # Schedule this outside the lock to avoid re-entrancy issues.
                seq_len = len(matched_seq)
                self._buffer.clear()
                threading.Thread(
                    target=self._apply_replacement,
                    args=(seq_len, replacement, matched_seq),
                    daemon=True,
                ).start()

        return None

    def _find_match(self) -> tuple[str, str] | tuple[None, None]:
        """
        Look for the longest matching sequence inside the current buffer,
        checking from the longest suffix down to length 2.
        """
        mappings = self._manager.active_mappings()
        if not mappings:
            return None, None

        buf = "".join(self._buffer)
        max_len = self._max_seq_len()

        for length in range(min(max_len, len(buf)), 1, -1):
            candidate = buf[-length:]
            if candidate in mappings:
                return candidate, mappings[candidate]

        return None, None

    def _apply_replacement(self, seq_len: int, replacement: str, original_seq: str) -> None:
        """
        Executed in a worker thread.
        Erases the typed sequence and types the replacement character.
        """
        import time
        # Small delay to let the last keydown event finish being processed
        # by the target application before we start sending backspaces.
        time.sleep(0.02)

        # Erase all characters in the sequence.
        for _ in range(seq_len):
            self._controller.press(Key.backspace)
            self._controller.release(Key.backspace)

        # Type the replacement.
        self._controller.type(replacement)

        if self._on_replacement:
            try:
                self._on_replacement(original_seq, replacement)
            except Exception:
                pass


def _key_to_char(key: Key | KeyCode | None) -> str | None:
    """
    Extract the printable character from a pynput key event.
    Returns None for special keys (shift, ctrl, enter, arrow keys, etc.).
    """
    if key is None:
        return None

    if isinstance(key, KeyCode):
        # key.char is the Unicode character, or None for dead keys / scancodes.
        return key.char  # may be None

    # It's a Key enum (special key) — not a printable character.
    return None
