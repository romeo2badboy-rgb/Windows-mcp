# AI Usage Guide - Windows MCP Server

**Essential guide for AI assistants using Windows MCP Server**

## 🎯 Core Principle: ALWAYS Start with get_desktop_state

### ❌ WRONG Approach
```
User: "Click the Submit button"
AI: [Guesses coordinates] mouse_click(x=500, y=300)
Result: ❌ Misses the button, clicks wrong spot
```

### ✅ CORRECT Approach
```
User: "Click the Submit button"
AI:
1. get_desktop_state() → See all elements with labels
2. Find "Submit" button → Label 7
3. click_element(label=7) → ✓ Success!
```

---

## 🚀 Workflow Pattern (USE THIS!)

### Pattern 1: UI Interaction (Most Common)
```
Step 1: get_desktop_state()
        ↓
Step 2: Analyze elements
        ↓
Step 3: click_element() or type_into_element()
        ↓
Step 4: Confirm success
```

**Example:**
```
User: "Fill the login form and submit"

AI Actions:
1. get_desktop_state()
   → Found: Label 3=Email field, Label 4=Password field, Label 5=Login button

2. type_into_element(label=3, text="user@email.com")
   → ✓ Typed into Email field

3. type_into_element(label=4, text="password123")
   → ✓ Typed into Password field

4. click_element(label=5)
   → ✓ Clicked Login button

Result: ✅ Form filled and submitted successfully
```

### Pattern 2: UI Interaction with Vision
```
Step 1: get_desktop_state(use_vision=True)
        ↓
Step 2: See annotated screenshot with labels
        ↓
Step 3: Use labels to interact
```

**When to use vision:**
- User says "show me", "I need to see"
- Complex UI with many elements
- Need to verify exact layout
- Debugging interaction issues

### Pattern 3: System Operations
```
Step 1: Direct tool use (no state needed)
        ↓
Step 2: Execute operation
        ↓
Step 3: Confirm result
```

**Example:**
```
User: "Take a screenshot and save to Desktop"

AI Actions:
1. screenshot(save_path="C:\\Users\\UserName\\Desktop\\screenshot.png")
   → ✓ Screenshot saved

Result: ✅ Screenshot saved to Desktop
```

---

## 📋 Tool Selection Guide

### Start Every Session With:
```
get_desktop_state() - Know what's on screen
```

### For Clicking:
```
✅ PREFER: click_element(label=N)
❌ AVOID:  mouse_click(x, y) - coordinates change!
```

### For Typing:
```
✅ PREFER: type_into_element(label=N, text="...")
❌ AVOID:  keyboard_type("...") - might type in wrong place!
```

### For Screenshots:
```
✅ USE: screenshot() - for quick captures
✅ USE: get_desktop_state(use_vision=True) - for UI analysis
```

### For Window Management:
```
✅ USE: list_windows() - see all windows
✅ USE: activate_window(title="...") - switch windows
```

### For Applications:
```
✅ USE: launch_application(path="notepad.exe")
✅ USE: kill_process(name="notepad.exe")
```

---

## ⚡ Speed Optimization

### Cache Awareness
```python
# First call - scans UI tree (1.2s)
get_desktop_state()

# Within 30 seconds - use cached labels
click_element(label=5)  # Fast!
type_into_element(label=7, text="hello")  # Fast!

# After 30 seconds - you'll get a warning
click_element(label=5)  # Warning: Cache stale
# → Best: Refresh state
get_desktop_state()  # Fresh scan
```

### Batch Operations
```python
# ✅ GOOD: Get state once, use multiple times
get_desktop_state()
click_element(label=3)
type_into_element(label=5, text="data")
click_element(label=7)

# ❌ BAD: Getting state repeatedly
get_desktop_state()
click_element(label=3)
get_desktop_state()  # Unnecessary!
type_into_element(label=5, text="data")
get_desktop_state()  # Unnecessary!
```

---

## 🎯 Best Practices

### 1. Always Describe What You're Doing
```
❌ "Clicking element 5"
✅ "Clicking element 5 (Submit button) at (450,300)"
```

