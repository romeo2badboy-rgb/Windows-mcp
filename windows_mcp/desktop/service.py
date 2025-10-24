"""Desktop management service."""

import ctypes
import subprocess
from typing import Optional
from locale import getpreferredencoding

try:
    import uiautomation as ua
    from uiautomation import (
        GetRootControl, Control, IsIconic, IsZoomed,
        IsWindowVisible, ControlFromCursor, GetScreenSize,
        WindowControl
    )
    UIAUTOMATION_AVAILABLE = True
except ImportError:
    UIAUTOMATION_AVAILABLE = False

import pyautogui
from PIL import Image
import psutil

from windows_mcp.desktop.config import (
    PROCESS_PER_MONITOR_DPI_AWARE,
    EXCLUDED_APPS,
    AVOIDED_APPS,
    BROWSER_NAMES
)
from windows_mcp.desktop.views import App, Size, Status


class Desktop:
    """Manages desktop state and operations."""

    def __init__(self):
        """Initialize the desktop service."""
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        except:
            pass

        self.encoding = getpreferredencoding()

    def get_screen_size(self) -> Size:
        """Get the screen dimensions.

        Returns:
            Size object with screen width and height
        """
        if UIAUTOMATION_AVAILABLE:
            width, height = GetScreenSize()
        else:
            width, height = pyautogui.size()

        return Size(width=width, height=height)

    def get_screenshot(self, scale: float = 0.7) -> Image.Image:
        """Capture a screenshot of the desktop.

        Args:
            scale: Scale factor for the screenshot

        Returns:
            PIL Image object
        """
        screenshot = pyautogui.screenshot()

        if scale != 1.0:
            new_size = (int(screenshot.width * scale), int(screenshot.height * scale))
            screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)

        return screenshot

    def get_cursor_location(self) -> tuple[int, int]:
        """Get the current mouse cursor position.

        Returns:
            Tuple of (x, y) coordinates
        """
        position = pyautogui.position()
        return (position.x, position.y)

    def get_element_under_cursor(self) -> Optional[Control]:
        """Get the UI element under the cursor.

        Returns:
            Control object or None if uiautomation not available
        """
        if not UIAUTOMATION_AVAILABLE:
            return None

        return ControlFromCursor()

    def is_app_visible(self, app: Control) -> bool:
        """Check if an application window is visible.

        Args:
            app: Control object for the application

        Returns:
            True if the app is visible
        """
        is_not_minimized = self._get_app_status(app) != Status.MINIMIZED
        size = self._get_app_size(app)
        area = size.area()
        return is_not_minimized and area > 10

    def is_app_browser(self, node: Control) -> bool:
        """Check if an application is a web browser.

        Args:
            node: Control object for the application

        Returns:
            True if the app is a browser
        """
        try:
            process = psutil.Process(node.ProcessId)
            return process.name() in BROWSER_NAMES
        except:
            return False

    def get_windows_version(self) -> str:
        """Get the Windows version string.

        Returns:
            Windows version description
        """
        response, status = self._execute_command(
            "(Get-CimInstance Win32_OperatingSystem).Caption"
        )
        if status == 0:
            return response.strip()
        return "Windows"

    def get_default_language(self) -> str:
        """Get the default system language.

        Returns:
            Language description string
        """
        response, status = self._execute_command(
            "Get-Culture | Select-Object -ExpandProperty DisplayName"
        )
        if status == 0:
            return response.strip()
        return "English (United States)"

    def _get_app_status(self, control: Control) -> Status:
        """Get the status of an application window.

        Args:
            control: Control object for the window

        Returns:
            Status enum value
        """
        if not UIAUTOMATION_AVAILABLE:
            return Status.NORMAL

        try:
            handle = control.NativeWindowHandle
            if IsIconic(handle):
                return Status.MINIMIZED
            elif IsZoomed(handle):
                return Status.MAXIMIZED
            elif IsWindowVisible(handle):
                return Status.NORMAL
            else:
                return Status.HIDDEN
        except:
            return Status.NORMAL

    def _get_app_size(self, control: Control) -> Size:
        """Get the size of an application window.

        Args:
            control: Control object for the window

        Returns:
            Size object with window dimensions
        """
        try:
            window = control.BoundingRectangle
            if window.isempty():
                return Size(width=0, height=0)
            return Size(width=window.width(), height=window.height())
        except:
            return Size(width=0, height=0)

    def _execute_command(self, command: str) -> tuple[str, int]:
        """Execute a PowerShell command.

        Args:
            command: PowerShell command to execute

        Returns:
            Tuple of (output, return_code)
        """
        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                timeout=25,
                errors='ignore'
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            return (stdout or stderr, result.returncode)
        except subprocess.TimeoutExpired:
            return ('Command execution timed out', 1)
        except Exception:
            return ('Command execution failed', 1)
