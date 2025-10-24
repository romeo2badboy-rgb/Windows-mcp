"""Configuration for UI tree element detection and categorization."""

from typing import Set

# Control types that are interactive (clickable, typeable, etc.)
INTERACTIVE_CONTROL_TYPE_NAMES: Set[str] = {
    'ButtonControl', 'ListItemControl', 'MenuItemControl', 'DocumentControl',
    'EditControl', 'CheckBoxControl', 'RadioButtonControl', 'ComboBoxControl',
    'HyperlinkControl', 'SplitButtonControl', 'TabItemControl',
    'TreeItemControl', 'DataItemControl', 'HeaderItemControl', 'TextBoxControl',
    'SpinnerControl', 'ScrollBarControl', 'ImageControl'
}

# Default actions that indicate interactivity
DEFAULT_ACTIONS: Set[str] = {
    'Click', 'Press', 'Jump', 'Check', 'Uncheck', 'Double Click'
}

# Control types that are informative (text, labels, etc.)
INFORMATIVE_CONTROL_TYPE_NAMES: Set[str] = {
    'TextControl', 'ImageControl', 'GroupControl', 'PaneControl'
}

# Maximum retries for thread operations
THREAD_MAX_RETRIES = 3

# Minimum area (in pixels) for element visibility
MIN_ELEMENT_AREA = 10

# Font settings for annotations
ANNOTATION_FONT_SIZE = 12
ANNOTATION_PADDING = 20