### 2. Confirm Success
```
After each operation, acknowledge:
"✓ Typed email into element 3"
"✓ Clicked Login button (element 7)"
```

### 3. Handle Errors Gracefully
```
If error: "Error: Label 99 out of range (0-45)"
Response: "I need to refresh the desktop state. Let me scan again."
→ get_desktop_state()
```

### 4. Use Descriptive Actions
```
❌ type_into_element(label=5, text="abc")
✅ type_into_element(label=5, text="user@email.com")
   "Typing email address into Email field (element 5)"
```

### 5. Leverage clear_first and press_enter
```
# Replace existing text
type_into_element(label=3, text="new text", clear_first=True)

# Submit after typing
type_into_element(label=5, text="search query", press_enter=True)
```

---

## 🚫 Common Mistakes to Avoid

### Mistake 1: Using Coordinates Instead of Labels
```
❌ WRONG:
mouse_click(x=500, y=300)  # What if window moves?

✅ CORRECT:
get_desktop_state()
click_element(label=7)  # Always works!
```

### Mistake 2: Not Refreshing Stale State
```
❌ WRONG:
get_desktop_state()  # 10:00 AM
[... 5 minutes later ...]
click_element(label=5)  # UI might have changed!

✅ CORRECT:
get_desktop_state()  # 10:00 AM
[... 5 minutes later ...]
get_desktop_state()  # Refresh!
click_element(label=5)  # Accurate!
```

### Mistake 3: Typing Without Focusing
```
❌ WRONG:
keyboard_type("hello")  # Types into whatever is focused!

✅ CORRECT:
type_into_element(label=5, text="hello")  # Clicks to focus first!
```

### Mistake 4: Ignoring Error Messages
```
❌ WRONG:
Error: "Invalid label 99"
Response: Trying again with same label

✅ CORRECT:
Error: "Invalid label 99"
Response: "Let me refresh the desktop state to see current elements"
→ get_desktop_state()
```

### Mistake 5: Not Using Vision When Needed
```
❌ WRONG:
User: "I don't know which button to click"
AI: [Guesses blindly]

✅ CORRECT:
User: "I don't know which button to click"
AI: get_desktop_state(use_vision=True)
    "Here's the annotated screenshot showing all buttons with labels..."
```

---

## 💡 Pro Tips

### Tip 1: Combine Operations
```python
# Fill entire form in one flow
get_desktop_state()

type_into_element(label=3, text="john@email.com", clear_first=True)
type_into_element(label=4, text="password123", clear_first=True)
click_element(label=5)  # Submit

"✓ Form filled and submitted successfully"
```

### Tip 2: Use Scrollable Elements
```python
# Scroll before clicking if element is off-screen
get_desktop_state(include_scrollable=True)

# Check scroll position in output
# Scroll if needed using mouse_scroll or keyboard
```

### Tip 3: Handle Different Clicks
```python
# Right-click for context menu
click_element(label=5, button="right")

# Double-click to open
click_element(label=7, clicks=2)

# Triple-click to select all
click_element(label=3, clicks=3)
```

### Tip 4: Type Special Characters
```python
# All text is supported
type_into_element(label=5, text="user@email.com")
type_into_element(label=7, text="C:\\Users\\Documents\\file.txt")
type_into_element(label=9, text="Hello! How are you?")
```

### Tip 5: Leverage Keyboard Shortcuts
```python
# For system-wide actions, use keyboard shortcuts
keyboard_press(keys=["win", "r"])  # Open Run dialog
keyboard_type(text="notepad")
keyboard_press(keys=["enter"])
```

---

## 📊 Decision Tree

```
User Request
    ↓
Does it involve UI interaction?
    ├─ YES → get_desktop_state() first
    │         ├─ Need to see UI? → use_vision=True
    │         ├─ Need to click? → click_element(label=N)
    │         ├─ Need to type? → type_into_element(label=N, text="...")
    │         └─ Multiple actions? → Use same state for all
    │
    └─ NO → Direct tool use
              ├─ Screenshot? → screenshot()
              ├─ System info? → get_system_info()
              ├─ Launch app? → launch_application()
              └─ System control? → shutdown/restart/lock
```

