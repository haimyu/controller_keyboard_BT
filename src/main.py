import struct
import sys
import os
import time
from input_processor import InputProcessor
from hid_codes import shortcut_to_hid_report
from bluetooth_service import BluetoothHIDService



class AssistiveKeyboard:
    def __init__(self, config_path):
        self.processor = InputProcessor(config_path)
        self.bluetooth = BluetoothHIDService()
        self.running = False
        
    def start(self):
        print("Starting Assistive Keyboard...")
        
        if not self.bluetooth.start_service():
            print("Failed to start Bluetooth service")
            sys.exit(1)
        

        print("Waiting for MacBook to pair...")
        time.sleep(5)
        
        try:
            js_device = open('/dev/input/js0', 'rb')
            self.running = True
            print("Joystick connected. Ready for input!")
            
        except FileNotFoundError:
            print("ERROR: No gamepad found at /dev/input/js0")
            print("Connect USB gamepad and try again")
            sys.exit(1)
        
        print("Press buttons to send shortcuts to MacBook")
        print("Press Ctrl+C to exit")
        
        try:
            while self.running:
                event = js_device.read(8)
                _, value, event_type, number = struct.unpack('IhBB', event)
                
                shortcut = self.processor.process_event(event_type, number, value)
                
                if shortcut:
                    self.send_shortcut(shortcut)
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()
             
    def send_shortcut(self, shortcut):
        hid_report = shortcut_to_hid_report(shortcut)
        print(f"{shortcut} → {hid_report}")
        
        success = self.bluetooth.send_hid_report(hid_report)
        if success:
            print(f"Sent '{shortcut}' to MacBook")
        else:
            print(f"Failed to send '{shortcut}'")
            
    def stop(self):
        self.running = False
        self.bluetooth.stop_service()
        print("Assistive keyboard stopped")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'shortcut_config.json')
    
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)
    

    if os.geteuid() != 0:
        print("ERROR: Must run as root for Bluetooth access")
        print("Use: sudo python src/main.py")
        sys.exit(1)
        
    keyboard = AssistiveKeyboard(config_path)
    keyboard.start()