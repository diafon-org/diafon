"""
System tray application entry point.

Provides:
  - Tray icon with enable/disable toggle
  - Profile selector submenu
  - Quick access to the settings / mapping editor window
  - Recent replacements log
  - "About" dialog

Requires PyQt6 and the engine packages.
Run with:  python -m latin2
Or via the installed console script:  latin2
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)

from engine.key_engine import KeyEngine
from engine.mapping_manager import MappingManager
from ui.settings_window import SettingsWindow

log = logging.getLogger(__name__)

ICON_ENABLED  = str(Path(__file__).parent / "assets" / "icon_on.png")
ICON_DISABLED = str(Path(__file__).parent / "assets" / "icon_off.png")


class _Bridge(QObject):
    """Thread-safe bridge: signal fires in the engine thread, slot runs in Qt thread."""
    replacement_occurred = pyqtSignal(str, str)


class TrayApp:
    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._manager = MappingManager()
        self._manager.load_all()

        self._engine = KeyEngine(self._manager)
        self._bridge = _Bridge()
        self._bridge.replacement_occurred.connect(self._on_replacement_in_qt)
        self._engine.set_on_replacement(
            lambda seq, rep: self._bridge.replacement_occurred.emit(seq, rep)
        )

        self._recent: list[tuple[str, str]] = []  # (sequence, replacement)
        self._settings_win: SettingsWindow | None = None

        self._tray = self._build_tray()
        self._tray.show()

        # Activate the first available profile by default.
        names = self._manager.profile_names()
        if names:
            self._manager.activate(names[0])
            log.info("Auto-activated profile: %s", names[0])

        self._engine.start()

    # ------------------------------------------------------------------
    # Tray construction
    # ------------------------------------------------------------------

    def _build_tray(self) -> QSystemTrayIcon:
        icon = self._get_icon(enabled=True)
        tray = QSystemTrayIcon(icon)
        tray.setToolTip("Latin 2.0 — active")
        tray.activated.connect(self._on_tray_activated)
        tray.setContextMenu(self._build_menu())
        return tray

    def _build_menu(self) -> QMenu:
        menu = QMenu()

        # --- Toggle ---
        self._action_toggle = QAction("Disable", menu)
        self._action_toggle.triggered.connect(self._toggle_engine)
        menu.addAction(self._action_toggle)

        menu.addSeparator()

        # --- Profiles submenu ---
        self._profiles_menu = QMenu("Profiles", menu)
        self._rebuild_profiles_menu()
        menu.addMenu(self._profiles_menu)

        menu.addSeparator()

        # --- Recent replacements (last 5) ---
        self._recent_menu = QMenu("Recent replacements", menu)
        self._recent_menu.addAction("(none yet)").setEnabled(False)
        menu.addMenu(self._recent_menu)

        menu.addSeparator()

        # --- Settings ---
        action_settings = QAction("Settings & Mappings…", menu)
        action_settings.triggered.connect(self._open_settings)
        menu.addAction(action_settings)

        menu.addSeparator()

        # --- Quit ---
        action_quit = QAction("Quit Latin 2.0", menu)
        action_quit.triggered.connect(self._quit)
        menu.addAction(action_quit)

        return menu

    def _rebuild_profiles_menu(self) -> None:
        self._profiles_menu.clear()
        active = self._manager.active_profile_names
        for name in self._manager.profile_names():
            action = QAction(name, self._profiles_menu)
            action.setCheckable(True)
            action.setChecked(name in active)
            action.triggered.connect(lambda checked, n=name: self._select_profile(n))
            self._profiles_menu.addAction(action)
        if not self._manager.profile_names():
            self._profiles_menu.addAction("(no profiles found)").setEnabled(False)

    # ------------------------------------------------------------------
    # Slots & callbacks
    # ------------------------------------------------------------------

    def _toggle_engine(self) -> None:
        if self._engine.is_enabled:
            self._engine.disable()
            self._action_toggle.setText("Enable")
            self._tray.setIcon(self._get_icon(enabled=False))
            self._tray.setToolTip("Latin 2.0 — paused")
        else:
            self._engine.enable()
            self._action_toggle.setText("Disable")
            self._tray.setIcon(self._get_icon(enabled=True))
            self._tray.setToolTip("Latin 2.0 — active")

    def _select_profile(self, name: str) -> None:
        self._manager.activate(name)
        self._rebuild_profiles_menu()
        # Rebuild the full context menu so checkmarks update.
        self._tray.setContextMenu(self._build_menu())

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._open_settings()

    def _on_replacement_in_qt(self, seq: str, rep: str) -> None:
        """Called in the Qt main thread after each successful replacement."""
        self._recent.insert(0, (seq, rep))
        self._recent = self._recent[:10]
        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        self._recent_menu.clear()
        if not self._recent:
            self._recent_menu.addAction("(none yet)").setEnabled(False)
            return
        for seq, rep in self._recent[:5]:
            label = f"{seq!r}  →  {rep}"
            self._recent_menu.addAction(label).setEnabled(False)

    def _open_settings(self) -> None:
        if self._settings_win is None or not self._settings_win.isVisible():
            self._settings_win = SettingsWindow(self._manager, self._engine)
        self._settings_win.show()
        self._settings_win.raise_()
        self._settings_win.activateWindow()

    def _quit(self) -> None:
        self._engine.stop()
        self._app.quit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_icon(enabled: bool) -> QIcon:
        path = ICON_ENABLED if enabled else ICON_DISABLED
        icon = QIcon(path)
        if icon.isNull():
            # Fallback: generate a simple colored square programmatically.
            from PyQt6.QtGui import QPixmap, QPainter, QColor
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#2ecc71" if enabled else "#95a5a6"))
            icon = QIcon(pixmap)
        return icon


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Latin 2.0")
    app.setQuitOnLastWindowClosed(False)   # keep running when settings window closes

    if not QSystemTrayIcon.isSystemTrayAvailable():
        log.error("System tray not available on this platform.")
        sys.exit(1)

    tray_app = TrayApp(app)  # noqa: F841 — keep reference alive

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