---

## 🎓 Example Scenarios

### Scenario 1: Web Form
```
User: "Fill the contact form: Name=John, Email=john@test.com, Submit"

AI Steps:
1. get_desktop_state()
2. Analyze: Found Name field (label 3), Email field (label 5), Submit button (label 8)
3. type_into_element(label=3, text="John")
4. type_into_element(label=5, text="john@test.com")
5. click_element(label=8)
6. Response: "✓ Contact form filled and submitted"
```

### Scenario 2: Search Operation
```
User: "Search for 'Python tutorial' and press enter"

AI Steps:
1. get_desktop_state()
2. Find search box (label 12)
3. type_into_element(label=12, text="Python tutorial", press_enter=True)
4. Response: "✓ Searched for 'Python tutorial'"
```

### Scenario 3: Complex Navigation
```
User: "Open Chrome, go to GitHub, and screenshot the page"

AI Steps:
1. launch_application(path="chrome.exe")
2. Wait 2 seconds for Chrome to open
3. get_desktop_state()
4. Find address bar (label 15)
5. type_into_element(label=15, text="github.com", press_enter=True)
6. Wait 3 seconds for page to load
7. screenshot(save_path="Desktop/github.png")
8. Response: "✓ Opened Chrome, navigated to GitHub, took screenshot"
```

### Scenario 4: Debugging
```
User: "The button isn't working"

AI Steps:
1. get_desktop_state(use_vision=True)
2. Response: "I can see the screen now. Here are all the buttons:
   - Label 5: 'Submit' button at (450, 300)
   - Label 7: 'Cancel' button at (550, 300)
   - Label 9: 'Reset' button at (350, 300)

   Which button are you trying to click?"
```

---

## ⚙️ Configuration Tips

### For Users (Claude Desktop Setup)
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

### For AI: Know Your Limitations
```
✅ CAN DO:
- Click any visible UI element
- Type into any text field
- Take screenshots
- Launch applications
- Control system (shutdown, restart, etc.)

❌ CANNOT DO:
- Interact with elements that are off-screen (scroll first!)
- Click on elements that don't exist (check with get_desktop_state)
- Read minds (always scan state first!)
- Work without proper setup (user must configure MCP server)
```

---

## 🎯 Summary: The Golden Rule

```
┌─────────────────────────────────────┐
│                                     │
│   ALWAYS GET STATE BEFORE ACTION    │
│                                     │
│   get_desktop_state() → FIRST       │
│   click/type → SECOND               │
│                                     │
└─────────────────────────────────────┘
```

**Remember:**
1. 🔍 **See first** (get_desktop_state)
2. 🎯 **Act second** (click_element / type_into_element)
3. ✅ **Confirm third** (acknowledge success)
4. 🔄 **Refresh when needed** (>30 seconds or UI changed)

**This makes you 10x faster and 100x more accurate!** 🚀

---

## 📚 Quick Reference Card

```
┌──────────────────────────────────────────────────┐
│ MOST USED PATTERNS                               │
├──────────────────────────────────────────────────┤
│ 1. Click something:                              │
│    get_desktop_state()                           │
│    click_element(label=N)                        │
│                                                  │
│ 2. Type something:                               │
│    get_desktop_state()                           │
│    type_into_element(label=N, text="...")        │
│                                                  │
│ 3. Fill form:                                    │
│    get_desktop_state()                           │
│    type_into_element(label=3, text="field1")     │
│    type_into_element(label=5, text="field2")     │
│    click_element(label=7)                        │
│                                                  │
│ 4. See UI:                                       │
│    get_desktop_state(use_vision=True)            │
│                                                  │
│ 5. Screenshot:                                   │
│    screenshot(save_path="path/to/file.png")      │
└──────────────────────────────────────────────────┘
```

Use this guide every time you interact with Windows! 🎯
