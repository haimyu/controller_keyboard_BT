# # src/bluetooth_service.py
# import dbus
# import dbus.service
# import dbus.mainloop.glib
# import socket
# import threading
# import time
# from gi.repository import GLib

# class BluetoothHIDService:
#     """
#     D-Bus interface to BlueZ for HID keyboard functionality
#     """
    
#     # HID Service UUIDs
#     HID_UUID = "00001124-0000-1000-8000-00805f9b34fb"
#     HID_CONTROL_PSM = 17    # L2CAP channel for HID control
#     HID_INTERRUPT_PSM = 19  # L2CAP channel for HID data
    
#     # HID Descriptor for standard keyboard
#     HID_DESCRIPTOR = bytes([
#         0x05, 0x01,  # Usage Page (Generic Desktop)
#         0x09, 0x06,  # Usage (Keyboard)
#         0xa1, 0x01,  # Collection (Application)
#         0x05, 0x07,  # Usage Page (Key Codes)
#         0x19, 0xe0,  # Usage Minimum (224)
#         0x29, 0xe7,  # Usage Maximum (231)
#         0x15, 0x00,  # Logical Minimum (0)
#         0x25, 0x01,  # Logical Maximum (1)
#         0x75, 0x01,  # Report Size (1)
#         0x95, 0x08,  # Report Count (8)
#         0x81, 0x02,  # Input (Data, Variable, Absolute)
#         0x95, 0x01,  # Report Count (1)
#         0x75, 0x08,  # Report Size (8)
#         0x81, 0x03,  # Input (Constant)
#         0x95, 0x06,  # Report Count (6)
#         0x75, 0x08,  # Report Size (8)
#         0x15, 0x00,  # Logical Minimum (0)
#         0x25, 0x65,  # Logical Maximum (101)
#         0x05, 0x07,  # Usage Page (Key Codes)
#         0x19, 0x00,  # Usage Minimum (0)
#         0x29, 0x65,  # Usage Maximum (101)
#         0x81, 0x00,  # Input (Data, Array)
#         0xc0         # End Collection
#     ])
    
#     def __init__(self):
#         self.bus = None
#         self.profile_manager = None
#         self.device_manager = None
#         self.adapter = None
#         self.control_socket = None
#         self.interrupt_socket = None
#         self.connected_device = None
#         self.running = False
        
#     def setup_dbus(self):
#         """Initialize D-Bus connection to BlueZ"""
#         try:
#             dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
#             self.bus = dbus.SystemBus()
            
#             # Get BlueZ objects
#             self.profile_manager = dbus.Interface(
#                 self.bus.get_object("org.bluez", "/org/bluez"),
#                 "org.bluez.ProfileManager1"
#             )
            
#             self.device_manager = dbus.Interface(
#                 self.bus.get_object("org.bluez", "/"),
#                 "org.freedesktop.DBus.ObjectManager"
#             )
            
#             # Find Bluetooth adapter (usually hci0)
#             adapter_path = self.find_adapter()
#             if not adapter_path:
#                 raise Exception("No Bluetooth adapter found")
                
#             self.adapter = dbus.Interface(
#                 self.bus.get_object("org.bluez", adapter_path),
#                 "org.bluez.Adapter1"
#             )
            
#             print("D-Bus connection established")
#             return True
            
#         except Exception as e:
#             print(f"D-Bus setup failed: {e}")
#             return False
    
#     def find_adapter(self):
#         """Find the first available Bluetooth adapter"""
#         objects = self.device_manager.GetManagedObjects()
#         for path, interfaces in objects.items():
#             if "org.bluez.Adapter1" in interfaces:
#                 return path
#         return None
    
#     def create_hid_profile(self):
#         """Register HID profile with BlueZ"""
#         try:
#             # Profile options for HID keyboard
#             profile_options = {
#                 "ServiceRecord": self.create_sdp_record(),
#                 "Role": "server",
#                 "RequireAuthentication": dbus.Boolean(False),
#                 "RequireAuthorization": dbus.Boolean(False),
#                 "AutoConnect": dbus.Boolean(True),
#                 "PSM": dbus.UInt16(self.HID_CONTROL_PSM)
#             }
            
#             profile_path = "/org/bluez/myapp/hid_profile"
            
#             # Register profile
#             self.profile_manager.RegisterProfile(
#                 profile_path, 
#                 self.HID_UUID, 
#                 profile_options
#             )
            
