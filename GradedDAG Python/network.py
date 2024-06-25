##############         IMPORTS         ##############
#####################################################
# Importer les bibliothèques nécessaires
import socket
import threading

#Importer d'autres fichier

##############         CLASSES         ##############
#####################################################
class NetworkTransport:
    def __init__(self, server_socket, timeout, _, max_pool, reflected_types_map):
        self.server_socket = server_socket
        self.timeout = timeout
        self.max_pool = max_pool
        self.reflected_types_map = reflected_types_map


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







