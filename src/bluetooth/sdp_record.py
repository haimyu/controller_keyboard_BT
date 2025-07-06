class SDPRecordBuilder:
    """Builds SDP records exactly matching working GitHub examples"""

    HID_KEYBOARD_DESCRIPTOR = bytes([
        0x05, 0x01,        # Usage Page (Generic Desktop)
        0x09, 0x06,        # Usage (Keyboard)
        0xA1, 0x01,        # Collection (Application)
        0x85, 0x01,        #   Report ID (1) - required for 9-byte reports
        0x75, 0x01,        #   Report Size (1)
        0x95, 0x08,        #   Report Count (8)
        0x05, 0x07,        #   Usage Page (Keyboard)
        0x19, 0xE0,        #   Usage Minimum (Left Ctrl)
        0x29, 0xE7,        #   Usage Maximum (Right GUI)
        0x15, 0x00,        #   Logical Minimum (0)
        0x25, 0x01,        #   Logical Maximum (1)
        0x81, 0x02,        #   Input (Data,Var,Abs) - 8 modifier keys
        0x95, 0x01,        #   Report Count (1)
        0x75, 0x08,        #   Report Size (8)
        0x81, 0x03,        #   Input (Const) - reserved byte
        0x95, 0x05,        #   Report Count (5)
        0x75, 0x01,        #   Report Size (1)
        0x05, 0x08,        #   Usage Page (LEDs)
        0x19, 0x01,        #   Usage Minimum (Num Lock)
        0x29, 0x05,        #   Usage Maximum (Kana)
        0x91, 0x02,        #   Output (Data,Var,Abs) - LED status from host
        0x95, 0x01,        #   Report Count (1)
        0x75, 0x03,        #   Report Size (3)
        0x91, 0x03,        #   Output (Const) - LED padding
        0x95, 0x06,        #   Report Count (6)
        0x75, 0x08,        #   Report Size (8)
        0x15, 0x00,        #   Logical Minimum (0)
        0x26, 0xFF, 0x00,  #   Logical Maximum (255)
        0x05, 0x07,        #   Usage Page (Keyboard)
        0x19, 0x00,        #   Usage Minimum (0)
        0x29, 0xFF,        #   Usage Maximum (255)
        0x81, 0x00,        #   Input (Data,Array) - 6 key code bytes
        0xC0,              # End Collection
    ])
    
    def create_hid_keyboard_record(self):
        hid_descriptor_hex = self.HID_KEYBOARD_DESCRIPTOR.hex()
        
        sdp_template = '''<?xml version="1.0" encoding="UTF-8" ?>
<record>
    <!-- Service Class ID List - identifies this as HID device -->
    <attribute id="0x0001">
        <sequence>
            <uuid value="0x1124" />
        </sequence>
    </attribute>
    
    <!-- Protocol Descriptor List - exact match to working example -->
    <attribute id="0x0004">
        <sequence>
            <sequence>
                <uuid value="0x0100" />
                <uint16 value="0x0011" />
            </sequence>
            <sequence>
                <uuid value="0x0011" />
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Browse Group List - helps with device categorization -->
    <attribute id="0x0005">
        <sequence>
            <uuid value="0x1002" />
        </sequence>
    </attribute>
    
    <!-- Language Based Attribute ID List - language support -->
    <attribute id="0x0006">
        <sequence>
            <uint16 value="0x656e" />
            <uint16 value="0x006a" />
            <uint16 value="0x0100" />
        </sequence>
    </attribute>
    
    <!-- Bluetooth Profile Descriptor List - HID profile declaration -->
    <attribute id="0x0009">
        <sequence>
            <sequence>
                <uuid value="0x1124" />
                <uint16 value="0x0100" />
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Additional Protocol Descriptor Lists - interrupt channel definition -->
    <attribute id="0x000d">
        <sequence>
            <sequence>
                <sequence>
                    <uuid value="0x0100" />
                    <uint16 value="0x0013" />
                </sequence>
                <sequence>
                    <uuid value="0x0011" />
                </sequence>
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Device identification strings - customized for your project -->
    <attribute id="0x0100">
        <text value="Assistive Keyboard" />
    </attribute>
    <attribute id="0x0101">
        <text value="Assistive Keyboard for Musicians" />
    </attribute>
    <attribute id="0x0102">
        <text value="Raspberry Pi Zero" />
    </attribute>
    
    <!-- HID-specific attributes - exact values from working example -->
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
        <uint8 value="0x00" />
    </attribute>
    <attribute id="0x0204">
        <boolean value="false" />
    </attribute>
    <attribute id="0x0205">
        <boolean value="false" />
    </attribute>
    
    <!-- HID Descriptor List - contains the complete HID report descriptor -->
    <attribute id="0x0206">
        <sequence>
            <sequence>
                <uint8 value="0x22" />
                <text encoding="hex" value="{hid_descriptor}" />
            </sequence>
        </sequence>
    </attribute>
    
    <!-- Remaining HID attributes - exact values from working example -->
    <attribute id="0x0207">
        <sequence>
            <sequence>
                <uint16 value="0x0409" />
                <uint16 value="0x0100" />
            </sequence>
        </sequence>
    </attribute>
    <attribute id="0x020b">
        <uint16 value="0x0100" />
    </attribute>
    <attribute id="0x020c">
        <uint16 value="0x0c80" />
    </attribute>
    <attribute id="0x020d">
        <boolean value="true" />
    </attribute>
    <attribute id="0x020e">
        <boolean value="false" />
    </attribute>
    <attribute id="0x020f">
        <uint16 value="0x0640" />
    </attribute>
    <attribute id="0x0210">
        <uint16 value="0x0320" />
    </attribute>
</record>'''
        
        return sdp_template.format(hid_descriptor=hid_descriptor_hex)
    