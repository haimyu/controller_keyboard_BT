import threading
import time

class ConnectionMonitor:
    """Monitors HID connection establishment"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.callback = None
        
    def start_monitoring(self, socket_manager, connection_callback):
        """Start monitoring for connections"""
        self.socket_manager = socket_manager
        self.callback = connection_callback
        self.monitoring = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_connections)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("Connection monitoring started")
    
    def _monitor_connections(self):
        """Monitor connection establishment"""
        try:
            print("Monitoring for HID connections...")
            
            if self.socket_manager.accept_connections():
                if self.callback:
                    self.callback()
            else:
                print("Connection monitoring failed")
                
        except Exception as e:
            print(f"Connection monitoring error: {e}")
    
    def stop(self):
        """Stop connection monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def get_status(self):
        """Get monitoring status"""
        return {
            'monitoring': self.monitoring,
            'thread_active': self.monitor_thread is not None and self.monitor_thread.is_alive()
        }
