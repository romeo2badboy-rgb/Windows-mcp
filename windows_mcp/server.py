"""
Windows MCP Server - Comprehensive Windows PC automation and control.

This MCP server provides AI with tools to:
- Capture and view the screen
- Control mouse and keyboard
- Manage windows and applications
- Control system operations (restart, shutdown, logout)
- Automate PC tasks
"""

import asyncio
import base64
import io
import os
import subprocess
import sys
import time
from typing import Any, Optional

import mss
import psutil
import pyautogui
from PIL import Image

try:
    import win32api
    import win32con
    import win32gui
    import win32process
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("Warning: pywin32 not available. Some features will be limited.")

try:
    from windows_mcp.desktop.service import Desktop
    from windows_mcp.tree.service import Tree
    DESKTOP_SERVICE_AVAILABLE = True
except ImportError:
    DESKTOP_SERVICE_AVAILABLE = False
    print("Warning: Desktop service not available. State tool will be limited.")

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Configure PyAutoGUI safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# Initialize MCP server
app = Server("windows-mcp-server")

# Initialize desktop service and cached state
desktop_service = Desktop() if DESKTOP_SERVICE_AVAILABLE else None
cached_tree_state = None


# ============================================================================
# SCREEN CAPTURE TOOLS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Windows automation tools."""
    return [
        # Desktop State Tool (MOST IMPORTANT - USE THIS FIRST!)
        Tool(
            name="get_desktop_state",
            description="[CRITICAL] Capture comprehensive desktop state including all interactive UI elements (buttons, links, text fields), informative content (text, labels), and scrollable areas. Each interactive element gets a numbered label for easy reference with click_element/type_element tools. Set use_vision=true to get an annotated screenshot showing element labels. USE THIS TOOL FIRST before any mouse/keyboard actions to understand what's on screen!",
            inputSchema={
                "type": "object",
                "properties": {
                    "use_vision": {
                        "type": "boolean",
                        "description": "Include annotated screenshot with labeled bounding boxes around interactive elements",
                        "default": False
                    },
                    "include_informative": {
                        "type": "boolean",
                        "description": "Include informative text elements (labels, status text, etc.)",
                        "default": True
                    },
                    "include_scrollable": {
                        "type": "boolean",
                        "description": "Include scrollable elements with scroll state",
                        "default": True
                    }
                }
            }
        ),

        # Enhanced Click Tool
        Tool(
            name="click_element",
            description="Click on a UI element using its label from get_desktop_state. More reliable than mouse_click for UI automation. Use the label number from the desktop state.",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "integer",
                        "description": "Element label number from get_desktop_state output"
                    },
                    "button": {
                        "type": "string",
                        "description": "Mouse button to click",
                        "enum": ["left", "right", "middle"],
                        "default": "left"
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of clicks (1=single, 2=double)",
                        "default": 1
                    }
                },
                "required": ["label"]
            }
        ),

        # Enhanced Type Tool
        Tool(
            name="type_into_element",
            description="Type text into a UI element using its label from get_desktop_state. Automatically clicks the element first. More reliable than keyboard_type for filling forms.",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "integer",
                        "description": "Element label number from get_desktop_state output"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into the element"
                    },
                    "clear_first": {
                        "type": "boolean",
                        "description": "Clear existing text before typing (Ctrl+A, Delete)",
                        "default": False
                    },
                    "press_enter": {
                        "type": "boolean",
                        "description": "Press Enter after typing",
                        "default": False
                    }
                },
                "required": ["label", "text"]
            }
        ),

        # Screen Capture Tools
        Tool(
            name="screenshot",
            description="Capture a screenshot of the entire screen or a specific monitor. Returns the image in base64 format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor": {
                        "type": "integer",
                        "description": "Monitor number to capture (0 for all monitors, 1 for primary, etc.)",
                        "default": 1
                    },
                    "save_path": {
                        "type": "string",
                        "description": "Optional path to save the screenshot to disk"
                    }
                }
            }
        ),
        Tool(
            name="get_screen_size",
            description="Get the dimensions of the screen(s)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="locate_on_screen",
            description="Find an image on the screen and return its coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file to locate on screen"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence threshold (0.0 to 1.0)",
                        "default": 0.9
                    }
                },
                "required": ["image_path"]
            }
        ),

        # Mouse Control Tools
        Tool(
            name="mouse_move",
            description="Move the mouse cursor to specific coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate"
                    },
                    "duration": {
                        "type": "number",
                        "description": "Duration of movement in seconds",
                        "default": 0.25
                    }
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="mouse_click",
            description="Click the mouse at current position or specified coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate (optional, uses current position if not provided)"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate (optional, uses current position if not provided)"
                    },
                    "button": {
                        "type": "string",
                        "description": "Mouse button to click",
                        "enum": ["left", "right", "middle"],
                        "default": "left"
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of clicks",
                        "default": 1
                    }
                }
            }
        ),
        Tool(
            name="mouse_scroll",
            description="Scroll the mouse wheel",
            inputSchema={
                "type": "object",
                "properties": {
                    "clicks": {
                        "type": "integer",
                        "description": "Number of scroll clicks (positive for up, negative for down)"
                    }
                },
                "required": ["clicks"]
            }
        ),
        Tool(
            name="get_mouse_position",
            description="Get the current mouse cursor position",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # Keyboard Control Tools
        Tool(
            name="keyboard_type",
            description="Type text using the keyboard",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    },
                    "interval": {
                        "type": "number",
                        "description": "Interval between key presses in seconds",
                        "default": 0.01
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="keyboard_press",
            description="Press a specific key or key combination",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "description": "Key(s) to press (e.g., ['ctrl', 'c'] for copy)",
                        "items": {"type": "string"}
                    }
                },
                "required": ["keys"]
            }
        ),

        # Window Management Tools
        Tool(
            name="list_windows",
            description="List all open windows with their titles and handles",
            inputSchema={
                "type": "object",
                "properties": {
                    "visible_only": {
                        "type": "boolean",
                        "description": "Only list visible windows",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="get_active_window",
            description="Get information about the currently active window",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="activate_window",
            description="Activate (bring to front) a window by title or handle",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title (partial match supported)"
                    },
                    "handle": {
                        "type": "integer",
                        "description": "Window handle (HWND)"
                    }
                }
            }
        ),
        Tool(
            name="close_window",
            description="Close a window by title or handle",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title (partial match supported)"
                    },
                    "handle": {
                        "type": "integer",
                        "description": "Window handle (HWND)"
                    }
                }
            }
        ),
        Tool(
            name="resize_window",
            description="Resize and/or move a window",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title (partial match supported)"
                    },
                    "handle": {
                        "type": "integer",
                        "description": "Window handle (HWND)"
                    },
                    "x": {"type": "integer", "description": "X position"},
                    "y": {"type": "integer", "description": "Y position"},
                    "width": {"type": "integer", "description": "Width"},
                    "height": {"type": "integer", "description": "Height"}
                }
            }
        ),

        # Application Control Tools
        Tool(
            name="launch_application",
            description="Launch an application by path or command",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to executable or command to run"
                    },
                    "args": {
                        "type": "array",
                        "description": "Command line arguments",
                        "items": {"type": "string"}
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory for the application"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="kill_process",
            description="Kill a process by name or PID",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Process name (e.g., 'notepad.exe')"
                    },
                    "pid": {
                        "type": "integer",
                        "description": "Process ID"
                    }
                }
            }
        ),
        Tool(
            name="list_processes",
            description="List all running processes",
            inputSchema={
                "type": "object",
                "properties": {
                    "name_filter": {
                        "type": "string",
                        "description": "Filter processes by name (partial match)"
                    }
                }
            }
        ),

        # System Control Tools
        Tool(
            name="shutdown",
            description="Shutdown the computer",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force shutdown without waiting for applications",
                        "default": False
                    },
                    "delay": {
                        "type": "integer",
                        "description": "Delay in seconds before shutdown",
                        "default": 0
                    }
                }
            }
        ),
        Tool(
            name="restart",
            description="Restart the computer",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force restart without waiting for applications",
                        "default": False
                    },
                    "delay": {
                        "type": "integer",
                        "description": "Delay in seconds before restart",
                        "default": 0
                    }
                }
            }
        ),
        Tool(
            name="logout",
            description="Log out the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Force logout without waiting for applications",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="lock_screen",
            description="Lock the workstation",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_system_info",
            description="Get system information (CPU, memory, disk usage, etc.)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent]:
    """Handle tool execution."""

    # Desktop State Tool
    if name == "get_desktop_state":
        return await tool_get_desktop_state(arguments)
    elif name == "click_element":
        return await tool_click_element(arguments)
    elif name == "type_into_element":
        return await tool_type_into_element(arguments)

    # Screen Capture Tools
    elif name == "screenshot":
        return await tool_screenshot(arguments)
    elif name == "get_screen_size":
        return await tool_get_screen_size(arguments)
    elif name == "locate_on_screen":
        return await tool_locate_on_screen(arguments)

    # Mouse Control Tools
    elif name == "mouse_move":
        return await tool_mouse_move(arguments)
    elif name == "mouse_click":
        return await tool_mouse_click(arguments)
    elif name == "mouse_scroll":
        return await tool_mouse_scroll(arguments)
    elif name == "get_mouse_position":
        return await tool_get_mouse_position(arguments)

    # Keyboard Control Tools
    elif name == "keyboard_type":
        return await tool_keyboard_type(arguments)
    elif name == "keyboard_press":
        return await tool_keyboard_press(arguments)

    # Window Management Tools
    elif name == "list_windows":
        return await tool_list_windows(arguments)
    elif name == "get_active_window":
        return await tool_get_active_window(arguments)
    elif name == "activate_window":
        return await tool_activate_window(arguments)
    elif name == "close_window":
        return await tool_close_window(arguments)
    elif name == "resize_window":
        return await tool_resize_window(arguments)

    # Application Control Tools
    elif name == "launch_application":
        return await tool_launch_application(arguments)
    elif name == "kill_process":
        return await tool_kill_process(arguments)
    elif name == "list_processes":
        return await tool_list_processes(arguments)

    # System Control Tools
    elif name == "shutdown":
        return await tool_shutdown(arguments)
    elif name == "restart":
        return await tool_restart(arguments)
    elif name == "logout":
        return await tool_logout(arguments)
    elif name == "lock_screen":
        return await tool_lock_screen(arguments)
    elif name == "get_system_info":
        return await tool_get_system_info(arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")


# ============================================================================
# DESKTOP STATE TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_get_desktop_state(args: dict) -> list[TextContent | ImageContent]:
    """Get comprehensive desktop state with UI element detection."""
    global cached_tree_state

    if not DESKTOP_SERVICE_AVAILABLE or desktop_service is None:
        return [TextContent(
            type="text",
            text="Error: Desktop service not available. Install uiautomation library."
        )]

    try:
        use_vision = args.get("use_vision", False)
        include_informative = args.get("include_informative", True)
        include_scrollable = args.get("include_scrollable", True)

        # Get the tree service
        tree = Tree(desktop_service)

        # Get the UI tree state
        tree_state = tree.get_state()
        cached_tree_state = tree_state  # Cache for click_element/type_into_element

        # Get system information
        windows_version = desktop_service.get_windows_version()
        default_language = desktop_service.get_default_language()

        # Build the response
        result = []

        # Add system info
        system_info = f"""=== DESKTOP STATE ===

Windows Version: {windows_version}
Default Language: {default_language}
Encoding: {desktop_service.encoding}

"""

        # Add interactive elements (most important!)
        interactive_text = tree_state.interactive_elements_to_string()
        system_info += f"=== INTERACTIVE ELEMENTS ===\n"
        system_info += "(Use these labels with click_element and type_into_element tools)\n\n"
        system_info += interactive_text + "\n\n"

        # Add informative elements if requested
        if include_informative:
            informative_text = tree_state.informative_elements_to_string()
            system_info += f"=== INFORMATIVE ELEMENTS ===\n"
            system_info += informative_text + "\n\n"

        # Add scrollable elements if requested
        if include_scrollable:
            scrollable_text = tree_state.scrollable_elements_to_string()
            system_info += f"=== SCROLLABLE ELEMENTS ===\n"
            system_info += scrollable_text + "\n\n"

        # Add statistics
        system_info += f"=== SUMMARY ===\n"
        system_info += f"Interactive Elements: {len(tree_state.interactive_nodes)}\n"
        system_info += f"Informative Elements: {len(tree_state.informative_nodes)}\n"
        system_info += f"Scrollable Elements: {len(tree_state.scrollable_nodes)}\n"

        result.append(TextContent(type="text", text=system_info))

        # Add annotated screenshot if requested
        if use_vision and tree_state.interactive_nodes:
            try:
                screenshot_bytes = tree.create_annotated_screenshot(
                    tree_state.interactive_nodes,
                    scale=0.7
                )
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                result.append(ImageContent(
                    type="image",
                    data=screenshot_b64,
                    mimeType="image/png"
                ))
                result.append(TextContent(
                    type="text",
                    text="Annotated screenshot showing labeled interactive elements."
                ))
            except Exception as e:
                result.append(TextContent(
                    type="text",
                    text=f"Warning: Could not generate annotated screenshot: {str(e)}"
                ))

        return result

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error getting desktop state: {str(e)}"
        )]


