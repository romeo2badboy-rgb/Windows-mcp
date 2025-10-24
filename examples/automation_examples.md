# Windows MCP Server - Automation Examples

This document provides practical examples of how to use the Windows MCP Server for various automation tasks.

## Basic Tasks

### Taking Screenshots

**Example 1: Capture primary screen**
```
User: "Take a screenshot"
AI: Uses screenshot tool with default monitor (1)
```

**Example 2: Capture and save**
```
User: "Take a screenshot and save it to C:\Users\YourName\Desktop\screenshot.png"
AI: Uses screenshot tool with save_path parameter
```

**Example 3: Capture all monitors**
```
User: "Capture all my monitors"
AI: Uses screenshot tool with monitor=0
```

## Mouse & Keyboard Automation

### Opening and Controlling Applications

**Example 1: Open Notepad and type**
```
User: "Open Notepad and type 'Meeting notes for today'"
Steps:
1. AI uses launch_application with path="notepad.exe"
2. AI waits briefly for window to open
3. AI uses keyboard_type with text="Meeting notes for today"
```

**Example 2: Use keyboard shortcuts**
```
User: "Copy the selected text"
Steps:
1. AI uses keyboard_press with keys=["ctrl", "c"]
```

**Example 3: Complex mouse interaction**
```
User: "Move mouse to (500, 300) and double-click"
Steps:
1. AI uses mouse_move with x=500, y=300
2. AI uses mouse_click with clicks=2
```

## Window Management

### Managing Multiple Windows

**Example 1: List all windows**
```
User: "Show me all open windows"
AI: Uses list_windows to display all windows with their titles and processes
```

**Example 2: Activate specific window**
```
User: "Switch to Chrome"
Steps:
1. AI uses list_windows to find Chrome window
2. AI uses activate_window with title="Chrome"
```

**Example 3: Organize windows**
```
User: "Move the Calculator window to the top-left corner and resize it to 400x600"
Steps:
1. AI uses resize_window with title="Calculator", x=0, y=0, width=400, height=600
```

## Application Management

### Process Control

**Example 1: Find resource-heavy processes**
```
User: "Show me which programs are using the most CPU"
Steps:
1. AI uses list_processes (which returns sorted by CPU usage)
2. AI displays top processes
```

**Example 2: Kill specific process**
```
User: "Close all instances of notepad"
Steps:
1. AI uses kill_process with name="notepad.exe"
```

**Example 3: Launch with arguments**
```
User: "Open Chrome in incognito mode"
Steps:
1. AI uses launch_application with path="chrome.exe" and args=["--incognito"]
```

## Advanced Automation Workflows

### Workflow 1: Screenshot + Analysis

```
User: "Take a screenshot and tell me what applications are visible"
Steps:
1. AI uses screenshot to capture screen
2. AI analyzes the image (using vision capabilities)
3. AI uses list_windows to correlate with open windows
4. AI provides detailed report
```

### Workflow 2: System Cleanup

```
User: "Show me system status and close any Chrome tabs using lots of memory"
Steps:
1. AI uses get_system_info to check memory usage
2. AI uses list_processes with name_filter="chrome"
3. AI identifies high-memory Chrome processes
4. AI uses kill_process on specific PIDs
5. AI confirms cleanup with updated system status
```

### Workflow 3: Automated Work Session

```
User: "Set up my work environment: open VS Code, Chrome, and Terminal"
Steps:
1. AI uses launch_application for "code.exe" (VS Code)
2. AI uses launch_application for "chrome.exe"
3. AI uses launch_application for "wt.exe" (Windows Terminal)
4. AI uses resize_window to arrange windows in optimal layout
```

### Workflow 4: Presentation Mode

```
User: "Prepare for presentation: close all apps except PowerPoint, set to fullscreen"
Steps:
1. AI uses list_windows to get all windows
2. AI uses close_window to close non-PowerPoint windows
3. AI uses activate_window to focus PowerPoint
4. AI uses keyboard_press with keys=["f5"] to start slideshow
```

## System Control

### Safe System Operations

**Example 1: Scheduled restart**
```
User: "Restart my computer in 10 minutes"
Steps:
1. AI uses restart with delay=600 (10 minutes * 60 seconds)
2. AI confirms the scheduled restart
```

**Example 2: Lock workstation**
```
User: "Lock my screen"
Steps:
1. AI uses lock_screen
2. System immediately locks
```

**Example 3: System information**
```
User: "Check my computer's performance"
Steps:
1. AI uses get_system_info
2. AI presents CPU, memory, disk usage in readable format
```

## Safety Tips

1. **Test First**: Always test automation on non-critical tasks first
2. **Confirm Actions**: Review what the AI plans to do before execution
3. **Save Work**: Save important work before system control operations
4. **Failsafe**: Remember PyAutoGUI's failsafe - move mouse to top-left to abort
5. **Backups**: Keep backups before running complex automation

## Combining Multiple Tools

### Example: Complete Task Automation

```
User: "Every 5 minutes, take a screenshot, check if CPU is over 80%, and if so, log it to a file"

This would require:
1. screenshot tool - to capture screen
2. get_system_info - to check CPU usage
3. keyboard/mouse control - to open notepad and log
4. (Would need custom scheduling - future feature)
```

### Example: Visual UI Automation

```
User: "Find the Submit button on screen and click it"

Steps:
1. AI uses screenshot to see the screen
2. AI uses locate_on_screen with submit button image
3. AI uses mouse_click at the found coordinates
```

## Troubleshooting Examples

**Issue: Mouse clicks not working**
```
Solution:
1. Check mouse_position to verify coordinates
2. Use get_screen_size to verify screen bounds
3. Ensure no fullscreen apps blocking automation
```

**Issue: Window not activating**
```
Solution:
1. Use list_windows to verify window exists
2. Check if window is minimized
3. Try using activate_window with exact title match
```

**Issue: Keyboard input not working**
```
Solution:
1. Ensure target window is active (use activate_window)
2. Check if target app requires admin privileges
3. Verify PyAutoGUI failsafe isn't triggered
```

## Best Practices

1. **Be Specific**: Provide exact window titles, coordinates, or process names
2. **Check State**: Verify system state before destructive operations
3. **Error Handling**: Expect and handle failures gracefully
4. **Incremental Testing**: Test each step before combining into workflows
5. **Documentation**: Keep track of successful automation patterns

## Future Automation Ideas

- Email automation (open Outlook, compose, send)
- File organization (sort downloads by type)
- Scheduled backups with visual confirmation
- Application health monitoring
- Automatic window layout switching
- Custom keyboard macro systems
- Voice-controlled PC operations
- Multi-step form filling

---

Have more automation ideas? The possibilities are endless with Windows MCP Server!
