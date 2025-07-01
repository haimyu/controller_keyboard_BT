# src/bluetooth_service_mock.py
"""
Mock Bluetooth HID service for development without Pi hardware
This simulates the Bluetooth functionality for testing
"""

class BluetoothHIDService:
    """Mock implementation of Bluetooth HID service"""
    
    def __init__(self):
        self.running = False
        self.connected_device = None
        print("🔧 Using MOCK Bluetooth service (development mode)")
        
    def setup_dbus(self):
        """Mock D-Bus setup"""
        print("✅ Mock D-Bus connection established")
        return True
        
    def create_hid_profile(self):
        """Mock HID profile registration"""
        print("✅ Mock HID profile registered")
        return True
        
    def make_discoverable(self):
        """Mock discoverable mode"""
        print("✅ Mock device is discoverable")
        return True
        
    def start_service(self):
        """Mock service startup"""
        print("🔧 Starting Mock Bluetooth HID service...")
        
        if not self.setup_dbus():
            return False
            
        if not self.create_hid_profile():
            return False
            
        if not self.make_discoverable():
            return False
            
        print("🎹 Mock Bluetooth HID service ready!")
        print("💡 In real Pi: MacBook would pair with this device")
        
        self.running = True
        self.connected_device = "Mock-MacBook"  # Simulate connection
        return True
        
    def send_hid_report(self, report_bytes):
        """
        Mock HID report transmission
        Args:
            report_bytes: List of 8 integers [modifier, reserved, key1-6]
        """
        if not self.running or not self.connected_device:
            print("❌ Mock: No Bluetooth connection available")
            return False
            
        print(f"📤 Mock: Would send HID report to {self.connected_device}: {report_bytes}")
        print(f"🎯 Mock: MacBook would receive keyboard shortcut")
        return True
        
    def stop_service(self):
        """Mock service shutdown"""
        self.running = False
        self.connected_device = None
        print("🛑 Mock Bluetooth HID service stopped")