import subprocess

class SystemConfigurator:
    def configure_for_hid(self):
        """Configure system for HID emulation"""
        try:
            self._configure_bluetooth()
            
            print("System configured")
            return True
            
        except Exception as e:
            print(f"System configuration failed: {e}")
            return False
    
    def _configure_bluetooth(self):
        """Configure Bluetooth adapter settings"""
        commands = [
            ["hciconfig", "hci0", "up"],
            ["hciconfig", "hci0", "sspmode", "1"],
            ["hciconfig", "hci0", "piscan"]
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, check=False)
            except Exception as e:
                print(f"Command {' '.join(cmd)} failed: {e}")

