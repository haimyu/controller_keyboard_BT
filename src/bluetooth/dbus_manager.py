import dbus
import dbus.service
import dbus.mainloop.glib
import subprocess

class DBusManager:
    HID_UUID = "00001124-0000-1000-8000-00805f9b34fb"
    
    def __init__(self):
        self.bus = None
        self.adapter = None
        self.profile_manager = None
        self.adapter_path = None
        
    def initialize(self):
        """Initialize D-Bus connection and find adapter"""
        try:
            print("Initializing D-Bus connection...")
            
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            
            self.adapter_path = self._find_adapter()
            if not self.adapter_path:
                print("❌ No Bluetooth adapter found")
                return False
                
            self.adapter = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter_path),
                "org.bluez.Adapter1"
            )
            
            self.profile_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.ProfileManager1"
            )
            
            print("✅ D-Bus connection established")
            return True
            
        except Exception as e:
            print(f"❌ D-Bus initialization failed: {e}")
            return False
    
    def _find_adapter(self):
        """Find first available Bluetooth adapter"""
        try:
            manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager"
            )
            
            objects = manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if "org.bluez.Adapter1" in interfaces:
                    return path
                    
        except Exception as e:
            print(f"❌ Failed to find adapter: {e}")
            
        return None
    
    def set_device_class(self):
        """Set device class to keyboard"""
        try:
            result = subprocess.run(
                ["hciconfig", "hci0", "class", "0x002540"], 
                capture_output=True, check=False
            )
            
            if result.returncode == 0:
                print("✅ Device class set to keyboard")
            return True
            
        except Exception as e:
            print(f"⚠️  Device class note: {e}")
            return True
    
    def register_hid_profile(self, sdp_record):
        """Register HID profile with given SDP record"""
        try:
            profile_options = {
                "ServiceRecord": sdp_record,
                "Role": "server",
                "RequireAuthentication": dbus.Boolean(False),
                "RequireAuthorization": dbus.Boolean(False),
                "AutoConnect": dbus.Boolean(True)
            }
            
            profile_path = "/assistive/keyboard/profile"
            
            self.profile_manager.RegisterProfile(
                profile_path,
                self.HID_UUID,
                profile_options
            )
            
            print("✅ HID profile registered")
            return True
            
        except Exception as e:
            print(f"❌ Profile registration failed: {e}")
            return False
    
    def make_discoverable(self):
        """Make device discoverable and pairable"""
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter_path),
                "org.freedesktop.DBus.Properties"
            )
            
            adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Alias", "Assistive Keyboard")
            adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            adapter_props.Set("org.bluez.Adapter1", "PairableTimeout", dbus.UInt32(0))
            
            subprocess.run(["hciconfig", "hci0", "piscan"], check=False)
            subprocess.run(["hciconfig", "hci0", "sspmode", "1"], check=False)
            
            print("✅ Device discoverable")
            return True
            
        except Exception as e:
            print(f"❌ Failed to make discoverable: {e}")
            return False
    
    def get_bluetooth_address(self):
        """Get Bluetooth MAC address"""
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter_path),
                "org.freedesktop.DBus.Properties"
            )
            
            return str(adapter_props.Get("org.bluez.Adapter1", "Address"))
            
        except Exception as e:
            print(f"❌ Failed to get address: {e}")
            return None
    
    def get_status(self):
        """Get D-Bus connection status"""
        return {
            'bus_connected': self.bus is not None,
            'adapter_found': self.adapter is not None,
            'profile_manager_ready': self.profile_manager is not None
        }
    
    def cleanup(self):
        """Clean up D-Bus resources"""
        # D-Bus cleanup if needed
        pass

