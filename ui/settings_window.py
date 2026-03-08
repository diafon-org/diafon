"""
Settings & Mapping Editor window.

Tabs:
  1. Profiles  — list existing profiles, create new ones, delete user profiles
  2. Mappings  — view/edit all sequences in the active profile(s)
  3. Overrides — personal overrides that shadow any profile
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableView, QLineEdit, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QMessageBox, QHeaderView,
    QSplitter, QTextEdit, QAbstractItemView, QFrame,
)

from engine.key_engine import KeyEngine
from engine.mapping_manager import MappingManager


class SettingsWindow(QWidget):
    def __init__(self, manager: MappingManager, engine: KeyEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._engine = engine

        self.setWindowTitle("Latin 2.0 — Settings")
        self.resize(800, 600)

        tabs = QTabWidget()
        tabs.addTab(ProfilesTab(manager, engine, self), "Profiles")
        tabs.addTab(MappingsTab(manager, self), "Mappings")
        tabs.addTab(OverridesTab(manager, self), "My Overrides")
        tabs.addTab(AboutTab(), "About")

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)


# ---------------------------------------------------------------------------
# Profiles Tab
# ---------------------------------------------------------------------------

class ProfilesTab(QWidget):
    def __init__(self, manager: MappingManager, engine: KeyEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager
        self._engine = engine

        layout = QVBoxLayout(self)

        # Status bar
        status_layout = QHBoxLayout()
        self._status_label = QLabel()
        self._update_status_label()
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        btn_toggle = QPushButton()
        btn_toggle.setText("Disable" if engine.is_enabled else "Enable")
        btn_toggle.clicked.connect(self._toggle)
        self._btn_toggle = btn_toggle
        status_layout.addWidget(btn_toggle)
        layout.addLayout(status_layout)

        layout.addWidget(_hr())

        # Profile list
        layout.addWidget(QLabel("<b>Available profiles</b> (select to activate):"))

        self._profile_list = QTableView()
        self._profile_model = QStandardItemModel(0, 3)
        self._profile_model.setHorizontalHeaderLabels(["Profile name", "Mappings", "Description"])
        self._profile_list.setModel(self._profile_model)
        self._profile_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._profile_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._profile_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._profile_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._populate_profiles()
        layout.addWidget(self._profile_list)

        btn_row = QHBoxLayout()
        btn_activate = QPushButton("Activate selected")
        btn_activate.clicked.connect(self._activate_selected)
        btn_new = QPushButton("New profile…")
        btn_new.clicked.connect(self._new_profile)
        btn_row.addWidget(btn_activate)
        btn_row.addWidget(btn_new)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _update_status_label(self) -> None:
        active = self._manager.active_profile_names
        state = "ACTIVE" if self._engine.is_enabled else "PAUSED"
        profiles = ", ".join(active) if active else "(none)"
        self._status_label.setText(f"<b>State:</b> {state} &nbsp;&nbsp; <b>Active profile:</b> {profiles}")

    def _populate_profiles(self) -> None:
        self._profile_model.setRowCount(0)
        active = self._manager.active_profile_names
        for name in self._manager.profile_names():
            profile = self._manager.get_profile(name) or {}
            count = len(profile.get("mappings", {}))
            desc = profile.get("meta", {}).get("description", "")
            name_item = QStandardItem(name)
            if name in active:
                font = name_item.font()
                font.setBold(True)
                name_item.setFont(font)
            count_item = QStandardItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_item = QStandardItem(desc)
            self._profile_model.appendRow([name_item, count_item, desc_item])

    def _toggle(self) -> None:
        if self._engine.is_enabled:
            self._engine.disable()
            self._btn_toggle.setText("Enable")
        else:
            self._engine.enable()
            self._btn_toggle.setText("Disable")
        self._update_status_label()

    def _activate_selected(self) -> None:
        rows = self._profile_list.selectionModel().selectedRows()
        if not rows:
            return
        name = self._profile_model.item(rows[0].row(), 0).text()
        self._manager.activate(name)
        self._populate_profiles()
        self._update_status_label()

    def _new_profile(self) -> None:
        dlg = NewProfileDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, desc, raw = dlg.values()
            try:
                mappings = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError as exc:
                QMessageBox.critical(self, "Invalid JSON", str(exc))
                return
            self._manager.create_profile(name, desc, mappings)
            self._populate_profiles()


# ---------------------------------------------------------------------------
# Mappings Tab
# ---------------------------------------------------------------------------

class MappingsTab(QWidget):
    def __init__(self, manager: MappingManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Search:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter sequences or characters…")
        self._search.textChanged.connect(self._apply_filter)
        top.addWidget(self._search)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._populate)
        top.addWidget(btn_refresh)
        layout.addLayout(top)

        self._table = QTableView()
        self._model = QStandardItemModel(0, 3)
        self._model.setHorizontalHeaderLabels(["Sequence", "→", "Unicode name"])
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterKeyColumn(-1)   # search all columns
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._table.setModel(self._proxy)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        self._count_label = QLabel()
        layout.addWidget(self._count_label)

        self._populate()

    def _populate(self) -> None:
        self._model.setRowCount(0)
        for seq, rep in sorted(self._manager.active_mappings().items()):
            seq_item  = QStandardItem(seq)
            font = QFont("monospace")
            seq_item.setFont(font)
            rep_item  = QStandardItem(rep)
            rep_item.setFont(font)
            try:
                import unicodedata
                uname = unicodedata.name(rep, "")
            except Exception:
                uname = ""
            name_item = QStandardItem(uname)
            self._model.appendRow([seq_item, rep_item, name_item])
        self._count_label.setText(f"{self._model.rowCount()} mapping(s) in active profile(s).")

    def _apply_filter(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)


# ---------------------------------------------------------------------------
# Overrides Tab
# ---------------------------------------------------------------------------

class OverridesTab(QWidget):
    def __init__(self, manager: MappingManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Overrides are personal mappings that take priority over every profile.\n"
            "They are stored in <code>~/.config/latin2/overrides.json</code>."
        ))

        self._table = QTableView()
        self._model = QStandardItemModel(0, 2)
        self._model.setHorizontalHeaderLabels(["Sequence", "Replacement"])
        self._table.setModel(self._model)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add override…")
        btn_add.clicked.connect(self._add)
        btn_del = QPushButton("Delete selected")
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._populate()

    def _populate(self) -> None:
        self._model.setRowCount(0)
        for seq, rep in sorted(self._manager.list_overrides().items()):
            self._model.appendRow([QStandardItem(seq), QStandardItem(rep)])

    def _add(self) -> None:
        dlg = AddOverrideDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            seq, rep = dlg.values()
            if seq and rep:
                self._manager.set_override(seq, rep)
                self._populate()

    def _delete(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        seq = self._model.item(rows[0].row(), 0).text()
        self._manager.remove_override(seq)
        self._populate()


# ---------------------------------------------------------------------------
# About Tab
# ---------------------------------------------------------------------------

class AboutTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("<h2>Latin 2.0</h2>")
        layout.addWidget(title)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setFrameStyle(QFrame.Shape.NoFrame)
        info.setHtml("""