async def tool_click_element(args: dict) -> list[TextContent]:
    """Click on a UI element by its label."""
    global cached_tree_state

    if cached_tree_state is None:
        return [TextContent(
            type="text",
            text="Error: No cached desktop state. Please run get_desktop_state first."
        )]

    try:
        label = args["label"]
        button = args.get("button", "left")
        clicks = args.get("clicks", 1)

        # Find the element by label
        if label < 0 or label >= len(cached_tree_state.interactive_nodes):
            return [TextContent(
                type="text",
                text=f"Error: Invalid label {label}. Valid range: 0-{len(cached_tree_state.interactive_nodes)-1}"
            )]

        element = cached_tree_state.interactive_nodes[label]

        # Click at the element's center
        x, y = element.center.x, element.center.y
        pyautogui.click(x=x, y=y, button=button, clicks=clicks, duration=0.2)

        click_type = "Double-clicked" if clicks == 2 else "Clicked"
        return [TextContent(
            type="text",
            text=f"{click_type} {button} button on element {label}: '{element.name}' "
                 f"({element.control_type}) at ({x},{y}) in app '{element.app_name}'"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error clicking element: {str(e)}")]


async def tool_type_into_element(args: dict) -> list[TextContent]:
    """Type text into a UI element."""
    global cached_tree_state

    if cached_tree_state is None:
        return [TextContent(
            type="text",
            text="Error: No cached desktop state. Please run get_desktop_state first."
        )]

    try:
        label = args["label"]
        text = args["text"]
        clear_first = args.get("clear_first", False)
        press_enter = args.get("press_enter", False)

        # Find the element by label
        if label < 0 or label >= len(cached_tree_state.interactive_nodes):
            return [TextContent(
                type="text",
                text=f"Error: Invalid label {label}. Valid range: 0-{len(cached_tree_state.interactive_nodes)-1}"
            )]

        element = cached_tree_state.interactive_nodes[label]

        # Click the element first to focus it
        x, y = element.center.x, element.center.y
        pyautogui.click(x=x, y=y, duration=0.2)
        time.sleep(0.1)

        # Clear existing text if requested
        if clear_first:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.press('delete')
            time.sleep(0.05)

        # Type the text
        pyautogui.write(text, interval=0.01)

        # Press enter if requested
        if press_enter:
            time.sleep(0.1)
            pyautogui.press('enter')

        action = "Typed (cleared first)" if clear_first else "Typed"
        enter_msg = " and pressed Enter" if press_enter else ""
        return [TextContent(
            type="text",
            text=f"{action} '{text}' into element {label}: '{element.name}' "
                 f"({element.control_type}) in app '{element.app_name}'{enter_msg}"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error typing into element: {str(e)}")]


# ============================================================================
# SCREEN CAPTURE TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_screenshot(args: dict) -> list[TextContent | ImageContent]:
    """Capture a screenshot."""
    try:
        monitor = args.get("monitor", 1)
        save_path = args.get("save_path")

        with mss.mss() as sct:
            if monitor == 0:
                # Capture all monitors
                screenshot = sct.grab(sct.monitors[0])
            else:
                # Capture specific monitor
                if monitor > len(sct.monitors) - 1:
                    return [TextContent(
                        type="text",
                        text=f"Error: Monitor {monitor} not found. Available monitors: {len(sct.monitors) - 1}"
                    )]
                screenshot = sct.grab(sct.monitors[monitor])

            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Save to file if requested
            if save_path:
                img.save(save_path)

            # Convert to base64 for response
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            return [
                ImageContent(
                    type="image",
                    data=img_base64,
                    mimeType="image/png"
                ),
                TextContent(
                    type="text",
                    text=f"Screenshot captured (Monitor {monitor}). Size: {screenshot.width}x{screenshot.height}" +
                         (f"\nSaved to: {save_path}" if save_path else "")
                )
            ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error capturing screenshot: {str(e)}")]


async def tool_get_screen_size(args: dict) -> list[TextContent]:
    """Get screen dimensions."""
    try:
        width, height = pyautogui.size()

        # Also get info about all monitors
        with mss.mss() as sct:
            monitors_info = []
            for i, monitor in enumerate(sct.monitors[1:], 1):
                monitors_info.append(
                    f"Monitor {i}: {monitor['width']}x{monitor['height']} "
                    f"at ({monitor['left']}, {monitor['top']})"
                )

        return [TextContent(
            type="text",
            text=f"Primary screen size: {width}x{height}\n" +
                 "\n".join(monitors_info)
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting screen size: {str(e)}")]


async def tool_locate_on_screen(args: dict) -> list[TextContent]:
    """Locate an image on screen."""
    try:
        image_path = args["image_path"]
        confidence = args.get("confidence", 0.9)

        if not os.path.exists(image_path):
            return [TextContent(type="text", text=f"Error: Image file not found: {image_path}")]

        location = pyautogui.locateOnScreen(image_path, confidence=confidence)

        if location:
            center = pyautogui.center(location)
            return [TextContent(
                type="text",
                text=f"Image found at: ({location.left}, {location.top})\n"
                     f"Size: {location.width}x{location.height}\n"
                     f"Center: ({center.x}, {center.y})"
            )]
        else:
            return [TextContent(type="text", text="Image not found on screen")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error locating image: {str(e)}")]


# ============================================================================
# MOUSE CONTROL TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_mouse_move(args: dict) -> list[TextContent]:
    """Move mouse cursor."""
    try:
        x = args["x"]
        y = args["y"]
        duration = args.get("duration", 0.25)

        pyautogui.moveTo(x, y, duration=duration)
        return [TextContent(type="text", text=f"Mouse moved to ({x}, {y})")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error moving mouse: {str(e)}")]


async def tool_mouse_click(args: dict) -> list[TextContent]:
    """Click mouse."""
    try:
        x = args.get("x")
        y = args.get("y")
        button = args.get("button", "left")
        clicks = args.get("clicks", 1)

        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)
            location = f"at ({x}, {y})"
        else:
            pyautogui.click(clicks=clicks, button=button)
            pos = pyautogui.position()
            location = f"at current position ({pos.x}, {pos.y})"

        click_type = "Double-clicked" if clicks == 2 else "Clicked"
        return [TextContent(type="text", text=f"{click_type} {button} button {location}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error clicking mouse: {str(e)}")]


async def tool_mouse_scroll(args: dict) -> list[TextContent]:
    """Scroll mouse wheel."""
    try:
        clicks = args["clicks"]
        pyautogui.scroll(clicks)
        direction = "up" if clicks > 0 else "down"
        return [TextContent(type="text", text=f"Scrolled {abs(clicks)} clicks {direction}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error scrolling: {str(e)}")]


async def tool_get_mouse_position(args: dict) -> list[TextContent]:
    """Get current mouse position."""
    try:
        x, y = pyautogui.position()
        return [TextContent(type="text", text=f"Mouse position: ({x}, {y})")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting mouse position: {str(e)}")]


# ============================================================================
# KEYBOARD CONTROL TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_keyboard_type(args: dict) -> list[TextContent]:
    """Type text."""
    try:
        text = args["text"]
        interval = args.get("interval", 0.01)

        pyautogui.write(text, interval=interval)
        return [TextContent(type="text", text=f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error typing: {str(e)}")]


async def tool_keyboard_press(args: dict) -> list[TextContent]:
    """Press key(s)."""
    try:
        keys = args["keys"]

        if len(keys) == 1:
            pyautogui.press(keys[0])
            return [TextContent(type="text", text=f"Pressed key: {keys[0]}")]
        else:
            pyautogui.hotkey(*keys)
            return [TextContent(type="text", text=f"Pressed key combination: {'+'.join(keys)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error pressing keys: {str(e)}")]


# ============================================================================
# WINDOW MANAGEMENT TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_list_windows(args: dict) -> list[TextContent]:
    """List all windows."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        visible_only = args.get("visible_only", True)
        windows = []

        def callback(hwnd, extra):
            if visible_only and not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd)
            if title:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    windows.append({
                        "handle": hwnd,
                        "title": title,
                        "pid": pid,
                        "process": process.name()
                    })
                except:
                    windows.append({
                        "handle": hwnd,
                        "title": title
                    })

        win32gui.EnumWindows(callback, None)

        if not windows:
            return [TextContent(type="text", text="No windows found")]

        result = f"Found {len(windows)} window(s):\n\n"
        for w in windows:
            result += f"Handle: {w['handle']}\n"
            result += f"Title: {w['title']}\n"
            if 'process' in w:
                result += f"Process: {w['process']} (PID: {w['pid']})\n"
            result += "\n"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing windows: {str(e)}")]


async def tool_get_active_window(args: dict) -> list[TextContent]:
    """Get active window info."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        rect = win32gui.GetWindowRect(hwnd)

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)

        result = f"Active Window:\n"
        result += f"Handle: {hwnd}\n"
        result += f"Title: {title}\n"
        result += f"Process: {process.name()} (PID: {pid})\n"
        result += f"Position: ({rect[0]}, {rect[1]})\n"
        result += f"Size: {rect[2] - rect[0]}x{rect[3] - rect[1]}"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting active window: {str(e)}")]


async def tool_activate_window(args: dict) -> list[TextContent]:
    """Activate a window."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        handle = args.get("handle")
        title = args.get("title")

        if handle:
            hwnd = handle
        elif title:
            hwnd = None
            def callback(h, extra):
                nonlocal hwnd
                if title.lower() in win32gui.GetWindowText(h).lower():
                    hwnd = h
                    return False
                return True

            win32gui.EnumWindows(callback, None)
            if not hwnd:
                return [TextContent(type="text", text=f"Window not found with title: {title}")]
        else:
            return [TextContent(type="text", text="Error: Must provide either 'handle' or 'title'")]

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)

        window_title = win32gui.GetWindowText(hwnd)
        return [TextContent(type="text", text=f"Activated window: {window_title}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error activating window: {str(e)}")]


async def tool_close_window(args: dict) -> list[TextContent]:
    """Close a window."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        handle = args.get("handle")
        title = args.get("title")

        if handle:
            hwnd = handle
        elif title:
            hwnd = None
            def callback(h, extra):
                nonlocal hwnd
                if title.lower() in win32gui.GetWindowText(h).lower():
                    hwnd = h
                    return False
                return True

            win32gui.EnumWindows(callback, None)
            if not hwnd:
                return [TextContent(type="text", text=f"Window not found with title: {title}")]
        else:
            return [TextContent(type="text", text="Error: Must provide either 'handle' or 'title'")]

        window_title = win32gui.GetWindowText(hwnd)
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

        return [TextContent(type="text", text=f"Closed window: {window_title}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error closing window: {str(e)}")]


async def tool_resize_window(args: dict) -> list[TextContent]:
    """Resize/move a window."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        handle = args.get("handle")
        title = args.get("title")

        if handle:
            hwnd = handle
        elif title:
            hwnd = None
            def callback(h, extra):
                nonlocal hwnd
                if title.lower() in win32gui.GetWindowText(h).lower():
                    hwnd = h
                    return False
                return True

            win32gui.EnumWindows(callback, None)
            if not hwnd:
                return [TextContent(type="text", text=f"Window not found with title: {title}")]
        else:
            return [TextContent(type="text", text="Error: Must provide either 'handle' or 'title'")]

        # Get current rect if some values not provided
        current_rect = win32gui.GetWindowRect(hwnd)

        x = args.get("x", current_rect[0])
        y = args.get("y", current_rect[1])
        width = args.get("width", current_rect[2] - current_rect[0])
        height = args.get("height", current_rect[3] - current_rect[1])

        win32gui.MoveWindow(hwnd, x, y, width, height, True)

        window_title = win32gui.GetWindowText(hwnd)
        return [TextContent(
            type="text",
            text=f"Resized window '{window_title}' to ({x}, {y}) {width}x{height}"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error resizing window: {str(e)}")]


# ============================================================================
# APPLICATION CONTROL TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_launch_application(args: dict) -> list[TextContent]:
    """Launch an application."""
    try:
        path = args["path"]
        cmd_args = args.get("args", [])
        working_dir = args.get("working_dir")

        cmd = [path] + cmd_args

        if working_dir:
            process = subprocess.Popen(cmd, cwd=working_dir)
        else:
            process = subprocess.Popen(cmd)

        return [TextContent(
            type="text",
            text=f"Launched application: {path}\nPID: {process.pid}"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error launching application: {str(e)}")]


async def tool_kill_process(args: dict) -> list[TextContent]:
    """Kill a process."""
    try:
        name = args.get("name")
        pid = args.get("pid")

        if pid:
            process = psutil.Process(pid)
            process_name = process.name()
            process.kill()
            return [TextContent(type="text", text=f"Killed process: {process_name} (PID: {pid})")]
        elif name:
            killed = []
            for proc in psutil.process_iter(['pid', 'name']):
                if name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed.append(f"{proc.info['name']} (PID: {proc.info['pid']})")

            if killed:
                return [TextContent(
                    type="text",
                    text=f"Killed {len(killed)} process(es):\n" + "\n".join(killed)
                )]
            else:
                return [TextContent(type="text", text=f"No processes found matching: {name}")]
        else:
            return [TextContent(type="text", text="Error: Must provide either 'name' or 'pid'")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error killing process: {str(e)}")]


async def tool_list_processes(args: dict) -> list[TextContent]:
    """List running processes."""
    try:
        name_filter = args.get("name_filter", "").lower()

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if name_filter and name_filter not in proc.info['name'].lower():
                    continue
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)

        # Limit to top 50
        processes = processes[:50]

        result = f"Found {len(processes)} process(es)" + (f" matching '{name_filter}'" if name_filter else "") + ":\n\n"

        for p in processes:
            result += f"PID: {p['pid']:6d} | {p['name']:30s} | "
            result += f"CPU: {p.get('cpu_percent', 0):5.1f}% | "
            result += f"MEM: {p.get('memory_percent', 0):5.1f}%\n"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing processes: {str(e)}")]


# ============================================================================
# SYSTEM CONTROL TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_shutdown(args: dict) -> list[TextContent]:
    """Shutdown the computer."""
    try:
        force = args.get("force", False)
        delay = args.get("delay", 0)

        if sys.platform == "win32":
            cmd = ["shutdown", "/s", "/t", str(delay)]
            if force:
                cmd.append("/f")
            subprocess.run(cmd)
            return [TextContent(
                type="text",
                text=f"Shutdown initiated (delay: {delay}s, force: {force})"
            )]
        else:
            return [TextContent(type="text", text="Error: Shutdown only supported on Windows")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error initiating shutdown: {str(e)}")]


async def tool_restart(args: dict) -> list[TextContent]:
    """Restart the computer."""
    try:
        force = args.get("force", False)
        delay = args.get("delay", 0)

        if sys.platform == "win32":
            cmd = ["shutdown", "/r", "/t", str(delay)]
            if force:
                cmd.append("/f")
            subprocess.run(cmd)
            return [TextContent(
                type="text",
                text=f"Restart initiated (delay: {delay}s, force: {force})"
            )]
        else:
            return [TextContent(type="text", text="Error: Restart only supported on Windows")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error initiating restart: {str(e)}")]


async def tool_logout(args: dict) -> list[TextContent]:
    """Logout current user."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        force = args.get("force", False)
        flags = win32con.EWX_LOGOFF
        if force:
            flags |= win32con.EWX_FORCE

        win32api.ExitWindowsEx(flags, 0)
        return [TextContent(type="text", text=f"Logout initiated (force: {force})")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error initiating logout: {str(e)}")]


async def tool_lock_screen(args: dict) -> list[TextContent]:
    """Lock the workstation."""
    if not WINDOWS_AVAILABLE:
        return [TextContent(type="text", text="Error: Windows API not available")]

    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return [TextContent(type="text", text="Workstation locked")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error locking workstation: {str(e)}")]


async def tool_get_system_info(args: dict) -> list[TextContent]:
    """Get system information."""
    try:
        import platform

        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory info
        mem = psutil.virtual_memory()

        # Disk info
        disk = psutil.disk_usage('/')

        # System info
        boot_time = psutil.boot_time()

        result = "=== SYSTEM INFORMATION ===\n\n"

        result += f"Platform: {platform.system()} {platform.release()}\n"
        result += f"Machine: {platform.machine()}\n"
        result += f"Processor: {platform.processor()}\n\n"

        result += f"CPU Usage: {cpu_percent}%\n"
        result += f"CPU Cores: {cpu_count}\n"
        if cpu_freq:
            result += f"CPU Frequency: {cpu_freq.current:.2f} MHz\n\n"

        result += f"Memory Total: {mem.total / (1024**3):.2f} GB\n"
        result += f"Memory Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)\n"
        result += f"Memory Available: {mem.available / (1024**3):.2f} GB\n\n"

        result += f"Disk Total: {disk.total / (1024**3):.2f} GB\n"
        result += f"Disk Used: {disk.used / (1024**3):.2f} GB ({disk.percent}%)\n"
        result += f"Disk Free: {disk.free / (1024**3):.2f} GB\n\n"

        result += f"Boot Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))}\n"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting system info: {str(e)}")]


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Run the Windows MCP server."""
    import sys
    from mcp.server.stdio import stdio_server

    print("Starting Windows MCP Server...", file=sys.stderr)
    print(f"Platform: {sys.platform}", file=sys.stderr)
    print(f"Python: {sys.version}", file=sys.stderr)

    if not WINDOWS_AVAILABLE:
        print("WARNING: pywin32 not available, some features will be limited", file=sys.stderr)

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