#             print("HID profile registered")
#             return True
            
#         except Exception as e:
#             print(f"HID profile registration failed: {e}")
#             return False
    
#     def create_sdp_record(self):
#         """Create Service Discovery Protocol record for HID keyboard"""
#         # This tells other devices we're a keyboard
#         sdp_record = f"""
#         <?xml version="1.0" encoding="UTF-8" ?>
#         <record>
#             <attribute id="0x0001">
#                 <sequence>
#                     <uuid value="{self.HID_UUID}" />
#                 </sequence>
#             </attribute>
#             <attribute id="0x0004">
#                 <sequence>
#                     <sequence>
#                         <uuid value="0x0100" />
#                         <uint16 value="{self.HID_CONTROL_PSM}" />
#                     </sequence>
#                     <sequence>
#                         <uuid value="0x0011" />
#                         <uint16 value="{self.HID_INTERRUPT_PSM}" />
#                     </sequence>
#                 </sequence>
#             </attribute>
#             <attribute id="0x0005">
#                 <sequence>
#                     <uuid value="0x1002" />
#                 </sequence>
#             </attribute>
#             <attribute id="0x0100">
#                 <text value="Assistive Keyboard" />
#             </attribute>
#             <attribute id="0x0101">
#                 <text value="HID Keyboard for Musicians" />
#             </attribute>
#             <attribute id="0x0200">
#                 <uint16 value="0x0100" />
#             </attribute>
#             <attribute id="0x0201">
#                 <uint16 value="0x0111" />
#             </attribute>
#             <attribute id="0x0202">
#                 <uint8 value="0x40" />
#             </attribute>
#             <attribute id="0x0203">
#                 <uint8 value="0x21" />
#             </attribute>
#             <attribute id="0x0204">
#                 <text value="en" />
#             </attribute>
#             <attribute id="0x0205">
#                 <text value="USB" />
#             </attribute>
#             <attribute id="0x0206">
#                 <sequence>
#                     <sequence>
#                         <uint8 value="0x22" />
#                         <text encoding="hex" value="{self.HID_DESCRIPTOR.hex()}" />
#                     </sequence>
#                 </sequence>
#             </attribute>
#             <attribute id="0x0207">
#                 <sequence>
#                     <sequence>
#                         <uint16 value="0x0409" />
#                         <uint16 value="0x0100" />
#                     </sequence>
#                 </sequence>
#             </attribute>
#         </record>
#         """
#         return sdp_record.strip()
    
#     def make_discoverable(self):
#         """Make Pi discoverable as keyboard device"""
#         try:
#             # Set adapter properties
#             adapter_props = dbus.Interface(
#                 self.bus.get_object("org.bluez", self.adapter.object_path),
#                 "org.freedesktop.DBus.Properties"
#             )
            
#             # Make discoverable and pairable
#             adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
#             adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
#             adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
#             adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            
#             print("Device is discoverable")
#             return True
            
#         except Exception as e:
#             print(f"Failed to make discoverable: {e}")
#             return False
    
#     def send_hid_report(self, report_bytes):
#         """
#         Send 8-byte HID report via Bluetooth
#         Args:
#             report_bytes: List of 8 integers [modifier, reserved, key1-6]
#         """
#         if not self.interrupt_socket or not self.connected_device:
#             print("No Bluetooth connection available")
#             return False
            
#         try:
#             # Convert to bytes and send
#             report = bytes(report_bytes)
#             self.interrupt_socket.send(report)
#             print(f"Sent HID report: {report_bytes}")
#             return True
            
#         except Exception as e:
#             print(f"Failed to send HID report: {e}")
#             return False
    
#     def start_service(self):
#         """Start the Bluetooth HID service"""
#         print("🔧 Starting Bluetooth HID service...")
        
#         if not self.setup_dbus():
#             return False
            
#         if not self.create_hid_profile():
#             return False
            
#         if not self.make_discoverable():
#             return False
            
#         print("Bluetooth HID service ready!")
#         print("Pair your MacBook with this device now")
        
#         self.running = True
#         return True
    
#     def stop_service(self):
#         """Stop the Bluetooth HID service"""
#         self.running = False
#         if self.control_socket:
#             self.control_socket.close()
#         if self.interrupt_socket:
#             self.interrupt_socket.close()
#         print("Bluetooth HID service stopped")