##############         IMPORTS         ##############
#####################################################
# Importer les bibliothèques nécessaires
import socket
import threading
import threading
import queue
import logging
import time
from typing import Dict, List, Type, Optional, Tuple
import contextlib
#Importer d'autres fichier

##############         CLASSES         ##############
#####################################################
class NetworkTransport:
    def __init__(self, max_pool: int, reflected_types_map: Dict[int, Type], logger: logging.Logger, timeout: float):
        self.conn_pool: Dict[str, List['NetConn']] = {}
        self.conn_pool_lock = threading.Lock()
        self.max_pool = max_pool

        self.msg_ch = queue.Queue()  # Channel for transferring messages between NetworkTransport and outer variables

        self.reflected_types_map = reflected_types_map

        self.logger = logger

        self.shutdown = False
        self.shutdown_ch = threading.Event()
        self.shutdown_lock = threading.Lock()

        self.stream = None  # Stream layer implementation (not provided in original code)

        # Context for cancelling existing connection handlers
        self.stream_ctx = contextlib.nullcontext()
        self.stream_ctx_lock = threading.RLock()

        self.timeout = timeout

    def start(self):
        self.logger.info("NetworkTransport started")
        # Start the network transport functionality
        # Example: threading.Thread(target=self._network_handler, daemon=True).start()

    def stop(self):
        with self.shutdown_lock:
            if not self.shutdown:
                self.shutdown = True
                self.shutdown_ch.set()
                self.logger.info("NetworkTransport is shutting down")
                # Cancel existing connection handlers
                with self.stream_ctx_lock:
                    if hasattr(self.stream_ctx, 'cancel'):
                        self.stream_ctx.cancel()



#############         FUNCTIONS         #############
#####################################################
def start_p2p_listen(name, cluster_port, max_pool, reflected_types_map):
    try:
        # Create a TCP socket and bind it to the specified port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("", cluster_port[name]))

        # Start listening for incoming connections
        server_socket.listen()

        # Initialize the network transport with the TCP socket
        trans = NetworkTransport(server_socket, 30, None, max_pool, reflected_types_map)

        print(f"Node {name} is listening on port {cluster_port[name]}")

        # Accept incoming connections in a separate thread
        threading.Thread(target=_accept_connections, args=(trans,), daemon=True).start()

    except Exception as e:
        return e

def _accept_connections(trans):
    while True:
        try:
            client_socket, client_address = trans.server_socket.accept()
            # Handle the incoming connection (not shown here)
            # Example: _handle_connection(client_socket, client_address)
        except Exception as e:
            print(f"Error accepting connection: {e}")

##############         EXEMPLES         #############
#####################################################
# Example usage:
'''
if __name__ == "__main__":
    name = "example_node"
    cluster_port = {"example_node": 8080}  # Replace with your actual port mapping
    max_pool = 10  # Replace with your actual max pool size
    reflected_types_map = {}  # Replace with your actual reflected types map

    start_p2p_listen(name, cluster_port, max_pool, reflected_types_map)
'''
################         MAIN         ###############
#####################################################







