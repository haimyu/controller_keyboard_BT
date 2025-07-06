import threading
import time
from .dbus_manager import DBusManager
from .socket_manager import SocketManager
from .sdp_record import SDPRecordBuilder
from .system_config import SystemConfigurator
from .connection_monitor import ConnectionMonitor

class BluetoothHIDService: 
    def __init__(self):
        self.dbus_manager = DBusManager()
        self.socket_manager = SocketManager()
        self.sdp_builder = SDPRecordBuilder()
        self.system_config = SystemConfigurator()
        self.connection_monitor = ConnectionMonitor()
        
        self.running = False
        self.connection_established = False
        
    def start_service(self):
        if not self.system_config.configure_for_hid():
            return False
            
        if not self.dbus_manager.initialize():
            return False
            
        if not self.dbus_manager.set_device_class():
            return False
            
        sdp_record = self.sdp_builder.create_hid_keyboard_record()
        if not self.dbus_manager.register_hid_profile(sdp_record):
            return False
            
        if not self.dbus_manager.make_discoverable():
            return False
            
        if not self.socket_manager.setup_hid_sockets():
            return False
            
        self.connection_monitor.start_monitoring(
            self.socket_manager,
            self._on_connection_established
        )
        
        self.running = True
        print("Bluetooth HID service ready!")
        return True
    
    def _on_connection_established(self):
        """Callback when both HID channels are connected"""
        self.connection_established = True
        print("HID device fully operational!")
    
    def send_hid_report(self, report_bytes):
        """Send HID report using socket manager"""
        if not self.connection_established:
            print("Device not connected")
            return False
            
        return self.socket_manager.send_hid_report(report_bytes)
    
    def stop_service(self):
        """Clean shutdown of all components"""
        self.running = False
        self.connection_established = False
        
        self.connection_monitor.stop()
        self.socket_manager.cleanup()
        self.dbus_manager.cleanup()
        
        print("Service stopped cleanly")
    
    def get_status(self):
        """Get comprehensive status from all components"""
        return {
            'running': self.running,
            'connected': self.connection_established,
            'dbus_status': self.dbus_manager.get_status(),
            'socket_status': self.socket_manager.get_status(),
            'connection_status': self.connection_monitor.get_status()
        }
