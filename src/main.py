import struct
import sys
import os
import time
import threading
import traceback
import subprocess
from input_processor import InputProcessor
from hid_codes import shortcut_to_hid_report, create_key_release_report
from bluetooth.hid_service import BluetoothHIDService

class AssistiveKeyboard:
    def __init__(self, config_path):
        self.processor = InputProcessor(config_path)
        self.bluetooth_service = BluetoothHIDService()
        self.running = False
        self.connected = False
        
        self.report_count = 0
        self.start_time = None
        
    def start(self):
        if not self._check_system_requirements():
            sys.exit(1)
        
        if not self._start_bluetooth_service():
            sys.exit(1)
        
        self._start_connection_monitoring()
        
        self._start_input_processing()
             
    def _check_system_requirements(self):
        """Check system requirements with clear error reporting"""

        if not os.path.exists('/dev/input/js0'):
            print("❌ No joystick found at /dev/input/js0")
            return False
        
        print("✅ Joystick detected")

        if os.geteuid() != 0:
            print("❌ Must run as root for Bluetooth access")
            return False
        
        print("✅ Root privileges confirmed")

        if not self._check_bluetooth_adapter():
            return False
        
        print("✅ System requirements satisfied")
        return True
    
    def _check_bluetooth_adapter(self):
        """Check if Bluetooth adapter is ready"""
        try:
            result = subprocess.run(["hciconfig", "hci0"], 
                                  capture_output=True, text=True)
            if "UP RUNNING" not in result.stdout:
                print("❌ Bluetooth adapter not ready")
                return False
            
            print("✅ Bluetooth adapter ready")
            return True
            
        except Exception as e:
            print(f"❌ Cannot check Bluetooth adapter: {e}")
            return False
    
    def _start_bluetooth_service(self):
        """Start the clean Bluetooth HID service"""
        try:
            if not self.bluetooth_service.start_service():
                print("❌ Failed to start Bluetooth service")
                return False
            
            print("✅ Bluetooth HID service started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Bluetooth service startup failed: {e}")
            return False
    
    def _start_connection_monitoring(self):
        """Start monitoring for dual-channel connection"""
        connection_monitor = threading.Thread(target=self._monitor_connection_status)
        connection_monitor.daemon = True
        connection_monitor.start()
    
    def _monitor_connection_status(self):
        """Monitor connection status"""
        connection_attempts = 0
        max_attempts = 60 
        
        print("⏳ Monitoring connection status...")
        
        while not self.connected and self.running and connection_attempts < max_attempts:
            status = self.bluetooth_service.get_status()
            
            if self._is_fully_connected(status):
                self.connected = True
                self._on_connection_established()
                break
            

            if connection_attempts % 10 == 0: 
                self._print_connection_status(status, connection_attempts)
            
            connection_attempts += 1
            time.sleep(1)
        
        if not self.connected:
            print(f"\n❌ Connection failed after {max_attempts} seconds")
            sys.exit(1)
    
    def _is_fully_connected(self, status):
        """Check if both HID channels are connected"""
        return (status['connected'] and 
                status['socket_status']['control_connected'] and 
                status['socket_status']['interrupt_connected'])

    def _print_connection_status(self, status, attempt):
        """Print detailed connection status"""
        print(f"⏳ Connection attempt {attempt}/60:")
        print(f"  • Service running: {'✅' if status['running'] else '❌'}")
        print(f"  • D-Bus ready: {'✅' if status['dbus_status']['bus_connected'] else '❌'}")
        print(f"  • Control channel: {'✅' if status['socket_status']['control_connected'] else '⏳'}")
        print(f"  • Interrupt channel: {'✅' if status['socket_status']['interrupt_connected'] else '⏳'}")
    
    def _on_connection_established(self):
        """Handle successful connection establishment"""
        self.start_time = time.time()
        print("Device fully operational!")
        print("Press buttons on joystick to send shortcuts...")
 
    def _start_input_processing(self):
        """Start processing joystick input"""
        try:
            js_device = open('/dev/input/js0', 'rb')
            self.running = True
            print("Joystick input processing started")
            
        except FileNotFoundError:
            print("Cannot access /dev/input/js0")
            sys.exit(1)
        
        try:
            while self.running:
                event = js_device.read(8)
                _, value, event_type, number = struct.unpack('IhBB', event)
                
                shortcut = self.processor.process_event(event_type, number, value)
                
                if shortcut and self.connected:
                    self._send_shortcut_with_performance_tracking(shortcut)
                    
        except KeyboardInterrupt:
            print("\n=== Shutdown requested ===")
            self._shutdown()
        except Exception as e:
            print(f"❌ Input processing error: {e}")
            self._shutdown()
    
    def _send_shortcut_with_performance_tracking(self, shortcut):
        """Send shortcut with performance measurement"""
        start_time = time.time()
        
        hid_report = shortcut_to_hid_report(shortcut)
        print(f"🎹 Sending '{shortcut}' → {hid_report}")
        
        success = self.bluetooth_service.send_hid_report(hid_report)
        
        send_time = time.time() - start_time
        
        if success:
            print(f"✅ '{shortcut}' sent successfully ({send_time*1000:.2f}ms)")
            self.report_count += 1
            
            time.sleep(0.05) 
            release_report = create_key_release_report()
            self.bluetooth_service.send_hid_report(release_report)
            
            if self.report_count % 10 == 0:
                self._print_performance_stats()
                
        else:
            print(f"❌ Failed to send '{shortcut}'")
    
    def _print_performance_stats(self):
        """Print performance statistics"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            rate = self.report_count / elapsed
            print(f"📊 Performance: {self.report_count} reports sent, "
                  f"{rate:.2f} reports/second average")
    
    def _shutdown(self):
        """Clean shutdown of all components"""
        print("🛑 Shutting down assistive keyboard...")
        
        self.running = False
        
        # Stop the clean service
        if hasattr(self, 'bluetooth_service'):
            self.bluetooth_service.stop_service()
        
        # Print final performance stats
        if self.report_count > 0:
            print(f"📊 Final stats: {self.report_count} shortcuts sent successfully")
        
        print("✅ Shutdown complete")

def main():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'shortcut_config.json')
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    try:
        keyboard = AssistiveKeyboard(config_path)
        keyboard.start()
        
    except KeyboardInterrupt:
        print("\n=== Shutdown requested ===")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()