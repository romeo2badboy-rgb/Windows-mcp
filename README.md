# Windows MCP Server

A comprehensive Model Context Protocol (MCP) server that enables AI assistants to control and automate Windows PCs. This server provides full PC automation capabilities including screen capture, mouse/keyboard control, window management, application control, and system operations.

## Features

### Screen Capture & Vision
- **Screenshot**: Capture full screen or specific monitors
- **Screen Size Detection**: Get screen dimensions and monitor information
- **Image Location**: Find images on screen with confidence matching

### Mouse Control
- **Mouse Movement**: Move cursor to specific coordinates with smooth motion
- **Mouse Clicking**: Left, right, middle clicks with single/double-click support
- **Mouse Scrolling**: Scroll up/down with precise control
- **Position Tracking**: Get current mouse cursor position

### Keyboard Control
- **Text Typing**: Type text with configurable speed
- **Key Pressing**: Press individual keys or key combinations (Ctrl+C, Alt+Tab, etc.)

### Window Management
- **List Windows**: View all open windows with titles and process information
- **Get Active Window**: Get information about the currently focused window
- **Activate Window**: Bring specific windows to the front
- **Close Window**: Close windows by title or handle
- **Resize/Move Windows**: Reposition and resize windows programmatically

### Application Control
- **Launch Applications**: Start programs with arguments and working directory
- **Kill Processes**: Terminate processes by name or PID
- **List Processes**: View running processes with CPU and memory usage

### System Control
- **Shutdown**: Power off the computer with optional delay
- **Restart**: Reboot the system with optional delay
- **Logout**: Log out the current user
- **Lock Screen**: Lock the workstation
- **System Information**: Get CPU, memory, disk usage, and system details

## Installation

### Prerequisites
- **Windows 10/11** (required for full functionality)
- **Python 3.10+**
- **Administrator privileges** (recommended for full system control)

### Step 1: Install Python Dependencies

```bash
# Clone or navigate to the repository
cd Windows-mcp

# Install the package and dependencies
pip install -e .
```

### Step 2: Install System Dependencies

Some features require additional system tools:

1. **Tesseract OCR** (optional, for OCR features):
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Add to PATH

### Step 3: Configure with Claude Desktop

Add this to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "windows-control": {
      "command": "python",
      "args": [
        "-m",
        "windows_mcp.server"
      ]
    }
  }
}
```

Or if you installed it as a package:

```json
{
  "mcpServers": {
    "windows-control": {
      "command": "windows-mcp"
    }
  }
}
```

### Step 4: Restart Claude Desktop

After adding the configuration, restart Claude Desktop to load the MCP server.

## Usage Examples

### Basic Automation Example

```
User: "Take a screenshot of my screen and save it to Desktop"

AI: [Uses screenshot tool with save_path parameter]

User: "Open Notepad and type 'Hello World'"

AI: [Uses launch_application to open notepad.exe, then keyboard_type to type the text]

User: "Click the Start button and then type 'calculator'"

AI: [Uses mouse_click at Start button coordinates, then keyboard_type to search]
```

### Advanced Automation Example

```
User: "List all Chrome windows, activate the first one, then take a screenshot"

AI: [Uses list_windows to find Chrome windows, activate_window to bring it to front,
     then screenshot to capture the screen]

User: "Show me system information and kill any processes using more than 50% CPU"

AI: [Uses get_system_info to show system status, list_processes to find high CPU
     processes, then kill_process to terminate them]
```

### System Control Example

```
User: "Lock my screen"

AI: [Uses lock_screen tool]

User: "Restart my computer in 60 seconds"

