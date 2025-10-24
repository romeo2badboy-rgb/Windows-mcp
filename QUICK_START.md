# Windows MCP Server - Quick Start Guide

## 🚀 Installation

```bash
cd Windows-mcp
pip install -e .
```

Add to Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "windows-control": {
      "command": "python",
      "args": ["-m", "windows_mcp.server"]
    }
  }
}
```

Restart Claude Desktop.

## 🎯 Smart UI Automation (Recommended!)

### Step 1: See What's on Screen

```
Ask Claude: "Show me all the interactive elements on screen"
```

Claude will use `get_desktop_state` and show you:
- All buttons, links, text fields numbered with labels
- Scrollable areas
- Text content
- Optionally: annotated screenshot with bounding boxes

### Step 2: Interact by Label

```
Ask Claude: "Click element 5"
Ask Claude: "Type 'hello' into element 7"
Ask Claude: "Fill the form - email in element 3, password in element 4, then click element 6"
```

Claude will use:
- `click_element(label=5)` - Clicks button/link at label 5
- `type_into_element(label=7, text='hello')` - Types into text field at label 7

## 💡 Why Use Smart UI Automation?

### ❌ Old Way (Coordinates)
```
"Click at position (450, 300)"  → Breaks if window moves!
```

### ✅ New Way (Semantic)
```
"Click element 5 (Login button)"  → Always works!
```

## 🔧 All Available Tools

### Smart UI Automation
- `get_desktop_state` - See all UI elements with labels
- `click_element` - Click by label number
- `type_into_element` - Type into by label number

### Screen Capture
- `screenshot` - Capture screen image
- `get_screen_size` - Get dimensions
- `locate_on_screen` - Find image on screen

### Mouse & Keyboard
- `mouse_move` - Move cursor
- `mouse_click` - Click mouse
- `mouse_scroll` - Scroll
- `keyboard_type` - Type text
- `keyboard_press` - Press keys

### Window Management
- `list_windows` - Show all windows
- `activate_window` - Switch to window
- `close_window` - Close window
- `resize_window` - Resize/move window

### Application Control
- `launch_application` - Start apps
- `kill_process` - Stop processes
- `list_processes` - Show running apps

### System Control
- `shutdown` - Power off
- `restart` - Reboot
- `logout` - Sign out
- `lock_screen` - Lock PC
- `get_system_info` - System stats

## 📝 Example Workflows

### Fill a Form
```
1. "Show me the desktop state with vision"
   → See annotated screenshot with labels
2. "Type my email into element 3"
   → Fills email field
3. "Type my password into element 4"
   → Fills password field
4. "Click element 5"
   → Clicks login button
```

### Automate Chrome
```
1. "Get desktop state"
   → See all Chrome UI elements
2. "Click the address bar (element 12)"
3. "Type 'github.com' and press enter"
4. "Click the search button (element 8)"
```

### System Automation
```
1. "Launch Calculator"
2. "Get desktop state to see calculator buttons"
3. "Click element 5, 7, 3, 9" (for 5+7=)
4. "Take a screenshot of the result"
```

## 🎓 Pro Tips

1. **Always use `get_desktop_state` first** - Know what's on screen before clicking
2. **Use vision mode** (`use_vision=true`) when you need to see exact locations
3. **Element labels are cached** - Run `get_desktop_state` again if UI changes
4. **Check element type** - Text fields, buttons, links all shown in state
5. **Scrollable elements** are listed separately with scroll position

## 🐛 Troubleshooting

**"No cached desktop state"**
→ Run `get_desktop_state` first

**"Invalid label"**
→ Check the label is in range (0 to N-1)

**"Desktop service not available"**
→ Install uiautomation: `pip install uiautomation`

**Element not found**
→ UI changed, run `get_desktop_state` again

## 📚 Learn More

- Full documentation: README.md
- Examples: examples/automation_examples.md
- MCP docs: https://modelcontextprotocol.io

---

**Happy Automating!** 🤖
