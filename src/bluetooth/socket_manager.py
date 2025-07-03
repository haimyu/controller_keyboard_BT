import socket
import threading
import subprocess


class SocketManager:
    """
    Manages HID L2CAP sockets for control and interrupt channels.
    """
    
    HID_CONTROL_PSM = 17
    HID_INTERRUPT_PSM = 19
    
    def __init__(self):
        self.control_socket = None
        self.interrupt_socket = None
        self.control_client = None
        self.interrupt_client = None
        self.bt_address = None
        
    def setup_hid_sockets(self):
        """Create both L2CAP sockets"""
        try:
            self.bt_address = self._get_bt_address()
            if not self.bt_address:
                return False
            
            self.control_socket = self._create_socket(self.HID_CONTROL_PSM)
            if not self.control_socket:
                return False
                
            self.interrupt_socket = self._create_socket(self.HID_INTERRUPT_PSM)
            if not self.interrupt_socket:
                return False
                
            print("✅ Both HID sockets created")
            return True
            
        except Exception as e:
            print(f"❌ Socket setup failed: {e}")
            return False
    
    def _create_socket(self, psm):
        """Create and bind a single L2CAP socket"""
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.bt_address, psm))
            sock.listen(1)
            print(f"✅ Socket created for PSM {psm}")
            return sock
            
        except Exception as e:
            print(f"❌ Failed to create socket for PSM {psm}: {e}")
            return None
    
    def _get_bt_address(self):
        try:
            result = subprocess.run(["hciconfig", "hci0"], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'BD Address:' in line:
                    return line.split('BD Address: ')[1].split(' ')[0]
        except:
            pass
        return None
    
    def accept_connections(self):
        """Accept connections on both channels"""
        try:
            if self.control_socket:
                self.control_client, addr = self.control_socket.accept()
                print(f"✅ Control connected: {addr}")
            
            if self.interrupt_socket:
                self.interrupt_client, addr = self.interrupt_socket.accept()
                print(f"✅ Interrupt connected: {addr}")
                
            return True
            
        except Exception as e:
            print(f"❌ Connection acceptance failed: {e}")
            return False
    
    def send_hid_report(self, report_bytes):
        """Send HID report on interrupt channel"""
        if not self.interrupt_client:
            print("❌ No interrupt connection")
            return False
            
        try:
            if len(report_bytes) != 8:
                print(f"❌ Invalid report length: {len(report_bytes)}")
                return False
                
            bytes_sent = self.interrupt_client.send(bytes(report_bytes))
            return bytes_sent == len(report_bytes)
            
        except Exception as e:
            print(f"❌ Send failed: {e}")
            return False
    
    def get_status(self):
        """Get socket status"""
        return {
            'control_socket_ready': self.control_socket is not None,
            'interrupt_socket_ready': self.interrupt_socket is not None,
            'control_connected': self.control_client is not None,
            'interrupt_connected': self.interrupt_client is not None
        }
    
    def cleanup(self):
        """Clean up all sockets"""
        for sock in [self.control_client, self.interrupt_client, 
                    self.control_socket, self.interrupt_socket]:
            if sock:
                try:
                    sock.close()
                except:
                    pass

