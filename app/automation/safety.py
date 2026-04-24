"""
Safety Layer — validates automation actions before execution.
Three tiers: SAFE (auto-execute), CONFIRM (ask user), BLOCKED (refuse).
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Safety Tiers ──────────────────────────────────────────────────

# Actions that execute immediately without confirmation
SAFE_ACTIONS = frozenset({
    "open_app",
    "search_browser",
    "open_url",
})

# Actions that require voice confirmation before execution
CONFIRM_ACTIONS = frozenset({
    "open_file",
    "type_text",
    "press_key",
    "click_screen",
})

# Actions that are always REFUSED (never execute)
BLOCKED_ACTIONS = frozenset({
    "delete_file",
    "format_disk",
    "shutdown",
    "restart",
    "rm",
    "rmdir",
    "del",
})

# Dangerous paths that can never be opened/modified
BLOCKED_PATHS = [
    r"C:\Windows\System32",
    r"C:\Windows\SysWOW64",
    r"C:\Windows\Boot",
    r"C:\Windows\assembly",
    r"C:\$Recycle.Bin",
]

# Dangerous key combos that are blocked
BLOCKED_KEYS = frozenset({
    "alt+f4",      # Close windows — too destructive
    "ctrl+alt+delete",
    "win+l",       # Lock screen
})


class SafetyResult:
    """Result of a safety check."""
    def __init__(self, allowed: bool, needs_confirm: bool = False, reason: str = ""):
        self.allowed = allowed
        self.needs_confirm = needs_confirm
        self.reason = reason

    def __repr__(self):
        return f"SafetyResult(allowed={self.allowed}, confirm={self.needs_confirm}, reason='{self.reason}')"


def validate_action(action_name: str, action_data: dict) -> SafetyResult:
    """
    Validate an automation action before execution.

    Args:
        action_name: The action type (e.g., "open_app", "type_text").
        action_data: Full action data dict from the LLM.

    Returns:
        SafetyResult indicating if action is allowed.
    """
    # Block list check
    if action_name in BLOCKED_ACTIONS:
        reason = f"Action '{action_name}' is blocked for safety."
        logger.warning(f"🚫 BLOCKED: {reason}")
        return SafetyResult(allowed=False, reason=reason)

    # Path safety check for file-related actions
    if action_name in ("open_file", "delete_file"):
        path = action_data.get("path", "")
        if not _is_path_safe(path):
            reason = f"Path '{path}' is in a protected system directory."
            logger.warning(f"🚫 BLOCKED PATH: {reason}")
            return SafetyResult(allowed=False, reason=reason)

    # Key combo safety for press_key
    if action_name == "press_key":
        keys = action_data.get("keys", "").lower().strip()
        if keys in BLOCKED_KEYS:
            reason = f"Key combination '{keys}' is blocked for safety."
            logger.warning(f"🚫 BLOCKED KEY: {reason}")
            return SafetyResult(allowed=False, reason=reason)

    # Safe actions — auto execute
    if action_name in SAFE_ACTIONS:
        return SafetyResult(allowed=True)

    # Confirm actions — need user confirmation
    if action_name in CONFIRM_ACTIONS:
        return SafetyResult(
            allowed=True,
            needs_confirm=True,
            reason=f"Action '{action_name}' requires confirmation."
        )

    # Unknown action — block by default
    reason = f"Unknown action '{action_name}' — blocked by default."
    logger.warning(f"🚫 UNKNOWN: {reason}")
    return SafetyResult(allowed=False, reason=reason)


def _is_path_safe(path: str) -> bool:
    """Check if a file path is safe to access (not a system directory)."""
    if not path:
        return False

    try:
        resolved = str(Path(path).resolve())
        for blocked in BLOCKED_PATHS:
            if resolved.lower().startswith(blocked.lower()):
                return False
        return True
    except Exception:
        return False
