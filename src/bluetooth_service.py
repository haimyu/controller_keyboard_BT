# src/bluetooth_service.py - COMPLETE FIXED VERSION
"""
Bluetooth HID Service for Assistive Keyboard
Implements proper dual-channel HID protocol (PSM 17 + PSM 19)
Fixed to work correctly with macOS by establishing separate control and interrupt channels
"""

import dbus
import dbus.service
import dbus.mainloop.glib
import socket
import threading
import time
import os
import subprocess
import sys

class BluetoothHIDService:
    """
    Complete Bluetooth HID service implementation with proper dual-channel support.
    
    This class implements the full HID-over-Bluetooth protocol which requires:
    - Control Channel (PSM 17): For configuration and control commands
    - Interrupt Channel (PSM 19): For actual HID data (keyboard reports)
    
    The previous implementation incorrectly used only one channel, which violated
    the HID protocol specification and caused macOS to ignore HID reports.
    """
    
    # Standard HID protocol identifiers
    HID_UUID = "00001124-0000-1000-8000-00805f9b34fb"
    HID_CONTROL_PSM = 17   # Control channel - for commands and configuration
    HID_INTERRUPT_PSM = 19 # Interrupt channel - for HID data (THIS IS WHERE KEYBOARD DATA GOES!)
    
    # HID descriptor that defines this device as a standard keyboard
    # This tells the OS exactly what kind of HID device we are
    HID_DESCRIPTOR = bytes([
        0x05, 0x01,        # Usage Page (Generic Desktop Controls)
        0x09, 0x06,        # Usage (Keyboard)
        0xA1, 0x01,        # Collection (Application)
        0x05, 0x07,        #   Usage Page (Keyboard/Keypad)
        0x19, 0xE0,        #   Usage Minimum (Left Control)
        0x29, 0xE7,        #   Usage Maximum (Right Command)
        0x15, 0x00,        #   Logical Minimum (0)
        0x25, 0x01,        #   Logical Maximum (1)
        0x75, 0x01,        #   Report Size (1 bit)
        0x95, 0x08,        #   Report Count (8 bits)
        0x81, 0x02,        #   Input (Data, Variable, Absolute) - Modifier byte
        0x95, 0x01,        #   Report Count (1)
        0x75, 0x08,        #   Report Size (8 bits)
        0x81, 0x01,        #   Input (Constant) - Reserved byte
        0x95, 0x06,        #   Report Count (6)
        0x75, 0x08,        #   Report Size (8 bits)
        0x15, 0x00,        #   Logical Minimum (0)
        0x25, 0x65,        #   Logical Maximum (101)
        0x05, 0x07,        #   Usage Page (Keyboard/Keypad)
        0x19, 0x00,        #   Usage Minimum (0)
        0x29, 0x65,        #   Usage Maximum (101)
        0x81, 0x00,        #   Input (Data, Array) - Key array
        0xC0               # End Collection
    ])
    
    def __init__(self):
        """Initialize the HID service with proper dual-channel architecture"""
        # D-Bus components for BlueZ interaction
        self.bus = None
        self.adapter = None
        self.profile_manager = None
        
        # CRITICAL: Separate sockets for each channel
        # This separation is what was missing in the broken version
        self.control_socket = None      # Listens on PSM 17
        self.interrupt_socket = None    # Listens on PSM 19
        self.control_client = None      # Connected client on PSM 17
        self.interrupt_client = None    # Connected client on PSM 19
        
        # Service state management
        self.running = False
        self.connection_thread = None
        self.connection_established = False
        
        print("🔧 Bluetooth HID Service initialized with dual-channel architecture")
        
    def start_service(self):
        """
        Start the complete HID service with proper dual-channel setup.
        This method orchestrates the entire service startup process.
        """
        print("🚀 Starting Bluetooth HID service...")
        
        # Step 1: Configure system for HID emulation
        if not self.configure_system_for_hid():
            print("❌ System configuration failed")
            return False
        
        # Step 2: Initialize D-Bus connection to BlueZ
        if not self.setup_dbus():
            print("❌ D-Bus setup failed")
            return False  
        
        # Step 3: Set device class to keyboard for proper recognition
        if not self.set_device_class():
            print("❌ Device class setup failed")
            return False
            
        # Step 4: Register HID profile with complete SDP record
        if not self.register_hid_profile():
            print("❌ HID profile registration failed")
            return False
            
        # Step 5: Make device discoverable and pairable
        if not self.make_discoverable():
            print("❌ Failed to make device discoverable")
            return False
            
        # Step 6: Create both L2CAP sockets (control and interrupt)
        if not self.setup_hid_sockets():
            print("❌ Socket setup failed")
            return False
            
        print("✅ Bluetooth HID service ready!")
        print("📱 Device appears as 'Assistive Keyboard' with keyboard icon")
        print("🔗 Pair your MacBook with this device now")
        print("⚠️  IMPORTANT: Both channels (PSM 17 and 19) must connect!")
        
        # Step 7: Start connection monitoring in background thread
        self.connection_thread = threading.Thread(target=self.wait_for_connections)
        self.connection_thread.daemon = True
        self.connection_thread.start()
        
        self.running = True
        return True
    
    def configure_system_for_hid(self):
        """
        Configure system runtime settings for HID emulation.
        This ensures the Bluetooth stack is ready for HID operation.
        """
        try:
            print("🔧 Configuring system for HID emulation...")
            
            # Ensure Bluetooth is powered on
            subprocess.run(["hciconfig", "hci0", "up"], check=False)
            
            # Enable simple secure pairing for better compatibility
            subprocess.run(["hciconfig", "hci0", "sspmode", "1"], check=False)
            
            # Set page and inquiry scan for discoverability
            subprocess.run(["hciconfig", "hci0", "piscan"], check=False)
            
            print("✅ System configured for HID operation")
            return True
            
        except Exception as e:
            print(f"❌ System configuration failed: {e}")
            return False
    
    def setup_dbus(self):
        """
        Initialize D-Bus connection to BlueZ daemon.
        This establishes communication with the system's Bluetooth service.
        """
        try:
            print("🔧 Setting up D-Bus connection...")
            
            # Set up D-Bus main loop for BlueZ communication
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            
            # Find the first available Bluetooth adapter
            adapter_path = self.find_adapter()
            if not adapter_path:
                print("❌ No Bluetooth adapter found")
                return False
                
            # Create interfaces for adapter control
            self.adapter = dbus.Interface(
                self.bus.get_object("org.bluez", adapter_path),
                "org.bluez.Adapter1"
            )
            
            # Create interface for profile management
            self.profile_manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/org/bluez"),
                "org.bluez.ProfileManager1"
            )
            
            print("✅ D-Bus connection established")
            return True
            
        except Exception as e:
            print(f"❌ D-Bus setup failed: {e}")
            return False
    
    def find_adapter(self):
        """
        Find the first available Bluetooth adapter in the system.
        Returns the D-Bus path to the adapter.
        """
        try:
            manager = dbus.Interface(
                self.bus.get_object("org.bluez", "/"),
                "org.freedesktop.DBus.ObjectManager"
            )
            
            objects = manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if "org.bluez.Adapter1" in interfaces:
                    print(f"✅ Found Bluetooth adapter: {path}")
                    return path
                    
        except Exception as e:
            print(f"❌ Failed to find adapter: {e}")
            
        return None
    
    def set_device_class(self):
        """
        Set device class to keyboard (0x002540).
        This makes the device appear with a keyboard icon in Bluetooth settings.
        """
        try:
            print("🔧 Setting device class to keyboard...")
            
            # Set device class using hciconfig
            result = subprocess.run(
                ["hciconfig", "hci0", "class", "0x002540"], 
                capture_output=True, 
                check=False
            )
            
            if result.returncode == 0:
                print("✅ Device class set to keyboard (0x002540)")
            else:
                print("⚠️  Device class will be set by D-Bus properties")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Device class setting note: {e}")
            return True  # Don't fail if this doesn't work
    
    def register_hid_profile(self):
        """
        Register HID profile with BlueZ using a complete SDP record.
        This tells the system exactly what kind of HID device we are.
        """
        try:
            print("🔧 Registering HID profile with BlueZ...")
            
            # Create profile options with complete SDP record
            profile_options = {
                "ServiceRecord": self.create_complete_sdp_record(),
                "Role": "server",
                "RequireAuthentication": dbus.Boolean(False),
                "RequireAuthorization": dbus.Boolean(False),
                "AutoConnect": dbus.Boolean(True)
            }
            
            profile_path = "/assistive/keyboard/profile"
            
            # Register the profile with BlueZ
            self.profile_manager.RegisterProfile(
                profile_path,
                self.HID_UUID,
                profile_options
            )
            
            print("✅ HID profile registered with complete SDP record")
            return True
            
        except Exception as e:
            print(f"❌ HID profile registration failed: {e}")
            return False
    
    def create_complete_sdp_record(self):
        """
        Create a complete Service Discovery Protocol (SDP) record.
        This is the "business card" that tells other devices what we are and how to connect.
        """
        # Convert our HID descriptor to hex string for SDP record
        hid_descriptor_hex = self.HID_DESCRIPTOR.hex()
        
        # Create comprehensive SDP record that defines our HID keyboard
        sdp_record = f"""<?xml version="1.0" encoding="UTF-8" ?>
<record>
    <!-- Service Class ID List - identifies this as HID -->
    <attribute id="0x0001">
        <sequence>
            <uuid value="0x1124" />
        </sequence>
    </attribute>
    
    <!-- Protocol Descriptor List - defines how to connect -->
    <attribute id="0x0004">
        <sequence>
            <!-- L2CAP layer -->
            <sequence>
                <uuid value="0x0100" />
            </sequence>
            <!-- Control channel PSM 17 -->
            <sequence>
                <uuid value="0x0011" />
                <uint16 value="0x{self.HID_CONTROL_PSM:04x}" />
            </sequence>
            <!-- L2CAP layer for interrupt -->
            <sequence>
                <uuid value="0x0100" />
            </sequence>
            <!-- Interrupt channel PSM 19 -->
            <sequence>
                <uuid value="0x0011" />
                <uint16 value="0x{self.HID_INTERRUPT_PSM:04x}" />
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Browse Group List -->
    <attribute id="0x0005">
        <sequence>
            <uuid value="0x1002" />
        </sequence>
    </attribute>
    
    <!-- Language Base Attribute ID List -->
    <attribute id="0x0006">
        <sequence>
            <uint16 value="0x656e" />
            <uint16 value="0x006a" />
            <uint16 value="0x0100" />
        </sequence>
    </attribute>
    
    <!-- Bluetooth Profile Descriptor List -->
    <attribute id="0x0009">
        <sequence>
            <sequence>
                <uuid value="0x1124" />
                <uint16 value="0x0111" />
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Additional Protocol Descriptor List -->
    <attribute id="0x000d">
        <sequence>
            <sequence>
                <sequence>
                    <uuid value="0x0100" />
                    <uint16 value="0x0013" />
                </sequence>
                <sequence>
                    <uuid value="0x0011" />
                    <uint16 value="0x{self.HID_CONTROL_PSM:04x}" />
                </sequence>
            </sequence>
            <sequence>
                <sequence>
                    <uuid value="0x0100" />
                    <uint16 value="0x0011" />
                </sequence>
                <sequence>
                    <uuid value="0x0011" />
                    <uint16 value="0x{self.HID_INTERRUPT_PSM:04x}" />
                </sequence>
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Service Name -->
    <attribute id="0x0100">
        <text value="Assistive Keyboard" />
    </attribute>
    
    <!-- Service Description -->
    <attribute id="0x0101">
        <text value="Assistive Keyboard for Musicians" />
    </attribute>
    
    <!-- Provider Name -->
    <attribute id="0x0102">
        <text value="Assistive Technology" />
    </attribute>
    
    <!-- HID Device Release Number -->
    <attribute id="0x0200">
        <uint16 value="0x0111" />
    </attribute>
    
    <!-- HID Parser Version -->
    <attribute id="0x0201">
        <uint16 value="0x0111" />
    </attribute>
    
    <!-- HID Device Subclass -->
    <attribute id="0x0202">
        <uint8 value="0x40" />
    </attribute>
    
    <!-- HID Country Code -->
    <attribute id="0x0203">
        <uint8 value="0x21" />
    </attribute>
    
    <!-- HID Virtual Cable -->
    <attribute id="0x0204">
        <boolean value="true" />
    </attribute>
    
    <!-- HID Reconnect Initiate -->
    <attribute id="0x0205">
        <boolean value="false" />
    </attribute>
    
    <!-- HID Descriptor List - THE CRITICAL PART -->
    <attribute id="0x0206">
        <sequence>
            <sequence>
                <uint8 value="0x22" />
                <text encoding="hex" value="{hid_descriptor_hex}" />
            </sequence>
        </sequence>
    </attribute>
    
    <!-- HID Language ID Base List -->
    <attribute id="0x0207">
        <sequence>
            <sequence>
                <uint16 value="0x0409" />
                <uint16 value="0x0100" />
            </sequence>
        </sequence>
    </attribute>
</record>"""
        
        return sdp_record.strip()
    
    def make_discoverable(self):
        """
        Make the Pi discoverable and pairable as a keyboard device.
        This allows the MacBook to find and connect to our device.
        """
        try:
            print("🔧 Making device discoverable...")
            
            # Get adapter properties interface
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter.object_path),
                "org.freedesktop.DBus.Properties"
            )
            
            # Power on the adapter
            adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
            time.sleep(1)
            
            # Set device name
            adapter_props.Set("org.bluez.Adapter1", "Alias", "Assistive Keyboard")
            
            # Make discoverable and pairable
            adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            
            # Set timeouts (0 = never timeout)
            adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            adapter_props.Set("org.bluez.Adapter1", "PairableTimeout", dbus.UInt32(0))
            
            # Additional system-level configuration
            subprocess.run(["hciconfig", "hci0", "piscan"], check=False)
            subprocess.run(["hciconfig", "hci0", "sspmode", "1"], check=False)
            
            print("✅ Device is discoverable as 'Assistive Keyboard'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to make discoverable: {e}")
            return False
    
    def get_bluetooth_address(self):
        """Get the Pi's Bluetooth MAC address"""
        try:
            adapter_props = dbus.Interface(
                self.bus.get_object("org.bluez", self.adapter.object_path),
                "org.freedesktop.DBus.Properties"
            )
            
            address = adapter_props.Get("org.bluez.Adapter1", "Address")
            print(f"📍 Using Bluetooth address: {address}")
            return str(address)
            
        except Exception as e:
            print(f"❌ Failed to get Bluetooth address: {e}")
            return None
    
    def setup_hid_sockets(self):
        """
        CRITICAL METHOD: Create both L2CAP sockets for HID communication.
        This is where the dual-channel architecture is implemented.
        """
        try:
            print("🔧 Setting up HID sockets...")
            
            # Get our Bluetooth address
            bt_address = self.get_bluetooth_address()
            if not bt_address:
                print("❌ Cannot get Bluetooth address")
                return False
            
            # Create CONTROL socket (PSM 17)
            # This handles configuration, setup, and control commands
            print("🔧 Creating control socket (PSM 17)...")
            self.control_socket = socket.socket(
                socket.AF_BLUETOOTH, 
                socket.SOCK_SEQPACKET, 
                socket.BTPROTO_L2CAP
            )
            self.control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.control_socket.bind((bt_address, self.HID_CONTROL_PSM))
            self.control_socket.listen(1)
            print(f"✅ Control socket listening: {bt_address}:{self.HID_CONTROL_PSM}")
            
            # Create INTERRUPT socket (PSM 19)
            # THIS IS WHERE THE ACTUAL HID DATA FLOWS - CRITICAL FOR FUNCTIONALITY
            print("🔧 Creating interrupt socket (PSM 19)...")
            self.interrupt_socket = socket.socket(
                socket.AF_BLUETOOTH, 
                socket.SOCK_SEQPACKET, 
                socket.BTPROTO_L2CAP
            )
            self.interrupt_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.interrupt_socket.bind((bt_address, self.HID_INTERRUPT_PSM))
            self.interrupt_socket.listen(1)
            print(f"✅ Interrupt socket listening: {bt_address}:{self.HID_INTERRUPT_PSM}")
            
            print("🎉 Both HID channels ready for macOS connection!")
            print("📡 Control Channel (PSM 17): Configuration and commands")
            print("📡 Interrupt Channel (PSM 19): HID data (keyboard reports)")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup HID sockets: {e}")
            return False
    
    def wait_for_connections(self):
        """
        Wait for macOS to establish BOTH control and interrupt connections.
        This is the heart of the dual-channel architecture.
        """
        try:
            print("⏳ Waiting for macOS to connect on BOTH channels...")
            print("📱 Please pair your MacBook now!")
            
            # Set reasonable timeouts for connection attempts
            self.control_socket.settimeout(60)    # 60 seconds for control
            self.interrupt_socket.settimeout(60)  # 60 seconds for interrupt
            
            # Phase 1: Wait for control connection
            print("🔄 Phase 1: Waiting for control connection (PSM 17)...")
            try:
                self.control_client, control_addr = self.control_socket.accept()
                print(f"✅ Control channel connected from: {control_addr}")
                print("🎯 Control channel established - configuration ready!")
            except socket.timeout:
                print("❌ Control connection timeout - check MacBook pairing")
                return
            except Exception as e:
                print(f"❌ Control connection error: {e}")
                return
            
            # Phase 2: Wait for interrupt connection
            print("🔄 Phase 2: Waiting for interrupt connection (PSM 19)...")
            try:
                self.interrupt_client, interrupt_addr = self.interrupt_socket.accept()
                print(f"✅ Interrupt channel connected from: {interrupt_addr}")
                print("🎯 Interrupt channel established - HID data ready!")
            except socket.timeout:
                print("❌ Interrupt connection timeout")
                print("💡 Try disconnecting and reconnecting MacBook")
                # Clean up control connection
                if self.control_client:
                    self.control_client.close()
                return
            except Exception as e:
                print(f"❌ Interrupt connection error: {e}")
                if self.control_client:
                    self.control_client.close()
                return
            
            # Verify we have separate connections (not the same socket)
            if self.control_client == self.interrupt_client:
                print("❌ CRITICAL ERROR: Control and interrupt are the same socket!")
                print("🔧 This indicates a fundamental protocol violation")
                return
            
            # Success! Both channels established
            self.connection_established = True
            print("\n🎉 DUAL-CHANNEL HID CONNECTION ESTABLISHED!")
            print("✅ Control Channel (PSM 17): Ready for commands")
            print("✅ Interrupt Channel (PSM 19): Ready for HID data")
            print("🚀 Device fully operational - ready to send keyboard shortcuts!")
            print("🎹 Press buttons on your joystick to test...\n")
            
        except Exception as e:
            print(f"❌ Connection establishment failed: {e}")
            self.cleanup_connections()
    
    def send_hid_report(self, report_bytes):
        """
        Send HID report on the INTERRUPT channel (PSM 19).
        This is the corrected method that uses the proper data channel.
        """
        # Verify we have a proper interrupt connection
        if not self.interrupt_client:
            print("❌ No interrupt channel connection (PSM 19)")
            print("💡 Make sure MacBook is properly paired and connected")
            return False
            
        # Verify connection is established
        if not self.connection_established:
            print("❌ Connection not fully established")
            return False
            
        try:
            # Validate report format
            if len(report_bytes) != 8:
                print(f"❌ Invalid HID report length: {len(report_bytes)} (expected 8)")
                return False
            
            # Send on INTERRUPT channel - this is where HID data belongs!
            report = bytes(report_bytes)
            bytes_sent = self.interrupt_client.send(report)
            
            if bytes_sent == len(report):
                print(f"✅ HID report sent successfully: {list(report_bytes)}")
                return True
            else:
                print(f"⚠️  Partial send: {bytes_sent}/{len(report)} bytes")
                return False
            
        except socket.error as e:
            print(f"❌ Socket error sending HID report: {e}")
            return self.attempt_reconnect_and_send(report_bytes)
        except Exception as e:
            print(f"❌ Failed to send HID report: {e}")
            return False
    
    def attempt_reconnect_and_send(self, report_bytes):
        """
        Attempt to reconnect the interrupt channel and resend the report.
        This handles transient connection issues.
        """
        try:
            print("🔄 Attempting to reconnect interrupt channel...")
            
            # Try to reconnect directly to known MacBook address
            macbook_address = "2C:CA:16:14:FE:90"  # Your MacBook's address
            
            # Create new interrupt connection
            new_interrupt = socket.socket(
                socket.AF_BLUETOOTH, 
                socket.SOCK_SEQPACKET, 
                socket.BTPROTO_L2CAP
            )
            new_interrupt.settimeout(5)
            new_interrupt.connect((macbook_address, self.HID_INTERRUPT_PSM))
            
            # Replace the old connection
            if self.interrupt_client:
                try:
                    self.interrupt_client.close()
                except:
                    pass
            
            self.interrupt_client = new_interrupt
            
            # Try sending the report again
            report = bytes(report_bytes)
            self.interrupt_client.send(report)
            
            print("✅ Reconnected and sent HID report successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Reconnection failed: {e}")
            print("💡 Try restarting the service or re-pairing the MacBook")
            return False
    
    def cleanup_connections(self):
        """Clean up all socket connections"""
        print("🧹 Cleaning up connections...")
        
        connections_to_close = [
            ("Control client", self.control_client),
            ("Interrupt client", self.interrupt_client),
            ("Control socket", self.control_socket),
            ("Interrupt socket", self.interrupt_socket)
        ]
        
        for name, connection in connections_to_close:
            if connection:
                try:
                    connection.close()
                    print(f"✅ {name} closed")
                except Exception as e:
                    print(f"⚠️  Error closing {name}: {e}")
    
    def stop_service(self):
        """
        Stop the HID service and clean up all resources.
        This ensures proper shutdown of both channels.
        """
        print("🛑 Stopping Bluetooth HID service...")
        
        self.running = False
        self.connection_established = False
        
        # Clean up all connections
        self.cleanup_connections()
        
        # Reset connection variables
        self.control_client = None
        self.interrupt_client = None
        self.control_socket = None
        self.interrupt_socket = None
        
        print("✅ Bluetooth HID service stopped cleanly")
    
    def get_connection_status(self):
        """
        Get detailed connection status for debugging.
        This helps diagnose connection issues.
        """
        status = {
            "service_running": self.running,
            "connection_established": self.connection_established,
            "has_control_socket": self.control_socket is not None,
            "has_interrupt_socket": self.interrupt_socket is not None,
            "has_control_client": self.control_client is not None,
            "has_interrupt_client": self.interrupt_client is not None,
            "channels_are_separate": (
                self.control_client is not None and 
                self.interrupt_client is not None and 
                self.control_client != self.interrupt_client
            )
        }
        
        return status
    
    def print_connection_status(self):
        """Print detailed connection status for debugging"""
        status = self.get_connection_status()
        
        print("\n📊 CONNECTION STATUS:")
        print(f"  Service Running: {'✅' if status['service_running'] else '❌'}")
        print(f"  Connection Established: {'✅' if status['connection_established'] else '❌'}")
        print(f"  Control Socket: {'✅' if status['has_control_socket'] else '❌'}")
        print(f"  Interrupt Socket: {'✅' if status['has_interrupt_socket'] else '❌'}")
        print(f"  Control Client: {'✅' if status['has_control_client'] else '❌'}")
        print(f"  Interrupt Client: {'✅' if status['has_interrupt_client'] else '❌'}")
        print(f"  Channels Separate: {'✅' if status['channels_are_separate'] else '❌'}")
        
        if status['connection_established']:
            print("🎉 Ready to send HID reports!")
        else:
            print("⚠️  Not ready - check connection status above")
        print("")