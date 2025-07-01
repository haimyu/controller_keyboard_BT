# tests/test_hid_codes.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from hid_codes import shortcut_to_hid_report

def test_basic_shortcuts():
    """Test common shortcut conversions"""
    
    # Test single key
    assert shortcut_to_hid_report("s") == [0, 0, 22, 0, 0, 0, 0, 0]
    
    # Test cmd+s
    assert shortcut_to_hid_report("cmd+s") == [8, 0, 22, 0, 0, 0, 0, 0]
    
    # Test cmd+alt+s  
    assert shortcut_to_hid_report("cmd+alt+s") == [12, 0, 22, 0, 0, 0, 0, 0]
    
    # Test multiple modifiers
    assert shortcut_to_hid_report("cmd+shift+z") == [10, 0, 29, 0, 0, 0, 0, 0]
    
    print("✅ All HID conversion tests PASSED!")

if __name__ == "__main__":
    test_basic_shortcuts()