# src/bluetooth_service.py
import dbus
import dbus.service
import dbus.mainloop.glib
import os
from gi.repository import GLib

class BluetoothAgent(dbus.service.Object):
    """Simple Bluetooth agent for auto-pairing"""
    
    def __init__(self, bus, path):
        super().__init__(bus, path)
        
    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        print("Agent released")
        
    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print(f"Authorizing service for {device}")
        return
        
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print(f"Auto-authorizing {device}")
        return

class BluetoothHIDDevice(dbus.service.Object):
    
    HID_DESCRIPTOR = bytes([
        0x05, 0x01,  
        0x09, 0x06,  
        0xa1, 0x01,  
        0x05, 0x07,  
        0x19, 0xe0,  
        0x29, 0xe7,  
        0x15, 0x00,  
        0x25, 0x01,  
        0x75, 0x01,  
        0x95, 0x08,  
        0x81, 0x02,  
        0x95, 0x01,  
        0x75, 0x08,  
        0x81, 0x03,  
        0x95, 0x06,  
        0x75, 0x08,  
        0x15, 0x00,  
        0x25, 0x65,  
        0x05, 0x07,  
        0x19, 0x00,  
        0x29, 0x65,  
        0x81, 0x00,  
        0xc0         
    ])
    
    def __init__(self, bus, path):
        super().__init__(bus, path)
        self.connected_devices = {}
        
    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        print(f"MacBook connected: {path}")
        self.connected_devices[path] = fd.take()
        
    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")  
    def RequestDisconnection(self, path):
        print(f"MacBook disconnected: {path}")
        if path in self.connected_devices:
            os.close(self.connected_devices[path])
            del self.connected_devices[path]
            
    def send_report(self, report_bytes):
        if not self.connected_devices:
            return False
            
        for path, fd in self.connected_devices.items():
            try:
                os.write(fd, bytes(report_bytes))
                print(f"Sent HID report: {report_bytes}")
                return True
            except Exception as e:
                print(f"Send failed: {e}")
        return False