<p><b>Latin 2.0</b> is a cross-platform keyboard enhancement tool that
auto-replaces typed character sequences with a single Unicode code point.</p>

<p><b>How to use:</b></p>
<ul>
  <li>Make sure the app is running (tray icon is active).</li>
  <li>Type a sequence anywhere — e.g. <code>ae</code> → <code>æ</code>,
      <code>n~</code> → <code>ñ</code>, <code>--</code> → <code>–</code>.</li>
  <li>Use the <b>Profiles</b> tab to switch between mapping sets.</li>
  <li>Use <b>My Overrides</b> to add personal substitutions.</li>
</ul>

<p><b>Adding a custom profile:</b></p>
<ol>
  <li>Click <i>New profile…</i> in the Profiles tab, or</li>
  <li>Drop a <code>.json</code> file into
      <code>~/.config/latin2/mappings/</code> and click Reload.</li>
</ol>

<p><b>Default sequences (sample):</b></p>
<table>
<tr><td><code>ae</code></td><td>→ æ</td><td>&nbsp;&nbsp;</td><td><code>A'</code></td><td>→ Á</td></tr>
<tr><td><code>oe</code></td><td>→ œ</td><td></td><td><code>n~</code></td><td>→ ñ</td></tr>
<tr><td><code>ss</code></td><td>→ ß</td><td></td><td><code>u\"</code></td><td>→ ü</td></tr>
<tr><td><code>--</code></td><td>→ –</td><td></td><td><code>---</code></td><td>→ —</td></tr>
<tr><td><code>-></code></td><td>→ →</td><td></td><td><code>&lt;-</code></td><td>→ ←</td></tr>
<tr><td><code>...</code></td><td>→ …</td><td></td><td><code>(c)</code></td><td>→ ©</td></tr>
</table>

<hr>
<p style="color:grey; font-size:small;">
Version 1.0.0 &nbsp;·&nbsp; MIT Licence &nbsp;·&nbsp; github.com/latin2
</p>
""")
        layout.addWidget(info)


# ---------------------------------------------------------------------------
# Dialogs
# ---------------------------------------------------------------------------

class NewProfileDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Profile")
        self.resize(500, 400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. My Greek Keys")
        form.addRow("Profile name:", self._name)
        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Optional description")
        form.addRow("Description:", self._desc)
        layout.addLayout(form)

        layout.addWidget(QLabel("Initial mappings (JSON, optional):"))
        self._json_edit = QTextEdit()
        self._json_edit.setPlaceholderText('{"alpha": "α", "beta": "β"}')
        self._json_edit.setFont(QFont("monospace"))
        layout.addWidget(self._json_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, str]:
        return self._name.text().strip(), self._desc.text().strip(), self._json_edit.toPlainText()


class AddOverrideDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Override")
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._seq = QLineEdit()
        self._seq.setPlaceholderText("e.g.  oo")
        form.addRow("Sequence to type:", self._seq)
        self._rep = QLineEdit()
        self._rep.setPlaceholderText("e.g.  °  (paste Unicode character)")
        form.addRow("Replacement character:", self._rep)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str]:
        return self._seq.text(), self._rep.text()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hr() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line
