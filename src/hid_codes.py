HID_SCAN_CODES = {
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08,
    'f': 0x09, 'g': 0x0A, 'h': 0x0B, 'i': 0x0C, 'j': 0x0D,
    'k': 0x0E, 'l': 0x0F, 'm': 0x10, 'n': 0x11, 'o': 0x12,
    'p': 0x13, 'q': 0x14, 'r': 0x15, 's': 0x16, 't': 0x17,
    'u': 0x18, 'v': 0x19, 'w': 0x1A, 'x': 0x1B, 'y': 0x1C, 'z': 0x1D,
    '1': 0x1E, '2': 0x1F, '3': 0x20, '4': 0x21, '5': 0x22,
    '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
    'enter': 0x28, 'escape': 0x29, 'backspace': 0x2A, 'tab': 0x2B,
    'space': 0x2C, 'minus': 0x2D, 'equal': 0x2E,
    'leftbrace': 0x2F, 'rightbrace': 0x30, 'backslash': 0x31,
    'semicolon': 0x33, 'apostrophe': 0x34, 'grave': 0x35,
    'comma': 0x36, 'dot': 0x37, 'slash': 0x38,
    'capslock': 0x39,
    'f1': 0x3A, 'f2': 0x3B, 'f3': 0x3C, 'f4': 0x3D,
    'f5': 0x3E, 'f6': 0x3F, 'f7': 0x40, 'f8': 0x41,
    'f9': 0x42, 'f10': 0x43, 'f11': 0x44, 'f12': 0x45,
    'printscreen': 0x46, 'scrolllock': 0x47, 'pause': 0x48,
    'insert': 0x49, 'home': 0x4A, 'pageup': 0x4B,
    'delete': 0x4C, 'end': 0x4D, 'pagedown': 0x4E,
    'right': 0x4F, 'left': 0x50, 'down': 0x51, 'up': 0x52
}

MODIFIERS = {
    'ctrl': 0x01,     # Left Control
    'shift': 0x02,    # Left Shift  
    'alt': 0x04,      # Left Alt (Option on Mac)
    'cmd': 0x08,      # Left GUI (Command on Mac)
    'rctrl': 0x10,    # Right Control
    'rshift': 0x20,   # Right Shift
    'ralt': 0x40,     # Right Alt
    'rcmd': 0x80      # Right GUI
}

def shortcut_to_hid_report(shortcut_string):
    """Convert shortcut string to proper 8-byte HID report for macOS"""
    parts = shortcut_string.lower().split('+')
    
    modifier_byte = 0x00
    key_codes = []
    
    for part in parts:
        part = part.strip()
        if part in MODIFIERS:
            modifier_byte |= MODIFIERS[part]
        elif part in HID_SCAN_CODES:
            key_codes.append(HID_SCAN_CODES[part])
    
    while len(key_codes) < 6:
        key_codes.append(0x00)
    
    key_codes = key_codes[:6]
    
    report = [0x01, modifier_byte, 0x00] + key_codes
    return report

def create_key_release_report():
    return [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
