import time
import struct
from input_processor import InputProcessor

processor = InputProcessor('shortcut_config.json')

def mapping():
    try:
        js_device = open('/dev/input/js0', 'rb')
        print("Press any button to reboot Pi...")
        
        while True:
            event = js_device.read(8)
            _, value, event_type, number = struct.unpack('IhBB', event)

            print(f"Button {number} - Event Type: {event_type}, Value: {value}")

            shortcut = processor.process_event(event_type, number, value)
            if shortcut:
                print(f"TRIGGER: {shortcut}")

            

    except FileNotFoundError:
        print("No gamepad found. Check: ls /dev/input/js*")
    except KeyboardInterrupt:
        print("Exiting...")

mapping()