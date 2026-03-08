"""
Mapping manager — loads, merges, and switches between mapping profiles.

A profile is a JSON file in the mappings/ directory with the schema:
    {
        "meta": { "name": "...", "description": "...", "version": "..." },
        "mappings": { "sequence": "replacement", ... }
    }

Profiles can be stacked/layered: a user can activate multiple profiles at once
and a user-overrides file can shadow any mapping from a base profile.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Resolution order for the mappings directory.
_MAPPINGS_DIRS: list[Path] = [
    Path(__file__).parent.parent / "mappings",              # repo built-ins
    Path.home() / ".config" / "latin2" / "mappings",       # user profiles
]

_OVERRIDES_FILE = Path.home() / ".config" / "latin2" / "overrides.json"


class MappingManager:
    """
    Manages multiple named profiles.

    Usage:
        manager = MappingManager()
        manager.load_all()
        manager.activate("Latin Extended")
        # Or stack multiple:
        manager.activate_multiple(["Latin Extended", "Math Symbols"])
        replacements = manager.active_mappings()   # merged dict
    """

    def __init__(self) -> None:
        # name -> parsed profile dict
        self._profiles: dict[str, dict[str, Any]] = {}
        # names of currently active profiles (in priority order, first wins)
        self._active: list[str] = []
        # user overrides (always highest priority)
        self._overrides: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Discovery & Loading
    # ------------------------------------------------------------------

    def load_all(self) -> None:
        """Scan all mapping directories and load every .json profile found."""
        for directory in _MAPPINGS_DIRS:
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.json")):
                self._load_file(path)

        self._load_overrides()
        log.info("Loaded %d mapping profile(s): %s", len(self._profiles), list(self._profiles.keys()))

    def reload(self) -> None:
        """Re-read all profiles from disk (useful after user edits a file)."""
        self._profiles.clear()
        self._overrides.clear()
        self.load_all()

    def _load_file(self, path: Path) -> None:
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("meta", {}).get("name") or path.stem
            self._profiles[name] = data
            log.debug("Loaded profile '%s' from %s (%d mappings)", name, path, len(data.get("mappings", {})))
        except Exception as exc:
            log.warning("Failed to load mapping file %s: %s", path, exc)

    def _load_overrides(self) -> None:
        """Load user overrides file (silently skip if absent)."""
        if not _OVERRIDES_FILE.exists():
            return
        try:
            with _OVERRIDES_FILE.open(encoding="utf-8") as f:
                data = json.load(f)
            self._overrides = data.get("mappings", {})
            log.debug("Loaded %d override(s) from %s", len(self._overrides), _OVERRIDES_FILE)
        except Exception as exc:
            log.warning("Failed to load overrides from %s: %s", _OVERRIDES_FILE, exc)

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def profile_names(self) -> list[str]:
        return sorted(self._profiles.keys())

    def get_profile(self, name: str) -> dict[str, Any] | None:
        return self._profiles.get(name)

    def activate(self, name: str) -> None:
        """Activate a single profile (replaces current selection)."""
        if name not in self._profiles:
            raise ValueError(f"Unknown profile: '{name!r}'. Available: {self.profile_names()}")
        self._active = [name]
        log.info("Activated profile: %s", name)

    def activate_multiple(self, names: list[str]) -> None:
        """
        Activate multiple profiles. Earlier entries in the list take precedence
        when two profiles define the same sequence.
        """
        for name in names:
            if name not in self._profiles:
                raise ValueError(f"Unknown profile: '{name!r}'. Available: {self.profile_names()}")
        self._active = list(names)
        log.info("Activated profiles (in priority order): %s", self._active)

    def deactivate_all(self) -> None:
        self._active.clear()

    @property
    def active_profile_names(self) -> list[str]:
        return list(self._active)

    # ------------------------------------------------------------------
    # Merged mappings (what the engine uses)
    # ------------------------------------------------------------------

    def active_mappings(self) -> dict[str, str]:
        """
        Return the merged mapping dict for the currently active profiles.
        Priority: user overrides > first active profile > second active profile > …
        """
        merged: dict[str, str] = {}
        # Lowest priority first; later updates will be overwritten by higher.
        for name in reversed(self._active):
            profile = self._profiles.get(name, {})
            merged.update(profile.get("mappings", {}))
        # User overrides win over everything.
        merged.update(self._overrides)
        return merged

    # ------------------------------------------------------------------
    # Override management
    # ------------------------------------------------------------------

    def set_override(self, sequence: str, replacement: str) -> None:
        """Add or update a user override and persist it."""
        self._overrides[sequence] = replacement
        self._save_overrides()

    def remove_override(self, sequence: str) -> None:
        """Remove a user override and persist the change."""
        self._overrides.pop(sequence, None)
        self._save_overrides()

    def list_overrides(self) -> dict[str, str]:
        return dict(self._overrides)

    def _save_overrides(self) -> None:
        _OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _OVERRIDES_FILE.open("w", encoding="utf-8") as f:
            json.dump({"mappings": self._overrides}, f, ensure_ascii=False, indent=2)
        log.debug("Saved overrides to %s", _OVERRIDES_FILE)

    # ------------------------------------------------------------------
    # Custom profile creation
    # ------------------------------------------------------------------

    def create_profile(self, name: str, description: str = "", mappings: dict[str, str] | None = None) -> Path:
        """
        Create a new user profile JSON file and load it into memory.
        Returns the path of the written file.
        """
        user_dir = Path.home() / ".config" / "latin2" / "mappings"
        user_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
        path = user_dir / f"{safe_name}.json"

        data: dict[str, Any] = {
            "meta": {
                "name": name,
                "description": description,
                "version": "1.0.0",
                "base_keyboard": "English International",
            },
            "mappings": mappings or {},
        }
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._profiles[name] = data
        log.info("Created profile '%s' at %s", name, path)
        return path

    def update_profile_mappings(self, name: str, mappings: dict[str, str]) -> None:
        """Replace the mappings block of an existing profile and save to disk."""
        if name not in self._profiles:
            raise ValueError(f"Unknown profile: {name!r}")
        profile = self._profiles[name]
        profile["mappings"] = mappings

        # Find and overwrite the file.
        for directory in _MAPPINGS_DIRS:
            safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
            candidate = directory / f"{safe_name}.json"
            if candidate.exists():
                with candidate.open("w", encoding="utf-8") as f:
                    json.dump(profile, f, ensure_ascii=False, indent=2)
                log.info("Updated profile '%s' at %s", name, candidate)
                return

        log.warning("Could not find file for profile '%s' to save updates.", name)
