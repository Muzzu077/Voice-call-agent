"""
App Registry — maps friendly app names to Windows executable paths.
Supports fuzzy name matching and custom overrides via environment variables.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Known app paths on Windows (checked at runtime)
_REGISTRY: dict[str, list[str]] = {
    # Browsers
    "chrome": [
        r"C:\Users\muzzu\AppData\Local\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],

    # Editors / IDEs
    "vscode": ["code"],  # Resolved via PATH
    "code": ["code"],
    "notepad": ["notepad.exe"],
    "notepad++": [
        r"C:\Program Files\Notepad++\notepad++.exe",
        r"C:\Program Files (x86)\Notepad++\notepad++.exe",
    ],

    # System tools
    "explorer": ["explorer.exe"],
    "terminal": ["wt.exe", "powershell.exe"],  # Windows Terminal or PowerShell
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "task_manager": ["taskmgr.exe"],
    "calculator": ["calc.exe"],
    "settings": ["ms-settings:"],
    "control_panel": ["control.exe"],

    # Media
    "spotify": [
        r"C:\Users\muzzu\AppData\Roaming\Spotify\Spotify.exe",
    ],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],

    # Communication
    "teams": [
        r"C:\Users\muzzu\AppData\Local\Microsoft\Teams\Update.exe --processStart Teams.exe",
    ],
    "discord": [
        r"C:\Users\muzzu\AppData\Local\Discord\Update.exe --processStart Discord.exe",
    ],
    "whatsapp": [
        r"C:\Users\muzzu\AppData\Local\WhatsApp\WhatsApp.exe",
    ],
}

# Alias map — common alternate names
_ALIASES: dict[str, str] = {
    "google chrome": "chrome",
    "google": "chrome",
    "vs code": "vscode",
    "visual studio code": "vscode",
    "visual studio": "vscode",
    "files": "explorer",
    "file manager": "explorer",
    "file explorer": "explorer",
    "windows terminal": "terminal",
    "shell": "terminal",
    "calc": "calculator",
    "paint": "mspaint",
    "snip": "snippingtool",
    "task manager": "task_manager",
    "system settings": "settings",
}


def resolve_app(name: str) -> Optional[str]:
    """
    Resolve a friendly app name to an executable path.

    Args:
        name: The app name the user said (e.g., "chrome", "vscode").

    Returns:
        Full path to exe, or None if not found.
    """
    name = name.strip().lower()

    # Check aliases first
    canonical = _ALIASES.get(name, name)

    # Look up in registry
    candidates = _REGISTRY.get(canonical, [])

    for candidate in candidates:
        # If it's a simple command name, check if it's in PATH
        if "\\" not in candidate and "/" not in candidate:
            found = shutil.which(candidate)
            if found:
                logger.debug(f"Resolved '{name}' via PATH: {found}")
                return found
            continue

        # Check if the full path exists
        if Path(candidate).exists():
            logger.debug(f"Resolved '{name}' to: {candidate}")
            return candidate

    logger.warning(f"Could not resolve app '{name}' — no matching executable found.")
    return None


def get_app_list() -> list[str]:
    """Return list of all registered app names."""
    return sorted(set(list(_REGISTRY.keys()) + list(_ALIASES.keys())))