class BluetoothHIDService:
    
    def __init__(self):
        self.bus = None
        self.adapter = None
        self.device_manager = None
        self.hid_device = None
        self.agent = None
        self.running = False
        
    def start_service(self):
        print("Starting Bluetooth HID service...")
        
        if not self.setup_dbus():
            return False
            
        if not self.setup_agent():
            return False
            
        if not self.create_hid_device():
            return False
            
        if not self.register_device():
            return False
            
        if not self.make_discoverable():
            return False
            
        print("Bluetooth HID service ready!")
        print("Pair your MacBook with this device now")
        
        self.running = True
        return True
    
    def setup_dbus(self):
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
            
            self.device_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.ProfileManager1"
            )
            
            print("D-Bus connection established")
            return True
            
        except Exception as e:
            print(f"D-Bus setup failed: {e}")
            return False
    
    def setup_agent(self):
        """Setup Bluetooth agent for pairing"""
        try:
            agent_path = "/assistive/keyboard/agent"
            self.agent = BluetoothAgent(self.bus, agent_path)
            
            agent_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.AgentManager1"
            )
            
            agent_manager.RegisterAgent(agent_path, "NoInputNoOutput")
            agent_manager.RequestDefaultAgent(agent_path)
            
            print("Bluetooth agent registered")
            return True
            
        except Exception as e:
            print(f"Agent setup failed: {e}")
            return False
    
    def find_adapter(self):
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
    
    def create_hid_device(self):
        try:
            device_path = "/assistive/keyboard/hid"
            self.hid_device = BluetoothHIDDevice(self.bus, device_path)
            print("HID device created")
            return True
            
        except Exception as e:
            print(f"Failed to create HID device: {e}")
            return False
    
    def register_device(self):
        try:
            profile_options = {
                "ServiceRecord": self.create_sdp_record(),
                "Role": "server",
                "RequireAuthentication": dbus.Boolean(False),
                "RequireAuthorization": dbus.Boolean(False),
                "AutoConnect": dbus.Boolean(True)
            }
            
            device_path = "/assistive/keyboard/hid"
            hid_uuid = "00001124-0000-1000-8000-00805f9b34fb"
            
            self.device_manager.RegisterProfile(
                device_path,
                hid_uuid,
                profile_options
            )
            
            print("HID profile registered")
            return True
            
        except Exception as e:
            print(f"Profile registration failed: {e}")
            print(f"Detailed error: {str(e)}")
            return False
    
    def create_sdp_record(self):
        return """
        <?xml version="1.0" encoding="UTF-8" ?>
        <record>
            <attribute id="0x0001">
                <sequence>
                    <uuid value="0x1124" />
                </sequence>
            </attribute>
            <attribute id="0x0004">
                <sequence>
                    <sequence>
                        <uuid value="0x0100" />
                        <uint16 value="0x0011" />
                    </sequence>
                    <sequence>
                        <uuid value="0x0011" />
                        <uint16 value="0x0013" />
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x0005">
                <sequence>
                    <uuid value="0x1002" />
                </sequence>
            </attribute>
            <attribute id="0x0009">
                <sequence>
                    <sequence>
                        <uuid value="0x1124" />
                        <uint16 value="0x0100" />
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x000d">
                <sequence>
                    <sequence>
                        <sequence>
                            <uuid value="0x0100" />
                            <uint16 value="0x0013" />
                        </sequence>
                        <sequence>
                            <uuid value="0x0011" />
                            <uint16 value="0x0013" />
                        </sequence>
                    </sequence>
                </sequence>
            </attribute>
            <attribute id="0x0100">
                <text value="Assistive Keyboard" />
            </attribute>
            <attribute id="0x0101">
                <text value="Keyboard" />
            </attribute>
            <attribute id="0x0102">
                <text value="Apple Inc." />
            </attribute>
            <attribute id="0x0200">
                <uint16 value="0x0100" />
            </attribute>
            <attribute id="0x0201">
                <uint16 value="0x0111" />
            </attribute>
            <attribute id="0x0202">
                <uint8 value="0x40" />
            </attribute>
            <attribute id="0x0203">
                <uint8 value="0x21" />
            </attribute>
            <attribute id="0x0206">
                <sequence>
                    <sequence>
                        <uint8 value="0x22" />
                        <text encoding="hex" value="05010906a101050719e029e71500250175019508810295017508810395067508150025650507190029658100c0" />
                    </sequence>
                </sequence>
            </attribute>
        </record>
        """.strip()
    
    def make_discoverable(self):
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter.object_path),
                "org.freedesktop.DBus.Properties"
            )
            
            adapter_props.Set("org.bluez.Adapter1", "Alias", "Assistive Keyboard")
            adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            
            print("Device is discoverable as 'Assistive Keyboard'")
            return True
            
        except Exception as e:
            print(f"Failed to make discoverable: {e}")
            return False
    
    def send_hid_report(self, report_bytes):
        if not self.hid_device:
            print("HID device not ready")
            return False
            
        return self.hid_device.send_report(report_bytes)
    
    def stop_service(self):
        self.running = False
        
        try:
            if self.device_manager and self.hid_device:
                device_path = "/assistive/keyboard/hid"
                self.device_manager.UnregisterProfile(device_path)
                print("HID profile unregistered")
        except Exception as e:
            print(f"Failed to unregister profile: {e}")
            
        try:
            if self.agent:
                agent_manager = dbus.Interface(
                    self.bus.get_object("org.bluez", "/org/bluez"),
                    "org.bluez.AgentManager1"
                )
                agent_path = "/assistive/keyboard/agent"
                agent_manager.UnregisterAgent(agent_path)
                print("Agent unregistered")
        except Exception as e:
            print(f"Failed to unregister agent: {e}")
            
        print("Bluetooth HID service stopped")