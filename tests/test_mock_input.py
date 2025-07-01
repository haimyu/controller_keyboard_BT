# tests/test_mock_input.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from input_processor import InputProcessor
from hid_codes import shortcut_to_hid_report

def simulate_joystick_events():
    """Simulate the joystick events you discovered on Pi"""
    
    # Load your configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'shortcut_config.json')
    processor = InputProcessor(config_path)
    
    # Test cases based on your real hardware discovery:
    # Button events: type=1, numbers 0-10, value 0/1
    # Joystick events: type=2, numbers 1-2, value -32767 to +32767
    
    test_events = [
        # Button presses (type=1, value=1)
        (1, 0, 1, "Button 0 press"),
        (1, 1, 1, "Button 1 press"), 
        (1, 2, 1, "Button 2 press"),
        (1, 3, 1, "Button 3 press"),
        
        # Button releases (should be ignored)
        (1, 0, 0, "Button 0 release"),
        
        # Joystick movements (type=2)
        (2, 1, -25000, "Joystick left"),
        (2, 1, 25000, "Joystick right"),
        (2, 2, -25000, "Joystick up"),
        (2, 2, 25000, "Joystick down"),
        
        # Joystick center (should be ignored)
        (2, 1, 0, "Joystick center X"),
        (2, 2, 0, "Joystick center Y"),
    ]
    
    print("🎮 SIMULATING JOYSTICK EVENTS:")
    print("=" * 50)
    
    for event_type, number, value, description in test_events:
        print(f"\n📡 {description}")
        print(f"   Raw event: type={event_type}, number={number}, value={value}")
        
        # Process through your input processor
        shortcut = processor.process_event(event_type, number, value)
        
        if shortcut:
            # Convert to HID report
            hid_report = shortcut_to_hid_report(shortcut)
            print(f"   ✅ Shortcut: {shortcut}")
            print(f"   📤 HID Report: {hid_report}")
            print(f"   🎯 Action: Would send '{shortcut}' to MacBook")
        else:
            print(f"   ❌ No shortcut mapped")

def test_full_pipeline():
    """Test the complete input → shortcut → HID pipeline"""
    print("\n" + "=" * 50)
    print("🔧 TESTING FULL PIPELINE")
    print("=" * 50)
    
    # Test specific musician shortcuts
    musician_shortcuts = [
        "cmd+s",      # Save
        "cmd+z",      # Undo  
        "cmd+c",      # Copy
        "cmd+v",      # Paste
        "cmd+left",   # Navigate left
        "cmd+right",  # Navigate right
    ]
    
    for shortcut in musician_shortcuts:
        hid_report = shortcut_to_hid_report(shortcut)
        print(f"'{shortcut}' → {hid_report}")

if __name__ == "__main__":
    simulate_joystick_events()
    test_full_pipeline()