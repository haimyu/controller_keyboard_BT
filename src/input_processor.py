import json

from bluetooth.hid_service import BluetoothHIDService
from hid_codes import create_key_release_report

class InputProcessor:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.shortcuts = json.load(f)
    
    def process_event(self, event_type, number, value):
        if event_type == 1 and value == 1: 
            shortcut_key = f"button_{number}"
            if shortcut_key in self.shortcuts:
                return self.shortcuts[shortcut_key]
        elif event_type == 1 and value == 0:
            release_report = create_key_release_report()
            BluetoothHIDService.send_hid_report(release_report)
        
        elif event_type == 2: 
            if number == 1:
                if value < -16000:
                    return self.shortcuts.get("joystick_left")
                elif value > 16000:
                    return self.shortcuts.get("joystick_right")
            elif number == 2: 
                if value < -16000:
                    return self.shortcuts.get("joystick_up")
                elif value > 16000:
                    return self.shortcuts.get("joystick_down")
        
        return None