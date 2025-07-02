# src/bluetooth_service.py
import dbus
import dbus.service
import dbus.mainloop.glib
import socket
import threading

class BluetoothHIDService:
    """Real Bluetooth HID service using D-Bus and L2CAP sockets"""
    
    HID_UUID = "00001124-0000-1000-8000-00805f9b34fb"
    HID_CONTROL_PSM = 17
    HID_INTERRUPT_PSM = 19
    
    # HID descriptor for standard keyboard
    HID_DESCRIPTOR = bytes([
        0x05, 0x01,  # Usage Page (Generic Desktop)
        0x09, 0x06,  # Usage (Keyboard)
        0xa1, 0x01,  # Collection (Application)
        0x05, 0x07,  # Usage Page (Key Codes)
        0x19, 0xe0,  # Usage Minimum (224)
        0x29, 0xe7,  # Usage Maximum (231)
        0x15, 0x00,  # Logical Minimum (0)
        0x25, 0x01,  # Logical Maximum (1)
        0x75, 0x01,  # Report Size (1)
        0x95, 0x08,  # Report Count (8)
        0x81, 0x02,  # Input (Data, Variable, Absolute)
        0x95, 0x01,  # Report Count (1)
        0x75, 0x08,  # Report Size (8)
        0x81, 0x03,  # Input (Constant)
        0x95, 0x06,  # Report Count (6)
        0x75, 0x08,  # Report Size (8)
        0x15, 0x00,  # Logical Minimum (0)
        0x25, 0x65,  # Logical Maximum (101)
        0x05, 0x07,  # Usage Page (Key Codes)
        0x19, 0x00,  # Usage Minimum (0)
        0x29, 0x65,  # Usage Maximum (101)
        0x81, 0x00,  # Input (Data, Array)
        0xc0         # End Collection
    ])
    
    def __init__(self):
        self.bus = None
        self.adapter = None
        self.profile_manager = None
        self.hid_socket = None
        self.client_socket = None
        self.running = False
        
    def start_service(self):
        """Start the HID service"""
        print("Starting Bluetooth HID service...")
        
        if not self.setup_dbus():
            return False
            
        if not self.register_hid_profile():
            return False
            
        if not self.make_discoverable():
            return False
            
        if not self.setup_hid_socket():
            return False
            
        print("Bluetooth HID service ready!")
        print("Pair your MacBook with this device now")
        
        self.connection_thread = threading.Thread(target=self.wait_for_connection)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
        self.running = True
        return True
    
    def setup_dbus(self):
        """Initialize D-Bus connection to BlueZ"""
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            
            adapter_path = self.find_adapter()
            if not adapter_path:
                print("No Bluetooth adapter found")
                return False
                
            self.adapter = dbus.Interface(
                self.bus.get_object("org.bluez", adapter_path),
                "org.bluez.Adapter1"
            )
            
            self.profile_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.ProfileManager1"
            )
            
            print("D-Bus connection established")
            return True
            
        except Exception as e:
            print(f"D-Bus setup failed: {e}")
            return False
    
    def find_adapter(self):
        """Find the first available Bluetooth adapter"""
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
            print(f"Failed to find adapter: {e}")
            
        return None
    
    def register_hid_profile(self):
        """Register HID profile with BlueZ"""
        try:
            profile_options = {
                "ServiceRecord": self.create_sdp_record(),
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
            
            print("HID profile registered")
            return True
            
        except Exception as e:
            print(f"HID profile registration failed: {e}")
            return False
    
    def create_sdp_record(self):
        """Create SDP record for HID keyboard"""
        sdp_record = f"""
        <?xml version="1.0" encoding="UTF-8" ?>
        <record>
            <attribute id="0x0001">
                <sequence>
                    <uuid value="{self.HID_UUID}" />
                </sequence>
            </attribute>
            <attribute id="0x0100">
                <text value="Assistive Keyboard" />
            </attribute>
            <attribute id="0x0101">
                <text value="HID Keyboard for Musicians" />
            </attribute>
            <attribute id="0x0206">
                <sequence>
                    <sequence>
                        <uint8 value="0x22" />
                        <text encoding="hex" value="{self.HID_DESCRIPTOR.hex()}" />
                    </sequence>
                </sequence>
            </attribute>
        </record>
        """
        return sdp_record.strip()
    
    def make_discoverable(self):
        """Make Pi discoverable as keyboard device"""
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter.object_path),
                "org.freedesktop.DBus.Properties"
            )
            
            adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            
            print("Device is discoverable")
            return True
            
        except Exception as e:
            print(f"Failed to make discoverable: {e}")
            return False
    
    def get_bluetooth_address(self):
        """Get Pi's Bluetooth address from adapter"""
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter.object_path),
                "org.freedesktop.DBus.Properties"
            )
            
            address = adapter_props.Get("org.bluez.Adapter1", "Address")
            print(f"Using Bluetooth address: {address}")
            return str(address)
            
        except Exception as e:
            print(f"Failed to get Bluetooth address: {e}")
            return None

    def setup_hid_socket(zself):
        """Create L2CAP socket for HID interrupt channel"""
        try:
            # Get Pi's Bluetooth address
            bt_address = self.get_bluetooth_address()
            if not bt_address:
                print("Failed to get Bluetooth address")
                return False
            
            self.hid_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            self.hid_socket.bind((bt_address, self.HID_INTERRUPT_PSM))
            self.hid_socket.listen(1)
            
            print(f"HID socket listening on {bt_address}:{self.HID_INTERRUPT_PSM}")
            return True
            
        except Exception as e:
            print(f"Failed to setup HID socket: {e}")
            return False

    def wait_for_connection(self):
        """Wait for MacBook to connect"""
        try:
            print("Waiting for MacBook connection...")
            self.client_socket, address = self.hid_socket.accept()
            print(f"MacBook connected: {address}")
            
        except Exception as e:
            print(f"Connection failed: {e}")
    
    def send_hid_report(self, report_bytes):
        """Send 8-byte HID report to MacBook"""
        if not self.client_socket:
            print("No MacBook connection available")
            return False
            
        try:
            report = bytes(report_bytes)
            self.client_socket.send(report)
            print(f"Sent HID report: {report_bytes}")
            return True
            
        except Exception as e:
            print(f"Failed to send HID report: {e}")
            return False
    
    def stop_service(self):
        """Stop the HID service"""
        self.running = False
        
        if self.client_socket:
            self.client_socket.close()
            
        if self.hid_socket:
            self.hid_socket.close()
            
        print("Bluetooth HID service stopped")