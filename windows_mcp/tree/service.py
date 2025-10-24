"""Service for traversing and analyzing the UI tree."""

import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

try:
    import uiautomation as ua
    from uiautomation import Control, GetRootControl, ScrollPattern
    UIAUTOMATION_AVAILABLE = True
except ImportError:
    UIAUTOMATION_AVAILABLE = False
    print("Warning: uiautomation not available. State tool will have limited functionality.")

from windows_mcp.tree.config import (
    INTERACTIVE_CONTROL_TYPE_NAMES,
    INFORMATIVE_CONTROL_TYPE_NAMES,
    DEFAULT_ACTIONS,
    MIN_ELEMENT_AREA,
    THREAD_MAX_RETRIES,
    ANNOTATION_FONT_SIZE,
    ANNOTATION_PADDING
)
from windows_mcp.tree.views import (
    TreeState,
    TreeElementNode,
    TextElementNode,
    ScrollElementNode,
    BoundingBox,
    Center
)

if TYPE_CHECKING:
    from windows_mcp.desktop.service import Desktop

# Configure logging
logger = logging.getLogger('windows-mcp.tree')


class Tree:
    """Handles UI tree traversal and element detection."""

    def __init__(self, desktop: 'Desktop'):
        """Initialize the tree service.

        Args:
            desktop: Desktop service instance
        """
        self.desktop = desktop
        self.screen_size = self.desktop.get_screen_size()
        self._element_cache = {}  # Cache for faster lookups
        self._last_scan_time = 0

    def get_state(self, force_refresh: bool = False) -> TreeState:
        """Get the current UI tree state with caching.

        Args:
            force_refresh: Force a full rescan even if cache is valid

        Returns:
            TreeState object containing interactive, informative, and scrollable elements
        """
        if not UIAUTOMATION_AVAILABLE:
            logger.warning("UIAutomation not available, returning empty state")
            return TreeState()

        try:
            import time
            current_time = time.time()

            # Use cache if less than 2 seconds old and not forced
            if not force_refresh and (current_time - self._last_scan_time) < 2.0:
                logger.debug("Using cached tree state")
                return self._cached_state if hasattr(self, '_cached_state') else self._scan_tree()

            logger.info("Scanning UI tree...")
            state = self._scan_tree()
            self._cached_state = state
            self._last_scan_time = current_time

            logger.info(
                f"Tree scan complete: {len(state.interactive_nodes)} interactive, "
                f"{len(state.informative_nodes)} informative, "
                f"{len(state.scrollable_nodes)} scrollable elements"
            )

            return state

        except Exception as e:
            logger.error(f"Error getting tree state: {e}", exc_info=True)
            return TreeState()

    def _scan_tree(self) -> TreeState:
        """Perform a full tree scan."""
        root = GetRootControl()
        interactive_nodes, informative_nodes, scrollable_nodes = self._get_appwise_nodes(root)

        return TreeState(
            interactive_nodes=interactive_nodes,
            informative_nodes=informative_nodes,
            scrollable_nodes=scrollable_nodes
        )

    def _get_appwise_nodes(
        self, node: Control
    ) -> tuple[list[TreeElementNode], list[TextElementNode], list[ScrollElementNode]]:
        """Get nodes organized by application.

        Args:
            node: Root control to start from

        Returns:
            Tuple of (interactive_nodes, informative_nodes, scrollable_nodes)
        """
        from windows_mcp.desktop.config import EXCLUDED_APPS, AVOIDED_APPS

        apps: list[Control] = []
        found_foreground_app = False

        # Get all application windows
        for app in node.GetChildren():
            if app.ClassName in EXCLUDED_APPS:
                apps.append(app)
            elif app.ClassName not in AVOIDED_APPS and self.desktop.is_app_visible(app):
                if not found_foreground_app:
                    apps.append(app)
                    found_foreground_app = True

        interactive_nodes, informative_nodes, scrollable_nodes = [], [], []

        # Process apps in parallel with retries
        with ThreadPoolExecutor() as executor:
            retry_counts = {app: 0 for app in apps}
            future_to_app = {
                executor.submit(self._get_nodes, app, self.desktop.is_app_browser(app)): app
                for app in apps
            }

            while future_to_app:
                for future in as_completed(list(future_to_app)):
                    app = future_to_app.pop(future)
                    try:
                        result = future.result()
                        if result:
                            i_nodes, t_nodes, s_nodes = result
                            interactive_nodes.extend(i_nodes)
                            informative_nodes.extend(t_nodes)
                            scrollable_nodes.extend(s_nodes)
                    except Exception as e:
                        retry_counts[app] += 1
                        if retry_counts[app] < THREAD_MAX_RETRIES:
                            new_future = executor.submit(
                                self._get_nodes, app, self.desktop.is_app_browser(app)
                            )
                            future_to_app[new_future] = app

        return interactive_nodes, informative_nodes, scrollable_nodes

    def _get_nodes(
        self, node: Control, is_browser: bool = False
    ) -> tuple[list[TreeElementNode], list[TextElementNode], list[ScrollElementNode]]:
        """Extract nodes from a UI element tree.

        Args:
            node: Control to extract nodes from
            is_browser: Whether this is a browser application

        Returns:
            Tuple of (interactive_nodes, informative_nodes, scrollable_nodes)
        """
        interactive_nodes = []
        informative_nodes = []
        scrollable_nodes = []

        app_name = node.Name.strip() or "Unknown"

        # Map special class names to friendly names
        class_name_map = {
            "Progman": "Desktop",
            "Shell_TrayWnd": "Taskbar",
            "Shell_SecondaryTrayWnd": "Taskbar",
            "Microsoft.UI.Content.PopupWindowSiteBridge": "Context Menu"
        }
        app_name = class_name_map.get(node.ClassName, app_name)

        def tree_traversal(current_node: Control, depth: int = 0):
            """Recursively traverse the UI tree."""
            if depth > 20:  # Prevent infinite recursion
                return

            # Check if element is scrollable
            if self._is_element_scrollable(current_node):
                scroll_pattern = current_node.GetScrollPattern()
                box = current_node.BoundingRectangle
                if not box.isempty():
                    x, y = box.xcenter(), box.ycenter()
                    scrollable_nodes.append(ScrollElementNode(
                        name=current_node.Name.strip() or current_node.LocalizedControlType or "Scrollable",
                        app_name=app_name,
                        control_type=current_node.LocalizedControlType or "Unknown",
                        bounding_box=BoundingBox(
                            left=box.left, top=box.top,
                            right=box.right, bottom=box.bottom,
                            width=box.width(), height=box.height()
                        ),
                        center=Center(x=x, y=y),
                        horizontal_scrollable=scroll_pattern.HorizontallyScrollable,
                        horizontal_scroll_percent=scroll_pattern.HorizontalScrollPercent
                            if scroll_pattern.HorizontallyScrollable else 0,
                        vertical_scrollable=scroll_pattern.VerticallyScrollable,
                        vertical_scroll_percent=scroll_pattern.VerticalScrollPercent
                            if scroll_pattern.VerticallyScrollable else 0,
                        is_focused=current_node.HasKeyboardFocus
                    ))

            # Check if element is interactive
            elif self._is_element_interactive(current_node):
                legacy_pattern = current_node.GetLegacyIAccessiblePattern()
                value = ""
                try:
                    value = legacy_pattern.Value.strip() if legacy_pattern.Value else ""
                except:
                    pass

                box = current_node.BoundingRectangle
                if not box.isempty():
                    x, y = box.xcenter(), box.ycenter()
                    interactive_nodes.append(TreeElementNode(
                        name=current_node.Name.strip() or current_node.LocalizedControlType or "",
                        control_type=current_node.LocalizedControlType or "Unknown",
                        value=value,
                        shortcut=current_node.AcceleratorKey or "",
                        bounding_box=BoundingBox(
                            left=box.left, top=box.top,
                            right=box.right, bottom=box.bottom,
                            width=box.width(), height=box.height()
                        ),
                        center=Center(x=x, y=y),
                        app_name=app_name,
                        is_enabled=current_node.IsEnabled,
                        is_keyboard_focusable=current_node.IsKeyboardFocusable
                    ))

            # Check if element is informative
            elif self._is_element_text(current_node):
                informative_nodes.append(TextElementNode(
                    name=current_node.Name.strip() or "",
                    app_name=app_name,
                    control_type=current_node.LocalizedControlType or "Text"
                ))

            # Recursively process children
            try:
                for child in current_node.GetChildren():
                    tree_traversal(child, depth + 1)
            except:
                pass

        tree_traversal(node)
        return interactive_nodes, informative_nodes, scrollable_nodes

    def _is_element_visible(self, node: Control, threshold: int = MIN_ELEMENT_AREA) -> bool:
        """Check if element is visible."""
        try:
            box = node.BoundingRectangle
            if box.isempty():
                return False
            area = box.width() * box.height()
            is_offscreen = not node.IsOffscreen or node.ControlTypeName in ['EditControl']
            return area > threshold and is_offscreen and node.IsControlElement
        except:
            return False

    def _is_element_enabled(self, node: Control) -> bool:
        """Check if element is enabled."""
        try:
            return node.IsEnabled
        except:
            return False

    def _is_element_interactive(self, node: Control) -> bool:
        """Check if element is interactive."""
        try:
            if node.ControlTypeName in INTERACTIVE_CONTROL_TYPE_NAMES:
                return (
                    self._is_element_visible(node) and
                    self._is_element_enabled(node)
                )
            return False
        except:
            return False

    def _is_element_text(self, node: Control) -> bool:
        """Check if element is informative text."""
        try:
            if node.ControlTypeName in INFORMATIVE_CONTROL_TYPE_NAMES:
                return (
                    self._is_element_visible(node) and
                    self._is_element_enabled(node) and
                    bool(node.Name.strip())
                )
            return False
        except:
            return False

    def _is_element_scrollable(self, node: Control) -> bool:
        """Check if element is scrollable."""
        try:
            scroll_pattern: ScrollPattern = node.GetScrollPattern()
            return scroll_pattern.VerticallyScrollable or scroll_pattern.HorizontallyScrollable
        except:
            return False

    def create_annotated_screenshot(
        self, nodes: list[TreeElementNode], scale: float = 0.7
    ) -> bytes:
        """Create an annotated screenshot with labeled bounding boxes.

        Args:
            nodes: List of interactive elements to annotate
            scale: Scale factor for the screenshot

        Returns:
            PNG image bytes with annotations
        """
        screenshot = self.desktop.get_screenshot(scale=scale)

        # Add padding
        width = screenshot.width + (2 * ANNOTATION_PADDING)
        height = screenshot.height + (2 * ANNOTATION_PADDING)
        padded_screenshot = Image.new("RGB", (width, height), color=(255, 255, 255))
        padded_screenshot.paste(screenshot, (ANNOTATION_PADDING, ANNOTATION_PADDING))

        draw = ImageDraw.Draw(padded_screenshot)

        try:
            font = ImageFont.truetype('arial.ttf', ANNOTATION_FONT_SIZE)
        except IOError:
            font = ImageFont.load_default()

        def get_random_color() -> str:
            """Generate a random color for annotations."""
            return "#{:06x}".format(random.randint(0, 0xFFFFFF))

        def draw_annotation(label: int, node: TreeElementNode):
            """Draw annotation for a single element."""
            box = node.bounding_box
            color = get_random_color()

            # Scale and pad the bounding box
            adjusted_box = (
                int(box.left * scale) + ANNOTATION_PADDING,
                int(box.top * scale) + ANNOTATION_PADDING,
                int(box.right * scale) + ANNOTATION_PADDING,
                int(box.bottom * scale) + ANNOTATION_PADDING
            )

            # Draw bounding box
            draw.rectangle(adjusted_box, outline=color, width=2)

            # Label dimensions
            label_text = str(label)
            bbox = draw.textbbox((0, 0), label_text, font=font)
            label_width = bbox[2] - bbox[0]
            label_height = bbox[3] - bbox[1]

            left, top, right, bottom = adjusted_box

            # Label position above bounding box
            label_x1 = right - label_width - 4
            label_y1 = top - label_height - 6
            label_x2 = label_x1 + label_width + 4
            label_y2 = label_y1 + label_height + 6

            # Draw label background and text
            draw.rectangle([(label_x1, label_y1), (label_x2, label_y2)], fill=color)
            draw.text((label_x1 + 2, label_y1 + 2), label_text, fill=(255, 255, 255), font=font)

        # Draw all annotations
        for idx, node in enumerate(nodes):
            try:
                draw_annotation(idx, node)
            except:
                pass

        # Convert to bytes
        buffer = BytesIO()
        padded_screenshot.save(buffer, format='PNG')
        return buffer.getvalue()
