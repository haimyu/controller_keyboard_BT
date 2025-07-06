class SDPRecordBuilder:
    """Builds SDP records for HID devices"""

    HID_KEYBOARD_DESCRIPTOR = bytes([
        0x05, 0x01,  # Usage Page (Generic Desktop)
        0x09, 0x06,  # Usage (Keyboard)
        0xA1, 0x01,  # Collection (Application)
        0x05, 0x07,  # Usage Page (Key Codes)
        0x19, 0xE0,  # Usage Minimum (224)
        0x29, 0xE7,  # Usage Maximum (231)
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
        0xC0         # End Collection
    ])
    
    def create_hid_keyboard_record(self):
        """Create complete SDP record for HID keyboard"""
        hid_descriptor_hex = self.HID_KEYBOARD_DESCRIPTOR.hex()

        sdp_template = self._get_hid_keyboard_template()
        
        return sdp_template.format(
            control_psm=17,
            interrupt_psm=19,
            hid_descriptor=hid_descriptor_hex
        )
    
    def _get_hid_keyboard_template(self):
        """Get SDP template for HID keyboard"""
        return '''<?xml version="1.0" encoding="UTF-8" ?>
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
            </sequence>
            <sequence>
                <uuid value="0x0011" />
                <uint16 value="0x{control_psm:04x}" />
            </sequence>
            <sequence>
                <uuid value="0x0100" />
            </sequence>
            <sequence>
                <uuid value="0x0011" />
                <uint16 value="0x{interrupt_psm:04x}" />
            </sequence>
        </sequence>
    </attribute>
    <attribute id="0x0100">
        <text value="Assistive Keyboard" />
    </attribute>
    <attribute id="0x0206">
        <sequence>
            <sequence>
                <uint8 value="0x22" />
                <text encoding="hex" value="{hid_descriptor}" />
            </sequence>
        </sequence>
    </attribute>
</record>'''

