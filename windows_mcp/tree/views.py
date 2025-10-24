"""Data models for UI tree elements and state."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BoundingBox:
    """Represents a bounding box for a UI element."""
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int

    def to_xywh_string(self) -> str:
        """Return as (x, y, width, height) string."""
        return f'({self.left},{self.top},{self.width},{self.height})'

    def to_xyxy_string(self) -> str:
        """Return as (x1, y1, x2, y2) string."""
        return f'({self.left},{self.top},{self.right},{self.bottom})'

    def center(self) -> tuple[int, int]:
        """Get the center point of the bounding box."""
        return (self.left + self.width // 2, self.top + self.height // 2)


@dataclass
class Center:
    """Represents the center point of a UI element."""
    x: int
    y: int

    def to_string(self) -> str:
        """Return as (x, y) string."""
        return f'({self.x},{self.y})'

    def to_list(self) -> list[int]:
        """Return as [x, y] list."""
        return [self.x, self.y]


@dataclass
class TreeElementNode:
    """Represents an interactive UI element in the tree."""
    name: str
    control_type: str
    value: str
    shortcut: str
    bounding_box: BoundingBox
    center: Center
    app_name: str
    is_enabled: bool = True
    is_keyboard_focusable: bool = False

    def to_row(self, index: int) -> list:
        """Convert to table row format."""
        return [
            index,
            self.app_name,
            self.control_type,
            self.name or "''",
            self.value or "''",
            self.shortcut or "None",
            self.center.to_string()
        ]

    def to_dict(self, index: int) -> dict:
        """Convert to dictionary format."""
        return {
            "label": index,
            "app_name": self.app_name,
            "control_type": self.control_type,
            "name": self.name,
            "value": self.value,
            "shortcut": self.shortcut,
            "coordinates": self.center.to_list(),
            "bounding_box": [
                self.bounding_box.left,
                self.bounding_box.top,
                self.bounding_box.right,
                self.bounding_box.bottom
            ],
            "is_enabled": self.is_enabled,
            "is_keyboard_focusable": self.is_keyboard_focusable
        }


@dataclass
class TextElementNode:
    """Represents an informative text element in the tree."""
    name: str
    app_name: str
    control_type: str = "Text"

    def to_row(self) -> list:
        """Convert to table row format."""
        return [self.app_name, self.control_type, self.name or "''"]


@dataclass
class ScrollElementNode:
    """Represents a scrollable UI element in the tree."""
    name: str
    control_type: str
    app_name: str
    bounding_box: BoundingBox
    center: Center
    horizontal_scrollable: bool
    horizontal_scroll_percent: float
    vertical_scrollable: bool
    vertical_scroll_percent: float
    is_focused: bool

    def to_row(self, index: int, base_index: int) -> list:
        """Convert to table row format."""
        return [
            base_index + index,
            self.app_name,
            self.control_type,
            self.name or "''",
            self.center.to_string(),
            "Yes" if self.horizontal_scrollable else "No",
            f"{self.horizontal_scroll_percent:.1f}" if self.horizontal_scrollable else "N/A",
            "Yes" if self.vertical_scrollable else "No",
            f"{self.vertical_scroll_percent:.1f}" if self.vertical_scrollable else "N/A",
            "Yes" if self.is_focused else "No"
        ]

    def to_dict(self, index: int, base_index: int) -> dict:
        """Convert to dictionary format."""
        return {
            "label": base_index + index,
            "app_name": self.app_name,
            "control_type": self.control_type,
            "name": self.name,
            "coordinates": self.center.to_list(),
            "horizontal_scrollable": self.horizontal_scrollable,
            "horizontal_scroll_percent": self.horizontal_scroll_percent,
            "vertical_scrollable": self.vertical_scrollable,
            "vertical_scroll_percent": self.vertical_scroll_percent,
            "is_focused": self.is_focused
        }


@dataclass
class TreeState:
    """Represents the complete UI tree state."""
    interactive_nodes: list[TreeElementNode] = field(default_factory=list)
    informative_nodes: list[TextElementNode] = field(default_factory=list)
    scrollable_nodes: list[ScrollElementNode] = field(default_factory=list)

    def interactive_elements_to_string(self) -> str:
        """Convert interactive elements to formatted table string."""
        if not self.interactive_nodes:
            return "No interactive elements found."

        # Build table manually for better control
        headers = ["Label", "App", "Type", "Name", "Value", "Shortcut", "Coordinates"]
        rows = [node.to_row(idx) for idx, node in enumerate(self.interactive_nodes)]

        # Simple table formatting
        result = " | ".join(headers) + "\n"
        result += "-" * (len(result) - 1) + "\n"
        for row in rows:
            result += " | ".join(str(cell) for cell in row) + "\n"

        return result

    def informative_elements_to_string(self) -> str:
        """Convert informative elements to formatted table string."""
        if not self.informative_nodes:
            return "No informative elements found."

        headers = ["App", "Type", "Name"]
        rows = [node.to_row() for node in self.informative_nodes]

        result = " | ".join(headers) + "\n"
        result += "-" * (len(result) - 1) + "\n"
        for row in rows[:100]:  # Limit to first 100 to avoid spam
            result += " | ".join(str(cell) for cell in row) + "\n"

        if len(rows) > 100:
            result += f"\n... and {len(rows) - 100} more informative elements"

        return result

    def scrollable_elements_to_string(self) -> str:
        """Convert scrollable elements to formatted table string."""
        if not self.scrollable_nodes:
            return "No scrollable elements found."

        headers = [
            "Label", "App", "Type", "Name", "Coordinates",
            "H-Scroll", "H-Pos%", "V-Scroll", "V-Pos%", "Focused"
        ]
        base_index = len(self.interactive_nodes)
        rows = [node.to_row(idx, base_index) for idx, node in enumerate(self.scrollable_nodes)]

        result = " | ".join(headers) + "\n"
        result += "-" * (len(result) - 1) + "\n"
        for row in rows:
            result += " | ".join(str(cell) for cell in row) + "\n"

        return result