AI: [Uses restart tool with delay parameter set to 60]
```

## Available Tools

### Screen Capture
- `screenshot` - Capture screen with optional monitor selection
- `get_screen_size` - Get screen dimensions
- `locate_on_screen` - Find image on screen

### Mouse Control
- `mouse_move` - Move cursor to coordinates
- `mouse_click` - Click mouse buttons
- `mouse_scroll` - Scroll mouse wheel
- `get_mouse_position` - Get cursor position

### Keyboard Control
- `keyboard_type` - Type text
- `keyboard_press` - Press keys or key combinations

### Window Management
- `list_windows` - List all open windows
- `get_active_window` - Get active window info
- `activate_window` - Activate a window
- `close_window` - Close a window
- `resize_window` - Resize/move a window

### Application Control
- `launch_application` - Launch programs
- `kill_process` - Kill processes
- `list_processes` - List running processes

### System Control
- `shutdown` - Shutdown computer
- `restart` - Restart computer
- `logout` - Logout current user
- `lock_screen` - Lock workstation
- `get_system_info` - Get system information

## Safety Features

1. **PyAutoGUI Failsafe**: Move mouse to top-left corner to abort automation
2. **Confirmation for Destructive Actions**: System control actions should be confirmed
3. **Error Handling**: All tools include comprehensive error handling
4. **Process Protection**: Prevents accidental system process termination

## Security Considerations

This MCP server provides powerful system control capabilities. Consider the following:

1. **Run with appropriate permissions**: Don't run as administrator unless necessary
2. **Review automation requests**: Understand what the AI will do before confirming
3. **Use in trusted environments**: Only use with trusted AI assistants
4. **Monitor system changes**: Keep track of automated actions
5. **Backup important data**: Before using system control features

## Troubleshooting

### "Windows API not available" Error
- Install pywin32: `pip install pywin32`
- Run post-install script: `python Scripts/pywin32_postinstall.py -install`

### Screenshot Not Working
- Check if mss is installed: `pip install mss`
- Verify screen permissions on Windows 11

### Mouse/Keyboard Control Not Working
- Install PyAutoGUI: `pip install pyautogui`
- Disable "Enhanced Pointer Precision" in Windows mouse settings for better accuracy

### Permission Errors
- Run Claude Desktop as administrator (only if necessary)
- Check Windows UAC settings

## Development

### Project Structure
```
Windows-mcp/
├── windows_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server implementation
├── pyproject.toml         # Python package configuration
├── package.json           # NPM package configuration
└── README.md              # This file
```

### Adding New Tools

1. Add tool definition in `list_tools()`
2. Add handler in `call_tool()`
3. Implement tool function following the pattern
4. Test thoroughly before deployment

### Testing

```bash
# Test the server directly
python -m windows_mcp.server

# Test with MCP inspector (if available)
mcp-inspector windows-mcp
```

## Dependencies

- **mcp** - Model Context Protocol SDK
- **pillow** - Image processing
- **pyautogui** - Mouse and keyboard automation
- **pywin32** - Windows API access
- **psutil** - Process and system utilities
- **mss** - Fast screenshot capture
- **pytesseract** - OCR (optional)
- **opencv-python** - Image processing

## Contributing

Contributions are welcome! Please ensure:
1. Code follows existing patterns
2. All tools include error handling
3. Documentation is updated
4. Security considerations are addressed

## License

MIT License - See LICENSE file for details

## Disclaimer

This software provides powerful system control capabilities. Users are responsible for:
- Understanding the actions performed by AI assistants
- Protecting their systems from unauthorized access
- Backing up important data before automation
- Complying with local laws and regulations

The authors are not responsible for any damages caused by misuse of this software.

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/Windows-mcp/issues)
- Documentation: This README
- MCP Documentation: https://modelcontextprotocol.io

## Changelog

### v0.1.0 (Initial Release)
- Complete screen capture system
- Full mouse and keyboard control
- Window management capabilities
- Application control
- System control (shutdown, restart, logout, lock)
- Process management
- System information retrieval

## Roadmap

Future enhancements:
- [ ] File system operations
- [ ] Clipboard management
- [ ] Registry access
- [ ] Network operations
- [ ] Task scheduling
- [ ] Custom macro recording/playback
- [ ] Multi-monitor advanced support
- [ ] Voice control integration
- [ ] AI vision-based screen analysis

---

**Made with AI automation in mind** 🤖
