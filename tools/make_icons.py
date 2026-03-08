#!/usr/bin/env python3
"""
Generate simple PNG tray icons programmatically so the app works out-of-the-box
without needing external image assets.

Run once:  python tools/make_icons.py
"""
import os
from pathlib import Path


def make_icon(path: Path, color_hex: str, letter: str = "L") -> None:
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt
        import sys

        app = QApplication.instance() or QApplication(sys.argv)
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(color_hex))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#ffffff"))
        font = QFont("Arial", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()

        path.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(path), "PNG")
        print(f"Written: {path}")
    except ImportError:
        # PyQt6 not available — write a minimal 1×1 transparent PNG as fallback.
        import struct, zlib
        def _png(r, g, b):
            def chunk(name, data):
                c = zlib.crc32(name + data) & 0xffffffff
                return struct.pack(">I", len(data)) + name + data + struct.pack(">I", c)
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            raw  = b"\x00" + bytes([r, g, b])
            idat = zlib.compress(raw)
            return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_png(*(int(color_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))))
        print(f"Written (fallback 1×1): {path}")


if __name__ == "__main__":
    assets = Path(__file__).parent.parent / "latin2" / "assets"
    make_icon(assets / "icon_on.png",  "#2ecc71", "L")
    make_icon(assets / "icon_off.png", "#95a5a6", "L")
