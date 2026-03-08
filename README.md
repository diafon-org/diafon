# Latin 2.0

A cross-platform background app that auto-replaces typed character sequences with Unicode code points, based on the English International keyboard layout.

Works on **macOS**, **Windows**, and **Linux** — in every application.

---

## How it works

While Latin 2.0 is running, it monitors every key you type. When you finish a known sequence (e.g. `ae`), it instantly erases those characters and inserts the mapped Unicode character (`æ`) — as if you had pressed a special key on a hardware keyboard.

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# or
pip install pynput PyQt6
```

### 2. Generate tray icons (first run only)

```bash
python tools/make_icons.py
```

### 3. Run

```bash
python -m latin2
```

Or after installing the package:

```bash
pip install -e .
latin2
```

A small tray icon appears. Latin 2.0 is now active.

---

## Platform-specific setup

### macOS

The app needs **Accessibility** permission to read keystrokes.

1. Go to **System Settings → Privacy & Security → Accessibility**.
2. Add your terminal emulator (or the `latin2` binary) to the allowed list.

### Windows

No extra configuration needed. Works out-of-the-box.

### Linux

Add your user to the `input` group, then log out and back in:

```bash
sudo usermod -aG input $USER
```

Alternatively, run as root (not recommended for daily use).

---

## Default sequences (sample)

| Type    | Get | Type    | Get |
|---------|-----|---------|-----|
| `ae`    | æ   | `AE`    | Æ   |
| `oe`    | œ   | `OE`    | Œ   |
| `ss`    | ß   | `th`    | þ   |
| `a'`    | á   | `A'`    | Á   |
| `e'`    | é   | `n~`    | ñ   |
| `u"`    | ü   | `o/`    | ø   |
| `a/`    | å   | `c,`    | ç   |
| `zh`    | ž   | `sh`    | š   |
| `--`    | –   | `---`   | —   |
| `->`    | →   | `<-`    | ←   |
| `...`   | …   | `(c)`   | ©   |
| `1/2`   | ½   | `+-`    | ±   |
| `eur`   | €   | `gbp`   | £   |

Full list: see [`mappings/latin_extended.json`](mappings/latin_extended.json).

---

## Customisation

### Switching profiles

Click the tray icon → **Profiles** → select the profile you want.

### Adding personal overrides

Click the tray icon → **Settings & Mappings…** → **My Overrides** tab → **Add override…**

Overrides are stored in `~/.config/latin2/overrides.json` and take priority over all profiles.

### Creating a new profile

1. Click the tray icon → **Settings & Mappings…** → **Profiles** tab → **New profile…**
2. Give it a name and paste JSON mappings, or start empty.
3. Profile is saved to `~/.config/latin2/mappings/<name>.json`.

Alternatively, drop any `.json` file with the standard schema into that directory.

### Profile JSON schema

```json
{
  "meta": {
    "name": "My Profile",
    "description": "...",
    "version": "1.0.0"
  },
  "mappings": {
    "sequence": "replacement",
    "alpha": "α",
    "beta":  "β"
  }
}
```

---

## Architecture

```
latin2.0/
├── latin2/               # Package & tray entry point
│   ├── tray_app.py       # QSystemTrayIcon + menus
│   ├── assets/           # icon_on.png, icon_off.png
│   └── __main__.py
├── engine/
│   ├── key_engine.py     # pynput listener + sequence matching + replacement
│   └── mapping_manager.py# JSON profile loader, override manager
├── ui/
│   └── settings_window.py# PyQt6 settings / mapping editor window
├── mappings/
│   └── latin_extended.json  # built-in default profile (~120 mappings)
└── tools/
    └── make_icons.py     # one-time icon generator
```

---

## Licence

MIT
