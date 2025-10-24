"""Configuration for desktop management."""

from typing import Set

# Browser process names
BROWSER_NAMES: Set[str] = {
    'msedge.exe', 'chrome.exe', 'firefox.exe', 'brave.exe', 'opera.exe'
}

# Apps to avoid processing
AVOIDED_APPS: Set[str] = {
    'AgentUI', 'SystemSettings', 'ShellExperienceHost'
}

# Apps to exclude from processing
EXCLUDED_APPS: Set[str] = {
    'Progman', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd',
    'Microsoft.UI.Content.PopupWindowSiteBridge',
    'Windows.UI.Core.CoreWindow', 'IME', 'MSCTFIME UI'
}

# DPI awareness settings
PROCESS_PER_MONITOR_DPI_AWARE = 2
