"""
Desktop Automation Engine — executes OS-level actions from structured commands.
Voice → STT → LLM → JSON → Safety → THIS ENGINE → OS
"""

import asyncio
import logging
import os
import subprocess
import webbrowser
from typing import Dict, Any, Optional

from app.automation.app_registry import resolve_app
from app.automation.safety import validate_action, SafetyResult
from app.memory.models import ActionResult

logger = logging.getLogger(__name__)


class DesktopEngine:
    """
    Executes desktop automation actions on Windows.

    Supported actions:
        Level 1: open_app, search_browser, open_url
        Level 2: open_file, type_text, press_key, click_screen
    """

    def __init__(self):
        self._pyautogui = None  # Lazy import

    def _get_pyautogui(self):
        """Lazy-load pyautogui to avoid import errors if not installed."""
        if self._pyautogui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True  # Move mouse to corner to abort
                pyautogui.PAUSE = 0.3     # Small delay between actions
                self._pyautogui = pyautogui
            except ImportError:
                logger.error("pyautogui not installed. Run: pip install pyautogui")
                return None
        return self._pyautogui

    async def execute(self, action_data: Dict[str, Any]) -> ActionResult:
        """
        Execute a desktop automation action.

        Args:
            action_data: Dict with 'action' key and action-specific params.

        Returns:
            ActionResult with success/failure and message.
        """
        action_name = action_data.get("action", "")

        # Safety check
        safety: SafetyResult = validate_action(action_name, action_data)

        if not safety.allowed:
            return ActionResult(
                success=False,
                message=f"Action blocked: {safety.reason}",
            )

        if safety.needs_confirm:
            logger.info(f"⚠️ Action '{action_name}' would normally need confirmation — auto-approving for now.")

        # Route to handler
        handlers = {
            "open_app": self._open_app,
            "search_browser": self._search_browser,
            "open_url": self._open_url,
            "open_file": self._open_file,
            "type_text": self._type_text,
            "press_key": self._press_key,
            "click_screen": self._click_screen,
        }

        handler = handlers.get(action_name)
        if handler is None:
            return ActionResult(
                success=False,
                message=f"Unknown desktop action: '{action_name}'",
            )

        try:
            return await handler(action_data)
        except Exception as e:
            logger.error(f"Desktop action '{action_name}' failed: {e}", exc_info=True)
            return ActionResult(
                success=False,
                message=f"Failed to execute '{action_name}': {str(e)}",
            )

    # ── Level 1: Basic Actions ──────────────────────────────────

    async def _open_app(self, data: Dict[str, Any]) -> ActionResult:
        """Open an application by name."""
        app_name = data.get("app", "").strip()
        if not app_name:
            return ActionResult(success=False, message="No app name provided.")

        exe_path = resolve_app(app_name)
        if not exe_path:
            return ActionResult(
                success=False,
                message=f"Could not find application '{app_name}' on this system.",
            )

        logger.info(f"🚀 Opening app: {app_name} → {exe_path}")

        try:
            # Run in thread to not block event loop
            await asyncio.to_thread(
                subprocess.Popen,
                exe_path,
                shell=True,
            )
            return ActionResult(
                success=True,
                message=f"Opened {app_name}.",
                data={"app": app_name, "path": exe_path},
            )
        except Exception as e:
            return ActionResult(success=False, message=f"Failed to open {app_name}: {e}")

    async def _search_browser(self, data: Dict[str, Any]) -> ActionResult:
        """Open browser and search for a query."""
        query = data.get("query", "").strip()
        if not query:
            return ActionResult(success=False, message="No search query provided.")

        search_url = f"https://www.google.com/search?q={query}"
        logger.info(f"🔍 Browser search: {query}")

        await asyncio.to_thread(webbrowser.open, search_url)
        return ActionResult(
            success=True,
            message=f"Searching for '{query}' in your browser.",
            data={"query": query, "url": search_url},
        )

    async def _open_url(self, data: Dict[str, Any]) -> ActionResult:
        """Open a specific URL in the default browser."""
        url = data.get("url", "").strip()
        if not url:
            return ActionResult(success=False, message="No URL provided.")

        # Add https:// if missing
        if not url.startswith("http"):
            url = f"https://{url}"

        logger.info(f"🌐 Opening URL: {url}")
        await asyncio.to_thread(webbrowser.open, url)
        return ActionResult(
            success=True,
            message=f"Opened {url} in your browser.",
            data={"url": url},
        )

    # ── Level 2: Advanced Actions ───────────────────────────────

    async def _open_file(self, data: Dict[str, Any]) -> ActionResult:
        """Open a file or folder with its default application."""
        path = data.get("path", "").strip()
        if not path:
            return ActionResult(success=False, message="No file path provided.")

        if not os.path.exists(path):
            return ActionResult(
                success=False,
                message=f"Path does not exist: {path}",
            )

        logger.info(f"📂 Opening: {path}")
        await asyncio.to_thread(os.startfile, path)
        return ActionResult(
            success=True,
            message=f"Opened {os.path.basename(path)}.",
            data={"path": path},
        )

    async def _type_text(self, data: Dict[str, Any]) -> ActionResult:
        """Type text at the current cursor position."""
        text = data.get("text", "")
        if not text:
            return ActionResult(success=False, message="No text to type.")

        pag = self._get_pyautogui()
        if not pag:
            return ActionResult(success=False, message="pyautogui not available.")

        logger.info(f"⌨️ Typing: {text[:40]}...")

        # Use pyperclip + Ctrl+V for Unicode support (pyautogui.write only does ASCII)
        try:
            import pyperclip
            pyperclip.copy(text)
            await asyncio.to_thread(pag.hotkey, "ctrl", "v")
        except ImportError:
            # Fallback to basic typewrite (ASCII only)
            await asyncio.to_thread(pag.write, text, interval=0.02)

        return ActionResult(
            success=True,
            message=f"Typed: '{text[:50]}'",
            data={"text": text},
        )

    async def _press_key(self, data: Dict[str, Any]) -> ActionResult:
        """Press a keyboard shortcut or key combination."""
        keys = data.get("keys", "").strip()
        if not keys:
            return ActionResult(success=False, message="No keys specified.")

        pag = self._get_pyautogui()
        if not pag:
            return ActionResult(success=False, message="pyautogui not available.")

        logger.info(f"🔑 Pressing keys: {keys}")

        # Parse "ctrl+s" → hotkey("ctrl", "s")
        key_parts = [k.strip() for k in keys.lower().split("+")]

        await asyncio.to_thread(pag.hotkey, *key_parts)
        return ActionResult(
            success=True,
            message=f"Pressed {keys}.",
            data={"keys": keys},
        )

    async def _click_screen(self, data: Dict[str, Any]) -> ActionResult:
        """Click at specific screen coordinates."""
        x = data.get("x")
        y = data.get("y")

        if x is None or y is None:
            return ActionResult(success=False, message="Click coordinates (x, y) not provided.")

        pag = self._get_pyautogui()
        if not pag:
            return ActionResult(success=False, message="pyautogui not available.")

        logger.info(f"🖱️ Clicking at ({x}, {y})")
        await asyncio.to_thread(pag.click, x=int(x), y=int(y))
        return ActionResult(
            success=True,
            message=f"Clicked at ({x}, {y}).",
            data={"x": x, "y": y},
        )
