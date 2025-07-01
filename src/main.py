# # src/main.py
# import struct
# import sys
# import os
# from input_processor import InputProcessor
# from hid_codes import shortcut_to_hid_report

# class AssistiveKeyboard:
#     def __init__(self, config_path):
#         self.processor = InputProcessor(config_path)
#         self.running = False
        
#     def start(self):
#         """Main application loop"""
#         try:
#             js_device = open('/dev/input/js0', 'rb')
#             self.running = True
#             print("Assistive keyboard started. Press Ctrl+C to exit.")
            
#             while self.running:
#                 event = js_device.read(8)
#                 _, value, event_type, number = struct.unpack('IhBB', event)
                
#                 # Process input event
#                 shortcut = self.processor.process_event(event_type, number, value)
                
#                 if shortcut:
#                     # Convert to HID report
#                     hid_report = shortcut_to_hid_report(shortcut)
#                     print(f"Shortcut: {shortcut} -> HID: {hid_report}")
                    
#                     # TODO: Send via Bluetooth
#                     self.send_hid_report(hid_report)
                    
#         except FileNotFoundError:
#             print("ERROR: No gamepad found at /dev/input/js0")
#             sys.exit(1)
#         except KeyboardInterrupt:
#             print("\nShutting down...")
#             self.stop()
            
#     def send_hid_report(self, hid_report):
#         """Send HID report via Bluetooth - PLACEHOLDER"""
#         # TODO: Implement Bluetooth transmission
#         print(f"Would send HID report: {hid_report}")
        
#     def stop(self):
#         """Clean shutdown"""
#         self.running = False

# if __name__ == "__main__":
#     config_path = "config/shortcut_config.json"
#     keyboard = AssistiveKeyboard(config_path)
#     keyboard.start()


# src/main.py
import struct
import sys
import os
import time
from input_processor import InputProcessor
from hid_codes import shortcut_to_hid_report

try:
    from bluetooth_service import BluetoothHIDService
    MOCK_MODE = False
    print("Using REAL Bluetooth service")
except ImportError:
    from bluetooth_service_mock import BluetoothHIDService
    MOCK_MODE = True
    print("Using MOCK Bluetooth service (development mode)")

class AssistiveKeyboard:
    def __init__(self, config_path):
        self.processor = InputProcessor(config_path)
        self.bluetooth = BluetoothHIDService()
        self.running = False
        
    def start(self):
        """Main application loop"""
        print("Starting Assistive Keyboard...")
        
        # Initialize Bluetooth HID service
        if not self.bluetooth.start_service():
            print("Failed to start Bluetooth service")
            sys.exit(1)
        
        if not MOCK_MODE:
            # Wait for MacBook pairing (only in real mode)
            print("Waiting for MacBook to pair...")
            time.sleep(5)
        
        # Try to open joystick device
        try:
            js_device = open('/dev/input/js0', 'rb')
            self.running = True
            print("Joystick connected. Ready for input!")
            
        except FileNotFoundError:
            if MOCK_MODE:
                print("🎮 No joystick found - entering SIMULATION mode")
                self.run_simulation()
                return
            else:
                print("ERROR: No gamepad found at /dev/input/js0")
                print("Connect USB gamepad and try again")
                sys.exit(1)
        
        # Real joystick input loop
        print("Press buttons to send shortcuts to MacBook")
        print("Press Ctrl+C to exit")
        
        try:
            while self.running:
                event = js_device.read(8)
                _, value, event_type, number = struct.unpack('IhBB', event)
                
                # Process input event
                shortcut = self.processor.process_event(event_type, number, value)
                
                if shortcut:
                    self.send_shortcut(shortcut)
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop()
            
    def run_simulation(self):
        """Simulate joystick input for development testing"""
        print("\nSIMULATION MODE - Testing predefined inputs")
        print("Press Ctrl+C to exit")
        
        # Simulate button presses
        test_events = [
            (1, 0, 1, "Save (cmd+s)"),
            (1, 1, 1, "Undo (cmd+z)"),
            (1, 2, 1, "Copy (cmd+c)"),
            (1, 3, 1, "Paste (cmd+v)"),
            (2, 1, -25000, "Navigate Left"),
            (2, 1, 25000, "Navigate Right"),
        ]
        
        try:
            for event_type, number, value, description in test_events:
                print(f"\n📡 Simulating: {description}")
                
                shortcut = self.processor.process_event(event_type, number, value)
                if shortcut:
                    self.send_shortcut(shortcut)
                
                time.sleep(2)  # 2 second delay between simulated inputs
                
            print("\nSimulation complete!")
            
        except KeyboardInterrupt:
            print("\nSimulation stopped")
            self.stop()
    
    def send_shortcut(self, shortcut):
        """Process and send a shortcut"""
        # Convert to HID report
        hid_report = shortcut_to_hid_report(shortcut)
        print(f"{shortcut} → {hid_report}")
        
        # Send via Bluetooth
        success = self.bluetooth.send_hid_report(hid_report)
        if success:
            print(f"Sent '{shortcut}' to MacBook")
        else:
            print(f"Failed to send '{shortcut}'")
            
    def stop(self):
        """Clean shutdown"""
        self.running = False
        self.bluetooth.stop_service()
        print("Assistive keyboard stopped")

if __name__ == "__main__":
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'shortcut_config.json')
    
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)
    
    # Check if running as root (only required for real Bluetooth)
    if not MOCK_MODE and os.geteuid() != 0:
        print("ERROR: Must run as root for Bluetooth access")
        print("Use: sudo python src/main.py")
        sys.exit(1)
        
    keyboard = AssistiveKeyboard(config_path)
    keyboard.start()