"""Data models for desktop state and applications."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Status(Enum):
    """Window status states."""
    MAXIMIZED = 'Maximized'
    MINIMIZED = 'Minimized'
    NORMAL = 'Normal'
    HIDDEN = 'Hidden'


@dataclass
class Size:
    """Represents window/screen dimensions."""
    width: int
    height: int

    def to_string(self) -> str:
        """Return as WxH string."""
        return f'{self.width}x{self.height}'

    def area(self) -> int:
        """Calculate area."""
        return self.width * self.height


@dataclass
class App:
    """Represents a running application window."""
    name: str
    depth: int
    status: Status
    size: Size
    handle: int
    process_id: Optional[int] = None
    process_name: Optional[str] = None

    def to_row(self) -> list:
        """Convert to table row format."""
        return [
            self.name,
            self.depth,
            self.status.value,
            self.size.width,
            self.size.height,
            self.handle
        ]
